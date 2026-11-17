# Personal Chess Coach

A personal chess coach for Claude, powered by the Stockfish chess engine.

## What it does

The coach answers *"Why?"* rather than *"What?"*. Instead of just finding the
best move, it explains plans, motifs and mistakes, and it builds a player
profile over time so it gets to know you as a player.

It can:

- analyze a position and explain the best move
- compare candidate moves
- identify openings and their typical plans
- analyze full games (PGN)
- show the critical moments of a game, with coach-style comments
- classify your mistakes and explain where they come from
- learn how you think and play

## Usage

Just talk to Claude:

- "Analyze this position: `r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4`"
- "Why is Ng5 the best move here?"
- "Compare Nf3 and d4 in this position"
- "Analyze my game" (then paste a PGN)
- "What kind of mistakes do I keep making?"

Analyzing positions, openings and games works in a normal chat in Claude
Desktop. Getting to know you as a player (your mistakes, style, weaknesses and
progress), the opening notebook and the records of your analyzed games need
**Cowork with a project folder**: that is where your player profile and notes
are saved. The first time you use one
of those features, the coach asks which player profile to use, or offers to
create one for you. In a normal chat it can still classify the mistakes in a
game, but nothing is saved.

## Project instructions (Cowork)

In Cowork, give the project these instructions (in the project's settings),
with your profile's filename filled in:

```markdown
# Chess coaching

For every chess question (a position, a FEN, a PGN, a move, an opening, a game,
my mistakes, my progress) use the **personal-chess-coach** skill: read its
SKILL.md first and follow the feature file it routes to. Do this before you
answer, also for questions that look simple.

Never work out moves, legality or evaluations yourself. Use the chess-engine
tools for that. Show boards the way the skill says.

My player profile is `<name>.yaml` in the root of the project folder. Take my
names, usernames, rating, games folder, library and study plan from its
`player` section.
```

Your details go in the `player` section at the top of your player profile, not
in the instructions. Every field except `name` is optional, and the coach
offers to fill them in the first time it classifies your mistakes:

```yaml
player:
  name: "<name>"
  aliases: ["<alias 1>", "<alias 2>"]   # your names in PGN files
  usernames:
    lichess: "<lichess username>"
    chess_com: "<chess.com username>"
  rating: <rating>
  games_folder: "<games folder>"         # your PGN files
  library: "<books file>.md"             # your chess books
  study_plan: "<study plan file>.md"
```

With these, the coach knows which side you played in a game, picks opening
statistics for your rating, and finds your games in the folder. Your library
and study plan are kept in the profile but not used yet.

Do not add instructions about how to show boards: project instructions take
precedence over the coach, and it would stop showing board images.

## What it needs

The coach does its analysis through a chess-engine server (an MCP server).
That server is not part of this plugin: it must be running and reachable
from your computer for the coach to work.

## How this was built

This project was developed by Pieter Rijken with the help of Claude Code
(Anthropic). The design, the chess-coaching approach and every change were
directed and reviewed by the author.

## License

[PolyForm Noncommercial License 1.0.0](LICENSE): free to use, change and share
for any noncommercial purpose. Commercial use is not allowed without the
author's permission.
