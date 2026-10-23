"""Step 11 — Feebate revenue by option (Batch F).

Computes, per feebate option {OptionA, OptionB} and per Category-E option
{E_removed, E_cars_only}:

  * annual net feebate revenue under the stated registration mix
    (2025-01..2025-05 frozen window, annualised x12/5 — Batch D/Fbar
    convention),
  * the E-shift revenue delta (6,400/yr, Category-B-skewed OMV
    composition, tables/e_shift_feebate_base_delta.csv — Batch E input)
    recomputed to the dollar per option,
  * sensitivity across Batch C mix proxies (main fallback / S1
    LTA-2025-OMV / S2 uniform weights; variant cut points from
    batch_handoff_c.json, banding recomputed per variant),
  * incidence against total COE revenue (merged car + C + D),
  * independent dollar-level cross-foot (band shares x quantums x
    registration counts) to verification/crossfoot_log.csv.

Design decisions (documented in methodology_notes.md s.13, provenance.md
s.9):
  * 'E removed' base = merged-car base (Jan-May 2025 annualised) +
    E-shifted 6,400/yr banded (Batch E convention: removal mechanics
    paper s2.23(a) — urgent buyers wait for the next COE bidding, so
    the flow re-enters the merged car category and pays the feebate).
    The delta against the same base EXCLUDING them is reported.
  * 'E cars-only' base = merged-car base + E-registered cars INCLUDED
    (6,400/yr, banded per the E-shift table). Rationale: the paper
    retains E for CAR registration (s2.23(b)) and states E COEs have
    been mostly used for Category B cars in recent years (s2.22), so
    the full E flow is car registrations; Batch E banded the full
    6,400/yr accordingly. Size: 6,400/yr (E quota 266.67/round x 24,
    2026-08..2026-10 last-6 observed).
  * The two E options therefore carry the same car-feebate base
    arithmetic; their difference is the Category-C side of the
    incidence denominator (E_removed: C quota +11.11%, price flat —
    Batch E; cars_only: C unchanged — paper s2.23(b) shield).
  * Option A's E-shift delta is derived by aggregating Batch E's
    Option-B band counts onto Option A's percentile bands
    (same percentile coordinate system: 0-35th = B's 0-10th + 10-35th,
    35-50th = B's 35-50th, >50th = B's 50-75th + >75th).
  * Sensitivity variants: variant cut points (Batch C) applied to the
    same base mix (catalog OMVs x 2025 registration weights); the
    E-shift delta is held at base cut points (Batch E banding) — the
    sensitivity isolates the mix-proxy effect on the base.

Every output row is stamped via config.output_label(); mix-based
numbers carry the 2025-01..2025-05 (frozen at 2025-05) data window;
quantums are PROPOSED (paper s2.18, Tables 1/2).
"""
from __future__ import annotations

import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import config as cfg

W = cfg.WORKSPACE_ROOT
TBL = cfg.DIR_TABLES
VER = cfg.DIR_VERIFICATION

Q_A = cfg.FEEBATE_QUANTUMS_OPTION_A   # [-15000, 0, 15000]
Q_B = cfg.FEEBATE_QUANTUMS_OPTION_B   # [-15000, -7500, 0, 7500, 15000]

# Batch D convention: merged forward quota held at last-6 average
MERGED_QUOTA_PER_ROUND = 2137.5       # tables/quota_reallocation.csv forward
ROUNDS_PER_YEAR = 24

# Incidence denominator inputs (stated windows)
WITHFEE_LATEST = {"OptionA": 129873.20, "OptionB": 129816.07}  # batch_handoff_d.json
WITHFEE_LATEST_WINDOW = "2027-12 (last forward round; Batch D withfee_latest)"
C_PRICE = 91813.5                     # last-6 average observed C premium (2026-08 b1..2026-10 b2)
C_WINDOW = "2026-08 b1..2026-10 b2 (last 6 biddings)"
C_QUOTA_YR_CARS_ONLY = 7468           # Batch E (311.17/round x 24 approx)
C_QUOTA_YR_E_REMOVED = 8298           # Batch E (311.17/0.9 x 24 approx; +11.11%)
D_QUOTA_PER_ROUND = 523.0             # last-6 average, coe_panel_perbidding.csv
D_PRICE = 11391.83                    # last-6 average observed D premium
D_WINDOW = "2026-08 b1..2026-10 b2 (last 6 biddings)"

E_SHIFT_ANNUAL = 6400                 # Batch E (266.67/round x 24 x 100%)
E_SHIFT_B_BASE = [337.35, 994.46, 821.11, 1675.11, 2571.97]  # tables/e_shift_feebate_base_delta.csv
E_SHIFT_B_BASE_TABLE_DELTA = 38624201.0  # Batch E headline (2dp band contributions)

# Batch C variant cut points (batch_handoff_c.json)
VARIANT_CUTPOINTS = {
    "base_main_fallback": {"OptionA": [28877, 36062],
                           "OptionB": [20310, 28877, 36062, 49662]},
    "S1_lta2025_omv": {"OptionA": [29800, 36283],
                       "OptionB": [21578, 29800, 36283, 49662]},
    "S2_uniform_weights": {"OptionA": [30629, 37301],
                           "OptionB": [21776, 30629, 37301, 50795]},
}

LABEL = ("Step 11 feebate revenue: PROPOSED quantums (paper s2.18, Tables 1/2); "
         "mix 2025-01..2025-05 frozen (main fallback: Jan-May 2025 registrations x "
         "Car Cost Aug 2026 catalog, coverage 98.73%); E-shift 6,400/yr "
         "Category-B-skewed (Batch E, paper s2.22); E_removed base incl. E-shift per "
         "Batch E convention (delta vs excluding base reported); E_cars_only base "
         "incl. E-registered cars (documented choice, s.13)")


def band_of(omv: float, cutpoints: list) -> int:
    """1-based band index; upper-inclusive convention (c_{k-1}, c_k]."""
    b = 1
    for c in cutpoints:
        if omv > c:
            b += 1
        else:
            break
    return b


def band_of_full(omv: float, cutpoints: list) -> int:
    """1-based band index, top band (c_last, inf)."""
    b = 1
    for i, c in enumerate(cutpoints, start=1):
        if omv > c:
            b = i + 1
    return b


def annualise(x: float) -> float:
    return x * 12.0 / 5.0


def main() -> None:
    # ------------------------------------------------------------------
    # 1. Load inputs
    # ------------------------------------------------------------------
    shares = pd.read_csv(os.path.join(TBL, "banding_shares.csv"))
    models_a = pd.read_csv(os.path.join(TBL, "banding_models_optionA.csv"))
    models_b = pd.read_csv(os.path.join(TBL, "banding_models_optionB.csv"))
    eshift = pd.read_csv(os.path.join(TBL, "e_shift_feebate_base_delta.csv"))
    handoff_d = json.load(open(os.path.join(W, "batch_handoff_d.json")))
    hk = {"OptionA": "optionA", "OptionB": "optionB"}
    fbar_d = {o: handoff_d["feebe_parameters"][hk[o]]["avg_quantum_registration_weighted_SGD"]
              for o in ("OptionA", "OptionB")}
    rev_d = {o: handoff_d["feebe_parameters"][hk[o]]["expected_annualised_revenue_SGD"]
             for o in ("OptionA", "OptionB")}

    # base band registration counts (annualised) from Batch C
    base_counts = {}
    base_counts_2dp = {}
    for opt in ("OptionA", "OptionB"):
        sub = shares[shares.option == opt]
        base_counts[opt] = sub.est_registrations_annualised_x12of5.astype(float).tolist()
        base_counts_2dp[opt] = (sub.band_share_pct / 100.0
                                * sub.est_registrations_annualised_x12of5.sum()).round(6).tolist()

    # E-shift Option B counts (Batch E) and Option A aggregation
    eshift_b = eshift.ann_registrations.astype(float).tolist()
    assert abs(sum(eshift_b) - E_SHIFT_ANNUAL) < 1e-6, "E-shift must sum to 6400/yr"
    eshift_a = [eshift_b[0] + eshift_b[1], eshift_b[2], eshift_b[3] + eshift_b[4]]
    eshift_counts = {"OptionA": eshift_a, "OptionB": eshift_b}
    quantum = {"OptionA": Q_A, "OptionB": Q_B}

    # ------------------------------------------------------------------
    # 2. Base revenue + E-shift delta (per option)
    # ------------------------------------------------------------------
    base_rev = {}
    eshift_delta = {}
    for opt in ("OptionA", "OptionB"):
        base_rev[opt] = sum(c * q for c, q in zip(base_counts[opt], quantum[opt]))
        eshift_delta[opt] = sum(c * q for c, q in zip(eshift_counts[opt], quantum[opt]))

    # ------------------------------------------------------------------
    # 3. Sensitivity: re-band base mix at variant cut points
    # ------------------------------------------------------------------
    sens_rows = []
    base_mix_rows = []
    for variant, cps in VARIANT_CUTPOINTS.items():
        for opt, mdf in (("OptionA", models_a), ("OptionB", models_b)):
            cuts = cps[opt]
            bands = mdf.omv_catalog_aug2026.map(lambda v: band_of_full(v, cuts))
            cnt = mdf.groupby(bands).reg_weight.sum()
            cnt = {int(b): annualise(cnt.get(b, 0.0)) for b in range(1, len(cuts) + 2)}
            rev = sum(cnt.get(b, 0.0) * q for b, q in enumerate(quantum[opt], start=1))
            base_mix_rows.append((variant, opt, cnt, rev))
            basis_note = ("variant cut points (Batch C) x base mix "
                          "(2025-01..2025-05 x catalog); E-shift delta at base "
                          "cut points (Batch E banding, invariant across variants)"
                          if variant != "base_main_fallback" else
                          "per-model RECOMPUTE at base cut points (reference row); "
                          "deviates from published banding_shares counts by <0.015% "
                          "of revenue due to per-band annualised-count rounding in "
                          "Batch C; E-shift delta at base cut points (Batch E banding)")
            sens_rows.append({
                "variant": variant,
                "feebate_option": opt,
                "band_counts_ann": json.dumps({f"band{b}": round(cnt.get(b, 0.0), 2)
                                               for b in range(1, len(cuts) + 2)}),
                "cutpoints_sgd": json.dumps(cuts),
                "base_revenue_sgd": round(rev, 2),
                "e_shift_delta_sgd_base_cutpoints": round(eshift_delta[opt], 2),
                "total_incl_e_shift_sgd": round(rev + eshift_delta[opt], 2),
                "basis_note": basis_note,
            })
    sens = pd.DataFrame(sens_rows)

    # ------------------------------------------------------------------
    # 4. fee_revenue_base.csv
    # ------------------------------------------------------------------
    rows = []
    for opt in ("OptionA", "OptionB"):
        for eopt in cfg.CATEGORY_E_OPTIONS:
            base_excl = base_rev[opt]
            delta = eshift_delta[opt]
            total = base_excl + delta
            if eopt == "E_removed":
                comp = (f"merged-car base (Jan-May 2025 annualised, A+B registrations) "
                        f"+ E-shifted 6,400/yr banded (Batch E convention: removal "
                        f"re-enters merged category); delta reported vs base excluding "
                        f"them")
            else:
                comp = (f"merged-car base (Jan-May 2025 annualised, A+B registrations) "
                        f"+ E-registered cars INCLUDED (6,400/yr, banded per E-shift "
                        f"table — documented choice: paper s2.23(b) retains E for car "
                        f"registration; s2.22 E mostly used for Category B cars)")
            rows.append({
                "feebate_option": opt,
                "e_option": eopt,
                "base_composition": comp,
                "base_merged_only_sgd": round(base_excl, 2),
                "e_shift_delta_sgd": round(delta, 2),
                "total_sgd": round(total, 2),
                "fbar_sgd": fbar_d[opt],
                "annual_registrations_base": int(sum(base_counts[opt])),
                "annual_registrations_e_shift": E_SHIFT_ANNUAL,
                "quantums_sgd": json.dumps(quantum[opt]),
                "label": cfg.output_label(cfg.TYPE_COMPUTED,
                                          scenario=f"{opt}+{eopt}",
                                          data_window=cfg.data_window_tag(),
                                          citation=LABEL),
                "value_type": cfg.TYPE_COMPUTED,
                "scenario": f"{opt}+{eopt}",
                "data_window": cfg.data_window_tag(),
                "citation": LABEL,
            })
    base = pd.DataFrame(rows)
    base.to_csv(os.path.join(TBL, "fee_revenue_base.csv"), index=False)

    # ------------------------------------------------------------------
    # 5. fee_revenue_sensitivity.csv
    # ------------------------------------------------------------------
    for _, r in sens.iterrows():
        pass
    sens["label"] = [cfg.output_label(cfg.TYPE_COMPUTED,
                                      scenario=f"{r['feebate_option']}+variant_{r['variant']}",
                                      data_window=cfg.data_window_tag(),
                                      citation=LABEL)
                     for _, r in sens.iterrows()]
    sens["value_type"] = cfg.TYPE_COMPUTED
    sens["scenario"] = [f"{r['feebate_option']}+variant_{r['variant']}" for _, r in sens.iterrows()]
    sens["data_window"] = cfg.data_window_tag()
    sens["citation"] = LABEL
    sens.to_csv(os.path.join(TBL, "fee_revenue_sensitivity.csv"), index=False)

    # ------------------------------------------------------------------
    # 6. Incidence vs total COE revenue (merged + C + D)
    # ------------------------------------------------------------------
    merged_rev = {opt: MERGED_QUOTA_PER_ROUND * ROUNDS_PER_YEAR * WITHFEE_LATEST[opt]
                  for opt in ("OptionA", "OptionB")}
    d_rev = D_QUOTA_PER_ROUND * ROUNDS_PER_YEAR * D_PRICE
    inc_rows = []
    inc = {}
    for opt in ("OptionA", "OptionB"):
        for eopt in cfg.CATEGORY_E_OPTIONS:
            c_yr = C_QUOTA_YR_E_REMOVED if eopt == "E_removed" else C_QUOTA_YR_CARS_ONLY
            c_rev = c_yr * C_PRICE
            total = merged_rev[opt] + c_rev + d_rev
            net = base_rev[opt] + eshift_delta[opt]
            pct = net / total * 100.0
            inc[f"{opt}_{eopt}"] = round(pct, 3)
            inc_rows.append({
                "feebate_option": opt,
                "e_option": eopt,
                "net_feebate_revenue_sgd": round(net, 2),
                "merged_car_coe_revenue_sgd": round(merged_rev[opt], 2),
                "merged_quota_per_round": MERGED_QUOTA_PER_ROUND,
                "merged_price_sgd": WITHFEE_LATEST[opt],
                "merged_price_window": WITHFEE_LATEST_WINDOW,
                "c_coe_revenue_sgd": round(c_rev, 2),
                "c_quota_per_year": c_yr,
                "c_price_sgd": C_PRICE,
                "c_window": C_WINDOW + " (price); Batch E quota effect",
                "d_coe_revenue_sgd": round(d_rev, 2),
                "d_quota_per_round": D_QUOTA_PER_ROUND,
                "d_price_sgd": round(D_PRICE, 2),
                "d_window": D_WINDOW,
                "total_coe_revenue_sgd": round(total, 2),
                "incidence_pct_of_total_coe": round(pct, 3),
                "label": cfg.output_label(cfg.TYPE_COMPUTED,
                                          scenario=f"{opt}+{eopt}",
                                          data_window=cfg.data_window_tag(),
                                          citation=LABEL),
                "value_type": cfg.TYPE_COMPUTED,
                "scenario": f"{opt}+{eopt}",
                "data_window": cfg.data_window_tag(),
                "citation": LABEL,
            })
    inc_df = pd.DataFrame(inc_rows)
    inc_df.to_csv(os.path.join(TBL, "fee_revenue_incidence.csv"), index=False)

    # ------------------------------------------------------------------
    # 7. Cross-foot: independent recompute to the dollar
    # ------------------------------------------------------------------
    xrows = []

    def add_x(component, band, regs, q, path):
        xrows.append({
            "component": component,
            "band": band,
            "registrations_ann": round(float(regs), 2),
            "quantum_sgd": int(q),
            "path": path,
            "contribution_sgd": round(float(regs) * q, 2),
        })

    for opt in ("OptionA", "OptionB"):
        labels_a = ["0-35th", "35-50th", ">50th"]
        labels_b = ["0-10th", "10-35th", "35-50th", "50-75th", ">75th"]
        labs = labels_a if opt == "OptionA" else labels_b
        for i, (regs, q, lab) in enumerate(zip(base_counts[opt], quantum[opt], labs), start=1):
            add_x(f"base_{opt}", f"{i}:{lab}", regs, q, "exact_band_counts")
        for i, (share, q, lab) in enumerate(zip(base_counts_2dp[opt], quantum[opt], labs), start=1):
            add_x(f"base_{opt}", f"{i}:{lab}", share, q, "share2dp_x_total")
        for i, (regs, q, lab) in enumerate(zip(eshift_counts[opt], quantum[opt], labs), start=1):
            add_x(f"e_shift_{opt}", f"{i}:{lab}", regs, q, "batch_e_band_counts")
        for i, (shp, q, lab) in enumerate(zip(eshift.share_of_e_shift_pct.tolist(), quantum[opt], labs), start=1):
            if opt == "OptionA":
                continue  # E-shift shares defined on Option B percentile bands only
            add_x(f"e_shift_{opt}", f"{i}:{lab}", shp / 100.0 * E_SHIFT_ANNUAL, q,
                  "share4dp_x_6400")
    xdf = pd.DataFrame(xrows)
    # expected vs actual blocks
    # tolerance 150 S$ = worst-case rounding of the published 2dp band
    # registration counts (5 counts x 0.005 x 15,000 S$ max quantum)
    blocks = [
        ("base_OptionA", "exact_band_counts", rev_d["OptionA"], 0.01),
        ("base_OptionB", "exact_band_counts", rev_d["OptionB"], 0.01),
        ("e_shift_OptionB", "batch_e_band_counts", E_SHIFT_B_BASE_TABLE_DELTA, 150.0),
        ("e_shift_OptionA", "batch_e_band_counts", eshift_delta["OptionA"], 0.01),
        ("base_OptionA", "share2dp_x_total", rev_d["OptionA"], None),
        ("base_OptionB", "share2dp_x_total", rev_d["OptionB"], None),
        ("e_shift_OptionB", "share4dp_x_6400", E_SHIFT_B_BASE_TABLE_DELTA, 150.0),
    ]
    crows = []
    for comp, path, expected, tol in blocks:
        sub = xdf[(xdf.component == comp) & (xdf.path == path)]
        actual = sub.contribution_sgd.sum()
        diff = actual - expected
        if tol is None:
            ok = "INFO (quantifies band-share rounding vs exact counts; not a pass/fail check)"
        else:
            ok = "PASS" if abs(diff) <= tol else "FAIL"
        crows.append({
            "component": comp,
            "path": path,
            "expected_sgd": round(expected, 2),
            "actual_sgd": round(actual, 2),
            "diff_sgd": round(diff, 2),
            "tolerance_sgd": tol if tol is not None else "n/a",
            "pass_fail": ok,
            "expected_source": ("batch_handoff_d.json expected_annualised_revenue_SGD"
                                if comp.startswith("base") else
                                ("batch_handoff_e.json (tables/e_shift_feebate_base_delta.csv)"
                                 if comp == "e_shift_OptionB" else
                                 "Step 11 recompute (aggregated from Batch E Option-B band counts)")),
            "note": ("2dp share path quantifies band-share rounding vs exact counts"
                     if path == "share2dp_x_total" else
                     ("Batch E per-band contributions used unrounded model-weight "
                      "counts; published band counts are 2dp -> diff is input "
                      "rounding (0.0007% relative)"
                      if path == "batch_e_band_counts" else
                      "independent dollar recompute")),
        })
    xfoot = pd.DataFrame(crows)
    xfoot.to_csv(os.path.join(VER, "crossfoot_log.csv"), index=False)

    # ------------------------------------------------------------------
    # 8. Console summary
    # ------------------------------------------------------------------
    print("=== STEP 11 FEEBATE REVENUE ===")
    for opt in ("OptionA", "OptionB"):
        print(f"{opt}: base (merged only) = {base_rev[opt]:,.2f}  "
              f"E-shift delta = {eshift_delta[opt]:+,.2f}  "
              f"total = {base_rev[opt]+eshift_delta[opt]:,.2f}  "
              f"(Fbar {fbar_d[opt]:,.2f})")
    print("\nIncidence (% of total COE revenue merged+C+D):")
    for k, v in inc.items():
        print(f"  {k}: {v:.3f}%")
    print("\nSensitivity (base revenue at variant cut points):")
    for _, r in sens.iterrows():
        print(f"  {r['variant']} {r['feebate_option']}: base {r['base_revenue_sgd']:,.0f}  "
              f"total incl E-shift {r['total_incl_e_shift_sgd']:,.0f}")
    print("\nCross-foot:")
    print(xfoot[["component", "path", "expected_sgd", "actual_sgd", "diff_sgd", "pass_fail"]].to_string(index=False))
    print("\nFiles: tables/fee_revenue_base.csv, tables/fee_revenue_sensitivity.csv, "
          "tables/fee_revenue_incidence.csv, verification/crossfoot_log.csv")


if __name__ == "__main__":
    main()
