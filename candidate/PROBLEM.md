# Azure Virtual Network (VNet) Flow Log Analyzer

**Role Track:** Microsoft Azure Networking — Network Engineering Intern  
**Environment:** Python 3  
**Run Sample Tests:** `python3 run_tests.py --part 1`  
**Submit Solution (Includes Hidden Tests):** `python3 run_tests.py --part 1 --submit`

---

## Background

In Microsoft Azure, **Network Security Groups (NSGs)** filter network traffic to and from resources inside an Azure Virtual Network (VNet). Every packet attempt generates a flow log entry. During an incident, network engineering tools analyze these logs to measure how much traffic is being dropped per source IP address.

---

## Part 1: Basic Drop Filtering & Byte Aggregation

Implement the function:

```python
def count_dropped_bytes(logs: list[str]) -> dict[str, int]:
```

### Log Format

Each element in `logs` is a single-line string representing a network flow record.

In **Part 1**, you may assume **every log line is valid and well-formed**, with fields always appearing in this exact space-separated order:

```text
<timestamp> SRC=<src_ip> DST=<dst_ip> PORT=<dst_port> ACTION=<ALLOW|DROP> BYTES=<byte_count>
```

Example:
```text
1700000001 SRC=192.168.1.10 DST=10.0.0.5 PORT=443 ACTION=DROP BYTES=1500
```

### Task

1. Filter for log lines where `ACTION=DROP`.
2. Sum the total `BYTES` dropped for each unique `<src_ip>`.
3. Return a dictionary mapping each `<src_ip>` (string) to its `total_dropped_bytes` (integer).
   - Source IPs that **only** have `ACTION=ALLOW` lines must **not** appear in the returned dictionary.
   - If a source IP has a `DROP` event with `BYTES=0`, include it in the dictionary with value `0`.
   - If `logs` is empty or contains no `DROP` lines, return `{}`.

---

### Example 1

**Input:**
```python
logs = [
    "1700000001 SRC=192.168.1.10 DST=10.0.0.5 PORT=443 ACTION=DROP BYTES=1200",
    "1700000002 SRC=192.168.1.20 DST=10.0.0.5 PORT=80 ACTION=ALLOW BYTES=5000",
    "1700000003 SRC=192.168.1.10 DST=10.0.0.6 PORT=22 ACTION=DROP BYTES=800",
    "1700000004 SRC=172.16.0.5 DST=10.0.0.5 PORT=443 ACTION=DROP BYTES=2000",
]
```

**Output:**
```python
{
    "192.168.1.10": 2000,
    "172.16.0.5": 2000,
}
```

**Explanation:**
- `"192.168.1.10"` has two `DROP` events: `1200 + 800 = 2000` bytes.
- `"192.168.1.20"` only has an `ALLOW` event, so it is excluded.
- `"172.16.0.5"` has one `DROP` event: `2000` bytes.

---

### Constraints (Part 1)
- `0 <= len(logs) <= 10,000`
- All log lines in Part 1 are guaranteed to follow the exact valid format above.
- Expected Time Complexity: $\mathcal{O}(N)$, where $N$ is the number of log lines.

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
