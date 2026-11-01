# Provenance — COE categorisation study (Batch B, Steps 3–4)

Run workspace: `/home/hteo/.hermes/kakis-runs/coe-category-study_20261022182314/`
Batch: B (Steps 3–4) — data fetch, provenance, anchor verification, baseline panel, published-PQP fetch.
Batch date: 2026-10-22 (all timestamps UTC).
Machine-readable provenance: `verification/provenance_log.csv` (per-resource fetch timestamp,
row counts, sha256). Per-request fetch log: `verification/fetch_requests.csv`.
Anchor-verification checks: `verification/constraint_report.csv` (stage `batch_b_step3`,
`batch_b_step4`).

## 1. Sources fetched

### 1.1 COE bidding results — `data/raw/coe_bids.csv`
- Source: data.gov.sg dataset **"COE Bidding Results / Prices" (LTA)**
  (https://data.gov.sg/datasets/d_69b3380ad7e51aff3a7dcc84eba52b8a/view),
  resource id `d_69b3380ad7e51aff3a7dcc84eba52b8a`.
- Fetched via `https://data.gov.sg/api/action/datastore_search` (action API only;
  versioned `api.data.gov.sg/v1` and `/v3` are dead — confirmed 403 in Batch A) with
  **offset pagination, limit=500/request** (plan-mandated; `start` param is ignored by
  the endpoint; large single fetches return HTTP 413).
- Rows: **1,990** (API-stated total 1,990 = fetched = plan expectation). Window:
  **2010-01 .. 2026-10**, both bidding exercises per month (199 months × 2 biddings ×
  5 categories = 1,990). Fields: `month, bidding_no, vehicle_class, quota,
  bids_success, bids_received, premium` (+ `_id` used only for uniqueness checks;
  all 1,990 `_id`s unique).
- sha256: `b8ff61472cb9e42fb8cc81c733a37ca6c9f90646f5d3dd36ed44cb4cbbe10df5`
- Fetch narrative: first run (started 2026-10-22T14:59Z) completed COE (4 requests,
  15:02Z) but was killed by a host timeout before registrations started;
  `src/fetch_data.py` is resumable, so the second run (15:11:05Z) verified COE
  completeness with one probe request and re-fetched nothing. Raw file left untouched.

### 1.2 Vehicle registrations — `data/raw/registrations.csv`
- Source: data.gov.sg dataset **"Vehicle Registrations"** (LTA),
  resource id `d_d3f4d708e1d0a37b4365414e2fad3a07`.
- Same action API + offset pagination, limit=500/request.
- Rows: **51,669** (API-stated total = fetched = plan expectation). **Frozen at
  2025-05** (last month = 2025-05, verified). Window 2016-01 .. 2025-05.
  Fields: `month, make, importer_type, fuel_type, vehicle_type, number`
  (+ `_id`, all unique).
- Fetch: 104 requests, 15:11:05Z–15:11:35Z (~30 s total; per-request log in
  `verification/fetch_requests.csv`: latency 15–667 ms, no retries).
- sha256: `6a700944937190b1d6d960a3d8c6d50a74b637e36d7670da0e568206e395aea8`
- **Null-`number` rows: 29,463 of 51,669 (57.0%)** — counted, logged, and to be
  **excluded consistently** by all downstream steps (valid rows: **22,206**).
  Interpretation (documented, verified against structure): `number` null = zero /
  unreported registrations for that (month, make, importer_type, fuel_type,
  vehicle_type) cell — the dataset lists zero-count cells explicitly as null.
  Monthly totals from the valid rows (e.g. 2025-01: 2,703; 2025-05: 4,455) are
  consistent with Singapore car-registration volumes.
  `importer_type` is null on 31,155 rows (makes not split by importer type;
  AMD = 13,830 rows, PI = 6,684 rows; no (month,make,fuel,vtype) group mixes typed
  and untyped rows).

### 1.3 CPI — NOT FETCHED (recorded per plan step 3c)
- Resource `d_bdaff844e3ef89d39fceb962ff8f0791` **not used**: it is optional
  context only, and no step of this study uses CPI. Recorded as
  `status="not used"` in `verification/provenance_log.csv`.

### 1.4 Published PQP — `data/processed/published_pqp.csv`
- **Primary source (full history):** SINGSTAT dataset on data.gov.sg,
  **"Motor Vehicle Quota, Quota Premium And Prevailing Quota Premium, Monthly"**
  (LTA data), page
  https://data.gov.sg/datasets/d_22094bf608253d36c0c63b52d852dd6e/view,
  resource id `d_22094bf608253d36c0c63b52d852dd6e`. Fetched 2026-10-22T15:31:37Z via
  the same action API (single request; wide store: 50 DataSeries × 296 month
  columns 2002Feb..2026Sep). Converted to long format:
  **12,904 rows** (month, category, bidding_no, measure, value + source series +
  OBSERVED label). Measures: Quota, Successful Bids, Bids Received, Quota Premium,
  **Prevailing Quota Premium**.
  - Per-category PQP series exist for **A, B, C, D only** (no published PQP for
    Category E — consistent with LTA: E is open category, PQP not applicable).
  - 6 "Total …" aggregate series excluded by design (per-category rows only).
  - sha256: `1341b1498bfe2b34d07ac5a69f00bcbb77aad61f6a7082e4b335ae110255b384`
- **Secondary source (current month, cross-check):** LTA OneMotoring live page
  https://onemotoring.lta.gov.sg/content/onemotoring/home/buying/coe-open-bidding.html
  — fetched and parsed successfully (2026-10-22T15:31Z). Results heading:
  **"Results for OCTOBER 2026 2nd Open Bidding Exercise"** (ended 21/10/2026 16:00).
  Published October 2026 values: A quota 1,191 / QP 132,004 / **PQP 129,883**;
  B 923 / 131,901 / **131,819**; C 308 / 92,200 / **91,814**; D 539 / 10,778 /
  **11,392**; E 270 / 135,790 / **0 (n/a)**.
  - QP cross-check vs raw `coe_bids` 2026-10 b2: **all 5 categories MATCH**.

## 2. Anchor verification results (all PASS — see constraint_report.csv)

| Check | Expected | Actual | Result |
|---|---|---|---|
| COE row count | API total = fetched = 1,990 | 1,990 = 1,990 | PASS |
| Registrations row count | API total = fetched = 51,669 | 51,669 = 51,669 | PASS |
| COE last month both biddings | 2026-10 with b1+b2 | 2026-10 with [1, 2] | PASS |
| Registrations last month | 2025-05 | 2025-05 | PASS |
| Null-`number` count | count + consistent exclusion | 29,463 null / 22,206 valid (logged) | PASS |
| Spot prices 2026-10 (8 values) | config.COE_SPOT_VALUES_2026_10 | all 8 exact matches | PASS |
| 2026 A>B inversion set | {2026-02 b2, 2026-04 b2, 2026-06 b2, 2026-10 b2} | identical set | PASS |
| PQP MA(3) convention | published PQP ≈ MA of last 3 months with bidding ending at month M | max abs diff $0.83 (see §4) | PASS |

## 3. Derived panels

- `data/processed/coe_panel_perbidding.csv` — **1,990 rows** (one per
  month × bidding × category, A–E, 2010-01..2026-10; 398 rows per category;
  reconciled 1:1 against raw). Derived fields: `a_minus_b_spread`
  (A premium − B premium, same bidding), `inversion` (1 if A > B in the same
  bidding), `monthly_mean_premium` (class mean across the month's biddings),
  monthly quota/bids totals, `n_biddings_in_month`. Every row stamped
  `label = "OBSERVED | data: coe_bids 2010-01..2026-10 …"` with
  `value_type=OBSERVED`, `scenario=""` — never conflated with scenario series.
- `data/processed/published_pqp.csv` — see §1.4 (OBSERVED-stamped).
- `tables/inversions_2026.csv` — the confirmed 2026 A>B inversion set (4 rows:
  2026-02 b2 spread +1,500; 2026-04 b2 +2,009; 2026-06 b2 +345; 2026-10 b2 +103),
  with prices, bid volumes, and OBSERVED label.

## 4. Discrepancies and data quirks (logged, none silently rewritten)

1. **COE thousands separators:** 109 raw `coe_bids` rows (2023-05..2026-10) carry
   comma-formatted numbers in `bids_success`/`bids_received` (e.g. "1,007").
   Raw file left untouched; commas stripped at transform time only
   (`src/verify_anchors.py`, `src/baseline_panel.py`).
2. **SINGSTAT single-cell error:** 2010-01 b2, Category D — SINGSTAT QP = 852 vs
   `coe_bids` (LTA bidding results) = 20,090. $852 is implausible for a 2010
   motorcycle COE; `coe_bids` treated as authoritative. Only diff among 1,980
   compared QP cells (SINGSTAT vs `coe_bids`, overlap 2010-01..2026-09).
3. **PQP moving-average convention (CONFIRMED):** LTA's published PQP(month M) =
   mean of **all** bidding clearing prices (both b1 and b2) in the last 3 months
   with bidding exercises, **ending at month M (M included)**, skipping months
   without bidding (e.g. 2020 Apr/May/Jun — consistent with LTA's own note on the
   COE Renewal page). Validation:
   - 2026-09 (SINGSTAT): A exact (128,715.00 vs 128,715); C (92,613.50→92,614)
     and D (11,160.67→11,161) match LTA rounding; **B off by −0.83**
     (131,615.17 vs 131,616 — minor unexplained LTA adjustment; logged).
   - 2026-10 (onemotoring live): A 129,882.50→129,883; B 131,818.83→131,819;
     C 91,813.50→91,814; D 11,391.83→11,392 — all match within ≤$0.50 rounding.
   The moving-average method used for scenario PQP derivation in later steps
   (config.PQP_WINDOW_MONTHS=3) is therefore externally validated, with a
   ≤$1 tolerance for LTA-side rounding.
4. **Registrations null `number` (29,463 rows):** see §1.2 — excluded
   consistently, count logged.
5. **First fetch attempt interrupted** by host timeout (420 s); `src/fetch_data.py`
   made resumable and re-run cleanly (no data re-fetched for COE; registrations
   fetched complete in one pass). No impact on data integrity (API-stated totals
   reconciled, `_id` uniqueness verified).

## 5. Environment

- python3.12, pandas 3.0.1, numpy, requests, lxml + bs4 (pd.read_html).
  Pre-verified in Batch A; confirmed working by this batch's runs.
- Endpoint used exclusively: `https://data.gov.sg/api/action/datastore_search`
  (per-request status logged; zero HTTP errors in the resumed run).

## 6. Scripts (this batch)

- `src/fetch_data.py` — bulk fetch (offset pagination ≤500, retries/backoff,
  per-request log, resumable, hard-fails on count mismatch / duplicate `_id`).
- `src/verify_anchors.py` — anchor checks + `tables/inversions_2026.csv` +
  constraint-report rows.
- `src/baseline_panel.py` — per-bidding OBSERVED panel with derived fields.
- `src/fetch_published_pqp.py` — published-PQP fetch (SINGSTAT + onemotoring
  cross-check + MA(3) validation + QP cross-checks + provenance upsert).

## 7. LTA 2025 OMV statistics verification (this batch, Step 5)

Target: an LTA 2025 annual vehicle statistics source with model-level
OMV detail, to anchor the Step 5 percentile cut points (paper s.2.15
bands by per-model OMV percentiles of 2025 registrations; the paper's
typical-models tables are "based on 2025 registrations").

**What was tried (2026-10-22/23):**
1. LTA statistics portal (lta.gov.sg transport statistics) and
   SINGSTAT tables (e.g. 51301 motor-vehicle series): aggregate
   registration counts by vehicle class only — NO model-level OMV
   distribution.
2. OneMotoring "Average OMV of New Cars Registered" page
   (https://onemotoring.lta.gov.sg/content/onemotoring/home/buying/
   upfront-vehicle-costs/open-market-value--omv-.html), yearly editions
   2002-2026: model-month AVERAGE OMV per make/model. This is the
   closest LTA-published 2025 model-level OMV dataset. The data is
   embedded server-side in hidden HTML inputs
   (`averageOmv_..._model-{M}_make-{K}_{month}_2025`, `modelValue_...`,
   `brandValue_...`); no separate public CSV/JSON endpoint was found.
   The `?year=2025` edition was fetched and archived.

**Found / coverage / detail:** 2025 edition = 50 makes, 222-359 models
per month, all 12 months of 2025, 3,366 model-month average-OMV values
(`S$X,XXX` format). It reports AVERAGE OMV per model-month, not the
registration-weighted distribution nor the "median OMV of past data"
LTA uses internally (s.2.15) — and only 142/217 of the current
catalog models match LTA-2025 model names (LTA names carry
fuel+cc suffixes, e.g. "...-- 1598cc").

**Archived (sha256):**
- `verification/lta_omv_2025_page.html` — raw 2025-edition page
  (sha256 3e69fe45b96d07e696e8e5d25e024afc52f6f0e475689d7c9375161777e21d87).
- `data/processed/lta_omv_2025_avg.csv` — parsed month/make/model/omv
  (3,366 rows; sha256
  c8a1e0d80a6a3e80d4716ba0f207b22f8acda52f9b6898a84531ab219327d331).

**Decision (recorded in methodology_notes.md s.7):** no downloadable
public 2025 model-level OMV distribution table exists in LTA's annual
statistics, so the Step 5 cut points use the **LABELLED FALLBACK** as
the primary variant — Jan-May 2025 make-level registration mix
(frozen window, 2025-05; data/raw/registrations.csv, valid
non-null-`number` rows only) x current Car Cost catalog (Aug-2026,
217 models) composition. The LTA 2025 edition is retained as
sensitivity variant S1; uniform weights as S2. Every mix-based number
carries the `2025-01..2025-05 (frozen at 2025-05)` data-window tag.
This is a first-class documented path per the plan, not a failure: the
fallback approximates the registration-weighted distribution LTA's
internal method implies more directly than a mean-OMV series, and the
gap to LTA's internal OMV base is measured by the typical-models
cross-validation (methodology_notes.md s.7;
tables/banding_mismatches.csv).

## 8. Demand-curve inputs (this batch, Step 6)

- `data/processed/coe_panel_perbidding.csv` (Batch B artifact;
  OBSERVED-stamped per-bidding panel, categories A-E, 199 months x 2
  biddings = 398 obs per category, 2010-01..2026-10;
  sha256 d576802d76f6fff648540d1f64a37b22a1a5147f95fb0ed8de6188dcf0e058cb).
  Source: data.gov.sg COE bidding results (resource
  d_69b3380ad7e51aff3a7dcc84eba52b8a), fetched and reconciled in Batch
  B — see earlier sections of this file.
- No new data fetches and no raw-data modifications in this batch;
  `data/raw/` untouched.
- Method precedent: prior coe-ev-rebate study at
  config.PRIOR_STUDY_DIR (/home/hteo/.hermes/kakis-runs/
  coe-rebate-bidding-analysis_20261012151812/ev_rebate_analysis/src/,
  READ-ONLY): Newey-West HAC SEs, levels-vs-diffs stationarity
  discipline, negative-control + graded-evidence patterns reused; its
  data NOT reused. Its EV-rebate headline was invalidated by a failed
  negative control — the motivating discipline for the NC1 lead
  control here, which flagged category C (lead p = 0.018 FAIL).

## 9. Step 11-13 data (this batch, Batch F)

### 9.1 LTA OneMotoring "Average OMV of New Cars Registered" 2017 edition
- URL: https://onemotoring.lta.gov.sg/content/onemotoring/home/buying/upfront-vehicle-costs/open-market-value--omv-.html?year=2017 (year-parameter pattern proven by Batch C for 2025; 2017 edition confirmed live and in-scope for this consultation — LTA retains ~10 years of editions).
- Fetched 2026-10-22T18:30:39Z via curl (no UA needed). 2,086,047 bytes; sha256 1e5214db59adfb566128e165af8e55a18f57f1683539ecce83809fb5cac1506e; archived to verification/lta_omv_2017_page.html.
- Parsed (hidden inputs, id pattern averageOmv_model-{k}_make-{n}_{m}_2017 + modelValue/brandValue rows): **5,178 model-month rows, 1,170 distinct models, months 1-12** -> data/processed/lta_omv_2017_avg.csv. This is the vintage-year model-level OMV source for renewal-cohort banding (Step 13, chain item 2 — SUCCESS, no fallback needed).

### 9.2 LTA annual vehicle statistics — 2017 COE class split and car volume
- URL: https://www.lta.gov.sg/content/web/lta/vehicle-and-driving-statistics/MVP02-1_New_Reg_by_COE.pdf (current annual series, 2015-2025 rows; fetched from the statistics listing at https://www.lta.gov.sg/content/web/lta/vehicle-and-driving-statistics.html).
- Fetched 2026-10-22T18:13:05Z. 138,181 bytes; sha256 263d60d3c9a00f7df8c62cdd4d6085036dc4ff0b51220ab3a6a59ad2af2cbfeb; 1 page (2015..2025 rows); archived to verification/MVP02-1_New_Reg_by_COE.pdf.
- Values used: 2017 A = 46,076; B = 45,699; C = 12,055; ETS = 7,706; D (motorcycles) = 9,640; Taxis = 2,770; Exempt = 1,842; Total = 125,788. **2017 car registrations (renewal cohort volume) = A + B = 91,775 per this table**; the 2017 slice of data/raw/registrations.csv (Batch B frozen resource, no re-fetch) yields 91,922 valid car registrations (56 makes); the 147-vehicle difference is carried as an explicit "E_residual" class (consistent with Category E car registrations being reported within the A/B/C/D/E structure of the LTA quota annex, s9.3). Column semantics verified against the LTA COE quota annex (s9.3): D = motorcycles; C = goods vehicles & buses; the table's "Total" = all car COE registrations (A+B+C+ETS+D+taxis+exempt).
- Discrepancy logged: the parent plan context stated data/raw/registrations.csv "contains NO 2017 data" — FALSE; the frozen file holds 2017-01..2017-12 (4,265 valid car rows). Implemented as specified (2017 slice used); discrepancy logged here with this citation.

### 9.3 LTA COE quota allocation annex, Apr 2010 - Jan 2026 (category semantics)
- URL: https://www.lta.gov.sg/content/dam/lta/documents/vehicle-and-driving-statistics/coe/COEQuotaAllocationRV_Apr2010-2025.pdf
- Fetched 2026-10-22T18:19:48Z. 5,990,346 bytes; sha256 d262df5573806aff8b61864c68d7c0b27ef34bcb2c22b30c82b64f67920457ff; 90 pages; archived to verification/COEQuotaAllocationRV_Apr2010-2025.pdf.
- Used for: (a) category-name semantics cross-check (Nov 2025 - Jan 2026 annex: C = Goods Vehicles & Buses, D = Motorcycles, E = Open (All except Motorcycles)); (b) 2017 annual quotas (A 10,233, B 10,326, C 5,250, D 17,250, E 6,163, Taxis 2,770, Exempt 3,900) as context only — not used in any Step 11-13 computation.

### 9.4 Historical LTA "Car Cost" PDF editions, 2017 — NOT AVAILABLE (chain item 1, attempted)
- Probed four URL patterns (LTA statistics listing + guessed DAM paths for the monthly "Cost for Cars Registered" / Car Cost series, 2017 editions): all 404. The LTA statistics page lists only the current monthly edition (M032, Aug 2026). Historical monthly Car Cost editions are not archived at the probed paths.
- Outcome: chain item 1 FAILED; chain item 2 (LTA OMV 2017 edition) SUCCEEDED and was used for model-level vintage OMVs; make/mix from the 2017 registrations slice (s9.2); official class split from the LTA annual statistics (s9.2). 2025-mix fallback NOT used (fallback_used = false).

### 9.5 D (motorcycle) revenue source and window (Step 11 incidence)
- Source: data/processed/coe_panel_perbidding.csv (Batch B, no re-fetch). Category D, latest 6 biddings, window 2026-08 b1 .. 2026-10 b2: avg quota 523.0/round, avg premium 11,391.83 -> 523.0 x 24 x 11,391.83 = 142,990,250.16 S$/yr (annualised, window stated in tables/fee_revenue_incidence.csv).
- C window: same 6-bidding window 2026-08 b1 .. 2026-10 b2, avg quota 311.17/round x 24 x 91,813.50 = 685,663,218 S$/yr (E cars-only quota); E-removal variant 8,298/yr (Batch E +11.11%, 10% E de-registration share fn5; exact 7,468.08/0.9 = 8,297.87 — Batch E's rounded 8,298 used; 0.11-vehicle/yr difference immaterial) x 91,813.50 = 761,868,423 S$/yr with C price HELD FLAT (Batch E: C/E price NOT DETECTABLE — conservative revenue bound).

### 9.6 Files written by this batch
- src/fee_revenue.py, src/demand_shift.py, src/renewal_cohort.py, src/renewal_impact.py
- data/processed/lta_omv_2017_avg.csv (5,178 rows), data/processed/renewal_cohort_banded.csv (52 rows)
- tables/fee_revenue_base.csv (4 rows), tables/fee_revenue_sensitivity.csv (8 rows), tables/fee_revenue_incidence.csv (8 rows)
- tables/demand_shift_by_band.csv (86 rows), tables/segment_shift.csv (6 rows)
- tables/renewal_impact_master.csv (8 rows), tables/renewal/*.csv (8 files, per-cell band x class)
- verification/crossfoot_log.csv (3 rows), verification/lta_omv_2017_page.html, verification/MVP02-1_New_Reg_by_COE.pdf, verification/COEQuotaAllocationRV_Apr2010-2025.pdf
- methodology_notes.md s.13-15 (appended), provenance.md s.9 (this section), batch_handoff_f.json

### 9.7 LTA OneMotoring "Average OMV of New Cars Registered" 2018 edition (2028-start sensitivity, added 2026-11-01)
- URL: https://onemotoring.lta.gov.sg/content/onemotoring/home/buying/upfront-vehicle-costs/open-market-value--omv-.html?year=2018 (same year-parameter pattern as s9.1; the 2018 edition is within LTA's ~10-year retention).
- Fetched 2026-11-01T02:40Z via curl (no UA needed) — AFTER the OneMotoring scheduled maintenance of 1 Nov 2026 00:00-08:00 SGT (pre-maintenance fetch attempts returned the maintenance shell page; the Wayback Machine holds no pre-2021 snapshot of the page, so the live fetch was the only source). 1,641,217 bytes; sha256 eae9c5409864d871d0ab1c292d89ee943138545c90c821ffedc0b357f73e3822; archived to verification/lta_omv_2018_page.html.
- Parsed (same hidden-input scheme, suffix _2018): **3,978 model-month rows, 875 distinct models, 44 makes, months 1-12** -> data/processed/lta_omv_2018_avg.csv (sha256 11300a28233be75558f6a08ac3594d0b34efe9b1cea8469cd062e1f696a90f29). One empty model-name input on the page is dropped (logged, not silently). Vintage-year model-level OMV source for the 2018 renewal cohort (Step 13b, SENSITIVITY).
- Edition sanity check: 426 models appear in both the 2017 and 2018 editions; median OMV 31,613 (2017) -> 32,198 (2018), 53% higher in 2018 — consistent with a genuine year-on-year edition.
- Official 2018 class split (s9.2 file, 2018 row): A = 39,877; B = 40,216; 2018 car registrations (A+B) = 80,093. The 2018 slice of data/raw/registrations.csv yields 80,281 valid car registrations (52 makes); the 188-vehicle difference is carried as E_residual (same treatment as 2017).
- Output: src/renewal_cohort_2028_sensitivity.py -> data/processed/renewal_cohort_banded_2028anchor.csv (52 rows; regime_start 2028-01-01 in every label). Headline quantum nets, PROPOSED_2025pct basis: Option A -377,561,400; Option B -274,526,775 (over 80,281 vehicles; -4,703/-3,420 per car). VINTAGE_2018pct basis: +135.2M / +143.4M. Method cross-check: the same computation applied to the 2017 cohort reproduces the shipped -517,215,600 / -353,265,450 exactly.

## 10. Batch H — Final provenance audit (Steps 16-18)

### 10.1 Registration freeze-date statement

data/raw/registrations.csv is FROZEN at 2025-05: the file covers
2016-01..2025-05 (51,669 rows; 29,463 null-`number` rows excluded
consistently across all batches = 57.0%; 22,206 valid rows). No
re-fetch was performed in any later batch; every mix-based number in
this study carries the explicit data-window tag "2025-01..2025-05
(frozen at 2025-05)" (banding/gaming/distortion mixes) or
"2017-01..2017-12 (OBSERVED)" (renewal cohort), and the freeze-label
audit (check i) fails any untagged mix-scale number. The LTA
2025 model-level OMV *distribution* is not public — the 2025 edition
reports model-month AVERAGE OMV only (s7) — which is why the main
banding uses the labelled Jan-May 2025 fallback mix and the LTA 2025
edition itself is carried as sensitivity S1.

### 10.2 LTA annual-statistics edition/coverage

- MVP02-1_New_Reg_by_COE.pdf (s9.2): current annual series, 2015..2025
  rows, fetched 2026-10-22T18:13:05Z, sha256
  263d60d3c9a00f7df8c62cdd4d6085036dc4ff0b51220ab3a6a59ad2af2cbfeb,
  archived at verification/MVP02-1_New_Reg_by_COE.pdf. Used for the
  2017 COE class split (A 46,076 / B 45,699 = 91,775 cars) in the
  renewal-cohort banding.
- LTA OneMotoring "Average OMV of New Cars Registered": 2025 edition
  (s7: 3,366 model-month average-OMV values; sha256
  c8a1e0d80a6a3e80d4716ba0f207b22f8acda52f9b6898a84531ab219327d331) and
  2017 edition (s9.1: 5,178 model-month rows, 1,170 distinct models,
  months 1-12; sha256 1e5214db59adfb566128e165af8e55a18f57f1683539ecce83809fb5cac1506e).
  LTA retains ~10 years of editions; the 2017 edition is live and was
  used directly for the derived vintage (no fallback).

### 10.3 Published-PQP fetch result

- SINGSTAT series d_22094bf608253d36c0c63b52d852dd6e ("COE premium,
  quarterly, PQP") fetched from the data.gov.sg API: 50 wide-format
  series rows converted to the long-format panel
  data/processed/published_pqp.csv = **12,904 rows, 2002-02..2026-09,
  categories A-D ONLY** (no published E PQP). sha256
  1341b1498bfe2b34d07ac5a69f00bcbb77aad61f6a7082e4b335ae110255b384.
- One cell error documented (s4.2): 2010-01 b2 Category D — SINGSTAT
  QP 852 vs LTA observed 20,090; LTA coe_bids treated as authoritative
  (sole outlier among 1,980 compared QP cells).

### 10.4 Historical Car Cost edition availability (derived vintage)

- 2025 (current) Car Cost catalog: local document extraction, 217
  models (88 Category-A class, 129 Category-B class) —
  data/processed/car_cost_aug2026.csv (M032, Aug 2026 edition).
- 2017 (derived vintage) Car Cost PDFs: NOT AVAILABLE — 4 probed URL
  patterns (LTA statistics listing + guessed DAM paths for the monthly
  "Cost for Cars Registered" / Car Cost series, 2017 editions) all
  returned 404; LTA lists only the current monthly edition at the
  probed paths (s9.4). Consequence: the 2017 renewal mix is built from
  the actual 2017 registrations slice (4,265 valid car rows) x LTA OMV
  2017 edition (s9.1) — a primary-source derivation, NOT the 2025
  fallback.

### 10.5 On-disk file audit (check j, final pass)

Every raw/derived file's sha256 and row count re-verified on disk by
`src/verify.py` check j (11 files: coe_bids 1,990 rows; registrations
51,669; published_pqp 12,904; coe_panel_perbidding 1,990;
lta_omv_2025_avg 3,366; lta_omv_2017_avg 5,178 (sha not previously
recorded — row count only); car_cost_aug2026 217 (row count only);
plus the 4 archived HTML/PDF evidence files with recorded shas).
All PASS. Fetch timestamps for the primary API resources are in
`verification/fetch_requests.csv` (Batch B); the 2025/2017 LTA pages,
the annual-statistics PDF and the quota annex carry per-fetch
timestamps and sha256 above (s7, s9.1-s9.3).

### 10.6 Files written by this batch (Batch H)

- src/verify.py (10-group suite), src/make_charts.py (8 figures)
- tables/verification_report.csv (all checks, expected/actual/pass-fail)
- verification/report_traceability.csv (per-number traceability map),
  verification/file_inventory.csv (deliverable inventory)
- charts/*.png (8 figures)
- REPORT.md, STATS_SUMMARY.md
- methodology_notes.md s.18 (appended), provenance.md s.10 (this
  section), batch_handoff_h.json
