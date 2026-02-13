#!/usr/bin/env python3
"""Update data/usage_daily.json from local OpenClaw logs.

This script is intended to run on *your machine* (not GitHub Actions), because
OpenClaw logs live under ~/.openclaw/.

It:
- Calculates a date window (default: today) in Asia/Taipei local time.
- Calls ~/.openclaw/workspace/openclaw_cost.py to get totals and by-model costs.
- Appends/updates the matching day entry in data/usage_daily.json.

Examples:
  ./tools/update_usage.py --date 2026-02-13
  ./tools/update_usage.py --yesterday

"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
from pathlib import Path

RE_COST = re.compile(r"Est\. cost:\s+\$(\d+\.\d+)")
RE_CALLS = re.compile(r"Calls:\s+([0-9,]+)")
RE_TOKENS = re.compile(r"Tokens:\s+([0-9,]+)")
RE_BREAK = re.compile(r"^([^\n]+)\n\s+calls=([0-9,]+)\s+tokens=([0-9,]+)\s+cost=\$(\d+\.\d+)", re.M)


def run_cost(since: str, until: str, by_model: bool) -> str:
    cmd = [os.path.expanduser("~/.openclaw/workspace/openclaw_cost.py"), "--since", since, "--until", until]
    if by_model:
        cmd.append("--by-model")
    return subprocess.check_output(cmd, text=True)


def parse_total(txt: str):
    calls = int(RE_CALLS.search(txt).group(1).replace(",", ""))
    tokens = int(RE_TOKENS.search(txt).group(1).replace(",", ""))
    cost = float(RE_COST.search(txt).group(1))
    return calls, tokens, cost


def parse_by_model(txt: str):
    out = {}
    for m in RE_BREAK.finditer(txt):
        key = m.group(1).strip()
        calls = int(m.group(2).replace(",", ""))
        tokens = int(m.group(3).replace(",", ""))
        cost = float(m.group(4))
        out[key] = {"calls": calls, "tokens": tokens, "costUsd": cost}
    return out


def load_json(path: Path):
    if not path.exists():
        return {"asOf": "", "days": []}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="YYYY-MM-DD (Asia/Taipei)")
    ap.add_argument("--yesterday", action="store_true")
    args = ap.parse_args()

    today = dt.date.today()
    if args.yesterday:
        d = today - dt.timedelta(days=1)
    elif args.date:
        d = dt.date.fromisoformat(args.date)
    else:
        d = today

    since = d.isoformat()
    until = (d + dt.timedelta(days=1)).isoformat()

    total_txt = run_cost(since, until, by_model=False)
    by_model_txt = run_cost(since, until, by_model=True)

    calls, tokens, cost = parse_total(total_txt)
    by_model = parse_by_model(by_model_txt)

    repo_root = Path(__file__).resolve().parent.parent
    out_path = repo_root / "data" / "usage_daily.json"
    obj = load_json(out_path)

    day_entry = {
        "date": since,
        "total": {"calls": calls, "tokens": tokens, "costUsd": cost},
        "byModel": by_model,
    }

    days = obj.get("days") or []
    replaced = False
    for i, existing in enumerate(days):
        if existing.get("date") == since:
            days[i] = day_entry
            replaced = True
            break
    if not replaced:
        days.append(day_entry)
        days.sort(key=lambda x: x.get("date") or "")

    obj["days"] = days
    obj["asOf"] = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    out_path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Updated {out_path} ({since})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
