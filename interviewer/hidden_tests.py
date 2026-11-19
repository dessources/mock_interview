"""
PRIVATE INTERVIEWER FILE — DO NOT SHARE WITH CANDIDATE
Comprehensive Hidden & Stress Test Suite for Parts 1, 2, and 3.
"""

from __future__ import annotations
import random
import reference_solutions as ref


def _build_part1_hidden_tests() -> list[dict]:
    tests: list[dict] = []

    # 1. Edge cases: k=0, empty logs, k > unique IPs
    tests.append(
        {
            "category": "Edge Case: Empty Logs & k=0",
            "hint": "What should your function return when k <= 0 or logs is empty?",
            "args": (
                [
                    "1700000001 SRC=10.0.0.1 DST=10.0.0.2 PORT=80 ACTION=DROP BYTES=500"
                ],
                0,
            ),
            "expected": [],
        }
    )

    # 2. Strict IPv4 & Port / Action / Duplicate-Key Validation
    malformed_logs = [
        "1700000001 SRC=256.0.0.1 DST=10.0.0.1 PORT=80 ACTION=DROP BYTES=100",       # octet 256
        "1700000001 SRC=10.0.0.1.5 DST=10.0.0.1 PORT=80 ACTION=DROP BYTES=100",      # 5 octets
        "1700000001 SRC=10.0.0 DST=10.0.0.1 PORT=80 ACTION=DROP BYTES=100",          # 3 octets
        "1700000001 SRC=10.00.0.1 DST=10.0.0.1 PORT=80 ACTION=DROP BYTES=100",       # leading zero '00'
        "1700000001 SRC=10.0.0.1 DST=10.0.0.01 PORT=80 ACTION=DROP BYTES=100",       # leading zero in DST
        "1700000001 SRC=10.0.0.1 DST=10.0.0.2 PORT=0 ACTION=DROP BYTES=100",         # port 0 invalid
        "1700000001 SRC=10.0.0.1 DST=10.0.0.2 PORT=65536 ACTION=DROP BYTES=100",     # port 65536 invalid
        "1700000001 SRC=10.0.0.1 DST=10.0.0.2 PORT=80 ACTION=REJECT BYTES=100",      # invalid ACTION
        "1700000001 SRC=10.0.0.1 DST=10.0.0.2 PORT=80 ACTION=DROP BYTES=-50",        # negative bytes
        "-5 SRC=10.0.0.1 DST=10.0.0.2 PORT=80 ACTION=DROP BYTES=100",                # negative timestamp
        "1700000001 SRC=10.0.0.1 SRC=10.0.0.1 PORT=80 ACTION=DROP BYTES=100",        # missing DST / duplicate SRC
        "   1700000009 BYTES=0 ACTION=DROP PORT=65535 DST=255.255.255.255 SRC=0.0.0.0  ",  # valid boundary values!
    ]
    tests.append(
        {
            "category": "Strict IPv4, Port & Boundary Validation",
            "hint": "Check octet bounds (0..255), leading zeros ('00'/'01'), port bounds (1..65535), and 0-byte drops.",
            "args": (malformed_logs, 5),
            "expected": [("0.0.0.0", 0)],
        }
    )

    # 3. Multi-way Tie-Breaking
    tie_logs = [
        "1700000001 SRC=10.0.0.10 DST=1.1.1.1 PORT=443 ACTION=DROP BYTES=500",
        "1700000002 SRC=10.0.0.2 DST=1.1.1.1 PORT=443 ACTION=DROP BYTES=500",
        "1700000003 SRC=10.0.0.1 DST=1.1.1.1 PORT=443 ACTION=DROP BYTES=300",
        "1700000004 SRC=10.0.0.1 DST=1.1.1.1 PORT=443 ACTION=DROP BYTES=200",
        "1700000005 SRC=10.0.0.20 DST=1.1.1.1 PORT=443 ACTION=DROP BYTES=900",
    ]
    tests.append(
        {
            "category": "Multi-Way Tie-Breaking & Exact K Slice",
            "hint": "When dropped byte totals are equal, break ties by IP string in ascending lexicographical order.",
            "args": (tie_logs, 3),
            "expected": [
                ("10.0.0.20", 900),
                ("10.0.0.1", 500),
                ("10.0.0.10", 500),
            ],
        }
    )

    # 4. Large Stress Test (40,000 log lines)
    rng = random.Random(42)
    stress_logs: list[str] = []
    for i in range(40_000):
        b = (i % 50)
        c = (i % 40)
        action = "DROP" if (i % 3 != 0) else "ALLOW"
        byte_cnt = rng.randint(64, 1500)
        stress_logs.append(
            f"{1700000000 + i} SRC=172.16.{b}.{c} DST=10.0.0.1 PORT=443 ACTION={action} BYTES={byte_cnt}"
        )
    expected_stress = ref.top_dropped_sources(stress_logs, 15)
    tests.append(
        {
            "category": "Performance Stress Test (40,000 Log Lines)",
            "hint": "Ensure single-pass O(N) aggregation using a hash map before sorting/heaping.",
            "args": (stress_logs, 15),
            "expected": expected_stress,
            "timeout_sec": 1.5,
        }
    )

    return tests


def _build_part2_hidden_tests() -> list[dict]:
    tests: list[dict] = []

    # 1. /0 Default Route, /32 Host Route, and Same-Length Rule Precedence
    tests.append(
        {
            "category": "CIDR /0 Bitmask & Same-Prefix Precedence",
            "hint": "Be careful shifting by 32 bits for a /0 prefix! Also, earlier rules win on ties of identical prefix length.",
            "fn": "match_longest_prefix",
            "args": (
                "172.31.255.254",
                [
                    ("10.0.0.0/8", "CORP"),
                    ("0.0.0.0/0", "FIRST_DEFAULT"),
                    ("0.0.0.0/0", "SECOND_DEFAULT"),
                ],
            ),
            "expected": "FIRST_DEFAULT",
        }
    )

    # 2. Non-Octet-Aligned Prefixes (/12, /20, /27, /31)
    tests.append(
        {
            "category": "Non-Octet Boundary Prefixes (/12, /20, /27)",
            "hint": "String prefix matching fails on /12 or /27! Convert IPv4 to a 32-bit integer and apply a bitwise mask.",
            "fn": "match_longest_prefix",
            "args": (
                "172.31.192.30",
                [
                    ("172.16.0.0/12", "PRIVATE_CLASS_B"),
                    ("172.31.192.0/27", "SUBNET_A_0_TO_31"),
                    ("172.31.192.32/27", "SUBNET_B_32_TO_63"),
                ],
            ),
            "expected": "SUBNET_A_0_TO_31",
        }
    )

    # 3. Unmatched IP & Malformed CIDR Rules Ignored
    tests.append(
        {
            "category": "Unmatched Route & Specific Override of INTERNAL",
            "hint": "If an IP matches 10.0.0.0/8 (INTERNAL) AND 10.5.5.0/24 (DMZ_EXTERNAL), the /24 route is longer so the IP is NOT internal!",
            "fn": "top_dropped_external_sources",
            "args": (
                [
                    "1700000001 SRC=10.5.5.9 DST=10.0.0.1 PORT=443 ACTION=DROP BYTES=4000",   # /24 DMZ_EXTERNAL -> keep!
                    "1700000002 SRC=10.5.6.9 DST=10.0.0.1 PORT=443 ACTION=DROP BYTES=9000",   # /8 INTERNAL -> exclude!
                    "1700000003 SRC=198.51.100.7 DST=10.0.0.1 PORT=80 ACTION=DROP BYTES=2500", # UNMATCHED -> keep!
                ],
                5,
                [
                    ("10.0.0.0/8", "INTERNAL"),
                    ("10.5.5.0/24", "DMZ_EXTERNAL"),
                    ("10.5.5.0/33", "INVALID_PREFIX_IGNORED"),
                ],
            ),
            "expected": [("10.5.5.9", 4000), ("198.51.100.7", 2500)],
        }
    )

    # 4. Stress Test: 30,000 Logs + 500 CIDR Rules
    rng = random.Random(101)
    cidr_rules: list[tuple[str, str]] = [("0.0.0.0/0", "INTERNET")]
    for i in range(1, 250):
        cidr_rules.append((f"10.{i}.0.0/16", "INTERNAL" if i % 2 == 0 else "PARTNER_VNET"))
        cidr_rules.append((f"10.{i}.{i % 100}.0/24", "INTERNAL" if i % 3 == 0 else "DMZ"))

    stress_logs: list[str] = []
    for i in range(30_000):
        second_octet = (i % 240) + 1
        third_octet = i % 120
        fourth_octet = (i % 250) + 1
        stress_logs.append(
            f"{1700000000 + i} SRC=10.{second_octet}.{third_octet}.{fourth_octet} DST=10.0.0.1 PORT=443 ACTION=DROP BYTES={rng.randint(100, 1000)}"
        )

    expected_stress = ref.top_dropped_external_sources(stress_logs, 10, cidr_rules)
    tests.append(
        {
            "category": "Performance Stress Test (30,000 Logs x 500 CIDR Rules)",
            "hint": "Pre-parse CIDR rules into 32-bit integers (or a Bitwise Trie) and evaluate LPM once per unique IP, not once per log line!",
            "fn": "top_dropped_external_sources",
            "args": (stress_logs, 10, cidr_rules),
            "expected": expected_stress,
            "timeout_sec": 1.5,
        }
    )

    return tests


def _build_part3_hidden_tests() -> list[dict]:
    tests: list[dict] = []

    # 1. Exact Boundary Window Inclusivity [t, t + W] & Duplicate Timestamps
    boundary_logs = [
        "1700000500 SRC=198.51.100.1 DST=10.0.0.1 PORT=80 ACTION=DROP BYTES=64",
        "1700000500 SRC=198.51.100.1 DST=10.0.0.1 PORT=80 ACTION=DROP BYTES=64",
        "1700000505 SRC=198.51.100.1 DST=10.0.0.1 PORT=80 ACTION=DROP BYTES=64",  # 505 - 500 == 5 (inclusive!) -> 3 events
        "1700000500 SRC=198.51.100.2 DST=10.0.0.1 PORT=80 ACTION=DROP BYTES=64",
        "1700000503 SRC=198.51.100.2 DST=10.0.0.1 PORT=80 ACTION=DROP BYTES=64",
        "1700000506 SRC=198.51.100.2 DST=10.0.0.1 PORT=80 ACTION=DROP BYTES=64",  # 506 - 500 == 6 > 5 -> max 2 in any 5s window
    ]
    tests.append(
        {
            "category": "Exact Window Boundary [t, t + W] & Same-Second Drops",
            "hint": "The window [t, t + window_sec] is inclusive on both ends (timestamps[right] - timestamps[left] <= window_sec).",
            "args": (boundary_logs, 5, 3),
            "expected": ["198.51.100.1"],
        }
    )

    # 2. Unordered Timestamps with Interleaved ALLOWs
    interleaved_logs = [
        "1700000090 SRC=203.0.113.77 DST=10.0.0.1 PORT=22 ACTION=DROP BYTES=100",
        "1700000010 SRC=203.0.113.77 DST=10.0.0.1 PORT=22 ACTION=DROP BYTES=100",
        "1700000085 SRC=203.0.113.77 DST=10.0.0.1 PORT=22 ACTION=DROP BYTES=100",
        "1700000080 SRC=203.0.113.77 DST=10.0.0.1 PORT=22 ACTION=DROP BYTES=100",
        "1700000082 SRC=203.0.113.77 DST=10.0.0.1 PORT=22 ACTION=ALLOW BYTES=100",
        "1700000088 SRC=203.0.113.77 DST=10.0.0.1 PORT=22 ACTION=DROP BYTES=100",
    ]
    tests.append(
        {
            "category": "Unsorted Log Stream & Early Outlier Timestamps",
            "hint": "Sort each IP's drop timestamps first and advance the left pointer using a `while` loop, not an `if` statement.",
            "args": (interleaved_logs, 10, 4),
            "expected": ["203.0.113.77"],
        }
    )

    # 3. Stress Test: 40,000 Drops on a Single IP Requiring O(N log N) Two-Pointer Window
    stress_logs: list[str] = []
    # 35,000 drops spaced 2 seconds apart -> in a 60s window, max is 31 drops
    for i in range(35_000):
        stress_logs.append(
            f"{1700000000 + i * 2} SRC=198.51.100.50 DST=10.0.0.1 PORT=443 ACTION=DROP BYTES=64"
        )
    # Burst of 45 drops within 30 seconds at the very end for 198.51.100.99
    for i in range(45):
        stress_logs.append(
            f"{1700500000 + (i % 30)} SRC=198.51.100.99 DST=10.0.0.1 PORT=443 ACTION=DROP BYTES=64"
        )

    tests.append(
        {
            "category": "Performance Stress Test (35,000+ Events per IP)",
            "hint": "Avoid O(N^2) nested loops over timestamps! Use a two-pointer sliding window in O(N) after sorting.",
            "args": (stress_logs, 60, 40),
            "expected": ["198.51.100.99"],
            "timeout_sec": 1.5,
        }
    )

    return tests


def get_hidden_tests(part: int) -> list[dict]:
    if part == 1:
        return _build_part1_hidden_tests()
    if part == 2:
        return _build_part2_hidden_tests()
    if part == 3:
        return _build_part3_hidden_tests()
    return []
