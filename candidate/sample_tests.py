"""
Public Sample Test Cases (Visible to Candidate)
You can inspect these test cases or add your own custom test cases at the bottom!
"""

PART1_SAMPLE_TESTS = [
    {
        "name": "Sample 1: Basic Aggregation & Tie-Breaking",
        "args": (
            [
                "1700000001 SRC=192.168.1.10 DST=10.0.0.5 PORT=443 ACTION=DROP BYTES=1200",
                "1700000002 SRC=192.168.1.20 DST=10.0.0.5 PORT=80 ACTION=ALLOW BYTES=5000",
                "1700000003 SRC=192.168.1.10 DST=10.0.0.6 PORT=22 ACTION=DROP BYTES=800",
                "1700000004 SRC=172.16.0.5 DST=10.0.0.5 PORT=443 ACTION=DROP BYTES=2000",
                "1700000005 SRC=999.168.1.1 DST=10.0.0.5 PORT=443 ACTION=DROP BYTES=9999",
            ],
            2,
        ),
        "expected": [("172.16.0.5", 2000), ("192.168.1.10", 2000)],
    },
    {
        "name": "Sample 2: Malformed Logs & Out-of-Order Keys",
        "args": (
            [
                "1700000010 ACTION=DROP BYTES=500 SRC=10.1.1.1 DST=10.0.0.1 PORT=8080",
                "1700000011 SRC=10.01.1.1 DST=10.0.0.1 PORT=80 ACTION=DROP BYTES=1000",  # leading zero in IP
                "1700000012 SRC=10.1.1.2 DST=10.0.0.1 PORT=70000 ACTION=DROP BYTES=1000",  # invalid port > 65535
                "1700000013 SRC=10.1.1.3 DST=10.0.0.1 PORT=22 ACTION=DROP BYTES=300",
                "corrupted_line_without_fields",
            ],
            5,
        ),
        "expected": [("10.1.1.1", 500), ("10.1.1.3", 300)],
    },
    {
        "name": "Sample 3: Only ALLOW Traffic Returns Empty List",
        "args": (
            [
                "1700000001 SRC=1.1.1.1 DST=2.2.2.2 PORT=53 ACTION=ALLOW BYTES=400",
                "1700000002 SRC=8.8.8.8 DST=2.2.2.2 PORT=53 ACTION=ALLOW BYTES=900",
            ],
            3,
        ),
        "expected": [],
    },
]

PART2_SAMPLE_TESTS = [
    {
        "name": "Sample 1: Longest Prefix Match Routing Table",
        "fn": "match_longest_prefix",
        "args": (
            "10.1.2.45",
            [
                ("0.0.0.0/0", "INTERNET"),
                ("10.0.0.0/8", "CORP_VNET"),
                ("10.1.0.0/16", "EAST_US_VNET"),
                ("10.1.2.0/24", "PROD_SUBNET"),
                ("10.1.3.0/24", "DEV_SUBNET"),
            ],
        ),
        "expected": "PROD_SUBNET",
    },
    {
        "name": "Sample 2: /32 Host Route vs /0 Default Route",
        "fn": "match_longest_prefix",
        "args": (
            "192.168.50.10",
            [
                ("0.0.0.0/0", "DEFAULT_GW"),
                ("192.168.50.0/24", "LAN_SUBNET"),
                ("192.168.50.10/32", "JUMP_BOX_HOST"),
            ],
        ),
        "expected": "JUMP_BOX_HOST",
    },
    {
        "name": "Sample 3: Filtered Top Dropped Sources (Excluding INTERNAL)",
        "fn": "top_dropped_external_sources",
        "args": (
            [
                "1700000001 SRC=10.1.2.50 DST=10.0.0.5 PORT=443 ACTION=DROP BYTES=9000",   # matches 10.1.2.0/24 -> EXTERNAL_DMZ (kept!)
                "1700000002 SRC=10.1.99.10 DST=10.0.0.5 PORT=443 ACTION=DROP BYTES=8000",  # matches 10.0.0.0/8 -> INTERNAL (excluded!)
                "1700000003 SRC=203.0.113.5 DST=10.0.0.5 PORT=22 ACTION=DROP BYTES=4500",  # matches 0.0.0.0/0 -> INTERNET (kept!)
            ],
            2,
            [
                ("0.0.0.0/0", "INTERNET"),
                ("10.0.0.0/8", "INTERNAL"),
                ("10.1.2.0/24", "EXTERNAL_DMZ"),
            ],
        ),
        "expected": [("10.1.2.50", 9000), ("203.0.113.5", 4500)],
    },
]

PART3_SAMPLE_TESTS = [
    {
        "name": "Sample 1: Rolling 10-Second Window Burst Detection",
        "args": (
            [
                "1700000001 SRC=203.0.113.9 DST=10.0.0.5 PORT=22 ACTION=DROP BYTES=64",
                "1700000005 SRC=203.0.113.9 DST=10.0.0.5 PORT=22 ACTION=DROP BYTES=64",
                "1700000011 SRC=203.0.113.9 DST=10.0.0.5 PORT=22 ACTION=DROP BYTES=64",  # [1..11] inclusive is 10s span (1700000011 - 1700000001 == 10) -> 3 drops!
                "1700000002 SRC=198.51.100.4 DST=10.0.0.5 PORT=80 ACTION=DROP BYTES=64",
                "1700000008 SRC=198.51.100.4 DST=10.0.0.5 PORT=80 ACTION=DROP BYTES=64",
                "1700000020 SRC=198.51.100.4 DST=10.0.0.5 PORT=80 ACTION=DROP BYTES=64",  # spread too far apart
            ],
            10,
            3,
        ),
        "expected": ["203.0.113.9"],
    },
    {
        "name": "Sample 2: Out-of-Order Logs & ALLOW Ignored",
        "args": (
            [
                "1700000108 SRC=192.0.2.55 DST=10.0.0.1 PORT=443 ACTION=DROP BYTES=100",
                "1700000100 SRC=192.0.2.55 DST=10.0.0.1 PORT=443 ACTION=DROP BYTES=100",
                "1700000104 SRC=192.0.2.55 DST=10.0.0.1 PORT=443 ACTION=ALLOW BYTES=100",
                "1700000105 SRC=192.0.2.55 DST=10.0.0.1 PORT=443 ACTION=DROP BYTES=100",
            ],
            10,
            3,
        ),
        "expected": ["192.0.2.55"],
    },
]
