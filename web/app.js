/* MERAS — منطق الواجهة: التنقل، الفحص، التنظيف، السلة، الإعدادات. */
(function () {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const LS_LANG = "meras.lang";
  const LS_THEME = "meras.theme";
  const CONFIRM_WORD = { ar: "نعم", en: "YES" };
  const CAT_ORDER = [
    "large", "old_downloads", "installers", "duplicates",
    "temp", "logs", "build", "empty_dirs",
  ];
  const PHASE_LABEL = {
    start: "ph_start", walk: "ph_walk", dup: "ph_dup",
    analyze_large: "ph_analyze_large", analyze_old: "ph_analyze_old",
    analyze_types: "ph_analyze_types", analyze_build: "ph_analyze_build",
    analyze_empty: "ph_analyze_empty", limit: "ph_limit",
    done: "ph_done", error: "t_scan_err",
  };

  // بعض نسخ WebKit داخل نافذة سطح المكتب ما بتوفّر localStorage،
  // وكتابته مباشرة كانت بتوقف السكربت كله قبل ما يرسم أي شي.
  const store = {
    get(key, fallback) {
      try {
        const v = window.localStorage.getItem(key);
        return v === null || v === undefined ? fallback : v;
      } catch (e) {
        return fallback;
      }
    },
    set(key, value) {
      try {
        window.localStorage.setItem(key, value);
      } catch (e) {
        /* الوضع الخاص أو قرص ممتلئ: نتجاهل ونكمل */
      }
    },
  };

  const state = {
    lang: store.get(LS_LANG, "ar"),
    theme: store.get(LS_THEME, "dark"),
    view: "dashboard",
    system: null,
    drives: [],
    folders: {},
    result: null,
    quarantine: { entries: [], size: 0 },
    selected: new Set(),
    riskFilter: "all",
    scanning: false,
    poll: null,
    pending: null,
  };

  // ---------- أدوات مساعدة ----------

  function t(key, vars) {
    let out = (I18N[state.lang] && I18N[state.lang][key]) ||
      (I18N.ar[key]) || key;
    if (vars) {
      for (const name of Object.keys(vars)) {
        out = out.split("{" + name + "}").join(String(vars[name]));
      }
    }
    return out;
  }

  function esc(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function bytes(n) {
    n = Number(n) || 0;
    if (n <= 0) return "0 B";
    const units = ["B", "KB", "MB", "GB", "TB"];
    const i = Math.min(units.length - 1, Math.floor(Math.log(n) / Math.log(1024)));
    const v = n / Math.pow(1024, i);
    return (i === 0 ? Math.round(v) : v >= 100 ? v.toFixed(0) : v.toFixed(1)) +
      " " + units[i];
  }

  function count(n) {
    return Number(n || 0).toLocaleString(state.lang === "ar" ? "ar" : "en");
  }

  function ms(value) {
    const s = Math.round((Number(value) || 0) / 1000);
    if (s < 60) return s + "s";
    return Math.floor(s / 60) + "m " + (s % 60) + "s";
  }

  async function api(path, body) {
    const options = body
      ? {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        }
      : {};
    const res = await fetch(path, options);
    if (!res.ok) throw new Error("HTTP " + res.status);
    return res.json();
  }

  // ---------- التنبيهات ----------

  function toast(message, kind) {
    const el = document.createElement("div");
    el.className = "toast" + (kind ? " " + kind : "");
    el.textContent = message;
    $("toasts").appendChild(el);
    setTimeout(() => {
      el.classList.add("out");
      setTimeout(() => el.remove(), 400);
    }, 3600);
  }

  // ---------- التنقل ----------

  function showView(name) {
    state.view = name;
    document.querySelectorAll(".view").forEach((v) => {
      v.classList.toggle("is-active", v.id === "view-" + name);
    });
    document.querySelectorAll(".nav-item").forEach((b) => {
      const on = b.dataset.view === name;
      b.classList.toggle("is-active", on);
      b.setAttribute("aria-selected", on ? "true" : "false");
    });
    if (name === "map") renderMap();
    if (name === "cleanup") renderCleanup();
    if (name === "trash") renderTrash();
  }

  // ---------- جسر سطح المكتب ----------

  // pywebview يحقن window.pywebview بعد تحميل الصفحة، أحيانا بعد ثوان.
  // فنتسق مع حدثه الرسمي، ومعه فحص دوري يبقى مفتوحا بلا حد للوقت،
  // وكلا الطريقين ينادي نفس الدالة مرة واحدة فقط.
  function bridgeReady() {
    return !!(window.pywebview && window.pywebview.api);
  }

  let desktopAttached = false;

  function attachDesktop() {
    if (desktopAttached || !bridgeReady()) return;
    desktopAttached = true;

    document.body.dataset.shell = "desktop";
    $("titlebar").hidden = false;

    $("tbMin").addEventListener("click", () => {
      window.pywebview.api.minimize_window();
    });
    $("tbMax").addEventListener("click", async () => {
      const full = await window.pywebview.api.toggle_maximize();
      $("tbMax").classList.toggle("is-on", !!full);
    });
    $("tbClose").addEventListener("click", () => {
      window.pywebview.api.close_window();
    });

    window.pywebview.api.app_info().then((info) => {
      if (info && info.version) setVersion(info.version);
    }).catch(() => {});
  }

  function waitForBridge() {
    window.addEventListener("pywebviewready", attachDesktop);
    const poll = setInterval(() => {
      if (desktopAttached) {
        clearInterval(poll);
        return;
      }
      attachDesktop();
    }, 250);
  }

  // ---------- السمة واللغة ----------

  function setVersion(v) {
    $("version").textContent = "v" + v;
    $("setVersion").textContent = v;
  }

  function applyLang() {
    const cfg = I18N[state.lang] || I18N.ar;
    document.documentElement.lang = cfg.lang;
    document.documentElement.dir = cfg.dir;
    document.title = t("app_title") + " — " + t("app_sub");
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      el.textContent = t(el.dataset.i18n);
    });
    $("confirmWord").textContent = CONFIRM_WORD[state.lang];
    document.querySelectorAll("#langSeg .seg-btn").forEach((b) => {
      b.classList.toggle("is-on", b.dataset.lang === state.lang);
    });
    renderAll();
  }

  function setLang(lang) {
    state.lang = lang;
    store.set(LS_LANG, lang);
    applyLang();
  }

  function setTheme(theme) {
    state.theme = theme;
    store.set(LS_THEME, theme);
    document.body.dataset.theme = theme;
    document.querySelectorAll("#themeSeg .seg-btn").forEach((b) => {
      b.classList.toggle("is-on", b.dataset.themeVal === theme);
    });
  }

  // ---------- المؤشر الدائري ----------

  const GAUGE_LEN = 2 * Math.PI * 80;

  function renderGauge() {
    const drive = state.drives[0];
    const fill = $("gaugeFill");
    if (!drive || !drive.total) {
      $("gaugePct").textContent = "—";
      fill.style.strokeDashoffset = GAUGE_LEN;
      $("gUsed").textContent = "—";
      $("gFree").textContent = "—";
      return;
    }
    const pct = drive.used_pct || 0;
    $("gaugePct").textContent = pct.toFixed(0) + "%";
    $("gaugeSvg").classList.toggle("is-hot", pct >= 85);
    fill.style.strokeDasharray = GAUGE_LEN;
    fill.style.strokeDashoffset = GAUGE_LEN * (1 - Math.min(100, pct) / 100);
    $("gUsed").textContent = bytes(drive.used);
    $("gFree").textContent = bytes(drive.free);
  }

  // ---------- لوحة القيادة ----------

  function categoriesOf(result) {
    const cats = (result && result.categories) || {};
    return CAT_ORDER
      .filter((key) => (cats[key] || []).length > 0)
      .map((key) => {
        const items = cats[key];
        const size = items.reduce((sum, it) => sum + (it.size || 0), 0);
        const risk = items.some((it) => it.risk === "danger")
          ? "danger"
          : items.some((it) => it.risk === "caution") ? "caution" : "safe";
        return { key, items, size, risk };
      })
      .sort((a, b) => b.size - a.size);
  }

  function renderDashboard() {
    renderGauge();

    const cats = categoriesOf(state.result);
    const itemCount = cats.reduce((sum, c) => sum + c.items.length, 0);

    $("statReclaim").textContent = state.result
      ? bytes(state.result.total_reclaimable) : "—";
    $("statFound").textContent = state.result
      ? t("items_found") + ": " + count(itemCount)
      : t("no_scan_yet");
    $("dashSub").textContent = state.result
      ? t("scan_now_hint") : t("no_scan_yet");

    const top = cats.slice(0, 4);
    const max = top.length ? top[0].size : 0;
    $("catBars").innerHTML = top.length
      ? top.map((c) => `
        <div class="mini-bar">
          <span>${esc(t("cat_" + c.key))}</span>
          <span class="track"><i class="fill ${c.risk}" style="width:${
            max ? Math.max(4, (c.size / max) * 100) : 0}%"></i></span>
          <b>${esc(bytes(c.size))}</b>
        </div>`).join("")
      : `<div class="empty-note">${esc(t("no_scan_yet"))}</div>`;

    const tiles = [
      {
        label: t("files_scanned"),
        val: state.result ? count(state.result.files_scanned) : "—",
        cls: "",
      },
      {
        label: t("scan_time"),
        val: state.result ? ms(state.result.duration_ms) : "—",
        cls: "",
      },
      {
        label: t("items_found"),
        val: state.result ? count(itemCount) : "—",
        cls: state.result && itemCount ? "ok" : "",
      },
      {
        label: t("trash"),
        val: bytes(state.quarantine.size),
        cls: state.quarantine.size ? "warn" : "",
      },
    ];
    $("statGrid").innerHTML = tiles.map((tile) => `
      <div class="stat-tile">
        <span class="lbl">${esc(tile.label)}</span>
        <span class="val ${tile.cls}">${esc(tile.val)}</span>
      </div>`).join("");

    $("scanMeta").innerHTML = state.result
      ? `<span class="meta-pill">${esc(t("files_scanned"))} <b>${
          count(state.result.files_scanned)}</b></span>
         <span class="meta-pill">${esc(t("scan_time"))} <b>${
          ms(state.result.duration_ms)}</b></span>
         <span class="meta-pill">${esc(t("items_found"))} <b>${
          count(itemCount)}</b></span>`
      : `<div class="empty-note">${esc(t("no_scan_yet"))}</div>`;

    $("setFiles").textContent = state.result
      ? count(state.result.files_scanned) : "—";

    const removable = cats.filter((c) => c.risk === "safe")
      .reduce((sum, c) => sum + c.items.length, 0);
    $("navTrashCount").textContent = count(itemCount);
    $("navTrashCount").dataset.zero = itemCount ? "0" : "1";
    $("navTrashCount").classList.toggle("bump", removable > 0 && !itemCount);
  }

  // ---------- خريطة المساحة ----------

  const FOLDER_KEYS = ["downloads", "desktop", "videos", "pictures", "documents", "temp"];

  const FOLDER_LABEL = {
    downloads: "Downloads", desktop: "Desktop", videos: "Videos",
    pictures: "Pictures", documents: "Documents", temp: "Temp",
  };

  function riskOf(pct) {
    if (pct >= 90) return "danger";
    if (pct >= 75) return "caution";
    return "safe";
  }

  function driveHolds(drive, path) {
    if (!drive || !path) return false;
    const a = String(drive.path).toLowerCase();
    const b = String(path).toLowerCase();
    return b.startsWith(a) || a.startsWith(b);
  }

  function renderMap() {
    const box = $("drives");
    if (!state.drives.length) {
      box.innerHTML = `<div class="empty-note">${esc(t("no_results"))}</div>`;
      return;
    }
    const rootSizes = (state.result && state.result.root_sizes) || {};

    box.innerHTML = state.drives.map((d) => {
      const pct = d.used_pct || 0;
      const risk = riskOf(pct);
      const tiles = FOLDER_KEYS.map((key) => {
        const path = state.folders[key];
        if (!path || !driveHolds(d, path)) return "";
        const size = rootSizes[path] || 0;
        return `<button class="tile ${size === 0 ? "empty" : "safe"}" type="button"
                  data-tile="${esc(key)}" data-path="${esc(path)}">
          <span class="tn">${esc(FOLDER_LABEL[key])}</span>
          <span class="tv">${esc(bytes(size))}</span>
          <span class="tc">${esc(path)}</span>
        </button>`;
      }).join("");

      return `
      <article class="drive">
        <div class="drive-top">
          <div class="drive-title">
            <div>
              <h3>${esc(d.label || d.path)}</h3>
              <div class="drive-path">${esc(d.path)}</div>
            </div>
            <span class="chip">${esc(d.fstype || d.path)}</span>
          </div>
          <div class="drive-nums">
            <div class="pct">${pct.toFixed(1)}%</div>
            <div class="sub">${esc(bytes(d.free))} ${esc(t("free"))}</div>
          </div>
        </div>
        <div class="dbar">
          <div class="dbar-fill ${risk}" style="width:${Math.min(100, pct)}%"></div>
        </div>
        <div class="tiles">
          <div class="tile ${risk}">
            <span class="tn">${esc(t("used"))}</span>
            <span class="tv">${esc(bytes(d.used))}</span>
            <span class="tc">${esc(t("risk_of"))}</span>
          </div>
          <div class="tile safe">
            <span class="tn">${esc(t("free"))}</span>
            <span class="tv">${esc(bytes(d.free))}</span>
            <span class="tc">${esc(t("safe"))}</span>
          </div>
          ${tiles}
        </div>
      </article>`;
    }).join("");
  }

  // ---------- التنظيف ----------

  function visibleCategories() {
    const cats = categoriesOf(state.result);
    if (state.riskFilter === "all") return cats;
    return cats.filter((c) => c.risk === state.riskFilter);
  }

  function renderCleanup() {
    const box = $("cats");
    const cats = visibleCategories();
    if (!cats.length) {
      box.innerHTML = `<div class="empty-note">${
        esc(state.result ? t("no_results") : t("no_scan_yet"))}</div>`;
      updateSelCount();
      return;
    }
    box.innerHTML = cats.map((c) => {
      const first = c.items[0];
      const reason = first
        ? t("r_" + first.reason_key, first.reason_params) : "";
      return `
      <article class="cat" data-cat="${esc(c.key)}">
        <button class="cat-head" type="button">
          <span class="cat-title">
            <i class="risk-dot ${c.risk}"></i>
            ${esc(t("cat_" + c.key))}
            <svg class="caret" viewBox="0 0 12 12" aria-hidden="true">
              <path d="M4 2l5 4-5 4" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </span>
          <span class="cat-size">${esc(bytes(c.size))} · ${
            count(c.items.length)} ${esc(t("items"))}</span>
        </button>
        <div class="cat-body">
          <div class="cat-reason">${esc(reason)}</div>
          <div class="files">
            ${c.items.slice(0, 200).map((it) => `
              <label class="file">
                <input type="checkbox" data-path="${esc(it.path)}"
                       ${state.selected.has(it.path) ? "checked" : ""}/>
                <span class="fname" title="${esc(it.path)}">${esc(it.path)}</span>
                <span class="fsize">${esc(bytes(it.size))}</span>
              </label>`).join("")}
          </div>
        </div>
      </article>`;
    }).join("");
    updateSelCount();
  }

  function selectedBytes() {
    const cats = (state.result && state.result.categories) || {};
    let total = 0;
    for (const key of CAT_ORDER) {
      for (const it of cats[key] || []) {
        if (state.selected.has(it.path)) total += it.size || 0;
      }
    }
    return total;
  }

  function updateSelCount() {
    const n = state.selected.size;
    $("selCount").textContent = count(n);
    $("cleanBtn").disabled = n === 0;
    state.pending = n ? { n, bytesSum: selectedBytes() } : null;
  }

  function clearSelection() {
    state.selected.clear();
    document.querySelectorAll("#cats input[type=checkbox]")
      .forEach((box) => { box.checked = false; });
    updateSelCount();
  }

  function selectAllSafe() {
    if (!state.result) {
      toast(t("no_scan_yet"), "err");
      return;
    }
    state.selected.clear();
    for (const c of categoriesOf(state.result)) {
      if (c.risk !== "safe") continue;
      for (const it of c.items) state.selected.add(it.path);
    }
    renderCleanup();
    toast(t("t_selected", { n: count(state.selected.size) }));
  }

  // ---------- نافذة التأكيد ----------

  function openConfirm() {
    if (!state.pending || !state.pending.n) {
      toast(t("t_none"), "err");
      return;
    }
    $("modalTitle").textContent = t("confirm_move_title", { n: state.pending.n });
    $("modalBody").textContent = t("confirm_move_body");
    $("modalSize").textContent = bytes(state.pending.bytesSum);
    $("confirmWord").textContent = CONFIRM_WORD[state.lang];
    $("confirmInput").value = "";
    $("modalOk").disabled = true;
    $("modal").hidden = false;
    setTimeout(() => $("confirmInput").focus(), 60);
  }

  function closeConfirm() {
    $("modal").hidden = true;
    state.pending = null;
  }

  async function doMove() {
    const paths = Array.from(state.selected);
    if (!paths.length) return;
    let data;
    try {
      data = await api("/api/quarantine/add", { paths });
    } catch (err) {
      toast(t("t_scan_err") + ": " + err.message, "err");
      closeConfirm();
      return;
    }
    closeConfirm();
    state.selected.clear();
    await Promise.all([loadQuarantine(), loadScanResult()]);
    renderAll();
    toast(
      t("t_moved", { n: count(data.moved_count), size: bytes(data.bytes_freed) }),
      "ok"
    );
    if (data.failed_count) {
      toast(count(data.failed_count) + " " + t("t_scan_err"), "err");
    }
  }

  // ---------- السلة ----------

  function renderTrash() {
    const list = $("qlist");
    const entries = state.quarantine.entries || [];
    $("qSize").textContent = bytes(state.quarantine.size);
    $("navQuarCount").textContent = count(entries.length);
    $("navQuarCount").dataset.zero = entries.length ? "0" : "1";

    if (!entries.length) {
      list.innerHTML = `<div class="empty-note">${esc(t("trash_empty"))}</div>`;
      $("restoreAllBtn").disabled = true;
      return;
    }
    $("restoreAllBtn").disabled = false;
    list.innerHTML = entries.map((entry, i) => `
      <div class="qrow" style="animation-delay:${Math.min(i, 12) * 0.03}s">
        <span class="qpath" title="${esc(entry.original_path)}">${
          esc(entry.original_path)}</span>
        <span class="qsize">${esc(bytes(entry.size))}</span>
        <span class="qtime">${esc(
          new Date(entry.quarantined_at * 1000).toLocaleString())}</span>
        <button class="qbtn" type="button" data-restore="${esc(entry.id)}">${
          esc(t("restore_one"))}</button>
      </div>`).join("");
  }

  async function restore(ids) {
    if (!ids.length) {
      toast(t("t_none"), "err");
      return;
    }
    try {
      const data = await api("/api/quarantine/restore", { ids });
      await loadQuarantine();
      renderAll();
      toast(t("t_restore", { n: count((data.restored || []).length) }), "ok");
    } catch (err) {
      toast(t("t_scan_err") + ": " + err.message, "err");
    }
  }

  // ---------- الفحص ----------

  function setScanDock(on) {
    $("scanDock").hidden = !on;
    $("tbState").textContent = on ? t("scanning") : "";
  }

  function paintProgress(st) {
    const pct = Math.max(0, Math.min(100, (st.progress || 0) * 100));
    $("scanPct").textContent = pct.toFixed(0) + "%";
    $("scanFill").style.width = pct + "%";
    const key = PHASE_LABEL[st.phase];
    $("scanPhase").textContent = key ? t(key) : t("scanning");
    $("scanPath").textContent = st.detail || t("scanning_sub");
  }

  function stopPolling() {
    if (state.poll) {
      clearInterval(state.poll);
      state.poll = null;
    }
    state.scanning = false;
    $("scanBtn").disabled = false;
    setScanDock(false);
  }

  async function pollStatus() {
    let st;
    try {
      st = await api("/api/scan/status");
    } catch (err) {
      stopPolling();
      return;
    }
    paintProgress(st);
    if (!st.running) {
      stopPolling();
      await loadScanResult();
      renderAll();
      toast(t("t_scan_done"), "ok");
    }
  }

  async function startScan() {
    if (state.scanning) return;
    try {
      const res = await api("/api/scan/start", {});
      if (res.status === "already_running") state.scanning = true;
    } catch (err) {
      toast(t("t_scan_err") + ": " + err.message, "err");
      return;
    }
    state.scanning = true;
    $("scanBtn").disabled = true;
    setScanDock(true);
    $("scanPct").textContent = "0%";
    $("scanFill").style.width = "0%";
    $("scanPath").textContent = t("scanning_sub");
    toast(t("t_scan_start"));
    if (state.poll) clearInterval(state.poll);
    state.poll = setInterval(pollStatus, 260);
    pollStatus();
  }

  async function cancelScan() {
    try {
      await api("/api/scan/cancel", {});
    } catch (err) {
      /* الإلغاء غير مدعوم في الخادم، الفحص يخلص وحده */
    }
  }

  // ---------- التحميل ----------

  async function loadSystem() {
    const data = await api("/api/system");
    state.system = data.system || {};
    state.drives = data.drives || [];
    state.folders = data.folders || {};
  }

  async function loadScanResult() {
    try {
      const data = await api("/api/scan/result");
      state.result = data && data.categories ? data : null;
    } catch (err) {
      state.result = null;
    }
  }

  async function loadQuarantine() {
    try {
      const data = await api("/api/quarantine");
      state.quarantine = { entries: data.entries || [], size: data.size || 0 };
    } catch (err) {
      state.quarantine = { entries: [], size: 0 };
    }
  }

  function renderAll() {
    renderDashboard();
    renderMap();
    renderCleanup();
    renderTrash();
  }

  // ---------- الإقلاع ----------

  function makeStars() {
    const wrap = $("stars");
    if (!wrap) return;
    let html = "";
    for (let i = 0; i < 46; i++) {
      const size = (Math.random() * 2.2 + 0.8).toFixed(1);
      const left = (Math.random() * 100).toFixed(1);
      const top = (Math.random() * 100).toFixed(1);
      const delay = (Math.random() * 3).toFixed(2);
      html += `<i style="width:${size}px;height:${size}px;left:${left}%;` +
        `top:${top}%;animation-delay:${delay}s"></i>`;
    }
    wrap.innerHTML = html;
  }

  function bootStep(label, pct) {
    $("bootStep").textContent = label;
    $("bootFill").style.width = pct + "%";
  }

  async function boot() {
    const boot = $("boot");
    boot.hidden = false;
    bootStep(t("ph_start"), 12);

    setTheme(state.theme);
    makeStars();
    applyLang();
    bootStep(t("ph_walk"), 34);

    try {
      await loadSystem();
      bootStep(t("map_hint"), 62);
      await loadQuarantine();
      bootStep(t("ph_analyze_large"), 82);
      await loadScanResult();
    } catch (err) {
      /* التطبيق يفتح حتى لو رد الخادم تأخر على طلب واحد */
    }

    bootStep(t("ph_done"), 100);
    showView(state.view);
    renderAll();
    bindEvents();
    waitForBridge();
    attachDesktop();
    setTimeout(() => {
      boot.classList.add("out");
      setTimeout(() => { boot.hidden = true; }, 520);
    }, 340);
  }

  // ---------- ربط الأحداث ----------

  let bound = false;

  function bindEvents() {
    if (bound) return;
    bound = true;

    document.querySelectorAll(".nav-item").forEach((btn) => {
      btn.addEventListener("click", () => showView(btn.dataset.view));
    });

    $("scanBtn").addEventListener("click", startScan);
    $("dashScan").addEventListener("click", startScan);
    $("dashClean").addEventListener("click", () => showView("cleanup"));
    $("selectAllBtn").addEventListener("click", selectAllSafe);
    $("clearSelBtn").addEventListener("click", clearSelection);
    $("cleanBtn").addEventListener("click", openConfirm);
    $("restoreAllBtn").addEventListener("click", () => {
      restore((state.quarantine.entries || []).map((e) => e.id));
    });
    $("scanCancel").addEventListener("click", cancelScan);

    $("modalCancel").addEventListener("click", closeConfirm);
    $("modalOk").addEventListener("click", doMove);
    $("confirmInput").addEventListener("input", (ev) => {
      $("modalOk").disabled =
        ev.target.value.trim() !== CONFIRM_WORD[state.lang];
    });
    $("modal").addEventListener("click", (ev) => {
      if (ev.target === $("modal")) closeConfirm();
    });

    $("riskFilter").addEventListener("click", (ev) => {
      const chip = ev.target.closest(".chip");
      if (!chip) return;
      state.riskFilter = chip.dataset.risk;
      $("riskFilter").querySelectorAll(".chip").forEach((c) => {
        c.classList.toggle("is-on", c === chip);
      });
      renderCleanup();
    });

    $("cats").addEventListener("click", (ev) => {
      const head = ev.target.closest(".cat-head");
      if (head) {
        head.closest(".cat").classList.toggle("is-open");
        return;
      }
      const box = ev.target.closest("input[type=checkbox]");
      if (box) {
        if (box.checked) state.selected.add(box.dataset.path);
        else state.selected.delete(box.dataset.path);
        updateSelCount();
      }
    });

    $("qlist").addEventListener("click", (ev) => {
      const btn = ev.target.closest("[data-restore]");
      if (btn) restore([btn.dataset.restore]);
    });

    $("drives").addEventListener("click", (ev) => {
      if (!ev.target.closest("[data-tile]")) return;
      showView("cleanup");
      const cat = document.querySelector(".cat");
      if (cat) {
        cat.classList.add("flash");
        setTimeout(() => cat.classList.remove("flash"), 800);
      }
    });

    $("langSeg").addEventListener("click", (ev) => {
      const btn = ev.target.closest("[data-lang]");
      if (btn) setLang(btn.dataset.lang);
    });

    $("themeSeg").addEventListener("click", (ev) => {
      const btn = ev.target.closest("[data-theme-val]");
      if (btn) setTheme(btn.dataset.themeVal);
    });

    document.addEventListener("keydown", (ev) => {
      if (ev.key === "Escape" && !$("modal").hidden) closeConfirm();
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();