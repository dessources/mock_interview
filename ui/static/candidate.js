/* ============================================================================
   HackerRank Project-Style Assessment IDE — Candidate Client Logic
   ============================================================================ */

(function () {
  "use strict";

  const CUSTOM_TEMPLATES = {
    count_dropped_bytes: JSON.stringify(
      [
        [
          "1700000001 SRC=192.168.1.10 DST=10.0.0.5 PORT=443 ACTION=DROP BYTES=1200",
          "1700000002 SRC=192.168.1.20 DST=10.0.0.5 PORT=80 ACTION=ALLOW BYTES=5000",
          "1700000003 SRC=192.168.1.10 DST=10.0.0.6 PORT=22 ACTION=DROP BYTES=800",
        ],
      ],
      null,
      2
    ),
    count_valid_dropped_bytes: JSON.stringify(
      [
        [
          "1700000010 ACTION=DROP BYTES=500 SRC=10.1.1.1 DST=10.0.0.1 PORT=8080",
          "1700000011 SRC=10.01.1.1 DST=10.0.0.1 PORT=80 ACTION=DROP BYTES=1000",
          "1700000012 SRC=999.1.1.1 DST=10.0.0.1 PORT=80 ACTION=DROP BYTES=9999",
          "1700000013 SRC=10.1.1.3 DST=10.0.0.1 PORT=22 ACTION=DROP BYTES=300",
        ],
      ],
      null,
      2
    ),
    top_dropped_sources: JSON.stringify(
      [
        [
          "1700000001 SRC=192.168.1.10 DST=10.0.0.5 PORT=443 ACTION=DROP BYTES=1200",
          "1700000002 SRC=172.16.0.5 DST=10.0.0.5 PORT=443 ACTION=DROP BYTES=2000",
          "1700000003 SRC=192.168.1.10 DST=10.0.0.6 PORT=22 ACTION=DROP BYTES=800",
        ],
        2,
      ],
      null,
      2
    ),
  };

  const state = {
    activePart: 1,
    unlockedParts: [1],
    files: [],
    openTabs: ["solution.py", "sample_tests.py"],
    activeFile: "solution.py",
    fileMeta: {},
    fileCache: {},
    dirtyFiles: new Set(),
    lastProblemHash: null,
    lastSolutionHash: null,
    saveTimer: null,
    isRunning: false,
    fontSize: 13.5,
    timer: { duration_sec: 3600, remaining_sec: 3600, running: false },
    lastReport: null,
    selectedCaseIdx: 0,
    ignoreChangeEvent: false,
  };

  let editor = null;

  // DOM helpers
  const $ = (id) => document.getElementById(id);

  function showToast(msg, isError = false) {
    const container = $("toastContainer");
    const el = document.createElement("div");
    el.className = "toast" + (isError ? " error" : "");
    el.textContent = msg;
    container.appendChild(el);
    setTimeout(() => {
      el.style.opacity = "0";
      el.style.transition = "opacity 0.25s ease";
      setTimeout(() => el.remove(), 260);
    }, 3400);
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function setSaveStatus(status) {
    const dot = $("saveStatus").querySelector(".save-dot");
    const txt = $("saveStatus").querySelector(".save-text");
    if (status === "saved") {
      dot.className = "save-dot saved";
      txt.textContent = "Saved";
    } else if (status === "saving") {
      dot.className = "save-dot dirty";
      txt.textContent = "Saving...";
    } else {
      dot.className = "save-dot dirty";
      txt.textContent = "Unsaved";
    }
  }

  // ==========================================================================
  // CODEMIRROR EDITOR INITIALIZATION
  // ==========================================================================

  function initEditor() {
    editor = CodeMirror.fromTextArea($("codeEditor"), {
      mode: "python",
      lineNumbers: true,
      indentUnit: 4,
      tabSize: 4,
      indentWithTabs: false,
      styleActiveLine: true,
      matchBrackets: true,
      autoCloseBrackets: true,
      lineWrapping: false,
      extraKeys: {
        Tab: (cm) => {
          if (cm.somethingSelected()) {
            cm.indentSelection("add");
          } else {
            cm.replaceSelection("    ", "end");
          }
        },
        "Shift-Tab": (cm) => cm.indentSelection("subtract"),
        "Ctrl-/": "toggleComment",
        "Cmd-/": "toggleComment",
        "Ctrl-S": () => {
          saveCurrentFile(true);
        },
        "Cmd-S": () => {
          saveCurrentFile(true);
        },
        "Ctrl-Enter": () => {
          runTests("sample");
        },
        "Cmd-Enter": () => {
          runTests("sample");
        },
      },
    });

    editor.on("change", () => {
      if (state.ignoreChangeEvent) return;
      const meta = state.fileMeta[state.activeFile];
      if (!meta || !meta.editable) return;

      state.fileCache[state.activeFile] = editor.getValue();
      state.dirtyFiles.add(state.activeFile);
      setSaveStatus("dirty");
      renderEditorTabs();

      if (state.saveTimer) clearTimeout(state.saveTimer);
      state.saveTimer = setTimeout(() => saveCurrentFile(false), 650);
    });

    // Global keyboard shortcut fallback inside VS Code Simple Browser
    window.addEventListener("keydown", (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s") {
        e.preventDefault();
        saveCurrentFile(true);
      } else if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        runTests("sample");
      }
    });
  }

  // ==========================================================================
  // API CALLS & FILE MANAGEMENT
  // ==========================================================================

  async function apiGet(url) {
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  }

  async function apiPost(url, body) {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
    return data;
  }

  async function openFile(fname, forceReload = false) {
    if (state.dirtyFiles.has(state.activeFile) && state.activeFile !== fname) {
      await saveCurrentFile(false);
    }

    if (!state.openTabs.includes(fname)) {
      state.openTabs.push(fname);
    }
    state.activeFile = fname;

    if (forceReload || state.fileCache[fname] === undefined) {
      const data = await apiGet(`/api/file?name=${encodeURIComponent(fname)}`);
      state.fileCache[fname] = data.content;
      if (fname === "solution.py") {
        state.lastSolutionHash = data.hash;
      }
    }

    const meta = state.fileMeta[fname] || { editable: false, language: "python" };
    state.ignoreChangeEvent = true;
    editor.setOption("mode", meta.language === "markdown" ? "markdown" : "python");
    editor.setOption("readOnly", !meta.editable);
    editor.setValue(state.fileCache[fname] || "");
    editor.clearHistory();
    state.ignoreChangeEvent = false;
    setTimeout(() => editor.refresh(), 10);

    $("readonlyBanner").classList.toggle("hidden", meta.editable);
    renderFileTree();
    renderEditorTabs();
  }

  async function saveCurrentFile(explicit = false) {
    const fname = state.activeFile;
    const meta = state.fileMeta[fname];
    if (!meta || !meta.editable) return;

    if (state.saveTimer) {
      clearTimeout(state.saveTimer);
      state.saveTimer = null;
    }

    const content = editor.getValue();
    state.fileCache[fname] = content;
    setSaveStatus("saving");
    try {
      const res = await apiPost("/api/file", { name: fname, content });
      if (fname === "solution.py") {
        state.lastSolutionHash = res.hash;
      }
      state.dirtyFiles.delete(fname);
      setSaveStatus("saved");
      renderEditorTabs();
      if (explicit) showToast(`Saved ${fname}`);
    } catch (err) {
      setSaveStatus("dirty");
      showToast(`Failed to save ${fname}: ${err.message}`, true);
    }
  }

  // ==========================================================================
  // RENDERING UI COMPONENTS
  // ==========================================================================

  function renderFileTree() {
    const ul = $("fileTree");
    ul.innerHTML = "";
    state.files.forEach((f) => {
      const li = document.createElement("li");
      li.className = "file-item" + (f.name === state.activeFile ? " active" : "");
      const icon = f.name.endsWith(".md") ? "&#128196;" : "&#128013;";
      const roTag = f.editable ? "" : `<span class="file-ro-tag">RO</span>`;
      const dirtyDot = state.dirtyFiles.has(f.name) ? " &#9679;" : "";
      li.innerHTML = `
        <span class="file-item-left">
          <span>${icon}</span>
          <span>${escapeHtml(f.name)}${dirtyDot}</span>
        </span>
        ${roTag}
      `;
      li.addEventListener("click", () => openFile(f.name));
      ul.appendChild(li);
    });
  }

  function renderEditorTabs() {
    const bar = $("editorTabs");
    bar.innerHTML = "";
    state.openTabs.forEach((fname) => {
      const btn = document.createElement("button");
      btn.className = "editor-tab" + (fname === state.activeFile ? " active" : "");
      const dirty = state.dirtyFiles.has(fname) ? " ●" : "";
      btn.textContent = fname + dirty;
      btn.addEventListener("click", () => openFile(fname));
      bar.appendChild(btn);
    });
  }

  function renderProblem(problemMd) {
    if (window.marked) {
      $("problemContent").innerHTML = window.marked.parse(problemMd);
    } else {
      $("problemContent").textContent = problemMd;
    }
  }

  function renderPartPills(unlockedParts, partScores) {
    [1, 2, 3].forEach((p) => {
      const pill = $(`pillPart${p}`);
      const scoreEl = $(`scorePart${p}`);
      const isUnlocked = unlockedParts.includes(p);

      pill.disabled = !isUnlocked;
      pill.classList.toggle("locked", !isUnlocked);
      pill.classList.toggle("active", p === state.activePart);

      const lockSpan = pill.querySelector(".pill-lock");
      const dotSpan = pill.querySelector(".pill-dot");
      if (isUnlocked && lockSpan) {
        lockSpan.outerHTML = `<span class="pill-dot"></span>`;
      } else if (!isUnlocked && dotSpan && p > 1) {
        dotSpan.outerHTML = `<span class="pill-lock">&#128274;</span>`;
      }

      const sc = partScores && (partScores[p] || partScores[String(p)]);
      if (sc && isUnlocked) {
        scoreEl.textContent = `${sc.passed}/${sc.total}`;
      } else {
        scoreEl.textContent = "";
      }
    });

    if (!unlockedParts.includes(state.activePart)) {
      state.activePart = 1;
    }
    $("activeTargetLabel").textContent = `Target: Part ${state.activePart}`;
  }

  function renderSubmissions(submissions) {
    $("subCountBadge").textContent = String(submissions.length);
    const list = $("submissionsList");
    if (!submissions.length) {
      list.innerHTML = `<div class="empty-state">No test runs yet. Click <strong>Run Code</strong> or <strong>Submit Code</strong> to evaluate your solution.</div>`;
      return;
    }
    list.innerHTML = submissions
      .map((s) => {
        const ok = !s.compile_error && s.passed === s.total && s.total > 0;
        const badgeCls = ok ? "pass" : "fail";
        const modeLabel = s.mode === "submit" ? "Submit" : "Sample Run";
        const scoreStr = s.compile_error ? "Syntax Error" : `${s.passed}/${s.total} Passed`;
        return `
          <div class="sub-card">
            <div class="sub-card-top">
              <strong>Part ${s.part} &middot; ${modeLabel}</strong>
              <span class="sub-badge ${badgeCls}">${scoreStr}</span>
            </div>
            <div class="muted">${escapeHtml(s.timestamp)} &middot; ${s.total_ms} ms</div>
          </div>
        `;
      })
      .join("");
  }

  function formatTimer(sec) {
    const s = Math.max(0, Math.floor(sec));
    const mins = Math.floor(s / 60);
    const secs = s % 60;
    return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  }

  function renderTimer() {
    const el = $("timerDisplay");
    $("timerText").textContent = formatTimer(state.timer.remaining_sec);
    el.classList.remove("warning", "danger");
    if (state.timer.remaining_sec <= 300) {
      el.classList.add("danger");
    } else if (state.timer.remaining_sec <= 600) {
      el.classList.add("warning");
    }
  }

  // ==========================================================================
  // TEST RUNNER & RESULTS RENDERING
  // ==========================================================================

  function switchConsoleTab(tabName) {
    document.querySelectorAll(".console-tab").forEach((t) => {
      t.classList.toggle("active", t.dataset.consoleTab === tabName);
    });
    $("consoleTabResults").classList.toggle("hidden", tabName !== "results");
    $("consoleTabCustom").classList.toggle("hidden", tabName !== "custom");
    $("consoleTabOutput").classList.toggle("hidden", tabName !== "output");
  }

  async function runTests(mode) {
    if (state.isRunning) return;
    state.isRunning = true;
    $("runSampleBtn").disabled = true;
    $("submitCodeBtn").disabled = true;

    switchConsoleTab("results");
    $("resultsEmpty").classList.add("hidden");
    $("resultsCompileError").classList.add("hidden");
    $("resultsGrid").classList.add("hidden");
    $("resultsLoading").classList.remove("hidden");
    $("loadingText").textContent =
      mode === "submit"
        ? `Submitting Part ${state.activePart} against Sample + Hidden & Stress Tests...`
        : `Running Part ${state.activePart} Sample Test Cases...`;

    try {
      // Ensure any edited file (like sample_tests.py or solution.py) is saved first
      if (state.dirtyFiles.has(state.activeFile)) {
        await saveCurrentFile(false);
      }

      const solutionCode =
        state.activeFile === "solution.py"
          ? editor.getValue()
          : state.fileCache["solution.py"];

      const data = await apiPost("/api/run", {
        part: state.activePart,
        mode,
        code: solutionCode,
      });

      state.lastReport = data.report;
      renderPartPills(state.unlockedParts, data.part_scores);
      renderTestReport(data.report, mode);
      await pollState();
    } catch (err) {
      $("resultsLoading").classList.add("hidden");
      $("resultsCompileError").classList.remove("hidden");
      $("compileErrorText").textContent = err.message;
      showToast(`Execution error: ${err.message}`, true);
    } finally {
      state.isRunning = false;
      $("runSampleBtn").disabled = false;
      $("submitCodeBtn").disabled = false;
    }
  }

  function renderTestReport(report, mode) {
    $("resultsLoading").classList.add("hidden");

    if (report.compile_error) {
      $("resultsCompileError").classList.remove("hidden");
      $("compileErrorText").textContent = report.compile_error;
      return;
    }

    $("resultsGrid").classList.remove("hidden");
    const allPass = report.passed === report.total && report.total > 0;
    const verdictEl = $("summaryVerdict");
    verdictEl.textContent = allPass
      ? mode === "submit"
        ? "All Test Cases Passed!"
        : "Sample Tests Passed!"
      : "Some Test Cases Failed";
    verdictEl.className = "summary-verdict " + (allPass ? "all-pass" : "some-fail");
    $("summaryCount").textContent = `${report.passed} / ${report.total} Test Cases Passed`;
    $("summaryTime").textContent = `Total: ${report.total_ms} ms`;

    // Collect stdout across sample tests for Console tab
    const stdoutChunks = [];
    report.cases.forEach((c) => {
      if (!c.is_hidden && c.stdout && c.stdout.trim()) {
        stdoutChunks.push(`--- Test Case ${c.index} (${c.name}) ---\n${c.stdout.trim()}`);
      }
    });
    $("globalStdoutBox").textContent = stdoutChunks.length
      ? stdoutChunks.join("\n\n")
      : "(No stdout printed during sample test execution)";

    const listEl = $("testCaseList");
    listEl.innerHTML = "";
    const firstFailIdx = report.cases.findIndex((c) => !c.passed);
    state.selectedCaseIdx = firstFailIdx >= 0 ? firstFailIdx : 0;

    report.cases.forEach((c, idx) => {
      const btn = document.createElement("button");
      btn.className = "tc-pill" + (idx === state.selectedCaseIdx ? " active" : "");
      let iconHtml = `<span class="tc-icon-pass">&#10004;</span>`;
      if (!c.passed) {
        iconHtml =
          c.status === "TLE"
            ? `<span class="tc-icon-tle">&#9201;</span>`
            : `<span class="tc-icon-fail">&#10008;</span>`;
      }
      const label = c.is_hidden ? `&#128274; Hidden Case ${idx}` : `Sample Case ${idx}`;
      btn.innerHTML = `
        <span class="tc-pill-left">${iconHtml}<span class="tc-pill-name">${label}</span></span>
        <span class="tc-time">${c.elapsed_ms} ms</span>
      `;
      btn.addEventListener("click", () => {
        state.selectedCaseIdx = idx;
        listEl.querySelectorAll(".tc-pill").forEach((el, i) => {
          el.classList.toggle("active", i === idx);
        });
        renderCaseDetail(c);
      });
      listEl.appendChild(btn);
    });

    if (report.cases.length > 0) {
      renderCaseDetail(report.cases[state.selectedCaseIdx]);
    }

    if (allPass && mode === "submit") {
      showToast(`Part ${state.activePart}: All ${report.total}/${report.total} tests passed!`);
    }
  }

  function renderCaseDetail(c) {
    const detail = $("testCaseDetail");
    const statusLabel = c.status.replace(/_/g, " ");

    if (c.is_hidden) {
      let html = `
        <div class="detail-header">
          <span class="detail-title">&#128274; ${escapeHtml(c.name)}</span>
          <span class="status-chip ${escapeHtml(c.status)}">${escapeHtml(statusLabel)} &middot; ${c.elapsed_ms} ms</span>
        </div>
        <div class="hidden-lock-card">
          <div class="hidden-lock-title">Hidden Test Case (Locked)</div>
          <div class="muted">Input and expected output are hidden to simulate the HackerRank judge environment.</div>
        </div>
      `;
      if (!c.passed && c.hint) {
        html += `
          <div class="detail-section">
            <div class="detail-label">Category Hint</div>
            <pre class="code-box">${escapeHtml(c.hint)}</pre>
          </div>
        `;
      }
      if (c.error) {
        html += `
          <div class="detail-section">
            <div class="detail-label">Error Details</div>
            <pre class="code-box error-box">${escapeHtml(c.error)}</pre>
          </div>
        `;
      }
      detail.innerHTML = html;
      return;
    }

    let html = `
      <div class="detail-header">
        <span class="detail-title">${escapeHtml(c.name)} <span class="muted">(${escapeHtml(c.fn)})</span></span>
        <span class="status-chip ${escapeHtml(c.status)}">${escapeHtml(statusLabel)} &middot; ${c.elapsed_ms} ms</span>
      </div>
      <div class="detail-section">
        <div class="detail-label">Input Arguments</div>
        <pre class="code-box">${escapeHtml(c.input_preview || "")}</pre>
      </div>
      <div class="detail-section">
        <div class="detail-label">Your Output</div>
        <pre class="code-box ${c.passed ? "" : "error-box"}">${escapeHtml(c.actual_preview || "")}</pre>
      </div>
      <div class="detail-section">
        <div class="detail-label">Expected Output</div>
        <pre class="code-box">${escapeHtml(c.expected_preview || "")}</pre>
      </div>
    `;

    if (c.error) {
      html += `
        <div class="detail-section">
          <div class="detail-label">Traceback / Error</div>
          <pre class="code-box error-box">${escapeHtml(c.error)}</pre>
        </div>
      `;
    }

    if (c.stdout && c.stdout.trim()) {
      html += `
        <div class="detail-section">
          <div class="detail-label">Debug Output (stdout)</div>
          <pre class="code-box">${escapeHtml(c.stdout.trim())}</pre>
        </div>
      `;
    }

    detail.innerHTML = html;
  }

  // ==========================================================================
  // CUSTOM INPUT EXECUTION
  // ==========================================================================

  async function runCustomInput() {
    const fn = $("customFnSelect").value;
    const raw = $("customArgsInput").value;
    let parsedArgs;
    try {
      parsedArgs = JSON.parse(raw);
      if (!Array.isArray(parsedArgs)) {
        throw new Error("Top-level JSON must be an array of function arguments.");
      }
    } catch (err) {
      $("customResultBox").textContent = `Invalid JSON arguments:\n${err.message}`;
      return;
    }

    $("runCustomBtn").disabled = true;
    $("customResultBox").textContent = "Running custom input...";
    $("customElapsed").textContent = "";

    try {
      if (state.dirtyFiles.has(state.activeFile)) {
        await saveCurrentFile(false);
      }
      const solutionCode =
        state.activeFile === "solution.py"
          ? editor.getValue()
          : state.fileCache["solution.py"];

      const res = await apiPost("/api/custom-run", {
        fn,
        args: parsedArgs,
        code: solutionCode,
      });

      $("customElapsed").textContent = `${res.elapsed_ms || 0} ms`;
      if (res.status === "OK") {
        let out = `Return Value:\n${res.result_repr}`;
        if (res.stdout && res.stdout.trim()) {
          out += `\n\nStdout:\n${res.stdout.trim()}`;
        }
        $("customResultBox").textContent = out;
      } else {
        $("customResultBox").textContent =
          `${res.status}:\n${res.error || "Unknown error"}` +
          (res.stdout ? `\n\nStdout:\n${res.stdout}` : "");
      }
    } catch (err) {
      $("customResultBox").textContent = `Error: ${err.message}`;
    } finally {
      $("runCustomBtn").disabled = false;
    }
  }

  // ==========================================================================
  // LIVE POLLING (Syncs Interviewer Unlocks & Timer Automatically)
  // ==========================================================================

  async function pollState() {
    try {
      const data = await apiGet("/api/state");
      $("envBadge").textContent = data.python_version || "Python 3";
      state.timer = data.timer;
      renderTimer();

      state.files = data.files;
      data.files.forEach((f) => {
        state.fileMeta[f.name] = f;
      });

      // Check if interviewer unlocked a new follow-up part!
      const prevMax = Math.max(...state.unlockedParts);
      const newMax = Math.max(...data.unlocked_parts);
      state.unlockedParts = data.unlocked_parts;

      if (data.problem_hash !== state.lastProblemHash) {
        const isInitial = state.lastProblemHash === null;
        state.lastProblemHash = data.problem_hash;
        renderProblem(data.problem_md);

        if (!isInitial && newMax > prevMax) {
          showToast(`Follow-Up Unlocked: Part ${newMax} is now available!`);
          state.activePart = newMax;
          // Scroll problem pane smoothly to the newly unlocked part
          const body = $("leftTabProblem");
          setTimeout(() => {
            body.scrollTo({ top: body.scrollHeight, behavior: "smooth" });
          }, 120);
        }
      }

      // If solution.py changed externally (e.g. unlock_part.py appended Part 2 stub)
      // and the user is NOT currently holding unsaved edits, sync it cleanly!
      if (
        state.lastSolutionHash !== null &&
        data.solution_hash !== state.lastSolutionHash &&
        !state.dirtyFiles.has("solution.py")
      ) {
        state.lastSolutionHash = data.solution_hash;
        const fresh = await apiGet("/api/file?name=solution.py");
        state.fileCache["solution.py"] = fresh.content;
        if (state.activeFile === "solution.py") {
          const cursor = editor.getCursor();
          state.ignoreChangeEvent = true;
          editor.setValue(fresh.content);
          editor.setCursor(cursor);
          state.ignoreChangeEvent = false;
        }
      }

      renderPartPills(state.unlockedParts, data.part_scores);
      renderSubmissions(data.submissions);
      renderFileTree();
    } catch (_err) {
      // Silently retry on next poll tick
    }
  }

  // ==========================================================================
  // RESIZABLE SPLITTERS
  // ==========================================================================

  function setupResizers() {
    // Horizontal resizer (Problem vs IDE)
    const resizerV = $("resizerMain");
    const paneProblem = $("paneProblem");
    let draggingV = false;

    resizerV.addEventListener("mousedown", () => {
      draggingV = true;
      resizerV.classList.add("dragging");
      document.body.style.cursor = "col-resize";
    });

    // Vertical resizer (Editor vs Console)
    const resizerH = $("resizerConsole");
    const consoleDrawer = $("consoleDrawer");
    const paneIde = $("paneIde");
    let draggingH = false;

    resizerH.addEventListener("mousedown", () => {
      draggingH = true;
      resizerH.classList.add("dragging");
      document.body.style.cursor = "row-resize";
    });

    window.addEventListener("mousemove", (e) => {
      if (draggingV) {
        const pct = (e.clientX / window.innerWidth) * 100;
        const clamped = Math.min(62, Math.max(22, pct));
        paneProblem.style.width = clamped + "%";
        editor.refresh();
      } else if (draggingH) {
        const rect = paneIde.getBoundingClientRect();
        const bottomPx = rect.bottom - e.clientY;
        const pct = (bottomPx / rect.height) * 100;
        const clamped = Math.min(68, Math.max(18, pct));
        consoleDrawer.style.height = clamped + "%";
        editor.refresh();
      }
    });

    window.addEventListener("mouseup", () => {
      if (draggingV || draggingH) {
        draggingV = false;
        draggingH = false;
        resizerV.classList.remove("dragging");
        resizerH.classList.remove("dragging");
        document.body.style.cursor = "";
        editor.refresh();
      }
    });
  }

  // ==========================================================================
  // EVENT WIRING & BOOTSTRAP
  // ==========================================================================

  function wireEvents() {
    // Part switcher pills
    [1, 2, 3].forEach((p) => {
      $(`pillPart${p}`).addEventListener("click", () => {
        if (!state.unlockedParts.includes(p)) return;
        state.activePart = p;
        renderPartPills(state.unlockedParts, null);
        // Sync custom input selector to a function from this part
        if (p === 1) $("customFnSelect").value = "count_dropped_bytes";
        if (p === 2) $("customFnSelect").value = "count_valid_dropped_bytes";
        if (p === 3) $("customFnSelect").value = "top_dropped_sources";
        $("customArgsInput").value = CUSTOM_TEMPLATES[$("customFnSelect").value];
        pollState();
      });
    });

    // Left tabs (Problem vs Submissions)
    document.querySelectorAll(".pane-tab").forEach((btn) => {
      btn.addEventListener("click", () => {
        const target = btn.dataset.leftTab;
        document.querySelectorAll(".pane-tab").forEach((b) =>
          b.classList.toggle("active", b === btn)
        );
        $("leftTabProblem").classList.toggle("hidden", target !== "problem");
        $("leftTabSubmissions").classList.toggle("hidden", target !== "submissions");
      });
    });

    // Bottom console tabs
    document.querySelectorAll(".console-tab").forEach((btn) => {
      btn.addEventListener("click", () => switchConsoleTab(btn.dataset.consoleTab));
    });

    // Run & Submit buttons
    $("runSampleBtn").addEventListener("click", () => runTests("sample"));
    $("submitCodeBtn").addEventListener("click", () => runTests("submit"));

    // Custom Input controls
    $("customFnSelect").addEventListener("change", () => {
      $("customArgsInput").value = CUSTOM_TEMPLATES[$("customFnSelect").value] || "[]";
    });
    $("customArgsInput").value = CUSTOM_TEMPLATES.count_dropped_bytes;
    $("runCustomBtn").addEventListener("click", runCustomInput);

    // Sidebar collapse / expand
    $("toggleSidebarBtn").addEventListener("click", () => {
      $("projectSidebar").classList.add("hidden");
      $("expandSidebarBtn").classList.remove("hidden");
      editor.refresh();
    });
    $("expandSidebarBtn").addEventListener("click", () => {
      $("projectSidebar").classList.remove("hidden");
      $("expandSidebarBtn").classList.add("hidden");
      editor.refresh();
    });

    // Font size controls
    $("fontIncBtn").addEventListener("click", () => {
      state.fontSize = Math.min(20, state.fontSize + 1);
      editor.getWrapperElement().style.fontSize = state.fontSize + "px";
      editor.refresh();
    });
    $("fontDecBtn").addEventListener("click", () => {
      state.fontSize = Math.max(11, state.fontSize - 1);
      editor.getWrapperElement().style.fontSize = state.fontSize + "px";
      editor.refresh();
    });

    // Theme toggle
    $("themeToggleBtn").addEventListener("click", () => {
      const html = document.documentElement;
      const next = html.getAttribute("data-theme") === "dark" ? "light" : "dark";
      html.setAttribute("data-theme", next);
      $("themeIcon").innerHTML = next === "dark" ? "&#9788;" : "&#9790;";
    });

    // In-page Reset Modal
    $("resetCodeBtn").addEventListener("click", () => {
      $("resetModal").classList.remove("hidden");
    });
    $("cancelResetBtn").addEventListener("click", () => {
      $("resetModal").classList.add("hidden");
    });
    $("confirmResetBtn").addEventListener("click", async () => {
      $("resetModal").classList.add("hidden");
      try {
        const res = await apiPost("/api/reset-solution", {});
        state.fileCache["solution.py"] = res.content;
        state.lastSolutionHash = res.hash;
        state.dirtyFiles.delete("solution.py");
        if (state.activeFile === "solution.py") {
          state.ignoreChangeEvent = true;
          editor.setValue(res.content);
          state.ignoreChangeEvent = false;
        }
        setSaveStatus("saved");
        showToast("Reset solution.py to starter stub");
      } catch (err) {
        showToast(`Reset failed: ${err.message}`, true);
      }
    });
  }

  async function boot() {
    initEditor();
    setupResizers();
    wireEvents();

    await pollState();
    await openFile("solution.py", true);

    // Local 1-second timer tick for smooth countdown
    setInterval(() => {
      if (state.timer.running && state.timer.remaining_sec > 0) {
        state.timer.remaining_sec -= 1;
        renderTimer();
      }
    }, 1000);

    // Sync state with server every 2 seconds
    setInterval(pollState, 2000);
  }

  document.addEventListener("DOMContentLoaded", boot);
})();
