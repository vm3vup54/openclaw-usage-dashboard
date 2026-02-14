#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

# Update yesterday's usage (Asia/Taipei local time on this machine)
python3 tools/update_usage.py --yesterday

# Commit & push only if changed
if git diff --quiet -- data/usage_daily.json; then
  echo "No usage changes"
  exit 0
fi

git add data/usage_daily.json

git config user.name "openclaw-bot"
git config user.email "openclaw-bot@local"

git commit -m "chore: update usage (yesterday)"

# Remote may have new commits (e.g., fx updates from GitHub Actions). Rebase then push.
git pull --rebase origin main

git push
