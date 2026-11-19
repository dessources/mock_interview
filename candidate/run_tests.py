#!/usr/bin/env python3
"""
HackerRank-Style Local Test Runner for Candidate Workspace.

Usage:
  python3 run_tests.py --part 1            # Run visible sample tests for Part 1
  python3 run_tests.py --part 1 --submit   # Run sample + hidden/stress tests for Part 1
  python3 run_tests.py --part 2 --submit   # Run sample + hidden/stress tests for Part 2
  python3 run_tests.py --part 3 --submit   # Run sample + hidden/stress tests for Part 3
"""

from __future__ import annotations
import argparse
import contextlib
import copy
import io
import multiprocessing
import os
import sys
sys.dont_write_bytecode = True
import time
import traceback

# Ensure current directory is on sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import solution
import sample_tests

# ANSI Color codes for HackerRank terminal feel
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def _worker_invoke(fn_name: str, args: tuple, queue: multiprocessing.Queue) -> None:
    """Execute candidate function in a child process to enforce strict timeouts and capture stdout."""
    buf = io.StringIO()
    try:
        if not hasattr(solution, fn_name):
            queue.put(
                {
                    "status": "MISSING_FN",
                    "error": f"Function `{fn_name}` is not defined in solution.py",
                    "stdout": "",
                    "elapsed_ms": 0.0,
                }
            )
            return
        fn = getattr(solution, fn_name)
        t0 = time.perf_counter()
        with contextlib.redirect_stdout(buf):
            result = fn(*args)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        queue.put(
            {
                "status": "OK",
                "result": result,
                "stdout": buf.getvalue(),
                "elapsed_ms": elapsed_ms,
            }
        )
    except Exception:
        queue.put(
            {
                "status": "EXCEPTION",
                "error": traceback.format_exc(),
                "stdout": buf.getvalue(),
                "elapsed_ms": 0.0,
            }
        )


def run_single_test(test_case: dict, default_fn: str, is_hidden: bool = False) -> dict:
    fn_name = test_case.get("fn", default_fn)
    timeout_sec = test_case.get("timeout_sec", 2.0)
    args_copy = copy.deepcopy(test_case["args"])

    queue: multiprocessing.Queue = multiprocessing.Queue()
    proc = multiprocessing.Process(
        target=_worker_invoke, args=(fn_name, args_copy, queue)
    )
    proc.start()
    proc.join(timeout=timeout_sec)

    if proc.is_alive():
        proc.terminate()
        proc.join()
        return {
            "passed": False,
            "status": "TLE",
            "elapsed_ms": timeout_sec * 1000.0,
            "stdout": "",
            "error": f"Time Limit Exceeded (> {timeout_sec:.1f}s). Check your algorithm's time complexity!",
        }

    if queue.empty():
        return {
            "passed": False,
            "status": "CRASH",
            "elapsed_ms": 0.0,
            "stdout": "",
            "error": "Process exited unexpectedly without returning a result.",
        }

    outcome = queue.get()
    if outcome["status"] != "OK":
        return {
            "passed": False,
            "status": outcome["status"],
            "elapsed_ms": outcome["elapsed_ms"],
            "stdout": outcome["stdout"],
            "error": outcome["error"],
        }

    actual = outcome["result"]
    expected = test_case["expected"]
    passed = actual == expected
    return {
        "passed": passed,
        "status": "PASSED" if passed else "WRONG_ANSWER",
        "actual": actual,
        "expected": expected,
        "elapsed_ms": outcome["elapsed_ms"],
        "stdout": outcome["stdout"],
    }


def format_preview(val: object, max_len: int = 180) -> str:
    s = repr(val)
    if len(s) > max_len:
        return s[: max_len - 3] + "..."
    return s


def load_hidden_tests(part: int) -> list[dict]:
    interviewer_dir = os.path.join(PARENT_DIR, "interviewer")
    hidden_file = os.path.join(interviewer_dir, "hidden_tests.py")
    if not os.path.exists(hidden_file):
        return []
    if interviewer_dir not in sys.path:
        sys.path.append(interviewer_dir)
    import hidden_tests  # type: ignore

    return hidden_tests.get_hidden_tests(part)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="HackerRank Local Test Runner for Azure VNet Flow Analyzer"
    )
    parser.add_argument(
        "--part",
        type=int,
        choices=[1, 2, 3],
        default=1,
        help="Which part of the challenge to test (1, 2, or 3)",
    )
    parser.add_argument(
        "--submit",
        action="store_true",
        help="Run both Sample Tests and Hidden/Stress Test Cases",
    )
    args = parser.parse_args()

    part_config = {
        1: (
            "Part 1: Top Offending Source IPs by Dropped Bytes",
            "top_dropped_sources",
            sample_tests.PART1_SAMPLE_TESTS,
        ),
        2: (
            "Part 2: CIDR Longest Prefix Match & Internal Filtering",
            "top_dropped_external_sources",
            sample_tests.PART2_SAMPLE_TESTS,
        ),
        3: (
            "Part 3: Sliding-Window Burst / DDoS Detection",
            "detect_burst_sources",
            sample_tests.PART3_SAMPLE_TESTS,
        ),
    }

    title, default_fn, public_cases = part_config[args.part]

    print(f"\n{BOLD}{CYAN}{'=' * 74}{RESET}")
    print(f"{BOLD}{CYAN}  HACKERRANK EXECUTION ENVIRONMENT — {title}{RESET}")
    mode_str = "FULL SUBMISSION (Sample + Hidden Tests)" if args.submit else "RUN CODE (Sample Tests Only)"
    print(f"{DIM}  Mode: {mode_str}{RESET}")
    print(f"{BOLD}{CYAN}{'=' * 74}{RESET}\n")

    total_passed = 0
    total_cases = 0

    # 1. Run Public Sample Tests
    print(f"{BOLD}▶ Public Sample Test Cases{RESET}")
    for idx, tc in enumerate(public_cases, start=1):
        total_cases += 1
        res = run_single_test(tc, default_fn, is_hidden=False)
        if res["passed"]:
            total_passed += 1
            print(
                f"  {GREEN}✔ Test Case {idx}: {tc['name']} — PASSED ({res['elapsed_ms']:.1f} ms){RESET}"
            )
            if res["stdout"].strip():
                print(f"    {DIM}Stdout: {res['stdout'].strip()}{RESET}")
        else:
            print(
                f"  {RED}✘ Test Case {idx}: {tc['name']} — {res['status']} ({res['elapsed_ms']:.1f} ms){RESET}"
            )
            print(f"    {BOLD}Input:{RESET}    {format_preview(tc['args'])}")
            if "expected" in res:
                print(f"    {BOLD}Expected:{RESET} {format_preview(res['expected'])}")
                print(f"    {BOLD}Actual:{RESET}   {format_preview(res['actual'])}")
            if "error" in res:
                for line in res["error"].strip().splitlines():
                    print(f"    {YELLOW}{line}{RESET}")
            if res["stdout"].strip():
                print(f"    {CYAN}Your Debug Output (stdout):{RESET}")
                for line in res["stdout"].strip().splitlines()[:10]:
                    print(f"      {line}")

    # 2. Run Hidden Test Cases if --submit is passed
    if args.submit:
        hidden_cases = load_hidden_tests(args.part)
        print(f"\n{BOLD}▶ Locked / Hidden Test Cases (Edge Cases & Scale Stress Tests){RESET}")
        for idx, tc in enumerate(hidden_cases, start=len(public_cases) + 1):
            total_cases += 1
            res = run_single_test(tc, default_fn, is_hidden=True)
            if res["passed"]:
                total_passed += 1
                print(
                    f"  {GREEN}✔ Hidden Test {idx} [{tc['category']}]: PASSED ({res['elapsed_ms']:.1f} ms){RESET}"
                )
            else:
                print(
                    f"  {RED}✘ Hidden Test {idx} [{tc['category']}]: {res['status']} ({res['elapsed_ms']:.1f} ms){RESET}"
                )
                print(
                    f"    {DIM}Hint / Category: {tc.get('hint', 'Check boundary conditions and malformed inputs.')}{RESET}"
                )
                if res["status"] in ("TLE", "EXCEPTION", "MISSING_FN", "CRASH"):
                    for line in res["error"].strip().splitlines()[-4:]:
                        print(f"    {YELLOW}{line}{RESET}")

    # Summary Banner
    print(f"\n{BOLD}{'-' * 74}{RESET}")
    score_color = GREEN if total_passed == total_cases else (YELLOW if total_passed > 0 else RED)
    print(
        f"{BOLD}  Result: {score_color}{total_passed} / {total_cases} Test Cases Passed{RESET}"
    )
    if not args.submit and total_passed == total_cases:
        print(
            f"  {CYAN}Tip: All sample tests passed! Run with `--submit` to test against hidden edge cases and large inputs.{RESET}"
        )
    print(f"{BOLD}{'-' * 74}{RESET}\n")

    return 0 if total_passed == total_cases else 1


if __name__ == "__main__":
    sys.exit(main())
