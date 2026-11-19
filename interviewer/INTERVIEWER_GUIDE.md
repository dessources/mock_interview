# Microsoft Network Engineering Intern — Interviewer Playbook

Welcome! Since you already landed a top-tier Data Engineering internship, you know how high-bar technical assessments feel from the candidate side. This guide gives you everything you need to run a realistic, high-signal mock interview for your friend targeting **Microsoft (Azure Networking / Network Engineering Intern)**.

---

## 1. What Microsoft Tests in Network Engineering Intern Interviews

### Phase A: The HackerRank / Codility Online Assessment (75–90 mins)
Microsoft's automated OA for Network Engineering / Cloud Infrastructure interns usually consists of **2 medium-difficulty coding questions** that blend **core DSA** with **networking/systems context**:
1. **Telemetry & Log Aggregation (Strings + Hash Maps + Heaps):**
   - Parsing firewall/NSG flow logs, syslog streams, or packet headers, filtering malformed records, and computing top-$K$ talkers or error rates.
2. **IPv4 / CIDR Bitwise Math & Routing Lookups (Bit Manipulation + Sorting/Tries):**
   - Converting dotted-quad IPs (`192.168.1.1`) into 32-bit unsigned integers, applying subnet masks (`/24`, `/12`, `/0`), and implementing **Longest Prefix Match (LPM)** across routing tables.
3. **Sliding-Window Rate Limiting / Anomaly Detection (Two Pointers / Queues):**
   - Counting bursts of dropped packets or SYN floods within a rolling $W$-second window.
4. **Network Topology Graphs (BFS / DFS / Dijkstra / Indegree):**
   - Questions like *Maximal Network Rank* (a classic Microsoft OA question), finding shortest paths with link latencies, or detecting disconnected components when a router fails.

### Phase B: Live Technical Loop (3 × 45-min interviews)
After passing the OA, Microsoft interviewers take a working solution and **layer follow-up constraints** (scale, memory, CIDR edge cases) followed by **10 minutes of practical networking troubleshooting** (TCP vs. UDP, DNS, traceroute/MTU, BGP/Subnetting).

> **How our mock problem bridges both:**
> By starting him on **Part 1** in a HackerRank-style test runner and unlocking **Part 2 (CIDR LPM)** and **Part 3 (Sliding Window)** as he passes each stage, he practices both the **automated HackerRank pressure** (passing hidden edge-case & TLE tests) and the **live Microsoft follow-up progression**.

---

## 2. Pre-Interview Setup Checklist (VS Code Window Sharing)

1. **Open two separate VS Code windows:**
   - **Window 1 (Shared with your friend):** Open the folder `/home/pianodessources/misc/mock_interview/candidate` directly (`code /home/pianodessources/misc/mock_interview/candidate`).
     - Verify the Explorer sidebar **only** shows `PROBLEM.md`, `run_tests.py`, `sample_tests.py`, and `solution.py`.
   - **Window 2 (Private on your monitor):** Keep `/home/pianodessources/misc/mock_interview/interviewer` open here with `INTERVIEWER_GUIDE.md` and `reference_solutions.py`.
2. **Reset the candidate workspace before starting:**
   ```bash
   python3 interviewer/unlock_part.py reset
   ```
3. **Show him the terminal commands in `candidate/`:**
   - Run sample tests (unlimited, shows full diffs):
     ```bash
     python3 run_tests.py --part 1
     ```
   - Submit code (runs hidden edge cases + 40,000-line stress test):
     ```bash
     python3 run_tests.py --part 1 --submit
     ```

---

## 3. Concrete Tips to Play the Interviewer Role Like a Pro

As a friend, the biggest temptation is to jump in immediately when he makes a typo or give away the algorithm too early. Here is how to run the room like an actual Microsoft engineer:

### Tip 1: Enforce the "Clarify & Plan Before Typing" Rule (First 3 Minutes)
- If he reads `PROBLEM.md` and immediately starts typing `for line in logs:`, gently stop him:
  > *"Before you jump into code, walk me through your plan and what edge cases you notice in the log format."*
- Check if he spots that `KEY=VALUE` fields can be **out of order** after the timestamp, and that leading zeros like `10.01.0.1` are invalid.

### Tip 2: Use the "Silent 90-Second Rule" When He Hits a Bug
- When a test fails or he writes a subtle bug, **wait 60–90 seconds** before speaking. In real interviews, candidates are evaluated on how they debug using test output and print statements.
- If he is still stuck after 90 seconds, use the **Tiered Hint Ladder** below (Level 1 = question, Level 2 = conceptual nudge, Level 3 = concrete fix).

### Tip 3: Watch How He Uses `--submit` vs. Sample Tests
- On HackerRank, many candidates pass the 3 public sample tests and assume they're done, only to score `3/10` because of hidden edge cases.
- Before he runs `--submit`, ask:
  > *"Before we hit submit, is there any custom test case you'd want to mentally trace or add to `sample_tests.py`?"*

### Tip 4: Ask "What Changes at 100 Million Lines?" (Your Data Engineering Superpower!)
- Draw on your Data Engineering background! Once his code passes, ask him:
  - *"Right now you're sorting all unique IPs (`O(U log U)`). What if `U = 5,000,000` and `k = 10`?"* (Push him toward `heapq.nsmallest` / min-heap of size $K$).
  - *"In Part 2, you're checking 500 CIDR rules for every log line (`30,000 * 500`). How can we avoid repeating CIDR lookups for the same IP?"* (Aggregate by IP first, or memoize/use a Bitwise Trie!).

### Tip 5: Keep a Live Timestamped Scorecard
- Jot down exact quotes or moments (e.g., *"14:00 — Caught the `/0` bitshift edge case on his own"* or *"28:00 — Tried string `.startswith()` for CIDR matching before switching to bitwise ints"*). Specific feedback after the interview is 10x more helpful than *"You did great!"*

---

## 4. Minute-by-Minute Timeline (60-Minute Session)

| Time | Phase | Your Action |
| :--- | :--- | :--- |
| **00:00 – 03:00** | **Intro & Setup** | Set the stage: *"We have 45–50 minutes of coding across a multi-part Azure Networking problem, plus 10 minutes for quick networking questions and feedback."* |
| **03:00 – 20:00** | **Part 1: Log Parsing & Top-K** | Let him read `PROBLEM.md`, explain his approach, code `top_dropped_sources`, run `--part 1`, and pass `--part 1 --submit`. |
| **20:00 – 38:00** | **Part 2: CIDR Longest Prefix Match** | Run `python3 interviewer/unlock_part.py 2` from your terminal. Have him implement `match_longest_prefix` and `top_dropped_external_sources`. |
| **38:00 – 50:00** | **Part 3: Sliding-Window Burst** | Run `python3 interviewer/unlock_part.py 3`. Have him implement `detect_burst_sources` using Two Pointers. |
| **50:00 – 55:00** | **Verbal Networking Q&A** | Ask 2–3 quick Azure / Networking fundamentals questions from Section 6 below. |
| **55:00 – 60:00** | **Debrief & Code Review** | Walk through his scorecard and show him any cool optimizations from `interviewer/reference_solutions.py`. |

---

## 5. Part-by-Part Bug Spotting & Tiered Hint Ladder

### Part 1: `top_dropped_sources(logs, k)`

#### Common Candidate Bugs to Watch For:
1. **Assuming Fixed Field Order:** Splitting by space and indexing `tokens[1]` as `SRC=` directly. (Sample Test 2 and Hidden Test 2 put `ACTION=DROP` first!)
2. **Weak IPv4 Validation:**
   - Using `int(octet)` without checking for leading zeros (`int("01") == 1`, which passes unless you check `len(p) > 1 and p[0] == "0"` or `str(int(p)) == p`).
   - Forgetting to validate `DST` IP as well as `SRC` IP.
   - Allowing `PORT=0` or `PORT=65536` (valid TCP/UDP ports here are `1..65535`).
3. **Sorting Tie-Breaker Bug:**
   - Using ` sorted(..., reverse=True)` on `(bytes, ip)` which sorts `ip` **descending** on ties instead of ascending!
   - **Fix:** Sort with `key=lambda item: (-item[1], item[0])`.

#### Tiered Hints for Part 1:
- **Level 1 (Subtle):** *"Take a look at Validation Rule #6 and Sample 2—are the `KEY=VALUE` tokens guaranteed to be in the same position every time?"*
- **Level 2 (Conceptual):** *"In Python, how can you sort by one value descending (`total_bytes`) and a second value ascending (`src_ip`) in a single tuple key?"*
- **Level 3 (Direct):** *"Use `key=lambda x: (-x[1], x[0])`—negating the integer flips it to descending while keeping the IP string ascending."*

---

### Part 2: `match_longest_prefix` & `top_dropped_external_sources`

#### Common Candidate Bugs to Watch For:
1. **The String Prefix Trap:** Trying to match CIDR blocks by comparing strings (e.g., checking if `"10.1.2.45"` starts with `"10.1."`). This completely breaks on non-octet boundaries like `/12` or `/27` (Hidden Test 5)!
2. **The `/0` Bit-Shift Trap:**
   - Writing `mask = (0xFFFFFFFF << (32 - prefix_len)) & 0xFFFFFFFF` Works in Python if masked, EXCEPT if someone writes `~((1 << (32 - prefix_len)) - 1)` or forgets to handle `prefix_len == 0` carefully. Always verify `0.0.0.0/0` gives `mask = 0`.
3. **Time Limit Exceeded (TLE) on Hidden Test 7 (30,000 logs × 500 CIDR rules):**
   - If the candidate calls `match_longest_prefix(src_ip, cidr_rules)` inside the 30,000-line loop AND re-parses the 500 CIDR strings every single time, that's $15,000,000$ string parses $\rightarrow$ **TLE (> 1.5s)**!
   - **Easy Fix #1:** Aggregate dropped bytes per unique `src_ip` first (there are far fewer unique IPs than log lines!), then call LPM once per unique IP.
   - **Easy Fix #2 (Bonus Points):** Pre-parse `cidr_rules` into `(net_int, mask, prefix_len, tag)` tuples once, or build a 32-bit binary Trie (`O(32)` lookup per IP).
   - *(Note: Python's built-in `ipaddress` module is also slow if instantiated $15,000,000$ times; bitwise integer math is ~50x faster!)*

#### Tiered Hints for Part 2:
- **Level 1 (Subtle):** *"How is an IPv4 address represented at the packet header level? How can we convert `'192.168.1.1'` into a single 32-bit number?"*
- **Level 2 (Conceptual):** *"Once you have a 32-bit integer `(a << 24) | (b << 16) | (c << 8) | d`, a `/prefix` mask just keeps the top `prefix` bits. What bitwise operator checks if two IPs share the top `prefix` bits?"*
- **Level 3 (Performance Hint if TLE):** *"Notice you're running the CIDR lookup on every single log line before grouping by IP. What if the same IP appears 1,000 times in the log?"*

---

### Part 3: `detect_burst_sources(logs, window_sec, threshold)`

#### Common Candidate Bugs to Watch For:
1. **Assuming Logs Are Chronological:** Logs can arrive out of order (Sample 2 & Hidden Test 6). Timestamps per IP must be sorted first.
2. **Off-by-One on Inclusive Window:** A window `[t, t + window_sec]` of `10` seconds starting at `t = 1` includes `t = 11` (`11 - 1 <= 10`). Using `< window_sec` instead of `<= window_sec` fails Sample 1 and Hidden Test 5.
3. **$\mathcal{O}(N^2)$ Nested Loop (TLE on Hidden Test 7):**
   - Checking every pair `(i, j)` of timestamps for an IP with 35,000 drops takes $\approx 6 \times 10^8$ operations and triggers a timeout.
   - **Fix:** Two Pointers (`left = 0`, advance `right`, and `while ts[right] - ts[left] > window_sec: left += 1`). Or even simpler: since `threshold` is fixed, after sorting `ts`, check if `ts[i + threshold - 1] - ts[i] <= window_sec`!

#### Tiered Hints for Part 3:
- **Level 1 (Subtle):** *"Are the log timestamps guaranteed to be sorted? And if `window_sec = 10` starting at `t = 1`, is `t = 11` inside or outside the window?"*
- **Level 2 (Conceptual):** *"Once an IP's drop timestamps are sorted, how can you find if `threshold` events fit inside `window_sec` in a single linear scan without nested loops?"*
- **Level 3 (Direct):** *"Maintain a `left` pointer (or check `timestamps[i + threshold - 1] - timestamps[i] <= window_sec` directly!)."*

---

## 6. Bonus: 5 Verbal Azure Networking Questions (Final 10 Minutes)

Ask 2 or 3 of these after the coding finishes to simulate the live Microsoft Network Engineering interview loop:

1. **Question:** *"In Part 2 we implemented Longest Prefix Match. Suppose a router has three routes: `10.0.0.0/8` via Next-Hop A, `10.1.0.0/16` via Next-Hop B, and `0.0.0.0/0` via Next-Hop C. If a packet arrives for `10.1.5.9`, which Next-Hop does it take—even if Next-Hop A has a lower administrative distance or OSPF cost?"*
   - **Expected Answer:** Always **Next-Hop B (`10.1.0.0/16`)**. Routers evaluate **Longest Prefix Match first** before comparing administrative distance or routing protocol metric. Metrics/AD only break ties between routes with the **exact same prefix length**.

2. **Question:** *"Why do network flow collectors (like Azure NSG Flow Logs, NetFlow, or sFlow) typically send telemetry over UDP rather than TCP?"*
   - **Expected Answer:** Lower overhead, no connection state on routers/switches, and no head-of-line blocking or retransmission storms during network congestion (when telemetry spikes most, you don't want retransmitting logs to congest the control plane).

3. **Question:** *"A VM in Azure Subnet A (`10.0.1.10/24`) cannot reach a database VM in Subnet B (`10.0.2.20/24`) on port 5432. How do you systematically isolate where the drop is happening?"*
   - **Expected Answer:** Layer-by-layer (OSI/TCP-IP):
     1. Check local guest OS firewall & route table on VM A.
     2. Check **Azure NSG** outbound rules on Subnet A / NIC A and inbound rules on Subnet B / NIC B.
     3. Check **User-Defined Routes (UDRs)** / Virtual Network peering status.
     4. Test TCP handshake (`tcping` / `nc -zv 10.0.2.20 5432`) and check if the DB service is listening (`ss -tlnp` on `0.0.0.0` vs `127.0.0.1`).

4. **Question:** *"What is the difference between a `/30`, `/31`, and `/32` subnet in IPv4?"*
   - **Expected Answer:**
     - `/32` = 1 IP (host route / loopback).
     - `/31` = 2 IPs (RFC 3021 point-to-point link with no network/broadcast waste).
     - `/30` = 4 IPs total (2 usable host IPs + 1 network address + 1 broadcast address, traditional point-to-point link).

---

## 7. Post-Interview Feedback Scorecard

| Competency | 1 (Needs Work) | 2 (Solid / Intern Ready) | 3 (Strong Hire) | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Problem Clarification** | Jumped straight into coding without reading validation rules. | Asked good clarifying questions; noticed key edge cases. | Proactively identified out-of-order keys, tie-breakers, and scale limits. | |
| **Coding & Python Fluency** | Struggled with string parsing or dictionary syntax. | Clean `defaultdict`/`Counter` and sorting with custom keys. | Modular helper functions (`parse_log_line`, `ipv4_to_int`), idiomatic & readable. | |
| **Networking & Bitwise Logic** | Used string matching for CIDR; unfamiliar with bitmasks. | Converted IP to 32-bit int and applied bitmask with minor hints. | Handled `/0` through `/32` cleanly using bitwise operations & LPM precedence. | |
| **Algorithmic Efficiency** | Left $O(N^2)$ loops that timed out on stress tests. | Optimized to $O(N \log N)$ when prompted by TLE. | Anticipated time complexity up front (heaps, memoized LPM / Trie, two pointers). | |
| **Debugging & Testing** | Guessed randomly when tests failed. | Read test diffs carefully and traced logic step-by-step. | Tested boundary conditions mentally before hitting `--submit`. | |
