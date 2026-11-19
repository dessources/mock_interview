#!/usr/bin/env python3
"""
PRIVATE INTERVIEWER HELPER: Live Follow-Up Unlocker

Run this from your private terminal during the mock interview to seamlessly
unlock Part 2 or Part 3 inside the candidate's folder without overwriting
their existing code in `candidate/solution.py`!

Usage:
  python3 interviewer/unlock_part.py 2       # Appends Part 2 prompt & function stubs
  python3 interviewer/unlock_part.py 3       # Appends Part 3 prompt & function stub
  python3 interviewer/unlock_part.py reset   # Resets candidate/PROBLEM.md to Part 1 only
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

## Part 2 (Follow-Up 1): CIDR Longest Prefix Match & Internal Subnet Filtering

**Run Sample Tests:** `python3 run_tests.py --part 2`  
**Submit Solution:** `python3 run_tests.py --part 2 --submit`

### Background

During the incident review, the Azure Networking team notices that many high-volume `DROP` logs come from internal Azure fabric health probes (e.g., `10.0.0.0/8`), EXCEPT for specific subnets inside `10.0.0.0/8` that have been delegated to external DMZ appliances (e.g., `10.1.2.0/24`).

In IP networking, routers classify an IP address against a routing table using **Longest Prefix Match (LPM)**:
- A CIDR rule has the format `"<network_ip>/<prefix_len>"`, where `0 <= prefix_len <= 32`.
- An IPv4 address matches a CIDR rule if the **top `prefix_len` most significant bits** of the 32-bit IPv4 address match the top `prefix_len` bits of `<network_ip>`.
- When multiple CIDR rules match an IP address, the rule with the **largest `prefix_len`** (most specific subnet) wins.
- If multiple matching rules share the exact same largest `prefix_len`, the rule that appears **earlier** in `cidr_rules` wins.
- If no rule matches (or the target `ip` is invalid), the classification is `"UNMATCHED"`.
- Malformed CIDR rules in `cidr_rules` must be ignored.

### Task

Implement two functions in `solution.py`:

```python
def match_longest_prefix(ip: str, cidr_rules: list[tuple[str, str]]) -> str:
```
Given a target IPv4 string `ip` and a list of `(cidr_prefix, route_tag)` tuples, return the `route_tag` of the Longest Prefix Match (or `"UNMATCHED"` if none match).

```python
def top_dropped_external_sources(
    logs: list[str], k: int, cidr_rules: list[tuple[str, str]]
) -> list[tuple[str, int]]:
```
Same as Part 1, except **exclude** any source IP whose Longest Prefix Match tag in `cidr_rules` equals `"INTERNAL"`. Source IPs that resolve to any other tag (including `"UNMATCHED"`) must be included.
"""

PART2_SOLUTION_STUB = """

# ============================================================================
# PART 2: CIDR Longest Prefix Match & Internal Subnet Filtering
# ============================================================================

def match_longest_prefix(ip: str, cidr_rules: list[tuple[str, str]]) -> str:
    \"\"\"
    Return the route_tag of the CIDR rule that matches `ip` with the longest
    prefix length (0..32). If no rule matches, return "UNMATCHED".
    \"\"\"
    # TODO: Write your Part 2 LPM implementation here
    pass


def top_dropped_external_sources(
    logs: list[str], k: int, cidr_rules: list[tuple[str, str]]
) -> list[tuple[str, int]]:
    \"\"\"
    Return the top `k` source IPs by total dropped bytes, EXCLUDING any
    source IP whose `match_longest_prefix(src_ip, cidr_rules)` == "INTERNAL".
    \"\"\"
    # TODO: Write your Part 2 filtered aggregation here
    pass
"""

PART3_PROBLEM_MD = """
---

## Part 3 (Follow-Up 2): Sliding-Window Burst / DDoS Anomaly Detection

**Run Sample Tests:** `python3 run_tests.py --part 3`  
**Submit Solution:** `python3 run_tests.py --part 3 --submit`

### Background

Some attackers avoid topping the total-bytes leaderboard by sending many small `DROP` probe packets (e.g., 64-byte TCP SYN scans) in a rapid burst.

### Task

Implement the function:

```python
def detect_burst_sources(
    logs: list[str], window_sec: int, threshold: int
) -> list[str]:
```

1. Consider only **valid** log lines where `ACTION=DROP`. (Note: log lines are **not** guaranteed to arrive in chronological order!)
2. Identify every unique `<src_ip>` that has **at least `threshold`** (`>= threshold`) `DROP` events occurring within **any inclusive rolling time window** of length `window_sec` seconds — i.e., `[t, t + window_sec]` where `t_last - t_first <= window_sec`.
3. Return the offending source IPs sorted in **ascending lexicographical order**.
4. Expected Time Complexity: $\\mathcal{O}(N \\log N)$ using sorting + a Two-Pointer / Sliding Window scan.
"""

PART3_SOLUTION_STUB = """

# ============================================================================
# PART 3: Sliding-Window Burst / DDoS Anomaly Detection
# ============================================================================

def detect_burst_sources(
    logs: list[str], window_sec: int, threshold: int
) -> list[str]:
    \"\"\"
    Return a lexicographically sorted list of unique source IPs that trigger
    at least `threshold` valid DROP events within any inclusive `window_sec`
    time window [t, t + window_sec].
    \"\"\"
    # TODO: Write your Part 3 sliding-window implementation here
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
        if "def match_longest_prefix" not in solution_text:
            solution_text = solution_text.rstrip() + "\n" + PART2_SOLUTION_STUB
            with open(CANDIDATE_SOLUTION, "w", encoding="utf-8") as f:
                f.write(solution_text)
            print("✔ Appended Part 2 function stubs to candidate/solution.py (existing code preserved)")

    if target in ("3", "all"):
        if "## Part 3 (Follow-Up 2):" not in problem_text:
            problem_text = problem_text.rstrip() + "\n" + PART3_PROBLEM_MD
            with open(CANDIDATE_PROBLEM, "w", encoding="utf-8") as f:
                f.write(problem_text)
            print("✔ Appended Part 3 instructions to candidate/PROBLEM.md")
        if "def detect_burst_sources" not in solution_text:
            solution_text = solution_text.rstrip() + "\n" + PART3_SOLUTION_STUB
            with open(CANDIDATE_SOLUTION, "w", encoding="utf-8") as f:
                f.write(solution_text)
            print("✔ Appended Part 3 function stub to candidate/solution.py (existing code preserved)")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("2", "3", "all", "reset"):
        print("Usage: python3 interviewer/unlock_part.py [2 | 3 | all | reset]")
        sys.exit(1)
    unlock(sys.argv[1])
