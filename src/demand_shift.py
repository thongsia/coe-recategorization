"""Step 12 — Demand shifts by car-value band (Batch F).

Applies each option's feebate-driven change in effective price (Fbar,
Batch D) to the merged A+B demand response (kappa_M from the M3
first-difference demand curves, Batch C) and decomposes the resulting
shift over the 217-catalog-model band / fuel / OMV attributes.

Arithmetic (documented in methodology_notes.md s.14):
  * The demand response to the feebate is modelled as a UNIFORM
    price-level shift: every registration's effective price moves by
    the band quantum; the NET market effect is Fbar =
    sum_b share_b x quantum_b (Batch D: OptionA +2,091.97,
    OptionB +2,149.11 S$/registration).
  * Total merged-market demand shift (bids/yr):
        dQ_total = -kappa_M x Fbar,
    kappa_M = 1/beta_A + 1/beta_B with beta_A = 4.988548,
    beta_B = 8.244765 S$/bid (M3 dpremium ~ d(bids), tables/
    demand_curves.csv; grades MEDIUM/LOW — SCENARIO ELASTICITY ONLY).
    => kappa_M = 0.321748 bids/S$; dQ_total: OptionA -673.09,
    OptionB -691.47 bids (reproduces Batch D within 0.01).
  * Because the response is a uniform price-level shift, the BAND
    decomposition allocates the total shift by each band's
    bid-response weight:
        w_b = (share_b x quantum_b) / sum_b(share_b x quantum_b),
        dQ_b = dQ_total x w_b.
    Rebate bands (negative quantum) get a POSITIVE dQ (their effective
    price falls); surcharge bands get a NEGATIVE dQ; the zero-quantum
    band gets 0. Sum_b dQ_b = dQ_total exactly (weights sum to 1).
  * Model-level allocation within a band is by the model's share of
    band annualised registrations (reg_weight, Jan-May 2025 x12/5 —
    frozen mix).

Outputs (scenario + data window on every row):
  tables/demand_shift_by_band.csv — per option x dimension
    {band, fuel EV/ICE, cohort current-A/current-B, OMV decile 1-10}:
    signed delta in bids/yr, pct of total shift, n_models,
    registration share.
  tables/segment_shift.csv — EV share of the shift and luxury
    (OMV > 75th percentile cut point, PROPOSED) vs mass-market mix.

These tables feed the unintended-consequence analysis in Step 14.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import config as cfg

W = cfg.WORKSPACE_ROOT
TBL = cfg.DIR_TABLES


def weighted_quantile(omv: pd.Series, weight: pd.Series, p: float) -> float:
    df = pd.DataFrame({"omv": omv, "w": weight}).sort_values("omv")
    cum = df.w.cumsum() / df.w.sum()
    return float(df.omv[cum >= p].iloc[0])


def main() -> None:
    dc = pd.read_csv(os.path.join(TBL, "demand_curves.csv"))
    m3 = dc[dc.spec == "M3_fdiff"]
    beta = {r.category: r.coef for r in m3[m3.term == "dbids_received"].itertuples()}
    kappa_a = 1.0 / beta["A"]
    kappa_b = 1.0 / beta["B"]
    kappa_m = kappa_a + kappa_b

    handoff_d = json.load(open(os.path.join(W, "batch_handoff_d.json")))
    hk = {"OptionA": "optionA", "OptionB": "optionB"}
    fbar = {o: handoff_d["feebe_parameters"][hk[o]]["avg_quantum_registration_weighted_SGD"]
            for o in ("OptionA", "OptionB")}
    dshift_d = {o: handoff_d["feebe_parameters"][hk[o]]["feebate_demand_shift_bids"]
                for o in ("OptionA", "OptionB")}

    shares = pd.read_csv(os.path.join(TBL, "banding_shares.csv"))
    models = {"OptionA": pd.read_csv(os.path.join(TBL, "banding_models_optionA.csv")),
              "OptionB": pd.read_csv(os.path.join(TBL, "banding_models_optionB.csv"))}
    quantums = {"OptionA": cfg.FEEBATE_QUANTUMS_OPTION_A,
                "OptionB": cfg.FEEBATE_QUANTUMS_OPTION_B}

    data_window = (f"demand curves coe_bids 2010-01..2026-10 (M3) x mix "
                   f"{cfg.REGISTRATION_MIX_WINDOW} (frozen at {cfg.REGISTRATION_FREEZE_MONTH})")
    cite = ("Step 12 demand shift: Fbar from Batch D (tables/merged_price_*_withfee.csv "
            "revenue note; reverified via shares x quantums x registrations, "
            "verification/crossfoot_log.csv); kappa_M = 1/beta_A + 1/beta_B from "
            "tables/demand_curves.csv M3_fdiff (grades A=MEDIUM B=LOW — SCENARIO "
            "ELASTICITY ONLY, no structural causal claim); band allocation weight "
            "w_b = (share_b x quantum_b)/sum(share_b x quantum_b); model allocation "
            "by reg_weight (2025-01..2025-05 frozen)")

    out_rows = []
    seg_rows = []

    for opt in ("OptionA", "OptionB"):
        mdf = models[opt].copy()
        qb = quantums[opt]
        sub = shares[shares.option == opt]
        band_share = dict(zip(sub.band, sub.band_share_pct / 100.0))

        dQ_total = -kappa_m * fbar[opt]
        # sanity vs Batch D
        assert abs(dQ_total - dshift_d[opt]) < 0.05, (opt, dQ_total, dshift_d[opt])

        # band weights and band-level shifts
        sw = {int(b): s * q for b, s, q in zip(sub.band, band_share.values(), qb)}
        sw_sum = sum(sw.values())
        dQ_band = {int(b): dQ_total * (sw.get(b, 0.0) / sw_sum)
                   for b in range(1, len(qb) + 1)}

        # model-level allocation by reg_weight within band
        mdf["band"] = mdf.band.astype(int)
        mdf["band_dq"] = mdf.band.map(dQ_band)
        bw = mdf.groupby("band").reg_weight.transform("sum")
        mdf["model_dq"] = mdf.band_dq * (mdf.reg_weight / bw)

        def emit(dim, value, idx, note=""):
            rows_m = mdf.loc[idx] if idx is not None else mdf
            d = rows_m.model_dq.sum()
            out_rows.append({
                "feebate_option": opt,
                "dimension": dim,
                "value": value,
                "delta_bids_per_year": round(d, 3),
                "pct_of_total_shift": round(d / dQ_total * 100.0, 3),
                "n_models": int(rows_m.shape[0]),
                "registration_share_pct": round(rows_m.reg_weight.sum() / mdf.reg_weight.sum() * 100.0, 3),
                "band_dq_note": note,
                "label": cfg.output_label(cfg.TYPE_COMPUTED,
                                          scenario=f"{opt}_feebe_demand_shift",
                                          data_window=data_window,
                                          citation=cite),
                "value_type": cfg.TYPE_COMPUTED,
                "scenario": f"{opt}_feebe_demand_shift",
                "data_window": data_window,
                "citation": cite,
            })

        # total row
        out_rows.append({
            "feebate_option": opt,
            "dimension": "TOTAL",
            "value": "all",
            "delta_bids_per_year": round(dQ_total, 3),
            "pct_of_total_shift": 100.0,
            "n_models": int(mdf.shape[0]),
            "registration_share_pct": 100.0,
            "band_dq_note": (f"dQ_total = -kappa_M x Fbar = -{kappa_m:.6f} x "
                             f"{fbar[opt]:,.2f} (Batch D: {dshift_d[opt]:,.2f})"),
            "label": cfg.output_label(cfg.TYPE_COMPUTED,
                                      scenario=f"{opt}_feebe_demand_shift",
                                      data_window=data_window, citation=cite),
            "value_type": cfg.TYPE_COMPUTED,
            "scenario": f"{opt}_feebe_demand_shift",
            "data_window": data_window,
            "citation": cite,
        })

        # 1) by band
        for b in range(1, len(qb) + 1):
            emit("band", f"band{b}_{sub.band_label[sub.band == b].iloc[0]}",
                 mdf.band == b,
                 note=f"w_b={sw.get(b,0.0)/sw_sum:+.4f} (share x quantum weight), "
                      f"quantum {qb[b-1]:+,} S$")
        # 2) EV vs ICE
        emit("fuel", "EV", mdf.fuel_type_code == "E")
        emit("fuel", "ICE", mdf.fuel_type_code != "E")
        # 3) current-A vs current-B cohort (catalog coe_class proxy for old-regime class)
        emit("cohort", "current_A", mdf.coe_class == "A",
             note="catalog coe_class (Car Cost Aug 2026) as proxy for old-regime A")
        emit("cohort", "current_B", mdf.coe_class == "B",
             note="catalog coe_class (Car Cost Aug 2026) as proxy for old-regime B")
        # 4) OMV decile (registration-weighted deciles of catalog OMV)
        qs = [weighted_quantile(mdf.omv_catalog_aug2026, mdf.reg_weight, p / 100.0)
              for p in range(10, 100, 10)]
        dec = np.searchsorted(qs, mdf.omv_catalog_aug2026, side="right") + 1
        dec = dec.clip(1, 10)
        mdf["omv_decile"] = dec
        for d10 in range(1, 11):
            emit("omv_decile", f"d{d10}", mdf.omv_decile == d10,
                 note=f"OMV in ({qs[d10-2]:,.0f}, {qs[d10-1]:,.0f}]"
                      if d10 < 10 else f"OMV > {qs[-1]:,.0f}")

        # segment shift
        ev = mdf.loc[mdf.fuel_type_code == "E"].model_dq.sum()
        ice = mdf.loc[mdf.fuel_type_code != "E"].model_dq.sum()
        lux_th = 49662  # Option B p75 cut point (PROPOSED; base-mix weighted percentile)
        lux = mdf.loc[mdf.omv_catalog_aug2026 > lux_th].model_dq.sum()
        mass = mdf.loc[mdf.omv_catalog_aug2026 <= lux_th].model_dq.sum()
        for seg, d, note in [
            ("EV_share_of_total_shift", ev, f"EV delta {ev:+.2f} vs ICE {ice:+.2f} bids/yr"),
            ("luxury_vs_mass_luxury", lux, f"OMV > {lux_th:,} (75th pct cut point, PROPOSED)"),
            ("luxury_vs_mass_mass", mass, f"OMV <= {lux_th:,}"),
        ]:
            seg_rows.append({
                "feebate_option": opt,
                "segment": seg,
                "delta_bids_per_year": round(d, 3),
                "pct_of_total_shift": round(d / dQ_total * 100.0, 3),
                "direction": "demand up" if d > 0 else "demand down",
                "note": note,
                "label": cfg.output_label(cfg.TYPE_COMPUTED,
                                          scenario=f"{opt}_feebe_demand_shift",
                                          data_window=data_window, citation=cite),
                "value_type": cfg.TYPE_COMPUTED,
                "scenario": f"{opt}_feebe_demand_shift",
                "data_window": data_window,
                "citation": cite,
            })

    df = pd.DataFrame(out_rows)
    df.to_csv(os.path.join(TBL, "demand_shift_by_band.csv"), index=False)
    sdf = pd.DataFrame(seg_rows)
    sdf.to_csv(os.path.join(TBL, "segment_shift.csv"), index=False)

    print("=== STEP 12 DEMAND SHIFTS ===")
    print(f"kappa_A={kappa_a:.6f} kappa_B={kappa_b:.6f} kappa_M={kappa_m:.6f} bids/S$")
    for opt in ("OptionA", "OptionB"):
        t = df[(df.feebate_option == opt) & (df.dimension == "TOTAL")].iloc[0]
        print(f"\n{opt}: total shift {t.delta_bids_per_year:+.2f} bids/yr "
              f"(Batch D {dshift_d[opt]:+.2f})")
        for dim in ("band", "fuel", "cohort"):
            for _, r in df[(df.feebate_option == opt) & (df.dimension == dim)].iterrows():
                print(f"  {dim} {r.value}: {r.delta_bids_per_year:+10.2f} "
                      f"({r.pct_of_total_shift:+7.2f}%)")
    print("\nSegment shift:")
    print(sdf[["feebate_option", "segment", "delta_bids_per_year", "pct_of_total_shift",
               "direction"]].to_string(index=False))
    print("\nFiles: tables/demand_shift_by_band.csv, tables/segment_shift.csv")


if __name__ == "__main__":
    main()
