#!/usr/bin/env python3
"""
usage: pgn_hash.py [-h] [-f FILE | -p PGN]

Compute a stable SHA-256 hash of a PGN game's movetext.

The hash is computed over the normalized movetext only — headers, comments,
NAG annotations, and result markers are stripped before hashing. This makes
the hash robust against changes to PGN headers (date, player names, event)
and cosmetic edits (added comments, punctuation like ! or ?).

options:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  Path to a .pgn file
  -p PGN, --pgn PGN    Raw PGN text (as a string argument)

Output:
  Prints a single SHA-256 hex digest to stdout.

Examples:
  pgn_hash.py -f game.pgn
  pgn_hash.py -p "1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 1-0"
"""

import argparse
import hashlib
import re
import sys


def normalize_movetext(pgn: str) -> str:
    """
    Strip everything that is not part of the core move sequence, then
    normalize whitespace, so the hash is stable across:
      - Different or missing PGN headers
      - Added/removed comments  { ... }
      - NAG annotations         $1, $2, !, ?, !!, ??, !?, ?!
      - Result markers          1-0, 0-1, 1/2-1/2, *
      - Move numbers            kept — they anchor the sequence
    """
    text = pgn

    # Remove PGN headers: [Tag "Value"] — handle both newline-separated and
    # inline (e.g. when passed as a single-line string argument)
    text = re.sub(r'\[[^\]]*\]', '', text)

    # Remove comments: { ... } (non-nested, which is all PGN allows)
    text = re.sub(r'\{[^}]*\}', '', text)

    # Remove recursive annotation variations: ( ... )
    # Repeat to handle nesting up to reasonable depth
    for _ in range(5):
        text = re.sub(r'\([^()]*\)', '', text)

    # Remove NAG annotations: $N or inline punctuation !, ?, !!, ??, !?, ?!
    text = re.sub(r'\$\d+', '', text)
    text = re.sub(r'[!?]+', '', text)

    # Remove result markers
    text = re.sub(r'\b(1-0|0-1|1/2-1/2|\*)\s*$', '', text.strip())

    # Collapse whitespace
    text = ' '.join(text.split())

    return text.strip()


def compute_hash(pgn: str) -> str:
    normalized = normalize_movetext(pgn)
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute a stable SHA-256 hash of a PGN game's movetext."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-f', '--file', type=str, help='Path to a .pgn file')
    group.add_argument('-p', '--pgn', type=str, help='Raw PGN text as a string argument')
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as fh:
                pgn = fh.read()
        except OSError as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        pgn = args.pgn

    print(compute_hash(pgn))


if __name__ == '__main__':
    main()
