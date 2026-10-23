# LTA COE re-categorisation consultation — scenario study (final report)

**Consultation:** LTA's proposed COE categorisation changes, consultation window 8 Oct – 2 Nov 2026 (`docs/consult_paper_text.md`). **Report date:** 2026-10-23.

**Conventions (read first).** PROPOSED values are the consultation paper's design parameters (band structure, cut-point
percentiles, quantums, review cadence) cited to paper sections. COMPUTED values are scenario estimates from fetched
data, always labelled with a data window: `2010-01..2026-10` (COE bidding results, OBSERVED), `2016-01..2025-05`
(vehicle registrations, OBSERVED, **frozen at 2025-05**), `2025-01..2025-05 (frozen at 2025-05)` (Jan–May 2025
registration mix × Car Cost Aug-2026 catalog — the labelled banding fallback), `2017-01..2017-12 (OBSERVED) + LTA
OMV 2017 edition` (renewal-cohort mix), `2002-02..2026-09` (published PQP history). Scenario estimates are not
predictions. Regime start date for every scenario: **2027-01-01** (ASSUMPTION — the paper states no implementation
date; see §1). Every number below is machine-checked against a source table cell by `src/verify.py` (check d):
zero untraceable numbers is the pass bar.

## Executive summary

**Headline finding 1 — the merge converges A and B onto one price, and the value-based feebate is a net revenue
source, but its size is very cut-point-sensitive.** Observed 2026-10 b2 (window 2010-01..2026-10, OBSERVED):
Category A 132,004 and Category B 131,901 [[t|tables/inversions_2026.csv|2026-10 / 2|a_premium,b_premium]] — the two
categories already clear within 103 S$ of each other [[t|tables/inversions_2026.csv|2026-10 / 2|spread_a_minus_b]].
Back-solving the merged A+B category with no feebate (COMPUTED, window 2010-01..2026-10) settles at 131,965.17 for
the last observed round [[t|tables/merged_price_nofeebate.csv|back_solved_history / 2026-10 / 2|merged_price_point]]
and 131,892.13 for the 2027-12 forward end
[[t|tables/merged_price_nofeebate.csv|forward_scenario / 2027-12 / 2|merged_price_point]].
Applying the PROPOSED feebate lowers the merged price by about 1.6%: 131,965.17 → 129,873.20 (Option A) and
131,965.17 → 129,816.07 (Option B) at the last observed round (2026-10 b2)
[[t|tables/merged_price_optionA_withfee.csv|back_solved_history / 2026-10 / 2|withfee_price_point]]
[[t|tables/merged_price_optionB_withfee.csv|back_solved_history / 2026-10 / 2|withfee_price_point]],
and 131,892.13 → 129,800.16 (A) / 129,743.03 (B) at the 2027-12 forward end
[[t|tables/merged_price_optionA_withfee.csv|forward_scenario / 2027-12 / 2|withfee_price_point]]
[[t|tables/merged_price_optionB_withfee.csv|forward_scenario / 2027-12 / 2|withfee_price_point]];
it is a net revenue source: S$95.76M (A) / S$98.38M (B) on the merged-car base, S$139.49M / S$137.00M including the
Category-E-shift flow of 6,400 registrations/yr
[[t|tables/fee_revenue_base.csv|OptionA / E_removed|base_merged_only_sgd,e_shift_delta_sgd,total_sgd,annual_registrations_e_shift]]
[[t|tables/fee_revenue_base.csv|OptionB / E_removed|base_merged_only_sgd,e_shift_delta_sgd,total_sgd]].
The feebate is only 1.81–1.86% of total COE revenue
[[t|tables/fee_revenue_incidence.csv|OptionB / E_removed|incidence_pct_of_total_coe]]
[[t|tables/fee_revenue_incidence.csv|OptionA / E_cars_only|incidence_pct_of_total_coe]].
Cut-point sensitivity dominates: at LTA-2025-edition cut points (S1) base revenue falls to S$59.63M (A) / S$70.36M (B),
and under uniform model weights (S2) to S$23.37M (A) / S$43.54M (B) (mix window 2025-01..2025-05, frozen at 2025-05)
[[t|tables/fee_revenue_sensitivity.csv|S1_lta2025_omv / OptionA|base_revenue_sgd]]
[[t|tables/fee_revenue_sensitivity.csv|S2_uniform_weights / OptionA|base_revenue_sgd]]
[[t|tables/fee_revenue_sensitivity.csv|S1_lta2025_omv / OptionB|base_revenue_sgd]]
[[t|tables/fee_revenue_sensitivity.csv|S2_uniform_weights / OptionB|base_revenue_sgd]].
Net demand response is small: −673.09 (A) / −691.47 (B) bids/yr
[[t|tables/fee_price_iteration_log.csv|OptionA|feebate_demand_shift_bids]]
[[t|tables/fee_price_iteration_log.csv|OptionB|feebate_demand_shift_bids]].

**Headline finding 2 — if the feebate is applied to COE renewals (the consultation's open PQP question), it is a
NET COST (rebate) to the government of S$517,215,600/yr (Option A) or S$353,265,450/yr (Option B)**
[[t|tables/renewal_impact_master.csv|OptionA+E_removed+renewal_feebate_yes|delta_vs_no_feebate_cell_sgd]]
[[t|tables/renewal_impact_master.csv|OptionB+E_removed+renewal_feebate_yes|delta_vs_no_feebate_cell_sgd]],
because the transition-year renewal cohort is vintage 2017 (derived as regime start 2027 minus the 10-year COE term,
§6) and is low-OMV relative to the 2025 cut points (mix window 2017-01..2017-12, OBSERVED; cut points
2025-01..2025-05). The full 2017-vintage cohort is 91,922 (A pricing) / 91,921 (B pricing) vehicles
[[t|tables/renewal_impact_master.csv|OptionA+E_removed+renewal_feebate_yes|cohort_volume]]
[[t|tables/renewal_impact_master.csv|OptionB+E_removed+renewal_feebate_yes|cohort_volume]]
[[t|tables/renewal_impact_master.csv|OptionA+E_removed+renewal_feebate_yes|vintage,vintage_derivation]].
Per vehicle at PROPOSED 2025 cut points, pre-A (old Category A) holders win: −12,628.77 S$ (A) / −9,260.73 S$ (B)
feebate rebate, while pre-B holders pay +1,393.10 S$ (A) / +1,587.45 S$ (B) more
[[t|tables/renewal_impact_master.csv|OptionA+E_removed+renewal_feebate_yes|preA_per_vehicle_quantum_sgd,preB_per_vehicle_quantum_sgd]]
[[t|tables/renewal_impact_master.csv|OptionB+E_removed+renewal_feebate_yes|preA_per_vehicle_quantum_sgd,preB_per_vehicle_quantum_sgd]].
Re-banding renewals at 2017-vintage cut points instead largely neutralises the net rebate (sensitivity, §6).

**Other flagged findings** (data windows stated per item):

- The paper's own indicative banding tables are **internally inconsistent under public OMVs**: of 32 reconstructed
  model rows for Option A, 2 rows and of 34 for Option B, 4 rows carry the verdict
  `PAPER_TABLE_INTERNALLY_INCONSISTENT`, and agreement with the paper's typical-models tables is only 24 of 32 (A)
  and 18 of 34 (B) (mix window 2025-01..2025-05, frozen at 2025-05)
  [[t|tables/banding_mismatches.csv|OptionA / PAPER_TABLE_INTERNALLY_INCONSISTENT|verdict]]
  [[t|tables/banding_mismatches.csv|OptionB / PAPER_TABLE_INTERNALLY_INCONSISTENT|verdict]].
- Category E/C interaction: removing E shifts 6,400 registrations/yr into the merged car category (one-round price
  pulse +1,428.14 S$ at the 2027-01 b1 round, window 2025-01..2025-05 for the mix)
  [[t|tables/fee_revenue_base.csv|OptionA / E_removed|annual_registrations_e_shift]]
  [[t|tables/ec_scenario_E_removed.csv|forward_scenario / 2027-01 / 1 / merged_car|e_shift_price_effect_sgd]],
  and raises the Category C quota 7,468 → 8,298/yr (+11.11%) with the C price held flat at 91,813.5
  (price window 2026-08 b1..2026-10 b2)
  [[t|tables/fee_revenue_incidence.csv|OptionA / E_cars_only|c_quota_per_year]]
  [[t|tables/fee_revenue_incidence.csv|OptionA / E_removed|c_quota_per_year,c_price_sgd]]
  [[t|verification/invariant_checks.csv|INV-9|expected]].
- Boundary spec-gaming exposure: the largest single zone is the 50th-percentile boundary of Option A, covering
  13.79% of the registration mix ≈ 6,312.1 registrations/yr with S$15,000 quantum at stake (mix window
  2025-01..2025-05, frozen at 2025-05)
  [[t|tables/boundary_gaming_zones.csv|OptionA / 50|zone_share_pct_covered_mix,est_registrations_annual_in_zone,quantum_at_stake_sgd]].
- Variant-family classification distortion: 139 model families; 12 spanning families / 28 models affected under
  Option A and 20 / 55 under Option B, with within-family quantum differences up to S$15,000 (mix window
  2025-01..2025-05, frozen at 2025-05)
  [[t|tables/classification_distortion.csv|OptionA / option_summary|n_families,n_spanning_families,members_affected,max_within_family_quantum_diff_sgd]]
  [[t|tables/classification_distortion.csv|OptionB / option_summary|n_families,n_spanning_families,members_affected]].
- Used-car channel: DIRECTIONAL only — no usable data was fetched for used cars; directions are stated, not
  quantified (mix window 2025-01..2025-05)
  [[t|tables/used_car_directional.csv|used_car_relative_attractiveness_upper_bands|statement]].

**Bottom line.** The merge converges the observed 2026-10 b2 levels 132,004/131,901
[[t|tables/inversions_2026.csv|2026-10 / 2|a_premium,b_premium]] to the 131,892.13 no-fee forward level
[[t|tables/merged_price_nofeebate.csv|forward_scenario / 2027-12 / 2|merged_price_point]]; the feebate adds
S$2,091.97 (A) / S$2,149.11 (B) of average registration-weighted quantum on the mix (window 2025-01..2025-05)
[[t|tables/fee_price_iteration_log.csv|OptionA|max_price_update_SGD]]
[[t|tables/fee_price_iteration_log.csv|OptionB|max_price_update_SGD]] and is a modest revenue source, but its
magnitude swings by roughly a factor of four across the documented cut-point sensitivities. The material open
question — applying the feebate to renewals — flips the sign: it rebates mass-market (pre-A) renewal holders and
costs S$517.2M (A) / S$353.3M (B) per transition year under full-cohort renewal (mix window 2017-01..2017-12;
cut points 2025-01..2025-05)
[[t|tables/renewal_impact_master.csv|OptionA+E_removed+renewal_feebate_yes|delta_vs_no_feebate_cell_sgd]]
[[t|tables/renewal_impact_master.csv|OptionB+E_removed+renewal_feebate_yes|delta_vs_no_feebate_cell_sgd]].

## 1. Scope and method

- **Scope.** Merge of Categories A + B into one passenger-car category with a value-based feebate — Option A: 3
  bands at the 35th/50th OMV percentiles of 2025 registrations with quantums −15,000 / 0 / +15,000; Option B: 5
  bands at the 10th/35th/50th/75th percentiles with quantums −15,000 / −7,500 / 0 / +7,500 / +15,000
  [[t|tables/banding_cutpoints.csv|OptionA / 35 / main|band_above_quantum_sgd]]
  [[t|tables/banding_cutpoints.csv|OptionB / 75 / main|band_above_quantum_sgd]]
  [[t|tables/banding_cutpoints.csv|OptionB / 35 / main|band_above_quantum_sgd]];
  reviewed annually (PROPOSED, paper s2.15–s2.18, Tables 1/2); Category E review (remove vs cars-only, PROPOSED,
  paper s2.22–s2.23); open question whether the feebate applies to COE renewals (PQP). 29 parameters were
  extracted from the paper: 18 PROPOSED and 11 OBSERVED/stated-fact, each with its paper citation
  (`tables/consultation_parameters.csv`).
- **Regime-start anchor (ASSUMPTION).** 2027-01-01: the paper contains no implementation date; the consultation
  runs 8 Oct – 2 Nov 2026 with a review due end-2026, so 1 Jan 2027 is the earliest plausible start. Every
  scenario table carries `regime_start: 2027-01-01`.
- **Transition-year vintage (derivation).** The 2027 renewal cohort = vehicles whose initial COE was registered in
  **2017 = 2027 − 10** (10-year COE term); the 2016 cohort is pre-regime and excluded. Stated in every renewal
  table as `vintage: 2017`, `vintage_derivation: 2027 - 10`
  [[t|tables/renewal_impact_master.csv|OptionA+E_removed+renewal_feebate_yes|vintage,vintage_derivation]].
- **Data.** COE bidding results 1,990 rows, 2010-01..2026-10, both biddings per month, all 5 categories
  (OBSERVED) [[t|verification/provenance_log.csv|coe_bids|fetched_rows,api_stated_total]]; vehicle registrations
  51,669 rows, 2016-01..2025-05, **frozen at 2025-05** (OBSERVED)
  [[t|verification/provenance_log.csv|registrations|fetched_rows,api_stated_total]]; published PQP 12,904 rows,
  2002-02..2026-09, categories A–D only (long format of the SINGSTAT series; 50 source series fetched). 29,463 of
  51,669 registration rows have null `number` (57.0%) and are excluded consistently; 22,206 valid rows remain.
  The 2025 model-level OMV distribution is not public (the LTA 2025 edition reports model-month *average* OMV
  only), so banding uses the labelled Jan–May 2025 fallback mix (window 2025-01..2025-05, frozen at 2025-05) with
  S1/S2 sensitivities (§4).
- **Method discipline.** Scenario estimates only (demand curves graded A=MEDIUM, B=LOW; no structural causal
  claim); negative controls (zero-quantum and zero-elasticity iterations, NC1 lead control); every table row
  carries label (OBSERVED/COMPUTED/SCENARIO/DIRECTIONAL), data window, regime start and citation; cross-footed to
  the dollar. Full detail in `docs/methodology_notes.md` and `docs/provenance.md`.

## 2. Observed baseline (OBSERVED, window 2010-01..2026-10)

- **A/B convergence.** 398 observations per category
  [[t|tables/demand_curves.csv|A / M1_linear / bids_received|n_obs]].
  In 2026, A cleared *above* B in exactly 4 rounds, all b2: 2026-02 b2 (spread +1,500)
  [[t|tables/inversions_2026.csv|2026-02 / 2|spread_a_minus_b]], 2026-04 b2 (+2,009)
  [[t|tables/inversions_2026.csv|2026-04 / 2|spread_a_minus_b]], 2026-06 b2 (+345)
  [[t|tables/inversions_2026.csv|2026-06 / 2|spread_a_minus_b]], 2026-10 b2 (+103)
  [[t|tables/inversions_2026.csv|2026-10 / 2|spread_a_minus_b]], with bid volumes of 1,975 vs 1,353
  [[t|tables/inversions_2026.csv|2026-02 / 2|a_bids_received,b_bids_received]], 2,410 vs 1,194
  [[t|tables/inversions_2026.csv|2026-04 / 2|a_bids_received,b_bids_received]], 1,768 vs 1,202
  [[t|tables/inversions_2026.csv|2026-06 / 2|a_bids_received,b_bids_received]] and 1,574 vs 1,149
  [[t|tables/inversions_2026.csv|2026-10 / 2|a_bids_received,b_bids_received]]. Inversion prices ranged
  105,001–132,004 across these rounds
  [[t|tables/inversions_2026.csv|2026-02 / 2|a_premium,b_premium]]
  [[t|tables/inversions_2026.csv|2026-10 / 2|a_premium,b_premium]].
- **Spot prices 2026-10 (all 8 values match the reference set exactly; window 2010-01..2026-10).** b1: A 130,001
  [[t|data/raw/coe_bids.csv|2026-10 / 1 / Category A|premium]], B 130,100
  [[t|data/raw/coe_bids.csv|2026-10 / 1 / Category B|premium]], C 91,889
  [[t|data/raw/coe_bids.csv|2026-10 / 1 / Category C|premium]], D 11,012
  [[t|data/raw/coe_bids.csv|2026-10 / 1 / Category D|premium]], E 137,000
  [[t|data/raw/coe_bids.csv|2026-10 / 1 / Category E|premium]]; b2: A 132,004, B 131,901
  [[t|tables/inversions_2026.csv|2026-10 / 2|a_premium,b_premium]], C 92,200
  [[t|data/raw/coe_bids.csv|2026-10 / 2 / Category C|premium]], E 135,790 with quota 270
  [[t|data/raw/coe_bids.csv|2026-10 / 2 / Category E|premium,quota]].
- **E premium.** E cleared 135,790 at 2026-10 b2, above both A (132,004) and B (131,901)
  [[t|data/raw/coe_bids.csv|2026-10 / 2 / Category E|premium]]
  [[t|tables/inversions_2026.csv|2026-10 / 2|a_premium,b_premium]]. The 6-round average E premium over max(A,B) is
  3,777.33 (underlying observed window 2026-08 b1..2026-10 b2)
  [[t|tables/ec_scenario_E_cars_only.csv|forward_scenario / 2027-01 / 1 / E|e_premium_over_car_sgd]].
- **Demand curves (COMPUTED elasticities, window 2010-01..2026-10, per-bidding M3 first-difference, NW-HAC SEs).**
  Category A: +4.99 S$/bid, CI [+3.76, +6.21], p=1.5e-15, grade MEDIUM
  [[t|tables/evidence_grading.csv|A / M3_fdiff / dbids_received|estimate,ci,p_value,grade]]; Category B:
  +8.24 S$/bid, CI [+3.74, +12.75], p=0.000334, grade LOW
  [[t|tables/evidence_grading.csv|B / M3_fdiff / dbids_received|estimate,ci,p_value,grade]]; Category C and E:
  NOT DETECTABLE, with the Category C NC1 lead control FAILING at p=0.018 (common-trend artifact, logged)
  [[t|tables/evidence_grading.csv|C / M3_fdiff / dbids_received|grade,negative_control_check]].

## 3. Merged A+B scenario (SCENARIO, regime start 2027-01-01; windows 2010-01..2026-10 back-solved + 2027 forward)

- **Quota (ASSUMPTION).** Forward merged quota held at 2,137.5/round — the last-6-rounds average of A+B observed
  quotas; the merge preserves total car quota (bids window 2010-01..2026-10, OBSERVED)
  [[t|tables/fee_revenue_incidence.csv|OptionA / E_removed|merged_quota_per_round]].
- **No-fee path.** Forward price flat at 131,892.13 at the 2027-12 end, with within-round A/B solution spread
  p10/p90 = 131,879.89/131,906.66
  [[t|tables/merged_price_nofeebate.csv|forward_scenario / 2027-12 / 2|merged_price_point,merged_price_p10,merged_price_p90]];
  the anchor (last observed round) is 131,965.17, so the forward path sits 73.04 S$ below the anchor ≈ a 23.5-bid
  gap [[t|tables/merged_price_nofeebate.csv|back_solved_history / 2026-10 / 2|merged_price_point]].
- **Bounds (negative control INV-7 PASS).** Every back-solved merged price lies within [min(A,B), max(A,B)] of the
  same round (min 18,761.4, max 133,760, 0 violations); forward prices stay within the static bounds [85,000;
  141,000] computed over 2025-01..2026-10
  [[t|verification/invariant_checks.csv|INV-7|expected,actual,status]].
- **Quota/bid reallocation.** At each historical round, A and B quotas are re-split at the common merged price —
  e.g. 2010-01 b1: A −51.99, B +51.99 quota units; A bid surplus +241.99
  [[t|tables/quota_reallocation.csv|back_solved_history / 2010-01 / 1|delta_quota_A,delta_quota_B,bid_surplus_A]].
  The table holds 422 rows (398 back-solved + 24 forward).
- **Volatility note.** The merge removes the A/B spread channel; with-fee forward prices are nearly flat (§4), so
  the main first-years price risk is the transition from observed levels to the forward equilibrium, not
  intra-year volatility.

## 4. Feebate (COMPUTED scenario estimates; PROPOSED quantums; mix window 2025-01..2025-05 unless stated)

### 4.1 Banding reconstruction and the paper's internal-consistency flag

- **Cut points (main variant, labelled fallback mix, 2025-01..2025-05, frozen at 2025-05).** Option A: 28,877 /
  36,062 (35th/50th percentiles)
  [[t|tables/banding_cutpoints.csv|OptionA / 35 / main|omv_cutpoint,band_above_quantum_sgd]]
  [[t|tables/banding_cutpoints.csv|OptionA / 50 / main|omv_cutpoint]];
  Option B: 20,310 / 28,877 / 36,062 / 49,662 (10th/35th/50th/75th)
  [[t|tables/banding_cutpoints.csv|OptionB / 10 / main|omv_cutpoint,band_above_quantum_sgd]]
  [[t|tables/banding_cutpoints.csv|OptionB / 75 / main|omv_cutpoint,band_above_quantum_sgd]].
- **Sensitivity cut points (same window).** S1 (LTA 2025-edition average OMV): 29,800 / 36,283 (A)
  [[t|tables/banding_cutpoints.csv|OptionA / 35 / sensitivity_S1_lta2025_omv|omv_cutpoint]]
  [[t|tables/banding_cutpoints.csv|OptionA / 50 / sensitivity_S1_lta2025_omv|omv_cutpoint]];
  21,578 / 29,800 / 36,283 / 49,662 (B)
  [[t|tables/banding_cutpoints.csv|OptionB / 10 / sensitivity_S1_lta2025_omv|omv_cutpoint]]
  [[t|tables/banding_cutpoints.csv|OptionB / 75 / sensitivity_S1_lta2025_omv|omv_cutpoint]].
  S2 (uniform model weights): 30,629 / 37,301 (A)
  [[t|tables/banding_cutpoints.csv|OptionA / 35 / sensitivity_S2_uniform_weights|omv_cutpoint]]
  [[t|tables/banding_cutpoints.csv|OptionA / 50 / sensitivity_S2_uniform_weights|omv_cutpoint]];
  21,776 / 30,629 / 37,301 / 50,795 (B)
  [[t|tables/banding_cutpoints.csv|OptionB / 10 / sensitivity_S2_uniform_weights|omv_cutpoint]]
  [[t|tables/banding_cutpoints.csv|OptionB / 75 / sensitivity_S2_uniform_weights|omv_cutpoint]].
- **Band shares (registration-weighted, Jan–May 2025 annualised, 2025-01..2025-05, frozen at 2025-05).** Option A:
  35.16 / 15.74 / 49.10 (cross-foot 100.0)
  [[t|tables/banding_shares.csv|OptionA / 0-35th|band_share_pct,cross_foot_sum_pct,est_registrations_annualised_x12of5,n_models,coverage_note]]
  [[t|tables/banding_shares.csv|OptionA / 35-50th|band_share_pct,est_registrations_annualised_x12of5,n_models]]
  [[t|tables/banding_shares.csv|OptionA / >50th|band_share_pct,est_registrations_annualised_x12of5,n_models]];
  Option B: 10.17 / 24.98 / 15.74 / 24.22 / 24.88 (cross-foot 99.99 — 2dp rounding, documented)
  [[t|tables/banding_shares.csv|OptionB / 0-10th|band_share_pct,cross_foot_sum_pct]]
  [[t|tables/banding_shares.csv|OptionB / 10-35th|band_share_pct,est_registrations_annualised_x12of5]]
  [[t|tables/banding_shares.csv|OptionB / 35-50th|band_share_pct]]
  [[t|tables/banding_shares.csv|OptionB / 50-75th|band_share_pct,est_registrations_annualised_x12of5]]
  [[t|tables/banding_shares.csv|OptionB / >75th|band_share_pct,est_registrations_annualised_x12of5]].
  Annualised registrations per band (A): 16,093 / 7,205 / 22,477, total 45,775 (Option B total 45,776)
  [[t|tables/fee_revenue_base.csv|OptionA / E_removed|annual_registrations_base]]
  [[t|tables/fee_revenue_base.csv|OptionB / E_removed|annual_registrations_base]].
  Coverage: 98.73% of Jan–May 2025 car registrations (19,073 of 19,318); 21 makes not in the catalog excluded
  [[t|tables/banding_shares.csv|OptionA / 0-35th|coverage_note]].
- **Typical-models cross-validation vs the paper's Tables 1/2 (2025-01..2025-05, frozen at 2025-05).** Agreement
  24 of 32 rows (A) and 18 of 34 rows (B); 2 rows (A) and 4 rows (B) are flagged
  PAPER_TABLE_INTERNALLY_INCONSISTENT — the paper's band assignment for those models contradicts its own stated
  cut points under public OMVs (two models of the same paper table row carry OMVs on opposite sides of the band
  boundary)
  [[t|tables/banding_mismatches.csv|OptionA / PAPER_TABLE_INTERNALLY_INCONSISTENT|verdict,notes]]
  [[t|tables/banding_mismatches.csv|OptionB / PAPER_TABLE_INTERNALLY_INCONSISTENT|verdict]].
  This flag is reported as a finding, not corrected in the paper's tables.

### 4.2 Revenue by option and sensitivity (mix window 2025-01..2025-05, frozen at 2025-05)

- **Base case (main cut points).** Merged-car feebate base: 95,760,000 (A) / 98,377,500 (B) S$/yr; E-shift delta
  (6,400 E-de-registered cars/yr re-entering the merged category, Category-B-skewed mix): +43,729,050 (A) /
  +38,624,175 (B); total incl. E-shift: 139,489,050 (A) / 137,001,675 (B) — identical for both E options within
  each feebate option
  [[t|tables/fee_revenue_base.csv|OptionA / E_removed|base_merged_only_sgd,e_shift_delta_sgd,total_sgd,annual_registrations_e_shift]]
  [[t|tables/fee_revenue_base.csv|OptionB / E_removed|base_merged_only_sgd,e_shift_delta_sgd,total_sgd]].
  Average registration-weighted quantum F̄ = 2,091.97 (A) / 2,149.11 (B)
  [[t|tables/fee_price_iteration_log.csv|OptionA|avg_quantum_registration_weighted_SGD]]
  [[t|tables/fee_price_iteration_log.csv|OptionB|avg_quantum_registration_weighted_SGD]].
- **Sensitivity (cut-point / OMV-base variants).** S1: base revenue 59,630,005.35 (A) / 70,363,905.27 (B); total
  incl. E-shift 103,359,055.35 / 108,988,080.27
  [[t|tables/fee_revenue_sensitivity.csv|S1_lta2025_omv / OptionA|base_revenue_sgd,total_incl_e_shift_sgd]]
  [[t|tables/fee_revenue_sensitivity.csv|S1_lta2025_omv / OptionB|base_revenue_sgd,total_incl_e_shift_sgd]];
  S2: base 23,365,106.19 (A) / 43,540,766.62 (B); total incl. E-shift 67,094,156.19 / 82,164,941.62
  [[t|tables/fee_revenue_sensitivity.csv|S2_uniform_weights / OptionA|base_revenue_sgd,total_incl_e_shift_sgd]]
  [[t|tables/fee_revenue_sensitivity.csv|S2_uniform_weights / OptionB|base_revenue_sgd,total_incl_e_shift_sgd]].
  The cut-point base dominates the uncertainty (≈4× swing on base revenue).
- **Incidence.** Feebate total is 1.843% (A, E removed) / 1.862% (A, E cars-only) / 1.811% (B, E removed) /
  1.83% (B, E cars-only) of total COE revenue
  [[t|tables/fee_revenue_incidence.csv|OptionA / E_removed|incidence_pct_of_total_coe]]
  [[t|tables/fee_revenue_incidence.csv|OptionA / E_cars_only|incidence_pct_of_total_coe]]
  [[t|tables/fee_revenue_incidence.csv|OptionB / E_removed|incidence_pct_of_total_coe]]
  [[t|tables/fee_revenue_incidence.csv|OptionB / E_cars_only|incidence_pct_of_total_coe]];
  merged-car COE revenue 6,662,495,160 (A) / 6,659,564,391 (B)
  [[t|tables/fee_revenue_incidence.csv|OptionA / E_removed|merged_car_coe_revenue_sgd]]
  [[t|tables/fee_revenue_incidence.csv|OptionB / E_removed|merged_car_coe_revenue_sgd]];
  D revenue 142,990,250.16 (= 523.0/round × 24 × 11,391.83, window 2026-08 b1..2026-10 b2)
  [[t|tables/fee_revenue_incidence.csv|OptionA / E_removed|d_coe_revenue_sgd,d_quota_per_round,d_price_sgd]].
- **Price-fee iteration (COMPUTED).** Converged in 2 iterations to residual 3.63798e-12 bids (tolerances
  0.01 S$ / 1e-06)
  [[t|tables/fee_price_iteration_log.csv|OptionA|final_residual_bids,tolerance_price_SGD,tolerance_bids]];
  with-fee latest prices 129,873.20 (A) / 129,816.07 (B) at 2026-10 b2
  [[t|tables/merged_price_optionA_withfee.csv|back_solved_history / 2026-10 / 2|withfee_price_point]]
  [[t|tables/merged_price_optionB_withfee.csv|back_solved_history / 2026-10 / 2|withfee_price_point]];
  forward-end PQP-level values 129,800.2 (A) / 129,743.0 (B)
  [[t|tables/fee_price_iteration_log.csv|OptionA|withfee_latest_forward_SGD]]
  [[t|tables/fee_price_iteration_log.csv|OptionB|withfee_latest_forward_SGD]].
- **Negative controls.** Zero-quantum run: exactly zero demand shift and zero revenue (max price deviation
  2.910e-11 S$); zero-elasticity run: with-fee price = no-fee price (INV-8a/8b PASS)
  [[t|verification/invariant_checks.csv|INV-8a|actual,status]]
  [[t|verification/invariant_checks.csv|INV-8b|actual,status]].
- **Demand shifts (scenario elasticity only; windows 2010-01..2026-10 × mix 2025-01..2025-05).** Total −673.09
  (A) / −691.47 (B) bids/yr via κ_M = 0.321748 bids/S$
  [[t|tables/fee_price_iteration_log.csv|OptionA|feebate_demand_shift_bids,merged_demand_slope_kappa_bids_per_SGD]]
  [[t|tables/fee_price_iteration_log.csv|OptionB|feebate_demand_shift_bids]].
  EV: −686.98 (A) / −595.44 (B) vs ICE +13.89 (A) / −96.03 (B); the EV share of the total shift is 102.06% (A) /
  86.11% (B) [[t|tables/segment_shift.csv|OptionA / EV_share_of_total_shift|delta_bids_per_year,pct_of_total_shift,note]]
  [[t|tables/segment_shift.csv|OptionB / EV_share_of_total_shift|delta_bids_per_year,note,pct_of_total_shift]].
  Luxury (OMV > 49,662, the PROPOSED 75th cut point): −1,201.47 (A) / −1,200.55 (B); mass (OMV ≤ 49,662):
  +528.38 (A) / +509.07 (B)
  [[t|tables/segment_shift.csv|OptionA / luxury_vs_mass_luxury|delta_bids_per_year,note]]
  [[t|tables/segment_shift.csv|OptionA / luxury_vs_mass_mass|delta_bids_per_year]]
  [[t|tables/segment_shift.csv|OptionB / luxury_vs_mass_luxury|delta_bids_per_year]]
  [[t|tables/segment_shift.csv|OptionB / luxury_vs_mass_mass|delta_bids_per_year]].

## 5. Category E / C interaction (SCENARIO, regime start 2027-01-01)

- **ASSUMPTION (E-to-car share).** Base case: 100% of E de-registrations re-enter the merged car category as new
  registrations, 6,400/yr, Category-B-skewed OMV composition (ASSUMPTION; sensitivity 50–100%)
  [[t|tables/fee_revenue_base.csv|OptionA / E_removed|annual_registrations_e_shift,base_composition]].
- **E removed.** One-round demand pulse at the 2027-01 b1 round: +459.5 bids, +1,428.14 S$ price effect
  [[t|tables/ec_scenario_E_removed.csv|forward_scenario / 2027-01 / 1 / merged_car|e_shift_bids,e_shift_price_effect_sgd]];
  E quota 0 from 2027-01. Per-band E-shift revenue contribution (mix window 2025-01..2025-05, frozen at 2025-05):
  0–10th −5,060,259.84 [[t|tables/e_shift_feebate_base_delta.csv|E_removed / 0-10th|share_of_e_shift_pct,quantum_revenue_contribution_sgd]];
  10–35th −7,458,453.88 [[t|tables/e_shift_feebate_base_delta.csv|E_removed / 10-35th|share_of_e_shift_pct,quantum_revenue_contribution_sgd]];
  35–50th 0 [[t|tables/e_shift_feebate_base_delta.csv|E_removed / 35-50th|share_of_e_shift_pct,quantum_revenue_contribution_sgd]];
  50–75th +12,563,321.21 [[t|tables/e_shift_feebate_base_delta.csv|E_removed / 50-75th|share_of_e_shift_pct,quantum_revenue_contribution_sgd]];
  >75th +38,579,593.67 [[t|tables/e_shift_feebate_base_delta.csv|E_removed / >75th|share_of_e_shift_pct,quantum_revenue_contribution_sgd]];
  shares of the E-shift: 5.2711 / 15.5384 / 12.8298 / 26.1736 / 40.1871%
  [[t|tables/e_shift_feebate_base_delta.csv|E_removed / 0-10th|share_of_e_shift_pct]]
  [[t|tables/e_shift_feebate_base_delta.csv|E_removed / 10-35th|share_of_e_shift_pct]]
  [[t|tables/e_shift_feebate_base_delta.csv|E_removed / 35-50th|share_of_e_shift_pct]]
  [[t|tables/e_shift_feebate_base_delta.csv|E_removed / 50-75th|share_of_e_shift_pct]]
  [[t|tables/e_shift_feebate_base_delta.csv|E_removed / >75th|share_of_e_shift_pct]].
- **Category C (both E options).** C price held flat at 91,813.5 (window 2026-08 b1..2026-10 b2 — C/E price
  response NOT DETECTABLE, so flat is the conservative revenue bound)
  [[t|tables/fee_revenue_incidence.csv|OptionA / E_removed|c_price_sgd,c_window]];
  C quota under removal rises 7,468 → 8,298 per yr, exactly ×1/0.9 = +11.11% (paper fn5: E receives 10% of A/B/C
  de-registrations; removing E redirects that share)
  [[t|tables/fee_revenue_incidence.csv|OptionA / E_cars_only|c_quota_per_year]]
  [[t|tables/fee_revenue_incidence.csv|OptionA / E_removed|c_quota_per_year]]
  [[t|verification/invariant_checks.csv|INV-9|expected,actual,status]];
  C forward quota 345.74/round (removed) vs 311.17 (cars-only) at the 2027-12 end
  [[t|tables/ec_scenario_E_removed.csv|forward_scenario / 2027-12 / 1 / C|quota,price]]
  [[t|tables/ec_scenario_E_cars_only.csv|forward_scenario / 2027-12 / 1 / C|quota]];
  C annual revenue 685,663,218 (cars-only) → 761,868,423 (removed)
  [[t|tables/fee_revenue_incidence.csv|OptionA / E_cars_only|c_coe_revenue_sgd]]
  [[t|tables/fee_revenue_incidence.csv|OptionA / E_removed|c_coe_revenue_sgd]].
- **E cars-only.** E retained for car registration; E premium over max(A,B) decays linearly from 3,777.33
  (2027-01 b1) [[t|tables/ec_scenario_E_cars_only.csv|forward_scenario / 2027-01 / 1 / E|e_premium_over_car_sgd,quota]]
  to 0 (2027-04 b1, start of round 7)
  [[t|tables/ec_scenario_E_cars_only.csv|forward_scenario / 2027-04 / 1 / E|e_premium_over_car_sgd]],
  with E quota flat at 266.67/round
  [[t|tables/ec_scenario_E_cars_only.csv|forward_scenario / 2027-01 / 1 / E|quota]].

## 6. Renewal-holder impacts (SCENARIO, regime start 2027-01-01; mix window 2017-01..2017-12 OBSERVED + LTA OMV
2017 edition; cut points 2025-01..2025-05, frozen at 2025-05)

- **Vintage and cohort.** Transition-year (2027) renewing cohort = vintage **2017 = 2027 − 10** (initial COE
  term); 2016 cohort pre-regime, excluded. Cohort volume 91,922 (A pricing) / 91,921 (B pricing) from the 2017
  slice of the frozen registration file (4,265 valid car rows, 56 makes), model OMVs from the LTA OMV 2017
  edition (5,178 model-month rows, 1,170 distinct models)
  [[t|tables/renewal_impact_master.csv|OptionA+E_removed+renewal_feebate_yes|cohort_volume,vintage,vintage_derivation]]
  [[t|tables/renewal_impact_master.csv|OptionB+E_removed+renewal_feebate_yes|cohort_volume]].
  The LTA annual-statistics table gives 2017 A = 46,076 and B = 45,699 (= 91,775)
  [[t|tables/renewal_impact_master.csv|OptionA+E_removed+renewal_feebate_yes|preA_registrations,preB_registrations]];
  the 147-vehicle difference vs the data slice is carried as an explicit E_residual class
  [[t|tables/renewal_impact_master.csv|OptionA+E_removed+renewal_feebate_yes|Eresidual_registrations]].
  Historical Car Cost 2017 PDFs were unavailable (4 probed URLs all 404), so the 2017 mix is from the actual
  2017 registrations slice + LTA OMV 2017 edition — NOT the 2025 fallback.
- **Pricing basis (per-cell PQP).** Renewal costs are priced at each cell's own merged-car **PQP** (3-month MA of
  the cell's own with-fee price path), never at the clearing price and never at a reused option-level PQP.
  At the 2027-12 transition-year end: 129,800.16 (all Option A cells) / 129,743.03 (all Option B cells)
  [[t|tables/renewal_impact_master.csv|OptionA+E_removed+renewal_feebate_yes|pqp_2027_12_sgd]]
  [[t|tables/renewal_impact_master.csv|OptionB+E_removed+renewal_feebate_yes|pqp_2027_12_sgd]];
  at the 2027-01 start of the regime: 130,122.07 (A, E removed) / 129,884.05 (A, E cars-only)
  [[t|tables/renewal_impact_master.csv|OptionA+E_removed+renewal_feebate_yes|pqp_2027_01_sgd]]
  [[t|tables/renewal_impact_master.csv|OptionA+E_cars_only+renewal_feebate_yes|pqp_2027_01_sgd]]
  and 130,064.94 (B, E removed) / 129,826.91 (B, E cars-only)
  [[t|tables/renewal_impact_master.csv|OptionB+E_removed+renewal_feebate_yes|pqp_2027_01_sgd]]
  [[t|tables/renewal_impact_master.csv|OptionB+E_cars_only+renewal_feebate_yes|pqp_2027_01_sgd]];
  the E-removed cells sit +238.02 (A) / +238.03 (B) S$ above their E-cars-only counterparts — the one-round pulse
  (1,428.14 S$) averaged over the 6-bid PQP window
  [[t|tables/ec_scenario_E_removed.csv|forward_scenario / 2027-01 / 1 / merged_car|e_shift_price_effect_sgd]].
- **ASSUMPTION (full-cohort renewal).** The whole 2017 cohort renews in the transition year (upper bound; actual
  renewal behaviour is not modelled) — stated in every renewal table's citation column
  [[t|tables/renewal_impact_master.csv|OptionA+E_removed+renewal_feebate_yes|citation]].
- **Winners and losers (PROPOSED 2025 cut points applied to a 2017-vintage cohort; mix window 2017-01..2017-12;
  cut points 2025-01..2025-05).** Per vehicle: pre-A holders −12,628.77 S$ (A) / −9,260.73 S$ (B); pre-B holders
  +1,393.10 S$ (A) / +1,587.45 S$ (B); E_residual holders +6,832.65 S$ (A) / +6,034.69 S$ (B); pre-A − pre-B per
  vehicle −14,021.87 (A) / −10,848.18 (B)
  [[t|tables/renewal_impact_master.csv|OptionA+E_removed+renewal_feebate_yes|preA_per_vehicle_quantum_sgd,preB_per_vehicle_quantum_sgd,Eresidual_per_vehicle_quantum_sgd,preA_minus_preB_per_vehicle_sgd]]
  [[t|tables/renewal_impact_master.csv|OptionB+E_removed+renewal_feebate_yes|preA_per_vehicle_quantum_sgd,preB_per_vehicle_quantum_sgd,Eresidual_per_vehicle_quantum_sgd,preA_minus_preB_per_vehicle_sgd]].
  Class totals: pre_A −581,883,150 (A) / −426,697,350 (B); pre_B +63,663,150 (A) / +72,544,800 (B)
  [[t|tables/renewal_impact_master.csv|OptionA+E_removed+renewal_feebate_yes|preA_quantum_sgd,preB_quantum_sgd]]
  [[t|tables/renewal_impact_master.csv|OptionB+E_removed+renewal_feebate_yes|preA_quantum_sgd,preB_quantum_sgd]].
  The cohort mean OMV is 22,002.27 — below the Option A 35th cut point (28,877) — so most of the cohort lands in
  the rebate bands; winner: pre_A, loser: pre_B (all renewal_feebate_yes cells)
  [[t|data/processed/renewal_cohort_banded.csv|2017 / PROPOSED_2025pct / OptionA / pre_A|avg_omv_sgd]]
  [[t|tables/banding_cutpoints.csv|OptionA / 35 / main|omv_cutpoint]]
  [[t|tables/renewal_impact_master.csv|OptionA+E_removed+renewal_feebate_yes|winner_preA_vs_preB,loser_preA_vs_preB]].
- **Annual transition-year cost (all 8 cells; mix window 2017-01..2017-12).** Option A: 11,931,490,307.52 (no
  feebate) → 11,414,274,707.52 (feebate applied) = −517,215,600 S$/yr net rebate; per vehicle 129,800.16 →
  124,173.48 [[t|tables/renewal_impact_master.csv|OptionA+E_removed+renewal_feebate_no|annual_cost_pqp_only_sgd,annual_quantum_revenue_sgd,annual_cost_total_sgd,per_vehicle_cost_pqp_only_sgd,per_vehicle_cost_total_sgd]]
  [[t|tables/renewal_impact_master.csv|OptionA+E_removed+renewal_feebate_yes|annual_cost_total_sgd,per_vehicle_cost_total_sgd,delta_vs_no_feebate_cell_sgd]];
  Option B: 11,926,237,506.23 → 11,572,972,056.23 = −353,265,450 S$/yr; per vehicle 129,743.03 → 125,899.93
  [[t|tables/renewal_impact_master.csv|OptionB+E_removed+renewal_feebate_no|annual_cost_pqp_only_sgd,per_vehicle_cost_pqp_only_sgd]]
  [[t|tables/renewal_impact_master.csv|OptionB+E_removed+renewal_feebate_yes|annual_cost_total_sgd,per_vehicle_cost_total_sgd,delta_vs_no_feebate_cell_sgd]];
  the renewal_feebate_no cells carry zero quantum effect by construction (identity: cost = PQP × cohort).
- **Sensitivity (vintage cut points; mix window 2017-01..2017-12).** Re-banding the 2017 cohort at 2017-vintage
  percentiles — Option A: 23,052 / 26,379
  [[t|data/processed/renewal_cohort_banded.csv|2017 / VINTAGE_2017pct / OptionA / 1|cutpoints_sgd,registrations]];
  Option B: 16,570.25 / 23,052 / 26,379 / 35,155
  [[t|data/processed/renewal_cohort_banded.csv|2017 / VINTAGE_2017pct / OptionB / 5|cutpoints_sgd,registrations]] —
  shifts the cohort composition (e.g. Option A pre_A registrations in band 1 fall from the majority at PROPOSED
  cut points to 25,458.33 at vintage cut points, while pre_B rises to 7,456.34 in band 1 and 33,533.33 in band 3)
  [[t|data/processed/renewal_cohort_banded.csv|2017 / VINTAGE_2017pct / OptionA / 1|registrations]]
  [[t|data/processed/renewal_cohort_banded.csv|2017 / VINTAGE_2017pct / OptionA / 3|registrations]],
  largely neutralising the net rebate — the direction of the renewal effect is cut-point-base-dependent.

## 7. Unintended consequences (COMPUTED where quantified; DIRECTIONAL otherwise; mix window 2025-01..2025-05,
frozen at 2025-05)

- **Band-boundary spec gaming (±5% OMV zones around each cut point — documented analytical choice).** Option A:
  p35 zone 27,433.15–30,320.85 (23 models, 11.837% of mix ≈ 5,418.3 registrations/yr, S$15,000 quantum at stake)
  [[t|tables/boundary_gaming_zones.csv|OptionA / 35|zone_lo_sgd,zone_hi_sgd,n_models_in_zone,zone_share_pct_covered_mix,est_registrations_annual_in_zone,quantum_at_stake_sgd,omv_adjustment_edge_sgd]];
  p50 zone 34,258.9–37,865.1 (23 models, **13.789% ≈ 6,312.1/yr — the largest single exposure**, S$15,000 at stake)
  [[t|tables/boundary_gaming_zones.csv|OptionA / 50|zone_lo_sgd,zone_hi_sgd,n_models_in_zone,zone_share_pct_covered_mix,est_registrations_annual_in_zone,quantum_at_stake_sgd]].
  Option B: p10 zone 19,294.5–21,325.5 (7 models, 5.558% ≈ 2,544.0/yr)
  [[t|tables/boundary_gaming_zones.csv|OptionB / 10|zone_lo_sgd,zone_hi_sgd,n_models_in_zone,zone_share_pct_covered_mix,est_registrations_annual_in_zone,quantum_at_stake_sgd]];
  p35 (23 models, 11.837% ≈ 5,418.5/yr)
  [[t|tables/boundary_gaming_zones.csv|OptionB / 35|zone_share_pct_covered_mix,est_registrations_annual_in_zone]];
  p50 (23 models, 13.789% ≈ 6,312.2/yr)
  [[t|tables/boundary_gaming_zones.csv|OptionB / 50|zone_share_pct_covered_mix,est_registrations_annual_in_zone]];
  p75 zone 47,178.9–52,145.1 (19 models, 6.837% ≈ 3,129.9/yr); S$7,500 quantum at stake at every Option B
  boundary [[t|tables/boundary_gaming_zones.csv|OptionB / 75|zone_lo_sgd,zone_hi_sgd,n_models_in_zone,zone_share_pct_covered_mix,est_registrations_annual_in_zone,quantum_at_stake_sgd]].
  Crossing a boundary requires an OMV move of 1,443.85 S$ at the Option A p35 boundary (5% of the cut point)
  [[t|tables/boundary_gaming_zones.csv|OptionA / 35|omv_adjustment_edge_sgd]].
- **Variant-family classification distortion.** 139 model families (base-name-stripped rule, documented). Option
  A: 12 families span bands, 28 models affected, 12.90% of the 217-model catalog mis-banded relative to the
  family mean, max within-family quantum difference S$15,000 (largest: BYD :: SEAL, OMV range 34,833–37,458,
  2 models) [[t|tables/classification_distortion.csv|OptionA / option_summary|n_families,n_spanning_families,members_affected,mis_banded_share_pct,max_within_family_quantum_diff_sgd,mis_banded_denominator]]
  [[t|tables/classification_distortion.csv|OptionA / BYD :: SEAL / spanning_family|omv_range_sgd,within_family_quantum_diff_sgd]];
  Option B: 20 spanning families, 55 affected, 25.35% mis-banded, max difference S$7,500
  [[t|tables/classification_distortion.csv|OptionB / option_summary|n_families,n_spanning_families,members_affected,mis_banded_share_pct,max_within_family_quantum_diff_sgd,mis_banded_denominator]].
- **Segment demand shifts** (windows 2010-01..2026-10 × mix 2025-01..2025-05): EV demand down (−686.98 A /
  −595.44 B bids/yr) [[t|tables/segment_shift.csv|OptionA / EV_share_of_total_shift|delta_bids_per_year]]
  [[t|tables/segment_shift.csv|OptionB / EV_share_of_total_shift|delta_bids_per_year]];
  luxury (OMV > 49,662) down (−1,201.47 A / −1,200.55 B)
  [[t|tables/segment_shift.csv|OptionA / luxury_vs_mass_luxury|delta_bids_per_year,note]]
  [[t|tables/segment_shift.csv|OptionB / luxury_vs_mass_luxury|delta_bids_per_year]];
  mass (OMV ≤ 49,662) up (+528.38 A / +509.07 B)
  [[t|tables/segment_shift.csv|OptionA / luxury_vs_mass_mass|delta_bids_per_year]]
  [[t|tables/segment_shift.csv|OptionB / luxury_vs_mass_mass|delta_bids_per_year]] — the feebate shifts the mix
  toward cheaper cars.
- **Renewal-holder effects** — the net-rebate finding of headline 2 (§6): renewal cost falls for older low-OMV
  cars, reducing upgrade pressure (mix window 2017-01..2017-12)
  [[t|tables/used_car_directional.csv|used_car_holding_incentive_renewal_feebate|statement]].
- **Used-car channel (DIRECTIONAL only — no usable data).** (i) Upper-band new cars become relatively more
  expensive (+7,500 / +15,000 S$ PROPOSED quantums on top of COE cost), so used-car relative attractiveness for
  high-OMV segments is directionally UP, stronger under Option A's top band; (ii) the renewal net-rebate makes
  holding/renewing older low-OMV cars directionally cheaper; (iii) E-removal removes the urgent-bid fast lane,
  pushing time-constrained buyers directionally toward used cars. No used-car numbers are produced — labelled
  DIRECTIONAL, not COMPUTED (mix window 2025-01..2025-05, frozen at 2025-05)
  [[t|tables/used_car_directional.csv|used_car_relative_attractiveness_upper_bands|statement,applies_to]]
  [[t|tables/used_car_directional.csv|used_car_urgency_channel_E_removed|statement]].
- **E/C supply interaction.** C quota +11.11% under E-removal with C price flat (conservative bound); C
  (goods/buses) supply is directionally eased, E urgent-demand channel closed (§5; price window
  2026-08 b1..2026-10 b2, mix window 2025-01..2025-05)
  [[t|verification/invariant_checks.csv|INV-9|expected]].

## 8. Master matrix (SCENARIO, regime start 2027-01-01; 8 cells = Option A/B × E removed/cars-only × renewal
feebate no/yes)

- **Per-cell PQP derivation (stated).** Each cell's PQP series is the 3-month moving average of that cell's *own*
  merged-car with-fee price path (own-path MA; the 2027-01 window spans 2026-09; 2026-10; 2027-01 — the last 3
  months with bidding ending at the regime start, 6 biddings). The MA-3 convention is externally validated
  (window 2002-02..2026-09 published PQP vs observed per-bidding premiums): recomputation matches within max
  0.83 S$ / mean 0.428 S$ (pooled A+B, 392 months, 2,352 bids)
  [[t|tables/pqp_derivation.csv|POOLED A+B (merged-PQP inputs) — HEADLINE / method_validation|max_abs_diff_sgd,mean_abs_diff_sgd,n_months,n_bids_compared,rule_note]];
  the residual signature (published − MA3 ∈ {0, 1/6, …, 5/6} S$) holds for 783 of 784 category-months, i.e. LTA
  rounds the MA up to the next whole dollar. At the 2027-12 transition-year end the per-cell PQP is 129,800.16
  (all Option A cells) / 129,743.03 (all Option B cells)
  [[t|tables/master_matrix.csv|OptionA+E_removed+renewal_feebate_no|pqp_2027_12_sgd]]
  [[t|tables/master_matrix.csv|OptionB+E_removed+renewal_feebate_no|pqp_2027_12_sgd]].
- **Cells and key values (2027-12; windows 2010-01..2026-10 back-solved + 2027 forward; mix 2025-01..2025-05;
  cohort 2017-01..2017-12).**
  - Option A, E removed, renewal no: PQP 129,800.16; feebate revenue 139,489,050 (base excl. E-shift 95,760,000;
    E-shift +43,729,050); renewal cost 11,931,490,307.52, delta 0
    [[t|tables/master_matrix.csv|OptionA+E_removed+renewal_feebate_no|pqp_2027_12_sgd,feebate_revenue_base_sgd,feebate_revenue_base_excl_e_shift_sgd,feebate_revenue_e_shift_delta_sgd,renewal_annual_cost_total_sgd,renewal_delta_vs_no_feebate_sgd]].
  - Option A, E removed, renewal yes: same prices/revenue; renewal cost 11,414,274,707.52, delta −517,215,600;
    per-vehicle pre_A −12,628.77 / pre_B 1,393.1; winner pre_A, loser pre_B
    [[t|tables/master_matrix.csv|OptionA+E_removed+renewal_feebate_yes|renewal_annual_cost_total_sgd,renewal_delta_vs_no_feebate_sgd,renewal_per_vehicle_preA_sgd,renewal_per_vehicle_preB_sgd,renewal_winner,renewal_loser]].
  - Option A, E cars-only, renewal no/yes: identical feebate revenue 139,489,050; 2027-01 PQP context 129,884.05
    (vs 130,122.07 for E removed — the +238.02 pulse difference); renewal delta 0 / −517,215,600
    [[t|tables/master_matrix.csv|OptionA+E_cars_only+renewal_feebate_no|feebate_revenue_base_sgd,pqp_2027_01_sgd_context]]
    [[t|tables/master_matrix.csv|OptionA+E_cars_only+renewal_feebate_yes|renewal_delta_vs_no_feebate_sgd]]
    [[t|tables/master_matrix.csv|OptionA+E_removed+renewal_feebate_no|pqp_2027_01_sgd_context]].
  - Option B cells: PQP 129,743.03; feebate revenue 137,001,675 (base 98,377,500 + E-shift 38,624,175); renewal
    cost 11,926,237,506.23 → 11,572,972,056.23 (delta −353,265,450); per-vehicle pre_A −9,260.73 / pre_B 1,587.45;
    winner pre_A, loser pre_B; 2027-01 PQP context 130,064.94 (removed) / 129,826.91 (cars-only)
    [[t|tables/master_matrix.csv|OptionB+E_removed+renewal_feebate_no|pqp_2027_12_sgd,pqp_2027_01_sgd_context,feebate_revenue_base_sgd,feebate_revenue_base_excl_e_shift_sgd,feebate_revenue_e_shift_delta_sgd,renewal_annual_cost_total_sgd]]
    [[t|tables/master_matrix.csv|OptionB+E_removed+renewal_feebate_yes|renewal_annual_cost_total_sgd,renewal_delta_vs_no_feebate_sgd,renewal_per_vehicle_preA_sgd,renewal_per_vehicle_preB_sgd,renewal_winner,renewal_loser]]
    [[t|tables/master_matrix.csv|OptionB+E_cars_only+renewal_feebate_no|pqp_2027_01_sgd_context]].
- **Toggle effect.** The renewal-feebate toggle changes *only* the renewal quantum column: the 4 distinct price
  paths (Option A/B × E removed/cars-only) are byte-identical across the toggle (max diff 0.0 within toggle
  pairs) [[t|tables/pqp_derivation.csv|OptionA+E_removed+renewal_feebate_no / cell|toggle_pair_max_diff_sgd]].
  The per-cell S1/S2 base-revenue sensitivity range is recorded in every cell
  [[t|tables/master_matrix.csv|OptionA+E_removed+renewal_feebate_no|feebate_revenue_sensitivity_range]].

## 9. Verification and caveats

- **Verification suite (Step 16, `src/verify.py` → `tables/verification_report.csv`).** 10 check groups (a)–(j):
  row-count reconciliation for every fetched resource; time anchors (COE last month 2026-10 has both biddings;
  registrations last month 2025-05) + 8 spot prices against the reference set; the 2026 A>B inversion set at
  per-bidding resolution; table-figure traceability of this report + STATS_SUMMARY.md (zero untraceable numbers);
  cross-foots (band shares 100.0/99.99% per option
  [[t|tables/banding_shares.csv|OptionA / 0-35th|cross_foot_sum_pct]]
  [[t|tables/banding_shares.csv|OptionB / 0-10th|cross_foot_sum_pct]];
  net feebate revenue independently recomputed to the dollar: base diff 0.0, E-shift diff −26.0 within 150.0
  tolerance [[t|verification/crossfoot_log.csv|base_OptionA / exact_band_counts|expected_sgd,actual_sgd,diff_sgd,tolerance_sgd]]
  [[t|verification/crossfoot_log.csv|e_shift_OptionB / batch_e_band_counts|expected_sgd,actual_sgd,diff_sgd,tolerance_sgd]]);
  scenario invariants / negative controls (INV-7, INV-8a, INV-8b, INV-9, INV-10 all PASS)
  [[t|verification/invariant_checks.csv|INV-7|status]];
  PQP MA-3 recheck vs published PQP (max 0.83 S$ / mean 0.428 S$ pooled A+B)
  [[t|tables/pqp_derivation.csv|POOLED A+B (merged-PQP inputs) — HEADLINE / method_validation|max_abs_diff_sgd,mean_abs_diff_sgd]];
  scenario-label audit (every renewal/E-C/master-matrix label carries the regime start date; every renewal table
  priced at the cell-level merged PQP; transition-year cohort vintage 2017 = start − 10)
  [[t|tables/renewal_impact_master.csv|OptionA+E_removed+renewal_feebate_yes|vintage,vintage_derivation,price_basis]];
  freeze-label audit (every mix-based number in the report carries an explicit data-window tag); provenance audit
  (sha256 + row counts on disk for all raw/processed files). Suite result on the final pass: 0 hard failures; 1
  documented exception (Option B band shares cross-foot to 99.99% at 2dp rounding) — see
  `tables/verification_report.csv`.
- **PQP method validation detail (window 2002-02..2026-09 published vs 2010-01..2026-10 observed).** Per
  category: A max 0.83 / mean 0.41 [[t|tables/pqp_derivation.csv|category A / method_validation|max_abs_diff_sgd,mean_abs_diff_sgd]];
  B max 0.83 / mean 0.446 (max at 2026-09 — known LTA-side −0.83 S$ deviation, logged)
  [[t|tables/pqp_derivation.csv|category B / method_validation|max_abs_diff_sgd,mean_abs_diff_sgd,month_of_max]];
  C max 0.83 / mean 0.438 [[t|tables/pqp_derivation.csv|category C / method_validation|max_abs_diff_sgd,mean_abs_diff_sgd]];
  D max 3,205.5 / mean 16.776 with exactly one explained outlier — the SINGSTAT single-cell error at 2010-01 b2
  (SINGSTAT QP 852 vs LTA 20,090; LTA treated as authoritative; only discrepancy among 1,980 compared QP cells)
  [[t|tables/pqp_derivation.csv|category D / method_validation|max_abs_diff_sgd,mean_abs_diff_sgd,result]].
- **Data limits (all labelled).** Registrations frozen at 2025-05 (51,669 rows, 2016-01..2025-05)
  [[t|verification/provenance_log.csv|registrations|fetched_rows]]; 29,463 null rows excluded (57.0%); the LTA
  2025 model-level OMV *distribution* is not public — main banding uses the labelled Jan–May 2025 fallback mix,
  LTA 2025 edition is sensitivity S1 (window 2025-01..2025-05, frozen at 2025-05); published PQP exists for A–D
  only (no E PQP published, window 2002-02..2026-09); historical Car Cost 2017 PDFs unavailable (4 probed URLs,
  all 404) — the 2017 renewal mix is built from the actual 2017 registration slice + LTA OMV 2017 edition, not a
  fallback (window 2017-01..2017-12); the used-car channel has no usable data (directional only).
- **Assumptions register.** (1) Regime start 2027-01-01 (no implementation date in the paper); (2) E-to-car
  re-entry share 100% base, sensitivity 50–100%; (3) ±5% OMV zone width for gaming analysis (documented
  analytical choice); (4) forward merged quota 2,137.5/round (last-6 average, held)
  [[t|tables/fee_revenue_incidence.csv|OptionA / E_removed|merged_quota_per_round]];
  (5) full-cohort renewal in the transition year (upper bound)
  [[t|tables/renewal_impact_master.csv|OptionA+E_removed+renewal_feebate_yes|citation]];
  (6) Jan–May 2025 mix for banding (frozen window; S1/S2 sensitivities); (7) C price held flat (NOT DETECTABLE —
  conservative revenue bound) [[t|tables/fee_revenue_incidence.csv|OptionA / E_removed|c_price_sgd]];
  (8) renewal costs priced at per-cell merged PQP (documented basis, §8).
- **What is PROPOSED vs COMPUTED.** PROPOSED: band structure, percentile anchors, quantums, annual review,
  E-options, E 10% de-registration share (paper s2.15–s2.23, Tables 1/2, fn5). COMPUTED (scenario estimates): cut
  points, shares, revenues, price paths, PQP series, demand shifts, renewal costs, gaming zones, distortion
  shares. OBSERVED: bidding results, registrations, published PQP. DIRECTIONAL: used-car channel.
- **Charts.** `charts/` — 8 figures, all labelled OBSERVED/SCENARIO/DIRECTIONAL with data windows
  (`src/make_charts.py`): FIG 1 A/B per-bidding convergence with the 2026 inversion set; FIG 2 merged price paths
  (no-fee vs with-fee, per-cell PQP, E pulse); FIG 3 OMV histogram with band overlays; FIG 4 feebate revenue by
  option with E-shift delta and sensitivities; FIG 5 demand shift by band; FIG 6 renewal costs per cell at
  cell-level PQP (regime start + vintage in title); FIG 7 C/E quota and price paths under both E options; FIG 8
  ±5% gaming zones with registration shares.

*End of report. Every numeric claim above was machine-verified against a cited table cell by `src/verify.py`
(check d, zero untraceable numbers) — see `verification/report_traceability.csv`.*
