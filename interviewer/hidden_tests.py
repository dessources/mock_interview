"""
PRIVATE INTERVIEWER FILE — DO NOT SHARE WITH CANDIDATE
Comprehensive Hidden & Stress Test Suite for Parts 1, 2, and 3.
"""

from __future__ import annotations
import random
import reference_solutions as ref


def _build_part1_hidden_tests() -> list[dict]:
    tests: list[dict] = []

    # 1. Empty Input
    tests.append(
        {
            "category": "Edge Case: Empty Log List",
            "hint": "Make sure an empty list returns an empty dictionary {}.",
            "args": ([],),
            "expected": {},
        }
    )

    # 2. Mixed ALLOW and DROP for the same IP
    mixed_logs = [
        "1700000001 SRC=10.0.0.5 DST=10.0.0.1 PORT=443 ACTION=ALLOW BYTES=9000",
        "1700000002 SRC=10.0.0.5 DST=10.0.0.1 PORT=443 ACTION=DROP BYTES=250",
        "1700000003 SRC=10.0.0.5 DST=10.0.0.1 PORT=443 ACTION=ALLOW BYTES=4000",
        "1700000004 SRC=10.0.0.5 DST=10.0.0.1 PORT=22 ACTION=DROP BYTES=750",
        "1700000005 SRC=10.0.0.6 DST=10.0.0.1 PORT=80 ACTION=ALLOW BYTES=5000",
    ]
    tests.append(
        {
            "category": "Mixed ALLOW & DROP Events on Same Source IP",
            "hint": "Only accumulate BYTES when ACTION=DROP; do not add ALLOW bytes for an IP that also has DROP events.",
            "args": (mixed_logs,),
            "expected": {"10.0.0.5": 1000},
        }
    )

    # 3. Leading/Trailing Whitespace & Multiple IPs
    ws_logs = [
        "  1700000001 SRC=192.168.10.1 DST=10.0.0.1 PORT=80 ACTION=DROP BYTES=100  ",
        "1700000002 SRC=192.168.10.2 DST=10.0.0.1 PORT=80 ACTION=DROP BYTES=0",
        "1700000003 SRC=192.168.10.1 DST=10.0.0.2 PORT=443 ACTION=DROP BYTES=50",
    ]
    tests.append(
        {
            "category": "Extra Whitespace & Multiple Drops",
            "hint": "Use `.strip().split()` so leading or trailing whitespace does not shift token indices.",
            "args": (ws_logs,),
            "expected": {"192.168.10.1": 150, "192.168.10.2": 0},
        }
    )

    # 4. Moderate Scale (5,000 Clean Logs)
    rng = random.Random(11)
    scale_logs: list[str] = []
    for i in range(5_000):
        action = "DROP" if i % 2 == 0 else "ALLOW"
        scale_logs.append(
            f"{1700000000 + i} SRC=10.1.{i % 20}.{i % 50} DST=10.0.0.1 PORT=443 ACTION={action} BYTES={rng.randint(64, 1500)}"
        )
    tests.append(
        {
            "category": "Scale Check (5,000 Clean Log Lines)",
            "hint": "Use a dictionary for O(1) lookup per log line instead of scanning a list of IPs.",
            "args": (scale_logs,),
            "expected": ref.count_dropped_bytes(scale_logs),
            "timeout_sec": 1.5,
        }
    )

    return tests


def _build_part2_hidden_tests() -> list[dict]:
    tests: list[dict] = []

    # 1. Strict IPv4 Validation (octets > 255, leading zeros, wrong octet count, DST invalid too!)
    ipv4_logs = [
        "1700000001 SRC=256.0.0.1 DST=10.0.0.1 PORT=80 ACTION=DROP BYTES=100",       # octet 256
        "1700000001 SRC=10.0.0.1.5 DST=10.0.0.1 PORT=80 ACTION=DROP BYTES=100",      # 5 octets
        "1700000001 SRC=10.0.0 DST=10.0.0.1 PORT=80 ACTION=DROP BYTES=100",          # 3 octets
        "1700000001 SRC=10.00.0.1 DST=10.0.0.1 PORT=80 ACTION=DROP BYTES=100",       # leading zero '00'
        "1700000001 SRC=10.0.0.1 DST=10.0.0.01 PORT=80 ACTION=DROP BYTES=100",       # leading zero in DST!
        "1700000001 SRC=10.0.0.1 DST=300.0.0.1 PORT=80 ACTION=DROP BYTES=100",       # invalid DST octet!
        "1700000001 SRC=0.0.0.0 DST=255.255.255.255 PORT=1 ACTION=DROP BYTES=42",    # valid boundary IPs & port 1!
    ]
    tests.append(
        {
            "category": "Strict IPv4 Validation (SRC & DST Octets, Leading Zeros)",
            "hint": "Remember to validate BOTH SRC and DST IPv4 addresses, reject leading zeros ('00'/'01'), and allow '0.0.0.0' and '255.255.255.255'.",
            "args": (ipv4_logs,),
            "expected": {"0.0.0.0": 42},
        }
    )

    # 2. Port, Timestamp, Action & Duplicate/Missing Key Validation
    field_logs = [
        "1700000001 SRC=10.0.0.1 DST=10.0.0.2 PORT=0 ACTION=DROP BYTES=100",         # port 0 invalid
        "1700000001 SRC=10.0.0.1 DST=10.0.0.2 PORT=65536 ACTION=DROP BYTES=100",     # port 65536 invalid
        "1700000001 SRC=10.0.0.1 DST=10.0.0.2 PORT=80 ACTION=REJECT BYTES=100",      # invalid ACTION
        "1700000001 SRC=10.0.0.1 DST=10.0.0.2 PORT=80 ACTION=DROP BYTES=-1",         # negative bytes
        "-5 SRC=10.0.0.1 DST=10.0.0.2 PORT=80 ACTION=DROP BYTES=100",                # negative timestamp
        "abc SRC=10.0.0.1 DST=10.0.0.2 PORT=80 ACTION=DROP BYTES=100",               # non-int timestamp
        "1700000001 SRC=10.0.0.1 SRC=10.0.0.1 PORT=80 ACTION=DROP BYTES=100",        # duplicate SRC / missing DST
        "1700000001 SRC=10.0.0.1 DST=10.0.0.2 PORT=80 ACTION=DROP BYTES=100 EXTRA=1",  # unexpected extra field
        "   0 BYTES=0 ACTION=DROP PORT=65535 DST=10.0.0.2 SRC=10.0.0.99   ",         # valid boundary: ts=0, port=65535, bytes=0, shuffled keys!
    ]
    tests.append(
        {
            "category": "Field Order, Duplicate Keys, Port & Boundary Checks",
            "hint": "Check port bounds (1..65535), non-negative timestamp & bytes (0 is valid!), exact 5 required keys with no duplicates or extra fields.",
            "args": (field_logs,),
            "expected": {"10.0.0.99": 0},
        }
    )

    # 3. Mixed Valid & Corrupted Stream (10,000 lines)
    rng = random.Random(22)
    mixed_stream: list[str] = []
    for i in range(10_000):
        if i % 5 == 0:
            mixed_stream.append(f"{1700000000 + i} SRC=10.01.{i % 20}.1 DST=10.0.0.1 PORT=443 ACTION=DROP BYTES=500")
        elif i % 7 == 0:
            mixed_stream.append(f"{1700000000 + i} BYTES=250 PORT=443 ACTION=DROP DST=10.0.0.1 SRC=172.16.{i % 10}.{i % 30}")
        else:
            action = "DROP" if i % 3 != 0 else "ALLOW"
            mixed_stream.append(
                f"{1700000000 + i} SRC=192.168.{i % 15}.{i % 40} DST=10.0.0.1 PORT=443 ACTION={action} BYTES={rng.randint(64, 1500)}"
            )
    tests.append(
        {
            "category": "Mixed Corrupted & Shuffled Telemetry (10,000 Lines)",
            "hint": "Ensure your parser handles shuffled keys and malformed lines efficiently in O(N) time.",
            "args": (mixed_stream,),
            "expected": ref.count_valid_dropped_bytes(mixed_stream),
            "timeout_sec": 1.5,
        }
    )

    return tests


def _build_part3_hidden_tests() -> list[dict]:
    tests: list[dict] = []

    # 1. Edge Case: k <= 0 and empty logs
    tests.append(
        {
            "category": "Edge Case: k = 0 & Negative k",
            "hint": "When k <= 0, return an empty list [] immediately.",
            "args": (
                ["1700000001 SRC=10.0.0.1 DST=10.0.0.2 PORT=80 ACTION=DROP BYTES=500"],
                0,
            ),
            "expected": [],
        }
    )

    # 2. Multi-Way Lexicographical Tie-Breaking & Exact K Slice
    tie_logs = [
        "1700000001 SRC=10.0.0.10 DST=1.1.1.1 PORT=443 ACTION=DROP BYTES=500",
        "1700000002 SRC=10.0.0.2 DST=1.1.1.1 PORT=443 ACTION=DROP BYTES=500",
        "1700000003 SRC=10.0.0.1 DST=1.1.1.1 PORT=443 ACTION=DROP BYTES=300",
        "1700000004 SRC=10.0.0.1 DST=1.1.1.1 PORT=443 ACTION=DROP BYTES=200",
        "1700000005 SRC=10.0.0.20 DST=1.1.1.1 PORT=443 ACTION=DROP BYTES=900",
        "1700000006 SRC=999.0.0.1 DST=1.1.1.1 PORT=443 ACTION=DROP BYTES=99999",  # invalid!
    ]
    tests.append(
        {
            "category": "Multi-Way Tie-Breaking & Invalid Line Filtering",
            "hint": "Sort by total_bytes descending, then src_ip ascending lexicographically: key=lambda x: (-x[1], x[0]).",
            "args": (tie_logs, 3),
            "expected": [
                ("10.0.0.20", 900),
                ("10.0.0.1", 500),
                ("10.0.0.10", 500),
            ],
        }
    )

    # 3. High-Scale Performance Stress Test (50,000 log lines, 2,000 unique IPs, k = 15)
    rng = random.Random(42)
    stress_logs: list[str] = []
    for i in range(50_000):
        b = i % 50
        c = i % 40
        action = "DROP" if (i % 3 != 0) else "ALLOW"
        byte_cnt = rng.randint(64, 1500)
        if i % 25 == 0:
            stress_logs.append(f"{1700000000 + i} SRC=172.16.{b}.999 DST=10.0.0.1 PORT=443 ACTION=DROP BYTES=9999")
        else:
            stress_logs.append(
                f"{1700000000 + i} SRC=172.16.{b}.{c} DST=10.0.0.1 PORT=443 ACTION={action} BYTES={byte_cnt}"
            )
    expected_stress = ref.top_dropped_sources(stress_logs, 15)
    tests.append(
        {
            "category": "High-Scale Performance Stress Test (50,000 Log Lines)",
            "hint": "Aggregate in a single O(N) pass, then extract top-k in O(U log K) using heapq.nsmallest (or O(U log U) sort).",
            "args": (stress_logs, 15),
            "expected": expected_stress,
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
