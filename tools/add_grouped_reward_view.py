from pathlib import Path
import re

app_path = Path("src/app.js")
index_path = Path("index.html")
css_path = Path("assets/styles.css")

app = app_path.read_text(encoding="utf-8")
index = index_path.read_text(encoding="utf-8")
css = css_path.read_text(encoding="utf-8")

# State used by the generator browser.
app = app.replace(
    '  generatorResults: [],\n  generated: [],',
    '  generatorResults: [],\n  generatorMode: "grouped",\n  expandedGeneratorGroups: new Set(),\n  generated: [],',
)

new_generator_block = r'''const GENERATOR_BATCH_SIZE = 80;

function generatorMatches(query) {
  const q = query.trim().toLowerCase();
  if (!q) return state.rows;
  return state.rows.filter((row) => rowSearchText(row).includes(q));
}

function rewardGroupKey(row) {
  return [row.item1, row.qty1, row.item2, row.qty2].join("|");
}

function groupGeneratorRows(rows) {
  const groups = new Map();
  for (const row of rows) {
    const key = rewardGroupKey(row);
    let group = groups.get(key);
    if (!group) {
      group = {
        key,
        label: effectText(row),
        rows: [],
      };
      groups.set(key, group);
    }
    group.rows.push(row);
  }
  return [...groups.values()].sort((a, b) => {
    const aMapped = itemInfo(a.rows[0].item1).mapped ? 0 : 1;
    const bMapped = itemInfo(b.rows[0].item1).mapped ? 0 : 1;
    return aMapped - bMapped || a.rows[0].index - b.rows[0].index;
  });
}

function generatorRowHtml(row, { compact = false } = {}) {
  const mapped = itemInfo(row.item1).mapped;
  return `
    <button class="result-row${compact ? " group-type-row" : ""}" type="button" data-index="${row.index}">
      <span class="result-main">
        <strong>${escapeHtml(effectText(row))}</strong>
        <small>Type ${row.typeStart}–${row.typeEnd} · #${row.index}</small>
      </span>
      <span class="result-meta">
        ${mapped ? "" : '<span class="badge warning">未特定</span>'}
        ${specialBadges(row).map((x) => `<span class="badge">${escapeHtml(x)}</span>`).join("")}
      </span>
    </button>`;
}

function generatorGroupHtml(group) {
  const expanded = state.expandedGeneratorGroups.has(group.key);
  const typeCount = group.rows.reduce((sum, row) => sum + rangeSize(row), 0);
  const mapped = group.rows.every(
    (row) => itemInfo(row.item1).mapped && itemInfo(row.item2).mapped
  );
  const badges = [...new Set(group.rows.flatMap((row) => specialBadges(row)))];

  return `
    <div class="result-group">
      <button class="result-row result-group-toggle" type="button"
              data-group-key="${escapeHtml(group.key)}" aria-expanded="${expanded}">
        <span class="result-main">
          <strong>${escapeHtml(group.label)}</strong>
          <small>${group.rows.length.toLocaleString()} QR2_INFO · ${typeCount.toLocaleString()} Type${typeCount === 1 ? "" : "s"}</small>
        </span>
        <span class="result-meta">
          ${mapped ? "" : '<span class="badge warning">未特定</span>'}
          ${badges.slice(0, 3).map((x) => `<span class="badge">${escapeHtml(x)}</span>`).join("")}
          <span class="badge group-count">${group.rows.length.toLocaleString()}件</span>
          <span class="group-chevron" aria-hidden="true">${expanded ? "▴" : "▾"}</span>
        </span>
      </button>
      ${expanded ? `<div class="group-types">${group.rows.map((row) => generatorRowHtml(row, { compact: true })).join("")}</div>` : ""}
    </div>`;
}

function generatorDisplayItems() {
  return state.generatorMode === "grouped"
    ? groupGeneratorRows(state.generatorResults)
    : state.generatorResults;
}

function renderGeneratorMatches(query, { reset = true } = {}) {
  const box = $("#generatorMatches");
  const previousScrollTop = box.scrollTop;

  if (reset) {
    state.generatorQuery = query;
    state.generatorLimit = GENERATOR_BATCH_SIZE;
    state.generatorResults = generatorMatches(query);
    state.expandedGeneratorGroups.clear();
  }

  const matches = state.generatorResults;
  const displayItems = generatorDisplayItems();
  if (!displayItems.length) {
    box.innerHTML = `<div class="empty-state compact">一致するQR2_INFOがありません。</div>`;
    return;
  }

  const visible = displayItems.slice(0, state.generatorLimit);
  const hasMore = visible.length < displayItems.length;
  const summary = state.generatorMode === "grouped"
    ? `報酬 ${visible.length.toLocaleString()} / ${displayItems.length.toLocaleString()}種類 · QR2_INFO ${matches.length.toLocaleString()}件`
    : `表示 ${visible.length.toLocaleString()} / ${matches.length.toLocaleString()}件`;

  box.innerHTML = `
    <div class="subtle result-summary">${summary}${hasMore ? " · 下へスクロールすると続きを読み込みます" : ""}</div>
    ${state.generatorMode === "grouped"
      ? visible.map(generatorGroupHtml).join("")
      : visible.map((row) => generatorRowHtml(row)).join("")}
    ${hasMore ? '<div class="subtle result-loading">続きを読み込み中…</div>' : ""}`;

  $$(".result-group-toggle", box).forEach((button) => {
    button.addEventListener("click", () => {
      const key = button.dataset.groupKey;
      if (state.expandedGeneratorGroups.has(key)) {
        state.expandedGeneratorGroups.delete(key);
      } else {
        state.expandedGeneratorGroups.add(key);
      }
      renderGeneratorMatches(state.generatorQuery, { reset: false });
    });
  });

  $$(".result-row[data-index]", box).forEach((button) => {
    button.addEventListener("click", () => {
      const row = state.rows.find((x) => x.index === Number(button.dataset.index));
      selectRow(row, { syncQuery: false });
    });
  });

  box.scrollTop = reset ? 0 : previousScrollTop;
}

function loadMoreGeneratorMatches() {
  const total = generatorDisplayItems().length;
  if (state.generatorLimit >= total) return;
  state.generatorLimit = Math.min(state.generatorLimit + GENERATOR_BATCH_SIZE, total);
  renderGeneratorMatches(state.generatorQuery, { reset: false });
}

function resolveType'''

app, count = re.subn(
    r'const GENERATOR_BATCH_SIZE = 80;.*?\nfunction resolveType',
    new_generator_block,
    app,
    count=1,
    flags=re.S,
)
if count != 1:
    raise SystemExit(f"generator block replacement failed: {count}")

# Bind the view-mode selector.
needle = '''  $("#generatorQuery").addEventListener("input", (event) => {
    renderGeneratorMatches(event.target.value);
  });

  const generatorBox = $("#generatorMatches");'''
replacement = '''  $("#generatorQuery").addEventListener("input", (event) => {
    renderGeneratorMatches(event.target.value);
  });

  $("#generatorViewMode").addEventListener("change", (event) => {
    state.generatorMode = event.target.value;
    renderGeneratorMatches($("#generatorQuery").value);
  });

  const generatorBox = $("#generatorMatches");'''
if needle not in app:
    raise SystemExit("generator event binding anchor not found")
app = app.replace(needle, replacement, 1)

# Add the mode selector directly below the search field.
index_needle = '''            <label class="field">
              <span>アイテム名 / Item ID / Type / Flag</span>
              <input id="generatorQuery" type="search" placeholder="例: 禁断の果実 / Forbidden Fruit / C6458704 / Q1B">
            </label>
            <div id="generatorMatches" class="result-list"></div>'''
index_replacement = '''            <label class="field">
              <span>アイテム名 / Item ID / Type / Flag</span>
              <input id="generatorQuery" type="search" placeholder="例: 禁断の果実 / Forbidden Fruit / C6458704 / Q1B">
            </label>
            <div class="generator-view-controls">
              <label class="field generator-view-mode">
                <span>表示方法</span>
                <select id="generatorViewMode">
                  <option value="grouped" selected>報酬ごとにまとめる</option>
                  <option value="entries">QR2_INFOを全件表示</option>
                </select>
              </label>
              <p class="subtle generator-view-help">検索欄が空でも閲覧できます。報酬をクリックすると対応するType範囲を展開します。</p>
            </div>
            <div id="generatorMatches" class="result-list"></div>'''
if index_needle not in index:
    raise SystemExit("index generator anchor not found")
index = index.replace(index_needle, index_replacement, 1)

css_addition = r'''

/* Generator reward grouping */
.generator-view-controls {
  display: flex;
  align-items: end;
  gap: 12px;
  margin-top: 10px;
}
.generator-view-mode {
  flex: 0 0 min(260px, 45%);
}
.generator-view-help {
  margin: 0 0 9px;
  line-height: 1.5;
}
.result-summary {
  position: sticky;
  top: 0;
  z-index: 3;
  padding: 5px 4px 9px;
  background: linear-gradient(#111827 75%, rgba(17, 24, 39, 0));
}
.result-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.result-group-toggle {
  position: relative;
}
.result-group-toggle[aria-expanded="true"] {
  border-color: #4c82a0;
  background: #121e2d;
}
.group-count {
  border-color: #405776;
}
.group-chevron {
  width: 1.2em;
  text-align: center;
  color: var(--muted);
  font-size: .9rem;
}
.group-types {
  display: flex;
  flex-direction: column;
  gap: 5px;
  margin: -1px 0 4px 18px;
  padding: 7px 0 3px 10px;
  border-left: 2px solid #2b3a50;
}
.group-type-row {
  padding: 8px 10px;
  border-radius: 10px;
  background: #0a111a;
}
.group-type-row .result-main strong {
  font-size: .84rem;
}
.group-type-row .result-main small {
  font-size: .72rem;
}
.result-loading {
  padding: 7px 4px;
}
@media (max-width: 700px) {
  .generator-view-controls {
    align-items: stretch;
    flex-direction: column;
  }
  .generator-view-mode {
    flex-basis: auto;
    width: 100%;
  }
  .generator-view-help {
    margin: 0;
  }
  .group-types {
    margin-left: 8px;
    padding-left: 7px;
  }
}
'''
if "/* Generator reward grouping */" not in css:
    css += css_addition

app_path.write_text(app, encoding="utf-8")
index_path.write_text(index, encoding="utf-8")
css_path.write_text(css, encoding="utf-8")
print("Grouped reward view applied")
