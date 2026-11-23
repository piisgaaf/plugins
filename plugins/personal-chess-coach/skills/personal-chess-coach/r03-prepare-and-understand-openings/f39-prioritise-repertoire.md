# 1.  F39 — Prioritise My Repertoire

## 1.1.  User question

> "Split my White repertoire into major, minor and rare lines."
> "Which lines of my repertoire should I prepare first?"
> "Where are the holes in my repertoire?"
> "Should I split this chapter?"
> "Update my repertoire overview."

## 1.2.  Capability unlocked

The user prepares efficiently. Their repertoire (one or more PGN files per side, each game a **chapter** named by its `[Event]` tag) is split into **major**, **minor** and **rare** lines by how often the positions come up in games at the player's rating band. The overview shows the **holes**: common opponent replies the repertoire has no answer to. It also says which chapters to **split** into a major/minor part and a rare part. The result is three Markdown files per side in `Repertoire/`, with the coach's advice at the bottom of each.

## 1.3.  Validation

A correct implementation demonstrates:

- Frequencies come only from `get_opening_continuations`, queried by SAN move list from the start position
- Transpositions merge: a position reached in two chapters or by two move orders is one position, with the highest reach
- Every chapter (`[Event]`) appears in exactly one of the three files, classed by the reach of its own line
- Holes list replies reached in ≥ 1% of games that have no answer and do not transpose straight into the repertoire
- A split is proposed only when the lower-class side variations are ≥ 40 plies and ≥ 50% of the chapter; a side variation more common than the main line is flagged
- A rerun replaces the tables but keeps everything below `<!-- coach notes -->`
- Work files stay in a temporary directory; only the three reports are written to the working folder, after the user's yes
- The PGN files themselves are never changed

---

## 1.4.  Where the files live

All paths are relative to the **working folder** ([SKILL.md §1.7.1](../SKILL.md#171--working-folder-decide-once-per-conversation)).

```
Repertoire/
  repertoire_white_major.md
  repertoire_white_minor.md
  repertoire_white_rare.md
  repertoire_black_major.md      ← once the Black repertoire is analysed
  …
```

The repertoire PGN files stay where the user keeps them; F39 only reads them. Their paths come from the profile's `player.repertoire` ([SKILL.md §1.7.5](../SKILL.md#175--player-details)) when it is set and the profile file is known without asking ([SKILL.md §1.7.2](../SKILL.md#172--when-to-resolve-the-profile)). Otherwise, look for `*.pgn` files under a folder named `repertoire` (any case) in the working folder and ask once which files belong to which side.

The script's work files (`tree.json`, `results.json`, `chapters.json`) go in a temporary directory (e.g. from `mktemp -d`), never in the working folder. Keep the same directory for the whole run, so the lookups are not repeated.

## 1.5.  Tools used

| Tool | When |
|---|---|
| [scripts/repfreq.py](../scripts/repfreq.py) | Always: `tree` (merge the PGNs), `frontier` (what to look up next), `add` (store the lookups), `report` (write the three files). Run it with `python3 -I` and its absolute path: `<skill-folder>` is the folder that contains `SKILL.md`, not the current directory. Exit code 3 means python-chess is missing: run `pip install chess` and retry |
| `get_opening_continuations` | For each position `frontier` lists: `moves` = the SAN moves it prints (as a list, from move 1; never a FEN you built yourself, [SKILL.md §1.2.7](../SKILL.md#127--fen-integrity)), `ratings` and `speeds` from the band (Step 1), `limit: 15` so all replies of ≥ 1% come back |

**Lichess only through the MCP tool.** Never fetch the Lichess explorer directly (`curl`, Python, a web fetch): that is the user's rule, and the code sandbox usually cannot reach it anyway. If `get_opening_continuations` fails (`found: false`), retry once; if it keeps failing, stop the loop, say so in one line and offer to finish later. Do not write reports from an incomplete loop without saying which lines are missing.

No engine analysis and no board images: this feature is about frequencies, not evaluations.

---

## 1.6.  Method

These rules are built into the script; know them to explain the result.

1. **Merge.** All PGN files of one side become one tree of positions, keyed by position (EPD), so transpositions merge. Each position keeps its sources (`file#n: Event`). The script ignores `[Variant]` tags: Scid exports often misuse them for the opening name, and python-chess would read them as a chess variant.
2. **Reach.** The start position has 100%. The player's own moves pass the reach on in full (two own alternatives both get it). An opponent reply gets reach × its Lichess frequency. Over several paths, the highest reach counts.
3. **Pruning.** Only opponent-to-move positions with reach ≥ 1% are looked up. The loop is frontier → lookups → add, until the frontier is empty.
4. **Classes** (share of the player's games with that side): **major** ≥ 5%, **minor** 1–5%, **rare** < 1%.
5. **Holes.** An opponent reply with reach ≥ 1% that has no answer in the files and does not transpose straight into the tree.
6. **Chapter class** is the reach of the first position that **only** that chapter covers (its own line). Each `[Event]` name appears exactly once over the three files.
7. **Split advice.** Opponent side variations off a chapter's main line, with reach and plies. A split is proposed when the side variations of a lower class are ≥ 40 plies **and** ≥ 50% of the chapter. A side variation that is more common than the main line is flagged in the Note column.

---

## 1.7.  Workflow

### 1.7.1.  Step 1 — Side, files and band

- **Side:** White or Black, from the request. If the user has both and did not say, ask once.
- **Files:** as in §1.4. If there are none for that side, say so in one line and stop.
- **Band:** `player.repertoire.ratings` and `.speeds` when set. Otherwise the two Lichess buckets around `player.rating` (e.g. 1862 → `[1800, 2000]`) with `["rapid", "classical"]`; without a rating, `[1800, 2000]`. Lichess ratings run higher than OTB ratings: if the rating is an OTB rating, say in one line that the next band up (e.g. `[2000, 2200]`) may fit better, and use the user's choice.

### 1.7.2.  Step 2 — Build the tree

```bash
W=$(mktemp -d)
python3 -I <skill-folder>/scripts/repfreq.py --work "$W" tree w "<file1.pgn>" "<file2.pgn>"
```

`w` or `b` is the player's side. Parse errors are printed per chapter: mention them to the user, they usually mean a broken move in the PGN.

### 1.7.3.  Step 3 — Look up the frontier

Repeat until `frontier` prints `to look up 0`:

1. `python3 -I <skill-folder>/scripts/repfreq.py --work "$W" frontier` lists the positions to look up, with reach and SAN moves.
2. Call `get_opening_continuations` for each (several calls in one turn are fine).
3. Store them in one call, a pair of arguments per position: the moves as printed, then the replies as `san:frequency_pct`:
   ```bash
   python3 -I <skill-folder>/scripts/repfreq.py --work "$W" add "d4 d5 c4" "e6:38.2 c6:27.1 dxc4:14.0 Nf6:5.3"
   ```
   `add` checks every move and stops on a mistyped one: fix it and retry.

A full White repertoire takes a few dozen lookups. Tell the user briefly how far the loop is between rounds (*"28 lines looked up, 9 to go"*).

### 1.7.4.  Step 4 — Write the reports

Before writing, say in one line what will happen (*"I'll write the three White files to `Repertoire/`; your coach notes in them are kept."*) and wait for the user's yes, unless they asked for the update. Then:

```bash
mkdir -p "<working folder>/Repertoire"
python3 -I <skill-folder>/scripts/repfreq.py --work "$W" report "<working folder>/Repertoire" --band "1800–2000, rapid and classical"
```

The script prints the count per class and checks that every Event is listed exactly once. If it reports Events not exactly once, or duplicate Event names, tell the user: two chapters with the same `[Event]` cannot be told apart.

After writing, check that each file is really there and changed (`md5sum` or `ls -l`): a file tool may report success without the new content arriving.

### 1.7.5.  Step 5 — Coach notes

The script writes only tables. Below `<!-- coach notes -->` in each file goes the coach's advice, from the tables and chess knowledge (read `chapters.json` in the work directory for the side variations):

- **Major file:** *Where preparation pays off most*: the biggest holes first, with a suggested answer that fits the existing repertoire. Major trunks that the files cover only through lower chapters (e.g. the QGA after 3.e4, the Four Pawns after 5.f4) are described as lines, without Event names, so each Event still appears in one file only.
- **Minor file:** which minor chapters to review and which holes to fill next; the split proposals in plain words.
- **Rare file:** a short note that these lines can be skipped until the major and minor lines are solid, plus anything that is a trap or a forcing line worth knowing anyway.

On a rerun, the existing notes are kept. Read them, then **add** what changed (new holes, a chapter that moved class) under a dated heading (`### Update YYYY-MM-DD`). Never rewrite or remove the user's own text there.

Keep in mind when advising: a major main line drops below 5% within a few moves, so filling holes usually pays off more than deepening the major chapters. Actually splitting a chapter in the PGN (a new `[Event]` per part) is not part of this feature; do it only when the user asks, and then in a new file, never by changing the original.

### 1.7.6.  Step 6 — Summary

In the chat, give a short summary, not the tables:

> *White, 1800–2000 rapid+classical, 45 lookups: 3 major chapters, 9 minor, 13 rare. Biggest holes: 1…e6 (8.2%), 2.c4 Nf6 after 1…d5 (4.9%). Split proposed for the Slav and Nimzo chapters. Saved to `Repertoire/repertoire_white_{major,minor,rare}.md`.*

Then offer the next step once: *"Shall I also check these lines with the engine and against your games?"* A yes routes to [F29](f29-learn-my-repertoire.md), which reuses this work directory.

---

## 1.8.  Practical notes

- **Scid export can hang on macOS.** Scid and scidCommunity may hang in the PGN export file dialog (likely the shared Tcl/Tk dialog). If the user is stuck there, say that the feature only needs a PGN file, from any program; Lichess studies export as PGN from the study's share menu.
- **Line endings and encoding** do not matter to the script; a UTF-8 PGN with LF or CRLF works.
- **Comments and NAGs** in the PGN are ignored; only the moves count.

---

## 1.9.  Quality checklist

- [ ] All frequencies came from `get_opening_continuations` with a SAN move list, at the band the user agreed to
- [ ] The frontier loop ran until nothing was left to look up, or the user was told which lines are missing
- [ ] Work files stayed in a temporary directory; only `Repertoire/repertoire_<side>_*.md` was written, after the user's yes
- [ ] Every Event appears exactly once over the three files (the script's check passed)
- [ ] Coach notes were added below `<!-- coach notes -->`; existing notes were kept unchanged
- [ ] The PGN files were not changed
- [ ] The chat shows a short summary with the biggest holes and the split proposals, not the tables
