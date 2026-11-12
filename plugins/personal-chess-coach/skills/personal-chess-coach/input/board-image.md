# 1.  Reading a FEN from a board picture or diagram

This is the only situation in which a FEN may be written by hand (SKILL.md §1.2.7).
A FEN read from a picture must pass every step below before any analysis uses it.

## 1.1.  Procedure

1. **Read the position.** Go rank by rank from rank 8 to rank 1, files a to h,
   and write the piece placement. Check the board's orientation first
   (coordinate labels, or the position of the kings and pawns).
2. **Validate.** Call `validate_fen`. If it is invalid, fix the reading and repeat.
3. **Render and compare.** Render the FEN with `scripts/fen_to_svg.py`
   (see [rendering/show-board.md](../rendering/show-board.md)), view the rendered
   image, and compare it with the user's picture or diagram **square by square**: all 64 squares,
   including empty ones. If any square differs, correct the FEN and go back to step 2.
4. **Show the rendered board** to the user, so they can confirm it too.
5. **State what the picture cannot show** and what you assumed for each field:
   - side to move (from the user's message if given, otherwise ask)
   - castling rights (assume available only if king and rook are on their home squares)
   - en passant square: assume none, but if the last move could have been a double
     pawn push that an enemy pawn could capture en passant, name that capture and
     say it would also be legal
   - halfmove clock and move number (estimate from development, or use 0 / 1)

## 1.2.  Rules

- Never use the FEN for analysis before steps 1–5 are complete.
- If the user corrects any field, take the user's version, then repeat steps 2–4.
- After it passes, the FEN counts as given by the user: later positions are derived
  with `apply_move` only (§1.2.7).
- If the picture is unreadable (cropped, blurred, pieces hidden), say which squares
  you cannot read and ask, instead of guessing.
