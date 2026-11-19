"""
Public Sample Test Cases (Visible to Candidate)
You can inspect these test cases or add your own custom test cases!
"""

PART1_SAMPLE_TESTS = [
    {
        "name": "Sample 1: Basic Filtering & Summation",
        "args": (
            [
                "1700000001 SRC=192.168.1.10 DST=10.0.0.5 PORT=443 ACTION=DROP BYTES=1200",
                "1700000002 SRC=192.168.1.20 DST=10.0.0.5 PORT=80 ACTION=ALLOW BYTES=5000",
                "1700000003 SRC=192.168.1.10 DST=10.0.0.6 PORT=22 ACTION=DROP BYTES=800",
                "1700000004 SRC=172.16.0.5 DST=10.0.0.5 PORT=443 ACTION=DROP BYTES=2000",
            ],
        ),
        "expected": {
            "192.168.1.10": 2000,
            "172.16.0.5": 2000,
        },
    },
    {
        "name": "Sample 2: Only ALLOW Traffic Returns Empty Dict",
        "args": (
            [
                "1700000001 SRC=1.1.1.1 DST=2.2.2.2 PORT=53 ACTION=ALLOW BYTES=400",
                "1700000002 SRC=8.8.8.8 DST=2.2.2.2 PORT=53 ACTION=ALLOW BYTES=900",
            ],
        ),
        "expected": {},
    },
    {
        "name": "Sample 3: Zero-Byte DROP Event Included",
        "args": (
            [
                "1700000001 SRC=10.0.0.9 DST=10.0.0.1 PORT=22 ACTION=DROP BYTES=0",
                "1700000002 SRC=10.0.0.8 DST=10.0.0.1 PORT=443 ACTION=DROP BYTES=64",
            ],
        ),
        "expected": {
            "10.0.0.9": 0,
            "10.0.0.8": 64,
        },
    },
]

PART2_SAMPLE_TESTS = [
    {
        "name": "Sample 1: Out-of-Order Keys & Invalid IPv4 Ignored",
        "args": (
            [
                "1700000010 ACTION=DROP BYTES=500 SRC=10.1.1.1 DST=10.0.0.1 PORT=8080",
                "1700000011 SRC=999.168.1.1 DST=10.0.0.1 PORT=443 ACTION=DROP BYTES=9999",
                "1700000012 SRC=10.01.1.1 DST=10.0.0.1 PORT=80 ACTION=DROP BYTES=1000",
                "1700000013 SRC=10.1.1.3 DST=10.0.0.1 PORT=22 ACTION=DROP BYTES=300",
                "corrupted_line_without_fields",
            ],
        ),
        "expected": {
            "10.1.1.1": 500,
            "10.1.1.3": 300,
        },
    },
    {
        "name": "Sample 2: Invalid Port, Action & Negative Bytes Ignored",
        "args": (
            [
                "1700000001 SRC=192.168.1.1 DST=10.0.0.1 PORT=70000 ACTION=DROP BYTES=100",
                "1700000002 SRC=192.168.1.2 DST=10.0.0.1 PORT=0 ACTION=DROP BYTES=100",
                "1700000003 SRC=192.168.1.3 DST=10.0.0.1 PORT=443 ACTION=REJECT BYTES=100",
                "1700000004 SRC=192.168.1.4 DST=10.0.0.1 PORT=443 ACTION=DROP BYTES=-50",
                "1700000005 SRC=192.168.1.5 DST=10.0.0.1 PORT=443 ACTION=DROP BYTES=450",
            ],
        ),
        "expected": {
            "192.168.1.5": 450,
        },
    },
]

PART3_SAMPLE_TESTS = [
    {
        "name": "Sample 1: Top-K Ranking & Lexicographical Tie-Breaking",
        "args": (
            [
                "1700000001 SRC=192.168.1.10 DST=10.0.0.5 PORT=443 ACTION=DROP BYTES=1200",
                "1700000002 SRC=192.168.1.20 DST=10.0.0.5 PORT=80 ACTION=ALLOW BYTES=5000",
                "1700000003 SRC=192.168.1.10 DST=10.0.0.6 PORT=22 ACTION=DROP BYTES=800",
                "1700000004 SRC=172.16.0.5 DST=10.0.0.5 PORT=443 ACTION=DROP BYTES=2000",
                "1700000005 SRC=999.168.1.1 DST=10.0.0.5 PORT=443 ACTION=DROP BYTES=9999",
                "1700000006 SRC=10.0.0.99 DST=10.0.0.5 PORT=443 ACTION=DROP BYTES=500",
            ],
            2,
        ),
        "expected": [("172.16.0.5", 2000), ("192.168.1.10", 2000)],
    },
    {
        "name": "Sample 2: k Larger Than Unique IPs & k = 0",
        "args": (
            [
                "1700000001 SRC=10.0.0.10 DST=1.1.1.1 PORT=443 ACTION=DROP BYTES=500",
                "1700000002 SRC=10.0.0.2 DST=1.1.1.1 PORT=443 ACTION=DROP BYTES=500",
            ],
            5,
        ),
        "expected": [("10.0.0.10", 500), ("10.0.0.2", 500)],
    },
]
