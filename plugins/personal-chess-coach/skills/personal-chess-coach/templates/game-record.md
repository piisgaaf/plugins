---
date: {{game date, YYYY-MM-DD, from the PGN [Date] tag (today if missing)}}
white: "{{White's name}}"
black: "{{Black's name}}"
result: "{{1-0 | 0-1 | 1/2-1/2 | *}}"
event: "{{event, or empty}}"
time_control: "{{TimeControl tag, or empty}}"
player_color: {{white | black | unknown}}
opening: "{{opening name, exactly as identify_opening returns it}}"
eco: {{ECO code, or —}}
mistake_categories: [{{categories from F08 for this game, e.g. tactical, positional; empty if F08 did not run}}]
root_causes: [{{root causes from F09 for this game; empty if F09 did not run}}]
analyses: [{{the features that contributed: f07, f08, f09, f10}}]
hash: {{the first line of pgn_hash.py --both: the game's hash}}
tags: [game-record]
created: {{YYYY-MM-DD}}
updated: {{YYYY-MM-DD}}
---
# {{White}} – {{Black}}, {{game date}}

**Result:** {{result}} · **Event:** {{event}} · **Time control:** {{time control}} · **Played:** {{White | Black | unknown}}

**Opening:** {{opening name}} ({{ECO}}) — {{1 sentence on the opening's idea, from F07}}

## In brief
{{F07's "In brief" summary}}

## Annotated game
{{F07's annotated move list, as shown in the chat. After each Blunder/Mistake-tier move, on its own line:}}
![[{{<hash>.svg — board before the move, from the player's side}}|400]]

## Mistakes
{{only if F08 ran; otherwise leave this heading empty. One entry per classified mistake:}}
### {{move number and move, e.g. 24.Rxf7??}}
- **Better was:** {{move}}
- **Type:** {{category}} — {{motif}}
- **Root cause:** {{root cause label, only if F09 ran}} — {{F09's explanation}}
- **What to practise:** {{only if F09 ran}}

## My thinking during the game
{{only if F10 ran; otherwise leave this heading empty. Dated entries, newest last:}}
**{{YYYY-MM-DD}}**
- **Move {{N}}: {{question}}** — {{the user's answer, in their own words}}. {{What it shows about this game, one sentence.}}

## PGN
```pgn
{{the PGN as F07 analysed it}}
```

## My notes
