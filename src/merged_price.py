#!/usr/bin/env python3
"""
Step 7 — Merged A+B clearing price, NO feebate (src/merged_price.py).

CONSTRUCTION (full derivation in methodology_notes.md s.9)
----------------------------------------------------------
Step 6 delivered FIRST-DIFFERENCE (M3) bidding-response specs per category:

    dP_c = alpha_c * d(bids_received)_c + beta_c * d(quota)_c      (S$ units)

M3 identifies SLOPES only (levels are non-stationary / trend-contaminated
per NC3), so the level-consistent demand representation used for the
clearing-price solve is the LOCAL linearization of the M3 surface,
anchored at each round's own observed clearing point (P_c,t, Q_c,t):

    N_c(P) = Q_c,t - (P - P_c,t) / alpha_c          (bids, at COE price P)

i.e. alpha_c = dP/dB|Q is the marginal bid spacing (S$/bid) at the margin,
so the demand slope is dN/dP = -1/alpha_c, and N_c(P_c,t) = Q_c,t exactly
(the observed auction is reproduced: no tuning). beta_c does NOT enter the
price solve: the clearing condition N_A(P_M) + N_B(P_M) = Q_M already maps
quota -> price through the demand curves, and with Q_M = Q_A + Q_B the
quota-response terms cancel identically. (beta_c is reported for context
only; it would matter for exogenous merged-quota changes in later steps.)

MERGED CLEARING PRICE (no feebate)
    N_M(P) = N_A(P) + N_B(P)
    P_M    = (P_A/alpha_A + P_B/alpha_B + (Q_A + Q_B - Q_M)) / kappa_M
    kappa_M = 1/alpha_A + 1/alpha_B                    (merged demand slope)
Back-solved history uses Q_M = Q_A,t + Q_B,t per round, so
P_M,t = (P_A,t/alpha_A + P_B,t/alpha_B) / kappa_M, a convex combination
(weights w_A = (1/alpha_A)/kappa_M ~ 0.62, w_B ~ 0.38) of the two observed
prices — the merged price must sit between the two category prices, which
is the Step 7 invariant.

FORWARD SCENARIO (regime start 2027-01, config.REGIME_START_DATE)
  - Demand anchored at the LAST observed round (2026-10 b2); bidder pools
    held at that level (no demand growth assumed).
  - Merged quota held at the most recent 6 biddings' (rounds') A+B average
    (2026-08 b1 .. 2026-10 b2) = 2137.5.
  - Horizon 2027-01 b1 .. 2027-12 b2 (24 rounds, 2 biddings/month).
  - Clearly separated (segment = forward_scenario) from back-solved
    history (segment = back_solved_history).

STATIC BOUNDS
  min/max of the OBSERVED A and B per-bidding premiums over the recent
  window 2025-01..2026-10 (22 months, 44 biddings per category).

UNCERTAINTY BAND (p10-p90)
  Monte Carlo: 10,000 draws, alpha_A ~ U(CI), alpha_B ~ U(CI) with the 80%
  NW-HAC CIs from tables/demand_curves.csv, parameters drawn independently
  (joint distribution not identified; bounding-style scenario band, not a
  statistical CI). Point estimate uses the exact M3 point coefficients.
  Depends on Step 6 curve evidence grades: catA = MEDIUM, catB = LOW
  (B's wide CI dominates the band) — SCENARIO ELASTICITY ONLY.

OUTPUTS
  tables/merged_price_nofeebate.csv   (back-solved + forward, point + p10-p90,
                                       static bounds columns, SCENARIO-labeled)
  tables/quota_reallocation.csv       (quota/bid reallocation under single
                                       price / single PQP, per round)
  verification/invariant_checks.csv   (INV-7 created here; Step 8 appends)
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
VER = config.DIR_VERIFICATION
os.makedirs(TBL, exist_ok=True)
os.makedirs(VER, exist_ok=True)

# ----------------------------------------------------------------------
# Constants (single source: config + prior batch outputs — nothing
# re-invented)
# ----------------------------------------------------------------------
ALPHA_TERM = "dbids_received"      # M3 slope, S$/bid
BETA_TERM = "dquota"               # M3 quota term, S$/unit (context only)
DATA_WINDOW_COE = "coe_bids 2010-01..2026-10 (per-bidding clearing prices)"
STATIC_BOUNDS_WINDOW = "2025-01..2026-10 (recent 22 months; 44 biddings per category)"
STATIC_BOUNDS_START = "2025-01"
FORWARD_START = "2027-01"
FORWARD_MONTHS = 12                # 2027-01 .. 2027-12
BIDDINGS_PER_MONTH = 2
RECENT_ROUNDS_FOR_QUOTA = 6        # most recent biddings (rounds) for quota hold
MC_DRAWS = 10_000
MC_SEED = 20261023

GRADE_NOTE = (
    "Step 6 M3 first-difference grades: catA=MEDIUM (p=1.5e-15, CI "
    "[+3.76,+6.21] S$/bid), catB=LOW (p=0.0003, CI [+3.74,+12.75] S$/bid, "
    "NC3 BG p=0.003) — SCENARIO ELASTICITY ONLY, no structural causal claim"
)
CITATION_NOFEE = (
    "data.gov.sg COE bidding results (resource d_69b3380ad7e51aff3a7dcc84eba52b8a); "
    "coefficients: tables/demand_curves.csv (M3_fdiff); static bounds from observed "
    "A/B premiums " + STATIC_BOUNDS_WINDOW + "; see verification/provenance_log.csv"
)
SCEN_NOFEE = "merged_AB_nofeebate"


# ----------------------------------------------------------------------
# Data
# ----------------------------------------------------------------------
def load_panel() -> pd.DataFrame:
    """A/B per-bidding panel, sorted by (month, bidding_no)."""
    p = pd.read_csv(os.path.join(config.DIR_DATA_PROCESSED,
                                 "coe_panel_perbidding.csv"))
    p = p[p.category.isin(["A", "B"])].copy()
    for c in ("premium", "quota", "bids_received"):
        p[c] = pd.to_numeric(p[c], errors="coerce")
    p = p.sort_values(["month", "bidding_no"]).reset_index(drop=True)
    p["m"] = pd.to_datetime(p.month, format="%Y-%m")
    assert p[["premium", "quota", "bids_received"]].isna().sum().sum() == 0
    assert (p.groupby("category").size() == 398).all(), "expect 398 obs/cat"
    return p


def load_m3() -> dict:
    """M3 coefficients + 80% NW-HAC CIs from tables/demand_curves.csv."""
    dc = pd.read_csv(os.path.join(TBL, "demand_curves.csv"))
    out = {}
    for cat in ("A", "B"):
        r_a = dc[(dc.category == cat) & (dc.spec == "M3_fdiff")
                 & (dc.term == ALPHA_TERM)].iloc[0]
        r_b = dc[(dc.category == cat) & (dc.spec == "M3_fdiff")
                 & (dc.term == BETA_TERM)].iloc[0]
        out[cat] = {
            "alpha": float(r_a.coef), "alpha_ci_lo": float(r_a.ci_lo),
            "alpha_ci_hi": float(r_a.ci_hi), "alpha_p": float(r_a.p),
            "beta": float(r_b.coef), "beta_ci_lo": float(r_b.ci_lo),
            "beta_ci_hi": float(r_b.ci_hi),
        }
    return out


def merged_price(p_a, p_b, q_a, q_b, q_m, alpha_a, alpha_b):
    """Closed-form merged clearing price (vectorized).

    P_M = (P_A/alpha_A + P_B/alpha_B + (Q_A + Q_B - Q_M)) / kappa_M,
    kappa_M = 1/alpha_A + 1/alpha_B.
    """
    kappa = 1.0 / alpha_a + 1.0 / alpha_b
    num = (p_a / alpha_a + p_b / alpha_b + (q_a + q_b - q_m))
    return num / kappa


# ----------------------------------------------------------------------
# Path construction
# ----------------------------------------------------------------------
def build_path(panel: pd.DataFrame, m3: dict) -> pd.DataFrame:
    """Back-solved history (398 rounds) + forward scenario (24 rounds)."""
    a = panel[panel.category == "A"].set_index(["month", "bidding_no"])
    b = panel[panel.category == "B"].set_index(["month", "bidding_no"])
    idx = a.index.intersection(b.index)
    a, b = a.loc[idx], b.loc[idx]
    assert len(idx) == 398

    # ---- back-solved history ----
    p_a = a.premium.to_numpy(float)
    p_b = b.premium.to_numpy(float)
    q_a = a.quota.to_numpy(float)
    q_b = b.quota.to_numpy(float)
    bg = pd.DataFrame({
        "segment": "back_solved_history",
        "month": idx.get_level_values(0),
        "bidding_no": idx.get_level_values(1),
        "obs_premium_A": p_a, "obs_premium_B": p_b,
        "obs_quota_A": q_a, "obs_quota_B": q_b,
        "obs_bids_received_A": a.bids_received.to_numpy(float),
        "obs_bids_received_B": b.bids_received.to_numpy(float),
        "merged_quota": q_a + q_b,
        "merged_quota_basis": "observed A+B quota per round",
    })
    bg["merged_price_point"] = merged_price(
        p_a, p_b, q_a, q_b, q_a + q_b, m3["A"]["alpha"], m3["B"]["alpha"])

    # ---- forward scenario ----
    last = idx[-1]
    fa, fb = a.loc[last], b.loc[last]
    recent = pd.DataFrame({
        "month": idx.get_level_values(0),
        "bidding_no": idx.get_level_values(1),
        "quota": a.loc[idx, "quota"].to_numpy(float),
        "quota_B": b.loc[idx, "quota"].to_numpy(float),
    })
    recent["q_m"] = recent.quota + recent.quota_B
    q_fwd = float(recent.tail(RECENT_ROUNDS_FOR_QUOTA).q_m.mean())
    q_fwd_basis = (
        f"SCENARIO: hold merged A+B quota at the most recent "
        f"{RECENT_ROUNDS_FOR_QUOTA} biddings (rounds) average "
        f"({recent.tail(RECENT_ROUNDS_FOR_QUOTA).month.iloc[0]} b"
        f"{int(recent.tail(RECENT_ROUNDS_FOR_QUOTA).bidding_no.iloc[0])} .. "
        f"{recent.month.iloc[-1]} b{int(recent.bidding_no.iloc[-1])}) "
        f"= {q_fwd:g}")

    months = pd.date_range(FORWARD_START, periods=FORWARD_MONTHS, freq="MS")
    fw_rows = []
    for m in months:
        for bid in (1, 2):
            fw_rows.append((m.strftime("%Y-%m"), bid))
    fw = pd.DataFrame(fw_rows, columns=["month", "bidding_no"])
    p_f = merged_price(
        np.full(len(fw), fa.premium), np.full(len(fw), fb.premium),
        np.full(len(fw), fa.quota), np.full(len(fw), fb.quota),
        np.full(len(fw), q_fwd), m3["A"]["alpha"], m3["B"]["alpha"])
    fw = fw.assign(
        segment="forward_scenario",
        obs_premium_A=np.nan, obs_premium_B=np.nan,
        obs_quota_A=np.nan, obs_quota_B=np.nan,
        obs_bids_received_A=np.nan, obs_bids_received_B=np.nan,
        merged_quota=q_fwd, merged_quota_basis=q_fwd_basis,
        merged_price_point=p_f)
    fw = fw[bg.columns]

    out = pd.concat([bg, fw], ignore_index=True)
    out.attrs["anchor_round"] = f"{last[0]} b{last[1]}"
    out.attrs["q_fwd"] = q_fwd
    out.attrs["q_fwd_basis"] = q_fwd_basis
    return out


def mc_band(path: pd.DataFrame, m3: dict) -> tuple[np.ndarray, np.ndarray]:
    """p10/p90 of the merged price from MC over (alpha_A, alpha_B) ~ U(CI)."""
    rng = np.random.default_rng(MC_SEED)
    n = len(path)
    aa = rng.uniform(m3["A"]["alpha_ci_lo"], m3["A"]["alpha_ci_hi"],
                     size=(MC_DRAWS, n))
    ab = rng.uniform(m3["B"]["alpha_ci_lo"], m3["B"]["alpha_ci_hi"],
                     size=(MC_DRAWS, n))
    p_a = path.obs_premium_A.to_numpy(float)
    p_b = path.obs_premium_B.to_numpy(float)
    q_a = path.obs_quota_A.to_numpy(float)
    q_b = path.obs_quota_B.to_numpy(float)
    q_m = path.merged_quota.to_numpy(float)
    # Forward rows have NaN obs levels; anchor them at the last round for
    # the draw computation (same closed form as build_path's forward).
    last_obs = path.index[path.obs_premium_A.notna()][-1]
    fill = {
        "p_a": path.loc[last_obs, "obs_premium_A"],
        "p_b": path.loc[last_obs, "obs_premium_B"],
        "q_a": path.loc[last_obs, "obs_quota_A"],
        "q_b": path.loc[last_obs, "obs_quota_B"],
    }
    p_a = np.where(np.isnan(p_a), fill["p_a"], p_a)
    p_b = np.where(np.isnan(p_b), fill["p_b"], p_b)
    q_a = np.where(np.isnan(q_a), fill["q_a"], q_a)
    q_b = np.where(np.isnan(q_b), fill["q_b"], q_b)
    P = (p_a / aa + p_b / ab + (q_a + q_b - q_m)) / (1.0 / aa + 1.0 / ab)
    return np.percentile(P, 10, axis=0), np.percentile(P, 90, axis=0)


def static_bounds(panel: pd.DataFrame) -> tuple[float, float]:
    w = panel[panel.m >= pd.Timestamp("2025-01-01")]  # STATIC_BOUNDS_START
    return float(w.premium.min()), float(w.premium.max())


# ----------------------------------------------------------------------
# Quota / bid reallocation under single price / single PQP
# ----------------------------------------------------------------------
def quota_reallocation(path: pd.DataFrame, m3: dict) -> pd.DataFrame:
    """Split the merged quota across the former A/B bidder pools at the
    common merged price; single PQP = 3-month MA of the scenario merged
    price series (config.PQP_WINDOW_MONTHS = 3)."""
    aa, ab = m3["A"]["alpha"], m3["B"]["alpha"]
    p_a = path.obs_premium_A.to_numpy(float)
    p_b = path.obs_premium_B.to_numpy(float)
    q_a = path.obs_quota_A.to_numpy(float)
    q_b = path.obs_quota_B.to_numpy(float)
    last_obs = path.index[path.obs_premium_A.notna()][-1]
    fa = {"p_a": path.loc[last_obs, "obs_premium_A"],
          "p_b": path.loc[last_obs, "obs_premium_B"],
          "q_a": path.loc[last_obs, "obs_quota_A"],
          "q_b": path.loc[last_obs, "obs_quota_B"]}
    p_a = np.where(np.isnan(p_a), fa["p_a"], p_a)
    p_b = np.where(np.isnan(p_b), fa["p_b"], p_b)
    q_a = np.where(np.isnan(q_a), fa["q_a"], q_a)
    q_b = np.where(np.isnan(q_b), fa["q_b"], q_b)
    P = path.merged_price_point.to_numpy(float)
    qa_at = q_a - (P - p_a) / aa
    qb_at = q_b - (P - p_b) / ab
    out = path[["segment", "month", "bidding_no"]].copy()
    out["merged_price"] = P
    out["obs_quota_A"] = path.obs_quota_A
    out["obs_quota_B"] = path.obs_quota_B
    out["merged_quota"] = path.merged_quota
    out["quota_A_at_common_price"] = qa_at
    out["quota_B_at_common_price"] = qb_at
    out["delta_quota_A"] = qa_at - np.where(path.obs_quota_A.notna(),
                                            path.obs_quota_A, q_a)
    out["delta_quota_B"] = qb_at - np.where(path.obs_quota_B.notna(),
                                            path.obs_quota_B, q_b)
    out["obs_bids_received_A"] = path.obs_bids_received_A
    out["obs_bids_received_B"] = path.obs_bids_received_B
    out["bid_surplus_A"] = (path.obs_bids_received_A - qa_at
                            ).where(path.obs_bids_received_A.notna())
    out["bid_surplus_B"] = (path.obs_bids_received_B - qb_at
                            ).where(path.obs_bids_received_B.notna())
    # Single PQP: 3-month moving average of monthly merged price
    monthly = path.groupby("month").merged_price_point.mean()
    pqp = monthly.rolling(config.PQP_WINDOW_MONTHS, min_periods=1).mean()
    out["single_pqp_3m"] = out.month.map(pqp)
    return out


# ----------------------------------------------------------------------
# Invariant INV-7
# ----------------------------------------------------------------------
def invariant_7(path: pd.DataFrame, smin: float, smax: float) -> dict:
    hist = path[path.segment == "back_solved_history"]
    lo = np.minimum(hist.obs_premium_A, hist.obs_premium_B)
    hi = np.maximum(hist.obs_premium_A, hist.obs_premium_B)
    P = hist.merged_price_point.to_numpy(float)
    ok_hist = bool(np.all((P >= lo.to_numpy() - 1e-9)
                          & (P <= hi.to_numpy() + 1e-9)))
    fwd = path[path.segment == "forward_scenario"]
    Pf = fwd.merged_price_point.to_numpy(float)
    ok_fwd = bool(np.all((Pf >= smin - 1e-9) & (Pf <= smax + 1e-9)))
    ok = ok_hist and ok_fwd
    return {
        "check_id": "INV-7",
        "step": "Step 7 (merged price, no feebate)",
        "check": ("no-response merged price within static bounds: every "
                  "back-solved merged price within [min, max] of the same "
                  "round's observed A/B prices; every forward-scenario "
                  "merged price within the static min/max bounds of the "
                  "current observed A/B price series"),
        "expected": (f"back-solved: min(A,B)_t <= P_M,t <= max(A,B)_t for "
                     f"all 398 rounds; forward: P_M within [{smin:g}, "
                     f"{smax:g}] (static bounds, {STATIC_BOUNDS_WINDOW}) "
                     "for all 24 rounds"),
        "actual": (f"back-solved: min P_M={P.min():g}, max P_M={P.max():g}, "
                   f"violations={int(np.sum(~((P >= lo.to_numpy() - 1e-9) & (P <= hi.to_numpy() + 1e-9))))}); "
                   f"forward: min P_M={Pf.min():g}, max P_M={Pf.max():g}, "
                   f"violations={int(np.sum(~((Pf >= smin - 1e-9) & (Pf <= smax + 1e-9))))}"),
        "status": "PASS" if ok else "FAIL",
        "details": ("P_M is a convex combination of the two observed prices "
                    "(weights 1/alpha over kappa_M) for the back-solved "
                    "rounds; the forward path is anchored at the last "
                    "observed round with the recent merged quota, so it "
                    "stays inside the recent A/B price range"),
    }


def invariant_frame(rows: list[dict]) -> pd.DataFrame:
    cols = ["check_id", "step", "check", "expected", "actual", "status",
            "details", "label", "value_type", "scenario", "data_window",
            "citation"]
    stamped = []
    for r in rows:
        r = dict(r)
        r["label"] = config.output_label(
            config.TYPE_COMPUTED, scenario="invariant_check",
            data_window=DATA_WINDOW_COE, citation=CITATION_NOFEE)
        r["value_type"] = config.TYPE_COMPUTED
        r["scenario"] = "invariant_check"
        r["data_window"] = DATA_WINDOW_COE
        r["citation"] = CITATION_NOFEE
        stamped.append(r)
    return pd.DataFrame(stamped, columns=cols)


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main() -> dict:
    panel = load_panel()
    m3 = load_m3()
    path = build_path(panel, m3)
    p10, p90 = mc_band(path, m3)
    path["merged_price_p10"] = p10
    path["merged_price_p90"] = p90

    smin, smax = static_bounds(panel)
    path["static_bound_min"] = smin
    path["static_bound_max"] = smax
    hist = path.segment == "back_solved_history"
    lo = np.minimum(path.obs_premium_A, path.obs_premium_B)
    hi = np.maximum(path.obs_premium_A, path.obs_premium_B)
    P = path.merged_price_point
    path["within_round_AB_bounds"] = np.where(
        hist, (P >= lo - 1e-9) & (P <= hi + 1e-9), "")
    path["within_static_bounds"] = np.where(
        ~hist, (P >= smin - 1e-9) & (P <= smax + 1e-9), "")

    # ---- write merged_price_nofeebate.csv ----
    out = path.copy()
    out["static_bounds_window"] = STATIC_BOUNDS_WINDOW
    out["curve_grade_dependency"] = GRADE_NOTE
    out["label"] = config.output_label(
        config.TYPE_SCENARIO, scenario=SCEN_NOFEE,
        data_window=DATA_WINDOW_COE + "; static bounds " +
        STATIC_BOUNDS_WINDOW, citation=CITATION_NOFEE)
    out["value_type"] = config.TYPE_SCENARIO
    out["scenario"] = SCEN_NOFEE
    out["data_window"] = (DATA_WINDOW_COE + "; static bounds "
                          + STATIC_BOUNDS_WINDOW)
    out["citation"] = CITATION_NOFEE
    out = out[[
        "segment", "month", "bidding_no",
        "obs_premium_A", "obs_premium_B",
        "obs_quota_A", "obs_quota_B",
        "obs_bids_received_A", "obs_bids_received_B",
        "merged_quota", "merged_quota_basis",
        "merged_price_point", "merged_price_p10", "merged_price_p90",
        "static_bound_min", "static_bound_max", "static_bounds_window",
        "within_round_AB_bounds", "within_static_bounds",
        "curve_grade_dependency", "label", "value_type", "scenario",
        "data_window", "citation",
    ]]
    out_path = os.path.join(TBL, "merged_price_nofeebate.csv")
    out.to_csv(out_path, index=False)

    # ---- quota reallocation ----
    real = quota_reallocation(path, m3)
    real["curve_grade_dependency"] = GRADE_NOTE
    real["label"] = config.output_label(
        config.TYPE_SCENARIO, scenario="quota_reallocation_single_price",
        data_window=DATA_WINDOW_COE, citation=(
            CITATION_NOFEE + "; single PQP = 3-month MA of the scenario "
            "merged price (config.PQP_WINDOW_MONTHS=3; paper fn3 p.12)"))
    real["value_type"] = config.TYPE_SCENARIO
    real["scenario"] = "quota_reallocation_single_price"
    real["data_window"] = DATA_WINDOW_COE
    real["citation"] = (CITATION_NOFEE + "; single PQP = 3-month MA of the "
                        "scenario merged price (config.PQP_WINDOW_MONTHS=3)")
    real_path = os.path.join(TBL, "quota_reallocation.csv")
    real.to_csv(real_path, index=False)

    # ---- invariant INV-7 (Step 8 appends INV-8a/8b; keep them) ----
    inv = invariant_7(path, smin, smax)
    inv_df = invariant_frame([inv])
    inv_path = os.path.join(VER, "invariant_checks.csv")
    if os.path.exists(inv_path):
        existing = pd.read_csv(inv_path)
        existing = existing[~existing.check_id.isin(["INV-7"])]
        inv_df = pd.concat([existing, inv_df], ignore_index=True)
    inv_df.to_csv(inv_path, index=False)

    # ---- console summary ----
    last_hist = path[path.segment == "back_solved_history"].iloc[-1]
    fwd = path[path.segment == "forward_scenario"]
    print("=" * 72)
    print("STEP 7 — MERGED A+B CLEARING PRICE, NO FEEBATE")
    print("=" * 72)
    print(f"alpha_A = {m3['A']['alpha']:+.4f} S$/bid (CI "
          f"[{m3['A']['alpha_ci_lo']:+.2f}, {m3['A']['alpha_ci_hi']:+.2f}]), "
          f"grade MEDIUM")
    print(f"alpha_B = {m3['B']['alpha']:+.4f} S$/bid (CI "
          f"[{m3['B']['alpha_ci_lo']:+.2f}, {m3['B']['alpha_ci_hi']:+.2f}]), "
          f"grade LOW")
    kappa = 1 / m3["A"]["alpha"] + 1 / m3["B"]["alpha"]
    print(f"kappa_M = {kappa:.6f} bids/S$  (w_A={1/m3['A']['alpha']/kappa:.3f}, "
          f"w_B={1/m3['B']['alpha']/kappa:.3f})")
    print(f"static bounds ({STATIC_BOUNDS_WINDOW}): "
          f"[{smin:g}, {smax:g}]")
    print(f"forward quota hold (last {RECENT_ROUNDS_FOR_QUOTA} rounds): "
          f"{path.attrs['q_fwd']:g}  anchor round {path.attrs['anchor_round']}")
    print(f"\nlatest back-solved ({last_hist.month} b{int(last_hist.bidding_no)}): "
          f"A={last_hist.obs_premium_A:g} B={last_hist.obs_premium_B:g} "
          f"-> merged {last_hist.merged_price_point:.1f} "
          f"[p10 {last_hist.merged_price_p10:.1f}, p90 {last_hist.merged_price_p90:.1f}]")
    print(f"forward 2027-12 b2: {fwd.iloc[-1].merged_price_point:.1f} "
          f"[p10 {fwd.iloc[-1].merged_price_p10:.1f}, "
          f"p90 {fwd.iloc[-1].merged_price_p90:.1f}]")
    print(f"\nINV-7: {inv['status']} — {inv['actual']}")
    print(f"\nWrote: {os.path.relpath(out_path, WS)} ({len(out)} rows), "
          f"{os.path.relpath(real_path, WS)} ({len(real)} rows), "
          f"{os.path.relpath(inv_path, WS)}")
    return {
        "path": path, "m3": m3, "smin": smin, "smax": smax,
        "real": real, "inv": inv, "kappa": kappa,
        "q_fwd": path.attrs["q_fwd"],
        "q_fwd_basis": path.attrs["q_fwd_basis"],
        "anchor_round": path.attrs["anchor_round"],
    }


if __name__ == "__main__":
    main()
