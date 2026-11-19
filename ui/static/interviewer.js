(function () {
  "use strict";

  const $ = (id) => document.getElementById(id);
  let loadedDocs = false;

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function showToast(msg) {
    const el = document.createElement("div");
    el.className = "toast";
    el.textContent = msg;
    $("toastContainer").appendChild(el);
    setTimeout(() => el.remove(), 3000);
  }

  function formatTimer(sec) {
    const s = Math.max(0, Math.floor(sec));
    const m = Math.floor(s / 60);
    const r = s % 60;
    return `${String(m).padStart(2, "0")}:${String(r).padStart(2, "0")}`;
  }

  async function postJson(url, body) {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return res.json();
  }

  async function refresh() {
    try {
      const res = await fetch("/api/interviewer/state", { cache: "no-store" });
      const data = await res.json();

      $("intTimerText").textContent = formatTimer(data.timer.remaining_sec);

      // Part status pills
      $("partStatusRow").innerHTML = [1, 2, 3]
        .map((p) => {
          const on = data.unlocked_parts.includes(p);
          const sc = data.part_scores[p] || data.part_scores[String(p)];
          const scTxt = sc ? ` (${sc.passed}/${sc.total})` : "";
          return `<div class="status-pill ${on ? "unlocked" : ""}">Part ${p}${scTxt}</div>`;
        })
        .join("");

      if (data.last_activity_ago_sec !== null) {
        $("lastActivityLabel").textContent = `Active ${data.last_activity_ago_sec}s ago`;
      }

      // Live feed
      const feed = $("activityFeed");
      if (!data.submissions.length) {
        feed.innerHTML = `<div class="empty">No runs recorded yet.</div>`;
      } else {
        feed.innerHTML = data.submissions
          .map((s) => {
            const ok = !s.compile_error && s.passed === s.total && s.total > 0;
            const cls = ok ? "badge-pass" : "badge-fail";
            const label = s.compile_error ? "Syntax Error" : `${s.passed}/${s.total}`;
            const fails = (s.failed_categories || [])
              .map((f) => `<li>${escapeHtml(f)}</li>`)
              .join("");
            return `
              <div class="feed-item">
                <div class="feed-top">
                  <strong>Part ${s.part} (${s.mode})</strong>
                  <span class="${cls}">${label} &middot; ${s.total_ms}ms</span>
                </div>
                <div class="muted">${escapeHtml(s.timestamp)}</div>
                ${fails ? `<ul class="feed-fails">${fails}</ul>` : ""}
              </div>
            `;
          })
          .join("");
      }

      $("liveCodeContent").textContent = data.candidate_solution || "";

      if (!loadedDocs) {
        loadedDocs = true;
        $("guideContent").innerHTML = window.marked
          ? window.marked.parse(data.guide_md)
          : escapeHtml(data.guide_md);
        $("solutionsContent").textContent = data.reference_solutions || "";
      }
    } catch (_err) {
      // Retry next tick
    }
  }

  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const target = btn.dataset.tab;
      document.querySelectorAll(".tab-btn").forEach((b) =>
        b.classList.toggle("active", b === btn)
      );
      $("panelGuide").classList.toggle("hidden", target !== "guide");
      $("panelSolutions").classList.toggle("hidden", target !== "solutions");
      $("panelLivecode").classList.toggle("hidden", target !== "livecode");
    });
  });

  $("unlockPart2Btn").addEventListener("click", async () => {
    await postJson("/api/interviewer/unlock", { action: "2" });
    showToast("Unlocked Part 2 in candidate workspace!");
    refresh();
  });

  $("unlockPart3Btn").addEventListener("click", async () => {
    await postJson("/api/interviewer/unlock", { action: "3" });
    showToast("Unlocked Part 3 in candidate workspace!");
    refresh();
  });

  $("resetPartsBtn").addEventListener("click", async () => {
    await postJson("/api/interviewer/unlock", { action: "reset" });
    showToast("Reset candidate workspace to Part 1 only.");
    refresh();
  });

  $("timerStartBtn").addEventListener("click", async () => {
    await postJson("/api/interviewer/timer", { action: "start" });
    showToast("Timer started");
    refresh();
  });

  $("timerPauseBtn").addEventListener("click", async () => {
    await postJson("/api/interviewer/timer", { action: "pause" });
    showToast("Timer paused");
    refresh();
  });

  $("timerReset60Btn").addEventListener("click", async () => {
    await postJson("/api/interviewer/timer", { action: "reset", duration_sec: 3600 });
    showToast("Timer reset to 60:00");
    refresh();
  });

  $("timerReset45Btn").addEventListener("click", async () => {
    await postJson("/api/interviewer/timer", { action: "reset", duration_sec: 2700 });
    showToast("Timer reset to 45:00");
    refresh();
  });

  refresh();
  setInterval(refresh, 2000);
})();
