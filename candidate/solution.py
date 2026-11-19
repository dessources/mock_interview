"""
Microsoft Network Engineering Intern — Coding Assessment
Candidate Workspace (`solution.py`)

Run public sample tests:
    python3 run_tests.py --part 1

Run full submission (includes hidden edge-case & stress tests):
    python3 run_tests.py --part 1 --submit
"""

from __future__ import annotations


# ============================================================================
# PART 1: Top Offending Source IPs by Dropped Bytes
# ============================================================================

def top_dropped_sources(logs: list[str], k: int) -> list[tuple[str, int]]:
    """
    Parse Azure NSG flow logs and return the top `k` source IPs by total
    dropped bytes.

    Args:
        logs: List of raw log strings.
        k: Maximum number of top offending source IPs to return.

    Returns:
        List of (src_ip, total_dropped_bytes) sorted by:
          1. total_dropped_bytes descending
          2. src_ip ascending (lexicographical tie-breaker)
    """
    # TODO: Write your Part 1 implementation here
    pass
