"""
PRIVATE INTERVIEWER FILE — DO NOT SHARE WITH CANDIDATE
Reference Solutions (Optimal & Suboptimal) for all 3 parts of the
Microsoft Network Engineering Intern Mock Assessment.
"""

from __future__ import annotations
from collections import defaultdict
import heapq


# ============================================================================
# SHARED HELPER: Strict IPv4 & Flow Log Validation
# ============================================================================

def is_valid_ipv4(ip_str: str) -> bool:
    """
    Validate dotted-quad IPv4 string (`A.B.C.D`):
    - Exactly 4 parts separated by '.'
    - Digits only, no leading zeros (e.g. '01' is invalid, '0' is valid)
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


def ipv4_to_int(ip_str: str) -> int:
    """Convert valid dotted-quad IPv4 string to a 32-bit unsigned integer."""
    a, b, c, d = map(int, ip_str.split("."))
    return (a << 24) | (b << 16) | (c << 8) | d


REQUIRED_KEYS = {"SRC", "DST", "PORT", "ACTION", "BYTES"}


def parse_log_line(line: str) -> tuple[int, str, str, int, str, int] | None:
    """
    Parse and validate a raw NSG flow log line.
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


# ============================================================================
# PART 1: Top Offending Source IPs by Dropped Bytes
# ============================================================================

def top_dropped_sources(logs: list[str], k: int) -> list[tuple[str, int]]:
    """
    Optimal Solution:
    Time Complexity: O(N + U log K) where N = len(logs), U = unique dropped IPs
    Space Complexity: O(U)
    """
    if k <= 0:
        return []

    dropped_bytes: dict[str, int] = defaultdict(int)
    for line in logs:
        parsed = parse_log_line(line)
        if parsed is None:
            continue
        _, src_ip, _, _, action, byte_count = parsed
        if action == "DROP":
            dropped_bytes[src_ip] += byte_count

    # Sort key: (-bytes, src_ip). heapq.nsmallest runs in O(U log K)
    return heapq.nsmallest(
        k, dropped_bytes.items(), key=lambda item: (-item[1], item[0])
    )


# ============================================================================
# PART 2: CIDR Longest Prefix Match (LPM) & Subnet Filtering
# ============================================================================

def parse_cidr(cidr_str: str) -> tuple[int, int, int] | None:
    """
    Parse 'A.B.C.D/prefix' into (network_int, mask_int, prefix_len).
    Returns None if malformed.
    Note: Carefully handles /0 so we don't shift by 32 bits without masking!
    """
    if "/" not in cidr_str:
        return None
    ip_part, prefix_part = cidr_str.split("/", 1)
    if not is_valid_ipv4(ip_part) or not prefix_part.isdigit():
        return None
    if len(prefix_part) > 1 and prefix_part[0] == "0":
        return None
    prefix_len = int(prefix_part)
    if prefix_len < 0 or prefix_len > 32:
        return None

    ip_int = ipv4_to_int(ip_part)
    if prefix_len == 0:
        mask = 0
    else:
        mask = ((0xFFFFFFFF << (32 - prefix_len)) & 0xFFFFFFFF)

    return (ip_int & mask), mask, prefix_len


def match_longest_prefix(ip: str, cidr_rules: list[tuple[str, str]]) -> str:
    """
    Match a single valid IPv4 address against a list of (cidr_str, route_tag) rules
    using Longest Prefix Match (LPM).
    - If multiple rules with the SAME prefix length match, the one that appears
      EARLIER in `cidr_rules` wins.
    - If no rule matches (or `ip` is invalid), return "UNMATCHED".
    """
    if not is_valid_ipv4(ip):
        return "UNMATCHED"

    ip_int = ipv4_to_int(ip)
    best_prefix = -1
    best_tag = "UNMATCHED"

    for cidr_str, tag in cidr_rules:
        parsed = parse_cidr(cidr_str)
        if parsed is None:
            continue
        net_int, mask, prefix_len = parsed
        if (ip_int & mask) == net_int:
            if prefix_len > best_prefix:
                best_prefix = prefix_len
                best_tag = tag

    return best_tag


class _TrieNode:
    __slots__ = ("children", "tag")

    def __init__(self) -> None:
        self.children: list[_TrieNode | None] = [None, None]
        self.tag: str | None = None


def top_dropped_external_sources(
    logs: list[str], k: int, cidr_rules: list[tuple[str, str]]
) -> list[tuple[str, int]]:
    """
    Optimal Solution using a 32-bit Binary Prefix Trie (or pre-parsed rule table):
    - Build the bitwise Trie once in O(R * 32) where R = len(cidr_rules).
    - Aggregate dropped bytes per unique source IP first in O(N).
    - Lookup each unique source IP in the Trie in O(32) = O(1) time!
    - Exclude any source IP whose Longest Prefix Match tag is "INTERNAL".
    """
    if k <= 0:
        return []

    # Build bitwise Trie for O(32) Longest Prefix Match
    root = _TrieNode()
    for cidr_str, tag in cidr_rules:
        parsed = parse_cidr(cidr_str)
        if parsed is None:
            continue
        net_int, _, prefix_len = parsed
        node = root
        for bit_idx in range(31, 31 - prefix_len, -1):
            bit = (net_int >> bit_idx) & 1
            if node.children[bit] is None:
                node.children[bit] = _TrieNode()
            node = node.children[bit]  # type: ignore[assignment]
        # Earlier rule wins on identical prefix length
        if node.tag is None:
            node.tag = tag

    def lookup_lpm(ip_str: str) -> str:
        ip_int = ipv4_to_int(ip_str)
        node: _TrieNode | None = root
        matched_tag = root.tag if root.tag is not None else "UNMATCHED"
        for bit_idx in range(31, -1, -1):
            if node is None:
                break
            bit = (ip_int >> bit_idx) & 1
            node = node.children[bit]
            if node is not None and node.tag is not None:
                matched_tag = node.tag
        return matched_tag

    dropped_bytes: dict[str, int] = defaultdict(int)
    for line in logs:
        parsed = parse_log_line(line)
        if parsed is None:
            continue
        _, src_ip, _, _, action, byte_count = parsed
        if action == "DROP":
            dropped_bytes[src_ip] += byte_count

    filtered = [
        (ip, total)
        for ip, total in dropped_bytes.items()
        if lookup_lpm(ip) != "INTERNAL"
    ]
    return heapq.nsmallest(k, filtered, key=lambda item: (-item[1], item[0]))


# ============================================================================
# PART 3: Sliding-Window Burst / DDoS Anomaly Detection
# ============================================================================

def detect_burst_sources(
    logs: list[str], window_sec: int, threshold: int
) -> list[str]:
    """
    Optimal Solution (Two-Pointer Sliding Window per IP):
    Identify all unique source IPs that have >= `threshold` valid `DROP` events
    within ANY inclusive time window `[t, t + window_sec]`.
    Return the list of offending IPs sorted in ascending lexicographical order.

    Time Complexity: O(N log N) due to sorting timestamps per IP.
    Space Complexity: O(N)
    """
    if threshold <= 0 or window_sec < 0:
        return []

    drops_by_ip: dict[str, list[int]] = defaultdict(list)
    for line in logs:
        parsed = parse_log_line(line)
        if parsed is None:
            continue
        timestamp, src_ip, _, _, action, _ = parsed
        if action == "DROP":
            drops_by_ip[src_ip].append(timestamp)

    burst_ips: list[str] = []
    for src_ip, timestamps in drops_by_ip.items():
        if len(timestamps) < threshold:
            continue
        timestamps.sort()
        left = 0
        for right in range(len(timestamps)):
            while timestamps[right] - timestamps[left] > window_sec:
                left += 1
            if (right - left + 1) >= threshold:
                burst_ips.append(src_ip)
                break

    burst_ips.sort()
    return burst_ips
