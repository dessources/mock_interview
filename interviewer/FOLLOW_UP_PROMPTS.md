# Follow-Up Prompts & Live Unlocker Instructions

During the mock interview, your friend starts with **only Part 1** visible in `candidate/PROBLEM.md` and `candidate/solution.py`.

## Option A: Automatic Live Unlocker (Recommended)
From your **private** terminal (outside his shared window), run:

```bash
# When he finishes Part 1 and you're ready to reveal Part 2:
python3 interviewer/unlock_part.py 2

# When he finishes Part 2 and you're ready to reveal Part 3:
python3 interviewer/unlock_part.py 3

# To reset PROBLEM.md back to Part 1 only:
python3 interviewer/unlock_part.py reset
```

Running `unlock_part.py` automatically appends the new problem section to `candidate/PROBLEM.md` and appends the new function stubs to the bottom of `candidate/solution.py` **without modifying any of the code he already wrote**.

---

## Option B: Manual Copy-Paste Prompts

If you prefer to paste the follow-ups manually into chat or his file, you can copy them directly from `interviewer/unlock_part.py` (`PART2_PROBLEM_MD` / `PART3_PROBLEM_MD`).
