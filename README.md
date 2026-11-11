# Claude plugins

A [Claude plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces)
with plugins by Pieter Rijken. The marketplace is called `piisgaaf`.

| Plugin | What it does |
|--------|--------------|
| `personal-chess-coach` | A personal chess coach powered by Stockfish. It analyzes positions and games, explains moves, identifies openings, classifies mistakes, and builds a player profile over time. |

## Installing

### Claude Desktop (Cowork)

1. Open the plugin settings and choose **Add marketplace**.
2. Enter `https://github.com/piisgaaf/plugins`.
3. Install **personal-chess-coach** from the `piisgaaf` marketplace.

### Claude Code

```
/plugin marketplace add piisgaaf/plugins
/plugin install personal-chess-coach@piisgaaf
```

## Updates

A new version is picked up when the marketplace is refreshed. In Claude Code,
run `/plugin marketplace update piisgaaf`, or turn on auto-update for the
`piisgaaf` marketplace under `/plugin` → **Marketplaces**.

## Requirements

The chess coach does not contain the chess engine. It connects to a separate
chess-engine server (Stockfish behind an MCP server) that must be running and
reachable from your computer, for example on the home network. That server is
not part of this plugin.

The plugin's connector is a small Node.js script, so Claude Code needs `node`
on its `PATH`.

## How this was built

These plugins were developed by Pieter Rijken with the help of Claude Code
(Anthropic). The design, the chess-coaching approach and every change were
directed and reviewed by the author.

## License

[PolyForm Noncommercial License 1.0.0](LICENSE): free to use, change and share
for any noncommercial purpose. Commercial use is not allowed without the
author's permission.
