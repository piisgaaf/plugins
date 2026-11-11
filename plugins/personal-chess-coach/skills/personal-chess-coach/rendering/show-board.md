# 1.  Showing a board

This file is the **only** place that decides how a position is shown to the user. Feature files only say "show the board" and link here. Follow this file every time a board is shown.

## 1.1.  Showing vs. checking

There are two different reasons to look at a board. Keep them apart:

| Purpose | How |
|---|---|
| **Showing** a position to the user | This file: an SVG image by default, a text board only as the fallback (§1.4) |
| **Checking** a position yourself (verifying where pieces stand before reasoning about it) | Call `fen_to_board` and read its output. Do **not** show that text board to the user, unless the text fallback is in use |

## 1.2.  Decide once per conversation

Before the first board of the conversation, decide from your own tool list. Never ask the user.

**Use SVG** (the default) when both are true:

1. You can run code (any code-execution or shell tool).
2. You can show the result, in order of preference:
   - `show_widget` (visualize): shows the image inline in the answer.
   - `present_files` / `SendUserFile`: shows the image as a file.

**Use the text fallback** (§1.4) only when one of these is missing, or when generating the SVG fails (§1.3, step 3).

Keep the decision for the rest of the conversation. Do not switch back and forth between SVG and text boards.

## 1.3.  Render the SVG

1. **Find the script.** It is `scripts/fen_to_svg.py` inside this skill's folder, which is the folder that contains `SKILL.md`. Use its absolute path, built from the path you read `SKILL.md` from. Do not rely on the current working directory: it is usually not the skill folder.
2. **Run it.** Always quote the FEN: it contains spaces.

   ```
   python3 <skill-folder>/scripts/fen_to_svg.py -s 400 -f "<FEN>" -o <output-file>
   ```

   - With `show_widget`: write to any writable path (e.g. `/tmp/board-17b.svg`), then read the file and pass its SVG markup to `show_widget`.
   - With `present_files` / `SendUserFile`: write to `/mnt/user-data/outputs/<name>.svg` and present that file.
   - Give each position its own file name (e.g. by move number and side: `board-17b.svg`), so earlier boards stay valid.
   - **Orientation:** add `--flip` to show the board from Black's side when the discussion is about Black's plan or Black's point of view. Otherwise show it from White's side.
3. **If it fails:**
   - Exit code 3 (message: `python-chess is not installed`): the `python-chess` package is missing. Run `pip install chess`, then run the script once more.
   - Any other failure, or the retry fails: use the text fallback (§1.4) for the rest of the conversation, and say why once.
4. **Show it** with the tool chosen in §1.2. Never paste raw SVG text into the chat.

## 1.4.  Text fallback

Call `fen_to_board` and show its diagram in a code block **exactly as the tool returned it**. Never retype, redraw or edit the board, and never add annotations inside the diagram: copying it by hand introduces errors (pieces on wrong squares). Put any remark, such as whose move it is, in the text outside the code block.

Say once per conversation why a text board is shown, in one short line:

- SVG unavailable (no code execution or no display tool): "(Text board: turn on code execution in Claude's settings to see board images.)"
- SVG failed: "(Text board: the board image could not be generated — <short reason>.)"

If the user explicitly asks for an SVG while SVG is unavailable, say it can't be shown here and keep using the text board.

## 1.5.  Saving a board with a note

When a feature writes a note (e.g. [F36](../r01-understand-my-chess/f36-opening-notebook.md)), its boards are saved as files in the feature's board folder (for F36: `Openings/boards/`) and embedded in the note. This is in addition to showing the board in the chat per §1.2.

- **SVG available:** run the script as in §1.3, but with `-d <board folder>` instead of `-o`, using the working folder's path as you access it. Add `--flip` for Black's side. The script names the file after the position (`<hash>.svg`, or `<hash>-black.svg` with `--flip`), creates the folder if needed, and **prints the file name**. Embed exactly that name in the note: `![[<printed name>|400]]`. Never make up or change a board file name.
- **SVG unavailable or failed:** put the `fen_to_board` text board in the note, in a code block, instead of the embed.
