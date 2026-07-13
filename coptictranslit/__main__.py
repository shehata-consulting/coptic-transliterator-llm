#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Command-line interface: transliterate a Coptic text file (or stdin) to Latin script."""

import argparse
import sys
from pathlib import Path

from . import __version__, translit_with_warnings


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="coptictranslit",
        description="Transliterate Coptic text to Latin script "
        "(Greco-Bohairic phonetic rules).",
    )
    parser.add_argument(
        "path",
        nargs="?",
        help="UTF-8 text file containing Coptic text; omit to read from stdin",
    )
    parser.add_argument(
        "-o", "--output",
        help="write the result to this file instead of stdout",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    args = parser.parse_args(argv)

    if args.path:
        text = Path(args.path).read_text(encoding="utf-8")
    else:
        text = sys.stdin.read()

    result, unmapped = translit_with_warnings(text)
    if unmapped:
        print(
            f"Warning: unmapped Coptic characters passed through: {unmapped}",
            file=sys.stderr,
        )

    if args.output:
        Path(args.output).write_text(result, encoding="utf-8")
    else:
        print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
