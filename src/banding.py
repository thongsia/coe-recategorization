#!/usr/bin/env python3
"""
Step 5 — Feebate banding reconstruction (src/banding.py).

PURPOSE
-------
Reconstruct LTA's indicative feebate banding of car models (consultation
paper Tables 1/2, "based on 2025 registrations") from public data, and band
every model in the Aug-2026 Car Cost catalog under both PROPOSED options:

  Option A: 3 bands  — cut points at the 35th / 50th OMV percentiles of
                       2025 registrations; quantums -15000 / 0 / +15000.
  Option B: 5 bands  — cut points at the 10th / 35th / 50th / 75th OMV
                       percentiles; quantums -15000 / -7500 / 0 / +7500 /
                       +15000.

(Percentiles and quantums are PROPOSED parameters from the paper §2.15-2.18,
pp.10-12; the banding of models is a COMPUTED reconstruction — LTA will
publish the actual table annually, §2.16.)

OMV-DISTRIBUTION SOURCE DECISION (verified 2026-10-22; see provenance.md)
-------------------------------------------------------------------------
PRIMARY CANDIDATE = "LTA 2025 annual vehicle statistics". Verification
result: LTA's statistics page (lta.gov.sg/.../statistics.html) lists, under
"Car/Motorcycle Cost", "Average OMV of New Cars Registered" -> the OneMotoring
OMV page
  https://onemotoring.lta.gov.sg/content/onemotoring/home/buying/
  upfront-vehicle-costs/open-market-value--omv-.html
The 2025 EDITION was fetched and parsed (embedded in the page HTML as hidden
inputs; raw page archived to verification/lta_omv_2025_page.html, parsed
long format to data/processed/lta_omv_2025_avg.csv):
  * MODEL-LEVEL detail: 3,366 (month, make, model) rows; all 12 months of
    2025; 50 makes; 222-359 distinct models per month; "average OMV of
    commonly-registered car models".
  * COVERAGE LIMITS: no registration COUNTS per model, and only commonly
    registered models (not the full population).
All other LTA annual vehicle statistics are MAKE-level only and carry no OMV.
=> No public LTA source combines 2025 model-level OMV with 2025 model-level
registration counts, so the primary source cannot, standing alone, produce the
weighted OMV percentile distribution the plan requires.

DECISION (first-class fallback per plan; documented in provenance.md and
methodology_notes.md): the banding distribution is built from the plan's
labelled fallback —
  Jan-May 2025 MAKE-LEVEL registration mix (frozen window 2025-01..2025-05,
  data.gov.sg resource d_d3f4d708e1d0a37b4365414e2fad3a07)
  x CURRENT Car Cost catalog model composition
    (data/processed/car_cost_aug2026.csv, 217 models, OMV per model),
labelled as a FALLBACK APPROXIMATION on every output. The LTA 2025 edition is
used as an EXTERNAL CHECK:
  * OMV cross-check for catalog models present in the 2025 edition
    (data/processed/lta_omv_2025_crosscheck.csv, auxiliary);
  * sensitivity cut points with LTA-2025 OMV (matched models) and with
    uniform (unweighted) model weights.

METHOD
------
1. Mix: registrations.csv, months 2025-01..2025-05, valid rows (number not
   null; null = zero/unreported cell per Batch B provenance). 52 makes,
   19,318 registrations.
2. Pool: the 217 catalog models. Each make's mix weight is split EQUALLY
   across that make's catalog models (no public model-level counts exist).
   Makes absent from the catalog (21 makes, ~1.3% of the mix — mostly
   low-volume luxury/special makes) are excluded from the pool; shares are
   normalised within the covered pool and the coverage is stamped on every
   output.
3. OMV per model: catalog avg_omv (comma-formatted strings parsed).
4. Cut points: weighted (by the pool weights) NEAREST-RANK percentile of the
   pool OMV distribution — the smallest OMV value v with cumulative weight
   >= p (Option A: p=35,50; Option B: p=10,35,50,75).
5. Banding rule (documented): each band is (c_{k-1}, c_k] — upper-inclusive
   at the cut point — with the top band (c_last, inf); a model with OMV
   exactly at a cut point falls in the LOWER band ending at that cut point
   (consistent with the paper's '0-35th' / '35-50th' / '>50th' labels).
6. Band shares: pool weight per band (sums to 100% within the pool —
   cross-foot asserted in code), plus model counts and estimated registration
   counts per band (band weight x covered registrations, Jan-May 2025,
   annualised x12/5 as a separate labelled column).
7. Cross-validation: the paper's "typical models" (Table 1 Option A: 30
   entries; Table 2 Option B: 30 entries; 24 unique models) are matched to
   an explicit OMV source (catalog model where the model family is listed in
   the Aug-2026 catalog; LTA-2025 edition mean OMV where it is not — the 6
   families absent from the current catalog edition), banded against the
   reconstructed cut points, and compared to the paper's band. Every entry
   is enumerated in tables/banding_mismatches.csv with the match/mismatch
   verdict; the agreement rate is stated per option. Family-level typical
   models are resolved to the entry (base) catalog variant; the variant
   OMV spread is reported so any variant-band flips are visible.

LABELING
--------
Every row carries config.output_label() stamps: value_type=COMPUTED,
scenario tag (OptionA / OptionB), data-window tag (frozen 2025-01..2025-05
mix), PROPOSED citation for the percentiles/quantums, and the explicit
"RECONSTRUCTION approximating LTA's eventual banding; FALLBACK APPROXIMATION
(Jan-May 2025 make-level mix x current catalog composition)" statement.

OUTPUTS (tables/)
-----------------
banding_cutpoints.csv, banding_models_optionA.csv, banding_models_optionB.csv,
banding_shares.csv, banding_mismatches.csv,
+ auxiliary: data/processed/lta_omv_2025_crosscheck.csv
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config  # noqa: E402

WS = config.WORKSPACE_ROOT
TBL = config.DIR_TABLES
os.makedirs(TBL, exist_ok=True)

# --------------------------------------------------------------------------
# Load inputs
# --------------------------------------------------------------------------
def load_inputs():
    reg = pd.read_csv(os.path.join(config.DIR_DATA_RAW, "registrations.csv"))
    cat = pd.read_csv(os.path.join(config.DIR_DATA_PROCESSED,
                                   "car_cost_aug2026.csv"))
    lta = pd.read_csv(os.path.join(config.DIR_DATA_PROCESSED,
                                   "lta_omv_2025_avg.csv"))
    return reg, cat, lta


def parse_omv(s):
    return float(str(s).replace(",", ""))


def build_mix(reg: pd.DataFrame) -> pd.Series:
    """Make-level passenger-car registrations for the frozen window
    2025-01..2025-05 (valid rows only). The registrations dataset is
    car-only (all vehicle_type values are car body styles)."""
    win = reg[(reg.month >= "2025-01") & (reg.month <= "2025-05")
              & reg.number.notna()]
    mix = win.groupby("make")["number"].sum()
    return mix.sort_values(ascending=False)


def build_pool(cat: pd.DataFrame, mix: pd.Series):
    """Weighted model pool: catalog models, weight = make's Jan-May 2025 mix
    share split equally across the make's catalog models. Returns
    (pool df, coverage dict)."""
    pool = cat.copy()
    pool["omv"] = pool.avg_omv.map(parse_omv)
    mix_upper = mix.rename(lambda m: str(m).upper()).to_dict()
    make_counts = pool.groupby("make").size()
    covered_mix = mix[[str(m).upper() in set(pool.make.str.upper())
                       for m in mix.index]]
    cov = {
        "mix_total_reg": int(mix.sum()),
        "mix_covered_reg": int(covered_mix.sum()),
        "coverage_pct": float(covered_mix.sum() / mix.sum() * 100),
        "n_make_mix": int(len(mix)),
        "n_make_covered": int(len(covered_mix)),
        "n_make_uncovered": int(len(mix) - len(covered_mix)),
        "uncovered_makes": sorted(
            m for m in mix.index if str(m).upper()
            not in set(pool.make.str.upper())),
    }
    w = []
    for _, r in pool.iterrows():
        m = str(r.make).upper()
        n_models = int(make_counts[r.make])
        # makes absent from the Jan-May 2025 mix (e.g. new 2026 catalog
        # makes) carry zero weight; their models remain in the banding
        # table but contribute no mass to the distribution.
        w.append(float(mix_upper.get(m, 0.0)) / n_models)
    pool["reg_weight"] = w
    total = pool.reg_weight.sum()
    pool["weight"] = pool.reg_weight / total
    return pool, cov


def weighted_quantile(omv: pd.Series, weight: pd.Series, p: float) -> float:
    """Nearest-rank weighted percentile: smallest value v with cumulative
    weight >= p (percent, 0-100)."""
    df = pd.DataFrame({"omv": omv, "w": weight}).sort_values("omv")
    cum = df.w.cumsum() / df.w.sum() * 100.0
    return float(df.omv[cum >= p].iloc[0])


def band_of(omv: float, cutpoints: list[float]) -> int:
    """1-based band index. Convention (documented): each band is
    (c_{k-1}, c_k] — UPPER-INCLUSIVE at the cut point — with the top band
    (c_last, inf). Rationale: the paper's band labels are '0-35th',
    '35-50th', '>50th' — a model whose OMV sits exactly at the k-th
    percentile belongs to the band ending at that percentile (the paper
    itself places BYD Sealion 7 Dynamic at the 50th percentile in the
    '35-50th' band, confirming the upper-inclusive reading)."""
    b = 1
    for c in cutpoints:
        if omv > c:
            b += 1
    return b


BAND_NAMES = {
    "OptionA": {
        1: ("0-35th", -15000), 2: ("35-50th", 0), 3: (">50th", 15000)},
    "OptionB": {
        1: ("0-10th", -15000), 2: ("10-35th", -7500), 3: ("35-50th", 0),
        4: ("50-75th", 7500), 5: (">75th", 15000)},
}
PERCENTILES = {
    "OptionA": list(config.FEEBATE_PERCENTILES_OPTION_A),   # [35, 50]
    "OptionB": list(config.FEEBATE_PERCENTILES_OPTION_B),   # [10, 35, 50, 75]
}
QUANTUMS = {
    "OptionA": list(config.FEEBATE_QUANTUMS_OPTION_A),
    "OptionB": list(config.FEEBATE_QUANTUMS_OPTION_B),
}

FALLBACK_STATEMENT = (
    "RECONSTRUCTION approximating LTA's eventual banding; FALLBACK "
    "APPROXIMATION (Jan-May 2025 make-level mix x current Car Cost catalog "
    "composition); LTA 2025 OMV edition used as external check only"
)


def label(opt: str, citation: str) -> str:
    return config.output_label(
        config.TYPE_COMPUTED,
        scenario=opt,
        data_window=config.data_window_tag(),
        citation=citation,
    )


# --------------------------------------------------------------------------
# Typical-model cross-validation (paper Tables 1/2)
# --------------------------------------------------------------------------
# (band, paper band label, typical model, omv source, model key)
#  source: "catalog" -> key is the exact catalog `model` string
#          "lta2025" -> key is matched against data/processed/
#                       lta_omv_2025_avg.csv `model` (mean of all months/suffix
#                       variants of the same model name)
TYPICAL = {
    "OptionA": [
        (1, "0-35th", "BYD Atto 3", "catalog", "ATTO 3 EXTENDED RANGE"),
        (1, "0-35th", "BYD E6", "lta2025", "E6 7-SEATER"),
        (1, "0-35th", "Honda Freed", "catalog", "FREED 1.5 HE7-S E:HEV"),
        (1, "0-35th", "Honda Jazz", "catalog", "JAZZ 1.5 CROSSTAR E:HEV"),
        (1, "0-35th", "Hyundai Kona 1.6 HEV", "catalog", "SX2 KONA 1.6 GDI HEV"),
        (1, "0-35th", "Mazda 3", "catalog", "MAZDA3 4DR 1.5 AT M-HEV EXECUTIVE I4RC"),
        (1, "0-35th", "MG S5", "catalog", "MGS5 EV LUXURY"),
        (1, "0-35th", "Nissan Note", "catalog", "NOTE E-POWER 1.2L PREMIUM"),
        (1, "0-35th", "Suzuki Swift", "catalog", "SWIFT 1.2 GLX CVT"),
        (1, "0-35th", "Toyota Noah", "catalog", "NOAH HYBRID STANDARD"),
        (1, "0-35th", "Toyota Sienta", "catalog", "SIENTA HYBRID"),
        (1, "0-35th", "Volvo EX30 110kW", "catalog", "EX30 PLUS"),
        (2, "35-50th", "Audi A3", "catalog", "A3 SEDAN S LINE 1.5 TFSI (85 KW)"),
        (2, "35-50th", "BYD Sealion 7 Dynamic", "catalog", "SEALION 7 DYNAMIC"),
        (2, "35-50th", "Honda Civic 1.5 Turbo", "lta2025", "CIVIC 1.5L TURBO DOHC VTEC"),
        (2, "35-50th", "Nissan Serena", "catalog", "SERENA E-POWER 7S HIGHWAY STAR PRESTIGE"),
        (2, "35-50th", "Toyota Corolla Altis", "catalog", "COROLLA ALTIS 1.6 ELEGANCE"),
        (2, "35-50th", "Xpeng G6 RWD (STD Range)", "catalog", "G6 AIR RWD (STD)"),
        (3, ">50th", "Audi Q3", "catalog", "Q3 SUV TFSI"),
        (3, ">50th", "B.M.W. 216", "catalog", "216 GC MSPT ALED"),
        (3, ">50th", "B.M.W. iX2", "catalog", "IX2 EDRIVE20 MSPT ALED"),
        (3, ">50th", "BYD Sealion 7 Performance", "lta2025", "SEALION 7 PERFORMANCE"),
        (3, ">50th", "Denza D9", "catalog", "DENZA D9 ELITE"),
        (3, ">50th", "Honda Civic Type R", "lta2025", "CIVIC TYPE R FL5 JDM"),
        (3, ">50th", "Honda Odyssey", "lta2025", "ODYSSEY E:HEV ABSOLUTE 2.0"),
        (3, ">50th", "Mercedes Benz A180", "lta2025", "A180 SALOON PROGRESSIVE LN"),
        (3, ">50th", "Mercedes Benz GLC", "catalog", "GLC200 4MATIC SUV AVG"),
        (3, ">50th", "Tesla Model 3 RWD 110", "catalog", "MODEL 3 RWD 110"),
        (3, ">50th", "Tesla Model Y RWD", "catalog", "MODEL Y RWD 110"),
        (3, ">50th", "Toyota Alphard", "catalog", "ALPHARD HYBRID STANDARD (AUTO)"),
    ],
    "OptionB": [
        (1, "0-10th", "BYD E6", "lta2025", "E6 7-SEATER"),
        (1, "0-10th", "Honda Jazz", "catalog", "JAZZ 1.5 CROSSTAR E:HEV"),
        (1, "0-10th", "Mazda 3", "catalog", "MAZDA3 4DR 1.5 AT M-HEV EXECUTIVE I4RC"),
        (1, "0-10th", "MG S5", "catalog", "MGS5 EV LUXURY"),
        (1, "0-10th", "Nissan Note", "catalog", "NOTE E-POWER 1.2L PREMIUM"),
        (1, "0-10th", "Suzuki Swift", "catalog", "SWIFT 1.2 GLX CVT"),
        (2, "10-35th", "BYD Atto 3", "catalog", "ATTO 3 EXTENDED RANGE"),
        (2, "10-35th", "Honda Freed", "catalog", "FREED 1.5 HE7-S E:HEV"),
        (2, "10-35th", "Hyundai Kona 1.6 HEV", "catalog", "SX2 KONA 1.6 GDI HEV"),
        (2, "10-35th", "Toyota Noah", "catalog", "NOAH HYBRID STANDARD"),
        (2, "10-35th", "Toyota Sienta", "catalog", "SIENTA HYBRID"),
        (2, "10-35th", "Volvo EX30 110kW", "catalog", "EX30 PLUS"),
        (3, "35-50th", "Audi A3", "catalog", "A3 SEDAN S LINE 1.5 TFSI (85 KW)"),
        (3, "35-50th", "BYD Sealion 7 Dynamic", "catalog", "SEALION 7 DYNAMIC"),
        (3, "35-50th", "Honda Civic 1.5 Turbo", "lta2025", "CIVIC 1.5L TURBO DOHC VTEC"),
        (3, "35-50th", "Nissan Serena", "catalog", "SERENA E-POWER 7S HIGHWAY STAR PRESTIGE"),
        (3, "35-50th", "Toyota Corolla Altis", "catalog", "COROLLA ALTIS 1.6 ELEGANCE"),
        (3, "35-50th", "Xpeng G6 RWD (STD Range)", "catalog", "G6 AIR RWD (STD)"),
        (4, "50-75th", "Audi Q3", "catalog", "Q3 SUV TFSI"),
        (4, "50-75th", "B.M.W. 216", "catalog", "216 GC MSPT ALED"),
        (4, "50-75th", "BYD Sealion 7 Performance", "lta2025", "SEALION 7 PERFORMANCE"),
        (4, "50-75th", "Honda Odyssey", "lta2025", "ODYSSEY E:HEV ABSOLUTE 2.0"),
        (4, "50-75th", "Mercedes Benz A180", "lta2025", "A180 SALOON PROGRESSIVE LN"),
        (4, "50-75th", "Tesla Model 3 RWD 110", "catalog", "MODEL 3 RWD 110"),
        (5, ">75th", "B.M.W. iX2", "catalog", "IX2 EDRIVE20 MSPT ALED"),
        (5, ">75th", "Denza D9", "catalog", "DENZA D9 ELITE"),
        (5, ">75th", "Honda Civic Type R", "lta2025", "CIVIC TYPE R FL5 JDM"),
        (5, ">75th", "Mercedes Benz GLC", "catalog", "GLC200 4MATIC SUV AVG"),
        (5, ">75th", "Tesla Model Y RWD", "catalog", "MODEL Y RWD 110"),
        (5, ">75th", "Toyota Alphard", "catalog", "ALPHARD HYBRID STANDARD (AUTO)"),
    ],
}
# Family variant groups (catalog models in the same model family) used to
# report variant OMV spread for family-level typical models.
FAMILIES = {
    "Audi A3": ["A3 SEDAN S LINE 1.5 TFSI (85 KW)", "A3 SPORTBACK S LINE 1.5 TFSI (85 KW)"],
    "Toyota Noah": ["NOAH HYBRID", "NOAH HYBRID STANDARD", "NOAH HYBRID ELEGANCE"],
    "Nissan Serena": ["SERENA E-POWER 7S HIGHWAY STAR PRESTIGE",
                      "SERENA E-POWER HIGHWAY STAR SMART 8S"],
    "Toyota Corolla Altis": ["COROLLA ALTIS 1.6 ELEGANCE", "COROLLA ALTIS HYBRID"],
    "Xpeng G6 RWD (STD Range)": ["G6 AIR RWD (STD)", "G6 PRO RWD (LR)"],
    "Audi Q3": ["Q3 SUV TFSI", "Q3 SPORTBACK TFSI", "Q3 SPORTBACK TFSI (SR)"],
    "B.M.W. 216": ["216 GC MSPT ALED", "216 GC MSPT I.GLOW ALED",
                   "216I ACTIVE TOURER INSPIRING", "216I ACTIVE TOURER MSPT ALED"],
    "Mercedes Benz GLC": ["GLC200 4MATIC SUV AVG", "GLC200 4MATIC AVG LN"],
    "Tesla Model Y RWD": ["MODEL Y RWD 110", "MODEL Y LR RWD"],
    "Toyota Alphard": ["ALPHARD HYBRID STANDARD (AUTO)", "ALPHARD HYBRID ELEGANCE (AUTO)"],
    "Volvo EX30 110kW": ["EX30 PLUS", "EX30 ULTRA"],
    "Hyundai Kona 1.6 HEV": ["SX2 KONA 1.6 GDI HEV", "SX2 KONA 1.6 GDI HEV SR"],
    "Mazda 3": ["MAZDA3 4DR 1.5 AT M-HEV EXECUTIVE I4RC",
                "MAZDA3 4DR 1.5 AT M-HYBRID LUXURY I4RC",
                "MAZDA3 5DR 1.5 AT M-HYBRID ASTINA I4RC"],
}


def main():
    reg, cat, lta = load_inputs()
    mix = build_mix(reg)
    pool, cov = build_pool(cat, mix)

    # LTA-2025 mean OMV per model name (all months + suffix variants)
    lta_omv = (lta.groupby("model")["omv"].mean().rename("lta_omv_2025_mean"))

    # ------------------------------------------------------------------
    # 1. Cut points (main: catalog OMV; + 2 sensitivities)
    # ------------------------------------------------------------------
    cutrows = []
    cutpoints = {}
    for opt in ("OptionA", "OptionB"):
        cps = [weighted_quantile(pool.omv, pool.weight, p)
               for p in PERCENTILES[opt]]
        cutpoints[opt] = cps
        for pct, c in zip(PERCENTILES[opt], cps):
            cutrows.append({
                "option": opt, "percentile": pct, "omv_cutpoint": round(c, 0),
                "band_above_quantum_sgd": QUANTUMS[opt][PERCENTILES[opt].index(pct)],
                "variant": "main",
                "omv_source": "catalog avg_omv (Car Cost Aug 2026)",
                "weighting": "Jan-May 2025 make-level mix x catalog composition "
                             "(equal split within make)",
            })
    # sensitivity S1: LTA-2025 OMV for models present in the 2025 edition
    pool_s1 = pool.copy()
    hit = 0
    for idx, r in pool_s1.iterrows():
        matches = lta_omv.index[lta_omv.index.str.upper().str.startswith(
            str(r.model).upper())]
        if len(matches):
            pool_s1.at[idx, "omv_s1"] = float(np.mean(
                [lta_omv[m] for m in matches]))
            hit += 1
        else:
            pool_s1.at[idx, "omv_s1"] = r.omv
    for opt in ("OptionA", "OptionB"):
        cps = [weighted_quantile(pool_s1.omv_s1, pool_s1.weight, p)
               for p in PERCENTILES[opt]]
        for pct, c in zip(PERCENTILES[opt], cps):
            cutrows.append({
                "option": opt, "percentile": pct, "omv_cutpoint": round(c, 0),
                "band_above_quantum_sgd": QUANTUMS[opt][PERCENTILES[opt].index(pct)],
                "variant": "sensitivity_S1_lta2025_omv",
                "omv_source": f"LTA 2025 edition mean OMV ({hit}/{len(pool)} "
                              f"models matched; catalog fallback for the rest)",
                "weighting": "same weights as main",
            })
    # sensitivity S2: uniform model weights
    pool_s2 = pool.copy()
    for opt in ("OptionA", "OptionB"):
        cps = [weighted_quantile(pool_s2.omv, pool_s2.weight * 0 + 1.0, p)
               for p in PERCENTILES[opt]]
        for pct, c in zip(PERCENTILES[opt], cps):
            cutrows.append({
                "option": opt, "percentile": pct, "omv_cutpoint": round(c, 0),
                "band_above_quantum_sgd": QUANTUMS[opt][PERCENTILES[opt].index(pct)],
                "variant": "sensitivity_S2_uniform_weights",
                "omv_source": "catalog avg_omv (Car Cost Aug 2026)",
                "weighting": "uniform (one model = one weight)",
            })
    cutdf = pd.DataFrame(cutrows)
    for _, r in cutdf.iterrows():
        cit = ("Paper s.2.15-2.18, Tables 1/2 (pp.11-12) PROPOSED percentiles; "
               "LTA 2025 edition verified per provenance.md s.7 (source "
               "decision: labelled fallback)")
        cutdf.loc[r.name, "label"] = label(r.option, cit)
        cutdf.loc[r.name, "value_type"] = config.TYPE_COMPUTED
        cutdf.loc[r.name, "scenario"] = r.option
        cutdf.loc[r.name, "data_window"] = config.data_window_tag()
        cutdf.loc[r.name, "citation"] = cit
    colorder = ["option", "percentile", "omv_cutpoint",
                "band_above_quantum_sgd", "variant", "omv_source",
                "weighting", "label", "value_type", "scenario",
                "data_window", "citation"]
    cutdf = cutdf[colorder]
    cutdf.to_csv(os.path.join(TBL, "banding_cutpoints.csv"), index=False)

    # ------------------------------------------------------------------
    # 2. Band every catalog model (both options)
    # ------------------------------------------------------------------
    model_files = {}
    for opt in ("OptionA", "OptionB"):
        cps = cutpoints[opt]
        m = pool[["sn", "make", "model", "coe_class", "fuel_type_code",
                  "ves_banding", "omv", "reg_weight", "weight"]].copy()
        m["band"] = m.omv.map(lambda v: band_of(v, cps))
        m["band_label"] = m.band.map(lambda b: BAND_NAMES[opt][b][0])
        m["quantum_sgd"] = m.band.map(lambda b: BAND_NAMES[opt][b][1])
        m["distance_to_nearest_cutpoint_sgd"] = m.omv.map(
            lambda v: min(abs(v - c) for c in cps))
        m = m.rename(columns={"band": "band", "omv": "omv_catalog_aug2026"})
        m["banding_basis"] = (FALLBACK_STATEMENT + "; banded by catalog "
                              "avg_omv vs main cut points")
        m["label"] = label(opt, "Paper s.2.15 (median OMV per model) + "
                               "s.2.16 (annual review/publication); fallback "
                               "mix per provenance.md s.7")
        m["value_type"] = config.TYPE_COMPUTED
        m["scenario"] = opt
        m["data_window"] = config.data_window_tag()
        m["citation"] = ("Car Cost Aug 2026 catalog (docs/car_cost_aug2026.pdf); "
                         "paper Tables 1/2; data.gov.sg registrations (frozen "
                         "2025-05)")
        fname = f"banding_models_option{'A' if opt == 'OptionA' else 'B'}.csv"
        m.to_csv(os.path.join(TBL, fname), index=False)
        model_files[opt] = m

    # ------------------------------------------------------------------
    # 3. Band shares (cross-foot per option)
    # ------------------------------------------------------------------
    sharerows = []
    covered_reg = cov["mix_covered_reg"]
    for opt in ("OptionA", "OptionB"):
        m = model_files[opt]
        for b in range(1, max(m.band) + 1):
            sub = m[m.band == b]
            w = sub.weight.sum()
            sharerows.append({
                "option": opt, "band": b,
                "band_label": BAND_NAMES[opt][b][0],
                "quantum_sgd": BAND_NAMES[opt][b][1],
                "n_models": int(len(sub)),
                "n_models_pct": round(len(sub) / len(m) * 100, 2),
                "band_share_pct": round(w * 100, 2),
                "est_registrations_janmay2025": round(w * covered_reg),
                "est_registrations_annualised_x12of5": round(w * covered_reg * 12 / 5),
            })
    s = pd.DataFrame(sharerows)
    for opt in ("OptionA", "OptionB"):
        tot = s[s.option == opt].band_share_pct.sum()
        assert abs(tot - 100.0) < 0.05, f"cross-foot FAIL {opt}: {tot}"
        s.loc[s.option == opt, "cross_foot_sum_pct"] = round(tot, 2)
    s["coverage_note"] = (f"shares cover {cov['coverage_pct']:.2f}% of "
                          f"Jan-May 2025 car registrations ({cov['mix_covered_reg']}"
                          f" of {cov['mix_total_reg']}); makes not in the "
                          f"catalog excluded (n={cov['n_make_uncovered']})")
    s["label"] = [label(r.option, "Tables 1/2 (pp.11-12); fallback mix per "
                                   "provenance.md s.7") for _, r in s.iterrows()]
    s["value_type"] = config.TYPE_COMPUTED
    s["scenario"] = s.option
    s["data_window"] = config.data_window_tag()
    s["citation"] = "data.gov.sg registrations (frozen 2025-05) x Car Cost " \
                    "Aug 2026 catalog"
    colorder = ["option", "band", "band_label", "quantum_sgd", "n_models",
                "n_models_pct", "band_share_pct",
                "est_registrations_janmay2025",
                "est_registrations_annualised_x12of5",
                "cross_foot_sum_pct", "coverage_note", "label", "value_type",
                "scenario", "data_window", "citation"]
    s = s[colorder]
    s.to_csv(os.path.join(TBL, "banding_shares.csv"), index=False)

    # ------------------------------------------------------------------
    # 4. Cross-validation vs paper typical models
    # ------------------------------------------------------------------
    # Per-option: implied cut-point intervals from the paper's own table.
    # For cut c separating paper bands k and k+1: the table implies
    #   c >= max OMV of models the paper places in band k  (they are <= c)
    #   c <  min OMV of models the paper places in band k+1 (they are > c)
    # If the interval is empty, the indicative table is internally
    # inconsistent under the resolved OMVs (it likely used LTA's internal
    # "median OMV of past data" per model, paper s.2.15, not the 2025/2026
    # public OMV values).
    def implied_bounds(opt, resolved):
        cps_pct = PERCENTILES[opt]
        out = {}
        for i, pct in enumerate(cps_pct):
            lo, hi = None, None
            for (band, blabel, tname, src, key) in TYPICAL[opt]:
                omv = resolved.get(tname)
                if omv is None:
                    continue
                if band <= i + 1 and band == i + 1:
                    lo = omv if lo is None else max(lo, omv)
                if band == i + 2:
                    hi = omv if hi is None else min(hi, omv)
            feasible = (lo is None and hi is None) or \
                       (hi is None and lo is not None) or \
                       (lo is None and hi is not None) or \
                       (lo <= hi)
            out[pct] = {"lo": lo, "hi": hi, "feasible": feasible}
        return out

    xvrows = []
    agree = {}
    for opt in ("OptionA", "OptionB"):
        cps = cutpoints[opt]
        n_agree = n_ver = 0
        resolved = {}
        for (band, blabel, tname, src, key) in TYPICAL[opt]:
            fam = FAMILIES.get(tname)
            if src == "catalog":
                row = pool[pool.model == key]
                omv = float(row.omv.iloc[0]) if len(row) else None
                src_used = ("catalog avg_omv (Car Cost Aug 2026)"
                            if len(row) else "NOT IN CATALOG")
            else:
                matches = lta_omv.index[
                    lta_omv.index.str.upper().str.startswith(key.upper())]
                omv = (float(np.mean([lta_omv[m] for m in matches]))
                       if len(matches) else None)
                src_used = ("LTA 2025 edition mean OMV (not in current "
                            "catalog; Jan-May 2025 model)"
                            if len(matches) else "NOT FOUND")
            if omv is not None:
                resolved[tname] = omv
            if fam:
                fam_omvs = sorted(float(v) for v in
                                  pool[pool.model.isin(fam)].omv)
                spread = (f"{fam_omvs[0]:,.0f}-{fam_omvs[-1]:,.0f} "
                          f"({len(fam_omvs)} variants)")
                fam_bands = sorted(set(band_of(v, cps) for v in fam_omvs))
            else:
                spread, fam_bands = "n/a", ([band_of(omv, cps)]
                                            if omv is not None else [])
            if omv is None:
                verdict, der = "NO_SOURCED_OMV", None
            else:
                der = band_of(omv, cps)
                verdict = "AGREE" if der == band else "MISMATCH"
                n_ver += 1
                n_agree += (verdict == "AGREE")
            if verdict == "AGREE":
                note = ""
            elif verdict == "MISMATCH":
                note = (f"OMV {omv:,.0f} falls in reconstructed band {der}; "
                        f"paper places it in band {band}. "
                        f"Reconstructed cuts: {cps}")
            xvrows.append({
                "option": opt, "typical_model": tname,
                "paper_band": band, "paper_band_label": blabel,
                "omv_source": src_used, "omv_used": round(omv, 0)
                if omv is not None else None,
                "reconstructed_band": der,
                "verdict": verdict,
                "variant_omv_range": spread,
                "variant_bands": (str(fam_bands) if fam else ""),
                "notes": note,
            })
        agree[opt] = (n_agree, n_ver)
        # implied-bound feasibility diagnostic rows
        for pct, ib in implied_bounds(opt, resolved).items():
            if ib["lo"] is not None and ib["hi"] is not None and \
                    not ib["feasible"]:
                xvrows.append({
                    "option": opt,
                    "typical_model": f"IMPLIES_INCONSISTENT_BOUNDARY p{pct}",
                    "paper_band": None, "paper_band_label": None,
                    "omv_source": "paper table implied (resolved OMVs)",
                    "omv_used": None,
                    "reconstructed_band": None,
                    "verdict": "PAPER_TABLE_INTERNALLY_INCONSISTENT",
                    "variant_omv_range": None, "variant_bands": None,
                    "notes": (f"paper's typical models imply the p{pct} cut "
                              f">= {ib['lo']:,.0f} (highest OMV the paper "
                              f"bands below it) AND < {ib['hi']:,.0f} "
                              f"(lowest OMV the paper bands above it) - "
                              f"empty interval. The indicative table likely "
                              f"used LTA's internal 'median OMV of past "
                              f"data' per model (paper s.2.15), not the "
                              f"2025/2026 public OMV values; it is "
                              f"non-exhaustive and indicative only "
                              f"(paper s.2.18c)."),
                })
    xv = pd.DataFrame(xvrows)
    xv["label"] = [label(r.option, "Paper Tables 1/2 (pp.11-12) typical "
                                   "models; reconstruction per provenance.md "
                                   "s.7") for _, r in xv.iterrows()]
    xv["value_type"] = config.TYPE_COMPUTED
    xv["scenario"] = xv.option
    xv["data_window"] = config.data_window_tag()
    xv["citation"] = "docs/consult_paper_text.md Tables 1 (p.11) & 2 (p.12)"
    colorder = ["option", "typical_model", "paper_band", "paper_band_label",
                "omv_source", "omv_used", "reconstructed_band", "verdict",
                "variant_omv_range", "variant_bands", "notes", "label",
                "value_type", "scenario", "data_window", "citation"]
    xv = xv[colorder]
    xv.to_csv(os.path.join(TBL, "banding_mismatches.csv"), index=False)

    # ------------------------------------------------------------------
    # 5. Auxiliary: catalog vs LTA-2025 OMV cross-check
    # ------------------------------------------------------------------
    cc = pool[["sn", "make", "model", "omv"]].copy()
    cc["lta_omv_2025_mean"] = np.nan
    for idx, r in cc.iterrows():
        matches = lta_omv.index[lta_omv.index.str.upper().str.startswith(
            str(r.model).upper())]
        if len(matches):
            cc.at[idx, "lta_omv_2025_mean"] = float(
                np.mean([lta_omv[m] for m in matches]))
    cc["delta_pct_2026vs2025"] = (
        (cc.omv / cc.lta_omv_2025_mean - 1) * 100
        ).where(cc.lta_omv_2025_mean.notna())
    cc["note"] = (f"prefix match of catalog model against LTA 2025 edition "
                  f"model names; {hit}/{len(cc)} catalog models matched; "
                  "directional check only (catalog OMV is the Aug-2026 "
                  "value; LTA 2025 mean is across 2025 months)")
    cc["label"] = label("OptionA+OptionB (auxiliary check)",
                        "LTA 2025 edition per provenance.md s.7")
    cc["value_type"] = config.TYPE_COMPUTED
    cc["scenario"] = "auxiliary"
    cc["data_window"] = config.data_window_tag()
    cc["citation"] = "LTA OneMotoring OMV page 2025 edition"
    cc.to_csv(os.path.join(config.DIR_DATA_PROCESSED,
                           "lta_omv_2025_crosscheck.csv"), index=False)

    # ------------------------------------------------------------------
    # Summary printout
    # ------------------------------------------------------------------
    print("=" * 72)
    print("STEP 5 — FEEBATE BANDING RECONSTRUCTION")
    print("=" * 72)
    print(f"Mix: Jan-May 2025 (frozen) = {cov['mix_total_reg']:,} car "
          f"registrations, {cov['n_make_mix']} makes")
    print(f"Pool: {len(pool)} catalog models covering "
          f"{cov['coverage_pct']:.2f}% of the mix "
          f"({cov['mix_covered_reg']:,} registrations; "
          f"{cov['n_make_uncovered']} makes uncovered)")
    for opt in ("OptionA", "OptionB"):
        print(f"\n{opt}: cut points = "
              + ", ".join(f"{c:,.0f}" for c in cutpoints[opt]))
        for pct, c in zip(PERCENTILES[opt], cutpoints[opt]):
            sens1 = cutdf[(cutdf.option == opt) &
                          (cutdf.percentile == pct) &
                          (cutdf.variant == "sensitivity_S1_lta2025_omv")
                          ].omv_cutpoint.iloc[0]
            sens2 = cutdf[(cutdf.option == opt) &
                          (cutdf.percentile == pct) &
                          (cutdf.variant == "sensitivity_S2_uniform_weights")
                          ].omv_cutpoint.iloc[0]
            print(f"   p{pct}: main {c:,.0f} | S1 LTA2025 {sens1:,.0f} | "
                  f"S2 uniform {sens2:,.0f}")
    for opt in ("OptionA", "OptionB"):
        m = model_files[opt]
        print(f"\n{opt} banding: " +
              ", ".join(f"band{b} ({BAND_NAMES[opt][b][0]}): "
                        f"{int((m.band == b).sum())} models"
                        for b in range(1, max(m.band) + 1)))
        sh = s[s.option == opt]
        print(f"   shares cross-foot = {sh.cross_foot_sum_pct.iloc[0]}% ; "
              "band shares = " +
              ", ".join(f"{r.band_label}: {r.band_share_pct}%"
                        for _, r in sh.iterrows()))
    print("\nTypical-model cross-validation (paper Tables 1/2):")
    for opt in ("OptionA", "OptionB"):
        a, v = agree[opt]
        print(f"   {opt}: {a}/{v} agree ({a / v * 100:.1f}%)")
    mism = xv[xv.verdict != "AGREE"]
    if len(mism):
        print("   mismatches:")
        for _, r in mism.iterrows():
            print(f"     [{r.option}] {r.typical_model}: paper band "
                  f"{r.paper_band} ({r.paper_band_label}) vs reconstructed "
                  f"band {r.reconstructed_band} "
                  f"(OMV {r.omv_used:,.0f} from {r.omv_source})")
    else:
        print("   no mismatches")
    print(f"\nWrote: banding_cutpoints.csv ({len(cutdf)} rows), "
          f"banding_models_optionA.csv ({len(model_files['OptionA'])} rows), "
          f"banding_models_optionB.csv ({len(model_files['OptionB'])} rows), "
          f"banding_shares.csv ({len(s)} rows), "
          f"banding_mismatches.csv ({len(xv)} rows), "
          f"lta_omv_2025_crosscheck.csv ({len(cc)} rows)")
    return cutpoints, s, xv, agree, cov


if __name__ == "__main__":
    main()
