"""
Step 15 — Master scenario matrix assembly (Batch G).

Joins Steps 7-13 into the 8 cells of {Option A, B} x {E removed,
E cars-only} x {renewal feebate no, yes}:

  * per-cell PRICE PATH  (merged-car scenario price per bidding round,
    2010-01..2027-12): option-level with-fee path (Batch D,
    tables/merged_price_option{A,B}_withfee.csv) + the Step 10 E-shift
    one-round demand pulse at 2027-01 b1 (+1,428.14 S$;
    tables/ec_scenario_E_removed.csv) for E_removed cells; UNADJUSTED
    for E_cars_only cells (paper s2.23(b): no car-demand shift). The two
    cells differing only in the renewal-feebate toggle share the IDENTICAL
    price path (the toggle affects renewal quanta only — config docstring).
    4 distinct paths are written as 8 per-cell files under
    data/processed/price_paths/<cell>.csv (toggle pairs byte-identical,
    verified programmatically below — not assumed).
  * cell-level PQP (data/processed/pqp_by_cell.csv, Step 9): latest
    2027-12 value per cell; the E-shift pulse shows in the cell PQP for
    2027-01..2027-03 in removal cells only.
  * feebate revenue summary (Batch F, Step 11): tables/fee_revenue_base.csv
    (net revenue incl. E-registered flow, both E options identical per
    option) + tables/fee_revenue_sensitivity.csv (S1/S2 cut-point
    sensitivity range).
  * renewal-cost summary (Batch F, Step 13): tables/renewal_impact_master.csv
    (2017 vintage cohort, cell-level PQP 2027-12, full-cohort renewal
    upper bound; toggle = quantum only).

Every row/file carries the config label stamp (regime start 2027-01-01 +
derived vintage 2017 + scenario tag).

Outputs:
  tables/master_matrix.csv          (one row per cell, 8 rows)
  data/processed/price_paths/<cell>.csv  (8 files, 4 distinct)

Programmatic checks (all asserted; results printed + recorded in handoff):
  T1  toggle-pair identity: the 4 {no/yes} file pairs are byte-identical
      (sha256) AND value-identical (pandas price column comparison).
  T2  pulse cross-foot: cell PQP (E_removed) - cell PQP (E_cars_only)
      for 2027-01..2027-03 == pulse/6 per option (the pulse round is one
      of the 6 prices in each of those 3-month PQP windows).
  T3  latest price consistency: path latest (2027-12) == pqp_2027_12
      (flat forward_scenario: price is constant from 2026-11 on).
  T4  renewal join consistency: renewal_impact_master pqp_2027_12 ==
      pqp_by_cell 2027-12 per cell.
  T5  revenue join: fee_revenue_base totals match per cell (identical
      across E options within an option — Batch F convention).
"""
from __future__ import annotations

import hashlib
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

WS = config.WORKSPACE_ROOT
TBL = config.DIR_TABLES
DATA = config.DIR_DATA_PROCESSED
DIR_PATHS = os.path.join(DATA, "price_paths")
os.makedirs(DIR_PATHS, exist_ok=True)

MIX_WINDOW = config.data_window_tag()
PATHS_WINDOW = (
    "coe_bids 2010-01..2026-10 (per-bidding clearing prices); "
    "band mix 2025-01..2025-05 (frozen at 2025-05)"
)


def cell_label(cell: str, citation: str) -> str:
    return config.output_label(
        config.TYPE_SCENARIO, scenario=cell, data_window=PATHS_WINDOW,
        citation=citation)


# ======================================================================
# Load inputs
# ======================================================================

def load_inputs() -> dict:
    inp = {}
    inp["pqp"] = pd.read_csv(os.path.join(DATA, "pqp_by_cell.csv"))
    inp["fee_base"] = pd.read_csv(os.path.join(TBL, "fee_revenue_base.csv"))
    inp["fee_sens"] = pd.read_csv(os.path.join(TBL, "fee_revenue_sensitivity.csv"))
    inp["renewal"] = pd.read_csv(os.path.join(TBL, "renewal_impact_master.csv"))
    # price paths (option-level with-fee)
    for opt in ("A", "B"):
        inp[f"withfee_{opt}"] = pd.read_csv(
            os.path.join(TBL, f"merged_price_option{opt}_withfee.csv"))
    # Step 10 E-shift pulse (E_removed only): e_shift_price_effect_sgd
    for eopt, f in (("E_removed", "ec_scenario_E_removed"),
                    ("E_cars_only", "ec_scenario_E_cars_only")):
        ec = pd.read_csv(os.path.join(TBL, f"{f}.csv"))
        mc = ec[ec.category == "merged_car"]
        s = mc.set_index(["month", "bidding_no"]).e_shift_price_effect_sgd
        pulsed = s[s > 0]
        inp[f"pulse_{eopt}"] = pulsed
        if eopt == "E_removed":
            assert len(pulsed) == 1, "expected exactly 1 pulsed round in E_removed"
            (m, b), = pulsed.index
            assert (m, b) == ("2027-01", 1), (
                f"pulse round must be 2027-01 b1, got {(m, b)}")
        else:
            assert len(pulsed) == 0, "E_cars_only must have no car-demand pulse"
    return inp


# ======================================================================
# Price paths (4 distinct, written as 8 per-cell files)
# ======================================================================

def build_price_paths(inp: dict) -> dict:
    """Return {distinct_path_id: DataFrame} with columns
    [month, bidding_no, segment, price_sgd, pulse_applied, pulse_effect_sgd].
    E_removed = option with-fee path + pulse at 2027-01 b1;
    E_cars_only = option with-fee path unadjusted."""
    paths = {}
    pulse = float(inp["pulse_E_removed"].iloc[0])
    for opt in ("A", "B"):
        base = inp[f"withfee_{opt}"][
            ["month", "bidding_no", "segment", "withfee_price_point"]
        ].rename(columns={"withfee_price_point": "price_sgd"}).copy()
        base = base.sort_values(["month", "bidding_no"]).reset_index(drop=True)
        base["pulse_applied"] = False
        base["pulse_effect_sgd"] = 0.0
        # cars-only: unadjusted
        paths[f"Option{opt}+E_cars_only"] = base.copy()
        # removed: one-round pulse
        rm = base.copy()
        mask = (rm.month == "2027-01") & (rm.bidding_no == 1)
        assert rm[mask].shape[0] == 1, "pulse round must exist exactly once"
        rm.loc[mask, "price_sgd"] = rm.loc[mask, "price_sgd"].iloc[0] + pulse
        rm.loc[mask, "pulse_applied"] = True
        rm.loc[mask, "pulse_effect_sgd"] = pulse
        paths[f"Option{opt}+E_removed"] = rm
    return paths


def write_price_path_files(paths: dict, inp: dict) -> dict:
    """Write 8 per-cell files (toggle pairs byte-identical by construction:
    the label uses the DISTINCT path id, never the toggle). Return
    {cell: filepath}."""
    pqp = inp["pqp"]
    written = {}
    for cell in config.MASTER_MATRIX_CELLS:
        opt, eopt, toggle = cell.split("+")
        pkey = f"{opt}+{eopt}"
        df = paths[pkey].copy()
        # attach the cell PQP for each month (Step 9; NaN 2010-01/02)
        p = pqp[pqp.cell == cell][["month", "pqp_sgd"]].rename(
            columns={"pqp_sgd": "pqp_cell_sgd"})
        df = df.merge(p, on="month", how="left")
        if eopt == "E_removed":
            source = (
                f"tables/merged_price_option{opt[-1]}_withfee.csv (Batch D "
                f"option-level with-fee) + Step 10 E-shift one-round pulse "
                f"2027-01 b1 (+{df.pulse_effect_sgd.max():.4f} S$, "
                f"tables/ec_scenario_E_removed.csv)")
        else:
            source = (
                f"tables/merged_price_option{opt[-1]}_withfee.csv (Batch D "
                f"option-level with-fee), UNADJUSTED (paper s2.23(b): "
                f"E cars-only, no car-demand shift)")
        citation = (
            "Step 15 master matrix: file named by cell id; label scenario "
            "tag = DISTINCT path id so the renewal-feebate toggle pair "
            "shares byte-identical files (toggle affects renewal quanta "
            "only, never the price path); pulse cross-foot vs pqp_by_cell "
            "see src/master_matrix.py T2")
        df["price_path_source"] = source
        df["label"] = cell_label(pkey, citation)
        df["value_type"] = config.TYPE_SCENARIO
        df["scenario"] = pkey
        df["data_window"] = PATHS_WINDOW
        df["citation"] = citation
        cols = ["month", "bidding_no", "segment", "price_sgd",
                "pulse_applied", "pulse_effect_sgd", "pqp_cell_sgd",
                "price_path_source", "label", "value_type", "scenario",
                "data_window", "citation"]
        df = df[cols]
        fp = os.path.join(DIR_PATHS, f"{cell}.csv")
        df.to_csv(fp, index=False)
        written[cell] = fp
    return written


def verify_toggle_identity(written: dict) -> dict:
    """T1: toggle pairs byte-identical (sha256) AND value-identical."""
    results = {}
    for opt in ("OptionA", "OptionB"):
        for eopt in config.CATEGORY_E_OPTIONS:
            no = written[f"{opt}+{eopt}+renewal_feebate_no"]
            yes = written[f"{opt}+{eopt}+renewal_feebate_yes"]
            h_no = hashlib.sha256(open(no, "rb").read()).hexdigest()
            h_yes = hashlib.sha256(open(yes, "rb").read()).hexdigest()
            byte_identical = h_no == h_yes
            d_no = pd.read_csv(no)
            d_yes = pd.read_csv(yes)
            value_identical = d_no[["month", "bidding_no", "price_sgd",
                                    "pulse_applied", "pulse_effect_sgd",
                                    "pqp_cell_sgd"]].equals(
                d_yes[["month", "bidding_no", "price_sgd", "pulse_applied",
                       "pulse_effect_sgd", "pqp_cell_sgd"]])
            key = f"{opt}+{eopt}"
            results[key] = {
                "byte_identical": byte_identical,
                "value_identical": value_identical,
                "sha256": h_no,
            }
            assert byte_identical and value_identical, f"TOGGLE CHECK FAIL: {key}"
    return results


# ======================================================================
# Master matrix
# ======================================================================

def build_master_matrix(inp: dict, paths: dict, written: dict) -> pd.DataFrame:
    pqp = inp["pqp"]
    fee_base = inp["fee_base"]
    fee_sens = inp["fee_sens"]
    ren = inp["renewal"]
    pulse = float(inp["pulse_E_removed"].iloc[0])

    # T2: pulse cross-foot on cell PQP (removed - cars_only == pulse/6)
    pulse_xfoot = {}
    for opt in ("OptionA", "OptionB"):
        diffs = []
        for month in ("2027-01", "2027-02", "2027-03"):
            rm = float(pqp.loc[(pqp.cell == f"{opt}+E_removed+renewal_feebate_no")
                               & (pqp.month == month), "pqp_sgd"].iloc[0])
            co = float(pqp.loc[(pqp.cell == f"{opt}+E_cars_only+renewal_feebate_no")
                               & (pqp.month == month), "pqp_sgd"].iloc[0])
            diffs.append(round(rm - co, 4))
        expected = pulse / 6.0
        # tolerance 0.01: pqp_by_cell publishes each cell PQP rounded to 2dp
        # independently, so the 2027-01 diff can carry a 1-cent rounding
        # artifact (observed for OptionB: 238.03 vs raw 238.0226 — matches
        # Batch E C-removal pulse +238.03 exactly, Batch F handoff)
        pulse_xfoot[opt] = {"diffs": diffs, "expected": round(expected, 4),
                            "pass": all(abs(d - expected) <= 0.01 for d in diffs)}
        assert pulse_xfoot[opt]["pass"], f"pulse cross-foot FAIL {opt}: {diffs}"

    rows = []
    for cell in config.MASTER_MATRIX_CELLS:
        opt, eopt, toggle = cell.split("+")
        pkey = f"{opt}+{eopt}"
        path = paths[pkey]
        latest = float(path[path.month == "2027-12"]["price_sgd"].iloc[0])
        # T3: latest path price == cell PQP 2027-12 (flat forward; pqp_by_cell
        # is published at 2dp, so compare at 2dp)
        pqp_2027_12 = float(pqp.loc[(pqp.cell == cell) & (pqp.month == "2027-12"),
                                    "pqp_sgd"].iloc[0])
        assert abs(round(latest, 2) - pqp_2027_12) < 1e-9, (
            f"T3 FAIL {cell}: path latest {latest} != PQP {pqp_2027_12}")
        # T4: renewal master PQP consistency
        r = ren[ren.cell == cell].iloc[0]
        assert abs(float(r.pqp_2027_12_sgd) - pqp_2027_12) < 1e-9, (
            f"T4 FAIL {cell}")
        # T5: fee revenue (identical across E options within an option)
        fb = fee_base[(fee_base.feebate_option == opt)
                      & (fee_base.e_option == eopt)].iloc[0]
        fb_other = fee_base[(fee_base.feebate_option == opt)
                            & (fee_base.e_option != eopt)].iloc[0]
        assert abs(float(fb.total_sgd) - float(fb_other.total_sgd)) < 1e-9, (
            f"T5 FAIL {opt}: E options differ")
        # sensitivity range (base excl. E-shift flow, per-variant recompute)
        sens = fee_sens[fee_sens.feebate_option == opt]
        s1 = float(sens[sens.variant == "S1_lta2025_omv"].base_revenue_sgd.iloc[0])
        s2 = float(sens[sens.variant == "S2_uniform_weights"].base_revenue_sgd.iloc[0])
        main_base_excl = float(fb.base_merged_only_sgd)
        sens_range = (
            f"S1_lta2025_omv {s1:,.0f} / S2_uniform_weights {s2:,.0f} "
            f"(base excl. E-shift flow; main base excl. E-shift "
            f"{main_base_excl:,.0f}; cut-point sensitivity dominates, "
            f"Batch F s.13)")

        if eopt == "E_removed":
            pulse_months = ("2027-01..2027-03 (cell PQP); pulse round "
                            f"2027-01 b1 (+{pulse:.2f} S$ on price path)")
            pulse_round = "2027-01 b1"
        else:
            pulse_months = "none (unadjusted path; paper s2.23(b))"
            pulse_round = "none"

        rows.append({
            "cell_id": cell,
            "regime_start": config.REGIME_START_DATE.isoformat(),
            "vintage": config.TRANSITION_YEAR_VINTAGE,
            "vintage_derivation": (
                f"{config.REGIME_START_DATE.year} - "
                f"{config.INITIAL_COE_TERM_YEARS}-yr COE term"),
            "price_path_distinct_id": pkey,
            "price_path_file": os.path.relpath(written[cell], WS),
            "price_path_source": (
                "option-level with-fee (Batch D) + E-shift pulse 2027-01 b1"
                if eopt == "E_removed"
                else "option-level with-fee (Batch D), unadjusted"),
            "price_path_latest_2027_12_sgd": round(latest, 2),
            "price_path_pulse_round": pulse_round,
            "price_path_pulse_months": pulse_months,
            "pqp_2027_12_sgd": round(pqp_2027_12, 2),
            "pqp_2027_01_sgd_context": round(float(r.pqp_2027_01_sgd), 2),
            "feebate_revenue_base_sgd": float(fb.total_sgd),
            "feebate_revenue_base_excl_e_shift_sgd": float(fb.base_merged_only_sgd),
            "feebate_revenue_e_shift_delta_sgd": float(fb.e_shift_delta_sgd),
            "feebate_revenue_sensitivity_range": sens_range,
            "renewal_cohort_volume": int(r.cohort_volume),
            "renewal_annual_cost_total_sgd": float(r.annual_cost_total_sgd),
            "renewal_annual_cost_pqp_only_sgd": float(r.annual_cost_pqp_only_sgd),
            "renewal_delta_vs_no_feebate_sgd": float(r.delta_vs_no_feebate_cell_sgd),
            "renewal_per_vehicle_preA_sgd": float(r.preA_per_vehicle_quantum_sgd),
            "renewal_per_vehicle_preB_sgd": float(r.preB_per_vehicle_quantum_sgd),
            "renewal_winner": r.winner_preA_vs_preB,
            "renewal_loser": r.loser_preA_vs_preB,
            "renewal_detail_pointer": f"tables/renewal/{cell}.csv",
            "label": cell_label(
                cell,
                "Step 15 master matrix: joins Steps 7-13; price path "
                f"data/processed/price_paths/{cell}.csv; cell PQP "
                "data/processed/pqp_by_cell.csv (Step 9); revenue "
                "tables/fee_revenue_base.csv (Step 11); renewal "
                "tables/renewal_impact_master.csv (Step 13); "
                "regime_start 2027-01-01 (config default; "
                "REGIME_START_SOURCE); vintage 2017 = 2027 - 10-yr COE "
                "term; toggle verified: renewal-feebate pair shares "
                "identical price path (byte-identical files)"),
            "value_type": config.TYPE_SCENARIO,
            "scenario": cell,
            "data_window": MIX_WINDOW,
            "citation": (
                "PROPOSED feebate design (paper s2.15-s2.18, Tables 1/2); "
                "PROPOSED E options (paper s2.21-s2.24); renewal feebate "
                "toggle = open consultation question (quanta only)"),
        })
    df = pd.DataFrame(rows)
    return df, pulse_xfoot


def main() -> None:
    inp = load_inputs()
    paths = build_price_paths(inp)
    written = write_price_path_files(paths, inp)
    toggle = verify_toggle_identity(written)
    matrix, pulse_xfoot = build_master_matrix(inp, paths, written)
    matrix.to_csv(os.path.join(TBL, "master_matrix.csv"), index=False)

    print("=== Step 15 master matrix ===")
    cols = ["cell_id", "price_path_latest_2027_12_sgd", "pqp_2027_12_sgd",
            "feebate_revenue_base_sgd", "renewal_annual_cost_total_sgd",
            "renewal_delta_vs_no_feebate_sgd", "renewal_per_vehicle_preA_sgd",
            "renewal_per_vehicle_preB_sgd", "renewal_winner", "renewal_loser"]
    print(matrix[cols].to_string(index=False))
    print("\nT1 toggle-pair identity (byte sha256 + value):")
    for k, v in toggle.items():
        print(f"  {k}: byte={v['byte_identical']} value={v['value_identical']} "
              f"sha256={v['sha256'][:16]}...")
    print("\nT2 pulse cross-foot (cell PQP removed - cars_only, 2027-01..03):")
    for k, v in pulse_xfoot.items():
        print(f"  {k}: diffs={v['diffs']} expected={v['expected']} "
              f"pass={v['pass']}")
    n_distinct = len({v["sha256"] for v in toggle.values()})
    assert n_distinct == 4, f"expected 4 distinct path hashes, got {n_distinct}"
    print(f"\nfiles written: {len(written)} (distinct paths: "
          f"{len({c.split('+renewal_feebate')[0] for c in written})})")
    print("master_matrix.csv rows:", len(matrix))


if __name__ == "__main__":
    main()
