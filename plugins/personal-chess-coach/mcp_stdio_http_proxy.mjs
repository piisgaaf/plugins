#!/usr/bin/env node
import readline from "node:readline";
import { request as httpRequest } from "node:http";
import { request as httpsRequest } from "node:https";

const HOST = process.env.MCP_HTTP_HOST ?? "127.0.0.1";
const PORT = Number(process.env.MCP_HTTP_PORT ?? "4000");
const PATH = process.env.MCP_HTTP_PATH ?? "/mcp"; // StreamableHTTP default endpoint is usually /mcp
const USE_TLS = process.env.MCP_HTTP_TLS === "1";
const TIMEOUT_MS = Number(process.env.MCP_HTTP_TIMEOUT_MS ?? "30000");

// Optional: enable verbose proxy logging to stderr
const DEBUG = process.env.MCP_PROXY_DEBUG === "1";

function log(...args) {
  console.error("[mcp-proxy]", ...args);
}
function dlog(...args) {
  if (DEBUG) console.error("[mcp-proxy][debug]", ...args);
}

function writeJson(obj) {
  process.stdout.write(JSON.stringify(obj) + "\n");
}

function jsonRpcError(id, code, message, data) {
  const err = { code, message };
  if (data !== undefined) err.data = data;
  writeJson({ jsonrpc: "2.0", id, error: err });
}

// Persist session across requests (critical for Streamable HTTP)
let sessionId = null; // learned from upstream response header
let cookie = null; // optional fallback if upstream uses cookies
let queue = Promise.resolve();

// Remember how the client initialized us so we can re-init upstream
let lastInitializeRequest = null;           // JSON-RPC "initialize" request from client
let sawClientInitializedNotification = false; // whether client already sent notifications/initialized

function getHeader(resHeaders, name) {
  // Node lowercases header keys, but be defensive
  const key = name.toLowerCase();
  return resHeaders[key] ?? resHeaders[name] ?? resHeaders[name.toUpperCase()];
}

function captureSessionFromResponse(resHeaders) {
  const sid = getHeader(resHeaders, "mcp-session-id");
  if (typeof sid === "string" && sid.length) {
    sessionId = sid;
    dlog("captured mcp-session-id:", sessionId);
  }

  // Some servers may set cookies; keep them if present
  // resHeaders["set-cookie"] can be string or array depending on Node version
  const setCookie = getHeader(resHeaders, "set-cookie");
  if (setCookie) {
    const raw = Array.isArray(setCookie) ? setCookie : [setCookie];
    cookie = raw.map((c) => String(c).split(";")[0].trim()).join("; ");
    dlog("captured cookie:", cookie);
  }
}

async function postJson(payload) {
  const reqFn = USE_TLS ? httpsRequest : httpRequest;
  const body = JSON.stringify(payload);

  return await new Promise((resolve, reject) => {
    const headers = {
      "content-type": "application/json",
      "accept": "application/json",
      "content-length": Buffer.byteLength(body, "utf8"),
      "user-agent": "mcp-stdio-http-proxy/0.3",
      // Some frameworks behave better with explicit connection semantics
      "connection": "keep-alive",
    };

    // Streamable HTTP session continuity
    if (sessionId) headers["mcp-session-id"] = sessionId;
    if (cookie) headers["cookie"] = cookie;

    dlog("POST", `${USE_TLS ? "https" : "http"}://${HOST}:${PORT}${PATH}`, {
      hasSession: Boolean(sessionId),
      method: payload?.method,
      id: payload?.id,
    });

    const req = reqFn(
      { method: "POST", hostname: HOST, port: PORT, path: PATH, headers },
      (res) => {
        let data = "";
        res.setEncoding("utf8");

        // IMPORTANT: capture session id on every response (some servers refresh it)
        captureSessionFromResponse(res.headers);

        res.on("data", (chunk) => (data += chunk));
        res.on("end", () => {
          const status = res.statusCode ?? 0;
          resolve({ status, body: data, headers: res.headers });
        });
      }
    );

    req.setTimeout(TIMEOUT_MS, () => {
      req.destroy(new Error(`HTTP timeout after ${TIMEOUT_MS}ms`));
    });

    req.on("error", reject);
    req.end(body);
  });
}

function isJsonRpcResponse(resp) {
  return resp && typeof resp === "object" && resp.jsonrpc === "2.0" && ("result" in resp || "error" in resp) && "id" in resp;
}

function isNotInitializedError(resp) {
  // Your Elixir server emits: message: "Server not initialized", reason: "not_initialized"
  return Boolean(
    resp &&
      resp.error &&
      (
        resp.error?.message?.includes("Server not initialized") ||
        resp.error?.data?.reason === "not_initialized" ||
        resp.error?.data?.message?.includes("Server not initialized")
      )
  );
}

function resetSession() {
  sessionId = null;
  cookie = null;
}

async function reinitializeUpstream() {
  if (!lastInitializeRequest) {
    throw new Error("Cannot reinitialize: no cached initialize request from client yet");
  }

  // 1) initialize (must have an id)
  const initMsg = lastInitializeRequest;
  const initResp = await postJson(initMsg);

  if (initResp.status < 200 || initResp.status >= 300) {
    throw new Error(`Upstream initialize failed HTTP ${initResp.status}`);
  }
  if (!initResp.body || !initResp.body.trim()) {
    throw new Error("Upstream initialize returned empty body");
  }

  let parsed;
  try {
    parsed = JSON.parse(initResp.body);
  } catch {
    throw new Error("Upstream initialize returned invalid JSON");
  }
  if (!isJsonRpcResponse(parsed)) {
    throw new Error("Upstream initialize returned non-JSON-RPC response");
  }
  if (parsed.error) {
    throw new Error(`Upstream initialize error: ${parsed.error.message || "unknown"}`);
  }

  // 2) notifications/initialized (no id, so no response expected)
  // Only send it if the client already sent it earlier; that matches the client lifecycle.
  if (sawClientInitializedNotification) {
    await postJson({ jsonrpc: "2.0", method: "notifications/initialized" });
  }
}

async function handleIncoming(msg) {
  // Cache lifecycle messages so we can re-init upstream later
  if (msg?.method === "initialize") {
    lastInitializeRequest = msg;
  }
  if (msg?.method === "notifications/initialized") {
    sawClientInitializedNotification = true;
  }

  const hasId = Object.prototype.hasOwnProperty.call(msg, "id");
  const id = msg.id;

  try {
    let { status, body } = await postJson(msg);

    // If session expired, reset + reinitialize + retry once
    // Streamable HTTP often uses 404 for unknown/expired session.
    if (status === 404 && msg?.method !== "initialize") {
      dlog("Upstream returned 404; assuming expired session. Reinitializing...");
      resetSession();
      await reinitializeUpstream();
      ({ status, body } = await postJson(msg));
    }

    // Notifications (no id): do not emit a response on stdout
    if (!hasId) return;

    if (status < 200 || status >= 300) {
      return jsonRpcError(id, -32603, "Upstream HTTP error", {
        status,
        snippet: (body || "").slice(0, 800),
      });
    }

    if (!body || !body.trim()) {
      return jsonRpcError(id, -32603, "Upstream returned empty body for request");
    }

    let resp;
    try {
      resp = JSON.parse(body);
    } catch {
      return jsonRpcError(id, -32603, "Upstream returned invalid JSON", {
        snippet: body.slice(0, 800),
      });
    }

    // If upstream reports not_initialized, reset + reinit + retry once
    if (isNotInitializedError(resp) && msg?.method !== "initialize") {
      dlog("Upstream reports not_initialized; resetting session and reinitializing...");
      resetSession();
      await reinitializeUpstream();

      const retry = await postJson(msg);
      status = retry.status;
      body = retry.body;

      if (status < 200 || status >= 300) {
        return jsonRpcError(id, -32603, "Upstream HTTP error after reinit", {
          status,
          snippet: (body || "").slice(0, 800),
        });
      }

      try {
        resp = JSON.parse(body);
      } catch {
        return jsonRpcError(id, -32603, "Upstream returned invalid JSON after reinit", {
          snippet: (body || "").slice(0, 800),
        });
      }
    }

    // Upstream might return an error object with a different id shape; force id to match request.
    // Claude expects the response id to match the request id.
    if (!isJsonRpcResponse(resp)) {
      return jsonRpcError(id, -32603, "Upstream returned non-JSON-RPC response", {
        snippet: JSON.stringify(resp).slice(0, 800),
      });
    }

    resp.id = id;
    resp.jsonrpc = "2.0";
    writeJson(resp);
  } catch (e) {
    if (hasId) {
      jsonRpcError(id, -32603, "Proxy/upstream error", { message: String(e?.message ?? e) });
    } else {
      log("Notification forward failed:", String(e?.message ?? e));
    }
  }
}

const rl = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });

rl.on("line", (line) => {
  const s = line.trim();
  if (!s) return;

  let msg;
  try {
    msg = JSON.parse(s);
  } catch {
    log("Bad JSON from client:", s.slice(0, 200));
    return;
  }

  queue = queue
    .then(() => handleIncoming(msg))
    .catch((e) => log("Queue error:", String(e?.message ?? e)));
});

rl.on("close", () => process.exit(0));
