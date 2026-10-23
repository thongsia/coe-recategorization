# STATS_SUMMARY — LTA COE re-categorisation study (one page)

Every value below is machine-traceable to a table cell (inline citation `[[t|table|rowkey|cols]]`), a documented
derived identity, or the provenance allowlist (`docs/provenance.md`). Regime start: 2027-01-01 (ASSUMPTION). Data
windows: bids 2010-01..2026-10 (OBSERVED); registrations 2016-01..2025-05 (frozen at 2025-05); banding mix
2025-01..2025-05 (frozen at 2025-05); renewal cohort 2017-01..2017-12 (OBSERVED); published PQP 2002-02..2026-09.

## Observed baseline

- 2026-10 b2 spot: A 132,004 / B 131,901 (spread +103) [[t|tables/inversions_2026.csv|2026-10 / 2|a_premium,b_premium,spread_a_minus_b]];
  b1: A 130,001 [[t|data/raw/coe_bids.csv|2026-10 / 1 / Category A|premium]] B 130,100 [[t|data/raw/coe_bids.csv|2026-10 / 1 / Category B|premium]]
  C 91,889 [[t|data/raw/coe_bids.csv|2026-10 / 1 / Category C|premium]] D 11,012 [[t|data/raw/coe_bids.csv|2026-10 / 1 / Category D|premium]]
  E 137,000 [[t|data/raw/coe_bids.csv|2026-10 / 1 / Category E|premium]];
  b2: C 92,200 [[t|data/raw/coe_bids.csv|2026-10 / 2 / Category C|premium]] E 135,790 [[t|data/raw/coe_bids.csv|2026-10 / 2 / Category E|premium]].
- 2026 A>B inversions: 4 rounds, all b2 — spreads +1,500 [[t|tables/inversions_2026.csv|2026-02 / 2|spread_a_minus_b]],
  +2,009 [[t|tables/inversions_2026.csv|2026-04 / 2|spread_a_minus_b]], +345 [[t|tables/inversions_2026.csv|2026-06 / 2|spread_a_minus_b]],
  +103 [[t|tables/inversions_2026.csv|2026-10 / 2|spread_a_minus_b]].
- 6-round avg E premium over max(A,B): 3,777.33 [[t|tables/ec_scenario_E_cars_only.csv|forward_scenario / 2027-01 / 1 / E|e_premium_over_car_sgd]]
  (window 2026-08 b1..2026-10 b2).
- Demand curves (M3 f-diff, NW-HAC): A +4.99 S$/bid, CI [+3.76,+6.21], p=1.5e-15, MEDIUM
  [[t|tables/evidence_grading.csv|A / M3_fdiff / dbids_received|estimate,ci,p_value,grade]];
  B +8.24 S$/bid, CI [+3.74,+12.75], p=0.000334, LOW [[t|tables/evidence_grading.csv|B / M3_fdiff / dbids_received|estimate,ci,p_value,grade]];
  C/E NOT DETECTABLE; C NC1 lead p=0.018 (FAIL, common-trend artifact)
  [[t|tables/evidence_grading.csv|C / M3_fdiff / dbids_received|grade,negative_control_check]].

## Merged A+B scenario

- No-fee merged price: 131,965.17 (2026-10 b2) [[t|tables/merged_price_nofeebate.csv|back_solved_history / 2026-10 / 2|merged_price_point]];
  forward 2027-12: 131,892.13, within-round spread p10/p90 131,879.89/131,906.66
  [[t|tables/merged_price_nofeebate.csv|forward_scenario / 2027-12 / 2|merged_price_point,merged_price_p10,merged_price_p90]].
- With-fee merged price: latest observed round 2026-10 b2 129,873.20 (A)
  [[t|tables/merged_price_optionA_withfee.csv|back_solved_history / 2026-10 / 2|withfee_price_point]] /
  129,816.07 (B) [[t|tables/merged_price_optionB_withfee.csv|back_solved_history / 2026-10 / 2|withfee_price_point]];
  forward 2027-12 end 129,800.16 (A) [[t|tables/merged_price_optionA_withfee.csv|forward_scenario / 2027-12 / 2|withfee_price_point]] /
  129,743.03 (B) [[t|tables/merged_price_optionB_withfee.csv|forward_scenario / 2027-12 / 2|withfee_price_point]];
  iteration residual 3.63798e-12 bids, tolerances 0.01 S$/1e-06 in 2 iterations
  [[t|tables/fee_price_iteration_log.csv|OptionA|final_residual_bids,tolerance_price_SGD,tolerance_bids,iterations_used]].
- INV-7 bounds [85,000;141,000] (2025-01..2026-10); back-solved min/max 18,761.4/133,760, 0 violations
  [[t|verification/invariant_checks.csv|INV-7|expected,actual]].
- Quota: forward 2,137.5/round [[t|tables/fee_revenue_incidence.csv|OptionA / E_removed|merged_quota_per_round]];
  re-split example 2010-01 b1: A −51.99 / B +51.99 / A bid surplus +241.99, 422 table rows
  [[t|tables/quota_reallocation.csv|back_solved_history / 2010-01 / 1|delta_quota_A,delta_quota_B,bid_surplus_A]].

## Feebate (PROPOSED quantums; COMPUTED estimates)

- Cut points (main, mix 2025-01..2025-05): A 28,877 [[t|tables/banding_cutpoints.csv|OptionA / 35 / main|omv_cutpoint]] /
  36,062 [[t|tables/banding_cutpoints.csv|OptionA / 50 / main|omv_cutpoint]]; B 20,310 [[t|tables/banding_cutpoints.csv|OptionB / 10 / main|omv_cutpoint]] /
  28,877 [[t|tables/banding_cutpoints.csv|OptionB / 35 / main|omv_cutpoint]] / 36,062 [[t|tables/banding_cutpoints.csv|OptionB / 50 / main|omv_cutpoint]] /
  49,662 [[t|tables/banding_cutpoints.csv|OptionB / 75 / main|omv_cutpoint,band_above_quantum_sgd]].
- Band shares (Jan–May 2025 annualised): A 35.16 [[t|tables/banding_shares.csv|OptionA / 0-35th|band_share_pct]] /
  15.74 [[t|tables/banding_shares.csv|OptionA / 35-50th|band_share_pct]] / 49.10 [[t|tables/banding_shares.csv|OptionA / >50th|band_share_pct]]
  (cross-foot 100.0 [[t|tables/banding_shares.csv|OptionA / 0-35th|cross_foot_sum_pct]]);
  B 10.17 [[t|tables/banding_shares.csv|OptionB / 0-10th|band_share_pct]] / 24.98 [[t|tables/banding_shares.csv|OptionB / 10-35th|band_share_pct]] /
  15.74 [[t|tables/banding_shares.csv|OptionB / 35-50th|band_share_pct]] / 24.22 [[t|tables/banding_shares.csv|OptionB / 50-75th|band_share_pct]] /
  24.88 [[t|tables/banding_shares.csv|OptionB / >75th|band_share_pct]] (cross-foot 99.99, 2dp rounding
  [[t|tables/banding_shares.csv|OptionB / 0-10th|cross_foot_sum_pct]]).
- Registrations/yr: base 45,775 (A) [[t|tables/fee_revenue_base.csv|OptionA / E_removed|annual_registrations_base]] /
  45,776 (B) [[t|tables/fee_revenue_base.csv|OptionB / E_removed|annual_registrations_base]];
  E-shift 6,400 [[t|tables/fee_revenue_base.csv|OptionA / E_removed|annual_registrations_e_shift]];
  per-band (A) 16,093 / 7,205 / 22,477 [[t|tables/banding_shares.csv|OptionA / 0-35th|est_registrations_annualised_x12of5]]
  [[t|tables/banding_shares.csv|OptionA / 35-50th|est_registrations_annualised_x12of5]]
  [[t|tables/banding_shares.csv|OptionA / >50th|est_registrations_annualised_x12of5]];
  coverage 98.73% (19,073 of 19,318) [[t|tables/banding_shares.csv|OptionA / 0-35th|coverage_note]].
- Revenue S$/yr: base 95,760,000 (A) [[t|tables/fee_revenue_base.csv|OptionA / E_removed|base_merged_only_sgd]] /
  98,377,500 (B) [[t|tables/fee_revenue_base.csv|OptionB / E_removed|base_merged_only_sgd]];
  E-shift delta +43,729,050 (A) [[t|tables/fee_revenue_base.csv|OptionA / E_removed|e_shift_delta_sgd]] /
  +38,624,175 (B) [[t|tables/fee_revenue_base.csv|OptionB / E_removed|e_shift_delta_sgd]];
  total incl. E-shift 139,489,050 (A) [[t|tables/fee_revenue_base.csv|OptionA / E_removed|total_sgd]] /
  137,001,675 (B) [[t|tables/fee_revenue_base.csv|OptionB / E_removed|total_sgd]];
  avg quantum F̄ 2,091.97 (A) [[t|tables/fee_price_iteration_log.csv|OptionA|avg_quantum_registration_weighted_SGD]] /
  2,149.11 (B) [[t|tables/fee_price_iteration_log.csv|OptionB|avg_quantum_registration_weighted_SGD]].
- Sensitivity: S1 base 59,630,005.35 (A) [[t|tables/fee_revenue_sensitivity.csv|S1_lta2025_omv / OptionA|base_revenue_sgd]] /
  70,363,905.27 (B) [[t|tables/fee_revenue_sensitivity.csv|S1_lta2025_omv / OptionB|base_revenue_sgd]],
  total 103,359,055.35 / 108,988,080.27 [[t|tables/fee_revenue_sensitivity.csv|S1_lta2025_omv / OptionA|total_incl_e_shift_sgd]]
  [[t|tables/fee_revenue_sensitivity.csv|S1_lta2025_omv / OptionB|total_incl_e_shift_sgd]];
  S2 base 23,365,106.19 (A) [[t|tables/fee_revenue_sensitivity.csv|S2_uniform_weights / OptionA|base_revenue_sgd]] /
  43,540,766.62 (B) [[t|tables/fee_revenue_sensitivity.csv|S2_uniform_weights / OptionB|base_revenue_sgd]],
  total 67,094,156.19 / 82,164,941.62 [[t|tables/fee_revenue_sensitivity.csv|S2_uniform_weights / OptionA|total_incl_e_shift_sgd]]
  [[t|tables/fee_revenue_sensitivity.csv|S2_uniform_weights / OptionB|total_incl_e_shift_sgd]].
- Incidence of total COE revenue: 1.843% (A, E removed) [[t|tables/fee_revenue_incidence.csv|OptionA / E_removed|incidence_pct_of_total_coe]] /
  1.862% (A, E cars-only) [[t|tables/fee_revenue_incidence.csv|OptionA / E_cars_only|incidence_pct_of_total_coe]] /
  1.811% (B, E removed) [[t|tables/fee_revenue_incidence.csv|OptionB / E_removed|incidence_pct_of_total_coe]] /
  1.83% (B, E cars-only) [[t|tables/fee_revenue_incidence.csv|OptionB / E_cars_only|incidence_pct_of_total_coe]];
  merged-car revenue 6,662,495,160 (A) [[t|tables/fee_revenue_incidence.csv|OptionA / E_removed|merged_car_coe_revenue_sgd]] /
  6,659,564,391 (B) [[t|tables/fee_revenue_incidence.csv|OptionB / E_removed|merged_car_coe_revenue_sgd]];
  D revenue 142,990,250.16 (= 523.0/round × 24 × 11,391.83)
  [[t|tables/fee_revenue_incidence.csv|OptionA / E_removed|d_coe_revenue_sgd,d_quota_per_round,d_price_sgd]].
- Demand shift: −673.09 (A) [[t|tables/fee_price_iteration_log.csv|OptionA|feebate_demand_shift_bids]] /
  −691.47 (B) [[t|tables/fee_price_iteration_log.csv|OptionB|feebate_demand_shift_bids]] bids/yr (κ_M = 0.321748
  [[t|tables/fee_price_iteration_log.csv|OptionA|merged_demand_slope_kappa_bids_per_SGD]]);
  EV −686.98 (A) [[t|tables/segment_shift.csv|OptionA / EV_share_of_total_shift|delta_bids_per_year]] /
  −595.44 (B) [[t|tables/segment_shift.csv|OptionB / EV_share_of_total_shift|delta_bids_per_year]] vs ICE +13.89 (A) / −96.03 (B)
  [[t|tables/segment_shift.csv|OptionA / EV_share_of_total_shift|note]]
  [[t|tables/segment_shift.csv|OptionB / EV_share_of_total_shift|note]];
  EV share of shift 102.06% (A) [[t|tables/segment_shift.csv|OptionA / EV_share_of_total_shift|pct_of_total_shift]] /
  86.11% (B) [[t|tables/segment_shift.csv|OptionB / EV_share_of_total_shift|pct_of_total_shift]];
  luxury (OMV > 49,662) −1,201.47 (A) [[t|tables/segment_shift.csv|OptionA / luxury_vs_mass_luxury|delta_bids_per_year]] /
  −1,200.55 (B) [[t|tables/segment_shift.csv|OptionB / luxury_vs_mass_luxury|delta_bids_per_year]];
  mass +528.38 (A) [[t|tables/segment_shift.csv|OptionA / luxury_vs_mass_mass|delta_bids_per_year]] /
  +509.07 (B) [[t|tables/segment_shift.csv|OptionB / luxury_vs_mass_mass|delta_bids_per_year]].

## Category E / C

- E-shift pulse (one round, 2027-01 b1): +459.5 bids, +1,428.14 S$
  [[t|tables/ec_scenario_E_removed.csv|forward_scenario / 2027-01 / 1 / merged_car|e_shift_bids,e_shift_price_effect_sgd]];
  per-band revenue contribution (E removed): −5,060,259.84 [[t|tables/e_shift_feebate_base_delta.csv|E_removed / 0-10th|quantum_revenue_contribution_sgd]] /
  −7,458,453.88 [[t|tables/e_shift_feebate_base_delta.csv|E_removed / 10-35th|quantum_revenue_contribution_sgd]] /
  0 [[t|tables/e_shift_feebate_base_delta.csv|E_removed / 35-50th|quantum_revenue_contribution_sgd]] /
  +12,563,321.21 [[t|tables/e_shift_feebate_base_delta.csv|E_removed / 50-75th|quantum_revenue_contribution_sgd]] /
  +38,579,593.67 [[t|tables/e_shift_feebate_base_delta.csv|E_removed / >75th|quantum_revenue_contribution_sgd]];
  shares 5.2711 / 15.5384 / 12.8298 / 26.1736 / 40.1871% [[t|tables/e_shift_feebate_base_delta.csv|E_removed / 0-10th|share_of_e_shift_pct]]
  [[t|tables/e_shift_feebate_base_delta.csv|E_removed / 10-35th|share_of_e_shift_pct]]
  [[t|tables/e_shift_feebate_base_delta.csv|E_removed / 35-50th|share_of_e_shift_pct]]
  [[t|tables/e_shift_feebate_base_delta.csv|E_removed / 50-75th|share_of_e_shift_pct]]
  [[t|tables/e_shift_feebate_base_delta.csv|E_removed / >75th|share_of_e_shift_pct]].
- C: price held flat 91,813.5 [[t|tables/fee_revenue_incidence.csv|OptionA / E_removed|c_price_sgd]]
  (window 2026-08 b1..2026-10 b2 [[t|tables/fee_revenue_incidence.csv|OptionA / E_removed|c_window]]);
  quota 7,468/yr (cars-only) [[t|tables/fee_revenue_incidence.csv|OptionA / E_cars_only|c_quota_per_year]] →
  8,298/yr (removed, exactly +11.11%) [[t|tables/fee_revenue_incidence.csv|OptionA / E_removed|c_quota_per_year]];
  forward quota 2027-12: 345.74/round (removed) [[t|tables/ec_scenario_E_removed.csv|forward_scenario / 2027-12 / 1 / C|quota]] /
  311.17 (cars-only) [[t|tables/ec_scenario_E_cars_only.csv|forward_scenario / 2027-12 / 1 / C|quota]];
  C annual revenue 685,663,218 (cars-only) [[t|tables/fee_revenue_incidence.csv|OptionA / E_cars_only|c_coe_revenue_sgd]] →
  761,868,423 (removed) [[t|tables/fee_revenue_incidence.csv|OptionA / E_removed|c_coe_revenue_sgd]].
- E cars-only: premium 3,777.33 (2027-01 b1) [[t|tables/ec_scenario_E_cars_only.csv|forward_scenario / 2027-01 / 1 / E|e_premium_over_car_sgd]]
  → 0 (2027-04 b1) [[t|tables/ec_scenario_E_cars_only.csv|forward_scenario / 2027-04 / 1 / E|e_premium_over_car_sgd]];
  E quota 266.67/round [[t|tables/ec_scenario_E_cars_only.csv|forward_scenario / 2027-01 / 1 / E|quota]].

## Renewal-holder impacts (vintage 2017 = 2027 − 10; cohort window 2017-01..2017-12)

- Cohort: 91,922 (A) [[t|tables/renewal_impact_master.csv|OptionA+E_removed+renewal_feebate_yes|cohort_volume]] /
  91,921 (B) [[t|tables/renewal_impact_master.csv|OptionB+E_removed+renewal_feebate_yes|cohort_volume]];
  LTA 2017 A=46,076 / B=45,699 (=91,775) [[t|tables/renewal_impact_master.csv|OptionA+E_removed+renewal_feebate_yes|preA_registrations,preB_registrations]];
  E_residual class 147 [[t|tables/renewal_impact_master.csv|OptionA+E_removed+renewal_feebate_yes|Eresidual_registrations]];
  mean OMV 22,002.27 (pre_A, PROPOSED cut points) [[t|data/processed/renewal_cohort_banded.csv|2017 / PROPOSED_2025pct / OptionA / pre_A|avg_omv_sgd]].
- Per-cell PQP: 129,800.16 (all A cells, 2027-12) [[t|tables/renewal_impact_master.csv|OptionA+E_removed+renewal_feebate_yes|pqp_2027_12_sgd]] /
  129,743.03 (all B cells) [[t|tables/renewal_impact_master.csv|OptionB+E_removed+renewal_feebate_yes|pqp_2027_12_sgd]];
  2027-01: 130,122.07 (A removed) [[t|tables/renewal_impact_master.csv|OptionA+E_removed+renewal_feebate_yes|pqp_2027_01_sgd]] /
  129,884.05 (A cars-only) [[t|tables/renewal_impact_master.csv|OptionA+E_cars_only+renewal_feebate_yes|pqp_2027_01_sgd]] /
  130,064.94 (B removed) [[t|tables/renewal_impact_master.csv|OptionB+E_removed+renewal_feebate_yes|pqp_2027_01_sgd]] /
  129,826.91 (B cars-only) [[t|tables/renewal_impact_master.csv|OptionB+E_cars_only+renewal_feebate_yes|pqp_2027_01_sgd]]
  (E-removed − cars-only = +238.02 (A) / +238.03 (B), pulse 1,428.14 over the 6-bid MA window
  [[t|tables/ec_scenario_E_removed.csv|forward_scenario / 2027-01 / 1 / merged_car|e_shift_price_effect_sgd]]).
- Per-vehicle quantum: pre_A −12,628.77 (A) [[t|tables/renewal_impact_master.csv|OptionA+E_removed+renewal_feebate_yes|preA_per_vehicle_quantum_sgd]] /
  −9,260.73 (B) [[t|tables/renewal_impact_master.csv|OptionB+E_removed+renewal_feebate_yes|preA_per_vehicle_quantum_sgd]];
  pre_B +1,393.10 (A) [[t|tables/renewal_impact_master.csv|OptionA+E_removed+renewal_feebate_yes|preB_per_vehicle_quantum_sgd]] /
  +1,587.45 (B) [[t|tables/renewal_impact_master.csv|OptionB+E_removed+renewal_feebate_yes|preB_per_vehicle_quantum_sgd]];
  E_residual +6,832.65 (A) [[t|tables/renewal_impact_master.csv|OptionA+E_removed+renewal_feebate_yes|Eresidual_per_vehicle_quantum_sgd]] /
  +6,034.69 (B) [[t|tables/renewal_impact_master.csv|OptionB+E_removed+renewal_feebate_yes|Eresidual_per_vehicle_quantum_sgd]];
  pre_A − pre_B −14,021.87 (A) [[t|tables/renewal_impact_master.csv|OptionA+E_removed+renewal_feebate_yes|preA_minus_preB_per_vehicle_sgd]] /
  −10,848.18 (B) [[t|tables/renewal_impact_master.csv|OptionB+E_removed+renewal_feebate_yes|preA_minus_preB_per_vehicle_sgd]];
  winner pre_A, loser pre_B [[t|tables/renewal_impact_master.csv|OptionA+E_removed+renewal_feebate_yes|winner_preA_vs_preB,loser_preA_vs_preB]].
- Class totals S$: pre_A −581,883,150 (A) [[t|tables/renewal_impact_master.csv|OptionA+E_removed+renewal_feebate_yes|preA_quantum_sgd]] /
  −426,697,350 (B) [[t|tables/renewal_impact_master.csv|OptionB+E_removed+renewal_feebate_yes|preA_quantum_sgd]];
  pre_B +63,663,150 (A) [[t|tables/renewal_impact_master.csv|OptionA+E_removed+renewal_feebate_yes|preB_quantum_sgd]] /
  +72,544,800 (B) [[t|tables/renewal_impact_master.csv|OptionB+E_removed+renewal_feebate_yes|preB_quantum_sgd]].
- Annual transition-year cost (full-cohort renewal): 11,931,490,307.52 → 11,414,274,707.52 = −517,215,600 (A)
  [[t|tables/renewal_impact_master.csv|OptionA+E_removed+renewal_feebate_no|annual_cost_pqp_only_sgd]]
  [[t|tables/renewal_impact_master.csv|OptionA+E_removed+renewal_feebate_yes|annual_cost_total_sgd,delta_vs_no_feebate_cell_sgd]];
  11,926,237,506.23 → 11,572,972,056.23 = −353,265,450 (B)
  [[t|tables/renewal_impact_master.csv|OptionB+E_removed+renewal_feebate_no|annual_cost_pqp_only_sgd]]
  [[t|tables/renewal_impact_master.csv|OptionB+E_removed+renewal_feebate_yes|annual_cost_total_sgd,delta_vs_no_feebate_cell_sgd]];
  per vehicle 129,800.16 → 124,173.48 (A) [[t|tables/renewal_impact_master.csv|OptionA+E_removed+renewal_feebate_yes|per_vehicle_cost_pqp_only_sgd,per_vehicle_cost_total_sgd]] /
  129,743.03 → 125,899.93 (B) [[t|tables/renewal_impact_master.csv|OptionB+E_removed+renewal_feebate_yes|per_vehicle_cost_pqp_only_sgd,per_vehicle_cost_total_sgd]].
- Vintage cut points (sensitivity): A 23,052 / 26,379 [[t|data/processed/renewal_cohort_banded.csv|2017 / VINTAGE_2017pct / OptionA / 1|cutpoints_sgd]];
  B 16,570.25 / 23,052 / 26,379 / 35,155 [[t|data/processed/renewal_cohort_banded.csv|2017 / VINTAGE_2017pct / OptionB / 5|cutpoints_sgd]];
  re-banded registrations: band1 pre_A 25,458.33 [[t|data/processed/renewal_cohort_banded.csv|2017 / VINTAGE_2017pct / OptionA / 1|registrations]] /
  band3 pre_A 33,533.33 [[t|data/processed/renewal_cohort_banded.csv|2017 / VINTAGE_2017pct / OptionA / 3|registrations]].

## Unintended consequences

- Gaming zones (±5% OMV; mix 2025-01..2025-05): A p35 27,433.15–30,320.85, 23 models, 11.837% ≈ 5,418.3/yr, S$15,000 at stake,
  1,443.85 S$ move to cross [[t|tables/boundary_gaming_zones.csv|OptionA / 35|zone_lo_sgd,zone_hi_sgd,n_models_in_zone,zone_share_pct_covered_mix,est_registrations_annual_in_zone,quantum_at_stake_sgd,omv_adjustment_edge_sgd]];
  A p50 34,258.9–37,865.1, 23 models, 13.789% ≈ 6,312.1/yr, S$15,000 [[t|tables/boundary_gaming_zones.csv|OptionA / 50|zone_lo_sgd,zone_hi_sgd,n_models_in_zone,zone_share_pct_covered_mix,est_registrations_annual_in_zone,quantum_at_stake_sgd]];
  B p10 19,294.5–21,325.5, 7 models, 5.558% ≈ 2,544.0/yr, S$7,500 [[t|tables/boundary_gaming_zones.csv|OptionB / 10|zone_lo_sgd,zone_hi_sgd,n_models_in_zone,zone_share_pct_covered_mix,est_registrations_annual_in_zone,quantum_at_stake_sgd]];
  B p35 11.837% ≈ 5,418.5/yr [[t|tables/boundary_gaming_zones.csv|OptionB / 35|zone_share_pct_covered_mix,est_registrations_annual_in_zone]];
  B p50 13.789% ≈ 6,312.2/yr [[t|tables/boundary_gaming_zones.csv|OptionB / 50|zone_share_pct_covered_mix,est_registrations_annual_in_zone]];
  B p75 47,178.9–52,145.1, 19 models, 6.837% ≈ 3,129.9/yr, S$7,500 [[t|tables/boundary_gaming_zones.csv|OptionB / 75|zone_lo_sgd,zone_hi_sgd,n_models_in_zone,zone_share_pct_covered_mix,est_registrations_annual_in_zone,quantum_at_stake_sgd]].
- Distortion (mix 2025-01..2025-05): 139 families; A: 12 spanning, 28 affected, 12.90% of 217 models, max ΔS$15,000 (BYD :: SEAL 34,833–37,458)
  [[t|tables/classification_distortion.csv|OptionA / option_summary|n_families,n_spanning_families,members_affected,mis_banded_share_pct,max_within_family_quantum_diff_sgd,mis_banded_denominator]]
  [[t|tables/classification_distortion.csv|OptionA / BYD :: SEAL / spanning_family|omv_range_sgd]];
  B: 20 spanning, 55 affected, 25.35%, max ΔS$7,500 [[t|tables/classification_distortion.csv|OptionB / option_summary|n_families,n_spanning_families,members_affected,mis_banded_share_pct,max_within_family_quantum_diff_sgd,mis_banded_denominator]].
- Used-car: DIRECTIONAL only (no usable data; mix 2025-01..2025-05)
  [[t|tables/used_car_directional.csv|used_car_relative_attractiveness_upper_bands|statement]].

## PQP method validation (published 2002-02..2026-09 vs observed 2010-01..2026-10)

- Pooled A+B: max 0.83 / mean 0.428 S$ over 392 months, 2,352 bids; residual ∈ {0,1/6,…,5/6} S$ for 783/784 months
  (LTA rounds MA up to next whole dollar)
  [[t|tables/pqp_derivation.csv|POOLED A+B (merged-PQP inputs) — HEADLINE / method_validation|max_abs_diff_sgd,mean_abs_diff_sgd,n_months,n_bids_compared,rule_note]];
  A 0.83/0.41 [[t|tables/pqp_derivation.csv|category A / method_validation|max_abs_diff_sgd,mean_abs_diff_sgd]];
  B 0.83/0.446 (max 2026-09, logged LTA-side −0.83) [[t|tables/pqp_derivation.csv|category B / method_validation|max_abs_diff_sgd,mean_abs_diff_sgd,month_of_max]];
  C 0.83/0.438 [[t|tables/pqp_derivation.csv|category C / method_validation|max_abs_diff_sgd,mean_abs_diff_sgd]];
  D 3,205.5/16.776 — single outlier 2010-01 b2 SINGSTAT QP 852 vs LTA 20,090 (1,980 cells compared)
  [[t|tables/pqp_derivation.csv|category D / method_validation|max_abs_diff_sgd,mean_abs_diff_sgd,result]].

## Data & verification

- coe_bids 1,990 rows [[t|verification/provenance_log.csv|coe_bids|fetched_rows]] (window 2010-01..2026-10);
  registrations 51,669 rows [[t|verification/provenance_log.csv|registrations|fetched_rows]] (window 2016-01..2025-05,
  29,463 nulls excluded, 57.0%);
  published PQP 12,904 rows, A–D only (window 2002-02..2026-09)
  [[t|verification/provenance_log.csv|published_pqp|api_stated_total,fetched_rows]].
- Verification suite: 0 hard failures; documented exception = Option B band shares cross-foot 99.99% (2dp rounding)
  [[t|tables/banding_shares.csv|OptionB / 0-10th|cross_foot_sum_pct]]; negative controls INV-7/8a/8b/9/10 all PASS
  [[t|verification/invariant_checks.csv|INV-7|status]]; cross-foot base diff 0.0, E-shift diff −26.0 within 150.0
  [[t|verification/crossfoot_log.csv|base_OptionA / exact_band_counts|expected_sgd,actual_sgd,diff_sgd,tolerance_sgd]]
  [[t|verification/crossfoot_log.csv|e_shift_OptionB / batch_e_band_counts|expected_sgd,actual_sgd,diff_sgd,tolerance_sgd]].
