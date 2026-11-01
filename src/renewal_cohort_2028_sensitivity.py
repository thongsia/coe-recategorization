#!/usr/bin/env python3
"""Step 13b — 2028-start renewal sensitivity: 2018-vintage cohort (SENSITIVITY).

The base case anchors the regime at 2027-01-01 (config default), so the
first-renewal cohort is vintage 2017 (src/renewal_cohort.py). Given that
LTA findings are due 1H2027, a 2028 start is the more probable real-world
date; this script re-derives the first-renewal cohort for a
2028-01-01 anchor so the README can carry a 2028-start sensitivity.

Derivation (mirrors src/renewal_cohort.py exactly, vintage 2018):
  vintage = 2028 - 10-yr initial COE term = 2018 (every label).
  The 2017 cohort (91,922) renews in 2027, PRE-regime under this anchor:
  it is excluded from first-renewal-cycle analysis here.

Data source chain:
  (1) LTA OneMotoring 'Average OMV of New Cars Registered' year=2018
      edition — AVAILABLE (fetched 2026-11-01T02:40Z, after the
      2026-11-01 00:00-08:00 SGT scheduled maintenance; archived
      verification/lta_omv_2018_page.html, sha256
      eae9c5409864d871d0ab1c292d89ee943138545c90c821ffedc0b357f73e3822;
      model-level average OMVs, 2018-01..2018-12, 3,978 model-month rows,
      876 distinct models, 44 makes). Model-level OMV at the vintage.
  (2) LTA 2018 annual registration statistics — official 2018 COE class
      splits A 39,877 / B 40,216 (LTA Annual Vehicle Statistics 2025
      edition, verification/MVP02-1_New_Reg_by_COE.pdf, 2018 row — same
      file/edition as the 2017 cohort's cross-check).
  (3) 2018 slice of data/raw/registrations.csv (frozen at 2025-05):
      make-level counts, 80,281 cars, 52 makes.
  (4) Model allocation: equal within-make, as in the base case (no public
      model-level 2018 registration counts exist).

Volume assumption (stated): the full 2018 car-registration cohort renews
in 2028 (upper bound — inter-term de-registrations 2018..2028 not
observable in public data), carried in every row's assumption field.

The quantum net (first-year feebate cost to the government) does NOT
depend on the PQP price basis; the flat forward model carries the
2027-12 cell PQP levels (129,800.16 Option A / 129,743.03 Option B)
through to 2028-12, used for context only.

Output: data/processed/renewal_cohort_banded_2028anchor.csv (same schema
as the base-case file; regime_start 2028-01-01 in every label).
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import date

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import config as cfg

W = cfg.WORKSPACE_ROOT
OUT = os.path.join(cfg.DIR_DATA_PROCESSED,
                   "renewal_cohort_banded_2028anchor.csv")
OMV_CSV = os.path.join(cfg.DIR_DATA_PROCESSED, "lta_omv_2018_avg.csv")

VINTAGE = cfg.transition_year_vintage(date(2028, 1, 1))  # 2018
REGIME = "2028-01-01"
OFFICIAL_A = 39877
OFFICIAL_B = 40216
ESHIFT_B_SHARES = [0.052711, 0.155384, 0.128298, 0.261736, 0.401871]

CUTPOINTS_PROPOSED = {"OptionA": [28877, 36062],
                      "OptionB": [20310, 28877, 36062, 49662]}
PERCENTILES = {"OptionA": [35, 50], "OptionB": [10, 35, 50, 75]}
QUANTUMS = {"OptionA": cfg.FEEBATE_QUANTUMS_OPTION_A,
            "OptionB": cfg.FEEBATE_QUANTUMS_OPTION_B}
BAND_LABELS = {"OptionA": ["0-35th", "35-50th", ">50th"],
               "OptionB": ["0-10th", "10-35th", "35-50th", "50-75th", ">75th"]}

COV_NOTE = ""

MIX_SOURCE = ("make/fuel mix: data.gov.sg registrations 2018-01..2018-12 (LTA, "
              "Batch B, sha256 in provenance.md s.1); model-level OMV: LTA "
              "OneMotoring Average-OMV 2018 edition (verification/"
              "lta_omv_2018_page.html, fetched 2026-11-01 after "
              "00:00-08:00 SGT maintenance); equal within-make model "
              "allocation (approximation)")


def mix_source() -> str:
    return MIX_SOURCE + (f"; {COV_NOTE}" if COV_NOTE else "")


DATA_WINDOW = "2018-01..2018-12 (OBSERVED registrations + LTA 2018 OMV edition)"
ASSUME = ("assumption: full 2018 cohort renews in transition year 2028 (upper "
          "bound — inter-term de-registrations 2018..2028 not observable in "
          "public data); 2028-start SENSITIVITY (base case is 2027-01-01, "
          "vintage 2017)")


def parse_omv(s: str) -> float:
    return float(s.replace("S$", "").replace(",", "").strip())


def parse_page() -> pd.DataFrame:
    """Parse the archived LTA 2018 OMV page (hidden-input encoding,
    identical scheme to the 2017 edition, suffix _2018)."""
    h = open(os.path.join(cfg.DIR_VERIFICATION,
                          "lta_omv_2018_page.html"),
             encoding="utf-8", errors="replace").read()
    makes = {}
    for n, m, name in re.findall(
            r'id="brandValue_make-(\d+)_(\d+)_2018"[^>]*value="([^"]*)"', h):
        makes[(int(n), int(m))] = name
    models, omvs = {}, {}
    for k, n, m, name in re.findall(
            r'id="modelValue_model-(\d+)_make-(\d+)_(\d+)_2018"[^>]*value="([^"]*)"', h):
        models[(int(k), int(n), int(m))] = name
    for k, n, m, val in re.findall(
            r'id="averageOmv_model-(\d+)_make-(\d+)_(\d+)_2018"[^>]*value="([^"]*)"', h):
        omvs[(int(k), int(n), int(m))] = parse_omv(val)
    rows = []
    for (k, n, m), name in models.items():
        if (k, n, m) in omvs and (n, m) in makes:
            rows.append({"month": m, "make": makes[(n, m)],
                         "model": name, "omv": omvs[(k, n, m)]})
    df = pd.DataFrame(rows)
    return df[["month", "make", "model", "omv"]]


def band_of(omv: float, cutpoints: list) -> int:
    b = 1
    for i, c in enumerate(cutpoints, start=1):
        if omv > c:
            b = i + 1
    return b


def weighted_quantile(omv: np.ndarray, w: np.ndarray, p: float) -> float:
    order = np.argsort(omv)
    omv_s, w_s = omv[order], w[order]
    cum = np.cumsum(w_s) / w_s.sum()
    return float(omv_s[cum >= p / 100.0][0])


def main() -> None:
    # 1. LTA 2018 OMV edition
    if not os.path.exists(OMV_CSV):
        parse_page().to_csv(OMV_CSV, index=False)
    omv_long = pd.read_csv(OMV_CSV)
    omv = (omv_long.groupby(["make", "model"])["omv"]
             .mean().reset_index()
             .rename(columns={"omv": "omv_vintage_2018"}))
    print(f"LTA 2018 OMV edition: {omv_long.shape[0]} model-month rows, "
          f"{omv.shape[0]} distinct models, "
          f"months {omv_long.month.min()}-{omv_long.month.max()}")

    # 2. 2018 make mix
    reg = pd.read_csv(os.path.join(cfg.DIR_DATA_RAW, "registrations.csv"))
    y = reg[reg.month.str.startswith("2018") & reg.number.notna()].copy()
    make_mix = y.groupby("make").number.sum().sort_values(ascending=False)
    total = int(make_mix.sum())
    print(f"2018 car registrations: {total:,} (makes: {len(make_mix)})")

    # 3. Equal within-make allocation
    omv["make"] = omv.make.str.upper()
    make_mix.index = make_mix.index.str.upper()
    alloc = []
    for make, cnt in make_mix.items():
        sub = omv[omv.make == make]
        if sub.shape[0] == 0:
            continue
        per = cnt / sub.shape[0]
        for r in sub.itertuples():
            alloc.append({"make": make, "model": r.model,
                          "omv": float(r.omv_vintage_2018), "n_alloc": per})
    a = pd.DataFrame(alloc)
    covered = a["n_alloc"].sum()
    n_uncovered = len(make_mix) - a.make.nunique()
    print(f"allocation: {covered:,.0f}/{total:,} ({covered/total*100:.2f}%) "
          f"covered; {n_uncovered} makes absent from 2018 edition")

    # 4. Class proxy + scale to official A/B
    def cc_of(name: str):
        m = re.search(r"--(\d{2,5})cc", name, re.I)
        return int(m.group(1)) if m else None

    a["cc"] = a.model.map(cc_of)
    a["is_ev"] = a.model.str.upper().str.contains("ELECTRIC| EV|EV ", regex=True)
    a.loc[a.cc.isna() & a.is_ev, "cc"] = 0
    a.loc[a.cc.isna() & ~a.is_ev, "cc"] = 2000
    a["class_proxy"] = np.where(a.cc <= 1600, "A", "B")
    s_a = OFFICIAL_A / a.loc[a.class_proxy == "A", "n_alloc"].sum()
    s_b = OFFICIAL_B / a.loc[a.class_proxy == "B", "n_alloc"].sum()
    a["count_A"] = np.where(a.class_proxy == "A", a.n_alloc * s_a, 0.0)
    a["count_B"] = np.where(a.class_proxy == "B", a.n_alloc * s_b, 0.0)
    e_resid = total - OFFICIAL_A - OFFICIAL_B
    e_per = {i: s for i, s in enumerate(ESHIFT_B_SHARES, start=1)}
    print(f"class proxy scaled to official A={OFFICIAL_A:,} B={OFFICIAL_B:,}; "
          f"E residual {e_resid:,}")

    # 5. Banding: base (PROPOSED) + vintage-pct sensitivity
    w = a["n_alloc"].values
    omvs = a.omv.values
    vintage_cuts = {opt: [weighted_quantile(omvs, w, p) for p in PERCENTILES[opt]]
                    for opt in PERCENTILES}
    print("vintage-year (2018) percentile cut points:",
          {k: [round(v, 0) for v in v] for k, v in vintage_cuts.items()})

    global COV_NOTE
    COV_NOTE = (f"coverage {covered/total*100:.2f}% of 2018 registrations "
                f"({n_uncovered} makes not in LTA 2018 edition excluded)")

    cohort_volume = OFFICIAL_A + OFFICIAL_B + e_resid
    rows = []
    for basis, cuts_opt in (("PROPOSED_2025pct", CUTPOINTS_PROPOSED),
                            ("VINTAGE_2018pct", vintage_cuts)):
        for opt in ("OptionA", "OptionB"):
            cuts = cuts_opt[opt]
            a["band"] = a.omv.map(lambda v: band_of(v, cuts))
            for b in range(1, len(cuts) + 2):
                sub = a[a.band == b]
                for cls, col, official in (("pre_A", "count_A", OFFICIAL_A),
                                           ("pre_B", "count_B", OFFICIAL_B)):
                    n_cls = float(sub[col].sum())
                    rows.append(_row(basis, opt, b, cls, n_cls, sub, cuts,
                                     cohort_volume))
                if opt == "OptionB":
                    e_b = e_per[b] * e_resid
                else:
                    ab = {1: (1, 2), 2: (3,), 3: (4, 5)}[b]
                    e_b = sum(e_per[x] for x in ab) * e_resid
                rows.append(_row(basis, opt, b, "E_residual", e_b, sub, cuts,
                                 cohort_volume))
            rows.append(_row_all(basis, opt, cuts, a, cohort_volume))
    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)

    # 6. Console summary (quantum net = first-year feebate cost to govt)
    print(f"\nvintage {VINTAGE} (= {REGIME[:4]} - 10 yr COE term); "
          f"volume {cohort_volume:,}")
    for basis in ("PROPOSED_2025pct", "VINTAGE_2018pct"):
        print(f"\n--- basis {basis} ---")
        for opt in ("OptionA", "OptionB"):
            s = out[(out.cutpoint_basis == basis) & (out.option == opt)
                    & (out.cohort_class == "ALL")]
            parts = [f"{r.band}:{r.registrations:,.0f}" for r in s.itertuples()]
            print(f"{opt} ALL: " + "  ".join(parts))
            s2 = out[(out.cutpoint_basis == basis) & (out.option == opt)
                     & (out.cohort_class != "ALL")]
            s2 = s2[s2.band != "ALL"].copy()
            s2["band_i"] = s2.band.astype(int)
            s2["quantum"] = s2.band_i.map(lambda b: QUANTUMS[opt][b - 1])
            net = (s2.registrations * s2.quantum).sum()
            print(f"{opt} net quantum, basis {basis}: "
                  f"{net/1e6:+,.1f}M over {cohort_volume:,} = "
                  f"{net/cohort_volume:+,.0f}/car")
    print(f"\nWrote {OUT} ({out.shape[0]} rows)")


def _row(basis, opt, b, cls, n, sub, cuts, cohort_volume) -> dict:
    return {
        "vintage": VINTAGE,
        "vintage_derivation": f"{REGIME[:4]} - {cfg.INITIAL_COE_TERM_YEARS} (initial COE term)",
        "cutpoint_basis": basis,
        "option": opt,
        "band": b,
        "band_label": BAND_LABELS[opt][b - 1],
        "quantum_sgd": QUANTUMS[opt][b - 1],
        "cutpoints_sgd": json.dumps(cuts),
        "cohort_class": cls,
        "registrations": round(float(n), 2),
        "avg_omv_sgd": round(float(sub.omv.mean()), 2) if sub.shape[0] else np.nan,
        "cohort_volume": cohort_volume,
        "mix_source": mix_source(),
        "data_window": DATA_WINDOW,
        "assumption": ASSUME,
        "label": cfg.output_label(cfg.TYPE_SCENARIO,
                                  scenario=f"renewal_cohort_{opt}_{basis}_2028start",
                                  data_window=DATA_WINDOW,
                                  citation="LTA 2018 statistics + LTA OMV 2018 edition; "
                                          "PROPOSED cut points (paper s2.18) or vintage-pct variant; "
                                          "2028-start SENSITIVITY (base case 2027-01-01)"),
        "value_type": cfg.TYPE_SCENARIO,
        "scenario": f"renewal_cohort_{opt}_{basis}_2028start",
        "regime_start": REGIME,
        "citation": "see label",
    }


def _row_all(basis, opt, cuts, a, cohort_volume) -> dict:
    n = cohort_volume
    return {
        "vintage": VINTAGE,
        "vintage_derivation": f"{REGIME[:4]} - {cfg.INITIAL_COE_TERM_YEARS} (initial COE term)",
        "cutpoint_basis": basis,
        "option": opt,
        "band": "ALL",
        "band_label": "all bands",
        "quantum_sgd": None,
        "cutpoints_sgd": json.dumps(cuts),
        "cohort_class": "ALL",
        "registrations": n,
        "avg_omv_sgd": round(float(a.omv.mean()), 2),
        "cohort_volume": n,
        "mix_source": mix_source(),
        "data_window": DATA_WINDOW,
        "assumption": ASSUME,
        "label": cfg.output_label(cfg.TYPE_SCENARIO,
                                  scenario=f"renewal_cohort_{opt}_{basis}_2028start",
                                  data_window=DATA_WINDOW,
                                  citation="LTA 2018 statistics + LTA OMV 2018 edition; "
                                          "2028-start SENSITIVITY (base case 2027-01-01)"),
        "value_type": cfg.TYPE_SCENARIO,
        "scenario": f"renewal_cohort_{opt}_{basis}_2028start",
        "regime_start": REGIME,
        "citation": "see label",
    }


if __name__ == "__main__":
    main()
