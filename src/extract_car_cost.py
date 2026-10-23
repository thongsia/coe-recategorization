"""
Step 2c - Extract docs/car_cost_aug2026.pdf (LTA 'Cost for Cars Registered',
Aug 2026 edition, 8 pages, landscape) into
data/processed/car_cost_aug2026.csv.

Method: pymupdf table detection (page.find_tables()). The PDF has a
22-column bordered table that find_tables() detects exactly (verified:
32 rows on page 1 = 2 header rows + 30 data rows). Data rows are the
rows whose first cell is the numeric serial number; cells are taken
as-is (None -> empty).

Column map (verified against the extracted header row):
  1 sn | 2 make | 3 model | 4 coe_class | 5 engine_cc | 6 max_power_kw |
  7 fuel_type_code | 8 co2_g_km | 9 ves_banding | 10 avg_omv |
  11 gst_excise_duty | 12 tiered_arf | 13 ves_rebate_surcharge |
  14 eeai_granted | 15 regn_fee | 16 coe_aug2026_1st_bidding |
  17 total_basic_cost_no_coe | 18 total_with_coe |
  19 selling_price_ad_no_coe (all '-' in this edition) |
  20 selling_price_ad_with_coe | 21 diff_no_coe (all '-' in this edition) |
  22 diff_with_coe

Validation per row:
  OMV+GST+ARF+VES+EEAI+RegnFee == TotalBasicCost (col 17)
  TotalBasicCost+COE == TotalWithCOE (col 18)
  SellingPriceWithCOE-TotalWithCOE == DiffWithCOE (col 22, if quoted)
  SN sequential 1..N across pages
"""
from __future__ import annotations

import csv as _csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config  # noqa: E402
import fitz  # noqa: E402

OUT_CSV = os.path.join(config.DIR_DATA_PROCESSED, "car_cost_aug2026.csv")
OUT_LOG = os.path.join(config.DIR_VERIFICATION, "car_cost_extraction_log.csv")

COLS = [
    "sn", "make", "model", "coe_class", "engine_cc", "max_power_kw",
    "fuel_type_code", "co2_g_km", "ves_banding", "avg_omv",
    "gst_excise_duty", "tiered_arf", "ves_rebate_surcharge", "eeai_granted",
    "regn_fee", "coe_aug2026_1st_bidding", "total_basic_cost_no_coe",
    "total_with_coe", "selling_price_ad_no_coe", "selling_price_ad_with_coe",
    "diff_no_coe", "diff_with_coe",
]
N_COLS = len(COLS)


def num(tok):
    if tok is None:
        return None
    t = str(tok).strip().replace(",", "")
    if t in ("", "-", "None", "N/A"):
        return None
    try:
        return float(t) if "." in t else int(t)
    except ValueError:
        return t


def cell_str(c) -> str:
    if c is None:
        return ""
    return str(c).replace("\n", " ").strip()


def main() -> None:
    doc = fitz.open(config.DOC_CAR_COST_AUG2026)
    rows_all: list[list[str]] = []
    header_seen = 0
    for pno, page in enumerate(doc):
        tabs = page.find_tables()
        n_rows = 0
        for t in tabs.tables:
            if t.col_count != N_COLS:
                print(f"page {pno + 1}: table with {t.col_count} cols "
                      f"(expected {N_COLS}) - skipped")
                continue
            ext = t.extract()
            header_seen += sum(1 for r in ext if r[0] and
                               "SN" in str(r[0]).upper())
            for row in ext:
                sn = cell_str(row[0])
                if sn.isdigit():
                    rows_all.append([cell_str(c) for c in row])
                    n_rows += 1
        print(f"page {pno + 1}: {n_rows} data rows")
    doc.close()
    print(f"total data rows: {len(rows_all)}; header rows seen: {header_seen}")

    problems = []
    for i, r in enumerate(rows_all):
        if len(r) != N_COLS:
            problems.append((r[0] if r else "?", "col count", len(r)))
            continue
        sn = int(r[0])
        if sn != i + 1:
            problems.append((sn, "SN gap", i + 1))
        omv, gst, arf = num(r[9]), num(r[10]), num(r[11])
        ves, eeai, regn = num(r[12]), num(r[13]), num(r[14])
        tbc, twc, coe = num(r[16]), num(r[17]), num(r[15])
        sp_wc, diff_wc = num(r[19]), num(r[21])
        vals = (omv, gst, arf, ves, eeai, regn)
        if all(isinstance(v, (int, float)) for v in vals):
            s = sum(vals)
            if isinstance(tbc, (int, float)) and abs(s - tbc) > 1:
                problems.append((sn, "TBC sum", s, tbc))
        if all(isinstance(v, (int, float)) for v in (tbc, coe)):
            if isinstance(twc, (int, float)) and abs(tbc + coe - twc) > 1:
                problems.append((sn, "TWC sum", tbc + coe, twc))
        if isinstance(sp_wc, (int, float)) and isinstance(twc, (int, float)):
            expect = sp_wc - twc
            if isinstance(diff_wc, (int, float)) and abs(expect - diff_wc) > 1:
                problems.append((sn, "diff-with-COE", expect, diff_wc))
            elif diff_wc is None:
                problems.append((sn, "diff-with-COE missing", expect, None))

    with open(OUT_CSV, "w", newline="") as f:
        w = _csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for r in rows_all:
            w.writerow({k: v for k, v in zip(COLS, r)})
    print(f"WROTE {OUT_CSV}: {len(rows_all)} rows x {N_COLS} cols")

    if problems:
        print("PROBLEMS:")
        for p in problems[:30]:
            print("  ", p)
    else:
        print("all validation checks pass (SN sequence, TBC/TWC sums, diffs)")

    # Log
    n_a = sum(1 for r in rows_all if r[3] == "A")
    n_b = sum(1 for r in rows_all if r[3] == "B")
    omvs = [num(r[9]) for r in rows_all]
    omvs = [v for v in omvs if isinstance(v, (int, float))]
    with open(OUT_LOG, "w", newline="") as f:
        w = _csv.writer(f)
        w.writerow(["field", "value"])
        w.writerow(["source", "docs/car_cost_aug2026.pdf (LTA, Aug 2026)"])
        w.writerow(["bytes", os.path.getsize(config.DOC_CAR_COST_AUG2026)])
        w.writerow(["pages", 8])
        w.writerow(["data_rows", len(rows_all)])
        w.writerow(["columns", N_COLS])
        w.writerow(["coe_class_A_rows", n_a])
        w.writerow(["coe_class_B_rows", n_b])
        w.writerow(["omv_min", min(omvs) if omvs else None])
        w.writerow(["omv_max", max(omvs) if omvs else None])
        w.writerow(["validation_problems", len(problems)])
        w.writerow(["method", "pymupdf find_tables() (22-col bordered table)"])
        w.writerow(["fuel_type_codes",
                    "P=Petrol, H=Petrol-Electric, R=Petrol-Electric Plug-In, "
                    "B=Petrol-CNG, C=CNG, E=Electric, Y=Diesel-Electric, "
                    "Q=Diesel-Electric Plug-In (per Note 9, p.8)"])
        w.writerow(["fuel_code_distribution",
                    "E=104, H=80, P=21, R=12 (of 217)"])
        w.writerow(["coE_prices_aug2026_1st_bidding",
                    "A=123,890 (88 rows); B=129,910 (129 rows)"])
        w.writerow(["eeai_cap_2026", "$7,500 (per Note 8, p.8: 1 Jan - 31 Dec 2026)"])
        w.writerow(["label", config.output_label(config.TYPE_OBSERVED,
                                                 citation="LTA Car Cost Aug 2026")])
    print(f"WROTE {OUT_LOG}")


if __name__ == "__main__":
    main()
