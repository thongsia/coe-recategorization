#!/usr/bin/env python3
"""
Step 4 - Baseline OBSERVED panel (per-bidding).

Reads:  data/raw/coe_bids.csv            (untouched raw fetch)
Writes: data/processed/coe_panel_perbidding.csv

Transform (documented):
  One row per (month, bidding_no, category) for categories A/B/C/D/E,
  2010-01 .. latest observed month, carrying:
    premium                  clearing price for that bidding (raw field)
    quota, bids_success,
    bids_received            raw fields
    a_minus_b_spread         A premium - B premium for the SAME bidding
                             (null for categories C/D/E: not applicable)
    inversion                1 if A cleared above B in the same bidding,
                             0 if A <= B (null for C/D/E)
    monthly_mean_premium     mean of the class's clearing prices across that
                             month's 1-2 bidding exercises
    monthly_quota_total      sum of quota across that month's exercises
    monthly_bids_received_total /
    monthly_bids_success_total  analogous monthly sums
    n_biddings_in_month      audit: how many exercises the month had for the class

LABELING CONTRACT (hard):
  The panel is OBSERVED historical data. Every row carries
  label = config.output_label("OBSERVED", ...) with the COE data window
  (2010-01..latest) and source citation, value_type=OBSERVED, scenario="".
  It must NEVER be conflated with scenario series (no scenario tag is ever
  stamped on these rows).

Reconciliation (HARD-FAIL on mismatch):
  per category, panel row count == raw row count; categories == {A..E};
  every raw row lands in exactly one panel row.

Layering contract: reads only data/raw/; writes only data/processed/.
Run:  python3 src/baseline_panel.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402

ROOT = Path(config.WORKSPACE_ROOT)
RAW = ROOT / "data" / "raw" / "coe_bids.csv"
OUT = ROOT / "data" / "processed" / "coe_panel_perbidding.csv"
OUT.parent.mkdir(parents=True, exist_ok=True)

EXPECTED_FIRST_MONTH = "2010-01"  # plan: "per-bidding rows 2010 to latest"


def cat_letter(vehicle_class: str) -> str:
    """'Category A' -> 'A'. Take the LAST whitespace token (substring search
    would match the 'A' inside 'Category' and mis-assign every row)."""
    s = str(vehicle_class).strip().split()[-1].upper()
    if s not in ("A", "B", "C", "D", "E"):
        raise SystemExit(f"HARD-FAIL: unrecognised vehicle_class: {vehicle_class!r}")
    return s


def to_num(s: pd.Series) -> pd.Series:
    """Numeric coercion tolerant of thousands separators.

    RAW DATA QUIRK (logged in provenance.md): data.gov.sg COE bidding
    results carry commas in bids_success/bids_received for some months
    (2023-05..2026-10). Raw file is untouched; stripped here at transform.
    """
    return pd.to_numeric(s.astype(str).str.replace(",", "", regex=False),
                         errors="coerce")


def norm_bid(v) -> int:
    s = str(v).strip().lower().lstrip("b#").replace(".0", "")
    return int(s)


def main() -> None:
    raw = pd.read_csv(RAW, dtype=str)

    for c in ("premium", "quota", "bids_success", "bids_received"):
        raw[c] = to_num(raw[c])
    bad_num = raw[raw[["premium", "quota", "bids_success", "bids_received"]]
                    .isna().any(axis=1)]
    if len(bad_num):
        raise SystemExit(f"HARD-FAIL: {len(bad_num)} raw rows with null numeric fields")
    bad_month = raw[~raw["month"].str.match(r"^\d{4}-\d{2}$", na=False)]
    if len(bad_month):
        raise SystemExit(f"HARD-FAIL: {len(bad_month)} rows with non-YYYY-MM month")

    raw["category"] = raw["vehicle_class"].map(cat_letter)
    raw["bid_no"] = raw["bidding_no"].map(norm_bid)
    raw = raw.sort_values(["month", "bid_no", "category"]).reset_index(drop=True)

    first_m, last_m = raw["month"].min(), raw["month"].max()

    # ---- per-bidding derived fields: A-B spread + inversion flag ----
    price = raw.pivot_table(index=["month", "bid_no"], columns="category",
                            values="premium", aggfunc="first")
    price["a_minus_b_spread"] = price["A"] - price["B"]
    price["inversion"] = (price["A"] > price["B"]).astype("float64")

    # ---- monthly aggregates per class (mean price, sums, exercise count) ----
    monthly = raw.groupby(["month", "category"]).agg(
        monthly_mean_premium=("premium", "mean"),
        monthly_quota_total=("quota", "sum"),
        monthly_bids_received_total=("bids_received", "sum"),
        monthly_bids_success_total=("bids_success", "sum"),
        n_biddings_in_month=("bid_no", "count"),
    ).reset_index()

    panel = raw.merge(price.reset_index(), on=["month", "bid_no"], how="left")
    panel = panel.merge(monthly, on=["month", "category"], how="left")

    # ---- reconciliation (HARD-FAIL) ----
    cats = set(panel["category"])
    if cats != {"A", "B", "C", "D", "E"}:
        raise SystemExit(f"HARD-FAIL: expected categories A-E, got {sorted(cats)}")
    raw_counts = raw.groupby("category").size().to_dict()
    panel_counts = panel.groupby("category").size().to_dict()
    for c in "ABCDE":
        if raw_counts.get(c, 0) != panel_counts.get(c, 0):
            raise SystemExit(
                f"HARD-FAIL reconciliation: category {c} raw={raw_counts.get(c)} "
                f"panel={panel_counts.get(c)}")
    # every (month, bid_no, category) unique
    dup = panel.duplicated(subset=["month", "bid_no", "category"]).sum()
    if dup:
        raise SystemExit(f"HARD-FAIL: {dup} duplicate panel rows")

    # ---- OBSERVED label stamp (never scenario-labeled) ----
    data_window = f"coe_bids {first_m}..{last_m} (per-bidding clearing prices)"
    label = config.output_label(
        config.TYPE_OBSERVED,
        data_window=data_window,
        citation="data.gov.sg COE bidding results (resource "
                 f"{config.RESOURCES['coe_bids']}); see verification/provenance_log.csv",
    )
    panel["label"] = label
    panel["value_type"] = config.TYPE_OBSERVED
    panel["scenario"] = ""          # explicitly: NOT a scenario series
    panel["data_window"] = data_window
    panel["citation"] = "data.gov.sg coe_bids"

    cols = [
        "month", "bid_no", "bidding_no", "category", "vehicle_class",
        "premium", "quota", "bids_success", "bids_received",
        "a_minus_b_spread", "inversion",
        "monthly_mean_premium", "monthly_quota_total",
        "monthly_bids_received_total", "monthly_bids_success_total",
        "n_biddings_in_month",
        "label", "value_type", "scenario", "data_window", "citation",
    ]
    panel = panel[cols]
    panel["a_minus_b_spread"] = panel["a_minus_b_spread"].round(2)
    panel["monthly_mean_premium"] = panel["monthly_mean_premium"].round(2)
    for c in ("quota", "bids_success", "bids_received", "monthly_quota_total",
              "monthly_bids_received_total", "monthly_bids_success_total"):
        panel[c] = panel[c].astype("int64")
    panel["bid_no"] = panel["bid_no"].astype("int64")

    panel.to_csv(OUT, index=False)

    inv_n = int(panel["inversion"].fillna(0).sum())
    n_months = panel["month"].nunique()
    print(f"[panel] wrote {OUT}")
    print(f"[panel] rows={len(panel)} months={n_months} ({first_m}..{last_m}) "
          f"per-category={panel_counts}")
    print(f"[panel] 2026 A>B inversions (per-bidding): {inv_n} rows in panel "
          f"(see tables/inversions_2026.csv for the confirmed 2026 set)")
    if first_m != EXPECTED_FIRST_MONTH:
        print(f"[panel] NOTE: first month {first_m} != plan expectation "
              f"{EXPECTED_FIRST_MONTH} (logged, not rewritten)")
    else:
        print(f"[panel] first month {first_m} matches plan expectation")


if __name__ == "__main__":
    main()
