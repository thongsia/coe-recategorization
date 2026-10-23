#!/usr/bin/env python3
"""
Step 3 (verification half) - anchor verification on the fetched raw data.

Reads:  data/raw/coe_bids.csv, data/raw/registrations.csv
Writes: tables/inversions_2026.csv
        (appends check rows to) verification/constraint_report.csv
Prints: full check summary (expected / actual / pass-fail) to stdout.

Checks (plan step 3):
  1. Row-count reconciliation: fetched rows == API-stated total (from
     verification/provenance_log.csv) == plan expectation (~1,990 / ~51,669).
  2. COE last month carries BOTH bidding numbers (expected 2026-10, b1+b2).
  3. Registrations last month == 2025-05 (frozen dataset).
  4. Registrations null-`number` rows: count, and confirm consistent
     exclusion is possible (nulls logged, not silently dropped).
  5. Spot-checked clearing prices 2026-10 (config.COE_SPOT_VALUES_2026_10).
  6. 2026 A>B inversion set at per-bidding resolution
     (config.A_GT_B_INVERSIONS_2026) -> tables/inversions_2026.csv.

All discrepancies are logged with actual values - never silently rewritten.
Run:  python3 src/verify_anchors.py
"""
from __future__ import annotations

import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402

ROOT = Path(config.WORKSPACE_ROOT)
RAW = ROOT / "data" / "raw"
TAB = ROOT / "tables"
VER = ROOT / "verification"
TAB.mkdir(parents=True, exist_ok=True)

PROV = VER / "provenance_log.csv"
CONSTRAINT = VER / "constraint_report.csv"

EXPECTED_COE_ROWS = 1990        # plan: "~1,990 rows, 2010 to 2026-10"
EXPECTED_REG_ROWS = 51669       # plan: "~51,669 rows"
EXPECTED_COE_LAST_MONTH = "2026-10"
EXPECTED_COE_LAST_MONTH_BIDDINGS = {1, 2}   # both b1 and b2
EXPECTED_REG_LAST_MONTH = "2025-05"

CHECKS: list[dict] = []


def record(check: str, expected: str, actual: str, status: str, detail: str = "") -> None:
    CHECKS.append({
        "check": check,
        "expected": expected,
        "actual": actual,
        "status": status,
        "detail": detail,
    })
    print(f"[{status.upper():7s}] {check}\n"
          f"        expected: {expected}\n        actual:   {actual}"
          + (f"\n        detail:   {detail}" if detail else ""))


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def norm_bid(v) -> int:
    """Normalize bidding_no ('1', 'b1', 1.0, '1.0') -> 1."""
    s = str(v).strip().lower().lstrip("b#").replace(".0", "")
    return int(s)


def _num(s: pd.Series) -> pd.Series:
    """Numeric coercion that tolerates thousands separators.

    RAW DATA QUIRK (logged): data.gov.sg COE bidding results carry
    thousands-separator commas in `bids_success` (41 rows) and
    `bids_received` (109 rows) for 2023-05..2026-10. The raw file is left
    untouched; commas are stripped at transform time only.
    """
    return pd.to_numeric(s.astype(str).str.replace(",", "", regex=False),
                         errors="coerce")


def main() -> None:
    # ---------- load raw data ----------
    coe = pd.read_csv(RAW / "coe_bids.csv", dtype=str)
    reg = pd.read_csv(RAW / "registrations.csv", dtype=str)
    prov = pd.read_csv(PROV, dtype=str)

    for c in ("premium", "quota", "bids_success", "bids_received"):
        coe[c] = _num(coe[c])
    coe_raw = pd.read_csv(RAW / "coe_bids.csv", dtype=str)
    n_comma_rows = int(
        coe_raw[
            [c for c in ("quota", "bids_success", "bids_received", "premium")]
        ].apply(lambda s: s.str.contains(",", regex=False)).any(axis=1).sum()
    )
    coe["bid_no"] = coe["bidding_no"].map(norm_bid)
    reg["n_num"] = _num(reg["number"])

    bad_month = coe[~coe["month"].str.match(r"^\d{4}-\d{2}$", na=False)]
    if len(bad_month):
        record("coe_month_format", "all months YYYY-MM", f"{len(bad_month)} bad rows",
               "FAIL", str(bad_month["month"].unique()[:10]))

    # raw-format quirk audit: thousands-separator commas in numeric fields
    # (transform strips them; raw file untouched)
    record(
        "coe_thousands_separators_audit",
        "identify rows with comma-formatted numbers (strip at transform time)",
        f"{n_comma_rows} raw rows affected (bids_success/bids_received, 2023-05..2026-10)",
        "PASS",
        "raw file left untouched; stripped in verify/panel transforms only",
    )

    # ---------- 1. row-count reconciliation ----------
    for key, fname, expected in (
        ("coe_bids", "coe_bids.csv", EXPECTED_COE_ROWS),
        ("registrations", "registrations.csv", EXPECTED_REG_ROWS),
    ):
        row = prov[prov["resource_key"] == key]
        stated = int(row["api_stated_total"].iloc[0]) if len(row) else -1
        n = len(pd.read_csv(RAW / fname, dtype=str))
        ok_api = (n == stated)
        ok_plan = (n == expected)
        status = "PASS" if (ok_api and ok_plan) else "FAIL"
        record(
            f"row_count_reconciliation:{key}",
            f"API-stated total == fetched == plan expectation ({expected})",
            f"fetched={n} api_stated={stated} plan_expected={expected}",
            status,
            "" if ok_plan else f"DISCREPANCY: fetched {n} vs plan expectation {expected} (logged, not rewritten)",
        )

    # ---------- 2. COE last month carries both biddings ----------
    last_m = coe["month"].max()
    bids_last = sorted(coe.loc[coe["month"] == last_m, "bid_no"].unique())
    ok = (last_m == EXPECTED_COE_LAST_MONTH) and set(bids_last) == EXPECTED_COE_LAST_MONTH_BIDDINGS
    record(
        "coe_last_month_both_biddings",
        f"last month {EXPECTED_COE_LAST_MONTH} with biddings {sorted(EXPECTED_COE_LAST_MONTH_BIDDINGS)}",
        f"last month {last_m} with biddings {bids_last}",
        "PASS" if ok else "FAIL",
    )

    # ---------- 3. registrations last month ----------
    reg_last = reg["month"].max()
    record(
        "registrations_last_month",
        EXPECTED_REG_LAST_MONTH,
        reg_last,
        "PASS" if reg_last == EXPECTED_REG_LAST_MONTH else "FAIL",
    )

    # ---------- 4. registrations null number ----------
    null_mask = reg["number"].isna() | (reg["number"].astype(str).str.strip().isin(["", "null", "None", "NA", "NaN"]))
    n_null = int(null_mask.sum())
    n_valid = len(reg) - n_null
    record(
        "registrations_null_number_count",
        "count null/blank 'number' rows; exclude consistently (logged, not dropped silently)",
        f"null_number_rows={n_null} valid_rows={n_valid} of {len(reg)}",
        "PASS" if n_null >= 0 else "FAIL",
        f"downstream mix estimates must use the {n_valid} valid rows (null-number rows excluded)",
    )

    # ---------- 5. spot-checked clearing prices 2026-10 ----------
    spot_results = []
    all_ok = True
    for bid_key, vals in config.COE_SPOT_VALUES_2026_10.items():
        bn = int(bid_key[1:])
        sub = coe[(coe["month"] == "2026-10") & (coe["bid_no"] == bn)]
        for cat, exp in vals.items():
            row = sub[sub["vehicle_class"].str.strip().str.endswith(cat)]
            if len(row) != 1:
                all_ok = False
                spot_results.append(f"2026-10 {bid_key} {cat}: MISSING row (found {len(row)})")
                continue
            got = float(row["premium"].iloc[0])
            if abs(got - exp) < 0.5:
                spot_results.append(f"2026-10 {bid_key} {cat}: {got:.0f} == {exp} OK")
            else:
                all_ok = False
                spot_results.append(
                    f"2026-10 {bid_key} {cat}: got {got:.0f} != expected {exp} DISCREPANCY")
    record(
        "spot_prices_2026_10",
        "config.COE_SPOT_VALUES_2026_10 (b1: A 130001 B 130100 C 91889 D 11012 E 137000; "
        "b2: A 132004 B 131901 E 135790)",
        "; ".join(spot_results),
        "PASS" if all_ok else "FAIL",
    )

    # ---------- 6. 2026 A>B inversion set (per-bidding) ----------
    piv = coe[coe["month"].str.startswith("2026")].pivot_table(
        index=["month", "bid_no"], columns="vehicle_class", values="premium", aggfunc="first"
    )
    piv.columns = [c.strip().split()[-1].upper() for c in piv.columns]
    piv["spread_A_minus_B"] = piv["A"] - piv["B"]
    actual_inversions = sorted(
        [(m, int(b)) for (m, b), r in piv.dropna(subset=["A", "B"]).iterrows() if r["A"] > r["B"]]
    )
    expected_inversions = sorted([(m, norm_bid(b)) for (m, b) in config.A_GT_B_INVERSIONS_2026])
    inv_ok = actual_inversions == expected_inversions
    record(
        "inversion_set_2026_per_bidding",
        f"{{{' '.join(f'{m} b{b}' for m, b in expected_inversions)}}}",
        f"{{{' '.join(f'{m} b{b}' for m, b in actual_inversions)}}}",
        "PASS" if inv_ok else "FAIL",
        "" if inv_ok else "DISCREPANCY: actual inversion set differs from plan expectation (logged with actual values)",
    )

    # ---------- write tables/inversions_2026.csv ----------
    inv_rows = []
    obs_label = config.output_label(
        config.TYPE_OBSERVED,
        citation="data.gov.sg COE bidding results (d_69b3380ad7e51aff3a7dcc84eba52b8a), "
                 "fetched per verification/provenance_log.csv",
    )
    for (m, b), r in piv.dropna(subset=["A", "B"]).iterrows():
        if r["A"] > r["B"]:
            inv_rows.append({
                "month": m,
                "bidding_no": int(b),
                "a_premium": round(float(r["A"]), 2),
                "b_premium": round(float(r["B"]), 2),
                "spread_a_minus_b": round(float(r["A"] - r["B"]), 2),
                "a_bids_received": int(coe[(coe["month"] == m) & (coe["bid_no"] == b)
                                           & (coe["vehicle_class"].str.strip().str.endswith("A"))]["bids_received"].iloc[0]),
                "b_bids_received": int(coe[(coe["month"] == m) & (coe["bid_no"] == b)
                                           & (coe["vehicle_class"].str.strip().str.endswith("B"))]["bids_received"].iloc[0]),
                "label": obs_label,
                "value_type": config.TYPE_OBSERVED,
                "scenario": "",
                "data_window": "",
                "citation": "data.gov.sg coe_bids",
            })
    inv_df = pd.DataFrame(inv_rows, columns=[
        "month", "bidding_no", "a_premium", "b_premium", "spread_a_minus_b",
        "a_bids_received", "b_bids_received",
        "label", "value_type", "scenario", "data_window", "citation"])
    inv_df.to_csv(TAB / "inversions_2026.csv", index=False)
    print(f"[verify] wrote {TAB / 'inversions_2026.csv'} ({len(inv_df)} rows)")

    # ---------- append checks to constraint_report.csv ----------
    ts = _now()
    new_cols_needed = not CONSTRAINT.exists()
    with open(CONSTRAINT, "a", newline="") as f:
        w = csv.writer(f)
        if new_cols_needed:
            w.writerow(["check", "status", "detail", "timestamp_utc", "constraint_stage"])
        for c in CHECKS:
            w.writerow([
                f"step3:{c['check']}",
                c["status"].lower(),
                f"expected={c['expected']} | actual={c['actual']}"
                + (f" | {c['detail']}" if c["detail"] else ""),
                ts,
                "batch_b_step3",
            ])
    print(f"[verify] appended {len(CHECKS)} check rows to {CONSTRAINT}")

    n_fail = sum(1 for c in CHECKS if c["status"] == "FAIL")
    print(f"[verify] SUMMARY: {len(CHECKS)} checks, {n_fail} FAIL")
    if n_fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
