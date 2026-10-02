#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "src" / "app.js"
META = ROOT / "data" / "metadata.json"
MARKER = "communityRewardMap"


def replace_once(text: str, old: str, new: str) -> str:
    if old not in text:
        raise RuntimeError(f"Patch anchor not found: {old[:80]!r}")
    return text.replace(old, new, 1)


def patch_app() -> bool:
    text = APP.read_text(encoding="utf-8")
    if MARKER in text:
        print("Community layer already present in app.js")
        return False

    text = replace_once(
        text,
        "  itemNames: {},\n  metadata: null,",
        "  itemNames: {},\n  community: null,\n  communityRewardMap: new Map(),\n  metadata: null,",
    )

    text = replace_once(
        text,
        "function itemInfo(id) {",
        '''function rowRewardKey(row) {
  return [
    parseInt(row.item1, 16),
    parseInt(row.item2, 16),
    parseInt(row.flag1, 16),
    parseInt(row.flag2, 16),
    Number(row.u1),
    Number(row.u2),
    Number(row.qty1),
    Number(row.qty2),
    parseInt(row.randomTable, 16),
  ].join(":");
}

function verifiedReward(row) {
  return state.communityRewardMap.get(rowRewardKey(row)) || null;
}

function itemInfo(id) {''',
    )

    text = replace_once(
        text,
        "function effectText(row) {\n  const parts = [];",
        '''function effectText(row) {
  const community = verifiedReward(row);
  if (community?.label) return community.label;
  const parts = [];''',
    )

    text = replace_once(
        text,
        '  if (row.u1 || row.u2) badges.push(`内部:${row.u1}/${row.u2}`);\n  return badges;',
        '  if (row.u1 || row.u2) badges.push(`内部:${row.u1}/${row.u2}`);\n  if (verifiedReward(row)) badges.push("実機確認済み");\n  return badges;',
    )

    text = replace_once(
        text,
        '''function rewardGroupKey(row) {
  return [row.item1, row.qty1, row.item2, row.qty2].join("|");
}''',
        '''function rewardGroupKey(row) {
  // Community reward_group/label is the user-facing receiving content.
  // Different internal flags can therefore live under one visible reward group.
  return effectText(row);
}''',
    )

    text = replace_once(
        text,
        '''  $("#mappedItems").textContent =
    `${m.itemNameCoverage.mappedUniqueItems}/${m.itemNameCoverage.uniqueItemsInQr2}`;''',
        '''  const usedItemIds = new Set(
    state.rows.flatMap((row) => [row.item1, row.item2]).filter((id) => id !== ZERO)
  );
  const mappedItemIds = [...usedItemIds].filter((id) => itemInfo(id).mapped);
  $("#mappedItems").textContent = `${mappedItemIds.length}/${usedItemIds.size}`;''',
    )

    old_boot = '''    const [loadedRows, namesResponse, metaResponse] = await Promise.all([
      loadQr2Dataset(),
      fetch("./data/item-names.json"),
      fetch("./data/metadata.json"),
    ]);

    if (!namesResponse.ok || !metaResponse.ok) {
      throw new Error("ローカルデータファイルの読み込みに失敗しました。");
    }

    state.rows = loadedRows;
    state.itemNames = await namesResponse.json();
    state.metadata = await metaResponse.json();'''
    new_boot = '''    const [loadedRows, namesResponse, metaResponse, communityResponse] = await Promise.all([
      loadQr2Dataset(),
      fetch("./data/item-names.json"),
      fetch("./data/metadata.json"),
      fetch("./data/community-yu08083.json"),
    ]);

    if (!namesResponse.ok || !metaResponse.ok || !communityResponse.ok) {
      throw new Error("ローカルデータファイルの読み込みに失敗しました。");
    }

    state.rows = loadedRows;
    state.itemNames = await namesResponse.json();
    state.metadata = await metaResponse.json();
    state.community = await communityResponse.json();
    state.communityRewardMap = new Map(
      (state.community.reward_signatures || []).map((reward) => [reward.reward_key, reward])
    );

    // Prefer the community catalog's JP labels. Existing English aliases/categories stay intact.
    for (const [id, name] of Object.entries(state.community.item_names_for_jp40 || {})) {
      const existing = state.itemNames[id] || {};
      state.itemNames[id] = {
        ...existing,
        name,
        name_en: existing.name_en || "",
        category: existing.category || "未分類",
        category_en: existing.category_en || "Unclassified",
        source: `${existing.source ? `${existing.source}; ` : ""}Yu08083/Yokai2-QR 実機確認済みYW3 catalog`,
      };
    }'''
    text = replace_once(text, old_boot, new_boot)

    text = replace_once(
        text,
        '    setStatus("日本版 Ver.4.0 データセットを読み込みました。", "success");',
        '    setStatus("日本版 Ver.4.0 + 有志実機確認済み報酬データを読み込みました。", "success");',
    )

    APP.write_text(text, encoding="utf-8")
    print("Patched src/app.js with community reward layer")
    return True


def patch_metadata() -> bool:
    data = json.loads(META.read_text(encoding="utf-8"))
    changed = False
    coverage = data.setdefault("itemNameCoverage", {})
    if coverage.get("mappedUniqueItems") != 175:
        coverage["mappedUniqueItems"] = 175
        changed = True
    loc = data.setdefault("localization", {})
    updates = {
        "mappedJapaneseItemNames": 175,
        "communityVerifiedCatalog": "Yu08083/Yokai2-QR/yw3/catalog.json",
        "communityCoverage": "175/175 JP4.0 QR2 item IDs; 26503/26503 Type values exact",
    }
    for key, value in updates.items():
        if loc.get(key) != value:
            loc[key] = value
            changed = True
    if changed:
        META.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("Updated metadata item-name coverage to 175/175")
    return changed


if __name__ == "__main__":
    patch_app()
    patch_metadata()
