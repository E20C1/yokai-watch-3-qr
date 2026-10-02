import {
  V2,
  base36,
  fromBase36,
  normalizeType,
  normalizeVariation,
  variationFromIndex,
  randomVariation,
  makeCode,
  makePayload,
  parsePayload,
} from "./qr-v2.js";
import { loadQr2Dataset } from "./data-loader.js";

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

const state = {
  rows: [],
  itemNames: {},
  metadata: null,
  selected: null,
  explorerLimit: 100,
  generatorLimit: 80,
  generatorQuery: "",
  generatorResults: [],
  generated: [],
};

const ZERO = "0x00000000";

function hexKey(value) {
  const body = String(value ?? "")
    .replace(/^0x/i, "")
    .toUpperCase()
    .padStart(8, "0");
  return `0x${body}`;
}

function itemInfo(id) {
  const key = hexKey(id);
  if (key === ZERO) return { name: "—", name_en: "—", category: "なし", category_en: "None", mapped: true };
  const mapped = state.itemNames[key];
  if (mapped) return { ...mapped, mapped: true };
  return { name: `未特定アイテム ${key}`, name_en: `Unknown item ${key}`, category: "未特定", category_en: "Unmapped", mapped: false };
}

function itemLabel(id, qty = 1) {
  const key = hexKey(id);
  if (key === ZERO) return "—";
  const info = itemInfo(key);
  return `${info.name} ×${qty}`;
}

function rangeSize(row) {
  return row.end - row.start + 1;
}

function effectText(row) {
  const parts = [];
  if (row.item1 !== ZERO) parts.push(itemLabel(row.item1, row.qty1));
  if (row.item2 !== ZERO) parts.push(itemLabel(row.item2, row.qty2));
  if (!parts.length) parts.push("アイテム報酬なし");
  return parts.join(" + ");
}

function specialBadges(row) {
  const badges = [];
  if (row.item2 !== ZERO) badges.push("2アイテム");
  if (row.flag1 !== ZERO) badges.push("Flag1");
  if (row.flag2 !== ZERO) badges.push("Flag2");
  if (row.randomTable !== ZERO) badges.push("抽選テーブル");
  if (row.u1 || row.u2) badges.push(`内部:${row.u1}/${row.u2}`);
  return badges;
}

function rowSearchText(row) {
  const a = itemInfo(row.item1);
  const b = itemInfo(row.item2);
  return [
    row.index,
    row.typeStart,
    row.typeEnd,
    row.start,
    row.end,
    row.item1,
    row.item2,
    row.flag1,
    row.flag2,
    row.randomTable,
    a.name,
    a.category,
    a.name_en,
    a.category_en,
    b.name,
    b.category,
    b.name_en,
    b.category_en,
    effectText(row),
  ]
    .join(" ")
    .toLowerCase();
}

function randomIntInclusive(min, max) {
  const span = max - min + 1;
  if (globalThis.crypto?.getRandomValues) {
    const buf = new Uint32Array(1);
    globalThis.crypto.getRandomValues(buf);
    return min + (buf[0] % span);
  }
  return min + Math.floor(Math.random() * span);
}

function findEntriesForType(typeText) {
  try {
    const type = normalizeType(typeText);
    const dec = fromBase36(type);
    return state.rows.filter((row) => dec >= row.start && dec <= row.end);
  } catch {
    return [];
  }
}

function setStatus(message, kind = "info") {
  const el = $("#status");
  el.textContent = message;
  el.dataset.kind = kind;
}

function switchTab(name) {
  $$(".tab-button").forEach((button) => {
    button.classList.toggle("active", button.dataset.tab === name);
  });
  $$(".tab-panel").forEach((panel) => {
    panel.hidden = panel.id !== `tab-${name}`;
  });
  history.replaceState(null, "", `#${name}`);
}

function renderMetadata() {
  const m = state.metadata;
  $("#datasetVersion").textContent = `${m.region} Ver.${m.gameVersion}`;
  $("#entryCount").textContent = m.qr2Entries.toLocaleString();
  $("#sourceHash").textContent = m.sourceConfigSha256;
  $("#mappedItems").textContent =
    `${m.itemNameCoverage.mappedUniqueItems}/${m.itemNameCoverage.uniqueItemsInQr2}`;

  $("#statEntries").textContent = m.qr2Entries.toLocaleString();
  $("#statItem2").textContent = m.stats.item2NonZero.toLocaleString();
  $("#statFlag1").textContent = m.stats.flag1NonZero.toLocaleString();
  $("#statFlag2").textContent = m.stats.flag2NonZero.toLocaleString();
  $("#statRandom").textContent = m.stats.randomTableNonZero.toLocaleString();

  const test = m.generator.testVector;
  const generated = makeCode(test.input.slice(0, 3), test.input.slice(3));
  const ok = generated === test.code;
  $("#selfTest").textContent = ok ? "PASS" : "FAIL";
  $("#selfTest").className = ok ? "status-pass" : "status-fail";
  if (!ok) setStatus("生成エンジンの自己テストに失敗しました。QRを使用しないでください。", "error");
}

function selectedRowCard(row) {
  if (!row) {
    return `<div class="empty-state">検索結果または一覧からQRエントリを選択してください。</div>`;
  }
  const badges = specialBadges(row)
    .map((value) => `<span class="badge">${escapeHtml(value)}</span>`)
    .join("");

  return `
    <div class="selection-head">
      <div>
        <div class="eyebrow">QR2_INFO #${row.index}</div>
        <h3>${escapeHtml(effectText(row))}</h3>
      </div>
      <div class="badge-row">${badges || '<span class="badge muted">通常報酬</span>'}</div>
    </div>
    <div class="kv-grid">
      <div><span>Type range</span><strong>${row.typeStart} – ${row.typeEnd}</strong></div>
      <div><span>Type count</span><strong>${rangeSize(row).toLocaleString()}</strong></div>
      <div><span>Item1</span><strong>${escapeHtml(itemLabel(row.item1, row.qty1))}</strong><code>${row.item1}</code></div>
      <div><span>Item2</span><strong>${escapeHtml(itemLabel(row.item2, row.qty2))}</strong><code>${row.item2}</code></div>
      <div><span>Flag1</span><code>${row.flag1}</code></div>
      <div><span>Flag2</span><code>${row.flag2}</code></div>
      <div><span>Random table</span><code>${row.randomTable}</code></div>
      <div><span>Unknown bools</span><strong>${row.u1} / ${row.u2}</strong></div>
    </div>`;
}

function selectRow(row, { jump = false, syncQuery = jump } = {}) {
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

function resolveType(row) {
  const mode = $("#typeMode").value;
  if (mode === "first") return row.typeStart;
  if (mode === "random") return base36(randomIntInclusive(row.start, row.end), 3);

  const manual = normalizeType($("#manualType").value);
  const dec = fromBase36(manual);
  if (dec < row.start || dec > row.end) {
    throw new Error(`Manual Type must be inside ${row.typeStart}–${row.typeEnd}.`);
  }
  return manual;
}

function variations(amount) {
  const mode = $("#variationMode").value;
  const seed = normalizeVariation($("#variationSeed").value || "0000");
  if (mode === "fixed") return Array.from({ length: amount }, () => seed);
  if (mode === "random") return Array.from({ length: amount }, () => randomVariation());

  const start = fromBase36(seed);
  return Array.from({ length: amount }, (_, index) => {
    const value = (start + index) % (V2.maxVariation + 1);
    return variationFromIndex(value);
  });
}

function qrCanvasFrom(container) {
  return container.querySelector("canvas") || null;
}

function renderGenerated() {
  const box = $("#generatedGrid");
  box.innerHTML = "";

  if (!state.generated.length) {
    box.innerHTML = `<div class="empty-state">まだ生成していません。</div>`;
    $("#exportCodes").disabled = true;
    return;
  }

  $("#exportCodes").disabled = false;

  for (const entry of state.generated) {
    const card = document.createElement("article");
    card.className = "qr-card";
    card.innerHTML = `
      <div class="qr-image"></div>
      <div class="qr-card-body">
        <div class="qr-type">${entry.type} <span>${entry.variation}</span></div>
        <code class="code-line">${entry.code}</code>
        <div class="qr-actions">
          <button type="button" class="secondary copy-code">Copy</button>
          <button type="button" class="secondary save-png">PNG</button>
        </div>
      </div>`;

    const target = $(".qr-image", card);
    // QRTool-compatible 3DS payload. For V2 the game reads the slash path.
    new globalThis.QRCode(target, {
      text: entry.payload,
      width: 220,
      height: 220,
      correctLevel: globalThis.QRCode.CorrectLevel.M,
    });

    $(".copy-code", card).addEventListener("click", async () => {
      await navigator.clipboard.writeText(entry.payload);
      setStatus(`Copied ${entry.type}/${entry.variation}.`, "success");
    });

    $(".save-png", card).addEventListener("click", () => {
      const canvas = qrCanvasFrom(target);
      if (!canvas) return;
      const a = document.createElement("a");
      a.href = canvas.toDataURL("image/png");
      a.download = `yw3-jp40-${entry.type}-${entry.variation}.png`;
      a.click();
    });

    box.appendChild(card);
  }
}

function generateBatch() {
  try {
    if (!state.selected) throw new Error("先にQRエントリを選択してください。");
    const amount = Math.max(1, Math.min(200, Number($("#amount").value) || 1));
    $("#amount").value = amount;

    const type = resolveType(state.selected);
    const vars = variations(amount);
    state.generated = vars.map((variation) => {
      const code = makeCode(type, variation);
      return {
        type,
        variation,
        code,
        payload: makePayload(code),
        rowIndex: state.selected.index,
      };
    });

    renderGenerated();
    setStatus(
      `Type ${type} のQRを ${state.generated.length} 枚生成しました。`,
      "success"
    );
  } catch (error) {
    setStatus(error.message, "error");
  }
}

function exportGeneratedCodes() {
  if (!state.generated.length) return;
  const header = [
    "# Yo-kai Watch 3 Sukiyaki Ver.4.0",
    `# QR2_INFO #${state.selected?.index ?? "?"}`,
    `# ${state.selected ? effectText(state.selected) : ""}`,
    "",
  ].join("\n");
  const body = state.generated
    .map((x) => `${x.type}\t${x.variation}\t${x.code}\t${x.payload}`)
    .join("\n");
  downloadText("yw3-jp40-qr-codes.txt", `${header}${body}\n`);
}

function explorerFilter(row) {
  const q = $("#explorerQuery").value.trim().toLowerCase();
  const filter = $("#specialFilter").value;
  if (q && !rowSearchText(row).includes(q)) return false;
  if (filter === "flags" && row.flag1 === ZERO && row.flag2 === ZERO) return false;
  if (filter === "item2" && row.item2 === ZERO) return false;
  if (filter === "random" && row.randomTable === ZERO) return false;
  if (filter === "unmapped" && itemInfo(row.item1).mapped) return false;
  if (filter === "simple" && specialBadges(row).length) return false;
  return true;
}

function renderExplorer(reset = false) {
  if (reset) state.explorerLimit = 100;
  const filtered = state.rows.filter(explorerFilter);
  const visible = filtered.slice(0, state.explorerLimit);
  $("#explorerCount").textContent =
    `${filtered.toLocaleString()} entries · showing ${visible.length.toLocaleString()}`;

  $("#explorerBody").innerHTML = visible
    .map(
      (row) => `
      <tr data-index="${row.index}">
        <td><button class="link-button" type="button">${row.index}</button></td>
        <td><code>${row.typeStart}–${row.typeEnd}</code></td>
        <td>
          <strong>${escapeHtml(effectText(row))}</strong>
          <div class="subtle">${escapeHtml(itemInfo(row.item1).category)}</div>
        </td>
        <td><code>${row.item1}</code>${row.item2 !== ZERO ? `<br><code>${row.item2}</code>` : ""}</td>
        <td>${specialBadges(row).map((x) => `<span class="badge">${escapeHtml(x)}</span>`).join(" ") || "—"}</td>
      </tr>`
    )
    .join("");

  $$("#explorerBody tr").forEach((tr) => {
    tr.addEventListener("click", () => {
      const row = state.rows.find((x) => x.index === Number(tr.dataset.index));
      selectRow(row, { jump: true });
    });
  });

  $("#showMore").hidden = visible.length >= filtered.length;
}

function analysisHtml(result, matches = []) {
  if (!result.valid) {
    return `<div class="analysis-bad"><strong>無効 / 未対応</strong><p>${escapeHtml(result.reason || "Checksum mismatch.")}</p></div>`;
  }

  const matching = matches
    .map(
      (row) => `
      <button type="button" class="analysis-match" data-index="${row.index}">
        <strong>${escapeHtml(effectText(row))}</strong>
        <span>QR2_INFO #${row.index} · ${row.typeStart}–${row.typeEnd}</span>
      </button>`
    )
    .join("");

  return `
    <div class="analysis-good">
      <div class="selection-head">
        <div><div class="eyebrow">V2 checksum</div><h3>有効</h3></div>
        <span class="badge success">PASS</span>
      </div>
      <div class="kv-grid">
        <div><span>Type</span><strong>${result.type}</strong></div>
        <div><span>Variation</span><strong>${result.variation}</strong></div>
        <div><span>Type decimal</span><strong>${fromBase36(result.type)}</strong></div>
        <div><span>Checksum</span><code>${result.checksum}</code></div>
      </div>
      <div class="analysis-matches">
        <h4>JP Ver.4.0 lookup</h4>
        ${matching || '<div class="empty-state compact">このTypeに対応するQR2_INFO範囲がありません。</div>'}
      </div>
    </div>`;
}

function analyzeText(text) {
  try {
    const result = parsePayload(text);
    let matches = [];
    if (result.valid) matches = findEntriesForType(result.type);
    $("#analysisResult").innerHTML = analysisHtml(result, matches);

    $$(".analysis-match").forEach((button) => {
      button.addEventListener("click", () => {
        const row = state.rows.find((x) => x.index === Number(button.dataset.index));
        selectRow(row, { jump: true });
      });
    });
  } catch (error) {
    $("#analysisResult").innerHTML = analysisHtml({ valid: false, reason: error.message });
  }
}

async function decodeImageFile(file) {
  if (!file) return;
  try {
    const bitmap = await createImageBitmap(file);
    const canvas = $("#decodeCanvas");
    const ctx = canvas.getContext("2d", { willReadFrequently: true });

    const scale = Math.min(1, 1600 / Math.max(bitmap.width, bitmap.height));
    canvas.width = Math.max(1, Math.round(bitmap.width * scale));
    canvas.height = Math.max(1, Math.round(bitmap.height * scale));
    ctx.drawImage(bitmap, 0, 0, canvas.width, canvas.height);

    const image = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const decoded = globalThis.jsQR(image.data, canvas.width, canvas.height, {
      inversionAttempts: "attemptBoth",
    });
    if (!decoded) throw new Error("画像からQRコードを検出できませんでした。");

    $("#analyzerText").value = decoded.data;
    analyzeText(decoded.data);
    setStatus("QR画像を読み取りました。", "success");
  } catch (error) {
    setStatus(error.message, "error");
  }
}

function downloadText(filename, text) {
  const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 500);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function bindEvents() {
  $$(".tab-button").forEach((button) => {
    button.addEventListener("click", () => switchTab(button.dataset.tab));
  });

  $("#generatorQuery").addEventListener("input", (event) => {
    renderGeneratorMatches(event.target.value);
  });

  const generatorBox = $("#generatorMatches");
  generatorBox.addEventListener(
    "scroll",
    () => {
      const nearBottom =
        generatorBox.scrollTop + generatorBox.clientHeight >= generatorBox.scrollHeight - 180;
      if (nearBottom) loadMoreGeneratorMatches();
    },
    { passive: true }
  );

  $("#typeMode").addEventListener("change", () => {
    $("#manualTypeWrap").hidden = $("#typeMode").value !== "manual";
  });

  $("#variationMode").addEventListener("change", () => {
    const mode = $("#variationMode").value;
    $("#variationSeedWrap").hidden = mode === "random";
    $("#variationSeedLabel").textContent = mode === "fixed" ? "Variation" : "Start variation";
  });

  $("#generate").addEventListener("click", generateBatch);
  $("#exportCodes").addEventListener("click", exportGeneratedCodes);
  $("#clearGenerated").addEventListener("click", () => {
    state.generated = [];
    renderGenerated();
  });

  $("#explorerQuery").addEventListener("input", () => renderExplorer(true));
  $("#specialFilter").addEventListener("change", () => renderExplorer(true));
  $("#showMore").addEventListener("click", () => {
    state.explorerLimit += 100;
    renderExplorer();
  });

  $("#analyzeText").addEventListener("click", () => analyzeText($("#analyzerText").value));
  $("#analyzerText").addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
      analyzeText(event.currentTarget.value);
    }
  });
  $("#imageInput").addEventListener("change", (event) => decodeImageFile(event.target.files?.[0]));

  const drop = $("#dropZone");
  ["dragenter", "dragover"].forEach((name) =>
    drop.addEventListener(name, (event) => {
      event.preventDefault();
      drop.classList.add("drag");
    })
  );
  ["dragleave", "drop"].forEach((name) =>
    drop.addEventListener(name, (event) => {
      event.preventDefault();
      drop.classList.remove("drag");
    })
  );
  drop.addEventListener("drop", (event) => decodeImageFile(event.dataTransfer.files?.[0]));

  document.addEventListener("paste", (event) => {
    const image = [...(event.clipboardData?.items || [])].find((x) => x.type.startsWith("image/"));
    if (!image) return;
    switchTab("analyzer");
    decodeImageFile(image.getAsFile());
  });
}

async function boot() {
  try {
    const [loadedRows, namesResponse, metaResponse] = await Promise.all([
      loadQr2Dataset(),
      fetch("./data/item-names.json"),
      fetch("./data/metadata.json"),
    ]);

    if (!namesResponse.ok || !metaResponse.ok) {
      throw new Error("ローカルデータファイルの読み込みに失敗しました。");
    }

    state.rows = loadedRows;
    state.itemNames = await namesResponse.json();
    state.metadata = await metaResponse.json();

    bindEvents();
    renderMetadata();
    renderGeneratorMatches("");
    renderExplorer(true);
    renderGenerated();

    const forbidden = state.rows.find((row) => hexKey(row.item1) === "0xC6458704");
    if (forbidden) selectRow(forbidden);

    const requested = location.hash.replace("#", "");
    switchTab(["generator", "explorer", "analyzer", "research"].includes(requested) ? requested : "generator");
    setStatus("日本版 Ver.4.0 データセットを読み込みました。", "success");
  } catch (error) {
    console.error(error);
    setStatus(error.message, "error");
    $("#app").classList.add("boot-failed");
  }
}

boot();
