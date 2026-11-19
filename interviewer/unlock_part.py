#!/usr/bin/env python3
"""
PRIVATE INTERVIEWER HELPER: Live Follow-Up Unlocker

Run this from your private terminal during the mock interview (or click the
Unlock buttons on the Interviewer Control Deck at http://127.0.0.1:8766)
to seamlessly unlock Part 2 or Part 3 inside the candidate's workspace
without overwriting any of their existing code in `candidate/solution.py`!

Usage:
  python3 interviewer/unlock_part.py 2       # Appends Part 2 (Validation) prompt & stub
  python3 interviewer/unlock_part.py 3       # Appends Part 3 (Top-K & Scale) prompt & stub
  python3 interviewer/unlock_part.py reset   # Resets candidate/PROBLEM.md & solution.py to Part 1 only
"""

from __future__ import annotations
import os
import sys

INTERVIEWER_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(INTERVIEWER_DIR)
CANDIDATE_PROBLEM = os.path.join(ROOT_DIR, "candidate", "PROBLEM.md")
CANDIDATE_SOLUTION = os.path.join(ROOT_DIR, "candidate", "solution.py")

PART2_PROBLEM_MD = """
---

## Part 2 (Follow-Up 1): Handling Corrupted Telemetry & Shuffled Fields

**Run Sample Tests:** `python3 run_tests.py --part 2`  
**Submit Solution:** `python3 run_tests.py --part 2 --submit`

### Background

Your Part 1 script works great on clean logs! Now we are deploying it to production Azure collectors, where telemetry lines occasionally arrive **corrupted**, **incomplete**, or with `KEY=VALUE` fields in **arbitrary order**.

### Task

Implement the function:

```python
def count_valid_dropped_bytes(logs: list[str]) -> dict[str, int]:
```

A log line is **valid** if and only if **all** of the following hold:
1. After stripping leading/trailing whitespace, the line consists of **6 space-separated tokens**: `<timestamp>` followed by 5 `KEY=VALUE` tokens.
2. `<timestamp>` is a non-negative integer (`>= 0`, digits only).
3. The 5 `KEY=VALUE` tokens contain **each** of the required keys (`SRC`, `DST`, `PORT`, `ACTION`, `BYTES`) **exactly once**, in **any order**.
4. Both `<src_ip>` (`SRC`) and `<dst_ip>` (`DST`) are valid **IPv4 addresses** (`A.B.C.D`):
   - Exactly **4** dot-separated octets.
   - Digits only, **no leading zeros** (e.g., `"0"` is valid, `"01"` or `"00"` is invalid).
   - Each octet is in the inclusive range `0 <= octet <= 255`.
5. `<dst_port>` (`PORT`) is an integer in the valid TCP/UDP port range `1 <= port <= 65535`.
6. `<ACTION>` is either `"ALLOW"` or `"DROP"`.
7. `<byte_count>` (`BYTES`) is a non-negative integer (`>= 0`, digits only).

Any line that violates any rule above must be **silently ignored**. Return `{src_ip: total_dropped_bytes}` for all valid `ACTION=DROP` lines.
"""

PART2_SOLUTION_STUB = """

# ============================================================================
# PART 2: Strict Telemetry Validation & Out-of-Order Field Parsing
# ============================================================================

def count_valid_dropped_bytes(logs: list[str]) -> dict[str, int]:
    \"\"\"
    Strictly validate raw NSG flow logs (ignoring malformed IPs, ports,
    actions, negative values, duplicate/missing keys, and handling shuffled
    KEY=VALUE fields) and return {src_ip: total_dropped_bytes} for valid
    ACTION=DROP lines.
    \"\"\"
    # TODO: Write your Part 2 implementation here
    pass
"""

PART3_PROBLEM_MD = """
---

## Part 3 (Follow-Up 2): Top-K Offenders, Tie-Breaking & High-Scale Optimization

**Run Sample Tests:** `python3 run_tests.py --part 3`  
**Submit Solution:** `python3 run_tests.py --part 3 --submit`

### Background

During a large incident, the Azure security dashboard does not want a dictionary with tens of thousands of source IPs—it only wants the **Top `k` worst offenders** ranked deterministically, and it needs to process **50,000+ log lines** within strict latency limits.

### Task

Implement the function:

```python
def top_dropped_sources(logs: list[str], k: int) -> list[tuple[str, int]]:
```

1. Reuse your **Part 2** validation and `ACTION=DROP` aggregation logic (all malformed lines are silently ignored).
2. Return the top `k` source IPs as a list of `(src_ip, total_dropped_bytes)` tuples:
   - Sorted by `total_dropped_bytes` in **descending** order.
   - If two source IPs have the exact same `total_dropped_bytes`, break ties by `src_ip` in **ascending lexicographical (ASCII)** order (e.g., `"10.0.0.10"` comes before `"10.0.0.2"` because `'1' < '2'`).
   - If `k <= 0` or there are no valid `DROP` lines, return `[]`.
   - If fewer than `k` unique source IPs have dropped traffic, return all of them in ranked order.

### Performance Constraints
- `0 <= len(logs) <= 100,000`
- `0 <= k <= 10,000`
- Expected Time Complexity: $\\mathcal{O}(N + U \\log K)$ using a heap (`heapq.nsmallest`) — or $\\mathcal{O}(N + U \\log U)$ — where $N$ is the number of log lines and $U$ is the number of unique source IPs.
"""

PART3_SOLUTION_STUB = """

# ============================================================================
# PART 3: Top-K Offenders, Tie-Breaking & High-Scale Optimization
# ============================================================================

def top_dropped_sources(logs: list[str], k: int) -> list[tuple[str, int]]:
    \"\"\"
    Return the top `k` valid offending source IPs as (src_ip, total_dropped_bytes)
    sorted by:
      1. total_dropped_bytes descending
      2. src_ip ascending (lexicographical tie-breaker)

    Returns [] if k <= 0 or no valid DROP lines exist.
    \"\"\"
    # TODO: Write your Part 3 implementation here
    pass
"""


def unlock(target: str) -> None:
    with open(CANDIDATE_PROBLEM, "r", encoding="utf-8") as f:
        problem_text = f.read()
    with open(CANDIDATE_SOLUTION, "r", encoding="utf-8") as f:
        solution_text = f.read()

    if target == "reset":
        marker = "\n---\n\n## Part 2 (Follow-Up 1):"
        if marker in problem_text:
            problem_text = problem_text.split(marker)[0] + "\n"
            with open(CANDIDATE_PROBLEM, "w", encoding="utf-8") as f:
                f.write(problem_text)
        sol_marker = "\n# ============================================================================\n# PART 2:"
        if sol_marker in solution_text:
            solution_text = solution_text.split(sol_marker)[0].rstrip() + "\n"
            with open(CANDIDATE_SOLUTION, "w", encoding="utf-8") as f:
                f.write(solution_text)
        print("✔ Reset candidate/PROBLEM.md and candidate/solution.py to Part 1 only.")
        return

    if target in ("2", "3", "all"):
        if "## Part 2 (Follow-Up 1):" not in problem_text:
            problem_text = problem_text.rstrip() + "\n" + PART2_PROBLEM_MD
            with open(CANDIDATE_PROBLEM, "w", encoding="utf-8") as f:
                f.write(problem_text)
            print("✔ Appended Part 2 instructions to candidate/PROBLEM.md")
        if "def count_valid_dropped_bytes" not in solution_text:
            solution_text = solution_text.rstrip() + "\n" + PART2_SOLUTION_STUB
            with open(CANDIDATE_SOLUTION, "w", encoding="utf-8") as f:
                f.write(solution_text)
            print("✔ Appended Part 2 function stub to candidate/solution.py (existing code preserved)")

    if target in ("3", "all"):
        if "## Part 3 (Follow-Up 2):" not in problem_text:
            problem_text = problem_text.rstrip() + "\n" + PART3_PROBLEM_MD
            with open(CANDIDATE_PROBLEM, "w", encoding="utf-8") as f:
                f.write(problem_text)
            print("✔ Appended Part 3 instructions to candidate/PROBLEM.md")
        if "def top_dropped_sources" not in solution_text:
            solution_text = solution_text.rstrip() + "\n" + PART3_SOLUTION_STUB
            with open(CANDIDATE_SOLUTION, "w", encoding="utf-8") as f:
                f.write(solution_text)
            print("✔ Appended Part 3 function stub to candidate/solution.py (existing code preserved)")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("2", "3", "all", "reset"):
        print("Usage: python3 interviewer/unlock_part.py [2 | 3 | all | reset]")
        sys.exit(1)
    unlock(sys.argv[1])
