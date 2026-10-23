"""Step 13 (part 2) — Renewal-holder impacts (Batch F).

Prices every renewal scenario at the CELL-LEVEL merged PQP from
data/processed/pqp_by_cell.csv (Step 9) — NEVER the merged clearing
price, NEVER a reused option-level PQP. The latest transition-year
value per cell (2027-12) is the primary price basis; the 2027-01 value
(capturing the one-round E-removal pulse in the removal cells) is
reported as the transition-start context.

Renewal-feebate toggle rule (the ENTIRE effect of the toggle):
  * renewal_feebate_no : renewal cost per vehicle = PQP only (the band
    quantum does NOT apply to renewals)
  * renewal_feebate_yes: renewal cost per vehicle = PQP + band quantum
    (quantum applied at renewal)
  The toggle changes ONLY the quantum — never the price path (verified
  by Batch E INV-10: all 4 toggle pairs share identical PQP series).

Cohort: vintage 2017 (regime start 2027-01-01 minus the 10-year COE
term; stated in every label). Volume 91,922 (full-cohort renewal
assumption — upper bound). pre-A / pre-B / E-residual split per
data/processed/renewal_cohort_banded.csv (PROPOSED_2025pct basis;
official LTA 2017 A/B counts).

Outputs:
  tables/renewal_impact_master.csv — one row per cell of
    {OptionA, B} x {E_removed, E_cars_only} x {renewal_feebate_no, yes}:
    annual cost per band (pointer), aggregate, delta vs no-feebate,
    per-capita cost, pre-A vs pre-B winners/losers, transition-year
    effect.
  tables/renewal/<cell>.csv — per cell, per band x cohort class:
    registrations, quantum, PQP, annual cost, delta vs no-quantum.

Every table/label carries the regime start date, the derived vintage
(2017 = 2027 - 10), and the cell-level-PQP price basis.
"""
from __future__ import annotations

import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import config as cfg

W = cfg.WORKSPACE_ROOT
TBL = cfg.DIR_TABLES
OUT_DIR = os.path.join(TBL, "renewal")
os.makedirs(OUT_DIR, exist_ok=True)

VINTAGE = cfg.TRANSITION_YEAR_VINTAGE
REGIME = cfg.REGIME_START_DATE.isoformat()
PRICE_BASIS = ("cell-level merged PQP, data/processed/pqp_by_cell.csv (Step 9); "
               "latest transition-year value 2027-12; 2027-01 reported as "
               "transition-start context; NEVER clearing price, NEVER reused "
               "option-level PQP")
MIX_WINDOW = "2017-01..2017-12 (OBSERVED) + LTA OMV 2017 edition"
CITE = ("Step 13 renewal impact: PROPOSED quantums (paper s2.18); cell-level PQP "
        "(Batch E, pqp_by_cell.csv); vintage 2017 = 2027-01-01 regime start - 10-yr "
        "COE term; full-cohort renewal assumption (upper bound); 2016 cohort "
        "pre-regime EXCLUDED")


def label(scenario: str) -> str:
    return cfg.output_label(cfg.TYPE_SCENARIO, scenario=scenario,
                            data_window=MIX_WINDOW, citation=CITE)


def main() -> None:
    q = pd.read_csv(os.path.join(cfg.DIR_DATA_PROCESSED, "pqp_by_cell.csv"))
    cohort = pd.read_csv(os.path.join(cfg.DIR_DATA_PROCESSED,
                                      "renewal_cohort_banded.csv"))
    cohort = cohort[cohort.cutpoint_basis == "PROPOSED_2025pct"]

    # latest transition-year PQP per cell + 2027-01
    q = q.sort_values("month")
    pqp = {}
    for cell in cfg.MASTER_MATRIX_CELLS:
        s = q[q.cell == cell]
        pqp[cell] = {
            "2027_12": float(s[s.month == "2027-12"].pqp_sgd.iloc[0]),
            "2027_01": float(s[s.month == "2027-01"].pqp_sgd.iloc[0]),
            "window": "2027-10;2027-11;2027-12 (3-month MA, 6 bids)",
        }

    # quantum per option-band
    quantums = {"OptionA": cfg.FEEBATE_QUANTUMS_OPTION_A,
                "OptionB": cfg.FEEBATE_QUANTUMS_OPTION_B}

    master_rows = []
    for cell in cfg.MASTER_MATRIX_CELLS:
        opt = cell.split("+")[0]
        eopt = cell.split("+")[1]
        toggle = cell.split("+")[2]
        p = pqp[cell]
        pq, pjan = p["2027_12"], p["2027_01"]
        on = toggle == "renewal_feebate_yes"
        qb = quantums[opt]

        c = cohort[(cohort.option == opt)
                   & (cohort.cohort_class != "ALL")].copy()
        c = c[c.band != "ALL"]
        c["band_i"] = c.band.astype(int)
        c["quantum"] = c.band_i.map(lambda b: qb[b - 1])
        c["cost_q"] = c.quantum * (1.0 if on else 0.0)
        c["annual_cost"] = c.registrations * (pq + c.cost_q)

        # per-cell detail file
        det = c[["band", "band_label", "cohort_class", "registrations",
                 "quantum_sgd", "avg_omv_sgd"]].copy()
        det["quantum_applied_sgd"] = c.cost_q.values
        det["renewal_cost_per_vehicle_sgd"] = (pq + c.cost_q).values
        det["annual_cost_sgd"] = c.annual_cost.values
        det["delta_vs_no_quantum_sgd"] = c.annual_cost.values - (
            c.registrations * pq).values
        for col, val in [("pqp_2027_12_sgd", pq), ("pqp_2027_01_sgd", pjan),
                         ("price_basis", PRICE_BASIS),
                         ("label", label(cell)),
                         ("value_type", cfg.TYPE_SCENARIO),
                         ("scenario", cell),
                         ("data_window", MIX_WINDOW),
                         ("citation", CITE)]:
            det[col] = val
        det.to_csv(os.path.join(OUT_DIR, f"{cell}.csv"), index=False)

        # aggregates
        total_n = float(c.registrations.sum())
        total_cost = float(c.annual_cost.sum())
        quantum_rev = float((c.registrations * c.cost_q).sum())
        base_cost = total_n * pq

        def cls_stats(cls):
            s = c[c.cohort_class == cls]
            n = float(s.registrations.sum())
            q_rev = float((s.registrations * s.cost_q).sum())
            return n, q_rev, (q_rev / n) if n else 0.0

        n_a, q_a, pc_a = cls_stats("pre_A")
        n_b, q_b, pc_b = cls_stats("pre_B")
        n_e, q_e, pc_e = cls_stats("E_residual")
        if on:
            winner = "pre_A" if pc_a < pc_b else ("pre_B" if pc_b < pc_a else "tie")
            loser = {"pre_A": "pre_B", "pre_B": "pre_A"}[winner]
        else:
            winner = "tie (no quantum)"
            loser = "tie (no quantum)"

        master_rows.append({
            "cell": cell,
            "feebate_option": opt,
            "e_option": eopt,
            "renewal_toggle": toggle,
            "pqp_2027_12_sgd": round(pq, 2),
            "pqp_2027_01_sgd": round(pjan, 2),
            "pqp_window": p["window"],
            "cohort_volume": int(total_n),
            "annual_cost_pqp_only_sgd": round(base_cost, 2),
            "annual_quantum_revenue_sgd": round(quantum_rev, 2),
            "annual_cost_total_sgd": round(total_cost, 2),
            "delta_vs_no_feebate_cell_sgd": round(quantum_rev, 2),
            "per_vehicle_cost_pqp_only_sgd": round(pq, 2),
            "per_vehicle_cost_total_sgd": round(total_cost / total_n, 2),
            "preA_registrations": int(n_a),
            "preA_quantum_sgd": round(q_a, 2),
            "preA_per_vehicle_quantum_sgd": round(pc_a, 2),
            "preB_registrations": int(n_b),
            "preB_quantum_sgd": round(q_b, 2),
            "preB_per_vehicle_quantum_sgd": round(pc_b, 2),
            "Eresidual_registrations": int(n_e),
            "Eresidual_per_vehicle_quantum_sgd": round(pc_e, 2),
            "winner_preA_vs_preB": winner,
            "loser_preA_vs_preB": loser,
            "preA_minus_preB_per_vehicle_sgd": round(pc_a - pc_b, 2),
            "transition_year_effect": (
                f"2027 total renewal spend {total_cost:,.0f} S$ at 2027-12 PQP "
                f"{pq:,.2f} (flat forward level); start-of-year PQP 2027-01 "
                f"{pjan:,.2f} (pulse +{pjan-pq:,.2f} S$ in removal cells only); "
                f"quantum effect {quantum_rev:,.0f} S$/yr"),
            "band_costs_pointer": f"tables/renewal/{cell}.csv",
            "price_basis": PRICE_BASIS,
            "vintage": VINTAGE,
            "vintage_derivation": f"{REGIME[:4]} - {cfg.INITIAL_COE_TERM_YEARS}",
            "regime_start": REGIME,
            "label": label(cell),
            "value_type": cfg.TYPE_SCENARIO,
            "scenario": cell,
            "data_window": MIX_WINDOW,
            "citation": CITE,
        })

    m = pd.DataFrame(master_rows)
    m.to_csv(os.path.join(TBL, "renewal_impact_master.csv"), index=False)

    print("=== STEP 13 RENEWAL IMPACT ===")
    cols = ["cell", "pqp_2027_12_sgd", "annual_cost_total_sgd",
            "delta_vs_no_feebate_cell_sgd", "preA_per_vehicle_quantum_sgd",
            "preB_per_vehicle_quantum_sgd", "winner_preA_vs_preB"]
    print(m[cols].to_string(index=False))
    print(f"\nFiles: tables/renewal_impact_master.csv + "
          f"{len(os.listdir(OUT_DIR))} per-cell files in tables/renewal/")


if __name__ == "__main__":
    main()
