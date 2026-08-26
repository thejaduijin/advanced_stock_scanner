#!/usr/bin/env python3
"""Convert latest Mehta ADVANCED Screener Excel → JSON for Next.js dashboard."""

import json
import math
import sys
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE / "output"
DATA_DIR = BASE / "public" / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def find_latest_excel():
    files = sorted(OUTPUT_DIR.glob("Mehta_Screener_*.xlsx"), reverse=True)
    return files[0] if files else None


def clean_value(v):
    if v is None:
        return None
    if isinstance(v, float):
        if math.isnan(v) or math.isinf(v):
            return None
        return round(v, 4)
    if hasattr(v, "isoformat"):
        return v.isoformat()
    if pd.isna(v):
        return None
    return v


def clean_record(d: dict):
    return {k: clean_value(v) for k, v in d.items()}


def convert():
    excel_path = find_latest_excel()
    if not excel_path:
        print("No Excel file found in output/. Run mehta_screener_advanced.py first.")
        sys.exit(1)

    print(f"Converting: {excel_path.name}")

    # ONLY read the "ALL" sheet — category sheets are just filtered views
    try:
        df = pd.read_excel(excel_path, sheet_name="ALL")
    except ValueError:
        # Fallback if sheet name differs
        xls = pd.ExcelFile(excel_path)
        sheet_name = "ALL" if "ALL" in xls.sheet_names else xls.sheet_names[0]
        df = pd.read_excel(excel_path, sheet_name=sheet_name)

    stocks = []
    for _, row in df.iterrows():
        d = row.to_dict()
        d["_sheet"] = "ALL"
        stocks.append(clean_record(d))

    # Read summary metadata
    meta = {}
    try:
        sdf = pd.read_excel(excel_path, sheet_name="SUMMARY")
        for _, row in sdf.iterrows():
            meta[str(row.get("Metric", ""))] = row.get("Value", "")
    except Exception:
        pass

    out = {
        "generated_at": str(meta.get("Run date", "")),
        "universe_size": int(meta.get("Universe size", len(stocks))) if meta.get("Universe size") else len(stocks),
        "counts": {
            "CONVICTION": int(meta.get("Conviction (3/3 High Wt)", 0)) if meta.get("Conviction (3/3 High Wt)") else 0,
            "3/3": int(meta.get("3/3 Super Performers", 0)) if meta.get("3/3 Super Performers") else 0,
            "2/3": int(meta.get("2/3 Performers", 0)) if meta.get("2/3 Performers") else 0,
            "1/3": int(meta.get("1/3 Weak", 0)) if meta.get("1/3 Weak") else 0,
            "0/3": int(meta.get("0/3 Exit", 0)) if meta.get("0/3 Exit") else 0,
            "RISK_REJECT": int(meta.get("Risk Rejects", 0)) if meta.get("Risk Rejects") else 0,
        },
        "stocks": stocks,
    }

    out_path = DATA_DIR / "latest.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    print(f"Written: {out_path} ({len(stocks)} unique stocks)")


if __name__ == "__main__":
    convert()