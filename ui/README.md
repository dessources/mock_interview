# HackerRank Project-Style Assessment UI — Quick Setup Guide

This UI recreates HackerRank's **Project-Style Assessment IDE** locally with **zero external dependencies** (works completely offline inside VS Code's Simple Browser).

## Dual-Window Isolation Setup

### 1. Start the Assessment Server (In Your Private Interviewer Terminal)
```bash
python3 ui/server.py
```
This launches two completely isolated local servers:
- **Candidate HackerRank IDE:** `http://127.0.0.1:8765` (Strictly locked to `candidate/` files only)
- **Private Interviewer Control Deck:** `http://127.0.0.1:8766` (Follow-up unlocker, timer, live activity feed, guide, and reference solutions)

---

### 2. Open the Interviewee Window (Share ONLY This Window)
1. Open a **new VS Code window** (`File -> New Window`, or open `/home/pianodessources/misc/mock_interview/candidate`).
2. Press `Ctrl+Shift+P` (Command Palette) and run:
   ```text
   Simple Browser: Show
   ```
3. Enter the candidate URL:
   ```text
   http://127.0.0.1:8765
   ```
4. *(Optional)* Hide the VS Code left sidebar (`Ctrl+B`) so the HackerRank IDE fills the entire shared window cleanly!

---

### 3. Open Your Private Interviewer Window (Keep Off-Screen / Separate Window)
Open `http://127.0.0.1:8766` in your second VS Code window (via `Simple Browser: Show`) or in your regular web browser. From there you can:
- **Start / Pause / Reset** the live countdown timer synced to your friend's screen.
- Click **Unlock Part 2** or **Unlock Part 3** — your friend's browser automatically shows a HackerRank notification, reveals the new follow-up in the Problem pane, and appends the new function stubs to `solution.py` without touching his existing code.
- Watch his **Live Activity Feed** (every Sample Run & Submit result + which hidden tests failed) and his **Live Code** alongside your **Interviewer Playbook** and **Reference Solutions**.
