"""
Step 14 — Unintended consequences, identified and quantified (Batch G).

Outputs (run workspace tables/ unless noted):
  (a) tables/boundary_gaming_zones.csv
      Band-boundary spec-gaming: zone = [0.95c, 1.05c] around each cut-off c
      (zone width ±5% OMV is a DOCUMENTED ANALYTICAL CHOICE, NOT an LTA
      parameter — stated on every row). Per option, per cut-off (main
      variant): registration share inside the zone (annualised Jan-May 2025
      mix x catalog, the documented banding convention), the OMV adjustment
      needed to cross the boundary (5% of c at the zone edge, 0 at the
      centre, linear between), and the quantum at stake (difference between
      the adjacent bands' quantums, 15,000 / 7,500 S$). Incentive
      interpretation: a dealer re-specs a vehicle across the boundary only
      if the quantum benefit exceeds any spec-upgrade cost; NO dealer cost
      data exist and none is fabricated — the quantified exposure is the
      zone registration share and the quantum is the maximum stake.
      Sensitivity: S1 (LTA-2025-OMV) and S2 (uniform weights) shift the
      zones — variant zone bounds are reported on each row.
  (b) tables/classification_distortion.csv
      Variant families (same make/model, differing specs) spanning band
      boundaries. Families grouped by (make, model base name) after
      stripping spec suffixes with a documented rule (see family_base()).
      Per option: n families, n spanning families, members affected,
      mis-banded share (denominator = all 217 catalog models), and the
      maximum within-family quantum difference (the distortion's monetary
      size). One summary row per option + one detail row per spanning
      family.
  (c) tables/segment_shift.csv — Batch F's table, verified/extended only.
      Confirms EV share of the total demand shift and the luxury
      (OMV > 49,662) vs mass-market mix shift are present per option
      (Step 12 results; not recomputed). Rows added ONLY if missing.
  (d) tables/used_car_directional.csv
      Used-car channel: DIRECTIONAL statements only — NO usable data exist
      in this study (no used-car price/turnover source was fetched). This
      is stated explicitly on every row; no numbers are produced.

Every row carries the config label stamp (value_type + scenario + data
window + regime start + vintage). Regime start 2027-01-01, vintage 2017.
"""
from __future__ import annotations

import os
import re
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

WS = config.WORKSPACE_ROOT
TBL = config.DIR_TABLES

MIX_WINDOW = config.data_window_tag()
LABEL_COMPUTED = config.output_label(
    config.TYPE_COMPUTED, data_window=MIX_WINDOW,
    citation=(
        "Step 14 unintended consequences: cut points tables/banding_cutpoints.csv "
        "(main variant, Batch C; S1/S2 sensitivity variants); model OMV + weights "
        "tables/banding_models_optionA/B.csv (Car Cost Aug 2026 catalog x Jan-May "
        "2025 make-level mix, coverage 98.73%); quantums PROPOSED (paper s2.18, "
        "Tables 1/2); ±5% zone width = documented analytical choice (config."
        "GAMING_ZONE_WIDTH_PCT), NOT an LTA parameter"
    ),
)


# ======================================================================
# Load inputs
# ======================================================================

def load_cutpoints() -> tuple[dict, dict]:
    """Return ({option: [cutpoints sorted by percentile]}, variant cutpoint
    map for the sensitivity note). Main variant is used for the analysis;
    S1/S2 bounds are reported for context only."""
    cp = pd.read_csv(os.path.join(TBL, "banding_cutpoints.csv"))
    main = {}
    variants = {}
    for _, r in cp.iterrows():
        opt = r["option"]
        entry = {
            "percentile": int(r["percentile"]),
            "cut": float(r["omv_cutpoint"]),
            "band_above_quantum": float(r["band_above_quantum_sgd"]),
        }
        if r["variant"] == "main":
            main.setdefault(opt, []).append(entry)
        variants.setdefault(opt, {})[r["variant"]] = entry
    for opt in main:
        main[opt].sort(key=lambda e: e["percentile"])
    return main, variants


def load_models() -> pd.DataFrame:
    """217-model catalog with OMV, weight (share of covered Jan-May 2025
    mix) and per-option band/quantum columns."""
    a = pd.read_csv(os.path.join(TBL, "banding_models_optionA.csv"))
    b = pd.read_csv(os.path.join(TBL, "banding_models_optionB.csv"))
    m = a[["sn", "make", "model", "coe_class", "omv_catalog_aug2026",
           "weight", "band", "quantum_sgd"]].rename(
        columns={"band": "band_A", "quantum_sgd": "quantum_A"})
    m = m.merge(
        b[["sn", "band", "quantum_sgd"]].rename(
            columns={"band": "band_B", "quantum_sgd": "quantum_B"}),
        on="sn")
    assert len(m) == 217, f"expected 217 catalog models, got {len(m)}"
    assert abs(m["weight"].sum() - 1.0) < 1e-9, "model weights must sum to 1"
    return m


def load_annual_reg_base() -> dict:
    """Annualised registration base per option (Batch F, Step 11) — used to
    annualise the zone shares (same source as the revenue base)."""
    fr = pd.read_csv(os.path.join(TBL, "fee_revenue_base.csv"))
    return {r["feebate_option"]: int(r["annual_registrations_base"])
            for _, r in fr.iterrows()}


# ======================================================================
# (a) Band-boundary spec-gaming zones
# ======================================================================

def build_gaming_zones() -> pd.DataFrame:
    main_cp, variants_cp = load_cutpoints()
    models = load_models()
    ann = load_annual_reg_base()
    width = config.GAMING_ZONE_WIDTH_PCT  # 5.0 — documented analytical choice

    rows = []
    for opt in ("OptionA", "OptionB"):
        cps = main_cp[opt]
        quantums = (config.FEEBATE_QUANTUMS_OPTION_A if opt == "OptionA"
                    else config.FEEBATE_QUANTUMS_OPTION_B)
        n_bands = len(cps) + 1
        for i, c in enumerate(cps):
            cval = c["cut"]
            lo, hi = 0.95 * cval, 1.05 * cval
            q_below = float(quantums[i])
            q_above = float(quantums[i + 1])
            # NOTE: tables/banding_cutpoints.csv column 'band_above_quantum_sgd'
            # carries the quantum of the band BELOW this cut-off (the band
            # that ENDS at this cut-off): e.g. OptionA p35 -> -15,000 (band 1),
            # p50 -> 0 (band 2); OptionB p75 -> +7,500 (band 4). Verified
            # against config quantums below; the column name is misleading.
            assert abs(c["band_above_quantum"] - q_below) < 1e-9, (
                f"cutpoint file value {c['band_above_quantum']} != quantum of "
                f"band below cut {q_below} at {opt} p{c['percentile']}")
            q_stake = abs(q_above - q_below)

            in_zone = models[(models["omv_catalog_aug2026"] >= lo)
                             & (models["omv_catalog_aug2026"] <= hi)]
            zone_share = float(in_zone["weight"].sum())          # of covered mix
            est_ann = zone_share * ann[opt]
            adj_edge = 0.05 * cval                               # OMV move at zone edge

            # sensitivity variants shift the zones (same percentile, other cut)
            sens = []
            for vname in ("sensitivity_S1_lta2025_omv", "sensitivity_S2_uniform_weights"):
                vc = variants_cp[opt][vname]["cut"]
                sens.append(f"{vname.replace('sensitivity_', '')}: "
                            f"[{0.95 * vc:,.0f}, {1.05 * vc:,.0f}] "
                            f"(cut {vc:,.0f})")
            sens_note = "; ".join(sens)

            rows.append({
                "option": opt,
                "percentile": c["percentile"],
                "cutpoint_sgd": round(cval, 2),
                "zone_width_pct": width,
                "zone_width_note": (
                    "±5% OMV zone width is a DOCUMENTED ANALYTICAL CHOICE "
                    "(this study), NOT an LTA parameter"),
                "zone_lo_sgd": round(lo, 2),
                "zone_hi_sgd": round(hi, 2),
                "n_models_in_zone": int(len(in_zone)),
                "models_in_zone": "; ".join(
                    f"{r.make} {r.model} ({r.omv_catalog_aug2026:,.0f})"
                    for r in in_zone.itertuples()) or "none",
                "zone_share_pct_covered_mix": round(100 * zone_share, 3),
                "coverage_note": (
                    "share of the Jan-May 2025 registration mix x catalog "
                    "(98.73% of registrations covered; makes not in the "
                    "catalog excluded)"),
                "est_registrations_annual_in_zone": round(est_ann, 1),
                "omv_adjustment_edge_sgd": round(adj_edge, 2),
                "omv_adjustment_centre_sgd": 0.0,
                "omv_adjustment_note": (
                    "OMV move to cross the boundary: 5% of the cut point at "
                    "the zone edge (max), 0 at the zone centre, linear in "
                    "between — a vehicle already inside the zone can cross "
                    "with proportionally less"),
                "quantum_below_cut_sgd": q_below,
                "quantum_above_cut_sgd": q_above,
                "quantum_at_stake_sgd": q_stake,
                "quantum_binds_note": (
                    f"max stake = adjacent-band quantum difference "
                    f"({q_stake:,.0f} S$); the OMV adjustment at the edge "
                    f"({adj_edge:,.2f} S$) is the physical distance to close, "
                    f"not the economic bound"),
                "incentive_note": (
                    f"A dealer re-specs a vehicle across this boundary only "
                    f"if the quantum benefit ({q_stake:,.0f} S$, the maximum "
                    f"stake) exceeds the spec-upgrade cost. No dealer cost "
                    f"data are available and none is fabricated — the "
                    f"quantified exposure is the zone registration share "
                    f"({100 * zone_share:.2f}% of the covered mix, ~"
                    f"{est_ann:,.0f} registrations/yr) plus the quantum at "
                    f"stake ({q_stake:,.0f} S$). Both directions are "
                    f"profitable (move up from the cheaper band or down "
                    f"into it). ±5% zone width = documented analytical "
                    f"choice, NOT an LTA parameter."),
                "sensitivity_zone_shift": sens_note,
                "label": LABEL_COMPUTED,
                "value_type": config.TYPE_COMPUTED,
                "scenario": opt,
                "data_window": MIX_WINDOW,
                "citation": (
                    "Step 14(a); cut points tables/banding_cutpoints.csv "
                    "(main variant + S1/S2); mix tables/banding_models_"
                    f"{opt[-1]}.csv; quantums PROPOSED (paper s2.18, Tables "
                    "1/2); annualised base tables/fee_revenue_base.csv"),
            })

    df = pd.DataFrame(rows)
    # invariant: zones of adjacent cut-offs must not overlap (else a model
    # could sit in two gaming zones) — verified per option
    for opt in ("OptionA", "OptionB"):
        z = df[df.option == opt].sort_values("cutpoint_sgd")
        for _, (r1, r2) in enumerate(zip(z.itertuples(), list(z.itertuples())[1:])):
            assert r2.zone_lo_sgd >= r1.zone_hi_sgd, (
                f"zone overlap at {opt} between cuts {r1.cutpoint_sgd} and "
                f"{r2.cutpoint_sgd}")
    return df


# ======================================================================
# (b) Classification distortion — variant families
# ======================================================================

# Documented base-name rule (catalog-derived, applied to the 217 Car Cost
# Aug 2026 catalog model names; every resulting family was inspected):
#   1. remove parenthesised spec groups: (85 KW), (SR), (MATRIX),
#      (LONG RANGE), (STD), (LR), (49KWH), (7-SEATER), (3-DOOR), ...
#   2. per-token cleanup: drop trailing commas/dots and trailing plus
#      (250+ -> 250, 4MATIC+ -> 4MATIC, "LN," -> LN); internal dots and
#      hyphens kept (I.GLOW, ZR-V, F-PACE, E-HS9); '#' kept (SMART #1)
#   3. drop spec tokens matching the patterns/whitelist (check the token
#      AS-IS before any splitting, so EDRIVE35 / 2.0L are stripped whole)
#      - 2-digit pure numbers stripped ONLY for B.M.W. (power codes:
#        I4 EDRIVE35 -> I4; X3 20/50 XDRIVE -> X3); elsewhere they are
#        model names (AVATR 07/11, ORA 5, IONIQ 5, MIFA 7)
#      - 3-digit pure numbers stripped only for non-B.M.W. AND only when
#        preceded by a letter token (Mercedes engine codes C 180 /
#        CLA 200 / GLC200 / MODEL 3 RWD 110); leading 3-digit tokens are
#        model names (PORSCHE 911, B.M.W. 116)
#   4. split letter+digit tokens of 3+ letters that END in digits
#      (GLE53 -> GLE 53, GLC200 -> GLC 200, RAV4 -> RAV 4, SDRIVE16 ->
#      SDRIVE 16) so engine-code variants merge; tokens with 1-2 leading
#      letters are model names (I7, ES90, XC60, C180, MAZDA3 -> MAZDA 3)
#      and are NOT split, except a trailing hybrid 'H' on a digit-ending
#      stem (RX350H -> RX350)
#   5. drop a LEADING token that repeats a multi-word make name
#      ("MERCEDES-BENZ GLB 250+..." -> "GLB 250+..."; single-word makes are
#      usually part of the model name, e.g. MAZDA3, and are left alone)
#   6. drop single-letter trim tokens A/E/S/L (COOPER E -> COOPER,
#      SORENTO A -> SORENTO); single-letter model names (Zeekr X, A3's
#      'A' inside letter+digit tokens) are untouched by design
#   7. SAFETY: if stripping would remove every token, keep the original
#      name (protects single-token model names such as Zeekr X, AVATR 07)
# Effect: same make/model with differing specs (trim, engine, powertrain,
# body, generation code) collapse to one family; distinct models stay apart
# (verified empirically by inspecting every resulting family).
_SPEC_PATTERNS = [
    r"^\d\.\d+[A-Z]?$",              # displacement: 1.5, 1.6, 2.0, 2.0L
    r"^\d\.\d+[A-Z]-[A-Z]$",         # 2.5I-S (Forester)
    r"^[A-Z]{2,}\d+-[A-Z]$",         # HE7-S (Honda Freed)
    r"^[A-Z]{2,}-SIN$",              # DX-SIN / HX-SIN (Honda SG trims)
    r"^\d+KW$", r"^\d+PS$",          # 100KW, 155KW, 404PS
    r"^\dMATIC\+?$", r"^\dAT$",      # 4MATIC(+), 4AT
    r"^\dDR$", r"^\dS$",             # 4DR/5DR, 7S/8S (Serena)
    r"^\d-SEATER$", r"^\d-TONE$", r"^\d+-DOOR$",
    r"^T\d+$", r"^R-[A-Z]+$",        # T8, R-DYN
    r"^EDRIVE\d+$",                  # EDRIVE40 (checked BEFORE splitting)
    r"^E-\d[A-Z]+$", r"^E:[A-Z]+$",  # E-4ORCE, E:HEV
]
_SPEC_WHITELIST = {
    # engine / platform / fuel / drivetrain
    "TFSI", "TDI", "GDI", "T-GDI", "DOHC", "I-VTEC", "DCT", "CVT",
    "HEV", "PHEV", "BEV", "EV", "HYBRID", "MHEV", "M-HYBRID", "M-HEV",
    "E-POWER", "DMI", "DM-I", "FWD", "RWD", "AWD", "2WD", "4WD",
    "PGR", "XDRIVE", "SDRIVE", "KW", "PS", "AUTO", "AT", "SINGLE",
    "MOTOR", "EYESIGHT",
    # body
    "SEDAN", "SPORTBACK", "SUV", "WAGON", "HATCHBACK", "COUPE", "TOURER",
    "WGN", "CABRIOLET", "FASTBACK", "MPV", "SHOOTING", "BRAKE", "DOOR",
    # trims / packages / marketing codes
    "LINE", "XLINE", "LUXURY", "PREMIUM", "ELITE", "EARTH", "AIR",
    "STANDARD", "EXTENDED", "RANGE", "LONG", "MAX", "ULTRA", "DYNAMIC",
    "SUNROOF", "TECH", "PACK", "INSPIRING", "PINNACLE", "PRESTIGE",
    "ACTIVE", "URBAN", "SPORT", "SPORTS", "GT", "RS", "SE", "EX", "SX",
    "DX", "SR", "GL", "GLX", "ER", "LR", "EXECUTIVE", "ASTINA",
    "PROGRESSIVE", "AVANTGARDE", "BUSINESS", "EDITION", "EXCLUSIVE",
    "PRO", "PLUS", "ORION", "PERFORMANCE", "SELECTION", "SPORTLINE",
    "RCRT", "LIFE", "NAVI", "CROSSTAR", "SPADA", "ELEGANCE", "ELEGANT",
    "GTI", "MATRIX", "ITP", "HL", "ISP", "LED", "ALED", "MSPT",
    "MSPTPRO", "I.GLOW", "ETSI", "EU6EB", "HIGHWAY", "STAR", "SMART",
    "EMH", "IRG", "LHP", "AHA", "CSS", "SES", "WDE", "LN", "DIG-T",
    "4ORCE", "II",
    # Mercedes sub-brand / short codes seen in this catalog
    "AMG", "AVG", "CAB",
    # generation / spec codes seen in this catalog
    "MX5", "SX2", "SG2",
}
_SINGLE_CHAR_TRIM = {"A", "E", "S", "L"}  # e.g. 'COOPER E', 'SORENTO A'; safety rule (7) applies


def family_base(make: str, model: str) -> str:
    name = re.sub(r"\([^)]*\)", " ", model)          # rule 1
    raw = []
    for t in name.upper().split():
        t = t.strip(",._").rstrip("+")               # rule 2
        if t:
            raw.append(t)
    make_words = re.sub(r"[^A-Z]", " ", make).split()
    if len(make_words) >= 2 and raw:                 # rule 5
        first = raw[0]
        comps = re.sub(r"[^A-Z]", " ", first).split()
        if comps and all(c in make_words for c in comps):
            raw = raw[1:]
    queue = list(enumerate(raw))                     # (index, token)
    kept = []
    while queue:
        idx, t = queue.pop(0)
        prev_letter = idx > 0 and bool(re.match(r"^[A-Z]", raw[idx - 1])) \
            if idx < len(raw) else False
        is_bmw2 = make == "B.M.W." and re.match(r"^\d{2}$", t)
        is_3dig = (make != "B.M.W." and re.match(r"^\d{3}$", t)
                   and (prev_letter or idx >= len(raw)))  # idx>=len(raw): split-off digit, stem was letters
        if is_bmw2 or is_3dig:
            continue
        if any(re.match(p, t) for p in _SPEC_PATTERNS):
            continue
        if t in _SPEC_WHITELIST:
            continue
        if len(t) == 1 and t in _SINGLE_CHAR_TRIM:
            next_tok = queue[0][1] if queue else None
            if not (next_tok and re.match(r"^\d{2,3}$", next_tok)):
                continue                              # keep power-code context: AMG E 53
        mh = re.match(r"^([A-Z]+\d+)H$", t)
        if mh:
            queue.append((idx, mh.group(1)))
            continue
        msplit = re.match(r"^([A-Z]{3,})(\d+(?:\.\d+)?)$", t)
        if msplit:
            queue = [(len(raw), msplit.group(1)),        # stem re-checked,
                     (len(raw), msplit.group(2))] + queue  # digit sub-token (order kept)
            continue
        kept.append(t)
    if not kept:                                      # rule 7 (safety)
        kept = list(raw)
    return " ".join(kept)


def build_classification_distortion() -> pd.DataFrame:
    models = load_models()
    models["family"] = [
        f"{r.make} :: {family_base(r.make, r.model)}"
        for r in models.itertuples()
    ]

    rows = []
    summary = {}
    for opt, band_col, q_col in (("OptionA", "band_A", "quantum_A"),
                                 ("OptionB", "band_B", "quantum_B")):
        fam = models.groupby("family").agg(
            n_members=("sn", "count"),
            makes=("make", "first"),
            bands=(band_col, lambda s: sorted(set(s))),
            qmin=(q_col, "min"), qmax=(q_col, "max"),
            omv_min=("omv_catalog_aug2026", "min"),
            omv_max=("omv_catalog_aug2026", "max"),
        ).reset_index()
        fam["spans"] = fam["bands"].apply(len) > 1
        spanning = fam[fam["spans"]]
        n_fam = len(fam)
        n_span = len(spanning)
        affected = int(spanning["n_members"].sum())
        mis_banded_share = affected / len(models)
        max_diff_fam = spanning.loc[spanning["qmax"].sub(spanning["qmin"]).idxmax()] \
            if n_span else None
        max_diff = float(max_diff_fam["qmax"] - max_diff_fam["qmin"]) if n_span else 0.0
        summary[opt] = dict(n_families=n_fam, n_spanning=n_span,
                            affected=affected, share=mis_banded_share,
                            max_diff=max_diff,
                            max_diff_family=max_diff_fam["family"] if n_span else "")
        for r in spanning.itertuples():
            members = models[models.family == r.family]
            detail = "; ".join(
                f"{x.model} (OMV {x.omv_catalog_aug2026:,.0f}, band {int(getattr(x, band_col))}, "
                f"q {int(getattr(x, q_col)):+,})"
                for x in members.sort_values("omv_catalog_aug2026").itertuples())
            rows.append({
                "row_type": "spanning_family",
                "option": opt,
                "family": r.family,
                "n_members": int(r.n_members),
                "members_bands_quantums": detail,
                "omv_range_sgd": f"{r.omv_min:,.0f} .. {r.omv_max:,.0f}",
                "bands_spanned": " | ".join(str(b) for b in r.bands),
                "within_family_quantum_diff_sgd": float(r.qmax - r.qmin),
                "mis_banded_share_pct": None,
                "label": LABEL_COMPUTED,
                "value_type": config.TYPE_COMPUTED,
                "scenario": opt,
                "data_window": MIX_WINDOW,
                "citation": (
                    "Step 14(b); family rule: documented base-name strip rule "
                    "(see src/consequences.py family_base); members from "
                    f"tables/banding_models_{opt[-1]}.csv"),
            })
        s = summary[opt]
        rows.append({
            "row_type": "option_summary",
            "option": opt,
            "family": None,
            "n_members": None,
            "members_bands_quantums": None,
            "omv_range_sgd": None,
            "bands_spanned": None,
            "within_family_quantum_diff_sgd": max_diff,
            "n_families": s["n_families"],
            "n_spanning_families": s["n_spanning"],
            "members_affected": s["affected"],
            "mis_banded_share_pct": round(100 * s["share"], 2),
            "mis_banded_denominator": "all 217 catalog models (Car Cost Aug 2026, Jan-May 2025 mix weights)",
            "max_within_family_quantum_diff_sgd": max_diff,
            "max_diff_family": s["max_diff_family"],
            "note": (
                f"{s['n_spanning']}/{s['n_families']} families span a band "
                f"boundary under {opt}; {s['affected']} of 217 models "
                f"({100 * s['share']:.2f}%) are in families where the band "
                f"depends on variant choice; max within-family quantum "
                f"difference {max_diff:,.0f} S$ = the distortion's monetary "
                f"size"),
            "label": LABEL_COMPUTED,
            "value_type": config.TYPE_COMPUTED,
            "scenario": opt,
            "data_window": MIX_WINDOW,
            "citation": (
                "Step 14(b); family rule: documented base-name strip rule "
                "(see src/consequences.py family_base); members from "
                f"tables/banding_models_{opt[-1]}.csv"),
        })

    df = pd.DataFrame(rows)
    # invariant: every family spanning under Option A also spans under
    # Option B (A's cut points 28,877/36,062 are a subset of B's
    # 20,310/28,877/36,062/49,662)
    span_a = set(models[
        models.groupby("family")["band_A"].transform("nunique") > 1].family)
    span_b = set(models[
        models.groupby("family")["band_B"].transform("nunique") > 1].family)
    assert span_a <= span_b, (
        f"families spanning A but not B: {sorted(span_a - span_b)}")
    return df, summary, models


# ======================================================================
# (c) Segment demand shifts — verify/extend Batch F's table
# ======================================================================

def check_segment_shift() -> dict:
    """Batch F's tables/segment_shift.csv must contain, per option: EV share
    of the total shift + luxury vs mass-market mix. Add rows ONLY if
    missing (Batch F's figures are NOT recomputed)."""
    p = os.path.join(TBL, "segment_shift.csv")
    df = pd.read_csv(p)
    required = {}
    for opt in ("OptionA", "OptionB"):
        segs = set(df.loc[df.feebate_option == opt, "segment"])
        required[opt] = {
            "EV_share_of_total_shift": "EV_share_of_total_shift" in segs,
            "luxury_vs_mass_luxury": "luxury_vs_mass_luxury" in segs,
            "luxury_vs_mass_mass": "luxury_vs_mass_mass" in segs,
        }
    missing = {opt: [k for k, ok in v.items() if not ok]
               for opt, v in required.items()}
    if any(missing.values()):
        raise RuntimeError(
            "segment_shift.csv rows missing and cannot be fabricated "
            "(Step 12 output): " + str(missing))
    # complete -> file left untouched (Batch F artifact, extension-only rule)
    return {"all_present": True, "per_option": required, "rows_added": 0}


# ======================================================================
# (d) Used-car channel — directional only, NO usable data
# ======================================================================

def build_used_car_directional() -> pd.DataFrame:
    lab = config.output_label(
        config.TYPE_DIRECTIONAL,
        scenario="all 8 master-matrix cells (Step 15)",
        data_window=MIX_WINDOW,
        citation=(
            "Step 14(d): used-car channel — DIRECTIONAL ONLY. No usable "
            "data: no used-car price/turnover source was fetched in this "
            "study; directions rest on the computed new-car and renewal "
            "effects (Steps 8-13) and are labelled DIRECTIONAL, not "
            "COMPUTED. No numbers are produced for the used-car channel."),
    )
    rows = [
        {
            "direction": "used_car_relative_attractiveness_upper_bands",
            "driver": (
                "feebate adds +7,500 S$ (Option B band 4) / +15,000 S$ "
                "(Option A band 3, Option B band 5) to the COE cost of NEW "
                "registrations in the upper bands (PROPOSED quantums, paper "
                "s2.18)"),
            "statement": (
                "New cars in the upper OMV bands become relatively more "
                "expensive vs equivalent used cars -> used-car relative "
                "attractability for high-OMV segments is directionally UP "
                "under both options (stronger in Option A's top band)."),
            "applies_to": "all 8 cells",
        },
        {
            "direction": "used_car_holding_incentive_renewal_feebate",
            "driver": (
                "renewal feebate at PROPOSED cut points is a NET REBATE for "
                "the 2017 vintage cohort (Batch F: -517.2M S$/yr Option A, "
                "-353.3M S$/yr Option B; pre-A cohort per-vehicle -12,629 / "
                "-9,261 S$) — renewal cost for older, low-OMV cars FALLS"),
            "statement": (
                "Holding an existing older car and renewing its COE becomes "
                "directionally CHEAPER -> sell-off/upgrade pressure is "
                "directionally DOWN and used-car supply of older low-OMV "
                "cars directionally PERSISTS; if LTA re-bands renewals at "
                "vintage cut points (VINTAGE_2017pct sensitivity), this "
                "effect is neutralised."),
            "applies_to": "cells with renewal_feebate_yes (4 of 8); "
                          "renewal_feebate_no cells: no effect",
        },
        {
            "direction": "used_car_urgency_channel_E_removed",
            "driver": (
                "'E removed' eliminates the urgent-bid COE channel "
                "(PROPOSED, paper s2.23(a): urgent buyers wait for the next "
                "bidding exercise)"),
            "statement": (
                "Urgent new-car demand loses its fast lane -> new-car "
                "urgency premium directionally DOWN; buyers with timing "
                "constraints are directionally PUSHED TOWARD the used-car "
                "channel (used-car attractiveness directionally UP in the "
                "E_removed cells vs E_cars_only)."),
            "applies_to": "E_removed cells (4 of 8)",
        },
    ]
    df = pd.DataFrame(rows)
    df["value_type"] = config.TYPE_DIRECTIONAL
    df["label"] = lab
    df["scenario"] = "all 8 master-matrix cells (Step 15)"
    df["data_window"] = MIX_WINDOW
    df["citation"] = lab.split("citation: ")[1]
    df = df[["direction", "driver", "statement", "applies_to", "value_type",
             "label", "scenario", "data_window", "citation"]]
    return df


# ======================================================================
# main
# ======================================================================

def main() -> None:
    zones = build_gaming_zones()
    zones.to_csv(os.path.join(TBL, "boundary_gaming_zones.csv"), index=False)
    print("=== (a) boundary gaming zones ===")
    for r in zones.itertuples():
        print(f"{r.option} p{r.percentile} cut {r.cutpoint_sgd:,.0f}: "
              f"zone [{r.zone_lo_sgd:,.0f}, {r.zone_hi_sgd:,.0f}] | "
              f"share {r.zone_share_pct_covered_mix:.2f}% | "
              f"~{r.est_registrations_annual_in_zone:,.0f} regs/yr | "
              f"OMV move @edge {r.omv_adjustment_edge_sgd:,.2f} | "
              f"stake {r.quantum_at_stake_sgd:,.0f}")

    distortion, summary, models = build_classification_distortion()
    distortion.to_csv(os.path.join(TBL, "classification_distortion.csv"),
                      index=False)
    print("\n=== (b) classification distortion ===")
    for opt, s in summary.items():
        print(f"{opt}: families={s['n_families']} spanning={s['n_spanning']} "
              f"affected={s['affected']}/217 "
              f"({100 * s['share']:.2f}%) max_diff={s['max_diff']:,.0f} "
              f"({s['max_diff_family']})")

    print("\nfamily list (sanity check):")
    fam = models.groupby("family").size()
    for f, n in fam.items():
        mark = " <== multi" if n > 1 else ""
        print(f"  [{n}] {f}{mark}")

    seg = check_segment_shift()
    print("\n=== (c) segment_shift.csv check ===")
    print("all required rows present:", seg["all_present"],
          "| rows added:", seg["rows_added"])
    for opt, v in seg["per_option"].items():
        print(f"  {opt}: {v}")

    used = build_used_car_directional()
    used.to_csv(os.path.join(TBL, "used_car_directional.csv"), index=False)
    print("\n=== (d) used-car directional ===")
    print(f"{len(used)} DIRECTIONAL rows written (no usable data — stated)")


if __name__ == "__main__":
    main()
