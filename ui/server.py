#!/usr/bin/env python3
"""
HackerRank Project-Style Assessment Server (Dual-Port Isolated Architecture)

  Candidate Assessment IDE:   http://127.0.0.1:8765  (Open in Interviewee VS Code Simple Browser)
  Interviewer Control Deck:   http://127.0.0.1:8766  (Open in your Private Interviewer Window)

Security & Isolation:
  - Port 8765 ONLY exposes whitelisted files inside `candidate/`.
  - Hidden test inputs and expected outputs are evaluated inside an isolated backend
    subprocess and NEVER sent to the candidate browser.
  - Zero external Python dependencies (uses Python 3 standard library only).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import re
import subprocess
import sys
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

sys.dont_write_bytecode = True

UI_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(UI_DIR)
CANDIDATE_DIR = os.path.join(ROOT_DIR, "candidate")
INTERVIEWER_DIR = os.path.join(ROOT_DIR, "interviewer")
STATIC_DIR = os.path.join(UI_DIR, "static")

# Whitelisted files in candidate/
CANDIDATE_FILES = {
    "solution.py": {"editable": True, "language": "python", "description": "Primary implementation file"},
    "sample_tests.py": {"editable": True, "language": "python", "description": "Public sample test cases (editable)"},
    "PROBLEM.md": {"editable": False, "language": "markdown", "description": "Problem specification"},
    "run_tests.py": {"editable": False, "language": "python", "description": "CLI test runner (read-only)"},
}

PART1_STARTER_STUB = '''"""
Microsoft Network Engineering Intern — Coding Assessment
Candidate Workspace (`solution.py`)

Run public sample tests:
    python3 run_tests.py --part 1

Run full submission (includes hidden tests):
    python3 run_tests.py --part 1 --submit
"""

from __future__ import annotations


# ============================================================================
# PART 1: Basic Drop Filtering & Byte Aggregation
# ============================================================================

def count_dropped_bytes(logs: list[str]) -> dict[str, int]:
    """
    Parse well-formed Azure NSG flow logs and return a dictionary mapping
    each source IP with at least one DROP event to its total dropped bytes.

    Args:
        logs: List of valid, well-formed log strings.

    Returns:
        Dict mapping src_ip -> total_dropped_bytes (for ACTION=DROP lines only).
    """
    # TODO: Write your Part 1 implementation here
    pass
'''


class AssessmentState:
    """Thread-safe shared state between Candidate IDE (:8765) and Interviewer Deck (:8766)."""

    def __init__(self, duration_sec: int = 3600) -> None:
        self.lock = threading.Lock()
        self.duration_sec = duration_sec
        self.remaining_sec = duration_sec
        self.timer_running = False
        self.timer_last_tick: float | None = None
        self.submissions: list[dict] = []
        self.part_scores: dict[int, dict] = {}
        self.next_sub_id = 1
        self.last_candidate_activity: float | None = None

    def get_timer_snapshot(self) -> dict:
        with self.lock:
            rem = self.remaining_sec
            if self.timer_running and self.timer_last_tick is not None:
                elapsed = time.time() - self.timer_last_tick
                rem = max(0, int(self.remaining_sec - elapsed))
                if rem == 0:
                    self.remaining_sec = 0
                    self.timer_running = False
                    self.timer_last_tick = None
            return {
                "duration_sec": self.duration_sec,
                "remaining_sec": rem,
                "running": self.timer_running,
            }

    def control_timer(self, action: str, duration_sec: int | None = None) -> dict:
        with self.lock:
            now = time.time()
            if self.timer_running and self.timer_last_tick is not None:
                self.remaining_sec = max(0, int(self.remaining_sec - (now - self.timer_last_tick)))
                self.timer_last_tick = now

            if action == "start":
                if self.remaining_sec <= 0:
                    self.remaining_sec = self.duration_sec
                self.timer_running = True
                self.timer_last_tick = now
            elif action == "pause":
                self.timer_running = False
                self.timer_last_tick = None
            elif action == "reset":
                if duration_sec is not None and duration_sec > 0:
                    self.duration_sec = duration_sec
                self.remaining_sec = self.duration_sec
                self.timer_running = False
                self.timer_last_tick = None
            elif action == "set" and duration_sec is not None and duration_sec > 0:
                self.duration_sec = duration_sec
                self.remaining_sec = duration_sec
                self.timer_last_tick = now if self.timer_running else None

        return self.get_timer_snapshot()

    def record_submission(self, part: int, mode: str, report: dict) -> dict:
        with self.lock:
            entry = {
                "id": self.next_sub_id,
                "timestamp": time.strftime("%H:%M:%S"),
                "part": part,
                "mode": mode,
                "passed": report["passed"],
                "total": report["total"],
                "total_ms": report["total_ms"],
                "compile_error": report.get("compile_error"),
                "failed_categories": [
                    f"{c['name']} ({c['status']})"
                    for c in report.get("cases", [])
                    if not c["passed"]
                ],
            }
            self.next_sub_id += 1
            self.submissions.insert(0, entry)
            self.submissions = self.submissions[:50]
            self.last_candidate_activity = time.time()

            prev = self.part_scores.get(part)
            # Always update on submit, or if no submit exists yet
            if prev is None or mode == "submit" or prev.get("mode") != "submit":
                self.part_scores[part] = {
                    "passed": report["passed"],
                    "total": report["total"],
                    "mode": mode,
                    "all_passed": report["passed"] == report["total"] and report["total"] > 0,
                }
            return entry


STATE = AssessmentState(duration_sec=3600)


def read_text_file(path: str) -> str:
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def get_unlocked_parts(problem_md: str) -> list[int]:
    parts = [1]
    if "## Part 2 (Follow-Up 1):" in problem_md:
        parts.append(2)
    if "## Part 3 (Follow-Up 2):" in problem_md:
        parts.append(3)
    return parts


def get_problem_meta() -> dict:
    problem_md = read_text_file(os.path.join(CANDIDATE_DIR, "PROBLEM.md"))
    solution_py = read_text_file(os.path.join(CANDIDATE_DIR, "solution.py"))
    unlocked = get_unlocked_parts(problem_md)
    problem_hash = hashlib.md5(problem_md.encode("utf-8")).hexdigest()[:12]
    solution_hash = hashlib.md5(solution_py.encode("utf-8")).hexdigest()[:12]
    return {
        "problem_md": problem_md,
        "unlocked_parts": unlocked,
        "problem_hash": problem_hash,
        "solution_hash": solution_hash,
    }


def scrub_interviewer_paths(text: str) -> str:
    """Ensure tracebacks never expose interviewer/ directory paths to the candidate."""
    if not text:
        return ""
    cleaned = text.replace(INTERVIEWER_DIR, "<judge>")
    cleaned = cleaned.replace(ROOT_DIR, "<workspace>")
    return cleaned


# ============================================================================
# ISOLATED TEST EXECUTION ENGINE (Runs in fresh Python subprocess)
# ============================================================================

RUNNER_SCRIPT = r'''
import contextlib
import copy
import io
import json
import multiprocessing
import os
import sys
import time
import traceback

sys.dont_write_bytecode = True

payload = json.loads(sys.stdin.read())
candidate_dir = payload["candidate_dir"]
interviewer_dir = payload["interviewer_dir"]
part = int(payload["part"])
mode = payload["mode"]

sys.path.insert(0, candidate_dir)

def format_val(v, limit=800):
    try:
        s = json.dumps(v, indent=2)
    except Exception:
        s = repr(v)
    if len(s) > limit:
        return s[:limit] + "\n... (truncated)"
    return s

# 1. Import candidate solution first so syntax errors are caught cleanly
try:
    import solution
except Exception:
    print(json.dumps({
        "compile_error": traceback.format_exc(),
        "passed": 0,
        "total": 0,
        "total_ms": 0.0,
        "cases": [],
    }))
    sys.exit(0)

# 2. Import sample_tests
try:
    import sample_tests
except Exception:
    print(json.dumps({
        "compile_error": "Error in sample_tests.py:\n" + traceback.format_exc(),
        "passed": 0,
        "total": 0,
        "total_ms": 0.0,
        "cases": [],
    }))
    sys.exit(0)

part_config = {
    1: ("count_dropped_bytes", sample_tests.PART1_SAMPLE_TESTS),
    2: ("count_valid_dropped_bytes", sample_tests.PART2_SAMPLE_TESTS),
    3: ("top_dropped_sources", sample_tests.PART3_SAMPLE_TESTS),
}
default_fn, public_cases = part_config[part]

all_cases = []
for i, tc in enumerate(public_cases):
    all_cases.append((i, False, tc))

if mode == "submit":
    sys.path.append(interviewer_dir)
    import hidden_tests
    hidden_cases = hidden_tests.get_hidden_tests(part)
    offset = len(public_cases)
    for j, tc in enumerate(hidden_cases):
        all_cases.append((offset + j, True, tc))

def _worker(fn_name, args, q):
    buf = io.StringIO()
    try:
        if not hasattr(solution, fn_name):
            q.put({
                "status": "MISSING_FN",
                "error": f"Function `{fn_name}` is not defined in solution.py",
                "stdout": "",
                "elapsed_ms": 0.0,
            })
            return
        fn = getattr(solution, fn_name)
        t0 = time.perf_counter()
        with contextlib.redirect_stdout(buf):
            res = fn(*args)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        q.put({
            "status": "OK",
            "result": res,
            "stdout": buf.getvalue(),
            "elapsed_ms": elapsed_ms,
        })
    except Exception:
        q.put({
            "status": "RUNTIME_ERROR",
            "error": traceback.format_exc(),
            "stdout": buf.getvalue(),
            "elapsed_ms": 0.0,
        })

results = []
passed_count = 0
total_ms = 0.0

for idx, is_hidden, tc in all_cases:
    fn_name = tc.get("fn", default_fn)
    timeout_sec = float(tc.get("timeout_sec", 2.0))
    args_copy = copy.deepcopy(tc["args"])

    q = multiprocessing.Queue()
    p = multiprocessing.Process(target=_worker, args=(fn_name, args_copy, q))
    p.start()
    p.join(timeout=timeout_sec)

    if p.is_alive():
        p.terminate()
        p.join()
        elapsed = round(timeout_sec * 1000.0, 2)
        total_ms += elapsed
        case_out = {
            "index": idx,
            "name": tc["category"] if is_hidden else tc["name"],
            "fn": fn_name,
            "is_hidden": is_hidden,
            "passed": False,
            "status": "TLE",
            "elapsed_ms": elapsed,
            "error": f"Time Limit Exceeded (> {timeout_sec:.1f}s). Check your algorithm's time complexity.",
            "stdout": "",
        }
        if is_hidden:
            case_out["hint"] = tc.get("hint", "Check boundary conditions and time complexity.")
        else:
            case_out["input_preview"] = format_val(tc["args"])
            case_out["expected_preview"] = format_val(tc["expected"])
            case_out["actual_preview"] = "(Timed out)"
        results.append(case_out)
        continue

    if q.empty():
        results.append({
            "index": idx,
            "name": tc["category"] if is_hidden else tc["name"],
            "fn": fn_name,
            "is_hidden": is_hidden,
            "passed": False,
            "status": "CRASH",
            "elapsed_ms": 0.0,
            "error": "Process exited unexpectedly.",
            "stdout": "",
        })
        continue

    out = q.get()
    elapsed = round(out["elapsed_ms"], 2)
    total_ms += elapsed

    if out["status"] != "OK":
        case_out = {
            "index": idx,
            "name": tc["category"] if is_hidden else tc["name"],
            "fn": fn_name,
            "is_hidden": is_hidden,
            "passed": False,
            "status": out["status"],
            "elapsed_ms": elapsed,
            "error": out["error"],
            "stdout": out["stdout"][:2000],
        }
        if is_hidden:
            case_out["hint"] = tc.get("hint", "")
        else:
            case_out["input_preview"] = format_val(tc["args"])
            case_out["expected_preview"] = format_val(tc["expected"])
            case_out["actual_preview"] = "(Exception)"
        results.append(case_out)
        continue

    actual = out["result"]
    expected = tc["expected"]
    ok = (actual == expected)
    if ok:
        passed_count += 1

    case_out = {
        "index": idx,
        "name": tc["category"] if is_hidden else tc["name"],
        "fn": fn_name,
        "is_hidden": is_hidden,
        "passed": ok,
        "status": "PASSED" if ok else "WRONG_ANSWER",
        "elapsed_ms": elapsed,
        "stdout": "" if is_hidden else out["stdout"][:2000],
    }
    if is_hidden:
        case_out["hint"] = tc.get("hint", "Check edge cases and specification rules.")
    else:
        case_out["input_preview"] = format_val(tc["args"])
        case_out["expected_preview"] = format_val(expected)
        case_out["actual_preview"] = format_val(actual)
    results.append(case_out)

print(json.dumps({
    "compile_error": None,
    "passed": passed_count,
    "total": len(results),
    "total_ms": round(total_ms, 2),
    "cases": results,
}))
'''

CUSTOM_RUNNER_SCRIPT = r'''
import contextlib
import io
import json
import sys
import time
import traceback

sys.dont_write_bytecode = True

payload = json.loads(sys.stdin.read())
sys.path.insert(0, payload["candidate_dir"])

try:
    import solution
except Exception:
    print(json.dumps({
        "status": "COMPILE_ERROR",
        "error": traceback.format_exc(),
        "stdout": "",
        "elapsed_ms": 0.0,
    }))
    sys.exit(0)

fn_name = payload["fn"]
if not hasattr(solution, fn_name):
    print(json.dumps({
        "status": "MISSING_FN",
        "error": f"Function `{fn_name}` is not defined in solution.py yet.",
        "stdout": "",
        "elapsed_ms": 0.0,
    }))
    sys.exit(0)

fn = getattr(solution, fn_name)
args = payload["args"]
buf = io.StringIO()
try:
    t0 = time.perf_counter()
    with contextlib.redirect_stdout(buf):
        result = fn(*args)
    elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    print(json.dumps({
        "status": "OK",
        "result_repr": repr(result),
        "stdout": buf.getvalue()[:4000],
        "elapsed_ms": elapsed_ms,
    }))
except Exception:
    print(json.dumps({
        "status": "RUNTIME_ERROR",
        "error": traceback.format_exc(),
        "stdout": buf.getvalue()[:4000],
        "elapsed_ms": 0.0,
    }))
'''


def execute_tests(part: int, mode: str) -> dict:
    payload = json.dumps({
        "candidate_dir": CANDIDATE_DIR,
        "interviewer_dir": INTERVIEWER_DIR,
        "part": part,
        "mode": mode,
    })
    try:
        proc = subprocess.run(
            [sys.executable, "-B", "-c", RUNNER_SCRIPT],
            input=payload,
            text=True,
            capture_output=True,
            timeout=20,
        )
    except subprocess.TimeoutExpired:
        return {
            "compile_error": "Global runner timeout exceeded (20s).",
            "passed": 0,
            "total": 0,
            "total_ms": 20000.0,
            "cases": [],
        }

    if proc.returncode != 0 or not proc.stdout.strip():
        return {
            "compile_error": scrub_interviewer_paths(proc.stderr or "Unexpected execution failure."),
            "passed": 0,
            "total": 0,
            "total_ms": 0.0,
            "cases": [],
        }

    report = json.loads(proc.stdout)
    if report.get("compile_error"):
        report["compile_error"] = scrub_interviewer_paths(report["compile_error"])
    for c in report.get("cases", []):
        if c.get("error"):
            c["error"] = scrub_interviewer_paths(c["error"])
    return report


def execute_custom_input(fn_name: str, args: list) -> dict:
    allowed_fns = {
        "count_dropped_bytes",
        "count_valid_dropped_bytes",
        "top_dropped_sources",
    }
    if fn_name not in allowed_fns:
        return {"status": "ERROR", "error": f"Unknown function: {fn_name}", "stdout": "", "elapsed_ms": 0.0}

    payload = json.dumps({
        "candidate_dir": CANDIDATE_DIR,
        "fn": fn_name,
        "args": args,
    })
    try:
        proc = subprocess.run(
            [sys.executable, "-B", "-c", CUSTOM_RUNNER_SCRIPT],
            input=payload,
            text=True,
            capture_output=True,
            timeout=5,
        )
    except subprocess.TimeoutExpired:
        return {
            "status": "TLE",
            "error": "Time Limit Exceeded (> 5.0s) on custom input.",
            "stdout": "",
            "elapsed_ms": 5000.0,
        }

    if proc.returncode != 0 or not proc.stdout.strip():
        return {
            "status": "RUNTIME_ERROR",
            "error": scrub_interviewer_paths(proc.stderr or "Execution failed."),
            "stdout": "",
            "elapsed_ms": 0.0,
        }
    res = json.loads(proc.stdout)
    if res.get("error"):
        res["error"] = scrub_interviewer_paths(res["error"])
    return res


def reset_candidate_solution() -> str:
    """Reset candidate/solution.py to clean stubs for all currently unlocked parts."""
    meta = get_problem_meta()
    unlocked = meta["unlocked_parts"]
    sol_path = os.path.join(CANDIDATE_DIR, "solution.py")
    with open(sol_path, "w", encoding="utf-8") as f:
        f.write(PART1_STARTER_STUB)

    # Re-append Part 2 / Part 3 stubs if those parts are unlocked
    if 2 in unlocked or 3 in unlocked:
        if INTERVIEWER_DIR not in sys.path:
            sys.path.append(INTERVIEWER_DIR)
        import unlock_part  # type: ignore

        target = "3" if 3 in unlocked else "2"
        unlock_part.unlock(target)

    return read_text_file(sol_path)


def run_unlock_action(action: str) -> dict:
    if INTERVIEWER_DIR not in sys.path:
        sys.path.append(INTERVIEWER_DIR)
    import unlock_part  # type: ignore

    unlock_part.unlock(action)
    return get_problem_meta()


# ============================================================================
# BASE HTTP HANDLER UTILITIES
# ============================================================================

class JsonHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:  # noqa: A002
        # Suppress noisy per-poll access logs
        return

    def send_json(self, data: dict, status: int = 200) -> None:
        raw = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def send_file(self, abs_path: str) -> None:
        if not os.path.isfile(abs_path):
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return
        ctype, _ = mimetypes.guess_type(abs_path)
        if abs_path.endswith(".js"):
            ctype = "application/javascript; charset=utf-8"
        elif abs_path.endswith(".css"):
            ctype = "text/css; charset=utf-8"
        elif abs_path.endswith(".html"):
            ctype = "text/html; charset=utf-8"
        with open(abs_path, "rb") as f:
            raw = f.read()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", ctype or "application/octet-stream")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(raw)

    def read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))


# ============================================================================
# PORT 8765: CANDIDATE ASSESSMENT IDE HANDLER (Strictly Isolated)
# ============================================================================

class CandidateHandler(JsonHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            self.send_file(os.path.join(STATIC_DIR, "candidate.html"))
            return

        if path.startswith("/static/"):
            rel = os.path.normpath(path[len("/static/"):]).lstrip("/")
            # Never serve interviewer assets on the candidate port!
            if rel.startswith("..") or "interviewer" in rel.lower():
                self.send_error(HTTPStatus.FORBIDDEN, "Forbidden")
                return
            full = os.path.join(STATIC_DIR, rel)
            if not os.path.abspath(full).startswith(os.path.abspath(STATIC_DIR)):
                self.send_error(HTTPStatus.FORBIDDEN, "Forbidden")
                return
            self.send_file(full)
            return

        if path == "/api/state":
            meta = get_problem_meta()
            files_list = []
            for fname, info in CANDIDATE_FILES.items():
                fpath = os.path.join(CANDIDATE_DIR, fname)
                size = os.path.getsize(fpath) if os.path.exists(fpath) else 0
                files_list.append({
                    "name": fname,
                    "editable": info["editable"],
                    "language": info["language"],
                    "description": info["description"],
                    "size": size,
                })
            with STATE.lock:
                scores = dict(STATE.part_scores)
                subs = list(STATE.submissions)
            self.send_json({
                "problem_md": meta["problem_md"],
                "unlocked_parts": meta["unlocked_parts"],
                "problem_hash": meta["problem_hash"],
                "solution_hash": meta["solution_hash"],
                "files": files_list,
                "timer": STATE.get_timer_snapshot(),
                "part_scores": scores,
                "submissions": subs,
                "python_version": f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            })
            return

        if path == "/api/file":
            qs = parse_qs(parsed.query)
            fname = qs.get("name", [""])[0]
            if fname not in CANDIDATE_FILES:
                self.send_json({"error": "File not accessible"}, status=403)
                return
            content = read_text_file(os.path.join(CANDIDATE_DIR, fname))
            self.send_json({
                "name": fname,
                "content": content,
                "editable": CANDIDATE_FILES[fname]["editable"],
                "language": CANDIDATE_FILES[fname]["language"],
                "hash": hashlib.md5(content.encode("utf-8")).hexdigest()[:12],
            })
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        try:
            body = self.read_json_body()
        except Exception:
            self.send_json({"error": "Invalid JSON body"}, status=400)
            return

        if path == "/api/file":
            fname = body.get("name", "")
            content = body.get("content", "")
            if fname not in CANDIDATE_FILES or not CANDIDATE_FILES[fname]["editable"]:
                self.send_json({"error": "File is read-only or not allowed"}, status=403)
                return
            fpath = os.path.join(CANDIDATE_DIR, fname)
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(content)
            with STATE.lock:
                STATE.last_candidate_activity = time.time()
            self.send_json({
                "ok": True,
                "name": fname,
                "hash": hashlib.md5(content.encode("utf-8")).hexdigest()[:12],
            })
            return

        if path == "/api/reset-solution":
            new_content = reset_candidate_solution()
            self.send_json({
                "ok": True,
                "content": new_content,
                "hash": hashlib.md5(new_content.encode("utf-8")).hexdigest()[:12],
            })
            return

        if path == "/api/run":
            part = int(body.get("part", 1))
            mode = body.get("mode", "sample")
            if part not in (1, 2, 3) or mode not in ("sample", "submit"):
                self.send_json({"error": "Invalid part or mode"}, status=400)
                return

            meta = get_problem_meta()
            if part not in meta["unlocked_parts"]:
                self.send_json({"error": f"Part {part} is currently locked by the interviewer."}, status=403)
                return

            # Optionally save solution.py before executing
            if isinstance(body.get("code"), str):
                with open(os.path.join(CANDIDATE_DIR, "solution.py"), "w", encoding="utf-8") as f:
                    f.write(body["code"])

            report = execute_tests(part, mode)
            sub_entry = STATE.record_submission(part, mode, report)
            with STATE.lock:
                scores = dict(STATE.part_scores)
            self.send_json({
                "part": part,
                "mode": mode,
                "report": report,
                "submission": sub_entry,
                "part_scores": scores,
            })
            return

        if path == "/api/custom-run":
            fn_name = body.get("fn", "count_dropped_bytes")
            args = body.get("args", [])
            if isinstance(body.get("code"), str):
                with open(os.path.join(CANDIDATE_DIR, "solution.py"), "w", encoding="utf-8") as f:
                    f.write(body["code"])
            res = execute_custom_input(fn_name, args)
            self.send_json(res)
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")


# ============================================================================
# PORT 8766: PRIVATE INTERVIEWER CONTROL DECK HANDLER
# ============================================================================

class InterviewerHandler(JsonHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            self.send_file(os.path.join(STATIC_DIR, "interviewer.html"))
            return

        if path.startswith("/static/"):
            rel = os.path.normpath(path[len("/static/"):]).lstrip("/")
            if rel.startswith(".."):
                self.send_error(HTTPStatus.FORBIDDEN, "Forbidden")
                return
            full = os.path.join(STATIC_DIR, rel)
            if not os.path.abspath(full).startswith(os.path.abspath(STATIC_DIR)):
                self.send_error(HTTPStatus.FORBIDDEN, "Forbidden")
                return
            self.send_file(full)
            return

        if path == "/api/interviewer/state":
            meta = get_problem_meta()
            with STATE.lock:
                scores = dict(STATE.part_scores)
                subs = list(STATE.submissions)
                last_act = STATE.last_candidate_activity
            self.send_json({
                "unlocked_parts": meta["unlocked_parts"],
                "timer": STATE.get_timer_snapshot(),
                "part_scores": scores,
                "submissions": subs,
                "last_activity_ago_sec": round(time.time() - last_act, 1) if last_act else None,
                "candidate_solution": read_text_file(os.path.join(CANDIDATE_DIR, "solution.py")),
                "guide_md": read_text_file(os.path.join(INTERVIEWER_DIR, "INTERVIEWER_GUIDE.md")),
                "reference_solutions": read_text_file(os.path.join(INTERVIEWER_DIR, "reference_solutions.py")),
            })
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        try:
            body = self.read_json_body()
        except Exception:
            self.send_json({"error": "Invalid JSON"}, status=400)
            return

        if path == "/api/interviewer/unlock":
            action = body.get("action", "")
            if action not in ("2", "3", "all", "reset"):
                self.send_json({"error": "Invalid action"}, status=400)
                return
            meta = run_unlock_action(action)
            self.send_json({"ok": True, "unlocked_parts": meta["unlocked_parts"]})
            return

        if path == "/api/interviewer/timer":
            action = body.get("action", "")
            duration_sec = body.get("duration_sec")
            if action not in ("start", "pause", "reset", "set"):
                self.send_json({"error": "Invalid timer action"}, status=400)
                return
            snap = STATE.control_timer(action, int(duration_sec) if duration_sec else None)
            self.send_json({"ok": True, "timer": snap})
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")


def main() -> None:
    parser = argparse.ArgumentParser(description="HackerRank Project-Style Assessment Server")
    parser.add_argument("--candidate-port", type=int, default=8765, help="Port for Candidate IDE (default: 8765)")
    parser.add_argument("--interviewer-port", type=int, default=8766, help="Port for Interviewer Control Deck (default: 8766)")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind (default: 127.0.0.1)")
    parser.add_argument("--duration", type=int, default=60, help="Assessment timer duration in minutes (default: 60)")
    args = parser.parse_args()

    STATE.control_timer("reset", args.duration * 60)

    cand_server = ThreadingHTTPServer((args.host, args.candidate_port), CandidateHandler)
    int_server = ThreadingHTTPServer((args.host, args.interviewer_port), InterviewerHandler)

    t1 = threading.Thread(target=cand_server.serve_forever, daemon=True)
    t2 = threading.Thread(target=int_server.serve_forever, daemon=True)
    t1.start()
    t2.start()

    print("\n" + "=" * 72)
    print("  HACKERRANK PROJECT-STYLE ASSESSMENT SERVER RUNNING")
    print("=" * 72)
    print(f"  [INTERVIEWEE WINDOW]  http://{args.host}:{args.candidate_port}")
    print(f"     -> In VS Code Interviewee Window: Ctrl+Shift+P -> 'Simple Browser: Show'")
    print(f"        and enter: http://{args.host}:{args.candidate_port}")
    print("-" * 72)
    print(f"  [INTERVIEWER WINDOW]  http://{args.host}:{args.interviewer_port}")
    print(f"     -> Private Control Deck (Unlock Parts, Timer, Live Feed, Guide, Solutions)")
    print("=" * 72)
    print("  Press Ctrl+C to stop both servers.\n", flush=True)

    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        cand_server.shutdown()
        int_server.shutdown()


if __name__ == "__main__":
    main()
