#!/usr/bin/env python3
"""
Step 10 — Category E/C scenarios (src/ec_scenarios.py).

Runs FIRST of the Step 9-10 pair: its E-shift demand feeds the per-E-option
merged-car price paths consumed by Step 9 (src/pqp.py).

Two PROPOSED Category E options under review (consultation paper s2.23,
pp.13-14 — PROPOSED, never re-invented):
  (a) E_removed    : Category E removed entirely; urgent buyers "would need
                     to wait for the next COE bidding exercise to do so"
                     (s2.23).
  (b) E_cars_only  : Category E retained for car registration only — "car
                     buyers with urgent needs will continue to have options,
                     without impacting Category C COE supply" (s2.23).

MODELING (full derivation + assumptions in methodology_notes.md s.11)
---------------------------------------------------------------------
E demand is NOT a bidding-response curve: catE M3 grade = NOT DETECTABLE
(evidence_grading.csv: b1 p=0.494; C likewise NOT DETECTABLE, NC1 lead
p=0.018 FAIL). E/C shifts are therefore modeled as QUOTA/DEMAND additions
to the merged-car market, never via an E bidding-response slope.

REMOVAL option (E_removed)
  * E-to-car shift share (ASSUMPTION, stated): base case 100% of E demand
    re-enters the next car bidding exercise; sensitivity range 50-100%.
    Rationale: the paper's own removal mechanics say urgent buyers wait for
    the next bidding — the demand moves, it is not destroyed; no observed
    drop-out rate exists, so 100% is the neutral "demand preserved" base
    and 50% a documented lower bound allowing for churn/abandonment.
  * E-shifted DEMAND (bids) entering the merged price solve: observed E
    per-bidding bids_received, most recent 6 rounds (2026-08 b1 .. 2026-10
    b2) average x shift share. Transient treatment (ASSUMPTION): ONE-ROUND
    PULSE at 2027-01 b1 — the "next COE bidding exercise" after the regime
    starts (s2.23) — with full reversion to the option-level with-fee path
    from 2027-01 b2. E demand is episodic urgent-demand; a permanent flow
    would contradict Batch D's static bidder-pool forward design and push
    the forward price outside the static-bounds logic.
    Delta price at the pulse round: dP = dN / kappa_M (kappa_M = 0.321748
    bids/S$, Step 6 M3 closed form — same linearity that gives Batch D's
    P_feb = P_nofee - Fbar).
  * E-shifted REGISTRATIONS entering the merged-car feebate base: observed
    E per-bidding cleared quota, most recent 6 rounds average x share,
    banded by OMV with the Category-B-skewed composition from
    tables/banding_models_optionB.csv (coe_class == 'B' subset, weights
    renormalized) — paper s2.22: "In recent years, Category E COEs have
    been mostly used for Category B cars." This is a delta to the feebate
    base for Batch F revenue; it does NOT alter this step's price paths
    (Batch D Fbar is kept, documented).
  * C quota: the 10% E deregistration share returns to Category C
    (mechanism-derived, paper fn5 p.13: "Since May 2017, Category E
    receives 10% of the deregistrations from Categories A, B and C"):
    C quota x (1/0.9) = +11.11%. C PRICE response is NOT quantified:
    catC bidding-response curve NOT DETECTABLE (NC1 lead p=0.018 FAIL —
    evidence_grading.csv), so the C price path is held at the no-shock
    observed level (conservative upper bound), stated explicitly.

CARS-ONLY option (E_cars_only)
  * E restricted to the merged car category: an E COE is functionally
    equivalent to a merged-car COE, so the E premium (E price above the
    merged-car price) COLLAPSES TOWARD 0 (ASSUMPTION): linear decay to 0
    over the first 6 forward rounds (3 months ~ E TCOE validity period,
    paper fn4 p.13); base level = mean of (E premium - max(A,B premium))
    over the most recent 6 observed rounds.
  * Category C supply SHIELDED: C quota unchanged (s2.23(b) "without
    impacting Category C COE supply"); no E-flow change to C.
  * NO car-demand shift: merged-car path = the option-level with-fee path
    from Batch D, STATED EXPLICITLY and carried unadjusted.

FORWARD WINDOW
  2027-01 b1 .. 2027-12 b2 (24 rounds, 2 biddings/month) — aligned with
  Batch D's forward window; regime start 2027-01-01 (config).

OUTPUTS
  tables/ec_scenario_E_removed.csv
  tables/ec_scenario_E_cars_only.csv
      quota + price paths for merged_car, C and E; observed history
      (2010-01..2026-10, OBSERVED inputs / SCENARIO back-solved merged
      prices) + forward scenario (SCENARIO, regime/vintage stamped).
  tables/e_shift_feebate_base_delta.csv
      OMV banding of the E-shifted registration volume (feeds Batch F
      feebate revenue); frozen 2025-01..2025-05 mix tag on band weights.
  verification/invariant_checks.csv  (INV-9 row appended, idempotent)
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
# Constants (single source: config + prior batch outputs)
# ----------------------------------------------------------------------
RECENT_ROUNDS = 6            # most recent biddings for anchor averages
FORWARD_START = "2027-01"
FORWARD_MONTHS = 12
BIDDINGS_PER_MONTH = 2
PULSE_ROUND = ("2027-01", 1)  # one-round pulse round (documented choice)

# E-to-car shift share (ASSUMPTION — stated in methodology_notes.md s.11)
E_TO_CAR_SHARE_BASE = 1.00
E_TO_CAR_SHARE_SENSITIVITY = [0.50, 1.00]

# C quota mechanism: E received 10% of A/B/C deregistrations since
# May 2017 (paper fn5 p.13); on removal that 10% of C's own flow returns
# to C -> C quota x 1/0.9.
C_QUOTA_REMOVAL_FACTOR = 1.0 / 0.9

DATA_WINDOW_COE = "coe_bids 2010-01..2026-10 (per-bidding clearing prices)"
CITATION_COE = ("data.gov.sg COE bidding results (resource "
                "d_69b3380ad7e51aff3a7dcc84eba52b8a); see "
                "verification/provenance_log.csv")
CITATION_E_OPTIONS = ("PROPOSED Category E options: consult_paper.pdf "
                      "s2.21-s2.24 (pp.13-14): s2.23(a) remove entirely "
                      "(urgent buyers wait for the next COE bidding "
                      "exercise); s2.23(b) retain for car registration "
                      "only (without impacting Category C COE supply); "
                      "fn4 p.13 E TCOE validity 3 months; fn5 p.13 E "
                      "receives 10% of A/B/C deregistrations since May "
                      "2017; s2.22 E COEs mostly used for Category B "
                      "cars in recent years")
E_PREMIUM_DECAY_ROUNDS = 6   # 3 months ~ E TCOE validity (fn4 p.13)

SCEN = {
    "E_removed": "ec_scenario_E_removed",
    "E_cars_only": "ec_scenario_E_cars_only",
}


# ----------------------------------------------------------------------
# Data loading
# ----------------------------------------------------------------------
def load_panel() -> pd.DataFrame:
    p = pd.read_csv(os.path.join(config.DIR_DATA_PROCESSED,
                                 "coe_panel_perbidding.csv"))
    for c in ("premium", "quota", "bids_received"):
        p[c] = pd.to_numeric(p[c], errors="coerce")
    return p.sort_values(["month", "bidding_no", "category"]).reset_index(drop=True)


def load_m3_kappa() -> float:
    """kappa_M = 1/alpha_A + 1/alpha_B from Step 6 M3 point estimates."""
    dc = pd.read_csv(os.path.join(TBL, "demand_curves.csv"))
    m3 = dc[(dc.spec == "M3_fdiff") & (dc.term == "dbids_received")]
    alpha = m3.set_index("category")["coef"].to_dict()
    return 1.0 / alpha["A"] + 1.0 / alpha["B"]


def load_withfee(option: str) -> pd.DataFrame:
    """Batch D option-level with-fee merged path (398 back-solved +
    24 forward rows)."""
    f = os.path.join(TBL, f"merged_price_option{option[-1]}_withfee.csv")
    d = pd.read_csv(f)
    assert len(d) == 422, f"{option}: expected 422 rows, got {len(d)}"
    assert set(d.segment.unique()) == {"back_solved_history", "forward_scenario"}
    return d


def recent6(cat: str, panel: pd.DataFrame) -> pd.DataFrame:
    d = panel[panel.category == cat].tail(RECENT_ROUNDS)
    assert len(d) == RECENT_ROUNDS, f"{cat}: expected {RECENT_ROUNDS} recent rounds"
    return d


# ----------------------------------------------------------------------
# E/C scenario construction
# ----------------------------------------------------------------------
def e_premium_level(panel: pd.DataFrame) -> float:
    """Base level of the E premium above the car price: mean over the
    most recent 6 observed rounds of (E premium - max(A premium, B
    premium))."""
    rounds = []
    for _, r in panel[(panel.month >= "2026-08")
                      & (panel.category == "E")].iterrows():
        m, b = r.month, r.bidding_no
        a = panel[(panel.category == "A") & (panel.month == m)
                  & (panel.bidding_no == b)].premium.iloc[0]
        bb = panel[(panel.category == "B") & (panel.month == m)
                   & (panel.bidding_no == b)].premium.iloc[0]
        e = r.premium
        rounds.append(e - max(a, bb))
    assert len(rounds) == RECENT_ROUNDS, f"expected {RECENT_ROUNDS} E rounds"
    return float(np.mean(rounds))


def build_forward_rounds() -> list[tuple[str, int]]:
    out = []
    y = 2027
    for i in range(FORWARD_MONTHS):
        m = f"{y}-{i+1:02d}"
        for b in (1, 2):
            out.append((m, b))
    assert len(out) == 24
    return out


def ec_scenario_table(option_e: str, panel: pd.DataFrame,
                      wf_a: pd.DataFrame, wf_b: pd.DataFrame,
                      kappa: float, e_prem: float,
                      e_bids6: float, e_quota6: float,
                      c_quota6: float, c_prem6: float) -> pd.DataFrame:
    """One E-option table: merged_car / C / E rows, history + forward."""
    rows = []

    # ---- observed history (2010-01 .. 2026-10, 398 rounds) ----
    hist_a = panel[panel.category == "A"].set_index(["month", "bidding_no"])
    hist_b = panel[panel.category == "B"].set_index(["month", "bidding_no"])
    hist_c = panel[panel.category == "C"].set_index(["month", "bidding_no"])
    hist_e = panel[panel.category == "E"].set_index(["month", "bidding_no"])
    wfa_hist = wf_a[wf_a.segment == "back_solved_history"].set_index(
        ["month", "bidding_no"])
    wfb_hist = wf_b[wf_b.segment == "back_solved_history"].set_index(
        ["month", "bidding_no"])
    for (m, b) in wfa_hist.index:
        a, bb = hist_a.loc[(m, b)], hist_b.loc[(m, b)]
        rows.append(_row(
            "observed_history", m, b, "merged_car",
            quota=round(float(a.quota) + float(bb.quota), 1),
            quota_vt=config.TYPE_COMPUTED,
            quota_basis=("sum of observed A+B quota per round "
                         "(OBSERVED inputs)"),
            price=None, price_vt=config.TYPE_OBSERVED,
            price_basis="OBSERVED category premiums carried in "
                        "obs_premium_A / obs_premium_B",
            obs_a=float(a.premium), obs_b=float(bb.premium),
            nofee=float(wfa_hist.loc[(m, b), "nofee_price_point"]),
            wfa=float(wfa_hist.loc[(m, b), "withfee_price_point"]),
            wfb=float(wfb_hist.loc[(m, b), "withfee_price_point"]),
            pulse_bids=0.0, pulse_dx=0.0,
            label=config.output_label(
                config.TYPE_SCENARIO, scenario=SCEN[option_e],
                data_window=DATA_WINDOW_COE, citation=CITATION_E_OPTIONS),
        ))
        c = hist_c.loc[(m, b)]
        rows.append(_row(
            "observed_history", m, b, "C",
            quota=float(c.quota), quota_vt=config.TYPE_OBSERVED,
            quota_basis="observed per-bidding quota",
            price=float(c.premium), price_vt=config.TYPE_OBSERVED,
            price_basis="observed per-bidding clearing premium",
            label=config.output_label(
                config.TYPE_OBSERVED, data_window=DATA_WINDOW_COE,
                citation=CITATION_COE),
        ))
        e = hist_e.loc[(m, b)]
        rows.append(_row(
            "observed_history", m, b, "E",
            quota=float(e.quota), quota_vt=config.TYPE_OBSERVED,
            quota_basis="observed per-bidding quota (10% of A/B/C "
                        "deregistrations since May 2017, paper fn5 p.13)",
            price=float(e.premium), price_vt=config.TYPE_OBSERVED,
            price_basis="observed per-bidding clearing premium",
            label=config.output_label(
                config.TYPE_OBSERVED, data_window=DATA_WINDOW_COE,
                citation=CITATION_COE),
        ))

    # ---- forward scenario (2027-01 .. 2027-12, 24 rounds) ----
    wfa_fwd = wf_a[wf_a.segment == "forward_scenario"].set_index(
        ["month", "bidding_no"])
    wfb_fwd = wf_b[wf_b.segment == "forward_scenario"].set_index(
        ["month", "bidding_no"])

    removed = option_e == "E_removed"
    if removed:
        pulse_bids = E_TO_CAR_SHARE_BASE * e_bids6
        pulse_dx = pulse_bids / kappa
    else:
        pulse_bids = 0.0
        pulse_dx = 0.0

    for i, (m, b) in enumerate(build_forward_rounds()):
        # merged_car
        wfa_b = float(wfa_fwd.loc[(m, b), "withfee_price_point"])
        wfb_b = float(wfb_fwd.loc[(m, b), "withfee_price_point"])
        nofee_b = float(wfa_fwd.loc[(m, b), "nofee_price_point"])
        is_pulse = (m, b) == PULSE_ROUND and removed
        pb = pulse_bids if is_pulse else 0.0
        pdx = pulse_dx if is_pulse else 0.0
        if removed:
            mq_basis = ("SCENARIO: merged A+B quota held at last-6 average "
                       "2137.5 (Batch D convention, 2026-08 b1..2026-10 b2)")
        else:
            mq_basis = ("SCENARIO: merged A+B quota held at last-6 average "
                       "2137.5 (Batch D convention, 2026-08 b1..2026-10 b2); "
                       "no car-demand shift under cars-only")
        mp_basis = (
            "SCENARIO: option-level with-fee merged path (Batch D, "
            "PROPOSED feebate; both options carried in "
            "withfee_price_optionA_base / withfee_price_optionB_base); "
            + ("E-shift one-round demand pulse at 2027-01 b1 "
               "(assumption: base 100% of E demand, sensitivity 50-100%, "
               "one-round pulse via kappa_M; see methodology s.11)"
               if is_pulse else
               ("E-shift pulse not active this round (reverted to "
                "option-level path)" if removed else
                "no adjustment — merged path = option-level with-fee "
                "path, stated explicitly (no car-demand shift, s2.23(b))")
        ))
        rows.append(_row(
            "forward_scenario", m, b, "merged_car",
            quota=2137.5, quota_vt=config.TYPE_SCENARIO,
            quota_basis=mq_basis,
            price=None, price_vt=config.TYPE_SCENARIO,
            price_basis=mp_basis,
            obs_a=np.nan, obs_b=np.nan,
            nofee=nofee_b, wfa=wfa_b, wfb=wfb_b,
            pulse_bids=pb, pulse_dx=pdx,
            label=config.output_label(
                config.TYPE_SCENARIO, scenario=SCEN[option_e],
                data_window=DATA_WINDOW_COE, citation=CITATION_E_OPTIONS),
        ))

        # C
        if removed:
            cq = c_quota6 * C_QUOTA_REMOVAL_FACTOR
            cq_basis = (
                "MECHANISM-DERIVED (SCENARIO level): +11.11% vs cars-only "
                "level — the 10% E deregistration share returns to C "
                "(since May 2017, paper fn5 p.13), so C quota = 100% of "
                f"its own deregistration flow: last-6 avg {c_quota6:.2f}/"
                f"round x 1/0.9 = {cq:.2f}/round")
        else:
            cq = c_quota6
            cq_basis = (
                "SCENARIO: C SHIELDED — hold at last-6 average observed C "
                f"quota {c_quota6:.2f}/round; no E-flow change "
                "(s2.23(b): 'without impacting Category C COE supply')")
        cp = c_prem6
        cp_basis = (
            "SCENARIO: flat at last-6 average observed C premium "
            f"{c_prem6:.2f}/round; "
            + ("quota +11.11% recorded but C price response NOT "
               "quantified — catC bidding-response NOT DETECTABLE "
               "(NC1 lead p=0.018 FAIL, evidence_grading.csv); price held "
               "at no-shock level = conservative upper bound"
               if removed else
               "no shock to C under cars-only"))
        rows.append(_row(
            "forward_scenario", m, b, "C",
            quota=cq, quota_vt=config.TYPE_SCENARIO, quota_basis=cq_basis,
            price=cp, price_vt=config.TYPE_SCENARIO, price_basis=cp_basis,
            label=config.output_label(
                config.TYPE_SCENARIO, scenario=SCEN[option_e],
                data_window=DATA_WINDOW_COE, citation=CITATION_E_OPTIONS),
        ))

        # E
        if removed:
            eq, ep = 0.0, None
            eq_basis = ("SCENARIO: 0 — Category E removed at regime start "
                        "(PROPOSED option (a), paper s2.23)")
            ep_basis = ("n/a — no Category E bidding under this option "
                        "(urgent buyers wait for the next COE bidding "
                        "exercise, s2.23)")
        else:
            eq = e_quota6
            eq_basis = (
                "SCENARIO: E retained for cars only — hold at last-6 "
                f"average observed E quota {e_quota6:.2f}/round "
                "(mechanism: 10% of A/B/C deregistrations since May 2017, "
                "paper fn5 p.13; unchanged under cars-only)")
            decay = max(0.0, 1.0 - i / E_PREMIUM_DECAY_ROUNDS)
            prem = e_prem * decay
            ep_a = wfa_b + prem
            ep_b = wfb_b + prem
            ep_basis = (
                f"SCENARIO: E restricted to the merged car category — E "
                f"premium above merged-car price collapses toward 0: "
                f"linear decay over first {E_PREMIUM_DECAY_ROUNDS} rounds "
                f"(3 months ~ E TCOE validity, paper fn4 p.13); base "
                f"level {e_prem:.2f} = mean(E - max(A,B)) last 6 observed "
                f"rounds; this round premium {prem:.2f} "
                f"({decay:.2f} of base) added to the option-level "
                "with-fee merged price")
            rows.append(_row(
                "forward_scenario", m, b, "E",
                quota=eq, quota_vt=config.TYPE_SCENARIO,
                quota_basis=eq_basis,
                price=None, price_vt=config.TYPE_SCENARIO,
                price_basis=ep_basis,
                e_prem=prem, epa=ep_a, epb=ep_b,
                label=config.output_label(
                    config.TYPE_SCENARIO, scenario=SCEN[option_e],
                    data_window=DATA_WINDOW_COE, citation=CITATION_E_OPTIONS),
            ))
            continue
        rows.append(_row(
            "forward_scenario", m, b, "E",
            quota=eq, quota_vt=config.TYPE_SCENARIO, quota_basis=eq_basis,
            price=ep, price_vt=config.TYPE_SCENARIO, price_basis=ep_basis,
            label=config.output_label(
                config.TYPE_SCENARIO, scenario=SCEN[option_e],
                data_window=DATA_WINDOW_COE, citation=CITATION_E_OPTIONS),
        ))

    df = pd.DataFrame(rows)
    return df


def _row(segment, m, b, cat, quota, quota_vt, quota_basis, price, price_vt,
         price_basis, obs_a=np.nan, obs_b=np.nan, nofee=np.nan,
         wfa=np.nan, wfb=np.nan, pulse_bids=np.nan, pulse_dx=np.nan,
         e_prem=np.nan, epa=np.nan, epb=np.nan, label="") -> dict:
    return {
        "segment": segment, "month": m, "bidding_no": b, "category": cat,
        "quota": quota, "quota_value_type": quota_vt,
        "quota_basis": quota_basis,
        "price": price, "price_value_type": price_vt,
        "price_basis": price_basis,
        "obs_premium_A": obs_a, "obs_premium_B": obs_b,
        "nofee_price_point": nofee,
        "withfee_price_optionA_base": wfa,
        "withfee_price_optionB_base": wfb,
        "e_shift_bids": pulse_bids,
        "e_shift_price_effect_sgd": pulse_dx,
        "e_premium_over_car_sgd": e_prem,
        "e_price_optionA": epa, "e_price_optionB": epb,
        "label": label,
    }


# ----------------------------------------------------------------------
# E-shift feebate-base delta (OMV banding; feeds Batch F)
# ----------------------------------------------------------------------
def e_shift_feebate_delta(e_annual_regs: float, option_e: str) -> pd.DataFrame:
    bm = pd.read_csv(os.path.join(TBL, "banding_models_optionB.csv"))
    bsub = bm[bm.coe_class == "B"].copy()
    wtot = float(bsub.weight.sum())
    bsub["w"] = bsub.weight / wtot
    g = bsub.groupby(["band", "band_label", "quantum_sgd"], as_index=False).agg(
        share=("w", "sum"), n_models=("w", "size"),
        avg_omv=("omv_catalog_aug2026", lambda s: np.average(
            s, weights=bsub.loc[s.index, "w"])))
    g["ann_registrations"] = e_annual_regs * g.share
    g["quantum_revenue_contribution_sgd"] = g.ann_registrations * g.quantum_sgd
    g["option_basis"] = ("Category-B-skewed OMV composition: coe_class=='B' "
                         "subset of tables/banding_models_optionB.csv, "
                         "weights renormalized (paper s2.22: E COEs mostly "
                         "used for Category B cars in recent years)")
    g["citation"] = (CITATION_E_OPTIONS + "; banding: Car Cost Aug 2026 "
                     "catalog x registrations 2025-01..2025-05 (frozen)")
    rows = []
    for _, r in g.iterrows():
        rows.append({
            "option": option_e, "band": r.band, "band_label": r.band_label,
            "quantum_sgd": r.quantum_sgd,
            "share_of_e_shift_pct": round(100 * r.share, 4),
            "n_models_in_band": r.n_models,
            "avg_omv_sgd": round(r.avg_omv, 2),
            "ann_registrations": round(r.ann_registrations, 2),
            "quantum_revenue_contribution_sgd": round(
                r.quantum_revenue_contribution_sgd, 2),
            "option_basis": r.option_basis,
            "label": config.output_label(
                config.TYPE_SCENARIO, scenario=SCEN["E_removed"],
                data_window=config.data_window_tag(), citation=r.citation),
            "value_type": config.TYPE_SCENARIO,
            "scenario": SCEN["E_removed"],
            "data_window": config.data_window_tag(),
            "citation": r.citation,
        })
    df = pd.DataFrame(rows)
    assert abs(df.share_of_e_shift_pct.sum() - 100.0) < 1e-6
    assert abs(df.ann_registrations.sum() - e_annual_regs) < 1e-6
    return df


# ----------------------------------------------------------------------
# Invariant INV-9
# ----------------------------------------------------------------------
def invariant_9(tab_rem: pd.DataFrame, tab_co: pd.DataFrame,
                c_factor_check: float) -> dict:
    fr = tab_rem[(tab_rem.segment == "forward_scenario")
                 & (tab_rem.category == "C")].quota.to_numpy(float)
    fc = tab_co[(tab_co.segment == "forward_scenario")
                & (tab_co.category == "C")].quota.to_numpy(float)
    ok = bool(np.allclose(fr, fc * C_QUOTA_REMOVAL_FACTOR, rtol=0, atol=1e-9))
    pulse = tab_rem[(tab_rem.segment == "forward_scenario")
                    & (tab_rem.category == "merged_car")
                    & (tab_rem.e_shift_bids > 0)]
    ok_pulse = (len(pulse) == 1
                and pulse.month.iloc[0] == "2027-01"
                and pulse.bidding_no.iloc[0] == 1)
    e_fwd_co = tab_co[(tab_co.segment == "forward_scenario")
                      & (tab_co.category == "E")]
    ok_eprem = (bool(np.all(e_fwd_co.e_premium_over_car_sgd.to_numpy()
                            >= -1e-9))
                and bool(np.isclose(
                    e_fwd_co.e_premium_over_car_sgd.iloc[-1], 0.0,
                    atol=1e-9)))
    ok = ok and ok_pulse and ok_eprem
    n_viol = int(np.sum(~np.isclose(
        fr, fc * C_QUOTA_REMOVAL_FACTOR, rtol=0, atol=1e-9)))
    pulse_rounds = f"{len(pulse)}"
    pulse_loc = "2027-01 b1" if ok_pulse else "UNEXPECTED"
    e_term = float(e_fwd_co.e_premium_over_car_sgd.iloc[-1])
    return {
        "check_id": "INV-9",
        "step": "Step 10 (Category E/C scenarios)",
        "check": ("(1) C forward quota under removal = C forward quota "
                  "under cars-only x 1/0.9 exactly (+11.11% "
                  "mechanism-derived); (2) E-shift demand pulse is exactly "
                  "one round (2027-01 b1) in the removal table and zero "
                  "everywhere else; (3) E premium over car price decays "
                  "to exactly 0 by the end of the 6-round decay window "
                  "and stays 0 (cars-only)"),
        "expected": (f"C ratio 1/0.9={C_QUOTA_REMOVAL_FACTOR:.6f} in all 24 "
                     "forward rounds; exactly 1 pulsed merged_car round "
                     "(2027-01 b1); E premium terminal value 0"),
        "actual": (f"C ratio mean={np.mean(fr / fc):.9f} "
                   f"(violations={n_viol}); pulsed rounds={pulse_rounds} "
                   f"({pulse_loc}); E premium terminal={e_term:.9f}"),
        "status": "PASS" if ok else "FAIL",
        "details": ("C factor is mechanism-derived from paper fn5 p.13 "
                    "(10% E deregistration share since May 2017); pulse "
                    "and decay are documented assumptions "
                    "(methodology_notes.md s.11)"),
    }


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main() -> dict:
    panel = load_panel()
    kappa = load_m3_kappa()
    assert abs(kappa - 0.3217482034578917) < 1e-9, kappa

    wf_a = load_withfee("OptionA")
    wf_b = load_withfee("OptionB")

    e6 = recent6("E", panel)
    c6 = recent6("C", panel)
    e_bids6 = float(e6.bids_received.mean())
    e_quota6 = float(e6.quota.mean())
    c_quota6 = float(c6.quota.mean())
    c_prem6 = float(c6.premium.mean())
    e_prem = e_premium_level(panel)
    assert e6.month.min() == "2026-08" and e6.month.max() == "2026-10"

    e_annual_regs = e_quota6 * E_TO_CAR_SHARE_BASE * 24
    pulse_dx = E_TO_CAR_SHARE_BASE * e_bids6 / kappa

    tab_rem = ec_scenario_table("E_removed", panel, wf_a, wf_b, kappa,
                                e_prem, e_bids6, e_quota6, c_quota6,
                                c_prem6)
    tab_co = ec_scenario_table("E_cars_only", panel, wf_a, wf_b, kappa,
                               e_prem, e_bids6, e_quota6, c_quota6,
                               c_prem6)

    tab_rem.to_csv(os.path.join(TBL, "ec_scenario_E_removed.csv"),
                   index=False)
    tab_co.to_csv(os.path.join(TBL, "ec_scenario_E_cars_only.csv"),
                   index=False)

    delta = e_shift_feebate_delta(e_annual_regs, "E_removed")
    delta.to_csv(os.path.join(TBL, "e_shift_feebate_base_delta.csv"),
                 index=False)

    inv = invariant_9(tab_rem, tab_co, c_quota6)
    cols = ["check_id", "step", "check", "expected", "actual", "status",
            "details", "label", "value_type", "scenario", "data_window",
            "citation"]
    inv = dict(inv)
    inv["label"] = config.output_label(
        config.TYPE_COMPUTED, scenario="invariant_check",
        data_window=DATA_WINDOW_COE, citation=CITATION_E_OPTIONS)
    inv["value_type"] = config.TYPE_COMPUTED
    inv["scenario"] = "invariant_check"
    inv["data_window"] = DATA_WINDOW_COE
    inv["citation"] = CITATION_E_OPTIONS
    inv_df = pd.DataFrame([inv], columns=cols)
    inv_path = os.path.join(VER, "invariant_checks.csv")
    if os.path.exists(inv_path):
        existing = pd.read_csv(inv_path)
        existing = existing[~existing.check_id.isin(["INV-9"])]
        inv_df = pd.concat([existing, inv_df], ignore_index=True)
    inv_df.to_csv(inv_path, index=False)

    print("=" * 72)
    print("STEP 10 — CATEGORY E/C SCENARIOS")
    print("=" * 72)
    print(f"kappa_M = {kappa:.6f} bids/S$ (Step 6 M3 closed form)")
    print(f"E last-6 averages (2026-08 b1..2026-10 b2): bids_received "
          f"{e_bids6:.2f}/round, quota {e_quota6:.2f}/round")
    print(f"C last-6 averages: quota {c_quota6:.2f}/round, premium "
          f"{c_prem6:.2f}/round")
    print(f"E premium base level (E - max(A,B), last 6 rounds): "
          f"{e_prem:.2f} SGD")
    print(f"E->car shift share: base {E_TO_CAR_SHARE_BASE:.0%}, "
          f"sensitivity {E_TO_CAR_SHARE_SENSITIVITY}")
    print(f"E-shifted registrations: {e_quota6:.2f}/round x 24 = "
          f"{e_annual_regs:.0f}/yr (base case 100%)")
    print(f"Pulse dP (base) = {e_bids6:.2f}/{kappa:.6f} = {pulse_dx:.2f} "
          f"SGD at 2027-01 b1; sensitivity 50%: {0.5 * pulse_dx:.2f} SGD")
    print(f"C quota removal factor = 1/0.9 = +{100 * (C_QUOTA_REMOVAL_FACTOR - 1):.2f}% "
          f"(mechanism-derived, paper fn5 p.13)")
    print(f"  C forward quota: cars-only {c_quota6:.2f}/round -> "
          f"{c_quota6 * 24:.0f}/yr; removal {c_quota6 * C_QUOTA_REMOVAL_FACTOR:.2f}/round -> "
          f"{c_quota6 * C_QUOTA_REMOVAL_FACTOR * 24:.0f}/yr")
    print("E-shift OMV banding (Category-B-skewed, Option B bands):")
    print(delta[["band_label", "share_of_e_shift_pct", "ann_registrations",
                 "quantum_sgd", "quantum_revenue_contribution_sgd"]]
          .to_string(index=False))
    print(f"net quantum revenue delta (E-shift registrations): "
          f"{delta.quantum_revenue_contribution_sgd.sum():,.0f} SGD/yr")
    print(f"INV-9: {inv['status']}")
    for f in ("ec_scenario_E_removed.csv", "ec_scenario_E_cars_only.csv",
              "e_shift_feebate_base_delta.csv"):
        print(f"wrote tables/{f}")
    return {
        "kappa_M": kappa,
        "e_bids6": e_bids6, "e_quota6": e_quota6,
        "c_quota6": c_quota6, "c_prem6": c_prem6,
        "e_prem": e_prem,
        "e_annual_regs": e_annual_regs,
        "pulse_dx": pulse_dx,
        "c_quota_removed": c_quota6 * C_QUOTA_REMOVAL_FACTOR,
        "inv9": inv["status"],
    }


if __name__ == "__main__":
    main()
