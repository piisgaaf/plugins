# 1.  F37 — Keep a Record of Every Analyzed Game

## 1.1.  User question

> "Save this game."
> "Keep a record of this analysis."
> (or: "yes" to the coach's offer "Save a record of this game?" at the end of the analysis)

## 1.2.  Capability unlocked

Every game the user has analyzed can be saved as a self-contained Markdown note in their working folder: the game details, the opening, the annotated move list with boards at the critical moments, and, if they were discussed in the same conversation, the mistakes with their type and root cause and the user's own thoughts during the game.

A game record holds only what was found about **this game**. It never copies what the Player Profile says at that moment (totals, shares, recurring weaknesses, comparisons with earlier games). This keeps the records an independent source: a fresh profile can later be built from only the records of a chosen period, so old habits stop lingering. That rebuild is a separate feature and only ever happens when the user asks for it explicitly; F37 never builds or changes a profile.

## 1.3.  Validation

A correct implementation demonstrates:

- After F07, saving creates `Game_Analysis/<record name>.md`, its boards in `Game_Analysis/boards/`, and the overview table (if missing)
- Mistake types and root causes (F08, F09) and the user's thoughts (F10) from the same conversation are in the record; nothing from the profile is
- Saving the same game again (also in a later conversation) updates the existing record instead of creating a duplicate
- Text the user wrote under "My notes" is never changed
- Without a working folder nothing is offered or written

---

## 1.4.  Where the records live

All paths are relative to the **working folder**: the folder the user mounted (the Cowork project folder, which may be an Obsidian vault or a subfolder of it).

```
Game_Analysis/
  Game_Analysis.base                              ← overview table (created once)
  boards/
    5f1e9a02.svg                                  ← board from White's side
    77c03b4d-black.svg                            ← board from Black's side
  2026-11-15 Pieter - Jansen.md                   ← one record per game
```

Boards are named by the script after the position itself (show-board.md §1.5), so they never clash and the same position always uses the same file.

Templates for both files are in this skill's `templates/` folder: [game-record.md](../templates/game-record.md) and [Game_Analysis.base](../templates/Game_Analysis.base). Always build records from these templates; do not invent another layout.

## 1.5.  MCP tools used

| Tool | When |
|---|---|
| Show the board as an **SVG image** ([show-board.md](../rendering/show-board.md)) | For each Blunder/Mistake-tier move of the F07 analysis — save its board in `Game_Analysis/boards/` (show-board.md §1.5) |
| `scripts/pgn_hash.py` | Always — the game's hash finds an existing record |

No engine analysis: F37 saves what the conversation already found.

---

## 1.6.  When to offer saving

Game records need a working folder ([SKILL.md §1.7.1](../SKILL.md#171--working-folder-decide-once-per-conversation)). Without one, never offer saving; if the user asks to save, say in one line that game records need Cowork with a project folder ([SKILL.md §1.7.3](../SKILL.md#173--without-a-working-folder)), and write nothing.

F37 assumes that [F07](../r01-understand-my-chess/f07-annotate-game.md) annotated the game earlier in this conversation. If it did not (e.g. only F05 or F06 ran, or the user pastes a game and asks straight away to save it), say so in one line and run F07 first: *"I'll annotate the game first, then save the record."*

- At the end of the analysis — as the last of F07's next steps — ask once: **"Save a record of this game?"**
- After F08, F09 or F10 added something about the same game: if the record was saved in this conversation, ask **"Add this to the game record?"**; if the user declined earlier, do not ask again.
- If the user says "save this game" (or similar) at any time, save without asking.
- Never save without the user's yes.

---

## 1.7.  Workflow

### 1.7.1.  Step 1 — Collect the facts

Gather from the conversation (do not run new analysis):

- **Game details** from the PGN headers (`load_pgn`'s `tags`): White, Black, result, event, time control, and the game date from `[Date]`. If the date is missing or incomplete (`????.??.??`), use today's date (`YYYY-MM-DD`; from the conversation context, or by running `date +%F`), as F08 does.
- **Which side the player had:** from the `player` section of the profile when it is known without asking (SKILL.md §1.7.2), or from what the user said. Otherwise `unknown`.
- **Opening** name and ECO code, as F07 Step 2 found them.
- **F07's** annotated move list and its **In brief** summary, exactly as shown in the chat.
- **Mistakes**, if F08 ran in this conversation: per classified mistake, the move, what was played and what was better, its category and motif. Take only this game's mistakes; leave out the totals, shares, severity and recurring weaknesses of F08's table.
- **Root causes**, if F09 ran: per explained mistake, the root cause, the explanation and "What to practise".
- **Thoughts during the game**, if F10 ran: each question, the user's answer in their own words, and what it shows about this game. Leave out the Thinking Profile summary (tendencies, confidence) and sentences that compare with earlier sessions.
- **The PGN** as F07 analysed it.
- **Hash:** run `python3 <skill-folder>/scripts/pgn_hash.py -p "<PGN>"` (the skill folder is the folder that contains `SKILL.md`, as in show-board.md §1.3).

**Never write anything from the profile into the record**, and never phrase an entry in terms of earlier games ("again", "as before", "the third time"). The record must read the same whatever the profile says.

### 1.7.2.  Step 2 — Build the name

`<game date> <White> - <Black>`, e.g. `2026-11-15 Pieter - Jansen`. Leave out a name that is unknown; with neither name, use `<game date> Game <first 8 characters of the hash>`.

Remove characters that Obsidian forbids or that break links: `: * " \ / < > | ? # ^ [ ]`, and also `+` and `!`. Collapse double spaces.

### 1.7.3.  Step 3 — Find an existing record

Search `Game_Analysis/` for a record whose `hash` frontmatter equals the game's hash.

- **Found** → Step 5 (update). Use that record, even if its name differs from what Step 2 produced.
- **Not found** → Step 4 (create). If a different game already uses the Step 2 name, append ` (2)`, ` (3)`, … until the name is free.

### 1.7.4.  Step 4 — Create

0. **Folder:** create `Game_Analysis/` if it does not exist, with a command (`mkdir -p "<working folder>/Game_Analysis"`), not by relying on the file tool to create parent folders. (`Game_Analysis/boards/` is created by the script.)
1. **Overview table:** if `Game_Analysis/Game_Analysis.base` does not exist, copy [templates/Game_Analysis.base](../templates/Game_Analysis.base) there unchanged.
2. **Boards:** for each Blunder/Mistake-tier move of the F07 analysis, save the board of the position before the move (`fen_before`) in `Game_Analysis/boards/` ([show-board.md §1.5](../rendering/show-board.md)), from the player's side (`--flip` when the player had Black; White's side when unknown). Use the file name the script prints.
3. **Record:** create `Game_Analysis/<name>.md` from [templates/game-record.md](../templates/game-record.md). Put each board embed (`![[<file name>|400]]`) on the line after its move in the annotated game. Fill the "Mistakes" and "My thinking during the game" sections only with what F08, F09 and F10 found in this conversation; leave them as an empty heading otherwise. Leave "My notes" empty.

### 1.7.5.  Step 5 — Update

1. **Annotated game and In brief:** if already filled, keep them as they are. Do not add a second annotated move list.
2. **Mistakes:** add a mistake that is not in the record yet. For a mistake already there, add only what is missing (e.g. its root cause). Never rewrite an earlier entry.
3. **My thinking during the game:** append the new questions and answers as a dated entry (`**YYYY-MM-DD**`).
4. **Frontmatter:** add new values to `mistake_categories`, `root_causes` and `analyses`, and set `updated` to today. Keep everything else.
5. **Boards:** run the script again for each board in the record. It writes the same file name for the same position, so this only repairs a missing file and never changes an embed.
6. **Never touch "My notes"**, and never delete a record, a section or an entry.

### 1.7.6.  Step 6 — Confirm

Tell the user in one line what happened, with the path, e.g.:

> Saved to `Game_Analysis/2026-11-15 Pieter - Jansen.md` (new record).
> Updated `Game_Analysis/2026-11-15 Pieter - Jansen.md`: added the root cause of 24.Rxf7.

---

## 1.8.  Quality checklist

- [ ] The user said yes (or asked to save) before anything was written
- [ ] F07 annotated this game before the record was written
- [ ] An existing record was searched for by `hash` before creating one
- [ ] The record follows the template; its name contains no forbidden characters
- [ ] `date` is the game date from the PGN (today only when the PGN has none)
- [ ] Nothing from the Player Profile is in the record: no totals, shares, severity, recurring weaknesses or comparisons with earlier games
- [ ] Each Blunder/Mistake-tier move has a board from the player's side, stored in `Game_Analysis/boards/` under the name the script printed
- [ ] Earlier entries are unchanged; "My notes" is untouched
