# Microsoft Network Engineering Intern — Interviewer Playbook

Welcome! Since you already landed a top-tier Data Engineering internship, you know how high-bar technical assessments feel from the candidate side. This guide gives you everything you need to run a realistic, approachable, and high-signal mock interview for your friend targeting **Microsoft (Azure Networking / Network Engineering Intern)**.

---

## 1. What Microsoft Tests in Network Engineering Intern Interviews

### Phase A: The HackerRank / Codility Online Assessment (75–90 mins)
Microsoft's automated OA for Network Engineering / Cloud Infrastructure interns usually consists of **2 medium-difficulty coding questions** that blend **core DSA** with **networking/systems context**:
1. **Telemetry & Log Aggregation (Strings + Hash Maps + Heaps):**
   - Parsing firewall/NSG flow logs, syslog streams, or packet headers, filtering malformed records, and computing top-$K$ talkers or error rates.
2. **IPv4 / CIDR Validation & Subnet Math:**
   - Validating dotted-quad IPv4 strings (`0..255`, no leading zeros) and matching subnets.
3. **Sliding-Window Rate Limiting / Graph Connectivity:**
   - Counting bursts of dropped packets or finding network ranks / shortest paths.

### Phase B: Progressive Live Follow-Ups (How This Mock Is Structured)
Instead of dumping a huge spec on your friend all at once, this problem breaks the **Azure VNet Flow Log Analyzer** into **3 bite-sized, realistic stages** where each part builds directly on his previous code:
- **Part 1 (Basic Filtering & Totals — ~10 min):** Clean, well-formed logs in fixed order $\rightarrow$ filter `ACTION=DROP` and sum `BYTES` per source IP.
- **Part 2 (Production Validation — ~15–20 min):** Same problem, but now logs can have shuffled `KEY=VALUE` fields, malformed IPv4 addresses (`256.x`, leading zeros `01`), invalid ports (`0`, `70000`), negative numbers, or duplicate/missing keys.
- **Part 3 (Top-K Ranking & Scale Optimization — ~15–20 min):** Return only the Top `k` offenders with deterministic tie-breaking `(-bytes, src_ip)`, optimized for **50,000+ log lines** using a heap ($\mathcal{O}(N + U \log K)$) instead of sorting everything.

---

## 2. Pre-Interview Setup Checklist (VS Code Simple Browser)

1. **Start the Dual-Port UI Server** from your private terminal:
   ```bash
   python3 ui/server.py
   ```
2. **Interviewee Window (Share ONLY This Window):**
   - Open a fresh VS Code window, run `Ctrl+Shift+P` $\rightarrow$ **`Simple Browser: Show`**, and open `http://127.0.0.1:8765`.
   - Press `Ctrl+B` to hide the VS Code sidebar so the HackerRank IDE fills the window cleanly.
3. **Private Interviewer Window (Your Second Screen / Separate Window):**
   - Open `http://127.0.0.1:8766` (via VS Code Simple Browser or your regular browser) to control the timer, live-unlock Part 2 and Part 3, monitor his test runs/code, and read this playbook.

---

## 3. Concrete Tips to Play the Interviewer Role Like a Pro

### Tip 1: Let Part 1 Be a Quick Confidence Builder
- Part 1 is intentionally clean so he gets into a rhythm with the HackerRank UI (`Run Code` vs `Submit Code`).
- Still enforce the **"Clarify & Plan for 2 Minutes Before Coding"** habit:
  > *"Walk me through how you'll parse each line and what data structure you'll use before you start typing."*

### Tip 2: Use the "Silent 90-Second Rule" When He Hits a Bug
- When a test fails in Part 2 or Part 3, **stay quiet for 60–90 seconds**. Watch how he uses the diff output, `print()` statements, or the **Custom Input** tab to isolate the bug himself.
- If he's still stuck after 90 seconds, step down the **Tiered Hint Ladder** below one level at a time.

### Tip 3: Encourage Modularity Between Parts
- When you unlock Part 2, watch whether he writes a clean helper like `is_valid_ipv4(ip)` and `parse_log_line(line)` or tries to cram 25 `if` statements inside one giant loop.
- When you unlock Part 3, a strong candidate will simply call `count_valid_dropped_bytes(logs)` from Part 2 instead of copy-pasting the parser! Gently compliment or suggest code reuse if he starts copy-pasting.

### Tip 4: Push on Scale & Optimization (Your Data Engineering Superpower!)
- Once Part 3 passes with `sorted()`, ask him:
  > *"Right now `sorted()` takes $\mathcal{O}(U \log U)$ time. Suppose Azure has 5,000,000 unique source IPs in a 10-minute window and the dashboard only wants `k = 10`. Can we do better than sorting all 5 million IPs?"*
- Guide him toward a **min-heap of size $k$** (`heapq.nsmallest` in Python $\rightarrow \mathcal{O}(U \log K)$ time and $\mathcal{O}(K)$ extra heap space!).

### Tip 5: Give Specific, Timestamped Feedback
- Note concrete moments during the session (e.g., *"Caught the leading-zero IPv4 case before hitting Submit"*, *"Forgot `DST` IP validation on first try, then debugged cleanly"*).

---

## 4. Minute-by-Minute Timeline (55–60 Minutes)

| Time | Phase | Your Action |
| :--- | :--- | :--- |
| **00:00 – 03:00** | **Kickoff** | Start the timer on port `8766`. Explain the UI (`Run Code` = sample tests, `Submit Code` = hidden tests). |
| **03:00 – 14:00** | **Part 1: Basic Filtering** | Let him implement `count_dropped_bytes(logs)` and pass `7/7` on Submit. |
| **14:00 – 32:00** | **Part 2: Validation & Shuffled Keys** | Click **Unlock Part 2** on your Control Deck (`8766`). Watch him design `is_valid_ipv4` + `parse_log_line` and pass hidden validation edge cases. |
| **32:00 – 48:00** | **Part 3: Top-K & Optimization** | Click **Unlock Part 3**. Have him implement `top_dropped_sources(logs, k)`, nail the tie-breaker, pass the 50,000-line stress test, and discuss `heapq.nsmallest` ($\mathcal{O}(N + U \log K)$). |
| **48:00 – 55:00** | **Verbal Networking Q&A** | Ask 2–3 quick Azure / Networking questions from Section 6. |
| **55:00 – 60:00** | **Debrief** | Walk through his scorecard and compare his code with `reference_solutions.py`. |

---

## 5. Part-by-Part Bug Spotting & Tiered Hint Ladder

### Part 1: `count_dropped_bytes(logs)`
- **Common Bugs:**
  - Accidentally including `ALLOW` IPs with value `0`, or forgetting to include `DROP` IPs that have `BYTES=0`.
  - Adding `BYTES` as strings (`"1200" + "800" = "1200800"`) instead of casting `int(...)`.
  - Returning a `defaultdict` works in Python (`defaultdict == dict` is `True`), though `dict(totals)` is cleaner.
- **Hints:**
  - *Level 1:* "What should happen if an IP has `ACTION=DROP` and `BYTES=0` vs. an IP that only has `ACTION=ALLOW`?"
  - *Level 2:* "Split the line by whitespace, then split each `KEY=VALUE` token on `=`."

### Part 2: `count_valid_dropped_bytes(logs)`
- **Common Bugs:**
  - **Only validating `SRC` IP and forgetting `DST` IP!** (Caught by Hidden Test 1!)
  - **Leading Zeros in IPv4:** `int("01")` returns `1` in Python without throwing an error! Must check `len(octet) > 1 and octet[0] == "0"` (or `str(int(octet)) == octet`).
  - **Assuming Fixed Field Order:** Indexing `tokens[1]` as `SRC` breaks when `ACTION=DROP` appears before `SRC=`.
  - **Duplicate Keys / Extra Fields:** Using `kv[k] = v` without checking `if k in kv` or `len(tokens) != 6` lets duplicate keys slip through.
  - **Port Boundary Off-by-One:** Allowing `PORT=0` (invalid) or rejecting `PORT=65535` (valid!).
  - **Negative Numbers:** Note that `"-5".isdigit()` is `False`, which automatically rejects negative numbers cleanly in Python!
- **Hints:**
  - *Level 1:* "Look closely at a line where `SRC` is valid—could any *other* field on that line make it invalid?"
  - *Level 2:* "In Python, `int('01')` succeeds and returns `1`. How can you reject leading zeros while still allowing `'0'`?"
  - *Level 3:* "Store the 5 `KEY=VALUE` tokens into a temporary dict `kv` while checking `if k in kv or k not in REQUIRED_KEYS: return None`."

### Part 3: `top_dropped_sources(logs, k)`
- **Common Bugs:**
  - **Tie-Breaker Direction Bug:** Writing `sorted(items, key=lambda x: (x[1], x[0]), reverse=True)` sorts `src_ip` **descending** on ties instead of ascending!
  - **`k <= 0` Bug:** Slicing `result[:k]` when `k = -1` returns everything except the last element instead of `[]`!
  - **Forgetting Validation:** Reusing Part 1's `count_dropped_bytes` instead of Part 2's `count_valid_dropped_bytes` crashes or includes invalid IPs!
  - **Complexity Discussion:** `sorted()` is $\mathcal{O}(U \log U)$; `heapq.nsmallest(k, totals.items(), key=lambda x: (-x[1], x[0]))` achieves $\mathcal{O}(U \log K)$.
- **Hints:**
  - *Level 1:* "If two IPs both dropped 500 bytes, which one should come first—and what does `reverse=True` do to the second tuple element?"
  - *Level 2:* "How can you sort the first field descending and the second field ascending without using `reverse=True`?"
  - *Level 3:* "Use `key=lambda item: (-item[1], item[0])` inside `heapq.nsmallest(k, totals.items(), key=...)`."

---

## 6. Bonus: 4 Verbal Azure Networking Questions (Final 10 Minutes)

1. **Why do flow collectors (like Azure NSG Flow Logs / NetFlow / sFlow) typically use UDP rather than TCP?**
   - *Expected:* Lower router overhead, stateless, no TCP retransmission storms or head-of-line blocking during congestion (exactly when telemetry volume spikes).
2. **A VM in Azure Subnet A (`10.0.1.10/24`) can't reach a DB in Subnet B (`10.0.2.20/24`) on port 5432. How do you debug it?**
   - *Expected:* Systematic OSI/TCP-IP isolation: local OS firewall & routes $\rightarrow$ Azure NSG outbound (Subnet A/NIC) & inbound (Subnet B/NIC) rules $\rightarrow$ User-Defined Routes (UDRs) / VNet peering $\rightarrow$ TCP handshake (`nc -zv` / `tcping`) & verify DB listening interface (`0.0.0.0` vs `127.0.0.1`).
3. **What is the difference between a `/30`, `/31`, and `/32` subnet in IPv4?**
   - *Expected:* `/32` = single host route (1 IP); `/31` = RFC 3021 point-to-point link (2 usable IPs); `/30` = 4 IPs total (2 usable host IPs + network + broadcast).
4. **How does a router choose between `10.0.0.0/8` and `10.1.2.0/24` when forwarding a packet to `10.1.2.50`?**
   - *Expected:* **Longest Prefix Match (LPM)** always picks the most specific prefix (`/24`) first, regardless of routing protocol metric or administrative distance.

---

## 7. Post-Interview Feedback Scorecard

| Competency | 1 (Needs Work) | 2 (Intern Ready) | 3 (Strong Hire) | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Clarification & Planning** | Started coding immediately without checking rules. | Clarified format & edge cases before coding. | Proactively caught leading zeros, tie-breakers, and scale limits. | |
| **Code Modularity** | Copy-pasted parsing code across all 3 parts. | Extracted `is_valid_ipv4` helper cleanly. | Built clean reusable pipeline: Part 3 directly reuses Part 2's parser. | |
| **Edge-Case Validation** | Missed `DST` IP, leading zeros, or shuffled keys. | Caught most validation rules with minimal debugging. | Nailed every boundary (`0.0.0.0`, port `1..65535`, `BYTES=0`, `k<=0`). | |
| **Optimization & Complexity** | Left inefficient loops or couldn't analyze Big-O. | Clean $\mathcal{O}(N + U \log U)$ solution & accurate Big-O. | Discussed/implemented $\mathcal{O}(N + U \log K)$ heap & streaming tradeoffs. | |
| **Debugging Composure** | Guessed randomly on test failures. | Read diffs & isolated bugs step by step. | Used Custom Input & traced edge cases calmly before hitting Submit. | |
