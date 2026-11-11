"""Command line for the concrete beam and masonry wall checks.

Usage:
  python3 design_check.py rc-beam examples/rc-beam-b1.json [--out sheet.md]
  python3 design_check.py masonry-wall examples/masonry-wall-w1.json [--out sheet.md]

Writes a Markdown hand-calculation sheet and prints one summary line. Exit codes: 0 pass,
1 fail, 2 unreadable input, 3 flagged as outside the supported range. Errors never echo the
input file's content.
"""
import argparse
import json
import sys
from pathlib import Path

import masonry_wall
import rc_beam

CHECKS = {"rc-beam": rc_beam.check, "masonry-wall": masonry_wall.check}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("check", choices=sorted(CHECKS))
    parser.add_argument("input", type=Path, help="JSON file with the inputs")
    parser.add_argument("--out", type=Path, help="write the Markdown sheet here")
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Input must be a JSON object.")
    except (OSError, ValueError):
        print("Input could not be read as a JSON object.", file=sys.stderr)
        return 2
    result = CHECKS[args.check](data)
    if args.out:
        try:
            args.out.write_text(result["sheet"], encoding="utf-8")
        except OSError:
            print("The sheet could not be written to that path.", file=sys.stderr)
            return 2
    else:
        sys.stdout.write(result["sheet"])
    summary = result["status"]
    if result["flags"]:
        summary += f": {len(result['flags'])} input(s) outside the supported range"
    print(summary, file=sys.stderr)
    return {"pass": 0, "fail": 1, "flagged": 3}[result["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
