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
progress) and the opening notebook need **Cowork with a project folder**: that
is where your player profile and notes are saved. The first time you use one
of those features, the coach asks which player profile to use, or offers to
create one for you. In a normal chat it can still classify the mistakes in a
game, but nothing is saved.

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
