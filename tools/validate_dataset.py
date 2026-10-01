#!/usr/bin/env python3
from __future__ import annotations

import base64
import gzip
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "qr2-jp40.js"
META = ROOT / "data" / "metadata.json"
HEX = re.compile(r"^0x[0-9A-F]{8}$")


def load_rows() -> list[dict]:
    text = DATA.read_text(encoding="utf-8")
    match = re.search(r'QR2_GZIP_BASE64\s*=\s*"([^"]+)"', text)
    if not match:
        raise RuntimeError("Embedded dataset string not found")
    raw = gzip.decompress(base64.b64decode(match.group(1)))
    return json.loads(raw)


def main() -> None:
    rows = load_rows()
    meta = json.loads(META.read_text(encoding="utf-8"))
    assert len(rows) == meta["qr2Entries"] == 2143

    overlaps = []
    prior = None
    for row in rows:
        assert int(row["typeStart"], 36) == row["start"]
        assert int(row["typeEnd"], 36) == row["end"]
        assert row["start"] <= row["end"]
        for key in ("item1", "item2", "flag1", "flag2", "randomTable"):
            assert HEX.match(row[key]), (row["index"], key, row[key])
        if prior and row["start"] <= prior["end"]:
            overlaps.append((prior["index"], row["index"]))
        prior = row

    stats = {
        "item2NonZero": sum(r["item2"] != "0x00000000" for r in rows),
        "flag1NonZero": sum(r["flag1"] != "0x00000000" for r in rows),
        "flag2NonZero": sum(r["flag2"] != "0x00000000" for r in rows),
        "randomTableNonZero": sum(r["randomTable"] != "0x00000000" for r in rows),
    }
    assert stats == meta["stats"], (stats, meta["stats"])

    print(f"OK: {len(rows)} QR2_INFO entries")
    print("stats:", stats)
    print(f"overlapping adjacent ranges: {len(overlaps)}")
    if overlaps:
        print("first overlaps:", overlaps[:10])


if __name__ == "__main__":
    main()
