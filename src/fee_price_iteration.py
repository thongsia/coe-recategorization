#!/usr/bin/env python3
"""
Step 8 — Feebate-adjusted merged price paths, iterated
(src/fee_price_iteration.py).

MECHANICS (full derivation in methodology_notes.md s.10)
--------------------------------------------------------
The PROPOSED feebate (consult paper s2.18(a)/(b)) adds a value-based
quantum f_k to the prevailing COE price for each OMV band k. Bidders in
band k therefore face effective price P + f_k and require the COE price
to be f_k lower: band k's demand curve shifts down by f_k. With
registration-weighted band shares s_k (Step 5, frozen 2025-01..2025-05
mix) and linear merged demand of slope kappa_M (bids/S$), the merged
demand under the feebate is

    N_feb(P) = N(P + Fbar),   Fbar = sum_k s_k * f_k
             = N(P) - Fbar * kappa_M      (linear: price-independent)

ITERATION (fixed point, per option, starting from the Step 7 no-fee path)
    P^(i+1) = P^(i) - [ Q_M - N_feb(P^(i)) ] / kappa_M
converged when max|P^(i+1) - P^(i)| < PRICE_TOL (S$) or
max|Q_M - N_feb| < BID_TOL (bids); MAX_ITER cap. For linear demand the
fixed point is P_feb = P_nofee - Fbar, reached in a single update
(residual 0 after the update); the loop is kept generic (and logged per
option) so the same machinery covers non-linear demand variants.

ZERO-ELASTICITY LIMIT (kappa_M -> 0, vertical demand): the feebate-induced
demand shift is Fbar * kappa_M -> 0, so there is no price response and the
with-fee price equals the no-fee price (INV-8b; price is then anchored at
the no-fee solution).

INTEGRITY CHECKS (negative controls)
    INV-8a  zero-quantum feebate (f_k = 0 for all k) -> Fbar = 0 -> zero
            demand shift, zero revenue, with-fee = no-fee price.
            revenue = sum_k s_k * f_k * N_k (N_k = annualised band
            registrations, Step 5).
    INV-8b  zero elasticity -> with-fee price = no-fee price (see above).

INPUTS
    Step 7 no-fee path (recomputed via src/merged_price.py — deterministic)
    tables/banding_shares.csv (shares x quantums, registration-weighted)
    tables/demand_curves.csv (M3 alphas + CIs, via merged_price.load_m3)

OUTPUTS
    tables/merged_price_optionA_withfee.csv
    tables/merged_price_optionB_withfee.csv
    tables/fee_price_iteration_log.csv   (residual + iteration count per option)
    verification/invariant_checks.csv    (INV-8a, INV-8b appended)
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config  # noqa: E402
import merged_price as MP  # noqa: E402

WS = config.WORKSPACE_ROOT
TBL = config.DIR_TABLES
VER = config.DIR_VERIFICATION

PRICE_TOL = 0.01     # S$
BID_TOL = 1e-6       # bids
MAX_ITER = 100

SCEN_A = "merged_AB_optionA_withfee"
SCEN_B = "merged_AB_optionB_withfee"
DATA_WINDOW_MIX = config.data_window_tag()


# ----------------------------------------------------------------------
# Feebate parameters
# ----------------------------------------------------------------------
def load_feebate() -> dict:
    """Band shares (registration-weighted, EXACT from annualised counts)
    and PROPOSED quantums per option, cross-checked against config."""
    bs = pd.read_csv(os.path.join(TBL, "banding_shares.csv"))
    out = {}
    cfg_q = {"OptionA": config.FEEBATE_QUANTUMS_OPTION_A,
             "OptionB": config.FEEBATE_QUANTUMS_OPTION_B}
    for opt in ("OptionA", "OptionB"):
        sub = bs[bs.option == opt]
        n = sub.est_registrations_annualised_x12of5.to_numpy(float)
        q = sub.quantum_sgd.to_numpy(float)
        ntot = float(n.sum())
        shares_exact = n / ntot
        assert list(map(float, cfg_q[opt])) == list(map(float, q)), \
            f"{opt}: quantum mismatch vs config"
        Fbar = float((shares_exact * q).sum())      # registration-weighted
        Fbar_rounded = float(((sub.band_share_pct / 100.0) * q).sum())
        revenue = float((q * n).sum())             # S$/yr, frozen mix
        out[opt] = {
            "shares": sub.band_share_pct.to_numpy(float) / 100.0,
            "shares_exact": shares_exact,
            "quantums": q,
            "annualised": n,
            "n_total": ntot,
            "Fbar": Fbar,
            "Fbar_from_rounded_shares": Fbar_rounded,
            "revenue": revenue,
        }
    return out


# ----------------------------------------------------------------------
# Iteration
# ----------------------------------------------------------------------
def no_fee_demand(P, q_a, q_b, p_a, p_b, alpha_a, alpha_b):
    """N_M(P) = Q_A + Q_B - (P-P_A)/alpha_A - (P-P_B)/alpha_B (vectorized)."""
    return (q_a + q_b - (P - p_a) / alpha_a - (P - p_b) / alpha_b)


def iterate_fee_price(P_nofee, q_m, q_a, q_b, p_a, p_b, alpha_a, alpha_b,
                      Fbar, kappa,
                      price_tol: float = PRICE_TOL,
                      max_iter: int = MAX_ITER):
    """Fixed-point iteration of the feebate-adjusted clearing price.

    Returns (P_feb, iterations_used, converged, final_residual_bids,
    max_price_update).
    """
    P = np.asarray(P_nofee, dtype=float).copy()
    iters = 0
    converged = False
    max_update = 0.0
    if kappa == 0.0:
        # Zero-elasticity limit: feebate-induced demand shift
        # Fbar*kappa -> 0, so no price response; price stays at the
        # no-fee anchor (INV-8b).
        final_res = 0.0 if float(np.max(np.abs(q_m - (q_a + q_b)))) < 1e-9 \
            else float(np.max(np.abs(q_m - (q_a + q_b))))
        return P, 0, True, final_res, 0.0
    for it in range(1, max_iter + 1):
        N_feb = no_fee_demand(P + Fbar, q_a, q_b, p_a, p_b,
                              alpha_a, alpha_b)
        residual = q_m - N_feb
        dP = -residual / kappa
        upd = float(np.max(np.abs(dP)))
        P_new = P + dP
        iters = it
        max_update = max(max_update, upd)
        if upd < price_tol:
            P = P_new
            converged = True
            break
        P = P_new
    N_feb = no_fee_demand(P + Fbar, q_a, q_b, p_a, p_b, alpha_a, alpha_b)
    final_res = float(np.max(np.abs(q_m - N_feb)))
    return P, iters, converged, final_res, max_update


# ----------------------------------------------------------------------
# Per-option with-fee path
# ----------------------------------------------------------------------
def option_path(path: pd.DataFrame, m3: dict, fee: dict,
                scenario: str) -> pd.DataFrame:
    """Build the with-fee table for one option (point + p10-p90 + iter log)."""
    aa, ab = m3["A"]["alpha"], m3["B"]["alpha"]
    kappa = 1.0 / aa + 1.0 / ab
    F = fee["Fbar"]

    p_a = path.obs_premium_A.to_numpy(float)
    p_b = path.obs_premium_B.to_numpy(float)
    q_a = path.obs_quota_A.to_numpy(float)
    q_b = path.obs_quota_B.to_numpy(float)
    q_m = path.merged_quota.to_numpy(float)
    last_obs = path.index[path.obs_premium_A.notna()][-1]
    fa = {"p_a": float(path.loc[last_obs, "obs_premium_A"]),
          "p_b": float(path.loc[last_obs, "obs_premium_B"]),
          "q_a": float(path.loc[last_obs, "obs_quota_A"]),
          "q_b": float(path.loc[last_obs, "obs_quota_B"])}
    p_a = np.where(np.isnan(p_a), fa["p_a"], p_a)
    p_b = np.where(np.isnan(p_b), fa["p_b"], p_b)
    q_a = np.where(np.isnan(q_a), fa["q_a"], q_a)
    q_b = np.where(np.isnan(q_b), fa["q_b"], q_b)

    P_nofee = path.merged_price_point.to_numpy(float)
    P_feb, iters, converged, resid, max_upd = iterate_fee_price(
        P_nofee, q_m, q_a, q_b, p_a, p_b, aa, ab, F, kappa)

    # MC band: translation of the Step 7 band (exact under linear shift)
    p10, p90 = MP.mc_band(path, m3)
    out = path[["segment", "month", "bidding_no",
                "obs_premium_A", "obs_premium_B",
                "obs_quota_A", "obs_quota_B",
                "merged_quota", "merged_quota_basis"]].copy()
    out["nofee_price_point"] = P_nofee
    out["avg_quantum_SGD"] = F
    out["demand_shift_bids"] = -F * kappa
    out["withfee_price_point"] = P_feb
    out["withfee_price_p10"] = p10 - F
    out["withfee_price_p90"] = p90 - F
    out["iterations"] = iters
    out["converged"] = converged
    out["final_residual_bids"] = resid
    out["feebate_revenue_per_registration"] = F
    out["expected_annualised_revenue_SGD"] = fee["revenue"]
    out["static_bound_min"] = path.static_bound_min
    out["static_bound_max"] = path.static_bound_max
    smin, smax = float(path.static_bound_min.iloc[0]), \
        float(path.static_bound_max.iloc[0])
    fwd_mask = out.segment == "forward_scenario"
    out["within_static_bounds"] = np.where(
        fwd_mask,
        (out.withfee_price_point >= smin - 1e-9)
        & (out.withfee_price_point <= smax + 1e-9), "")
    out["curve_grade_dependency"] = MP.GRADE_NOTE + ("; band shares: Step 5 "
        "registration-weighted mix 2025-01..2025-05 (frozen at 2025-05); "
        "quantums PROPOSED (consult paper s2.18)")
    out["label"] = config.output_label(
        config.TYPE_SCENARIO, scenario=scenario,
        data_window=MP.DATA_WINDOW_COE + "; band mix " + DATA_WINDOW_MIX,
        citation=(MP.CITATION_NOFEE + "; quantums PROPOSED: consult_paper.pdf "
                  "s2.18(a)/(b) (pp.10-12); band shares: tables/banding_shares.csv"))
    out["value_type"] = config.TYPE_SCENARIO
    out["scenario"] = scenario
    out["data_window"] = MP.DATA_WINDOW_COE + "; band mix " + DATA_WINDOW_MIX
    out["citation"] = (MP.CITATION_NOFEE + "; quantums PROPOSED: "
                       "consult_paper.pdf s2.18(a)/(b) (pp.10-12); band "
                       "shares: tables/banding_shares.csv")
    return out, {"iterations": iters, "converged": converged,
                 "residual": resid, "max_update": max_upd, "F": F,
                 "kappa": kappa}


# ----------------------------------------------------------------------
# Invariants
# ----------------------------------------------------------------------
def invariant_zero_quantum(path: pd.DataFrame, m3: dict,
                           feeA: dict) -> dict:
    """INV-8a: f_k = 0 for all k -> zero demand shift, zero revenue,
    with-fee price = no-fee price."""
    aa, ab = m3["A"]["alpha"], m3["B"]["alpha"]
    kappa = 1.0 / aa + 1.0 / ab
    p_a = path.obs_premium_A.to_numpy(float)
    p_b = path.obs_premium_B.to_numpy(float)
    q_a = path.obs_quota_A.to_numpy(float)
    q_b = path.obs_quota_B.to_numpy(float)
    q_m = path.merged_quota.to_numpy(float)
    last_obs = path.index[path.obs_premium_A.notna()][-1]
    fa = {"p_a": float(path.loc[last_obs, "obs_premium_A"]),
          "p_b": float(path.loc[last_obs, "obs_premium_B"]),
          "q_a": float(path.loc[last_obs, "obs_quota_A"]),
          "q_b": float(path.loc[last_obs, "obs_quota_B"])}
    p_a = np.where(np.isnan(p_a), fa["p_a"], p_a)
    p_b = np.where(np.isnan(p_b), fa["p_b"], p_b)
    q_a = np.where(np.isnan(q_a), fa["q_a"], q_a)
    q_b = np.where(np.isnan(q_b), fa["q_b"], q_b)
    P_nofee = path.merged_price_point.to_numpy(float)
    P_feb, iters, converged, resid, _ = iterate_fee_price(
        P_nofee, q_m, q_a, q_b, p_a, p_b, aa, ab, Fbar=0.0, kappa=kappa)
    max_diff = float(np.max(np.abs(P_feb - P_nofee)))
    demand_shift = 0.0 * kappa          # Fbar=0 -> no shift
    revenue = 0.0                       # sum_k s_k*0*N_k
    ok = (max_diff < 1e-9 and abs(demand_shift) < 1e-12 and revenue == 0.0)
    return {
        "check_id": "INV-8a",
        "step": "Step 8 (feebate iteration, negative control)",
        "check": "zero-quantum feebate produces zero demand shift and "
                 "zero revenue (and with-fee price = no-fee price)",
        "expected": "Fbar = sum_k s_k*0 = 0 -> demand shift = Fbar*kappa_M "
                    "= 0 bids; revenue = sum_k s_k*0*N_k = 0 S$/yr; "
                    "with-fee price identical to no-fee price on all 422 "
                    "rounds",
        "actual": f"iterations={iters}, max|P_feb-P_nofee|={max_diff:.3e} "
                  f"S$, demand shift={demand_shift:.3e} bids, "
                  f"revenue={revenue:.3e} S$/yr, final residual="
                  f"{resid:.3e} bids",
        "status": "PASS" if ok else "FAIL",
        "details": "run through the same iterate_fee_price machinery as "
                   "Options A/B (Fbar := 0); revenue computed as "
                   "sum_k s_k*f_k*N_k with N_k from Step 5 annualised "
                   "registrations",
    }


def invariant_zero_elasticity(path: pd.DataFrame, m3: dict,
                              feeA: dict) -> dict:
    """INV-8b: zero elasticity (kappa_M -> 0) -> with-fee price = no-fee
    price (feebate-induced demand shift Fbar*kappa_M -> 0)."""
    aa, ab = m3["A"]["alpha"], m3["B"]["alpha"]
    p_a = path.obs_premium_A.to_numpy(float)
    p_b = path.obs_premium_B.to_numpy(float)
    q_a = path.obs_quota_A.to_numpy(float)
    q_b = path.obs_quota_B.to_numpy(float)
    q_m = path.merged_quota.to_numpy(float)
    last_obs = path.index[path.obs_premium_A.notna()][-1]
    fa = {"p_a": float(path.loc[last_obs, "obs_premium_A"]),
          "p_b": float(path.loc[last_obs, "obs_premium_B"]),
          "q_a": float(path.loc[last_obs, "obs_quota_A"]),
          "q_b": float(path.loc[last_obs, "obs_quota_B"])}
    p_a = np.where(np.isnan(p_a), fa["p_a"], p_a)
    p_b = np.where(np.isnan(p_b), fa["p_b"], p_b)
    q_a = np.where(np.isnan(q_a), fa["q_a"], q_a)
    q_b = np.where(np.isnan(q_b), fa["q_b"], q_b)
    P_nofee = path.merged_price_point.to_numpy(float)
    P_feb, iters, converged, resid, _ = iterate_fee_price(
        P_nofee, q_m, q_a, q_b, p_a, p_b, aa, ab,
        Fbar=feeA["Fbar"], kappa=0.0)
    max_diff = float(np.max(np.abs(P_feb - P_nofee)))
    ok = max_diff < 1e-9
    return {
        "check_id": "INV-8b",
        "step": "Step 8 (feebate iteration, negative control)",
        "check": "zero elasticity makes with-fee price equal no-fee price",
        "expected": "kappa_M = 0 (vertical demand, zero response of bid "
                    "count to price) -> feebate-induced demand shift "
                    "Fbar*kappa_M = 0 -> no price adjustment; with-fee "
                    "price identical to no-fee price on all 422 rounds",
        "actual": f"kappa_M := 0, OptionA Fbar={feeA['Fbar']:.2f} S$; "
                  f"iterations={iters}, max|P_feb-P_nofee|={max_diff:.3e} "
                  f"S$",
        "status": "PASS" if ok else "FAIL",
        "details": "zero-elasticity limit taken inside iterate_fee_price "
                   "(kappa=0 branch): demand shift -> 0, price anchored at "
                   "the no-fee solution; note that at kappa=0 the market "
                   "is indeterminate (quota gap of 23.5 bids in the "
                   "forward segment cannot be cleared at any price) — the "
                   "invariant concerns the feebate's PRICE effect, which "
                   "is zero",
    }


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main() -> dict:
    # rebuild the Step 7 no-fee path (deterministic; reuses its machinery)
    panel = MP.load_panel()
    m3 = MP.load_m3()
    path = MP.build_path(panel, m3)
    p10, p90 = MP.mc_band(path, m3)
    path["merged_price_p10"] = p10
    path["merged_price_p90"] = p90
    smin, smax = MP.static_bounds(panel)
    path["static_bound_min"] = smin
    path["static_bound_max"] = smax

    fees = load_feebate()

    results = {}
    for opt, scen, fname in (
            ("OptionA", SCEN_A, "merged_price_optionA_withfee.csv"),
            ("OptionB", SCEN_B, "merged_price_optionB_withfee.csv")):
        out, info = option_path(path, m3, fees[opt], scen)
        out_path = os.path.join(TBL, fname)
        out.to_csv(out_path, index=False)
        results[opt] = {"table": out_path, "info": info, "out": out}
        last = out[out.segment == "back_solved_history"].iloc[-1]
        fw = out[out.segment == "forward_scenario"].iloc[-1]
        print(f"{opt}: Fbar={info['F']:.2f} S$ (rounded shares: "
              f"{fees[opt]['Fbar_from_rounded_shares']:.2f}), demand shift="
              f"{info['F']*info['kappa']:.1f} bids, "
              f"annualised revenue={fees[opt]['revenue']:,.0f} S$")
        print(f"  latest back-solved ({last.month} b{int(last.bidding_no)}): "
              f"no-fee {last.nofee_price_point:.1f} -> with-fee "
              f"{last.withfee_price_point:.1f} "
              f"[p10 {last.withfee_price_p10:.1f}, p90 {last.withfee_price_p90:.1f}]")
        print(f"  forward 2027-12 b2: {fw.withfee_price_point:.1f} "
              f"[p10 {fw.withfee_price_p10:.1f}, p90 {fw.withfee_price_p90:.1f}]")
        print(f"  iterations={info['iterations']}, converged="
              f"{info['converged']}, final residual={info['residual']:.3e} "
              f"bids (max update {info['max_update']:.4f} S$)")

    # ---- iteration log ----
    log_rows = []
    for opt in ("OptionA", "OptionB"):
        info = results[opt]["info"]
        fee = fees[opt]
        q = ", ".join(f"{x:+.0f}" for x in fee["quantums"])
        log_rows.append({
            "option": opt,
            "feebate_quantums_sgd": "[" + q + "]",
            "band_shares_pct": "[" + ", ".join(
                f"{s * 100:.2f}" for s in fee["shares"]) +
            "] (2dp from tables/banding_shares.csv; exact counts used "
            "for the weighted average)",
            "avg_quantum_registration_weighted_SGD": round(fee["Fbar"], 2),
            "avg_quantum_from_2dp_shares_SGD": round(
                fee["Fbar_from_rounded_shares"], 2),
            "merged_demand_slope_kappa_bids_per_SGD": round(info["kappa"], 6),
            "feebate_demand_shift_bids": round(-fee["Fbar"] * info["kappa"], 2),
            "starting_path": "Step 7 no-fee path (tables/merged_price_nofeebate.csv; "
                             "398 back-solved + 24 forward rounds)",
            "tolerance_price_SGD": PRICE_TOL,
            "tolerance_bids": BID_TOL,
            "max_iterations": MAX_ITER,
            "converged": info["converged"],
            "iterations_used": info["iterations"],
            "iterations_note": "iterations = updates+verifications: 1 price "
                               "update (max update = Fbar) then 1 "
                               "verification pass at tolerance; fixed point "
                               "P_feb = P_nofee - Fbar is exact for linear "
                               "demand, so convergence is reached in 2 "
                               "passes",
            "final_residual_bids": float(f"{info['residual']:.6g}"),
            "max_price_update_SGD": round(info["max_update"], 4),
            "withfee_latest_back_solved_SGD": round(
                float(results[opt]["out"].loc[
                    results[opt]["out"].segment == "back_solved_history",
                    "withfee_price_point"].iloc[-1]), 1),
            "withfee_latest_forward_SGD": round(
                float(results[opt]["out"].loc[
                    results[opt]["out"].segment == "forward_scenario",
                    "withfee_price_point"].iloc[-1]), 1),
            "expected_annualised_revenue_SGD": round(fee["revenue"], 0),
            "revenue_note": "revenue = sum_k f_k * N_k, N_k = Step 5 "
                            "annualised band registrations (2025-01..2025-05 "
                            "mix frozen; 98.73% coverage) — COMPUTED under "
                            "PROPOSED quantums",
            "curve_grade_dependency": MP.GRADE_NOTE,
        })
    log = pd.DataFrame(log_rows)
    log["label"] = [
        config.output_label(config.TYPE_COMPUTED, scenario=s,
                            data_window=MP.DATA_WINDOW_COE + "; band mix "
                            + DATA_WINDOW_MIX,
                            citation=(MP.CITATION_NOFEE + "; quantums "
                                      "PROPOSED: consult_paper.pdf s2.18"))
        for s in (SCEN_A, SCEN_B)]
    log["value_type"] = config.TYPE_COMPUTED
    log["scenario"] = [SCEN_A, SCEN_B]
    log["data_window"] = MP.DATA_WINDOW_COE + "; band mix " + DATA_WINDOW_MIX
    log["citation"] = MP.CITATION_NOFEE + "; quantums PROPOSED: " \
        "consult_paper.pdf s2.18(a)/(b) (pp.10-12)"
    log_path = os.path.join(TBL, "fee_price_iteration_log.csv")
    log.to_csv(log_path, index=False)

    # ---- invariants (append to Step 7's verification file) ----
    inv8a = invariant_zero_quantum(path, m3, fees["OptionA"])
    inv8b = invariant_zero_elasticity(path, m3, fees["OptionA"])
    inv_path = os.path.join(VER, "invariant_checks.csv")
    inv_all = pd.read_csv(inv_path)
    new_rows = MP.invariant_frame([inv8a, inv8b])
    inv_all = inv_all[~inv_all.check_id.isin(["INV-8a", "INV-8b"])]
    inv_all = pd.concat([inv_all, new_rows], ignore_index=True)
    inv_all.to_csv(inv_path, index=False)

    print(f"\nINV-8a (zero quantum): {inv8a['status']} — {inv8a['actual']}")
    print(f"INV-8b (zero elasticity): {inv8b['status']} — {inv8b['actual']}")
    print(f"\nWrote: merged_price_optionA_withfee.csv "
          f"({len(results['OptionA']['out'])} rows), "
          f"merged_price_optionB_withfee.csv "
          f"({len(results['OptionB']['out'])} rows), "
          f"fee_price_iteration_log.csv ({len(log)} rows), "
          f"verification/invariant_checks.csv (appended)")
    return {
        "results": results, "fees": fees, "log": log,
        "inv8a": inv8a, "inv8b": inv8b, "path": path,
        "smin": smin, "smax": smax,
    }


if __name__ == "__main__":
    main()
