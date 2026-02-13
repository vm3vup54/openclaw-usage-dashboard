#!/usr/bin/env python3
"""Fetch USD/TWD exchange rate from Bank of Taiwan (rate.bot.com.tw) and write data/fx.json.

Default: use USD row, extract cash/spot buy/sell.
This script is designed to run in GitHub Actions.

Output schema (data/fx.json):
{
  quotedAt: "YYYY-MM-DD HH:MM",
  usdTwd: { cashBuying, cashSelling, spotBuying, spotSelling, label },
  source: "..."
}

"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import urllib.request

URL = "https://rate.bot.com.tw/xrt?Lang=zh-TW"


def fetch_html(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def extract_quoted_at(html: str) -> str:
    # BOT may render the timestamp near the phrase but not necessarily contiguous.
    # We'll locate the phrase then search forward for a datetime.
    anchor = "牌價最新掛牌時間"
    idx = html.find(anchor)
    if idx == -1:
        return ""
    window = html[idx: idx + 300]
    m = re.search(r"(\d{4})[/-](\d{2})[/-](\d{2})\s+(\d{2}:\d{2})", window)
    if not m:
        return ""
    y, mo, d, hm = m.groups()
    return f"{y}-{mo}-{d} {hm}"


def extract_usd_row(html: str):
    # BOT page is HTML. We'll locate the USD row by the visible currency label: 美金 (USD)
    # Then extract the next 4 rate cells in order:
    # 現金買入 現金賣出 即期買入 即期賣出

    marker = "美金 (USD)"

    # Locate the row boundaries around the marker (safer than regex across the whole table).
    idx = html.find(marker)
    if idx == -1:
        raise RuntimeError("Cannot locate USD marker")

    tr_start = html.rfind("<tr", 0, idx)
    tr_end1 = html.find("</tr>", idx)
    if tr_start == -1 or tr_end1 == -1:
        raise RuntimeError("Cannot locate USD <tr> boundaries")

    # Some currencies render cash+spot across two consecutive <tr> (rowspan=2).
    tr_end2 = html.find("</tr>", tr_end1 + len("</tr>"))
    row = html[tr_start: (tr_end2 + len("</tr>")) if tr_end2 != -1 else (tr_end1 + len("</tr>"))]

    def extract_nums(s: str):
        return re.findall(
            r"<td[^>]*class=\"rate-content-(?:cash|sight|spot)[^\"]*\"[^>]*>\s*(\d+\.\d+)\s*</td>",
            s,
            flags=re.S,
        )

    nums = extract_nums(row)
    if len(nums) < 4 and tr_end2 != -1:
        # Try only first row then second row separately isn't needed; this usually fixes it.
        pass

    if len(nums) < 4:
        raise RuntimeError(f"Not enough numeric cells found in USD row: {len(nums)}")

    cash_buy, cash_sell, spot_buy, spot_sell = map(float, nums[:4])
    return cash_buy, cash_sell, spot_buy, spot_sell


def main() -> int:
    out_path = Path(__file__).resolve().parent.parent / "data" / "fx.json"

    html = fetch_html(URL)
    quoted_at = extract_quoted_at(html)
    cash_buy, cash_sell, spot_buy, spot_sell = extract_usd_row(html)

    payload = {
        "quotedAt": quoted_at,
        "usdTwd": {
            "label": "即期賣出",
            "spotSelling": spot_sell,
            "spotBuying": spot_buy,
            "cashSelling": cash_sell,
            "cashBuying": cash_buy,
        },
        "source": URL,
    }

    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
