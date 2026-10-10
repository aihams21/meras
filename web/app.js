/* MERAS — منطق الواجهة */
"use strict";

const $ = (id) => document.getElementById(id);
const api = async (path, opts) => {
  const res = await fetch(path, opts);
  if (!res.ok) throw new Error("HTTP " + res.status);
  return res.json();
};

let LANG = localStorage.getItem("meras_lang") || "ar";
let SCAN = null;          // نتيجة الفحص
let SYSTEM = null;        // معلومات النظام
let SELECTED = new Set(); // المسارات المحددة
let polling = null;

const t = (k, vars) => {
  let s = (I18N[LANG] && I18N[LANG][k]) ?? I18N.ar[k] ?? k;
  if (vars) for (const [kk, vv] of Object.entries(vars)) s = s.replaceAll("{" + kk + "}", vv);
  return s;
};

/* ---------- format ---------- */
function bytes(n) {
  if (!n && n !== 0) return "—";
  const u = ["B", "KB", "MB", "GB", "TB"];
  let i = 0, v = n;
  while (v >= 1024 && i < u.length - 1) { v /= 1024; i++; }
  return (v >= 100 || i === 0 ? Math.round(v) : v.toFixed(1)) + " " + u[i];
}
function num(n) { return new Intl.NumberFormat(LANG === "ar" ? "ar-EG" : "en-US").format(n); }

/* ---------- i18n apply ---------- */
function applyLang() {
  document.documentElement.lang = I18N[LANG].lang;
  document.documentElement.dir = I18N[LANG].dir;
  document.body.dir = I18N[LANG].dir;
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    el.textContent = t(el.dataset.i18n);
  });
  $("langLabel").textContent = LANG === "ar" ? "EN" : "ع";
  $("langBtn").querySelector(".ctl-ico").textContent = LANG === "ar" ? "A" : "ع";
  const tbLabel = $("tbLabel");
  if (tbLabel) tbLabel.textContent = t("app_title");
  localStorage.setItem("meras_lang", LANG);
  render();
}
function toggleLang() { LANG = LANG === "ar" ? "en" : "ar"; applyLang(); }

/* ---------- theme ---------- */
function applyTheme(theme) {
  document.body.dataset.theme = theme;
  localStorage.setItem("meras_theme", theme);
  $("themeIco").textContent = theme === "dark" ? "☀" : "☾";
}
function toggleTheme() {
  applyTheme(document.body.dataset.theme === "dark" ? "light" : "dark");
}

/* ---------- shell: desktop vs browser ---------- */
const isDesktop = !!(window.pywebview && window.pywebview.api);
let apiBridge = null;

async function initShell() {
  const params = new URLSearchParams(location.search);
  const wantBoot = params.get("boot") === "1";

  if (isDesktop) {
    document.body.dataset.shell = "desktop";
    $("titlebar").hidden = false;
    bindTitlebar();
    apiBridge = window.pywebview.api;
    if (wantBoot) await runBoot();
  } else if (wantBoot) {
    // في المتصفح: بدون شاشة إقلاع (نفس المسار أسرع)
    $("boot").hidden = true;
  }
}

function bindTitlebar() {
  $("tbMin").onclick = () => { try { apiBridge.minimize_window(); } catch (e) { /* تجاهل */ } };
  $("tbMax").onclick = () => { try { apiBridge.toggle_maximize(); } catch (e) { /* تجاهل */ } };
  $("tbClose").onclick = () => { try { apiBridge.close_window(); } catch (e) { window.close(); } };
  // سحب النافذة من أي مكان فارغ بالشريط + دعم السحب المزدوج للإطار
  const drag = document.querySelector(".tb-drag");
  if (drag) {
    drag.addEventListener("dblclick", () => { try { apiBridge.toggle_maximize(); } catch (e) { /* تجاهل */ } });
  }
}

async function runBoot() {
  const boot = $("boot");
  const sub = $("bootSub");
  boot.hidden = false;
  const steps = [
    [280, "جارٍ تهيئة النظام…"],
    [760, "قراءة الأقراص والمساحات…"],
    [1250, "تحميل واجهة الخريطة…"],
    [1650, "جاهز"],
  ];
  for (const [ms, label] of steps) {
    await new Promise((r) => setTimeout(r, ms - (boot.dataset.last ? +boot.dataset.last : 0)));
    boot.dataset.last = ms;
    if (sub) sub.textContent = label;
  }
  await new Promise((r) => setTimeout(r, 180));
  boot.classList.add("out");
  setTimeout(() => { boot.hidden = true; boot.classList.remove("out"); }, 520);
}

function bump(el) {
  if (!el) return;
  el.classList.remove("bump");
  void el.offsetWidth;
  el.classList.add("bump");
}

/* ---------- stars ---------- */
function makeStars() {
  const box = $("stars");
  const n = window.innerWidth < 700 ? 40 : 90;
  let html = "";
  for (let i = 0; i < n; i++) {
    const x = Math.random() * 100, y = Math.random() * 100;
    const d = (Math.random() * 4).toFixed(2);
    const s = (Math.random() * 1.6 + 0.6).toFixed(1);
    html += `<i style="left:${x}%;top:${y}%;animation-delay:${d}s;opacity:${s}"></i>`;
  }
  box.innerHTML = html;
}

/* ---------- risk color ---------- */
function riskColor(risk) {
  return risk === "danger" ? "#ef4444" : risk === "caution" ? "#f59e0b" : "#10b981";
}
function riskOfCat(key) {
  if (!SCAN || !SCAN.categories || !SCAN.categories[key]) return "safe";
  const list = SCAN.categories[key];
  if (!list.length) return "safe";
  if (list.some((i) => i.risk === "danger")) return "danger";
  if (list.some((i) => i.risk === "caution")) return "caution";
  return "safe";
}

/* ---------- render summary + drives ---------- */
function render() {
  if (!SYSTEM) return;
  const drives = SYSTEM.drives || [];
  const totalUsed = drives.reduce((a, d) => a + d.used, 0);
  const totalFree = drives.reduce((a, d) => a + d.free, 0);
  const totalAll = totalUsed + totalFree;
  const reclaim = SCAN ? (SCAN.total_reclaimable || 0) : 0;

  $("usedVal").textContent = bytes(totalUsed);
  $("freeVal").textContent = bytes(totalFree);
  $("reclaimVal").textContent = reclaim ? bytes(reclaim) : "—";
  bump($("usedVal")); bump($("freeVal")); bump($("reclaimVal"));
  $("usedBar").style.width = totalAll ? (totalUsed / totalAll * 100) + "%" : "0%";
  $("freeBar").style.width = totalAll ? (totalFree / totalAll * 100) + "%" : "0%";
  $("reclaimBar").style.width = totalAll ? Math.min(100, reclaim / totalAll * 100) + "%" : "0%";

  const sys = SYSTEM.system || {};
  $("sysVal").textContent = `${sys.os_name || "?"} · ${sys.arch || "?"}`;
  $("version").textContent = "v" + (SCAN && SCAN.app_version ? SCAN.app_version : "1.0.0");

  renderDrives(drives);
  renderCats();
}

function renderDrives(drives) {
  const host = $("drives");
  if (!drives.length) {
    host.innerHTML = `<p class="empty-q">${t("not_found")}</p>`;
    return;
  }
  const cats = (SCAN && SCAN.categories) || {};
  const order = ["duplicates", "large", "old_downloads", "build", "installers", "logs", "temp", "empty_dirs"];

  host.innerHTML = drives.map((d) => {
    const pct = Math.min(100, d.used_pct || 0);
    const color = pct > 90 ? "#ef4444" : pct > 75 ? "#f59e0b" : "#22d3ee";
    const tiles = order.map((k) => {
      const list = cats[k] || [];
      if (!list.length) return "";
      const size = list.reduce((a, i) => a + i.size, 0);
      const risk = riskOfCat(k);
      return `<div class="tile ${risk}" data-cat="${k}" title="${t("cat_" + k)} — ${bytes(size)}">
        <span class="tn">${t("cat_" + k)}</span>
        <span class="tv">${bytes(size)}</span></div>`;
    }).join("");
    return `<div class="drive">
      <h3><span>${d.label || d.path}</span><span class="chip">${d.removable ? t("removable") : t("fixed")}</span></h3>
      <div class="drive-sub">${d.path}</div>
      <div class="dbar"><div class="dbar-fill" style="width:${pct}%;background:${color}"></div></div>
      <div class="dnums"><span class="u">${bytes(d.used)} · ${Math.round(pct)}%</span><span class="f">${bytes(d.free)}</span></div>
      <div class="tiles">${tiles || `<div class="tile empty"><span class="tn">${t("not_found")}</span></div>`}</div>
    </div>`;
  }).join("");

  host.querySelectorAll(".tile[data-cat]").forEach((el) => {
    el.onclick = () => {
      const card = document.querySelector(`.cat[data-key="${el.dataset.cat}"]`);
      if (card) {
        card.scrollIntoView({ behavior: "smooth", block: "center" });
        card.classList.add("open");
        card.classList.remove("flash");
        void card.offsetWidth;
        card.classList.add("flash");
      }
    };
  });
}

/* ---------- categories ---------- */
const CAT_ORDER = [
  ["duplicates", "safe"], ["large", "danger"], ["old_downloads", "danger"],
  ["installers", "caution"], ["build", "caution"], ["logs", "safe"],
  ["temp", "safe"], ["empty_dirs", "safe"],
];

function renderCats() {
  const host = $("cats");
  if (!SCAN) {
    host.innerHTML = `<p class="empty-cat">${t("scanning")}</p>`;
    return;
  }
  if (SCAN.error) {
    host.innerHTML = `<p class="empty-cat">${SCAN.error}</p>`;
    return;
  }
  const cats = SCAN.categories || {};
  const cards = CAT_ORDER.map(([key]) => {
    const list = cats[key] || [];
    const size = list.reduce((a, i) => a + i.size, 0);
    const risk = riskOfCat(key);
    const body = list.length
      ? `<div class="cat-reason">${reasonText(list[0])}</div>
         <div class="files">${list.slice(0, 400).map((it) => `
           <label class="file">
             <input type="checkbox" data-path="${escAttr(it.path)}" ${SELECTED.has(it.path) ? "checked" : ""}>
             <span class="fname" title="${escAttr(it.path)}">${escHtml(basename(it.path))}</span>
             <span class="fsize">${bytes(it.size)}</span>
           </label>`).join("")}</div>
         ${list.length > 400 ? `<p class="cat-reason">+${num(list.length - 400)}</p>` : ""}`
      : `<p class="empty-cat">${t("empty_cat")}</p>`;
    return `<div class="cat" data-key="${key}" data-risk="${risk}">
      <div class="cat-head">
        <span class="cat-title"><i class="risk-dot ${risk}"></i>${t("cat_" + key)}</span>
        <span class="cat-size">${list.length ? bytes(size) + " · " + num(list.length) : "—"}</span>
      </div>
      <div class="cat-body">${body}</div>
    </div>`;
  }).join("");

  host.innerHTML = cards;
  host.querySelectorAll(".cat-head").forEach((h) => {
    h.onclick = () => h.parentElement.classList.toggle("open");
  });
  host.querySelectorAll('input[type="checkbox"]').forEach((cb) => {
    cb.onchange = () => {
      if (cb.checked) SELECTED.add(cb.dataset.path); else SELECTED.delete(cb.dataset.path);
      updateSel();
    };
  });
  updateSel();
}

function reasonText(item) {
  const params = { ...(item.reason_params || {}) };
  if (params.keep) params.keep = basename(params.keep);
  return t(item.reason_key, params);
}

function basename(p) {
  const parts = String(p).split(/[\\/]/);
  return parts[parts.length - 1] || p;
}
function escHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function escAttr(s) { return escHtml(s).replace(/`/g, "&#96;"); }

function updateSel() {
  const n = SELECTED.size;
  $("selCount").textContent = num(n);
  $("cleanBtn").disabled = n === 0;
}

/* ---------- toast ---------- */
function toast(msg, kind = "") {
  const el = document.createElement("div");
  el.className = "toast " + kind;
  el.textContent = msg;
  $("toasts").appendChild(el);
  setTimeout(() => { el.style.opacity = "0"; el.style.transition = "opacity .4s"; }, 3800);
  setTimeout(() => el.remove(), 4400);
}

/* ---------- scan ---------- */
async function startScan() {
  $("scanBtn").disabled = true;
  $("progressWrap").hidden = false;
  $("progFill").style.width = "8%";
  $("progLabel").textContent = t("t_scan_start");
  SELECTED.clear();
  await api("/api/scan/start", { method: "POST" });
  if (polling) clearInterval(polling);
  polling = setInterval(pollScan, 700);
}

async function pollScan() {
  try {
    const st = await api("/api/scan/status");
    if (st.phase === "done" || st.phase === "error") {
      clearInterval(polling); polling = null;
      $("scanBtn").disabled = false;
      $("progFill").style.width = "100%";
      $("progLabel").textContent = st.phase === "error" ? t("t_scan_err") : t("t_scan_done");
      SCAN = await api("/api/scan/result");
      render();
      loadQuarantine();
      setTimeout(() => { $("progressWrap").hidden = true; }, 1600);
    } else {
      const wobble = 15 + Math.random() * 45;
      $("progFill").style.width = Math.min(96, wobble + (st.progress || 0) * 80) + "%";
    }
  } catch (e) {
    clearInterval(polling); polling = null;
    $("scanBtn").disabled = false;
  }
}

/* ---------- quarantine ---------- */
async function loadQuarantine() {
  try {
    const q = await api("/api/quarantine");
    $("qSize").textContent = bytes(q.size || 0);
    const host = $("qlist");
    if (!q.entries.length) {
      host.innerHTML = `<p class="empty-q">${t("empty_q")}</p>`;
      return;
    }
    host.innerHTML = q.entries.map((e) => `
      <div class="qrow">
        <span class="qpath" title="${escAttr(e.original_path)}">${escHtml(basename(e.original_path))}</span>
        <span class="fsize">${bytes(e.size)}</span>
        <span class="qtime">${new Date(e.quarantined_at * 1000).toLocaleString()}</span>
      </div>`).join("");
  } catch (e) { /* تجاهل */ }
}

/* ---------- modal flow ---------- */
let pendingPaths = [];
function openConfirm() {
  if (!SELECTED.size) { toast(t("t_none"), "err"); return; }
  pendingPaths = [...SELECTED];
  const size = pendingPaths.reduce((a, p) => a + (sizeOf(p)), 0);
  $("modalBody").textContent = t("no_delete_note");
  $("modalSize").textContent = bytes(size);
  const word = LANG === "ar" ? "نعم" : "YES";
  $("confirmWord").textContent = word;
  $("modalOk").dataset.word = word;
  $("confirmInput").value = "";
  $("modalOk").disabled = true;
  $("modal").hidden = false;
  $("confirmInput").focus();
}
function sizeOf(p) {
  if (!SCAN) return 0;
  for (const list of Object.values(SCAN.categories || {})) {
    const hit = list.find((i) => i.path === p);
    if (hit) return hit.size;
  }
  return 0;
}
function closeModal() { $("modal").hidden = true; pendingPaths = []; }

async function doMove() {
  try {
    const res = await api("/api/quarantine/add", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ paths: pendingPaths }),
    });
    const moved = res.moved_count || 0;
    toast(t("t_moved", { n: num(moved), size: bytes(res.bytes_freed || 0) }), "ok");
    if (res.failed_count) toast(t("t_scan_err"), "err");
    SELECTED.clear();
    closeModal();
    loadQuarantine();
    if (SYSTEM) {
      const r = await api("/api/system");
      SYSTEM = r;
      render();
    }
  } catch (e) {
    toast(String(e), "err");
  }
}

async function restoreAll() {
  try {
    const q = await api("/api/quarantine");
    const ids = q.entries.map((e) => e.id);
    if (!ids.length) return;
    const res = await api("/api/quarantine/restore", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ids }),
    });
    toast(t("t_restore", { n: num(res.restored_count) }), "ok");
    loadQuarantine();
  } catch (e) { toast(String(e), "err"); }
}

/* ---------- init ---------- */
function bind() {
  $("langBtn").onclick = toggleLang;
  $("themeBtn").onclick = toggleTheme;
  $("scanBtn").onclick = startScan;
  $("cleanBtn").onclick = openConfirm;
  $("restoreAllBtn").onclick = restoreAll;
  $("modalCancel").onclick = closeModal;
  $("modal").onclick = (e) => { if (e.target === $("modal")) closeModal(); };
  $("confirmInput").oninput = (e) => {
    $("modalOk").disabled = e.target.value.trim() !== $("modalOk").dataset.word;
  };
  $("modalOk").onclick = doMove;
  $("selectAllBtn").onclick = () => {
    if (!SCAN) return;
    const cats = SCAN.categories || {};
    ["duplicates", "temp", "logs", "empty_dirs", "installers"].forEach((k) => {
      (cats[k] || []).forEach((i) => SELECTED.add(i.path));
    });
    renderCats();
  };
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !$("modal").hidden) closeModal();
  });
}

(async function init() {
  makeStars();
  bind();
  applyTheme(localStorage.getItem("meras_theme") || "dark");
  applyLang();
  await initShell();
  try {
    SYSTEM = await api("/api/system");
    render();
    startScan();
  } catch (e) {
    toast(String(e), "err");
  }
  loadQuarantine();
})();