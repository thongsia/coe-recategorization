"""Step 13 (part 1) — Renewal cohort banding at the derived vintage (Batch F).

Vintage derivation: regime start 2027-01-01 (config) minus the 10-year
initial COE term => first-renewal cohort vintage = 2017 (stated in every
label). The 2016 cohort renews in 2026, PRE-regime, and is EXCLUDED.

Cohort volume: 91,922 passenger cars registered in 2017 (OBSERVED,
data.gov.sg LTA registration resource d_d3f4d708... fetched and
reconciled in Batch B; make/fuel/vehicle_type level, 2017-01..2017-12).
Cross-check: LTA official 2017 Category A + B new registrations =
46,076 + 45,699 = 91,775 (OBSERVED, LTA Annual Vehicle Statistics
2025 edition, verification/MVP02-1_New_Reg_by_COE.pdf) — residual
147 = cars registered under the open Category E (computed).

Data source chain (documented in provenance.md s.9):
  (1) Historical 'Cost for Cars Registered' PDF editions for ~2017 on
      onemotoring.lta.gov.sg — NOT AVAILABLE (URL-pattern probes 404;
      LTA statistics page lists only the latest edition M032 Aug 2026).
  (2) LTA OneMotoring 'Average OMV of New Cars Registered' year=2017
      edition — AVAILABLE (fetched 2026-10-22T18:30:38Z, archived
      verification/lta_omv_2017_page.html, sha256
      1e5214db59adfb566128e165af8e55a18f57f1683539ecce83809fb5cac1506e);
      model-level average OMVs, 2017-01..2017-12.
  (3) LTA 2017 annual registration statistics — make/fuel mix from
      data/raw/registrations.csv 2017 slice (Batch B resource); COE
      class split from verification/MVP02-1_New_Reg_by_COE.pdf (2017 row).
  (4) 2025 mix fallback NOT needed (fallback_used = false).

Model-level allocation (documented approximation): each 2017 make's
registration count is split EQUALLY across that make's models in the
LTA 2017 OMV edition (no public model-level 2017 registration counts
exist; the edition carries OMVs only).

Pre-A / pre-B cohort split: OFFICIAL LTA 2017 A/B counts (46,076 /
45,699), NOT a proxy — model-level classes are assigned with the
2017-era rule (cc <= 1,600cc => A else B; engine displacement parsed
from the LTA 2017 model names; MPO criterion unobservable — stated
approximation) and then scaled to match the official totals exactly.
The 147 E-registered residual is banded with the Batch E
Category-B-skewed E-shift composition (documented).

Banding:
  base = PROPOSED cut points (2025-registration percentiles, paper
         s2.18 Tables 1/2) — scenario-consistent with Batches C/D/E;
  sensitivity = vintage-year (2017) percentile cut points computed from
         the vintage cohort's own weighted OMV distribution (the
         paper's annual-review mechanism applied one year late).

Output: data/processed/renewal_cohort_banded.csv (vintage, mix source,
band, data window, cohort volume all recorded).
"""
from __future__ import annotations

import json
import os
import re
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import config as cfg

W = cfg.WORKSPACE_ROOT
OUT = os.path.join(cfg.DIR_DATA_PROCESSED, "renewal_cohort_banded.csv")
OMV_PAGE = os.path.join(cfg.DIR_VERIFICATION, "lta_omv_2017_page.html")
OMV_CSV = os.path.join(cfg.DIR_DATA_PROCESSED, "lta_omv_2017_avg.csv")

VINTAGE = cfg.TRANSITION_YEAR_VINTAGE          # 2017
REGIME = cfg.REGIME_START_DATE.isoformat()     # 2027-01-01
OFFICIAL_A = 46076
OFFICIAL_B = 45699
# Batch E E-shift composition (Option B percentile bands), for the E residual
ESHIFT_B_SHARES = [0.052711, 0.155384, 0.128298, 0.261736, 0.401871]
E_RESIDUAL_B = [337.35, 994.46, 821.11, 1675.11, 2571.97]  # per 6400/yr

CUTPOINTS_PROPOSED = {"OptionA": [28877, 36062],
                      "OptionB": [20310, 28877, 36062, 49662]}
PERCENTILES = {"OptionA": [35, 50], "OptionB": [10, 35, 50, 75]}
QUANTUMS = {"OptionA": cfg.FEEBATE_QUANTUMS_OPTION_A,
            "OptionB": cfg.FEEBATE_QUANTUMS_OPTION_B}
BAND_LABELS = {"OptionA": ["0-35th", "35-50th", ">50th"],
               "OptionB": ["0-10th", "10-35th", "35-50th", "50-75th", ">75th"]}

COV_NOTE = ""  # set in main()

MIX_SOURCE = ("make/fuel mix: data.gov.sg registrations 2017-01..2017-12 (LTA, "
              "Batch B, sha256 in provenance.md s.1); model-level OMV: LTA "
              "OneMotoring Average-OMV 2017 edition (verification/"
              "lta_omv_2017_page.html); equal within-make model allocation "
              "(approximation)")


def mix_source() -> str:
    return MIX_SOURCE + (f"; {COV_NOTE}" if COV_NOTE else "")
DATA_WINDOW = "2017-01..2017-12 (OBSERVED registrations + LTA 2017 OMV edition)"
ASSUME = ("assumption: full 2017 cohort renews in transition year 2027 (upper "
          "bound — inter-term de-registrations 2017..2027 not observable in public data)")


def parse_omv(s: str) -> float:
    return float(s.replace("S$", "").replace(",", "").strip())


def parse_page() -> pd.DataFrame:
    """Parse the archived LTA 2017 OMV page (hidden-input encoding).

    Inputs are keyed by their id attributes:
      id="monthValue_M_2017"                 value=month number
      id="brandValue_make-N_M_2017"          value=make name
      id="modelValue_model-K_make-N_M_2017"  value=model name
      id="averageOmv_model-K_make-N_M_2017"  value=OMV (S$...)
    A model and its OMV share (K, N, M); a make is (N, M).
    """
    h = open(OMV_PAGE, encoding="utf-8", errors="replace").read()

    months = dict(re.findall(
        r'id="monthValue_(\d+)_2017"[^>]*value="(\d+)"', h))
    makes = {}
    for n, m, name in re.findall(
            r'id="brandValue_make-(\d+)_(\d+)_2017"[^>]*value="([^"]*)"', h):
        makes[(int(n), int(m))] = name
    models, omvs = {}, {}
    for k, n, m, name in re.findall(
            r'id="modelValue_model-(\d+)_make-(\d+)_(\d+)_2017"[^>]*value="([^"]*)"', h):
        models[(int(k), int(n), int(m))] = name
    for k, n, m, val in re.findall(
            r'id="averageOmv_model-(\d+)_make-(\d+)_(\d+)_2017"[^>]*value="([^"]*)"', h):
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
    # ----------------------------------------------------------
    # 1. LTA 2017 OMV edition -> model level
    # ----------------------------------------------------------
    if not os.path.exists(OMV_CSV):
        omv_long = parse_page()
        omv_long.to_csv(OMV_CSV, index=False)
        n_models_long = omv_long.shape[0]
    else:
        omv_long = pd.read_csv(OMV_CSV)
        n_models_long = omv_long.shape[0]
    omv = (omv_long.groupby(["make", "model"])["omv"]
             .mean().reset_index()
             .rename(columns={"omv": "omv_vintage_2017"}))
    n_models = omv.shape[0]
    print(f"LTA 2017 OMV edition: {n_models_long} model-month rows, "
          f"{n_models} distinct models, months {omv_long.month.min()}-{omv_long.month.max()}")

    # ----------------------------------------------------------
    # 2. 2017 make mix (OBSERVED)
    # ----------------------------------------------------------
    reg = pd.read_csv(os.path.join(cfg.DIR_DATA_RAW, "registrations.csv"))
    y = reg[reg.month.str.startswith("2017") & reg.number.notna()].copy()
    make_mix = y.groupby("make").number.sum().sort_values(ascending=False)
    total = int(make_mix.sum())
    print(f"2017 car registrations: {total:,} (makes: {len(make_mix)})")

    # ----------------------------------------------------------
    # 3. Equal within-make model allocation
    # ----------------------------------------------------------
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
                          "omv": float(r.omv_vintage_2017), "n_alloc": per})
    a = pd.DataFrame(alloc)
    covered = a["n_alloc"].sum()
    n_uncovered_makes = len(make_mix) - a.make.nunique()
    print(f"allocation: {covered:,.0f}/{total:,} ({covered/total*100:.2f}%) covered; "
          f"{n_uncovered_makes} makes absent from 2017 edition")

    # ----------------------------------------------------------
    # 4. Model class (2017-era rule) + scale to official A/B
    # ----------------------------------------------------------
    def cc_of(name: str):
        m = re.search(r"--(\d{2,5})cc", name, re.I)
        return int(m.group(1)) if m else None

    a["cc"] = a.model.map(cc_of)
    a["is_ev"] = a.model.str.upper().str.contains("ELECTRIC| EV|EV ", regex=True)
    no_cc = a.cc.isna()
    a.loc[a.cc.isna() & a.is_ev, "cc"] = 0          # EV -> <=1600cc branch -> A
    a.loc[a.cc.isna() & ~a.is_ev, "cc"] = 2000      # unparseable non-EV -> B (stated)
    a["class_proxy"] = np.where(a.cc <= 1600, "A", "B")
    n_no_cc = int(no_cc.sum())

    np_a = a.loc[a.class_proxy == "A", "n_alloc"].sum()
    np_b = a.loc[a.class_proxy == "B", "n_alloc"].sum()
    s_a, s_b = OFFICIAL_A / np_a, OFFICIAL_B / np_b
    a["count_A"] = np.where(a.class_proxy == "A", a["n_alloc"] * s_a, 0.0)
    a["count_B"] = np.where(a.class_proxy == "B", a["n_alloc"] * s_b, 0.0)
    print(f"class proxy: {n_no_cc} models w/o cc suffix; scaled to official "
          f"A={OFFICIAL_A:,} B={OFFICIAL_B:,}")

    # E residual banded with Batch E B-skewed composition (per 6400 -> per 1)
    e_resid = total - OFFICIAL_A - OFFICIAL_B
    e_per = {i: c / 6400.0 for i, c in enumerate(E_RESIDUAL_B, start=1)}

    # ----------------------------------------------------------
    # 5. Banding: base (PROPOSED) + vintage-pct sensitivity
    # ----------------------------------------------------------
    w = a["n_alloc"].values
    omvs = a.omv.values
    vintage_cuts = {opt: [weighted_quantile(omvs, w, p) for p in PERCENTILES[opt]]
                    for opt in PERCENTILES}
    print("vintage-year (2017) percentile cut points:",
          {k: [round(v, 0) for v in v] for k, v in vintage_cuts.items()})

    rows = []
    global COV_NOTE
    COV_NOTE = (f"coverage {covered/total*100:.2f}% of 2017 registrations "
                f"({n_uncovered_makes} makes not in LTA 2017 edition excluded)")
    for basis, cuts_opt in (("PROPOSED_2025pct", CUTPOINTS_PROPOSED),
                            ("VINTAGE_2017pct", vintage_cuts)):
        for opt in ("OptionA", "OptionB"):
            cuts = cuts_opt[opt]
            a["band"] = a.omv.map(lambda v: band_of(v, cuts))
            for b in range(1, len(cuts) + 2):
                sub = a[a.band == b]
                for cls, col, official in (("pre_A", "count_A", OFFICIAL_A),
                                           ("pre_B", "count_B", OFFICIAL_B)):
                    n_cls = float(sub[col].sum())
                    rows.append(_row(basis, opt, b, cls, n_cls, sub, cuts))
                # E residual: Batch E composition aggregated to this option's bands
                if opt == "OptionB":
                    e_b = e_per[b] * e_resid
                else:
                    # aggregate B percentile bands -> A bands
                    ab = {1: (1, 2), 2: (3,), 3: (4, 5)}[b] if opt == "OptionA" else (b,)
                    e_b = sum(e_per[x] for x in ab) * e_resid
                rows.append(_row(basis, opt, b, "E_residual", e_b, sub, cuts))
            # ALL rows
            rows.append(_row_all(basis, opt, cuts, a))
    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)

    # ----------------------------------------------------------
    # 6. Console summary
    # ----------------------------------------------------------
    print(f"\nvintage {VINTAGE} (= {REGIME[:4]} - 10 yr COE term); volume {total:,}")
    for basis in ("PROPOSED_2025pct", "VINTAGE_2017pct"):
        print(f"\n--- basis {basis} ---")
        for opt in ("OptionA", "OptionB"):
            s = out[(out.cutpoint_basis == basis) & (out.option == opt)
                    & (out.cohort_class == "ALL")]
            parts = [f"{r.band}:{r.registrations:,.0f}" for r in s.itertuples()]
            print(f"{opt} ALL: " + "  ".join(parts))
    print(f"\nWrote {OUT} ({out.shape[0]} rows)")
    print(f"fallback_used = False (2025 mix not needed)")


def _row(basis, opt, b, cls, n, sub, cuts) -> dict:
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
        "cohort_volume": 91922,
        "mix_source": mix_source(),
        "data_window": DATA_WINDOW,
        "assumption": ASSUME,
        "label": cfg.output_label(cfg.TYPE_COMPUTED,
                                  scenario=f"renewal_cohort_{opt}_{basis}",
                                  data_window=DATA_WINDOW,
                                  citation="LTA 2017 statistics + LTA OMV 2017 edition; "
                                          "PROPOSED cut points (paper s2.18) or vintage-pct variant"),
        "value_type": cfg.TYPE_COMPUTED,
        "scenario": f"renewal_cohort_{opt}_{basis}",
        "data_window": DATA_WINDOW,
        "citation": "see label",
    }


def _row_all(basis, opt, cuts, a) -> dict:
    n = int(OFFICIAL_A + OFFICIAL_B) + 147
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
        "label": cfg.output_label(cfg.TYPE_COMPUTED,
                                  scenario=f"renewal_cohort_{opt}_{basis}",
                                  data_window=DATA_WINDOW,
                                  citation="LTA 2017 statistics + LTA OMV 2017 edition"),
        "value_type": cfg.TYPE_COMPUTED,
        "scenario": f"renewal_cohort_{opt}_{basis}",
        "data_window": DATA_WINDOW,
        "citation": "see label",
    }


if __name__ == "__main__":
    main()
