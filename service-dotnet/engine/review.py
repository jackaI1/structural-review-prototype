"""Independent synthetic workflow engine. No section sizing or code compliance."""
import hashlib
import io
import json
import math
from pathlib import Path
import re
import sys
import warnings

from pypdf import PdfReader

SCHEDULE = re.compile(
    r"BEAM\s+([A-Za-z][A-Za-z0-9_-]{0,31})\s+"
    r"SPAN_M=(\S+)\s+TRIBUTARY_M=(\S+)\s+LOAD_KPA=(\S+)"
)


def review(data):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            reader = PdfReader(io.BytesIO(data), strict=True)
            if reader.is_encrypted or not 1 <= len(reader.pages) <= 50:
                raise ValueError("Use an unencrypted PDF of 1 to 50 pages.")
            pages = [page.extract_text() or "" for page in reader.pages]
    except Exception as exc:
        raise ValueError("Cannot read the drawing PDF.") from exc

    members = []
    identifiers = set()
    for page_number, text in enumerate(pages, 1):
        matches = list(SCHEDULE.finditer(text))
        if len(matches) != len(re.findall(r"\bBEAM\b", text)):
            raise ValueError("Incomplete synthetic member schedule.")
        for match in matches:
            identifier = match[1]
            span, width, load = (float(value) for value in match.groups()[1:])
            if any(not math.isfinite(value) or not 0 < value <= 100
                   for value in (span, width, load)):
                raise ValueError("Synthetic schedule values must be in (0, 100].")
            if identifier in identifiers or len(members) >= 200:
                raise ValueError("Duplicate member ID or more than 200 members.")
            identifiers.add(identifier)
            line_load = width * load
            members.append({
                "id": identifier, "page": page_number, "spanM": span,
                "tributaryM": width, "loadKpa": load,
                "lineLoadKnPerM": round(line_load, 6),
                "momentKnM": round(line_load * span ** 2 / 8, 6),
                "reactionKn": round(line_load * span / 2, 6),
            })
    messages = ["Illustrative simply supported uniform-load calculations only; "
                "no section sizing, load combinations or code-compliance checks."]
    if not members:
        messages.append("No synthetic schedule found; engineer input is required.")
    return {
        "schemaVersion": 1, "mode": "synthetic-demo",
        "sha256": hashlib.sha256(data).hexdigest(), "pageCount": len(pages),
        "members": members, "requiresEngineerApproval": True,
        "warnings": messages,
    }


def main():
    try:
        result = review(Path(sys.argv[1]).read_bytes())
        print(json.dumps(result, allow_nan=False))
        return 0
    except Exception:
        # Never include uploaded text or local paths in process output.
        print("Drawing could not be reviewed.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
