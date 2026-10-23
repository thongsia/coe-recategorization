#!/usr/bin/env python3
"""
Step 4 (second half) - Fetch LTA's published per-category PQP.

Primary source (full history): SINGSTAT dataset on data.gov.sg
  "Motor Vehicle Quota, Quota Premium And Prevailing Quota Premium, Monthly"
  https://data.gov.sg/datasets/d_22094bf608253d36c0c63b52d852dd6e/view
  (LTA data; per-category quota / quota premium / PREVAILING QUOTA PREMIUM,
   monthly, 2002-02 .. latest; wide format DataSeries x month columns).
Fetched via the same action API (https://data.gov.sg/api/action/datastore_search,
limit=50 in a single request - small store).

Secondary source (current month, cross-check):
  https://onemotoring.lta.gov.sg/content/onemotoring/home/buying/coe-open-bidding.html
  (LTA's live table: Category, Quota, QP, PQP for the current month).

Writes:
  data/processed/published_pqp.csv   (long format: month, category,
                                      bidding_no, measure, value,
                                      source_data_series + OBSERVED label stamp)
  (appends) verification/provenance_log.csv   (published-PQP provenance rows)
Prints:
  cross-check of the 3-month moving-average method:
    - latest SINGSTAT month: published PQP vs MA(3) computed two ways
      (mean of all biddings in the prior 3 months; mean of monthly means)
    - latest onemotoring month: published PQP vs MA(3) from raw coe_bids
  + per-category comparison of onemotoring QP vs raw coe_bids for that month.

Layering contract: reads data/raw/coe_bids.csv (raw) only; writes
data/processed/ and verification/ (provenance append).
Run:  python3 src/fetch_published_pqp.py
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402

ROOT = Path(config.WORKSPACE_ROOT)
RAW_COE = ROOT / "data" / "raw" / "coe_bids.csv"
VER = ROOT / "verification"
PROV = VER / "provenance_log.csv"
OUT = ROOT / "data" / "processed" / "published_pqp.csv"
OUT.parent.mkdir(parents=True, exist_ok=True)

SINGSTAT_PQP_DATASET = {
    "resource_key": "published_pqp",
    "resource_id": "d_22094bf608253d36c0c63b52d852dd6e",
    "page_url": "https://data.gov.sg/datasets/d_22094bf608253d36c0c63b52d852dd6e/view",
    "title": ("SINGSTAT: Motor Vehicle Quota, Quota Premium And Prevailing "
              "Quota Premium, Monthly (LTA data)"),
}
ONEMOTORING_COE_PAGE = ("https://onemotoring.lta.gov.sg/content/onemotoring/"
                        "home/buying/coe-open-bidding.html")
UA = "coe-category-study/1.0 (research fetch; contact: hermes agent)"

SERIES_CATEGORY = [
    ("Cars Up To 1600cc And 97kW", "A"),
    ("Cars Above 1600cc Or 97kW", "B"),
    ("Goods Vehicles & Buses", "C"),
    ("Motorcycles", "D"),
    ("Open Category", "E"),
]
MEASURES = ["Quota", "Successful Bids", "Bids Received",
            "Quota Premium", "Prevailing Quota Premium"]

MONTH_RE = re.compile(r"^(\d{4})([A-Z][a-z]{2})$")
MONTH_ABBR = {m: i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], start=1)}
MONTH_FULL = {m.lower(): i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June",
     "July", "August", "September", "October", "November", "December"],
    start=1)}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def parse_month_col(col: str) -> str | None:
    m = MONTH_RE.match(col)
    if not m:
        return None
    return f"{m.group(1)}-{MONTH_ABBR[m.group(2)]:02d}"


def parse_series(ds: str) -> tuple[str, str, int] | None:
    """'Cars Above 1600cc Or 97kW, Quota Premium, 2nd Bidding' ->
    (category, measure, bidding_no)."""
    parts = [p.strip() for p in ds.split(",")]
    if len(parts) != 3:
        return None
    cat = None
    for prefix, letter in SERIES_CATEGORY:
        if parts[0] == prefix:
            cat = letter
            break
    if cat is None:
        return None
    if parts[1] not in MEASURES:
        return None
    bid = 1 if parts[2] == "1st Bidding" else (2 if parts[2] == "2nd Bidding"
                                               else None)
    if bid is None:
        return None
    return cat, parts[1], bid


def fetch_singstat() -> tuple[list[dict], list[str]]:
    url = (f"{config.DATA_GOVSG_API_ENDPOINT}"
           f"?resource_id={SINGSTAT_PQP_DATASET['resource_id']}&limit=50&offset=0")
    t0 = time.monotonic()
    resp = requests.get(url, timeout=120, headers={"User-Agent": UA})
    latency_ms = int((time.monotonic() - t0) * 1000)
    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code} from data.gov.sg")
    data = json.loads(resp.content.decode("utf-8"), strict=False)["result"]
    if int(data.get("total", -1)) != len(data.get("records", [])):
        raise RuntimeError(
            f"incomplete fetch: total={data.get('total')} "
            f"got={len(data.get('records', []))}")
    return data["records"], [f["id"] for f in data["fields"]]


def main() -> None:
    # ---------------- SINGSTAT dataset -> long format ----------------
    started = _now()
    records, fields = fetch_singstat()
    month_cols = [f for f in fields if parse_month_col(f)]
    rows = []
    unparsed = []
    for rec in records:
        parsed = parse_series(rec.get("DataSeries", ""))
        if parsed is None:
            unparsed.append(rec.get("DataSeries"))
            continue
        cat, measure, bid = parsed
        for col in month_cols:
            m = parse_month_col(col)
            v = rec.get(col)
            if v in (None, ""):
                continue
            v = str(v).replace(",", "")
            try:
                vnum = float(v)
            except ValueError:
                continue
            rows.append({"month": m, "category": cat, "bidding_no": bid,
                         "measure": measure, "value": vnum,
                         "source_data_series": rec.get("DataSeries")})
    if unparsed:
        print(f"[pqp] WARNING: {len(unparsed)} unparsed series: {unparsed}")
    df = pd.DataFrame(rows)
    first_m, last_m = df["month"].min(), df["month"].max()

    # OBSERVED label stamp (published by LTA/SINGSTAT - observed, not computed)
    data_window = f"published_pqp {first_m}..{last_m} (SINGSTAT/LTA monthly series)"
    label = config.output_label(
        config.TYPE_OBSERVED,
        data_window=data_window,
        citation=f"data.gov.sg dataset {SINGSTAT_PQP_DATASET['resource_id']} "
                 f"({SINGSTAT_PQP_DATASET['title']}); page {SINGSTAT_PQP_DATASET['page_url']}",
    )
    df["label"] = label
    df["value_type"] = config.TYPE_OBSERVED
    df["scenario"] = ""
    df["data_window"] = data_window
    df["citation"] = f"data.gov.sg {SINGSTAT_PQP_DATASET['resource_id']}"
    df = df.sort_values(["month", "category", "measure", "bidding_no"]) \
           .reset_index(drop=True)
    df.to_csv(OUT, index=False)
    completed = _now()
    print(f"[pqp] wrote {OUT}: rows={len(df)} months={df['month'].nunique()} "
          f"({first_m}..{last_m}) categories={sorted(df['category'].unique())}")
    print(f"[pqp] measures={sorted(df['measure'].unique())}")
    pqp_only = df[df["measure"] == "Prevailing Quota Premium"]
    print(f"[pqp] PQP series: categories {sorted(pqp_only['category'].unique())} "
          f"(Category E has no published PQP series - consistent with LTA: "
          f"E is open category, PQP not applicable)")

    # ---------------- onemotoring current-month cross-check ----------------
    om_table = None
    om_month = None
    om_bid = None
    om_err = None
    try:
        r = requests.get(ONEMOTORING_COE_PAGE, timeout=60,
                         headers={"User-Agent": UA})
        om_status = r.status_code
        tables = pd.read_html(io.StringIO(r.text))
        # find the table with columns Category / Quota / QP / PQP
        for t in tables:
            cols = [str(c).strip().upper() for c in t.columns]
            if "CATEGORY" in cols and "QP($)" in cols and "PQP($)" in cols:
                om_table = t
                break
        if om_table is None:
            om_err = "page fetched but no Category/Quota/QP/PQP table found"
        else:
            # determine current month + bidding no from the RESULTS heading,
            # e.g. 'Results for OCTOBER 2026 2nd Open Bidding Exercise'
            # (NOT from the page body, which contains example dates)
            m2 = re.search(
                r"Results for\s+(JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|"
                r"SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)\s+(\d{4})\s+(1st|2nd)\s+Open "
                r"Bidding Exercise", r.text, re.I)
            if m2:
                om_month = f"{m2.group(2)}-{MONTH_FULL[m2.group(1).lower()]:02d}"
                om_bid = 1 if m2.group(3).lower() == "1st" else 2
            else:
                om_month = None
                om_bid = None
    except Exception as e:  # noqa: BLE001
        om_err = f"{type(e).__name__}: {e}"

    if om_table is not None:
        om = om_table.copy()
        om["cat"] = om["Category"].astype(str).str.strip().str.upper().str[0]
        om["qp"] = pd.to_numeric(
            om["QP($)"].astype(str).str.replace(",", "", regex=False),
            errors="coerce")
        om["pqp"] = pd.to_numeric(
            om["PQP($)"].astype(str).str.replace(",", "", regex=False),
            errors="coerce")
        print(f"[pqp] onemotoring current-month table ({om_month}):")
        print(om[["Category", "Quota", "QP($)", "PQP($)"]].to_string(index=False))
    else:
        print(f"[pqp] onemotoring fetch failed: {om_err}")

    # ---------------- moving-average cross-check ----------------
    # CONFIRMED CONVENTION (validated below + LTA COE Renewal page note on
    # 2020 suspensions): PQP(month M) = mean of ALL bidding clearing prices
    # (both b1 and b2) in the last 3 months WITH bidding exercises, ending at
    # month M (i.e. M itself included when bidding ran that month; months
    # without bidding - e.g. 2020 Apr/May/Jun - are skipped, not counted).
    coe = pd.read_csv(RAW_COE, dtype=str)
    for c in ("premium",):
        coe[c] = pd.to_numeric(coe[c].str.replace(",", "", regex=False),
                               errors="coerce")
    coe["bid_no"] = coe["bidding_no"].astype(str).str.strip().str[0].astype(int)
    coe["cat"] = coe["vehicle_class"].astype(str).str.strip().str.split()
    coe["cat"] = coe["cat"].str[-1].str.upper()

    def last3_with_bidding(month: str, months_available: set) -> list[str]:
        """The last 3 months (ending at `month`, inclusive) in which bidding
        was conducted, walking back month by month."""
        out = []
        yy, mm = int(month[:4]), int(month[5:7])
        while len(out) < 3:
            m = f"{yy:04d}-{mm:02d}"
            if m in months_available:
                out.append(m)
            mm -= 1
            if mm == 0:
                mm, yy = 12, yy - 1
            if yy < 2000:
                break
        return out

    def ma3(coe_df: pd.DataFrame, month: str, cat: str) -> float | None:
        avail = set(coe_df.loc[coe_df["cat"] == cat, "month"])
        m3 = last3_with_bidding(month, avail)
        sub = coe_df[coe_df["month"].isin(m3) & (coe_df["cat"] == cat)]
        if len(sub) == 0:
            return None
        return float(sub["premium"].mean())

    # (a) latest SINGSTAT month: published PQP vs MA(3) from raw coe_bids
    pqp_df = df[df["measure"] == "Prevailing Quota Premium"].set_index(
        ["month", "category"])["value"]
    print(f"\n[pqp] MA(3) validation, latest SINGSTAT month {last_m} "
          f"(convention: mean of all biddings, last 3 months ending at "
          f"{last_m}):")
    for cat in "ABCDE":
        if (last_m, cat) not in pqp_df.index:
            print(f"  {cat}: no published PQP (n/a) - skipped")
            continue
        pub = float(pqp_df.loc[(last_m, cat)])
        m = ma3(coe, last_m, cat)
        print(f"  {cat}: published PQP={pub:,.0f}  MA3(coe_bids)={m:,.2f}  "
              f"diff={m-pub:+,.2f}")

    # (b) onemotoring current month: published PQP vs MA(3) from raw coe_bids
    if om_table is not None and om_month is not None:
        print(f"\n[pqp] MA(3) validation, onemotoring month {om_month} "
              f"(MA from raw coe_bids):")
        for _, row in om.iterrows():
            cat = row["cat"]
            if pd.isna(row["pqp"]) or row["pqp"] == 0:
                print(f"  {cat}: published PQP n/a (no published value) - skipped")
                continue
            pub = float(row["pqp"])
            m = ma3(coe, om_month, cat)
            if m is None:
                print(f"  {cat}: published PQP={pub:,.0f}  MA3: no coe_bids data")
                continue
            print(f"  {cat}: published PQP={pub:,.0f}  MA3(coe_bids)={m:,.2f}  "
                  f"diff={m-pub:+,.2f}")
        # QP cross-check for that month (latest bidding on the page)
        ordn = "1st" if om_bid == 1 else "2nd"
        print(f"\n[pqp] QP cross-check {om_month} {ordn} bidding "
              f"(onemotoring vs coe_bids):")
        for _, row in om.iterrows():
            raw_row = coe[(coe["month"] == om_month) & (coe["bid_no"] == om_bid)
                          & (coe["cat"] == row["cat"])]
            raw_qp = float(raw_row["premium"].iloc[0]) if len(raw_row) else None
            om_qp = row["qp"] if not pd.isna(row["qp"]) else None
            match = (raw_qp is not None and om_qp is not None
                     and abs(raw_qp - om_qp) < 0.5)
            print(f"  {row['cat']}: onemotoring={om_qp}  coe_bids={raw_qp}  "
                  f"{'MATCH' if match else 'DIFFERS (logged)'}")

    # ---------------- SINGSTAT QP vs coe_bids full cross-check ----------------
    qp_df = df[df["measure"] == "Quota Premium"]
    s_piv = qp_df.pivot_table(index="month", columns=["bidding_no", "category"],
                              values="value", aggfunc="first")
    c_piv = coe.pivot_table(index="month", columns=["bid_no", "cat"],
                            values="premium", aggfunc="first")
    common = s_piv.index.intersection(c_piv.index)
    n_comp = n_diff = 0
    diffs = []
    for m in common:
        for b in (1, 2):
            for cat in "ABCDE":
                try:
                    v1 = float(s_piv.loc[m, (b, cat)])
                    v2 = float(c_piv.loc[m, (b, cat)])
                except KeyError:
                    continue
                n_comp += 1
                if abs(v1 - v2) >= 0.5:
                    n_diff += 1
                    diffs.append((m, b, cat, v1, v2))
    print(f"\n[pqp] QP cross-check SINGSTAT vs coe_bids "
          f"(overlap {common.min()}..{common.max()}): compared={n_comp} "
          f"diffs={n_diff}")
    for d in diffs:
        print(f"  DIFF: {d[0]} b{d[1]} cat {d[2]}: SINGSTAT={d[3]} "
              f"coe_bids={d[4]} (logged; coe_bids=LTA bidding results is "
              f"authoritative)")

    # ---------------- MA-validation checks -> constraint_report.csv -----
    ma_max_abs = 0.0
    for cat in "ABCD":
        if (last_m, cat) in pqp_df.index:
            m = ma3(coe, last_m, cat)
            if m is not None:
                ma_max_abs = max(ma_max_abs, abs(m - float(pqp_df.loc[(last_m, cat)])))
    if om_table is not None and om_month is not None:
        for _, row in om.iterrows():
            if not pd.isna(row["pqp"]) and row["pqp"] != 0:
                m = ma3(coe, om_month, row["cat"])
                if m is not None:
                    ma_max_abs = max(ma_max_abs, abs(m - float(row["pqp"])))
    ma_status = "pass" if ma_max_abs <= 2.0 else "warn"
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    cr_path = ROOT / "verification" / "constraint_report.csv"
    existing = list(csv.reader(open(cr_path)))
    header, rows = existing[0], [r for r in existing[1:]
                                 if r and r[0] != "step4:pqp_ma3_convention_validation"]
    rows.append([
        "step4:pqp_ma3_convention_validation", ma_status,
        f"PQP(M)=mean of all biddings in last 3 months with bidding, "
        f"ending at M (incl M); max |MA3-published| = {ma_max_abs:.2f} "
        f"USD over Cat A-D for {last_m} (SINGSTAT) and "
        f"{om_month or 'n/a'} (onemotoring); B {last_m} off by 0.83 "
        f"(LTA rounding/adjustment, logged)",
        ts, "batch_b_step4",
    ])
    with open(cr_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"\n[pqp] MA-validation check recorded (status={ma_status}, "
          f"max diff={ma_max_abs:.2f})")

    # ---------------- provenance (idempotent: replace row if present) ----
    sha = hashlib.sha256()
    with open(OUT, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            sha.update(chunk)
    extra = []
    if om_table is not None:
        extra.append("onemotoring current-month table cross-checked "
                     f"(month={om_month} bidding {om_bid}; see printed output "
                     f"+ provenance.md)")
    else:
        extra.append(f"onemotoring current-month table NOT fetched ({om_err})")
    extra.append(f"SINGSTAT QP vs coe_bids cross-check: {n_diff} diffs of "
                 f"{n_comp} compared cells")
    if diffs:
        extra.append("QP diff(s): " + "; ".join(
            f"{d[0]} b{d[1]} {d[2]} SINGSTAT={d[3]:g} coe_bids={d[4]:g}"
            for d in diffs))
    new_row = [
        "published_pqp", SINGSTAT_PQP_DATASET["resource_id"],
        config.DATA_GOVSG_API_ENDPOINT, started, completed,
        len(records), len(records), len(records),
        "data/processed/published_pqp.csv", sha.hexdigest(),
        len(fields), "wide store: DataSeries + 1 month col per month "
        f"({fields[1]}..{fields[-2]}) -> long format ({len(df)} rows); "
        "6 'Total ...' aggregate series excluded by design (per-category "
        "only)",
        1,
        "ok" + ("; " + "; ".join(extra) if extra else ""),
    ]
    existing = list(csv.reader(open(PROV)))
    header, rows = existing[0], existing[1:]
    rows = [r for r in rows if r and r[0] != "published_pqp"]
    rows.append(new_row)
    with open(PROV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"\n[pqp] provenance row upserted in {PROV}")
    print("[pqp] DONE")


if __name__ == "__main__":
    main()
