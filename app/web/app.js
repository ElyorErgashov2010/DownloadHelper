/* ============================================================
   Download Helper — asosiy oyna JS qismi
   Python bilan aloqa: QWebChannel (obek nomi: "dh").
   JS -> Python:  dh.xxx(...)        (slotlar web_main_window.py da)
   Python -> JS:  window.DH.call(n)  (Python runJavaScript orqali)
   ============================================================ */
"use strict";
(function () {
  const $ = (id) => document.getElementById(id);

  /* ── Python bridge ─────────────────────────────────────── */

  let bridge = null;
  function dh(name, ...args) {
    if (bridge) bridge[name](...args);
  }

  /* ── Holat ─────────────────────────────────────────────── */

  const state = {
    tab: 0,
    queueOpen: false,
    s3Open: false,
    tasks: [],
    selectedTask: null,
    retry: 2,
    prog: { value: 0, finished: null },
    progFrameReady: false,
  };

  /* ── Log box (qatorlar bo'yicha) ────────────────────────── */

  function makeLogBox(el, maxLines) {
    const lines = [];
    function nearBottom() {
      return el.scrollHeight - el.scrollTop - el.clientHeight < 48;
    }
    function append(text) {
      const stick = nearBottom();
      const parts = String(text).split("\n");
      for (const p of parts) {
        if (p === "") continue;
        lines.push(p);
        const div = document.createElement("div");
        div.textContent = p;
        el.appendChild(div);
      }
      while (lines.length > maxLines) {
        lines.shift();
        if (el.firstChild) el.removeChild(el.firstChild);
      }
      if (stick) el.scrollTop = el.scrollHeight;
    }
    function replaceLast(text) {
      const stick = nearBottom();
      if (el.lastChild) el.lastChild.textContent = text;
      else append(text);
      if (lines.length) lines[lines.length - 1] = text;
      if (stick) el.scrollTop = el.scrollHeight;
    }
    function clear() {
      lines.length = 0;
      el.innerHTML = "";
    }
    return {
      append,
      replaceLast,
      clear,
      text() { return lines.join("\n"); },
    };
  }

  const logBox = makeLogBox($("logBox"), 5000);
  const histLogBox = makeLogBox($("histLogBox"), 5000);

  /* ── Progress bar (iframe) ─────────────────────────────── */

  const progFrame = $("progressFrame");

  function pushProg() {
    if (!state.progFrameReady) return;
    progFrame.contentWindow.postMessage(
      { type: "state", value: state.prog.value, finished: state.prog.finished },
      "*"
    );
  }

  progFrame.addEventListener("message", (e) => {
    if (e.data && e.data.type === "ready") {
      state.progFrameReady = true;
      pushProg();
    }
  });

  /* ── Formni Python holatidan tiklash ────────────────────── */

  function applyForm(f) {
    if (!f) return;
    if ("command" in f) $("cmd").value = f.command;
    if ("name" in f) $("fileName").value = f.name;
    if ("dest" in f) {
      const r = document.querySelector('input[name="dest"][value="' + f.dest + '"]');
      if (r) r.checked = true;
      setDestEnabled(f.dest);
    }
    if ("local_path" in f) $("localPath").value = f.local_path;
    if ("s3_profile" in f && f.s3_profile) $("s3Profile").value = f.s3_profile;
    if ("s3_path" in f) $("s3Path").value = f.s3_path;
    if ("delete_local" in f) $("deleteLocalCb").checked = !!f.delete_local;
    if ("auto" in f) {
      $("autoCb").checked = !!f.auto;
      $("autoNormCb").disabled = !f.auto;
    }
    if ("auto_normalize" in f) $("autoNormCb").checked = !!f.auto_normalize;
    if ("retry" in f) setRetry(f.retry, false);
  }

  function setDestEnabled(dest) {
    const local = dest === "local";
    $("localPath").disabled = !local;
    $("browseBtn").disabled = !local;
    $("s3Profile").disabled = local;
    $("s3Path").disabled = local;
    $("s3SettingsBtn").disabled = local;
    $("deleteLocalCb").disabled = local;
  }

  function setRetry(n, notify) {
    state.retry = n;
    $("retryVal").textContent = String(n);
    document.querySelectorAll("#retryList .dd-item").forEach((li) => {
      li.classList.toggle("selected", Number(li.dataset.v) === n);
    });
    if (notify) dh("retrySet", n);
  }

  /* ── Python -> JS (window.DH.call orqali keladi) ────────── */

  const DH = {
    init(f) { applyForm(f); },

    focusCommand() { $("cmd").focus(); },

    logAppend(t) { logBox.append(t); },
    logReplaceLast(t) { logBox.replaceLast(t); },
    logClear() { logBox.clear(); },

    histLogAppend(t) { histLogBox.append(t); },
    histLogClear() { histLogBox.clear(); },

    progress(s) {
      if (!s) return;
      if (s.reset) {
        state.prog = { value: 0, finished: null };
        $("progressStatus").textContent = "";
        $("progressInfo").textContent = "";
        pushProg();
        return;
      }
      if (s.pct != null) state.prog.value = s.pct;
      if (s.finished != null) {
        state.prog.finished = s.finished;
        if (s.finished) state.prog.value = 100;
      }
      if (s.status != null) $("progressStatus").textContent = s.status;
      if (s.info != null) $("progressInfo").textContent = s.info;
      pushProg();
    },

    toolsStatusUpdate(items) {
      const el = $("toolsStatus");
      const paths = [];
      el.innerHTML = "";
      if (!items || !items.length) {
        el.textContent = "\u00a0";
        return;
      }
      items.forEach((t, i) => {
        if (i > 0) {
          const sep = document.createElement("span");
          sep.innerHTML = "&nbsp;&nbsp;|&nbsp;&nbsp;";
          el.appendChild(sep);
        }
        const dot = document.createElement("span");
        dot.className = t.found ? "ok" : "bad";
        dot.textContent = "\u25cf";
        el.appendChild(dot);
        el.appendChild(document.createTextNode(" "));
        const b = document.createElement("b");
        b.textContent = t.name;
        el.appendChild(b);
        el.appendChild(document.createTextNode(t.found ? " \u2014 Tayyor" : " \u2014 Topilmadi"));
        paths.push(t.name + ": " + (t.found ? t.path : "Topilmadi"));
      });
      el.title = paths.join("\n");
    },

    busy(d, s, c, o) {
      $("downloadBtn").disabled = !d;
      $("stopBtn").disabled = !s;
      $("clearFormBtn").disabled = !c;
      $("openFolderBtn").disabled = !o;
    },

    queueUpdate(items) {
      const ul = $("queueList");
      ul.innerHTML = "";
      (items || []).forEach((q, i) => {
        const li = document.createElement("li");
        const label = document.createElement("label");
        const cb = document.createElement("input");
        cb.type = "checkbox";
        cb.dataset.i = i;
        const span = document.createElement("span");
        span.textContent = (i + 1) + ". " + q.name + "  [" + q.dest + "]";
        label.appendChild(cb);
        label.appendChild(span);
        li.appendChild(label);
        li.addEventListener("click", (e) => {
          if (e.target === cb) return;
          cb.checked = !cb.checked;
          li.classList.toggle("selected", cb.checked);
        });
        cb.addEventListener("change", () => li.classList.toggle("selected", cb.checked));
        ul.appendChild(li);
      });
      const n = (items || []).length;
      const t = $("queueToggle");
      const arrow = state.queueOpen ? "\u25bc" : "\u25b6";
      const act = state.queueOpen ? "Yashirish" : "Ko'rsatish";
      t.innerHTML = "";
      t.appendChild(document.createTextNode(arrow + " Navbat (" + n + ") \u2014 " + act));
    },

    s3FailuresUpdate(items) {
      const n = (items || []).length;
      const ul = $("s3FailList");
      ul.innerHTML = "";
      (items || []).forEach((f, i) => {
        const li = document.createElement("li");
        const label = document.createElement("label");
        const cb = document.createElement("input");
        cb.type = "checkbox";
        cb.dataset.i = i;
        const span = document.createElement("span");
        span.textContent = (i + 1) + ". " + f.name + "  \u2014  " + f.error;
        label.appendChild(cb);
        label.appendChild(span);
        li.appendChild(label);
        li.addEventListener("click", (e) => {
          if (e.target === cb) return;
          cb.checked = !cb.checked;
          li.classList.toggle("selected", cb.checked);
        });
        cb.addEventListener("change", () => li.classList.toggle("selected", cb.checked));
        ul.appendChild(li);
      });
      const t = $("s3Toggle");
      t.hidden = n === 0;
      if (n === 0) {
        state.s3Open = false;
        $("s3FailList").hidden = true;
        $("s3RetryAllBtn").hidden = true;
        $("s3RetrySelBtn").hidden = true;
        $("s3ClearBtn").hidden = true;
      }
      const arrow = state.s3Open ? "\u25bc" : "\u25b6";
      t.innerHTML = "";
      t.appendChild(document.createTextNode(arrow + " S3 xatolari (" + n + ")"));
    },

    s3FailuresOpen() {
      state.s3Open = true;
      $("s3Toggle").hidden = false;
      $("s3FailList").hidden = false;
      $("s3RetryAllBtn").hidden = false;
      $("s3RetrySelBtn").hidden = false;
      $("s3ClearBtn").hidden = false;
      DH.s3FailuresUpdate(window.__lastS3Fails || []);
    },

    tasksUpdate(tasks) {
      state.tasks = tasks || [];
      const tb = $("taskRows");
      tb.innerHTML = "";
      state.tasks.forEach((t) => {
        const tr = document.createElement("tr");
        tr.dataset.id = t.id;
        if (t.id === state.selectedTask) tr.classList.add("selected");
        const cells = [t.name, t.status, t.date, t.dest];
        cells.forEach((c, i) => {
          const td = document.createElement("td");
          td.textContent = c;
          if (i === 0) td.className = "c-name";
          if (i === 1) td.className = "st-" + t.status;
          tr.appendChild(td);
        });
        tr.addEventListener("click", () => {
          state.selectedTask = t.id;
          tb.querySelectorAll("tr").forEach((x) => x.classList.remove("selected"));
          tr.classList.add("selected");
        });
        tb.appendChild(tr);
      });
    },

    showTab(i) { setTab(i, false); },

    s3Profiles(names, active) {
      const sel = $("s3Profile");
      sel.innerHTML = "";
      (names || []).forEach((n) => {
        const o = document.createElement("option");
        o.value = n;
        o.textContent = n;
        sel.appendChild(o);
      });
      if (active && names && names.indexOf(active) !== -1) sel.value = active;
    },
  };

  // Python uchun dispatcher
  window.DH = {
    call(name, args) {
      if (typeof DH[name] === "function") DH[name](...args);
    },
  };
  // s3FailuresOpen uchun oxirgi ro'yxatni eslab turish
  const _origS3 = DH.s3FailuresUpdate.bind(DH);
  DH.s3FailuresUpdate = (items) => { window.__lastS3Fails = items; _origS3(items); };

  /* ── Tablar ────────────────────────────────────────────── */

  function setTab(i, notify) {
    state.tab = i;
    document.querySelectorAll(".tab").forEach((t) =>
      t.classList.toggle("active", Number(t.dataset.tab) === i)
    );
    $("tab-new").classList.toggle("active", i === 0);
    $("tab-history").classList.toggle("active", i === 1);
    if (notify) dh("tabChanged", i);
  }
  document.querySelectorAll(".tab").forEach((t) =>
    t.addEventListener("click", () => setTab(Number(t.dataset.tab), true))
  );

  /* ── Form maydonlari (debounce bilan sinxron) ───────────── */

  function debounce(fn, ms) {
    let t = null;
    return function (...a) {
      clearTimeout(t);
      t = setTimeout(() => fn(...a), ms);
    };
  }

  $("cmd").addEventListener("input", debounce(() => dh("commandSet", $("cmd").value), 150));
  $("cmd").addEventListener("paste", () => dh("pasted", $("cmd").value));
  $("fileName").addEventListener("input", debounce(() => dh("nameSet", $("fileName").value), 150));
  $("localPath").addEventListener("input", debounce(() => dh("localPathSet", $("localPath").value), 150));
  $("s3Path").addEventListener("input", debounce(() => dh("s3PathSet", $("s3Path").value), 150));
  $("s3Profile").addEventListener("change", () => dh("s3ProfileSet", $("s3Profile").value));
  $("deleteLocalCb").addEventListener("change", () => dh("deleteLocalSet", $("deleteLocalCb").checked));
  $("autoCb").addEventListener("change", () => {
    $("autoNormCb").disabled = !$("autoCb").checked;
    dh("autoSet", $("autoCb").checked);
  });
  $("autoNormCb").addEventListener("change", () => dh("autoNormalizeSet", $("autoNormCb").checked));
  document.querySelectorAll('input[name="dest"]').forEach((r) =>
    r.addEventListener("change", () => {
      setDestEnabled(r.value);
      dh("destSet", r.value);
    })
  );

  /* ── Tugmalar ──────────────────────────────────────────── */

  $("parseBtn").addEventListener("click", () => dh("parse"));
  $("pasteBtn").addEventListener("click", () => dh("paste"));
  $("normalizeBtn").addEventListener("click", () => dh("normalize"));
  $("toolsRefreshBtn").addEventListener("click", () => dh("refreshTools"));
  $("browseBtn").addEventListener("click", () => dh("browseLocal"));
  $("s3SettingsBtn").addEventListener("click", () => dh("s3Settings"));
  $("helpBtn").addEventListener("click", () => dh("help"));
  $("autoHelpBtn").addEventListener("click", () => dh("autoHelp"));
  $("downloadBtn").addEventListener("click", () => dh("download"));
  $("addQueueBtn").addEventListener("click", () => dh("addQueue"));
  $("stopBtn").addEventListener("click", () => dh("stop"));
  $("clearFormBtn").addEventListener("click", () => dh("clearForm"));
  $("openFolderBtn").addEventListener("click", () => dh("openFolder"));
  $("logCopyBtn").addEventListener("click", () => dh("logCopy", logBox.text()));
  $("logSaveBtn").addEventListener("click", () => dh("logSave", logBox.text()));
  $("histLogCopyBtn").addEventListener("click", () => dh("histLogCopy", histLogBox.text()));
  $("histLogSaveBtn").addEventListener("click", () => dh("histLogSave", histLogBox.text()));

  $("viewLogsBtn").addEventListener("click", () => {
    if (state.selectedTask != null) dh("viewTaskLogs", state.selectedTask);
  });
  $("redownloadBtn").addEventListener("click", () => {
    if (state.selectedTask != null) dh("redownloadTask", state.selectedTask);
  });
  $("deleteTaskBtn").addEventListener("click", () => {
    if (state.selectedTask != null) dh("deleteTask", state.selectedTask);
  });

  /* ── Navbat ────────────────────────────────────────────── */

  $("queueToggle").addEventListener("click", () => {
    state.queueOpen = !state.queueOpen;
    $("queueList").hidden = !state.queueOpen;
    $("queueRemoveBtn").hidden = !state.queueOpen;
    $("queueClearBtn").hidden = !state.queueOpen;
    $("queueToggle").classList.toggle("on", state.queueOpen);
    DH.queueUpdate(window.__lastQueue || []);
  });
  const _origQueue = DH.queueUpdate.bind(DH);
  DH.queueUpdate = (items) => { window.__lastQueue = items; _origQueue(items); };

  function checkedIndexes(ul) {
    return Array.from(ul.querySelectorAll('input[type="checkbox"]:checked'))
      .map((cb) => Number(cb.dataset.i));
  }
  $("queueRemoveBtn").addEventListener("click", () => dh("queueRemove", checkedIndexes($("queueList"))));
  $("queueClearBtn").addEventListener("click", () => dh("queueClear"));

  /* ── S3 xatolari ───────────────────────────────────────── */

  $("s3Toggle").addEventListener("click", () => {
    state.s3Open = !state.s3Open;
    $("s3FailList").hidden = !state.s3Open;
    $("s3RetryAllBtn").hidden = !state.s3Open;
    $("s3RetrySelBtn").hidden = !state.s3Open;
    $("s3ClearBtn").hidden = !state.s3Open;
    DH.s3FailuresUpdate(window.__lastS3Fails || []);
  });
  $("s3RetryAllBtn").addEventListener("click", () => dh("s3RetryAll"));
  $("s3RetrySelBtn").addEventListener("click", () => dh("s3RetrySelected", checkedIndexes($("s3FailList"))));
  $("s3ClearBtn").addEventListener("click", () => dh("s3FailClear"));

  /* ── Qayta urinish dropdown (1..10) ────────────────────── */

  const retryDd = $("retryDd");
  const retryList = $("retryList");
  for (let n = 1; n <= 10; n++) {
    const li = document.createElement("div");
    li.className = "dd-item";
    li.dataset.v = n;
    li.textContent = String(n);
    li.addEventListener("click", (e) => {
      e.stopPropagation();
      setRetry(n, true);
      closeRetry();
    });
    retryList.appendChild(li);
  }
  function openRetry() {
    retryList.classList.add("open");
    $("retryBtn").classList.add("open");
  }
  function closeRetry() {
    retryList.classList.remove("open");
    $("retryBtn").classList.remove("open");
  }
  $("retryBtn").addEventListener("click", (e) => {
    e.stopPropagation();
    if (retryList.classList.contains("open")) closeRetry();
    else openRetry();
  });
  document.addEventListener("click", (e) => {
    if (!retryDd.contains(e.target)) closeRetry();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeRetry();
    if (e.key === "F1") {
      e.preventDefault();
      dh("help");
    }
  });

  /* ── Tashqi havolalar ──────────────────────────────────── */

  document.querySelectorAll("a[data-ext]").forEach((a) =>
    a.addEventListener("click", (e) => {
      e.preventDefault();
      dh("openUrl", a.dataset.ext);
    })
  );

  /* ── QWebChannel ulanish ───────────────────────────────── */

  function connect(channel) {
    bridge = channel.objects.dh;
    if (bridge && bridge.loaded) bridge.loaded();
  }

  if (window.qt && qt.webChannelTransport) {
    new QWebChannel(qt.webChannelTransport, connect);
  } else {
    // oddiy brauzerda (dev) ochilganda — Python yo'q
    console.warn("QWebChannel topilmadi — sahifa faqat ko'rish uchun.");
  }
})();
