#!/usr/bin/env python3
"""
Step 6 — Per-category price-bidding-response (demand) curves
(src/demand_curves.py).

FIT
---
Data: data/processed/coe_panel_perbidding.csv — per-bidding rows, categories
A-E, 2010-01..2026-10 (199 months x 2 biddings = 398 obs per category;
OBSERVED-stamped; see Batch B provenance). Series are sequentially ordered
(month, then bidding_no).

For each category K in A, B, C, E (D is the negative-control reference,
see below), three specs are fitted; standard errors are NEWEY-WEST HAC,
maxlags = 4 per-bidding obs (~2 calendar months — the prior coe-ev-rebate
study used Newey-West lag-3 on monthly data, the same autocorrelation span
at the per-bidding frequency):

  M1 linear levels:
      premium_{K,t} = a + b1*bids_received_{K,t} + b2*quota_{K,t}
                      + b3*trend_t + e
  M2 log-log:
      ln(premium_{K,t}) = a + e1*ln(bids_received_{K,t}) + e2*ln(quota_{K,t})
                          + b3*trend_t + e
  M3 FIRST DIFFERENCES (primary for scenario use):
      dpremium_{K,t} = a + b1*d(bids_received)_{K,t}
                       + b2*d(quota)_{K,t} + e

  trend_t = calendar month index (2010-01 = 0). M3 is first differences
  because the levels specs show strong residual autocorrelation under a
  linear trend (Durbin-Watson ~0.05-0.15, Breusch-Godfrey p < 0.001 for
  A/B/C/E): the secular COE price rise (2010..2026, prices roughly 7x) is
  not absorbed by a linear trend, so levels coefficients are common-trend
  contaminated. M3 isolates the within-auction demand-price response
  (same pattern as the prior study's ADF levels-vs-diffs diagnostics).

ROLE OF THE COEFFICIENTS (stated on every output)
-------------------------------------------------
SCENARIO ELASTICITIES ONLY. The coefficients describe the historical
association between a category's bidding demand and its clearing price,
for use in scenario iteration in later steps (Steps 7-8, 10, 12). They
carry NO structural causal claim: quota policy and vehicle-cost regimes
(VES/EEAI/PARF) change over time, and bidding demand itself responds to
the expected COE price (simultaneity). Evidence is therefore graded
LOW/MEDIUM at best — see tables/evidence_grading.csv.

NEGATIVE CONTROLS (motivated by the prior study's failure mode)
----------------------------------------------------------------
The prior coe-ev-rebate study (method precedent documented in
docs/methodology_notes.md) invalidated its headline EV-rebate price effect
because its
"clean" negative-control categories (C/D/E) showed the SAME 2022-01 price
jump as the treated category — the effect was a market-wide common shock,
not the treatment channel. The analogue risk here: the within-category
price-bidding coefficient picks up COMMON secular dynamics (COE price
inflation, quota policy, pandemic) correlated across all categories,
rather than a genuine category-specific demand response. Controls:

  NC1 LEAD CONTROL (per category, levels spec): re-fit M1 with the
      bidding demand of the NEXT bidding round (t+1; for b2 of month m
      this is b1 of m+1) in place of the contemporaneous demand. The
      clearing price of round t is set at auction t — bids submitted in
      round t+1 cannot move it. Expect b1_lead ~ 0 (p > 0.10). A
      significant lead effect means the contemporaneous coefficient is a
      common-trend artifact (the prior study's exact failure mode) ->
      the category's headline elasticities are INVALIDATED (grade NOT
      DETECTABLE). Lead-2 is reported alongside.
  NC2 CATEGORY-D REFERENCE (mechanism check): Category D (large goods)
      is the cleanest COE market in the panel — no car cost-regime
      (VES/EEAI/PARF) confounders apply to it. The same specs are fit
      on D. If the bidding->price mechanism is real, D (with a stable,
      low price level and no residual autocorrelation) should show a
      clean, significant positive response — and indeed it does
      (b1 ~ +5.6 S$/bid, p < 0.001, DW ~ 1.1), which VALIDATES the
      mechanism. The converse risk — an artifact-like D response with
      A/B/C/E non-response while D's price level were trending like the
      car categories — did not materialise. NC2 is therefore a
      MECHANISM VALIDATION, and (combined with the A/B/C/E residual
      autocorrelation) it motivates using the first-difference spec M3
      for scenario elasticities rather than the trend-contaminated
      levels spec M1.
  NC3 RESIDUAL DIAGNOSTICS (per category, M1 and M3): Durbin-Watson,
      Ljung-Box Q(1..4), Breusch-Godfrey (nlags=4). Significant residual
      autocorrelation flags that the spec (and/or HAC window) is
      insufficient.
  NC4 SUBSAMPLE STABILITY (per category, M3): b1 re-estimated on
      pre-2018-01 and 2018-01+; the sign should be stable.

EVIDENCE GRADING RUBRIC (per claim; coefficients are scenario
elasticities only — structural causal grades are NOT awarded)
--------------------------------------------------------------
  MEDIUM:            primary coefficient HAC p < 0.05, predicted sign
                     (positive: more bids vs fixed quota -> higher
                     clearing price), NC1 PASS (lead p > 0.10), NC3 BG
                     p > 0.05 on the same spec, NC4 sign-stable.
  LOW:               coefficient significant (p < 0.10) but at least one
                     control is a concern (NC1 marginal, NC3 BG
                     significant, NC4 sign-flip), OR only marginally
                     significant (0.05 <= p < 0.10) with clean controls,
                     OR a levels-spec coefficient whose spec is
                     trend-contaminated (reported for reference).
  NOT DETECTABLE:    coefficient p > 0.10 (not distinguishable from
                     zero), OR NC1 FAILS (lead p < 0.05 -> the
                     contemporaneous coefficient is a common-trend
                     artifact; headline invalid for that category — the
                     prior study's failure mode), OR predicted sign
                     reversed on a significant coefficient.

OUTPUTS (tables/)
-----------------
demand_curves.csv      coefficients + HAC intervals per (category, spec,
                       term); NC1 rows carry an outcome column; NC3
                       diagnostics (M1 and M3) and NC4 subsample rows
                       included.
evidence_grading.csv   one row per claim with grade + reason + the
                       negative-control check result; commented rubric
                       block appended (prior-study style).

Every row stamped with config labels (COMPUTED; coe_bids 2010-01..
2026-10 window; data.gov.sg resource citation; SCENARIO-ELASTICITY-ONLY
statement).
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.diagnostic import acorr_breusch_godfrey, acorr_ljungbox
from statsmodels.stats.stattools import durbin_watson

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config  # noqa: E402

WS = config.WORKSPACE_ROOT
TBL = config.DIR_TABLES
os.makedirs(TBL, exist_ok=True)

CATS = ["A", "B", "C", "E"]          # fitted categories (scenario elasticities)
D_REF = "D"                          # negative-control reference category
NW_LAGS = 4                          # per-bidding obs (~2 calendar months)
DATA_WINDOW = "coe_bids 2010-01..2026-10 (per-bidding clearing prices)"
CITATION = ("data.gov.sg COE bidding results (resource "
            "d_69b3380ad7e51aff3a7dcc84eba52b8a); see "
            "verification/provenance_log.csv")
SCENARIO_NOTE = ("SCENARIO ELASTICITY ONLY — no structural causal claim; "
                 "use for scenario iteration in Steps 7-8/10/12")


def label(cat: str) -> str:
    return config.output_label(
        config.TYPE_COMPUTED,
        scenario=f"cat{cat}_demand_curve",
        data_window=DATA_WINDOW,
        citation=CITATION + "; " + SCENARIO_NOTE,
    )


def load_panel() -> pd.DataFrame:
    p = pd.read_csv(os.path.join(config.DIR_DATA_PROCESSED,
                                 "coe_panel_perbidding.csv"))
    for c in ("premium", "quota", "bids_received", "bids_success"):
        p[c] = pd.to_numeric(p[c], errors="coerce")
    p = p.sort_values(["month", "bidding_no"]).reset_index(drop=True)
    m = pd.to_datetime(p.month, format="%Y-%m")
    p["month_idx"] = (m.dt.year * 12 + m.dt.month -
                      (m.iloc[0].year * 12 + m.iloc[0].month))
    return p


def fit_ols(y: pd.Series, X: pd.DataFrame,
            maxlags: int = NW_LAGS) -> sm.RegressionResults:
    d = pd.concat([y.rename("__y__"), X], axis=1).dropna()
    yv = d.pop("__y__")
    xv = sm.add_constant(d.astype(float))
    return sm.OLS(yv, xv).fit(cov_type="HAC",
                              cov_kwds={"maxlags": maxlags})


def coef_row(res: sm.RegressionResults, term: str, cat: str, spec: str,
             note: str, extra: dict | None = None) -> dict:
    ci = res.conf_int().loc[term]
    r = {
        "category": cat, "spec": spec, "term": term,
        "coef": float(res.params[term]),
        "se_hac": float(res.bse[term]),
        "p": float(res.pvalues[term]),
        "ci_lo": float(ci[0]), "ci_hi": float(ci[1]),
        "n_obs": int(res.nobs),
        "r2": float(res.rsquared),
        "nw_lags": NW_LAGS,
        "note": note,
        "label": label(cat), "value_type": config.TYPE_COMPUTED,
        "scenario": f"cat{cat}_demand_curve", "data_window": DATA_WINDOW,
        "citation": CITATION,
    }
    if extra:
        r.update(extra)
    return r


def diag_rows(K: str, res: sm.RegressionResults, spec: str) -> list[dict]:
    resid = np.asarray(res.resid)
    dw = float(durbin_watson(resid))
    lb = acorr_ljungbox(resid, lags=[1, 2, 3, 4], return_df=True)
    bg = acorr_breusch_godfrey(res, nlags=4, result_object=False)
    bg_stat, bg_p = float(bg[0]), float(bg[1])
    base = {"category": K, "spec": f"NC3_diagnostics_{spec}",
            "n_obs": int(res.nobs), "r2": float(res.rsquared),
            "nw_lags": NW_LAGS, "se_hac": np.nan,
            "ci_lo": np.nan, "ci_hi": np.nan,
            "label": label(K), "value_type": config.TYPE_COMPUTED,
            "scenario": f"cat{K}_demand_curve", "data_window": DATA_WINDOW,
            "citation": CITATION}
    rows = [dict(base, term="durbin_watson", coef=dw, p=np.nan,
                 note="DW on residuals (2 = no autocorrelation)")]
    for lg in (1, 2, 3, 4):
        rows.append(dict(base, term=f"ljung_box_Q{lg}",
                         coef=float(lb.loc[lg, "lb_stat"]),
                         p=float(lb.loc[lg, "lb_pvalue"]),
                         note=f"Ljung-Box Q({lg}) on residuals"))
    rows.append(dict(base, term="breusch_godfrey", coef=bg_stat, p=bg_p,
                     note="Breusch-Godfrey nlags=4 on residuals; p<0.05 -> "
                          "residual autocorrelation beyond NW window"))
    return rows, {"dw": dw, "bg_p": bg_p,
                  "bg_significant": bg_p < 0.05,
                  "lb_p1": float(lb.loc[1, "lb_pvalue"])}


def main():
    p = load_panel()
    rows = []
    diagnostics = {}
    fits = {}

    for K in CATS + [D_REF]:
        sub = p[p.category == K].reset_index(drop=True)
        y = sub.premium
        trend = sub.month_idx.astype(float)

        # M1 linear levels
        X1 = pd.DataFrame({"bids_received": sub.bids_received,
                           "quota": sub.quota, "trend": trend})
        res1 = fit_ols(y, X1)
        fits[(K, "M1")] = (res1, X1)
        for t in ("bids_received", "quota", "trend"):
            rows.append(coef_row(
                res1, t, K, "M1_linear",
                "linear levels spec; NW HAC SEs; trend-contaminated if "
                "NC3 flags residual autocorrelation (see M3)"))

        # M2 log-log
        yl = np.log(y)
        X2 = pd.DataFrame({"ln_bids_received": np.log(sub.bids_received),
                           "ln_quota": np.log(sub.quota), "trend": trend})
        res2 = fit_ols(yl, X2)
        fits[(K, "M2")] = (res2, X2)
        for t in ("ln_bids_received", "ln_quota", "trend"):
            rows.append(coef_row(res2, t, K, "M2_loglog",
                                 "log-log spec; NW HAC SEs; coef = "
                                 "elasticity"))

        # M3 first differences (primary for scenario use)
        dy = y.diff()
        X3 = pd.DataFrame({"dbids_received": sub.bids_received.diff(),
                           "dquota": sub.quota.diff()})
        res3 = fit_ols(dy, X3)
        fits[(K, "M3")] = (res3, X3)
        for t in ("dbids_received", "dquota"):
            rows.append(coef_row(
                res3, t, K, "M3_fdiff",
                "FIRST-DIFFERENCE spec (primary for scenario use): "
                "within-auction demand-price response, trend removed"))

        # NC1: lead control on the levels spec (clearing price of round t
        # is set at auction t; round t+1 bids cannot move it)
        for lag, note in (
                (1, "NC1 lead control: NEXT-bidding-round demand; expect "
                    "~0 (price set at auction t)"),
                (2, "NC1 lead control lag-2 (supplementary)")):
            Xl = pd.DataFrame({
                f"bids_lead_{lag}": sub.bids_received.shift(-lag),
                "quota": sub.quota, "trend": trend})
            resl = fit_ols(y, Xl)
            pl = float(resl.pvalues[f"bids_lead_{lag}"])
            rows.append(coef_row(
                resl, f"bids_lead_{lag}", K, f"NC1_lead{lag}", note,
                extra={"outcome": "PASS" if pl >= 0.10
                       else ("MARGINAL" if pl >= 0.05 else "FAIL")}))

        # NC3: residual diagnostics on M1 and M3
        for spec, res in (("M1", res1), ("M3", res3)):
            d_rows, diag = diag_rows(K, res, spec)
            diagnostics[(K, spec)] = diag
            rows.extend(d_rows)

        # NC4: subsample stability on M3 (pre-2018 vs 2018+)
        split = 8 * 12  # months from 2010-01 to 2018-01
        for name, mask in (("pre_2018", sub.month_idx < split),
                           ("post_2018", sub.month_idx >= split)):
            subm = sub[mask].reset_index(drop=True)
            Xm = pd.DataFrame({"dbids_received": subm.bids_received.diff(),
                               "dquota": subm.quota.diff()})
            resm = fit_ols(subm.premium.diff(), Xm)
            rows.append(coef_row(resm, "dbids_received", K,
                                 f"NC4_subsample_{name}",
                                 f"b1 re-estimated on {name} subsample "
                                 "(first differences)"))

    # ------------------------------------------------------------------
    # NC2 verdict (mechanism reference on the clean category D)
    # ------------------------------------------------------------------
    def std_response(K, spec):
        """Predicted price change per +10% bidding demand, as % of the
        category's mean premium (levels specs) or per +10% of median
        bidding change (fdiff spec, expressed vs mean premium)."""
        res, _ = fits[(K, spec)]
        b1 = float(res.params["bids_received" if spec != "M3"
                     else "dbids_received"])
        sub = p[p.category == K]
        mean_prem = float(sub.premium.mean())
        med_bids = float(sub.bids_received.median())
        return b1, b1 * 0.10 * med_bids / mean_prem * 100.0, mean_prem

    nc2 = {K: std_response(K, "M1") for K in CATS + [D_REF]}
    nc3 = {K: std_response(K, "M3") for K in CATS + [D_REF]}
    d_b1, d_std, d_mean = nc2[D_REF]
    d_b1f, d_stdf, _ = nc3[D_REF]
    d_mechanism_ok = (d_b1 > 0 and fits[(D_REF, "M1")][0].pvalues[
        "bids_received"] < 0.05
        and not diagnostics[(D_REF, "M1")]["bg_significant"]) or \
        (d_b1f > 0 and fits[(D_REF, "M3")][0].pvalues[
            "dbids_received"] < 0.05)
    abce_std = float(np.mean([nc2[k][1] for k in CATS]))
    nc2_note = (
        f"standardised response per +10% bids, % of mean premium — M1: "
        f"A={nc2['A'][1]:+.2f} B={nc2['B'][1]:+.2f} "
        f"C={nc2['C'][1]:+.2f} E={nc2['E'][1]:+.2f} "
        f"D(ref)={d_std:+.2f}; M3: A={nc3['A'][1]:+.2f} "
        f"B={nc3['B'][1]:+.2f} C={nc3['C'][1]:+.2f} "
        f"E={nc3['E'][1]:+.2f} D(ref)={d_stdf:+.2f}. "
        f"D mechanism validation = {d_mechanism_ok}")

    # ------------------------------------------------------------------
    # Evidence grading
    # ------------------------------------------------------------------
    grades = []

    def add_grade(claim, K, spec, term, est, ci, pv, nobs, grade, reason,
                  nc_check, notes=""):
        grades.append({
            "claim": claim, "category": K, "spec": spec, "term": term,
            "estimate": est, "ci": ci, "p_value": pv, "n_obs": nobs,
            "grade": grade, "reason": reason,
            "negative_control_check": nc_check, "notes": notes,
            "label": label(K), "value_type": config.TYPE_COMPUTED,
            "scenario": f"cat{K}_demand_curve", "data_window": DATA_WINDOW,
            "citation": CITATION,
        })

    for K in CATS:
        sub = p[p.category == K].reset_index(drop=True)
        res1, _ = fits[(K, "M1")]
        res2, _ = fits[(K, "M2")]
        res3, _ = fits[(K, "M3")]

        b1 = float(res1.params["bids_received"])
        p1 = float(res1.pvalues["bids_received"])
        b1f = float(res3.params["dbids_received"])
        p1f = float(res3.pvalues["dbids_received"])
        ci1 = res1.conf_int().loc["bids_received"]
        ci1f = res3.conf_int().loc["dbids_received"]
        lead = next(r for r in rows
                    if r["category"] == K and r["spec"] == "NC1_lead1")
        lead_ok = lead["outcome"] == "PASS"
        lead_marginal = lead["outcome"] == "MARGINAL"
        bg1 = diagnostics[(K, "M1")]
        bg3 = diagnostics[(K, "M3")]
        nc4 = [r for r in rows if r["category"] == K
               and str(r["spec"]).startswith("NC4_subsample")]
        signs = [np.sign(r["coef"]) for r in nc4]
        sign_stable = (len(signs) == 2 and signs[0] == signs[1]
                       and signs[0] > 0)

        # ---- CLAIM 1 (PRIMARY): within-auction response (M3 fdiff) ----
        if not lead_ok:
            g1, reason1 = "NOT DETECTABLE", (
                f"NC1 lead control FAILS (lead-1 p={lead['p']:.3f} < 0.05): "
                f"the clearing price responds to NEXT round's bids — the "
                f"contemporaneous coefficient is a common-trend artifact "
                f"(prior study's failure mode); headline elasticity "
                f"invalidated for this category")
        elif p1f > 0.10:
            g1, reason1 = "NOT DETECTABLE", (
                f"M3 b1 p={p1f:.3f} > 0.10 — within-auction "
                f"price-bidding coefficient not distinguishable from zero "
                f"under NW-HAC")
        elif b1f < 0:
            g1, reason1 = "NOT DETECTABLE", (
                f"M3 b1 significant ({b1f:+.2f}, p={p1f:.3f}) but NEGATIVE "
                f"— predicted sign reversed (more bids vs fixed quota "
                f"should raise the clearing price)")
        elif p1f < 0.05 and bg3["bg_p"] > 0.05 and sign_stable:
            g1, reason1 = "MEDIUM", (
                f"M3 b1 p={p1f:.4f} < 0.05, positive sign; NC1 lead PASS "
                f"(p={lead['p']:.2f}); NC3 BG p={bg3['bg_p']:.2f} > 0.05 "
                f"on M3; NC4 signs stable — usable as scenario elasticity "
                f"(no structural causal claim)")
        else:
            concerns = []
            if lead_marginal:
                concerns.append(f"NC1 marginal (p={lead['p']:.3f})")
            if bg3["bg_p"] <= 0.05:
                concerns.append(
                    f"NC3 BG p={bg3['bg_p']:.3f} significant on M3")
            if not sign_stable:
                concerns.append("NC4 subsample sign instability")
            if p1f >= 0.05:
                concerns.append(f"only marginal significance "
                                f"(p={p1f:.3f})")
            g1, reason1 = "LOW", (
                f"concern(s): {', '.join(concerns) if concerns else 'mixed'}"
                f" — usable with caution as scenario elasticity only")
        add_grade(
            f"cat{K} within-auction price response to bidding demand "
            f"(first difference, S$ per additional bid) — PRIMARY",
            K, "M3_fdiff", "dbids_received",
            f"{b1f:+.2f} S$/bid (+100 bids: {b1f * 100:+,.0f} S$)",
            f"[{ci1f[0]:+,.2f}, {ci1f[1]:+,.2f}]", p1f, int(res3.nobs),
            g1, reason1,
            (f"NC1 lead1 p={lead['p']:.3f} ({lead['outcome']}); "
             f"NC2 D-ref mechanism={'OK' if d_mechanism_ok else 'NOT OK'}; "
             f"NC3 M3 BG p={bg3['bg_p']:.3f}; "
             f"NC4 signs {signs}"),
            f"standardised: {nc3[K][1]:+.2f}% of mean premium "
            f"({nc3[K][2]:,.0f}) per +10% bids")

        # ---- CLAIM 2: levels association (M1; reference) ----
        trend_flag = bg1["bg_significant"]
        if trend_flag:
            g2 = "LOW"
            reason2 = (
                f"levels spec is TREND-CONTAMINATED (NC3: DW={bg1['dw']:.2f}, "
                f"BG p={bg1['bg_p']:.3f} < 0.05): the linear trend does not "
                f"absorb the secular COE price rise, so the levels "
                f"coefficient is NOT a clean scenario elasticity; prefer "
                f"M3. Reported for reference only.")
        elif p1 < 0.05 and b1 > 0 and lead_ok:
            g2 = "LOW"
            reason2 = (
                f"levels association significant (p={p1:.4f}) but levels "
                f"specs are associational at best (simultaneity); scenario "
                f"elasticity only, prefer M3.")
        else:
            g2 = "NOT DETECTABLE"
            if p1 > 0.10:
                ptxt = f"p={p1:.3f} > 0.10 (not distinguishable from zero)"
            else:
                ptxt = f"p={p1:.3f} significant but negative sign"
            reason2 = (
                f"levels b1 {ptxt} under NW-HAC; "
                + ("levels spec trend-contaminated; prefer M3."
                   if trend_flag else "levels spec not usable."))
        add_grade(
            f"cat{K} levels price association with bidding demand "
            f"(S$ per additional bid) — reference",
            K, "M1_linear", "bids_received",
            f"{b1:+.2f} S$/bid (+100 bids: {b1 * 100:+,.0f} S$)",
            f"[{ci1[0]:+,.2f}, {ci1[1]:+,.2f}]", p1, int(res1.nobs),
            g2, reason2,
            (f"NC1 lead1 p={lead['p']:.3f} ({lead['outcome']}); "
             f"NC3 M1 DW={bg1['dw']:.2f}, BG p={bg1['bg_p']:.3f}"),
            f"standardised: {nc2[K][1]:+.2f}% of mean premium "
            f"({nc2[K][2]:,.0f}) per +10% bids")

        # ---- CLAIM 3: log-log elasticity (M2) ----
        e1 = float(res2.params["ln_bids_received"])
        e1p = float(res2.pvalues["ln_bids_received"])
        e1ci = res2.conf_int().loc["ln_bids_received"]
        if not lead_ok:
            g3, reason3 = "NOT DETECTABLE", (
                f"NC1 lead control FAILS (p={lead['p']:.3f}) — the "
                f"contemporaneous association is a common-trend artifact; "
                f"elasticity invalid")
        elif e1p > 0.10:
            g3, reason3 = "NOT DETECTABLE", (
                f"e1={e1:+.3f} not distinguishable from zero "
                f"(p={e1p:.3f})")
        elif e1 < 0:
            g3, reason3 = "NOT DETECTABLE", (
                f"e1={e1:+.3f} significant (p={e1p:.3f}) but NEGATIVE — "
                f"predicted sign reversed; not usable as an elasticity")
        elif e1p < 0.05 and bg1["bg_p"] > 0.05:
            g3, reason3 = "MEDIUM", (
                f"e1={e1:+.3f} (p={e1p:.3f}); NC1 PASS; NC3 M1 clean — "
                f"scenario elasticity only")
        else:
            g3, reason3 = "LOW", (
                f"e1={e1:+.3f} p={e1p:.3f}; "
                + ("levels spec trend-contaminated (BG significant) — "
                   "elasticity reported with caution"
                   if bg1["bg_p"] <= 0.05 else
                   "marginal or control concern; scenario elasticity only"))
        add_grade(
            f"cat{K} price elasticity wrt bidding demand (log-log)",
            K, "M2_loglog", "ln_bids_received",
            f"e1={e1:+.3f}", f"[{e1ci[0]:+.3f}, {e1ci[1]:+.3f}]", e1p,
            int(res2.nobs), g3, reason3,
            (f"NC1 lead1 p={lead['p']:.3f} ({lead['outcome']}); "
             f"NC2 D-ref mechanism={'OK' if d_mechanism_ok else 'NOT OK'}"),
            "elasticity read for scenario iteration only")

    # D reference (control row, not a scenario claim)
    add_grade(
        "Category D reference (negative-control mechanism check for the "
        "bidding->price channel)", D_REF, "M1_linear", "bids_received",
        f"{d_b1:+.2f} S$/bid (M3: {d_b1f:+.2f})",
        f"std={d_std:+.2f}% (M1), {d_stdf:+.2f}% (M3)",
        float(fits[(D_REF, 'M1')][0].pvalues["bids_received"]), 398,
        ("PASS (mechanism validated)" if d_mechanism_ok
         else "FAIL (mechanism not validated)"),
        ("D (large goods) is the cleanest COE market in the panel (no "
         "car cost-regime confounders); a clean significant positive "
         "response VALIDATES the bidding->price mechanism and motivates "
         "the first-difference spec for the car categories whose levels "
         "residuals are autocorrelated"),
        ("PASS" if d_mechanism_ok else "FAIL"), nc2_note)

    out = pd.DataFrame(rows)
    cols = ["category", "spec", "term", "coef", "se_hac", "p", "ci_lo",
            "ci_hi", "n_obs", "r2", "nw_lags", "note"]
    if "outcome" in out.columns:
        cols.insert(11, "outcome")
    cols += ["label", "value_type", "scenario", "data_window", "citation"]
    out = out[cols]
    out.to_csv(os.path.join(TBL, "demand_curves.csv"), index=False)

    g = pd.DataFrame(grades)
    g.to_csv(os.path.join(TBL, "evidence_grading.csv"), index=False)
    with open(os.path.join(TBL, "evidence_grading.csv"), "a") as fh:
        fh.write("# ---- grading rubric & caveats ----\n")
        fh.write("# grades: MEDIUM / LOW / NOT DETECTABLE (scenario\n"
                 "# elasticities only — structural causal grades NOT awarded)\n")
        fh.write(f"# primary claim per category = M3 first-difference "
                 f"coefficient (trend removed;\n")
        fh.write("# levels specs M1/M2 are trend-contaminated where NC3 "
                 "flags residual autocorrelation\n"
                 f"# — DW~0.05-0.15, BG p<0.001 for A/B/C/E under a "
                 f"linear trend; NW-HAC maxlags={NW_LAGS} per-bidding\n"
                 f"# obs (~2 calendar months); per-bidding series "
                 f"2010-01..2026-10, N=398 per category.\n")
        fh.write("# MEDIUM: HAC p<0.05, predicted (positive) sign, NC1 "
                 "lead PASS (p>0.10), NC3 BG p>0.05 on the same spec,\n"
                 "# NC4 subsample signs stable.\n")
        fh.write("# LOW: significant but any control concern, or only "
                 "marginally significant (0.05<=p<0.10), or a\n"
                 "# trend-contaminated levels-spec coefficient reported "
                 "for reference.\n")
        fh.write("# NOT DETECTABLE: p>0.10, OR NC1 FAILS (lead p<0.05 -> "
                 "common-trend artifact; headline invalidated — prior\n"
                 "# study's failure mode), OR predicted sign reversed.\n")
        fh.write(f"# NC2 D-reference mechanism validation = "
                 f"{d_mechanism_ok} ({nc2_note})\n")
        fh.write("# simultaneity caveat: bidding demand responds to the\n"
                 "# expected COE price; coefficients are associational.\n")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("=" * 72)
    print("STEP 6 — PER-CATEGORY PRICE-BIDDING-RESPONSE CURVES")
    print("=" * 72)
    print(f"Data: per-bidding 2010-01..2026-10, N=398 per category; "
          f"NW-HAC maxlags={NW_LAGS}")
    for K in CATS + [D_REF]:
        r1 = out[(out.category == K) & (out.spec == "M1_linear")
                 & (out.term == "bids_received")].iloc[0]
        r2 = out[(out.category == K) & (out.spec == "M2_loglog")
                 & (out.term == "ln_bids_received")].iloc[0]
        r3 = out[(out.category == K) & (out.spec == "M3_fdiff")
                 & (out.term == "dbids_received")].iloc[0]
        lead = out[(out.category == K) & (out.spec == "NC1_lead1")].iloc[0]
        d1 = diagnostics[(K, "M1")]
        d3 = diagnostics[(K, "M3")]
        tag = " (REF)" if K == D_REF else ""
        print(f"\ncat {K}{tag}:")
        print(f"  M1 b1={r1.coef:+.2f} S$/bid p={r1.p:.4f} "
              f"[{r1.ci_lo:+.2f}, {r1.ci_hi:+.2f}] R2={r1.r2:.3f} "
              f"(DW={d1['dw']:.2f}, BG p={d1['bg_p']:.4f})")
        print(f"  M2 e1={r2.coef:+.3f} p={r2.p:.4f} "
              f"[{r2.ci_lo:+.3f}, {r2.ci_hi:+.3f}]")
        print(f"  M3 b1={r3.coef:+.2f} S$/bid p={r3.p:.4f} "
              f"[{r3.ci_lo:+.2f}, {r3.ci_hi:+.2f}] R2={r3.r2:.3f} "
              f"(DW={d3['dw']:.2f}, BG p={d3['bg_p']:.4f})")
        print(f"  NC1 lead1 p={lead.p:.3f} ({lead.outcome}); std(M1)="
              f"{nc2[K][1]:+.2f}% std(M3)={nc3[K][1]:+.2f}%")
    print(f"\nNC2 D-reference mechanism validation = {d_mechanism_ok}")
    print(nc2_note)
    print("\nEvidence grades:")
    for _, r in g.iterrows():
        print(f"  [{r.grade:16s}] {r.claim[:75]}")
        print(f"      est={r.estimate} p={r.p_value}")
    print(f"\nWrote: demand_curves.csv ({len(out)} rows), "
          f"evidence_grading.csv ({len(g)} rows)")
    return out, g, nc2, nc3, d_mechanism_ok, diagnostics


if __name__ == "__main__":
    main()
