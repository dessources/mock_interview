# Azure Virtual Network (VNet) Flow Log Analyzer

**Role Track:** Microsoft Azure Networking — Network Engineering Intern  
**Environment:** Python 3  
**Run Sample Tests:** `python3 run_tests.py --part 1`  
**Submit Solution (Includes Hidden & Stress Tests):** `python3 run_tests.py --part 1 --submit`

---

## Background

In Microsoft Azure, **Network Security Groups (NSGs)** filter network traffic to and from Azure resources in an Azure Virtual Network (VNet). Every packet attempt generates a flow log entry. During an incident, network engineering tools must rapidly parse millions of raw flow log entries to identify top offending source IP addresses whose traffic is being dropped.

---

## Part 1: Top Offending Source IPs by Dropped Bytes

Implement the function:

```python
def top_dropped_sources(logs: list[str], k: int) -> list[tuple[str, int]]:
```

### Log Format

Each element in `logs` is a single-line string representing a network flow record. A **valid** log line contains space-separated `KEY=VALUE` fields (after an integer Unix epoch timestamp) in the exact format below:

```text
<timestamp> SRC=<src_ip> DST=<dst_ip> PORT=<dst_port> ACTION=<ALLOW|DROP> BYTES=<byte_count>
```

Example of a valid log line:
```text
1700000001 SRC=192.168.1.10 DST=10.0.0.5 PORT=443 ACTION=DROP BYTES=1500
```

### Validation Rules

Real-world telemetry streams occasionally contain corrupted or incomplete lines. A log line is **valid** if and only if:
1. `<timestamp>` is a non-negative integer (`>= 0`).
2. `<src_ip>` and `<dst_ip>` are valid **IPv4 addresses** in dotted-quad decimal notation (`A.B.C.D`):
   - Must consist of exactly **4** dot-separated octets.
   - Each octet must consist only of digits, have **no leading zeros** (except `"0"` itself — e.g., `"01"` is invalid), and represent an integer in the inclusive range `0 <= octet <= 255`.
3. `<dst_port>` is an integer in the valid TCP/UDP port range `1 <= port <= 65535`.
4. `<ACTION>` is either `"ALLOW"` or `"DROP"`.
5. `<byte_count>` is a non-negative integer (`>= 0`).
6. Extra leading/trailing whitespace on the line is permitted, and the `KEY=VALUE` fields after `<timestamp>` may appear in **any order** (e.g., `ACTION=DROP` before `SRC=...`), provided all 5 required keys (`SRC`, `DST`, `PORT`, `ACTION`, `BYTES`) are present exactly once.

Any log line that violates these rules must be **silently ignored**.

### Task

1. Filter for valid log lines where `ACTION=DROP`.
2. Aggregate the **total `BYTES`** dropped for each unique `<src_ip>`.
3. Return the top `k` source IPs as a list of `(src_ip, total_dropped_bytes)` tuples:
   - Sorted by `total_dropped_bytes` in **descending** order.
   - If two source IPs have the exact same `total_dropped_bytes`, break ties by `src_ip` in **ascending lexicographical (ASCII)** order (e.g., `"10.0.0.2"` comes before `"10.0.0.10"`).
   - If `k <= 0` or no valid `DROP` records exist (or only `0`-byte drops exist? Note: include any IP that had at least one valid `ACTION=DROP` line, even if `BYTES=0`), return `[]` when `k <= 0`. If fewer than `k` unique source IPs have dropped traffic, return all of them.

---

### Example 1

**Input:**
```python
logs = [
    "1700000001 SRC=192.168.1.10 DST=10.0.0.5 PORT=443 ACTION=DROP BYTES=1200",
    "1700000002 SRC=192.168.1.20 DST=10.0.0.5 PORT=80 ACTION=ALLOW BYTES=5000",
    "1700000003 SRC=192.168.1.10 DST=10.0.0.6 PORT=22 ACTION=DROP BYTES=800",
    "1700000004 SRC=172.16.0.5 DST=10.0.0.5 PORT=443 ACTION=DROP BYTES=2000",
    "1700000005 SRC=999.168.1.1 DST=10.0.0.5 PORT=443 ACTION=DROP BYTES=9999",  # Invalid IP
]
k = 2
```

**Output:**
```python
[("172.16.0.5", 2000), ("192.168.1.10", 2000)]
```

**Explanation:**
- `"192.168.1.10"` has two valid `DROP` events: `1200 + 800 = 2000` bytes.
- `"192.168.1.20"` is `ACTION=ALLOW`, so it is ignored.
- `"172.16.0.5"` has one valid `DROP` event: `2000` bytes.
- `"999.168.1.1"` has an invalid octet (`999 > 255`), so the line is ignored.
- Both `"172.16.0.5"` and `"192.168.1.10"` have `2000` bytes. Breaking ties lexicographically, `"172.16.0.5" < "192.168.1.10"`.

---

### Constraints
- `0 <= len(logs) <= 100,000`
- `0 <= k <= 10,000`
- Expected Time Complexity: $\mathcal{O}(N + U \log K)$ or $\mathcal{O}(N + U \log U)$, where $N$ is the number of log lines and $U$ is the number of unique source IPs.

