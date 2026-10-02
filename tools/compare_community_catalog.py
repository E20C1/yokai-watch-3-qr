#!/usr/bin/env python3
from __future__ import annotations

import base64
import gzip
import json
import re
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCAL_DATA = ROOT / "data" / "qr2-jp40.js"
OUT_DATA = ROOT / "data" / "community-yu08083.json"
OUT_COMPARE = ROOT / "data" / "community-comparison.json"
OUT_DOC = ROOT / "docs" / "COMMUNITY_COMPARISON.md"
UPSTREAM_REPO = "Yu08083/Yokai2-QR"
UPSTREAM_PATH = "yw3/catalog.json"
RAW_URL = f"https://raw.githubusercontent.com/{UPSTREAM_REPO}/main/{UPSTREAM_PATH}"
API = f"https://api.github.com/repos/{UPSTREAM_REPO}"
ZERO = "0x00000000"


def get_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "E20C1-yw3-qr-research"})
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.load(response)


def load_local_rows() -> list[dict]:
    text = LOCAL_DATA.read_text(encoding="utf-8")
    match = re.search(r'QR2_GZIP_BASE64\s*=\s*"([^"]+)"', text)
    if not match:
        raise RuntimeError("Embedded JP4.0 dataset not found")
    return json.loads(gzip.decompress(base64.b64decode(match.group(1))))


def dec_hex(value: str) -> int:
    return int(value, 16)


def local_reward_key(row: dict) -> str:
    # Upstream reward_key order is the QR2_INFO payload fields after Start/End.
    values = [
        dec_hex(row["item1"]), dec_hex(row["item2"]),
        dec_hex(row["flag1"]), dec_hex(row["flag2"]),
        int(row["u1"]), int(row["u2"]), int(row["qty1"]), int(row["qty2"]),
        dec_hex(row["randomTable"]),
    ]
    return ":".join(map(str, values))


def upstream_key(row: dict) -> str:
    if row.get("reward_key"):
        return str(row["reward_key"])
    grants = row.get("grants") or []
    item1 = int(row.get("item_id") or (grants[0]["item_id"] if grants else 0))
    item2 = int(grants[1]["item_id"]) if len(grants) > 1 else 0
    qty1 = int(grants[0].get("quantity", 1)) if grants else 1
    qty2 = int(grants[1].get("quantity", 1)) if len(grants) > 1 else 1
    return ":".join(map(str, [item1, item2, 0, 0, 0, 0, qty1, qty2, int(row.get("random_table") or 0)]))


def tree_blob_sha(commit_sha: str) -> str | None:
    tree = get_json(f"{API}/git/trees/{commit_sha}?recursive=1")
    for entry in tree.get("tree", []):
        if entry.get("path") == UPSTREAM_PATH:
            return entry.get("sha")
    return None


def type_map(rows: list[dict], key_fn, profile_filter: bool = False):
    out: dict[int, list[tuple[str, dict]]] = defaultdict(list)
    for row in rows:
        if profile_filter and row.get("profile") not in (None, "yw2"):
            continue
        key = key_fn(row)
        for number in range(int(row["start"]), int(row["end"]) + 1):
            out[number].append((key, row))
    return out


def compact_reward(row: dict, key: str) -> dict:
    return {
        "reward_key": key,
        "label": row.get("reward_group") or row.get("label") or row.get("name") or "名称未確認",
        "name": row.get("name") or row.get("label") or "名称未確認",
        "item_id": row.get("item_id", 0),
        "grants": row.get("grants") or [],
        "random_table": row.get("random_table", 0),
    }


def main() -> None:
    local = load_local_rows()
    catalog = get_json(RAW_URL)
    upstream = [r for r in catalog.get("rewards", []) if r.get("profile") in (None, "yw2")]
    if not upstream:
        raise RuntimeError("Upstream update reward table is empty")

    head = get_json(f"{API}/commits/main")
    commit_sha = head["sha"]
    blob_sha = tree_blob_sha(commit_sha)

    local_map = type_map(local, local_reward_key)
    upstream_map = type_map(upstream, upstream_key, profile_filter=True)

    all_types = sorted(set(local_map) | set(upstream_map))
    type_counts = {"exact": 0, "multiple_candidate": 0, "community_only": 0, "ours_only": 0, "conflict": 0}
    type_conflicts = []
    for number in all_types:
        ours = {x[0] for x in local_map.get(number, [])}
        theirs = {x[0] for x in upstream_map.get(number, [])}
        if not ours:
            cls = "community_only"
        elif not theirs:
            cls = "ours_only"
        elif len(ours) > 1 or len(theirs) > 1:
            cls = "multiple_candidate" if ours & theirs else "conflict"
        elif ours == theirs:
            cls = "exact"
        else:
            cls = "conflict"
        type_counts[cls] += 1
        if cls in ("conflict", "multiple_candidate") and len(type_conflicts) < 100:
            type_conflicts.append({"type_dec": number, "type": base36(number), "ours": sorted(ours), "community": sorted(theirs), "classification": cls})

    local_keys = {local_reward_key(r) for r in local}
    upstream_keys = {upstream_key(r) for r in upstream}
    exact_keys = local_keys & upstream_keys

    # Collapse upstream update rewards to one human-readable record per reward key.
    reward_by_key = {}
    for row in upstream:
        key = upstream_key(row)
        current = reward_by_key.get(key)
        candidate = compact_reward(row, key)
        if current is None or (current["label"] == "名称未確認" and candidate["label"] != "名称未確認"):
            reward_by_key[key] = candidate

    local_item_ids = {
        dec_hex(r[field])
        for r in local for field in ("item1", "item2")
        if r[field] != ZERO
    }
    names: dict[int, str] = {}
    for item in catalog.get("items", []):
        iid = int(item.get("item_id", 0))
        name = item.get("name") or item.get("label")
        if iid in local_item_ids and name:
            names[iid] = name
    for row in upstream:
        for grant in row.get("grants") or []:
            iid = int(grant.get("item_id", 0))
            if iid in local_item_ids and grant.get("name"):
                names.setdefault(iid, grant["name"])
        iid = int(row.get("item_id", 0))
        if iid in local_item_ids and (row.get("name") or row.get("label")):
            names.setdefault(iid, row.get("name") or row.get("label"))

    item_names = {
        f"0x{iid:08X}": names[iid]
        for iid in sorted(names)
    }
    unresolved = [f"0x{iid:08X}" for iid in sorted(local_item_ids) if iid not in names]

    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    provenance = {
        "repository": UPSTREAM_REPO,
        "path": UPSTREAM_PATH,
        "branch": "main",
        "commit": commit_sha,
        "blob_sha": blob_sha,
        "license": "MIT",
        "retrieved_at": generated,
        "note": "Derived mapping only; upstream QR images are not copied.",
    }

    community_data = {
        "provenance": provenance,
        "game_id": catalog.get("game_id"),
        "title": catalog.get("title"),
        "default_version": catalog.get("default_version", "update"),
        "verified_note": "Upstream README states listed QR reward contents were checked on real hardware.",
        "reward_signatures": [reward_by_key[k] for k in sorted(reward_by_key)],
        "item_names_for_jp40": item_names,
        "unresolved_jp40_item_ids": unresolved,
    }
    OUT_DATA.write_text(json.dumps(community_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    comparison = {
        "generated_at": generated,
        "provenance": provenance,
        "counts": {
            "ours_qr2_rows": len(local),
            "community_update_rows": len(upstream),
            "ours_unique_reward_signatures": len(local_keys),
            "community_unique_reward_signatures": len(upstream_keys),
            "exact_reward_signatures": len(exact_keys),
            "community_only_reward_signatures": len(upstream_keys - local_keys),
            "ours_only_reward_signatures": len(local_keys - upstream_keys),
            "ours_type_values": len(local_map),
            "community_type_values": len(upstream_map),
            "union_type_values": len(all_types),
            "jp40_item_ids": len(local_item_ids),
            "community_named_jp40_item_ids": len(item_names),
            "community_unresolved_jp40_item_ids": len(unresolved),
        },
        "type_classification": type_counts,
        "community_only_reward_keys": sorted(upstream_keys - local_keys),
        "ours_only_reward_keys": sorted(local_keys - upstream_keys),
        "sample_type_conflicts": type_conflicts,
        "unresolved_item_ids": unresolved,
    }
    OUT_COMPARE.write_text(json.dumps(comparison, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    c = comparison["counts"]
    t = type_counts
    doc = f"""# Yu08083 YW3 catalog comparison\n\nThis file is generated by `tools/compare_community_catalog.py`.\n\n## Source\n\n- Upstream: `{UPSTREAM_REPO}/{UPSTREAM_PATH}`\n- Commit: `{commit_sha}`\n- Blob: `{blob_sha or 'unknown'}`\n- License: MIT (see upstream repository)\n- Retrieved: {generated}\n- Only derived reward/name mappings are stored here; upstream QR image assets are not copied.\n\n## JP Ver.4.0 vs community update table\n\n| Metric | Count |\n|---|---:|\n| Our QR2_INFO rows | {c['ours_qr2_rows']} |\n| Community update rows | {c['community_update_rows']} |\n| Our unique reward signatures | {c['ours_unique_reward_signatures']} |\n| Community unique reward signatures | {c['community_unique_reward_signatures']} |\n| Exact reward signatures | {c['exact_reward_signatures']} |\n| Community-only reward signatures | {c['community_only_reward_signatures']} |\n| Ours-only reward signatures | {c['ours_only_reward_signatures']} |\n| Our covered Type values | {c['ours_type_values']} |\n| Community covered Type values | {c['community_type_values']} |\n\n### Type-by-Type classification\n\n| Classification | Count |\n|---|---:|\n| Exact | {t['exact']} |\n| Multiple candidate | {t['multiple_candidate']} |\n| Community only | {t['community_only']} |\n| Ours only | {t['ours_only']} |\n| Conflict | {t['conflict']} |\n\nA Type is **exact** when the complete `reward_key` matches: Item1, Item2, Flag1, Flag2, both internal values, both quantities, and RandomQRTable. This deliberately compares internal behavior rather than Japanese labels alone.\n\n## Item names\n\n- JP4.0 item IDs used by QR2: {c['jp40_item_ids']}\n- Names found in community catalog: {c['community_named_jp40_item_ids']}\n- Still unresolved from community catalog: {c['community_unresolved_jp40_item_ids']}\n\nMachine-readable results are in `data/community-comparison.json` and the derived verified mapping is in `data/community-yu08083.json`.\n"""
    OUT_DOC.write_text(doc, encoding="utf-8")

    print(json.dumps({"counts": c, "type_classification": t, "unresolved": unresolved}, ensure_ascii=False, indent=2))


def base36(number: int) -> str:
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    out = ""
    n = number
    if n == 0:
        return "000"
    while n:
        n, rem = divmod(n, 36)
        out = chars[rem] + out
    return out.rjust(3, "0")


if __name__ == "__main__":
    main()
