# openclaw-usage-dashboard

A tiny GitHub Pages dashboard for OpenClaw usage/cost (USD + TWD).

## How data flows

- **Usage/cost (USD)** is exported locally from your machine (OpenClaw logs live under `~/.openclaw/`).
  - Run: `./tools/update_usage.py --yesterday` (or `--date YYYY-MM-DD`)
  - This updates `data/usage_daily.json`.
  - Then commit & push.

- **FX (USD→TWD)** is refreshed daily in GitHub Actions from Bank of Taiwan and committed into `data/fx.json`.

## Local update (recommended daily cron)

```bash
cd openclaw-usage-dashboard
./tools/update_usage.py --yesterday
git add data/usage_daily.json
git commit -m "chore: update usage"
git push
```

## Notes

- This is an estimate based on OpenClaw recorded `usage.cost.total`.
- TWD conversion uses Bank of Taiwan **spot selling** rate by default.
