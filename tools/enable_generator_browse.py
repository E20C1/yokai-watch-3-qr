from pathlib import Path

# This script is intentionally reproducible and safe to rerun from GitHub Actions.
path = Path("src/app.js")
app = path.read_text(encoding="utf-8")

old_state = '''  selected: null,\n  explorerLimit: 100,\n  generated: [],\n};'''
new_state = '''  selected: null,\n  explorerLimit: 100,\n  generatorLimit: 80,\n  generatorQuery: "",\n  generatorResults: [],\n  generated: [],\n};'''
if old_state not in app:
    raise SystemExit("state block not found")
app = app.replace(old_state, new_state, 1)

start = app.index("function selectRow(")
end = app.index("\nfunction resolveType", start)
new_section = r'''function selectRow(row, { jump = false, syncQuery = jump } = {}) {
  state.selected = row;
  $("#selectedEntry").innerHTML = selectedRowCard(row);
  $("#manualType").value = row.typeStart;

  // Browsing the result list should not collapse it to the selected reward.
  // Explorer / Analyzer jumps still synchronize the search field.
  if (syncQuery) {
    $("#generatorQuery").value = effectText(row);
    renderGeneratorMatches($("#generatorQuery").value);
  }

  if (jump) {
    switchTab("generator");
    $("#selectedEntry").scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

const GENERATOR_BATCH_SIZE = 80;

function generatorMatches(query) {
  const q = query.trim().toLowerCase();
  if (!q) return state.rows;
  return state.rows.filter((row) => rowSearchText(row).includes(q));
}

function generatorRowHtml(row) {
  const mapped = itemInfo(row.item1).mapped;
  return `
    <button class="result-row" type="button" data-index="${row.index}">
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

function renderGeneratorMatches(query, { reset = true } = {}) {
  const box = $("#generatorMatches");
  const previousScrollTop = box.scrollTop;

  if (reset) {
    state.generatorQuery = query;
    state.generatorLimit = GENERATOR_BATCH_SIZE;
    state.generatorResults = generatorMatches(query);
  }

  const matches = state.generatorResults;
  if (!matches.length) {
    box.innerHTML = `<div class="empty-state compact">一致するQR2_INFOがありません。</div>`;
    return;
  }

  const visible = matches.slice(0, state.generatorLimit);
  const hasMore = visible.length < matches.length;
  const summary = `表示 ${visible.length.toLocaleString()} / ${matches.length.toLocaleString()}件`;

  box.innerHTML = `
    <div class="subtle">${summary}${hasMore ? " · 下へスクロールすると続きを読み込みます" : ""}</div>
    ${visible.map(generatorRowHtml).join("")}
    ${hasMore ? '<div class="subtle">続きを読み込み中…</div>' : ""}`;

  $$(".result-row", box).forEach((button) => {
    button.addEventListener("click", () => {
      const row = state.rows.find((x) => x.index === Number(button.dataset.index));
      selectRow(row, { syncQuery: false });
    });
  });

  // Re-rendering a larger batch should keep the user's current browse position.
  box.scrollTop = reset ? 0 : previousScrollTop;
}

function loadMoreGeneratorMatches() {
  if (state.generatorLimit >= state.generatorResults.length) return;
  state.generatorLimit = Math.min(
    state.generatorLimit + GENERATOR_BATCH_SIZE,
    state.generatorResults.length
  );
  renderGeneratorMatches(state.generatorQuery, { reset: false });
}
'''
app = app[:start] + new_section + app[end:]

needle = '''  $("#generatorQuery").addEventListener("input", (event) => {\n    renderGeneratorMatches(event.target.value);\n  });\n'''
insert = '''  $("#generatorQuery").addEventListener("input", (event) => {\n    renderGeneratorMatches(event.target.value);\n  });\n\n  const generatorBox = $("#generatorMatches");\n  generatorBox.addEventListener(\n    "scroll",\n    () => {\n      const nearBottom =\n        generatorBox.scrollTop + generatorBox.clientHeight >= generatorBox.scrollHeight - 180;\n      if (nearBottom) loadMoreGeneratorMatches();\n    },\n    { passive: true }\n  );\n'''
if needle not in app:
    raise SystemExit("generator input binding not found")
app = app.replace(needle, insert, 1)

path.write_text(app, encoding="utf-8")
print("Enabled incremental generator browsing: 80 rows per scroll batch.")
