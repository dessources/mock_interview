"""
PRIVATE INTERVIEWER FILE — DO NOT SHARE WITH CANDIDATE
Reference Solutions for all 3 progressive stages of the
Azure VNet Flow Log Analyzer mock interview.
"""

from __future__ import annotations
from collections import defaultdict
import heapq


# ============================================================================
# PART 1: Basic Drop Filtering & Byte Aggregation (Clean Input)
# ============================================================================

def count_dropped_bytes(logs: list[str]) -> dict[str, int]:
    """
    Part 1 Optimal Solution:
    Every line is guaranteed valid and in fixed order:
      <timestamp> SRC=<src_ip> DST=<dst_ip> PORT=<port> ACTION=<ALLOW|DROP> BYTES=<n>

    Time Complexity: O(N)
    Space Complexity: O(U) where U is unique dropped source IPs
    """
    totals: dict[str, int] = defaultdict(int)
    for line in logs:
        parts = line.strip().split()
        # parts: [timestamp, SRC=..., DST=..., PORT=..., ACTION=..., BYTES=...]
        src_ip = parts[1].split("=", 1)[1]
        action = parts[4].split("=", 1)[1]
        byte_count = int(parts[5].split("=", 1)[1])
        if action == "DROP":
            totals[src_ip] += byte_count
    return dict(totals)


# ============================================================================
# PART 2: Strict Telemetry Validation & Out-of-Order Field Parsing
# ============================================================================

def is_valid_ipv4(ip_str: str) -> bool:
    """
    Validate dotted-quad IPv4 string (`A.B.C.D`):
    - Exactly 4 dot-separated octets
    - Digits only, no leading zeros (e.g., '01' is invalid, '0' is valid)
    - Each octet in 0..255
    """
    parts = ip_str.split(".")
    if len(parts) != 4:
        return False
    for p in parts:
        if not p.isdigit():
            return False
        if len(p) > 1 and p[0] == "0":
            return False
        val = int(p)
        if val < 0 or val > 255:
            return False
    return True


REQUIRED_KEYS = {"SRC", "DST", "PORT", "ACTION", "BYTES"}


def parse_log_line(line: str) -> tuple[int, str, str, int, str, int] | None:
    """
    Parse and strictly validate a raw NSG flow log line.
    Returns (timestamp, src_ip, dst_ip, port, action, byte_count) if valid,
    or None if malformed.
    """
    tokens = line.strip().split()
    if len(tokens) != 6:
        return None

    ts_str = tokens[0]
    if not ts_str.isdigit():
        return None
    timestamp = int(ts_str)

    kv: dict[str, str] = {}
    for token in tokens[1:]:
        if "=" not in token:
            return None
        k, v = token.split("=", 1)
        if k in kv or k not in REQUIRED_KEYS:
            return None
        kv[k] = v

    if len(kv) != 5:
        return None

    src_ip = kv["SRC"]
    dst_ip = kv["DST"]
    if not (is_valid_ipv4(src_ip) and is_valid_ipv4(dst_ip)):
        return None

    port_str = kv["PORT"]
    if not port_str.isdigit():
        return None
    port = int(port_str)
    if port < 1 or port > 65535:
        return None

    action = kv["ACTION"]
    if action not in ("ALLOW", "DROP"):
        return None

    bytes_str = kv["BYTES"]
    if not bytes_str.isdigit():
        return None
    byte_count = int(bytes_str)

    return timestamp, src_ip, dst_ip, port, action, byte_count


def count_valid_dropped_bytes(logs: list[str]) -> dict[str, int]:
    """
    Part 2 Optimal Solution:
    Silently ignore malformed lines and aggregate dropped bytes per valid source IP.

    Time Complexity: O(N)
    Space Complexity: O(U)
    """
    totals: dict[str, int] = defaultdict(int)
    for line in logs:
        parsed = parse_log_line(line)
        if parsed is None:
            continue
        _, src_ip, _, _, action, byte_count = parsed
        if action == "DROP":
            totals[src_ip] += byte_count
    return dict(totals)


# ============================================================================
# PART 3: Top-K Ranking, Tie-Breaking & High-Scale Optimization
# ============================================================================

def top_dropped_sources(logs: list[str], k: int) -> list[tuple[str, int]]:
    """
    Part 3 Optimal Solution:
    Reuses Part 2's validated aggregation, then extracts the top `k` offenders
    in O(U log K) time using `heapq.nsmallest` with key `(-total_bytes, src_ip)`.

    Time Complexity: O(N + U log K)
    Space Complexity: O(U)
    """
    if k <= 0:
        return []

    totals = count_valid_dropped_bytes(logs)
    return heapq.nsmallest(
        k, totals.items(), key=lambda item: (-item[1], item[0])
    )
