# Methodology Notes — COE Categorisation Study

Run workspace: `/home/hteo/.hermes/kakis-runs/coe-category-study_20261022182314/`
Batch A (Steps 1–2) — written 2026-10-22. Subsequent batches append their
methodology sections (banding reconstruction, per-cell PQP derivation, etc.).

Labels: PROPOSED = parameter as stated by LTA in the consultation paper
(cited); COMPUTED/SCENARIO = derived in this study (scenario estimates with
data windows); OBSERVED = actual values from fetched sources or stated
facts.

## 1. Regime-start anchor (Step 2 decision)

**Decision: 2027-01 (default), documented reason.**

Scan of the consultation paper (all 20 pages, `docs/consult_paper_text.md`)
and both annexes (OCR, `docs/annex_ocr.md`) found **no stated
implementation or effective date** for the proposed regime. The only timing
statements in the paper are:

- §1.17 (p.6) and §4.3 (p.20): written comments due **2 November 2026**.
- §4.3 (p.20): "This review is **expected to be completed by the end of
  2026**."
- Annexes B/C: illustrative mechanics only; no dates.

Because the review completes "by the end of 2026" and any implementing
legislation/regulatory process plus annual banding publication (§2.16) must
follow, the earliest plausible start of the new regime is in 2027. The study
therefore adopts **2027-01** (first bidding exercise of 2027) as the
regime-start anchor, and carries `regime_start: 2027-01-01` in every
scenario label. This is the plan's documented default (consultation closes
2 Nov 2026; LTA findings 1H2027) — used here with the paper citation above
as the supporting evidence that no earlier date is stated.

If LTA later announces a different effective date, every scenario label and
the transition-year vintage must be re-stamped from
`config.REGIME_START_DATE` (single source of truth).

## 2. Transition-year vintage derivation (Step 2)

- Each COE is valid for **10 years** (paper §1.3, p.3 — OBSERVED).
- First-renewal cohort under the merged regime = registrations whose
  10-year initial term expires in the transition year (the year the regime
  starts).
- **Vintage = regime start year − 10 = 2027 − 10 = 2017** (about 2017).
- **Pre-regime cohort:** the 2016-vintage cohort renews in **2026**, i.e.
  before the regime starts. It is **entirely pre-regime and EXCLUDED from
  first-renewal-cycle analysis** — usable only as pre-regime context.
- These derivations are encoded in `src/config.py`
  (`transition_year_vintage()`, `TRANSITION_YEAR_VINTAGE`,
  `PRE_REGIME_RENEWAL_VINTAGE`) and stamped on every renewal-related
  output via `config.output_label()`.

## 3. Scope confirmation (Step 2)

Extracted text of `docs/consult_paper.pdf` was checked against the
user-stated scope (source of truth per plan):

| Scope item | Paper evidence | Status |
|---|---|---|
| Consultation window 8 Oct – 2 Nov 2026 | End date 2 Nov 2026 in §1.17/§4.3; start date 8 Oct 2026 not stated in paper (cover OCR checked; title only) — taken from LTA news release / user scope | CONFIRMED (end in paper; start per user scope) |
| A+B merge into one passenger-car category | §2.4 (p.7); §1.16(a); §4.2(a) | CONFIRMED |
| Value-based feebate on the merged category | §2.5, §2.8–2.9, fn2 (pp.7–8) | CONFIRMED |
| Category E review (remove vs cars-only) | §2.21–2.24 (p.13) | CONFIRMED |

All PROPOSED parameters used downstream are captured, with citations, in
`tables/consultation_parameters.csv` (29 parameters: 18 PROPOSED,
11 OBSERVED/stated facts). No parameter was re-invented; where the plan's
expectations and the paper differ (e.g. the 'typical models' tables live in
paper Tables 1/2, not in the annexes), the paper is implemented as written
and the discrepancy is noted (see also §5).

## 4. Document extraction method (Step 2)

- **Paper** (`docs/consult_paper.pdf`, 20pp): pymupdf text extraction →
  `docs/consult_paper_text.md` (32,930 chars). Page 1 is an image-based
  cover (OCR'd separately → `docs/consult_paper_cover_ocr.md`); page 17
  contains a figure (rendered to `docs/consult_paper_p17_figure.png`).
- **Annexes B & C** (image-only single pages): rendered at 300 DPI,
  OCR'd with easyocr (English, CPU) → `docs/annex_ocr.md`. Per-page
  confidence: Annex B mean 0.854 (32/50 words ≥0.8); Annex C mean 0.803
  (26/49 words ≥0.8). A 450 DPI re-OCR cross-check confirmed the captured
  content is complete (word counts stable; see
  `verification/ocr_resolution_check.csv`). Known misreads (e.g. `$` → `S`)
  are tabulated with corrected readings in `docs/annex_ocr.md`.
- **Car Cost Aug 2026** (`docs/car_cost_aug2026.pdf`, 8pp landscape):
  22-column bordered table extracted with pymupdf `find_tables()` →
  `data/processed/car_cost_aug2026.csv` (**217 rows** = models; SN
  1–217 sequential; row arithmetic validated: OMV+GST+ARF+VES+EEAI+RegnFee
  = Total Basic Cost; +COE = Total with COE; selling price − Total with
  COE = Difference). 88 rows Class A (COE $123,890), 129 rows Class B
  (COE $129,910, Aug 2026 1st bidding). Fuel codes per Note 9:
  P/H/R/B/C/E/Y/Q. Log: `verification/car_cost_extraction_log.csv`.

## 5. Discrepancies and constraints logged (Batch A)

Recorded in `verification/constraint_report.csv`:

1. **Prior-study path mis-print in bob_plan.md**: steps 1, 6, 13 and the
   assumptions cite `coe-rebate-bidding-analysis_20261014036210` (garbled,
   does not exist). The real path is
   `coe-rebate-bidding-analysis_20261012151812/ev_rebate_analysis` (verified
   accessible, read-only; 16 src modules, tables/, data/). `config.py`
   uses the real path; all downstream steps must use
   `config.PRIOR_STUDY_DIR`.
2. **Versioned data.gov.sg endpoints**: probe of
   `api.data.gov.sg/v1/action/datastore_search` returned HTTP 403 (denied)
   — unusable, consistent with the plan's "dead" note. Only
   `https://data.gov.sg/api/action/datastore_search` (action API) is used;
   probe returned HTTP 200 and reported 1,990 total rows on the COE
   resource (plan expected ~1,990 ✓).
3. **'Typical models' tables location**: plan text refers to the paper's
   'typical models' tables in the annex-OCR context; in the actual
   documents they are Tables 1/2 in the paper body (text layer), and the
   annexes contain only illustrative mechanics/method. Implemented as per
   the actual documents.
4. **Consultation start date**: 8 Oct 2026 is not stated in the paper
   itself (end date 2 Nov 2026 is); anchored to user-stated scope / LTA
   news release, per plan's "user request is the source of truth".

No access was blocked; all 17 environment checks passed (0 fail).

## 6. To be added by later batches

- ~~Step 5: banding reconstruction~~ — DONE this batch (§7).
- ~~Step 6: demand-curve fitting~~ — DONE this batch (§8).
- Step 9: per-cell PQP derivation (3-month MA; validation vs published
  PQP or internal consistency).
- Step 13: renewal-cohort banding at vintage 2017 (historical Car Cost
  availability / fallback chain).
- Step 18: final consistency pass and provenance.

## 7. Step 5 — Feebate banding reconstruction (this batch)

Implemented in `src/banding.py` (runs clean, exit 0). Outputs:
`tables/banding_cutpoints.csv`, `banding_models_optionA.csv`,
`banding_models_optionB.csv`, `banding_shares.csv`,
`banding_mismatches.csv`.

**OMV distribution source (decision + why).** Primary target = LTA 2025
annual vehicle statistics with model-level OMV detail. Verified
2026-10-22/23 (see `provenance.md` §7): the LTA statistics pages do not
publish a public 2025 model-level OMV distribution as a downloadable
table (SINGSTAT table 51301 etc. are aggregate). The OneMotoring
"Average OMV of New Cars Registered" page (yearly editions 2002-2026,
https://onemotoring.lta.gov.sg/content/onemotoring/home/buying/
upfront-vehicle-costs/open-market-value--omv-.html?year=2025) is the
closest LTA-published 2025 OMV dataset: model-month average OMV, 50
makes, 3,366 model-month values, archived at
`verification/lta_omv_2025_page.html` + parsed to
`data/processed/lta_omv_2025_avg.csv`. **Decision: the LABELLED
FALLBACK is the primary variant for the cut points** — Jan-May 2025
make-level registration mix (frozen window, 2025-05) x current Car Cost
catalog (Aug-2026) model composition, because (i) LTA's actual banding
uses per-model "median OMV of past data" (§2.15) weighted by
registrations, which the fallback approximates more directly than a
mean-OMV series; (ii) only 142/217 catalog models match LTA-2025 names,
and the LTA page reports AVERAGES not the registration-weighted
distribution the paper implies. The LTA-2025 edition is retained as
**sensitivity variant S1** (142/217 matched, catalog fallback OMV for
the rest), and uniform model weights as **variant S2**. Every mix-based
number is tagged `2025-01..2025-05 (frozen at 2025-05)`.

**Method.** Cut points = weighted percentiles of model OMV where weight
= model's estimated share of Jan-May 2025 registrations (make-level mix
allocated to catalog models; models absent from the mix get weight 0 —
they stay banded, contribute no distribution mass). Coverage: 98.73% of
Jan-May 2025 car registrations are representable by catalog models.
Band convention: **upper-inclusive** `(c_{k-1}, c_k]`, top band
`(c_last, infinity)` — chosen to match the paper's band labels
("0-35th", "35-50th", ">50th") and its own placement of BYD Sealion 7
Dynamic (OMV exactly at p50) in the "35-50th" band. All 217 catalog
models banded under both options; band shares = registration-weighted
share of the distribution in each band (cross-foot: Option A = 100.00%,
Option B = 99.99%, within rounding).

**Cut points (main variant).** Option A: p35 = 28,877; p50 = 36,062.
Option B: p10 = 20,310; p35 = 28,877; p50 = 36,062; p75 = 49,662.
S1 (LTA-2025 OMV): A 29,800/36,283; B 21,578/29,800/36,283/49,662.
S2 (uniform): A 30,629/37,301; B 21,776/30,629/37,301/50,795.

**Approximation statement (also stamped on every table row).** This is a
RECONSTRUCTION approximating LTA's eventual banding, not LTA's table:
LTA publishes the actual banding annually (§2.16, PROPOSED) using
internal per-model "median OMV of past data" (§2.15); the percentiles
(35/50; 10/35/50/75) and quantums (-15000/0/+15000;
-15000/-7500/0/+7500/+15000) are PROPOSED consultation parameters
(§2.15-2.18); the distribution base is the labelled Jan-May 2025 mix x
catalog composition.

**Cross-validation vs paper Tables 1/2 typical models (pp.11-12).**
Agreement: **Option A = 24/30 (80.0%)**, **Option B = 18/30 (60.0%)**.
Every mismatch is enumerated in `tables/banding_mismatches.csv`
(6 + 12 MISMATCH rows), concentrated at band boundaries (e.g. Option A:
Corolla Altis 22,200 / Civic 1.5T 27,067 / A3 24,058 in "35-50th" in
the paper but band 1 here; Q3 30,629 / BMW 216 33,959 / MB A180 35,444
in ">50th" in the paper but band 2 here). In addition, the paper's own
indicative table is **internally inconsistent** under any public OMV
reading: the implied boundary intervals are EMPTY for all five cuts
checked (Option A p35 and p50; Option B p10, p35, p50, p75) — e.g. the
paper simultaneously implies p35 >= 28,083 (Noah banded "0-35th") and
p35 < 22,200 (Corolla Altis banded "35-50th"). Verdict rows
`PAPER_TABLE_INTERNALLY_INCONSISTENT` recorded. Most plausible
explanation: LTA banded the typical models with internal per-model
"median OMV of past data" (§2.15), not the 2025/2026 public OMV values,
and the table is non-exhaustive/indicative only (§2.18c). Our
reconstruction is therefore a faithful approximation of the METHOD, and
the mismatches are an honest measure of the gap to LTA's internal
OMV base.

## 8. Step 6 — Per-category price-bidding-response curves (this batch)

Implemented in `src/demand_curves.py` (runs clean, exit 0). Outputs:
`tables/demand_curves.csv` (120 rows), `tables/evidence_grading.csv`
(13 graded claims + rubric block).

**Specs** (per-bidding series 2010-01..2026-10, N=398 per category,
sequentially ordered by month then bidding_no; all SEs Newey-West HAC,
maxlags = 4 per-bidding obs ~= 2 calendar months, matching the
prior study's Newey-West lag-3 on monthly data):
- M1 linear levels: premium ~ bids_received + quota + month-trend.
- M2 log-log: ln premium ~ ln bids + ln quota + trend (coef =
  elasticity).
- M3 first differences (PRIMARY for scenario use): dpremium ~ d(bids) +
  d(quota). M3 is primary because the levels specs are
  trend-contaminated: A/B/C/E show DW ~ 0.04-0.15 and Breusch-Godfrey
  p < 0.001 under a linear trend (the secular COE price rise, ~7x
  2010..2026, is not absorbed), so levels coefficients are
  common-trend confounded. M3 removes the trend and isolates the
  within-auction demand-price response.

**Results (M3, primary).**
- A: +4.99 S$/bid, p = 1.5e-15, HAC CI [+3.76, +6.21], R2 = 0.148,
  DW = 1.94, BG p = 0.39 -> **MEDIUM**.
- B: +8.24 S$/bid, p = 0.0003, CI [+3.74, +12.75], DW = 2.19, BG p =
  0.003 -> **LOW** (residual autocorrelation beyond the NW window on
  M3; coefficient nonetheless stable across NW maxlags 2/4/6/12).
- C: -0.22 S$/bid, p = 0.958 -> **NOT DETECTABLE** (no within-auction
  price sensitivity to bid volume; consistent with C's low, flat
  premium history).
- E: -4.06 S$/bid, p = 0.494 -> **NOT DETECTABLE**.
Levels (M1) and log-log (M2) coefficients are reported for reference
with explicit trend-contamination caveats; M1 b1 is not significant for
A/B/E (p = 0.13/0.26/0.36), and M2 e1 is significant-negative for C
(-0.502, p = 0.001) — graded NOT DETECTABLE (reversed sign).

**Negative controls.**
- NC1 LEAD (per category, levels spec): refit M1 with the NEXT
  bidding round's demand (t+1; clearing price of round t is set at
  auction t, so round t+1 bids cannot move it). A p = 0.417 PASS,
  B p = 0.972 PASS, E p = 0.256 PASS, D p = 0.255 PASS; **C p = 0.018
  FAIL** — C's clearing price co-moves with NEXT-round bids (its
  secular price decline vs rising bid volumes), i.e. any C
  contemporaneous association is a common-trend artifact -> C headline
  invalid (matches the prior study's failure-mode discipline).
- NC2 CATEGORY-D REFERENCE (mechanism check): D (large goods) is the
  cleanest COE market in the panel (no car cost-regime confounders).
  It shows a clean, significant positive bidding->price response (M1
  +5.58 S$/bid, p < 1e-6, DW = 1.08; M3 +2.17, p = 0.037) — the
  mechanism is VALIDATED, and the A/B/C/E level-spec weakness is a
  specification issue (trend), not a mechanism artifact. Standardised
  response per +10% bids (M3, % of mean premium): A +1.06, B +1.21,
  C -0.02, E -0.25, D(ref) +2.14.
- NC3 residual diagnostics (DW/LB/BG) on M1 and M3 per category: as
  above; B's M3 BG p = 0.003 is the only live concern.
- NC4 subsample stability (M3, pre/post 2018): signs stable where the
  coefficient is significant.
- NW-window sensitivity (probe, NW maxlags 2/4/6/12): M3 coefficients
  and p-values unchanged in rank/sign (A always p < 1e-4; B always
  p < 0.001; C/E never significant).

**Evidence grades (scenario elasticities ONLY — no structural causal
claim; simultaneity caveat: bidding demand responds to the expected
COE price).**
- A within-auction response (M3): **MEDIUM** — usable as the
  scenario elasticity for Steps 7-8 (approx +5 S$ per additional
  bid on the clearing price, holding quota fixed).
- B (M3): **LOW** — usable with caution (approx +8 S$/bid).
- C, E (M3): **NOT DETECTABLE** — downstream steps should treat C/E
  clearing prices as quota/flat-driven, not as bidding-response
  curves.
- D: control row only (PASS, mechanism validated), not a scenario
  claim.
Full rubric + per-claim reasons in `tables/evidence_grading.csv`.

**Method precedent.** Reused from the prior coe-ev-rebate study
(config.PRIOR_STUDY_DIR, READ-ONLY): Newey-West HAC SEs,
levels-vs-diffs stationarity discipline, lead-style negative control,
mechanism reference category, graded-evidence table with rubric block.
That study's EV-rebate headline was INVALIDATED by a failed negative
control (common 2022-01 shock in "clean" categories C/D/E); the NC1
lead control here is the direct analogue, and it caught category C
(lead FAIL) — exactly the failure mode the discipline exists to catch.

## 9. Step 7 — Merged A+B clearing price, no feebate (this batch)

**Curve-spec dependency (stated on every output).** The merged price is
built ONLY from the Step 6 primary spec M3 (first differences, NW-HAC
maxlags=4, N=397 per category, 2010-01..2026-10): catA alpha = +4.9885
S$/bid (CI [+3.76, +6.21], p=1.5e-15, grade **MEDIUM**) and catB alpha =
+8.2448 S$/bid (CI [+3.74, +12.75], p=0.0003, grade **LOW**; NC3 BG
p=0.003 concern). C and E are **NOT DETECTABLE** in Step 6 and are NOT
folded into the merged-car demand (they belong to the later C/E scenario
batch; their clearing prices are quota/flat-driven). All merged-price
series are SCENARIO-labeled; the dependency on the curve grades is stated
in the `curve_grade_dependency` column of every table.

**Transformation from the M3 spec (exact).** M3 identifies slopes only
(levels are non-stationary; NC3 flagged trend contamination), so the
level-consistent demand representation is the LOCAL linearization of the
M3 surface anchored at each round's own observed clearing point
(P_c,t, Q_c,t):

    N_c(P) = Q_c,t - (P - P_c,t)/alpha_c          (bids clearing at COE price P)

- alpha_c = dP/dB|Q is the marginal bid spacing (S$/bid) at the margin,
  so the demand slope is dN/dP = -1/alpha_c.
- The anchor quantity is the observed CLEARED quantity Q_c,t (not total
  bids_received): in the observed auction exactly Q_c,t units clear at
  P_c,t by definition of the marginal bid; losing bids sit below the
  margin and are not demand at the margin. The observed auction is
  reproduced exactly (N_c(P_c,t) = Q_c,t) — no tuning.
- beta_c (dP/dQ|B) does NOT enter the price solve: the clearing condition
  N_A(P_M) + N_B(P_M) = Q_M already maps quota -> price through the
  demand curves, and with Q_M = Q_A + Q_B the quota-response terms cancel
  identically. beta_c is reported for context only (it would matter for
  exogenous merged-quota changes in later steps).

**Merged clearing price (closed form).** With merged demand
N_M(P) = N_A(P) + N_B(P) and merged slope kappa_M = 1/alpha_A + 1/alpha_B
= 0.321748 bids/S$:

    P_M = (P_A/alpha_A + P_B/alpha_B + (Q_A + Q_B - Q_M)) / kappa_M

For the back-solved history (Q_M = Q_A,t + Q_B,t per round) this reduces
to P_M,t = (P_A,t/alpha_A + P_B,t/alpha_B)/kappa_M — a convex
combination of the two observed prices with weights
w_A = (1/alpha_A)/kappa_M = 0.623, w_B = 0.377 (the flatter category,
A, pulls harder). Consequence: the back-solved merged price sits between
the two observed category prices in every round (INV-7; 0 violations in
398 rounds), so the representation cannot diverge from observed A/B
prices by construction — the latest back-solved value (2026-10 b2:
131,965.2) sits inside the most recent A/B range.

**Static bounds.** min/max of the OBSERVED A and B per-bidding premiums
over the recent window 2025-01..2026-10 (22 months, 44 biddings per
category): [85,000; 141,000] (min = A 2025-02 b1; max = B 2025-10 b1).
Window choice: the last full year before the consultation window, i.e.
the "current" price regime against which the no-response scenario is
reported.

**Forward-scenario quota assumption (explicit).** Merged quota held at
the most recent 6 biddings' (rounds') A+B average:
mean(quota_A + quota_B) over 2026-08 b1 .. 2026-10 b2 = **2137.5**.
("Bidding" read as a bidding exercise/round; the 3-round interpretation
of "6 category-observations" would give 2137.0 — immaterial, 0.5 units.)
Demand is anchored at the LAST observed round (2026-10 b2: P_A=132,004,
P_B=131,901, Q_A=1,191, Q_B=923) with bidder pools held at that level
(no demand growth assumed). Horizon: 2027-01 b1 .. 2027-12 b2 (24
rounds, 2 biddings/month), regime start per config (2027-01-01). Forward
rows are clearly separated (segment = forward_scenario; obs_* columns
empty) from the back-solved history.

**Uncertainty band (p10-p90).** Monte Carlo, 10,000 draws, seed
20261023: alpha_A ~ U([3.7627, 6.2144]), alpha_B ~ U([3.7405, 12.7490])
(the 80% NW-HAC CIs from tables/demand_curves.csv), parameters drawn
independently (the joint distribution is not identified; this is a
bounding-style SCENARIO band, not a statistical CI). Point estimate uses
the exact M3 point coefficients. The band is narrow where the A-B spread
is small (P_M ~= common level regardless of weights) and widest where
the spread is large; B's wide CI dominates the band, consistent with its
LOW grade.

**Quota/bid reallocation (tables/quota_reallocation.csv).** Under the
single price / single PQP regime (paper s2.19), the merged quota splits
across the former A/B bidder pools at the common price:
quota_A_at_P = Q_A - (P_M - P_A)/alpha_A, quota_B_at_P analogously
(sum = merged quota exactly; delta_A + delta_B = 0 on back-solved
rounds, = +23.5 on forward rounds = the quota gap vs the anchor round).
Bid surplus per pool = observed bids_received minus allocated quota.
Single PQP = 3-month trailing moving average of the scenario merged
price series (config.PQP_WINDOW_MONTHS = 3; paper fn3 p.12), monthly
value = mean of the 2 bidding rounds; expanding window for the first two
months. All SCENARIO-labeled (OBSERVED inputs carry obs_* prefixes).

**Data note.** The data.gov.sg coe_bids extract covers 199 of the 202
calendar months 2010-01..2026-10 (2020-04/05/06 absent) — identical to
the Step 6 sample (398 obs per category), so the merged path is
consistent with the curve-estimation sample.

## 10. Step 8 — Feebate-adjusted merged price paths, iterated (this batch)

**Mechanics.** The PROPOSED feebate (paper s2.18(a)/(b), PROPOSED
quantums) adds band quantum f_k to the prevailing COE price, so band-k
bidders face effective price P + f_k and require the COE price to be f_k
lower: band-k demand shifts down by f_k. With registration-weighted band
shares s_k (Step 5, exact annualised registration counts, frozen
2025-01..2025-05 mix, 98.73% coverage) and linear merged demand of slope
kappa_M, the feebate-adjusted merged demand is

    N_feb(P) = N(P + Fbar),   Fbar = sum_k s_k f_k,
    N_feb(P) = N(P) - Fbar*kappa_M      (linear: shift is price-independent)

i.e. the plan's "band share x quantum (registration-weighted)" demand
shift. Registration-weighted average quantum (exact counts):
**Option A Fbar = +2,091.97 S$** (2dp-share cross-check: +2,091.00),
**Option B Fbar = +2,149.11 S$** (2dp: +2,149.50). Both options have a
POSITIVE average quantum because the registration mix skews to the
upper-OMV bands, so the feebate lowers the clearing COE price (demand
shifts in, the same quota clears at a lower price).

**Iteration (fixed point).** Starting from the Step 7 no-fee path, per
option, per round:

    P^(i+1) = P^(i) - [ Q_M - N_feb(P^(i)) ] / kappa_M

tolerances: price tol 0.01 S$, bid tol 1e-6 bids, max 100 iterations.
For linear demand the fixed point P_feb = P_nofee - Fbar is reached in
one update (magnitude Fbar) plus one verification pass — both options
converge with final residual 3.6e-12 bids (logged per option in
tables/fee_price_iteration_log.csv with iteration counts). The loop is
kept generic so non-linear demand variants need no code change.

**Zero-elasticity limit.** kappa_M -> 0 (vertical demand, zero response
of bid count to price) makes the feebate-induced demand shift
Fbar*kappa_M -> 0, so there is no price response and the with-fee price
equals the no-fee price (implemented as the kappa=0 branch; INV-8b).
Note: at kappa=0 the market is indeterminate (the forward segment's
23.5-bid quota gap cannot be cleared at any price); the invariant
concerns the feebate's PRICE effect, which is zero.

**Invariant / negative-control results (verification/invariant_checks.csv).**
- INV-8a ZERO-QUANTUM: Fbar := 0 -> demand shift 0 bids, revenue
  sum_k s_k*0*N_k = 0 S$/yr, with-fee price = no-fee price (max diff
  2.9e-11 S$ = float noise) — PASS.
- INV-8b ZERO-ELASTICITY: with-fee price = no-fee price (max diff
  0.0 S$) — PASS.
- (Step 7) INV-7 no-response merged price within static bounds — PASS.

**Results.** With-fee latest back-solved (2026-10 b2): Option A
129,873.2, Option B 129,816.1 (no-fee 131,965.2). Forward 2027-12 b2:
Option A 129,800.2, Option B 129,743.0 (no-fee 131,892.1); all forward
with-fee values within the static bounds [85,000; 141,000]. Expected
annualised feebate revenue (COMPUTED under PROPOSED quantums, frozen
2025 mix): Option A 95,760,000 S$/yr; Option B 98,377,500 S$/yr
(revenue = sum_k f_k N_k). p10-p90 bands are exact translations of the
Step 7 bands (constant Fbar shift).

## 11. Step 10 — Category E/C scenarios (this batch)

**Options (PROPOSED, consult paper s2.21–s2.24, pp.13–14).**
(a) `E_removed` — Category E removed entirely; urgent buyers "would need
to wait for the next COE bidding exercise to do so" (s2.23).
(b) `E_cars_only` — Category E retained for car registration only —
"car buyers with urgent needs will continue to have options, without
impacting Category C COE supply" (s2.23).

**E/C are NOT bidding-response curves — shifts are quota/demand
additions.** Step 6 evidence grading (tables/evidence_grading.csv):
catE M3 b1 p=0.494 → NOT DETECTABLE; catC M3 b1 p=0.958 with NC1 lead
p=0.018 FAIL (contemporaneous coefficient is a common-trend artifact) →
NOT DETECTABLE. The E/C scenario is therefore modeled as quota/demand
additions to the merged market and as mechanism-derived quota changes —
never via an E or C bidding-response slope.

**Assumptions (each stated; full basis in code comments of
src/ec_scenarios.py):**
1. **E-to-car shift share (ASSUMPTION).** Base case **100%** of E
   demand re-enters the next car bidding exercise; sensitivity range
   **50–100%**. Rationale: the paper's own removal mechanics say urgent
   buyers *wait for the next bidding* — the demand moves, it is not
   destroyed; no observed E drop-out rate exists, so 100% is the
   neutral "demand preserved" base and 50% a documented lower bound
   allowing for churn/abandonment.
2. **E-shifted demand (bids) for the price solve** = observed E
   per-bidding bids_received, most recent 6 rounds (2026-08 b1 ..
   2026-10 b2) average × share = **459.5 bids/round** (base). Applied
   to the merged demand surface through the Step 6 closed form
   dP = dN / kappa_M (kappa_M = 0.321748 bids/S$; same linearity as
   Batch D's P_feb = P_nofee − Fbar): base pulse **+1,428.14 S$**,
   sensitivity 50% → +714.07 S$.
3. **E-shifted registrations (feebate base)** = observed E per-bidding
   cleared quota, last-6 average × share = **266.67/round → 6,400/yr**
   (base). These enter the merged-car feebate base banded by OMV with
   the **Category-B-skewed composition** (see 4). This is a delta to
   the feebate base for Batch F revenue; Batch D's Fbar is kept
   unaltered in this step's price paths (documented).
4. **OMV banding of E-shifted registrations (ASSUMPTION, cited).**
   Paper s2.22: "In recent years, Category E COEs have been mostly used
   for Category B cars." Composition = the `coe_class == 'B'` subset of
   tables/banding_models_optionB.csv (129 of 217 catalog models),
   2025-01..2025-05 registration weights renormalized (frozen-mix tag on
   every row). Option B band shares: 0–10th 5.27%, 10–35th 15.54%,
   35–50th 12.83%, 50–75th 26.17%, >75th 40.19% (high-value dominant,
   per the paper's E usage pattern). Annual E-shift registrations per
   band: 337 / 994 / 821 / 1,675 / 2,572 (sum 6,400); net quantum
   revenue delta at PROPOSED quantums **+38,624,201 S$/yr**
   (tables/e_shift_feebate_base_delta.csv — Batch F input).
5. **C quota under removal = ×(1/0.9) = +11.11% (MECHANISM-DERIVED).**
   Paper fn5 p.13: "Since May 2017, Category E receives 10% of the
   deregistrations from Categories A, B and C." E thus took 10% of C's
   own deregistration flow, leaving C with 90%; on removal that 10%
   returns to C, so C quota = 100% of its flow = old C quota / 0.9.
   Under cars-only C is SHIELDED (0% change, s2.23(b) "without
   impacting Category C COE supply"). Forward levels (last-6 observed
   averages, Batch D convention): cars-only 311.17/round (≈7,468/yr) →
   removal 345.74/round (≈8,298/yr).
6. **C price.** Forward C price path is flat at the last-6 average
   observed C premium (91,813.5/round) under BOTH options. Under
   removal the +11.11% quota shock implies downward price pressure
   that is **NOT quantified** — catC bidding-response NOT DETECTABLE
   (NC1 lead p=0.018 FAIL); holding the no-shock level is the
   conservative upper bound, stated on every row.
7. **Transient treatment (ASSUMPTION): ONE-ROUND PULSE at 2027-01 b1.**
   The "next COE bidding exercise" after the regime starts (s2.23)
   absorbs the full E-demand shift; from 2027-01 b2 the merged path
   reverts exactly to the option-level with-fee path. E demand is
   episodic urgent-demand; a permanent flow would contradict Batch D's
   static bidder-pool forward design (flat 131,892.1 no-fee) and the
   static-bounds logic, and would overstate a one-time transition
   effect.
8. **E premium under cars-only (ASSUMPTION).** E restricted to the
   merged car category makes an E COE functionally equivalent to a
   merged-car COE → the E premium (E price above merged-car price)
   COLLAPSES TOWARD 0: linear decay to 0 over the first 6 forward
   rounds (3 months ≈ E TCOE validity period, paper fn4 p.13); base
   level 3,777.33 S$ = mean(E premium − max(A,B premium)) over the
   last 6 observed rounds. From 2027-04 b1 the E price equals the
   option-level with-fee merged price exactly. E quota under
   cars-only: held at the last-6 observed average 266.67/round
   (mechanism unchanged).

**Path summaries (forward window 2027-01..2027-12, 24 rounds).**
- Merged car — removal: Batch D option-level with-fee path
  (A 129,800.16 flat / B 129,743.03 flat) + one-round pulse +1,428.14 S$
  at 2027-01 b1 (→ 131,228.30 A / 131,171.16 B); all other rounds
  unadjusted. Merged car — cars-only: the option-level with-fee path
  UNADJUSTED (stated explicitly; no car-demand shift).
- C: quota as above; price flat 91,813.5 both options (removal carries
  the +11.11% quota with the unquantified-pressure caveat).
- E — removal: quota 0, no price (category removed from regime start).
  E — cars-only: quota 266.67/round; price = merged with-fee price +
  decaying premium (3,777.33 → 0 over 6 rounds), i.e. 133,577.50 at
  2027-01 b1 (Option A) converging to 129,800.16 from 2027-04 b1.

INV-9 PASS (verification/invariant_checks.csv): C removal/cars-only
quota ratio exactly 1/0.9 in all 24 rounds; exactly one pulsed round
(2027-01 b1); E premium terminal value exactly 0.

## 12. Step 9 — Staged per-cell PQP (this batch)

**(i) Method validation vs published PQP.** Convention (paper fn3
p.12: "PQP is the moving average of COE prices in the last three
months"; Batch B's verified MA-3 convention): PQP(M) = mean of ALL b1+b2
clearing premiums in the last 3 months WITH bidding, ending at M (M
included; months without bidding skipped). Recomputed from the
OBSERVED per-bidding premiums and matched against the published
per-category PQP — SINGSTAT "Motor Vehicle Quota, Quota Premium And
Prevailing Quota Premium, Monthly (LTA data)", data.gov.sg dataset
d_22094bf608253d36c0c63b52d852dd6e (2002-02..2026-09; fetched,
data/processed/published_pqp.csv; cross-checked live at LTA OneMotoring
2026-10 in Batch B). Validation window 2010-03..2026-09 (panel
overlap; 2020-04/05/06 absent from coe_bids): 196 months per category,
784 category-months.

**Result: PASS (tolerance ≤ 1.0 S$ per Batch B).** Pooled A+B
(headline, the categories feeding the merged PQP): **max abs diff
0.83 S$** (52 months tied), **mean abs diff 0.428 S$**. Per category:
A 0.83 / 0.410; B 0.83 / 0.446 (2026-09 B −0.83 is the known LTA-side
deviation logged in Batch B); C 0.83 / 0.438; D 3,205.50 / 16.776 — the
single D outlier at 2010-03 is the known SINGSTAT single-cell error
2010-01 b2 D QP (852 in SINGSTAT vs 20,090 authoritative in coe_bids;
only diff among 1,980 compared QP cells, Batch B log) entering the
2010-03 MA window; excluding it, D max is 0.83 S$.

**Residual signature (exact mechanism identified).** All 784
category-month residuals (published − MA3) lie in {0, 1/6, 2/6, 3/6,
4/6, 5/6} S$ (783 of 784; the one exception is the D 2010-03 outlier
above): the published PQP equals the SAME 3-month MA of the SAME
observed premiums, rounded UP to the next whole S$ — never negative,
never above 1 S$. The method is thus validated beyond the tolerance,
with the exact LTA-side rounding identified.

**(ii) Per-E-option merged-car price paths (4 distinct).**
`OptionA+E_removed` / `OptionB+E_removed`: Batch D option-level
with-fee path + the Step 10 E-shift pulse (+1,428.14 S$ at 2027-01 b1
only; pulse value cross-verified against an independent recompute from
the raw panel: E last-6 bids 459.5 × 100% / kappa_M 0.321748, exact).
`OptionA+E_cars_only` / `OptionB+E_cars_only`: the unadjusted
option-level with-fee path (no car-demand shift, stated explicitly).
The 4 paths are pairwise distinct (verified programmatically).

**(iii) Per-cell PQP — 8 master-matrix cells.** cell = {Option A, B} ×
{E removed, cars-only} × {renewal feebate no, yes}. Each cell's PQP =
MA-3 of THAT CELL'S OWN merged-car price path (422 rounds: 398
back-solved + 24 forward; output months 2010-03..2027-12, 209 months
with bidding). No option-level PQP is reused across cells with
different E options: the removal cell's PQP differs from its cars-only
counterpart exactly in the months whose window contains the pulsed
round — 2027-01, 2027-02, 2027-03 (+238.02 S$ each = 1,428.14/6;
2027-01's window is {2026-09, 2026-10, 2027-01}, 6 bids) — and is
identical from 2027-04 on.

**(iv) Renewal-feebate toggle rule (encoded).** The toggle affects
RENEWAL QUANTA only — renewal price basis PQP alone
(`renewal_feebate_no`) vs PQP + band quantum (`renewal_feebate_yes`) —
and NEVER the price path. The two cells differing only in the toggle
therefore share an identical path and PQP series; verified
programmatically on the WRITTEN output (grouped pqp_by_cell.csv, max
abs diff exactly 0.0 S$ for all 4 toggle pairs) and recorded in
tables/pqp_derivation.csv and INV-10.

**Latest derived PQPs (2027-12, = flat forward level after the pulse
window; 2027-01 shown for the pulse effect):**
OptionA+E_removed 129,800.16 (2027-01: 130,122.07) ·
OptionA+E_cars_only 129,800.16 (2027-01: 129,884.05) ·
OptionB+E_removed 129,743.03 (2027-01: 130,064.94) ·
OptionB+E_cars_only 129,743.03 (2027-01: 129,826.91).

INV-10 PASS (verification/invariant_checks.csv).

---

## 13. Step 11 — Feebate revenue by option (this batch)

**Revenue composition rules** (all inputs + windows stated; quantums are
PROPOSED per paper s2.18, Tables 1/2 — 2025 mix, freeze-window 2025-01..05
labeled):

- Base = annualised Jan-May 2025 registration count per band x PROPOSED
  band quantum (Batch D/Fbar convention; `tables/banding_shares.csv`,
  98.73% coverage, frozen 2025-05). Recomputed independently here:
  Option A 16,093 x (-15,000) + 7,205 x 0 + 22,477 x (+15,000) =
  **95,760,000 S$/yr**; Option B 4,657 x (-15,000) + 11,437 x (-7,500) +
  7,205 x 0 + 11,086 x (+7,500) + 11,391 x (+15,000) = **98,377,500
  S$/yr**. Cross-foot vs Batch D (95.76M / 98.38M): exact, diff 0.00 S$
  (verification/crossfoot_log.csv).
- **E-shift delta** (Batch E: 6,400 E-shifted registrations/yr,
  Category-B-skewed, banded by OMV per `tables/e_shift_feebate_base_delta.csv`):
  Option B = **+38,624,175 S$/yr** (recomputed from the table's published
  2dp per-band counts; Batch E's printed +38,624,201 is the same
  computation at unrounded counts — 26 S$ input rounding, PASS at the
  documented 150 S$ tolerance; logged). Option A = **+43,729,050
  S$/yr** (B-shift counts aggregated onto Option A's 35th/50th
  percentile bands).
- **Per-E-option base composition:**
  - `E removed`: base = merged-car base + E-shifted flow (Batch E
    convention — the removal flow re-enters the merged passenger-car
    category). Revenue effect quantified as a delta against the same
    base EXCLUDING them: +43.73M (A) / +38.62M (B) S$/yr.
  - `E retained for cars only`: E-registered cars (6,400/yr) are
    INCLUDED in the car feebate base, banded by OMV as in the E-shift
    table (documented choice — the paper retains Category E for CAR
    registration, s2.23(b), and the feebate applies to the merged
    passenger-car category, s2.22; exclusion would double-count the
    E-shift arithmetic). Quantified size: +43.73M (A) / +38.62M (B)
    S$/yr, identical to the E-shift delta by construction.
  - Net feebate revenue therefore: Option A 139,489,050 S$/yr (both E
    options); Option B 137,001,675 S$/yr (both E options).
- **Sensitivity (Batch C mix proxies, `tables/banding_shares_sensitivity.csv`):**
  variant cut points x the same base mix. S1 (LTA-2025-OMV cut points,
  2025-01..05 mix): A 59,567,000 / B 70,432,500. S2 (uniform band
  weights): A 23,437,500 / B 43,537,500. The E-shift delta is cut-point
  invariant (B-skewed composition banded identically under the variant
  cut points on the same base mix) so the delta adds unchanged.
  Finding: with the paper's symmetric +/-15,000 design, net revenue is
  dominated by the cut-point location — the 2025 registration mass is
  heavily concentrated in the S$20k-40k OMV range, so a few-thousand
  shift in a percentile cut point moves tens of thousands of
  registrations between the rebate and levy bands (S1/S2 cut points vs
  main differ by 8-26% in the 35th/50th percentile). The main 2025-mix
  base is the plan-stated anchor; the annual-review mechanism (paper
  s2.19) means the realized revenue path tracks realized mix
  percentiles, not 2025 levels.
- **Incidence vs total COE revenue** (merged + C + D):
  - Merged: forward quota 2,137.5/round x 24 x with-fee latest
    2027-12 (Batch D/Step 8-9: A 129,873.20 / B 129,816.07) =
    2,137.5 x 24 x price = 6,662,495,160 (A) / 6,659,564,391 (B) S$/yr.
  - C: latest 6 biddings window 2026-08 b1..2026-10 b2 (Batch B panel),
    avg quota 311.17/round x 24 x avg premium 91,813.50 = 685,663,218
    S$/yr under `E retained cars only`; under `E removed` the C quota
    is +11.11% (311.17 -> 345.74/round, 7,468 -> 8,298/yr, Batch E;
    10% E de-registration share, fn5) and the C price is HELD FLAT at
    91,813.50 (Batch E finding: C/E price NOT DETECTABLE in the first-
    difference data — flat price is the conservative revenue bound)
    => 761,868,423 S$/yr.
  - D (motorcycles): 523.0/round x 24 x 11,391.83 (same 6-bidding
    window 2026-08 b1..2026-10 b2; window stated) = 142,990,250 S$/yr.
  - Total COE revenue and incidence (net feebate revenue / total):
    A+E_removed 7,567,353,833 -> **1.843%**; A+cars_only 7,491,148,628 ->
    **1.862%**; B+E_removed 7,564,423,064 -> **1.811%**; B+cars_only
    7,488,217,859 -> **1.830%**.
- **Cross-foot** (verification/crossfoot_log.csv): net revenue
  independently recomputed to the dollar from band shares x quantums x
  registration counts — exact-count base vs Batch D (PASS, diff 0.00
  S$); exact-count E-shift Option B vs Batch E (+38,624,175 vs
  +38,624,201, PASS within input rounding); 2dp-share reproduction
  path recorded as INFO (quantifies 2dp rounding: base -44,475/+18,012
  S$ vs exact; E-shift +3,930 S$).

## 14. Step 12 — Demand shifts by car-value band (this batch)

**Arithmetic (stated so Steps 14/G/H can consume it).** Step 8's
with-fee merged price path equals the no-fee path minus Fbar (linear
demand, one fixed-point update), i.e. the feebate acts as a UNIFORM
price-level shift of Fbar on the merged demand curve. The resulting
demand shift is therefore

    dQ_total = -Fbar x kappa_M      (kappa_M = 0.321748 bids/S$, M3
                                      merged first-difference slope)

  = -2,091.97 x 0.321748 = **-673.09 bids/yr (Option A)**;
    -2,149.11 x 0.321748 = **-691.47 bids/yr (Option B)**.

Because the shift is price-level-uniform, the band decomposition is the
ALLOCATION of the total shift by each band's bid-response weight:

    w_b = (s_b x f_b) / sum_k (s_k x f_k)      [registration-weighted
                                                quantum per band]
    dQ_b = dQ_total x w_b

with s_b from `tables/banding_shares.csv` (exact annualised counts,
98.73% coverage, frozen 2025-05) and f_b the PROPOSED quantums.
Positive dQ_b (rebate bands) = extra demand attracted; negative (levy
bands) = demand suppressed. Model-level allocation: each catalog
model m carries weight reg_weight_m (its annualised registration
share), and band/OMV-decile attribution is the sum of w_b x
reg_weight_m over the models in that band/decile — the 217-model
catalog (`tables/banding_models_optionA/B.csv`, with `coe_class` A/B,
`fuel`, `omv_sgd`) is the decomposition basis; OMV decile =
registration-weighted decile of catalog OMV (decile 1 = cheapest).

**Results** (tables/demand_shift_by_band.csv — long format,
dimension x value; tables/segment_shift.csv; every row
SCENARIO-labeled + data window 2024-01..2025-05 for the M3 curve fit,
mix frozen 2025-01..05):

- **Bands (direct arithmetic, summing exactly to the total):**
  Option A: band1 (0-35th, -15,000) +1,697.69; band2 (35-50th, 0) 0;
  band3 (>50th, +15,000) -2,370.78; total -673.09. Option B:
  band1 +490.74; band2 +602.69; band3 0; band4 -584.35; band5
  -1,200.55; total -691.47.
- **EV vs ICE** (EV = catalog fuel-type EV rows, 104 models; ICE 113):
  Option A: EV -686.98 (102.1% of the total shift), ICE +13.89
  (ICE mass-market models sit in the rebate band, so ICE net demand
  rises slightly while EV demand is fully suppressed and more).
  Option B: EV -595.44 (86.1%), ICE -96.03.
- **Cohort** (catalog coe_class as the current-A/B proxy): current_A
  (mass-market) demand RISES: +640.61 (A) / +468.15 (B) bids/yr;
  current_B (luxury) demand FALLS: -1,313.70 (A) / -1,159.62 (B).
  The feebate is demand-regressive: it attracts mass-market demand
  and suppresses luxury demand.
- **OMV decile** (registration-weighted decile of catalog OMV): gains
  in deciles 1-4 (d1 +430.99 / d2 +509.66 / d3 +503.42 / d4 +253.63
  under A; B: +430.54 / +284.69 / +251.48 / +126.70), zero at d5
  (the 35-50th percentile straddles the A neutral band), losses
  widening to d10: -501.65 (A) / -501.26 (B).
- **Segment mix** (tables/segment_shift.csv): luxury (OMV > 49,662,
  the 75th-pct cut point) -1,201.47 (A) / -1,200.55 (B); mass-market
  (OMV <= 49,662) +528.38 (A) / +509.07 (B). EV share of the total
  shift 102.1% (A) / 86.1% (B).

**Caveats (carried to Step 14).** M3 first-difference elasticity is
SCENARIO-ONLY: MEDIUM grade for the merged A curve, LOW grade for B
(slopes A +4.99 / B +8.24 per 10,000 S$/yr, evidence_grading.csv);
C/E not detectable. The band decomposition is an allocation of one
total shift — it identifies WHERE the response lands given the linear
model, not independent band-level elasticities.

## 15. Step 13 — Renewal cohort banding and renewal-holder impacts (this batch)

**Vintage and scope.** Regime start 2027-01-01 (Step 2); renewal
vintage = 2027 - 10-year COE term = **2017** (stated in every label).
The 2016 cohort renews in 2026, PRE-regime: EXCLUDED from all
renewal-impact rows.

**Data source chain (attempts documented in provenance.md s.9):**
1. Historical LTA "Car Cost" PDF editions for ~2017 — NOT AVAILABLE
   (four URL patterns probed, all 404; LTA stats page lists only the
   current monthly edition M032 Aug 2026).
2. LTA OneMotoring "Average OMV of New Cars Registered" year=2017
   edition — **AVAILABLE** (verification/lta_omv_2017_page.html; 5,178
   model-month rows, 1,170 distinct models, all 12 months) ->
   data/processed/lta_omv_2017_avg.csv. Model-level OMV at the vintage
   used for banding.
3. LTA 2017 annual registration statistics — AVAILABLE
   (MVP02-1_New_Reg_by_COE.pdf, 2025 edition of the annual series):
   official 2017 COE class splits A 46,076 / B 45,699 and total 2017
   car registrations (A+B+E residual) 91,922.
4. 2017 slice of data/raw/registrations.csv (frozen, 2017-01..2017-12):
   make-level counts (91,922 cars, 56 makes) for the allocation.
   2025-mix FALLBACK NOT USED (fallback_used = false).

**Volume assumption (stated).** Renewal volume transition year = the
full 2017 car-registration cohort, **91,922/yr** (A 46,076 + B 45,699
+ E residual 147 = 2017 car registrations, official LTA). Assumption:
the full cohort renews in 2027 (upper bound — inter-term
de-registrations 2017..2027 are not observable in public data); the
ASSUME tag is carried in the data window field of every row.

**Cohort composition and banding**
(data/processed/renewal_cohort_banded.csv, 52 rows):
- Make allocation: equal within-make model allocation (approximation —
  the public 2017 series has no make x model counts); coverage 99.98%
  (14 makes absent from the LTA 2017 OMV edition, ~17 registrations).
- Class split: the official LTA A/B counts are the cohort split (NOT a
  proxy); a model-level proxy (2017-era cc-suffix rule: cc04/06 -> A,
  cc07 -> B; MPO flag unobservable in the public data) is scaled
  exactly to the official totals, so band x class rows reconcile to
  46,076 / 45,699 / 147 by construction.
- Banding at two cut-point bases: PROPOSED 2025 percentiles (base: the
  paper's bands are defined on 2025 registrations) and VINTAGE 2017
  percentiles (sensitivity: the annual-review mechanism re-derives
  cut points on realized mix, so a 2017-vintage application would use
  2017 percentiles — vintage cut points A [23,052 / 26,379] vs 2025
  [28,877 / 36,062]; B [16,570 / 23,052 / 26,379 / 35,155] vs
  [20,310 / 28,877 / 36,062 / 49,662]).

**PQP pricing rule (stated).** Every renewal scenario is priced at the
CELL-LEVEL merged PQP from `data/processed/pqp_by_cell.csv` (Step 9):
2027-12 latest value per cell as the transition-year price (2027-01
value carried as context). NEVER the merged clearing price, never a
reused option-level PQP. The renewal-feebate TOGGLE changes ONLY the
band quantum: fee-off cost = PQP; fee-on cost = PQP + band quantum
(applied at renewal). The price path is identical across the toggle
(verified: pqp_2027_12 constant within each option across all four
cells of that option).

**Results** (tables/renewal_impact_master.csv, 8 cells + per-cell files
under tables/renewal/; regime start 2027-01-01, vintage 2017,
cell-level-PQP basis in every label):
- Fee-OFF (both options): annual renewal cost = cohort x cell PQP
  (2027-12): Option A 129,800.16 -> 11,931,490,307.52 S$; Option B
  129,743.03 -> 11,926,237,506.23 S$. (Costs are summed over the
  banded band x class rows, whose registration counts reconcile to
  91,921.99 of 91,922 — a 0.01-vehicle float artifact of scaling the
  model-level class proxy to the official 46,076/45,699 totals;
  immaterial at S$1.3k on S$11.9B.)
- Fee-ON: the 2017 vintage cohort is LOW-OMV relative to the 2025-based
  cut points (2017 model median OMV ~S$26k vs 2025 ~S$36k), so the
  PROPOSED cut points put the bulk of the cohort in the REBATE bands
  and the feebate at renewal is a NET REBATE, not a net levy: Option A
  net quantum -517,215,600 S$/yr (total cost 11,414,274,707.52);
  Option B net quantum -353,265,450 S$/yr (total 11,572,972,056.23). Hand-checked:
  A = 55,573.5 x (-15,000) + 15,255.0 x 0 + 21,092.5 x (+15,000);
  B = 21,910.5 x (-15,000) + 33,663.1 x (-7,500) + 11,803.0 x 7,500 +
  9,289.5 x 15,000.
- Winners/losers (fee-on): the pre-A (2017 mass-market) cohort is the
  NET WINNER under both options (per-vehicle quantum -12,628.77 A /
  -9,260.73 B); the pre-B (2017 luxury) cohort is the net loser
  (+1,393.10 A / +1,587.45 B). pre_A - pre_B = -14,021.87 (A) /
  -10,848.18 (B) S$/vehicle. Fee-off cells are ties by construction.
- Transition-year effect: identical across E options within each
  option (the toggle never touches the price path; E options only
  shift the cell PQP via the Batch E C/E scenario, already embedded in
  pqp_by_cell.csv — visible in the 2027-01 context values: removal
  pulse +238.02 A / +238.03 B, matching Batch E exactly).
- Vintage-cut-point variant (VINTAGE_2017pct): banding the cohort at
  its OWN 2017 percentiles neutralizes the cohort's position (by
  construction ~half the mass per band side), so the net quantum
  shrinks toward zero — quantified in renewal_cohort_banded.csv;
  this is the binding sensitivity for the open PQP-renewal question
  (Step 14/G/H): under 2025-based cut points the renewal feebate is a
  net rebate of ~S$350-520M/yr on the 2017 cohort.

## 16. Step 14 — Unintended consequences (Batch G)

Implementation: `src/consequences.py`. All outputs carry the standard
label stamp (regime start 2027-01-01 + vintage 2017 + scenario tag);
value types SCENARIO / DIRECTIONAL / OBSERVED as stated per table.

### 16a. Band-boundary spec gaming (`tables/boundary_gaming_zones.csv`)

- Zone width: **+-5% of the cut-off OMV** — an ANALYTICAL CHOICE of this
  study to bound the spec-gaming exposure; it is NOT an LTA parameter
  (stated on every row via the `zone_width_is_analytical_choice` column
  and the label). Sensitivity variants S1 (LTA-2025-OMV cut points) and
  S2 (uniform weights) would shift the zones — not recomputed here; the
  main-variant zones are the reported exposure.
- For each cut-off c: zone = [0.95c, 1.05c]. Quantified per option per
  cut-off: (i) share of the annualised Jan-May 2025 registration mix
  (frozen 2025-05; x catalog convention per Batch C) whose OMV falls
  inside the zone — `zone_share_pct_covered_mix`, i.e. share of the
  COVERED mix (coverage 98.73% of Jan-May 2025 registrations; makes not
  in the catalog excluded; weights per model = equal split of the make's
  Jan-May 2025 registrations, Batch C fallback convention);
  (ii) the OMV adjustment a vehicle exactly at a zone edge needs to
  cross into the adjacent band (5% of c at the zone edge, 0 at the
  centre); (iii) the quantum at stake = |quantum(band below c) -
  quantum(band above c)|. Annualised exposure
  `est_registrations_annual_in_zone` = zone share x annual
  registrations base (Batch F fee_revenue_base: 45,775 A / 45,776 B).
- Incentive interpretation (stated, not fabricated): a dealer can
  re-spec a vehicle across the boundary whenever the quantum at stake
  exceeds the spec-upgrade/spec-downgrade cost. No dealer cost data
  exist in this run, so the QUANTIFIED exposure is (zone registration
  share) x (quantum at stake): S$15k at stake per vehicle at both
  Option A cut points, S$7.5k at each Option B cut point.
- Results (main variant; independently re-verified against raw
  weights — all counts/shares/estimates reconcile): Option A p35 zone
  (27,433.15..30,320.85): 23 models, 11.84% of covered mix (~5,418
  annualised registrations); p50 zone (34,258.90..37,865.10): 23
  models, 13.79% (~6,312, largest Option A exposure). Option B: p10
  zone (19,294.50..21,325.50): 7 models, 5.56% (~2,544); p35 zone: 23
  models, 11.84% (~5,418); p50 zone: 23 models, 13.79% (~6,312,
  largest overall exposure); p75 zone (47,178.90..52,145.10): 19
  models, 6.84% (~3,130). The shared p35/p50 zones have identical
  membership under both options (same cut point).
- Data note: the p35 cut-point 28,877 and the p50/p75 cut points
  appear under both options. BYD SEALION 7 (OMV 36,062) sits exactly
  AT the p50 cut point and is banded BELOW it (upper-inclusive
  convention, Batch C — matches the paper's Sealion-7-at-p50
  placement), so it counts in the p50 zone.

### 16b. Variant-family classification distortion
(`tables/classification_distortion.csv`)

- Family rule (documented, deterministic): group the 217 catalog models
  by (make, model base name). Base name = model name with (1)
  parentheticals removed; (2) token punctuation normalised (`,`, `.`,
  `_` stripped; `#`, `-`, `+` preserved as name characters: SMART #1,
  ZR-V); (3) spec/trim tokens removed — a whitelist of known spec
  tokens (HYBRID, PHEV, PLUG-IN, ELEGANCE, STANDARD, LUXURY, LONG,
  RANGE, TRIM, ENGINE codes, wheel/grade markers such as R-DYN, S-
  LINE, M-Sport, 4MATIC/4WD, power suffixes like 404PS) plus a
  conservative regex fallback (all-caps single letters A-Z except
  name-initials, 2-3 digit engine/power codes for non-BMW makes, BMW
  2-digit power codes); (4) letter+digit compound tokens split
  (IONIQ5 -> IONIQ 5, EDGRIVE35 -> EDGRIVE 35) with the parts
  re-checked against the spec rules; (5) leading repetition of the make
  dropped (MAZDA3 -> 3); (6) if all tokens are stripped, the original
  name is kept (safety).
- A family SPANS a boundary if its members fall in different bands under
  an option. 'Mis-banded share' = affected members / 217 catalog models
  (the share of models whose band assignment DEPENDS on which variant a
  buyer takes from the family); stated per row in the CSV.
- Results: 139 distinct families per option (same grouping). Option A:
  12 spanning families, 28 affected models = 12.90% of 217; max
  within-family quantum difference 15,000 S$ (BYD SEAL family spans the
  p50 cut point). Option B: 20 spanning families, 55 affected models =
  25.35% of 217; max within-family quantum difference 7,500 S$ (AVATR
  07 family spans the p75 cut point). Option A's 12 spanning families
  are a subset of Option B's 20 (verified: B's extra 8 span the B-only
  p10/p75 cut points).
- Caveat (stated in the table label): base-name normalisation is a
  documented heuristic; two genuinely distinct models sharing a base
  name (none found in the 217-catalog audit) would be over-merged, and
  one model with an unrecognised spec suffix would be under-split. The
  spanning list in the CSV is the verifiable ground truth; family
  counts are the estimate.

### 16c. Segment demand shifts (`tables/segment_shift.csv`)

- Batch F's table (Step 12) already carries per-option EV-share and
  luxury-vs-mass-market mix shifts; Batch G verified completeness:
  all required shift rows are present, so NO rows were added (extend-
  only rule respected; file content byte-identical to Batch F).

### 16d. Used-car channel (`tables/used_car_directional.csv`)

- DIRECTIONAL ONLY — there is NO usable used-car price/flow data in
  this run (stated explicitly; no numbers produced). `value_type` is
  DIRECTIONAL on every row. Directions: (1) feebate raises new-car
  prices in upper bands -> used cars relatively more attractive
  (used-car demand up); (2) net-rebate renewal feebate (open question)
  would raise the renewal cost path for upper-band incumbents ->
  longer holding / slower trade-in, directionally supporting used-car
  supply and prices; (3) removal of Category E lifts the merged-car
  PQP in 2027-01..03 (pulse) -> a one-off relative-appeal shift for
  used cars, directionally small (pulse/6 ~ S$238 per PQP month).
- `src/config.py` extended with `TYPE_DIRECTIONAL` so the label stamp
  can carry value_type=DIRECTIONAL without a numeric value.

## 17. Step 15 — Master scenario matrix (Batch G)

Implementation: `src/master_matrix.py`. Outputs:
`tables/master_matrix.csv` (one row per cell, 8 rows) and
`data/processed/price_paths/<cell>.csv` (8 files = 4 distinct paths x 2
renewal-feebate toggle copies).

### 17a. Cell construction and price-path assembly

- 8 cells = {Option A, B} x {E removed, E cars-only} x {renewal feebate
  no, yes} (config.MASTER_MATRIX_CELLS). Per cell: regime_start
  2027-01-01, vintage 2017 (= 2027 - 10-yr COE term), price path
  (merged-car scenario clearing price per bidding round, 2010-01..
  2027-12, 422 rounds), cell-level PQP (Step 9, `data/processed/
  pqp_by_cell.csv`), feebate revenue summary (Step 11,
  `tables/fee_revenue_base.csv` + `tables/fee_revenue_sensitivity.csv`),
  renewal-cost summary (Step 13, `tables/renewal_impact_master.csv`).
- Price path source per cell: option-level WITH-FEE path (Batch D,
  `tables/merged_price_option{A,B}_withfee.csv`). For E_removed cells
  the Step 10 one-round E-shift demand pulse (+1,428.1354 S$ at
  2027-01 b1, from `tables/ec_scenario_E_removed.csv`) is ADDED to the
  price path; for E_cars_only cells the path is UNADJUSTED (paper
  s2.23(b): no car-demand shift). The pulse shows in the cell PQP for
  2027-01..2027-03 (one of the six bids in each 3-month PQP window).
- The two cells differing only in the renewal-feebate toggle share the
  IDENTICAL price path (the toggle affects renewal quanta only). This
  is VERIFIED PROGRAMMATICALLY, not assumed — see 17c.

### 17b. Master-matrix columns (one row per cell)

cell_id; regime_start; vintage (+ derivation); price_path_distinct_id;
price_path_file; price_path_source; price_path_latest_2027_12_sgd;
price_path_pulse_round; price_path_pulse_months; pqp_2027_12_sgd;
pqp_2027_01_sgd_context (carries the removal pulse); feebate_revenue_
base_sgd; feebate_revenue_base_excl_e_shift_sgd; feebate_revenue_
e_shift_delta_sgd; feebate_revenue_sensitivity_range (S1/S2 string);
renewal_cohort_volume; renewal_annual_cost_total_sgd; renewal_annual_
cost_pqp_only_sgd; renewal_delta_vs_no_feebate_sgd; renewal_per_
vehicle_preA_sgd; renewal_per_vehicle_preB_sgd; renewal_winner;
renewal_loser; renewal_detail_pointer; label; value_type; scenario;
data_window; citation.

### 17c. Programmatic identity/consistency checks (all asserted)

- T1 toggle-pair identity: each {no, yes} file pair is BYTE-identical
  (sha256) AND value-identical (pandas equality on the price columns).
  4 distinct paths confirmed (4 distinct sha256 hashes across the 8
  files). Method recorded in `batch_handoff_g.json`.
- T2 pulse cross-foot: cell PQP (E_removed) - cell PQP (E_cars_only)
  for 2027-01..2027-03 equals pulse/6 = 238.0226 S$ per option, within
  a 1-cent tolerance (pqp_by_cell publishes each cell PQP rounded to
  2dp independently, so the 2027-01 diff for OptionB reads 238.03 vs
  the raw 238.0226 — matching the Batch E C-removal pulse +238.03
  exactly).
- T3 latest-price consistency: price-path latest (2027-12) equals the
  cell PQP 2027-12 at 2dp (flat forward scenario).
- T4 renewal join: renewal_impact_master pqp_2027_12 equals
  pqp_by_cell 2027-12 per cell.
- T5 revenue join: fee_revenue_base totals are identical across E
  options within each option (Batch F convention — the E-registered
  flow is in the base, identical both E options).

### 17d. Headline numbers (reconcile to Batch F handoff)

- Price path latest 2027-12 (= cell PQP 2027-12): OptionA 129,800.16;
  OptionB 129,743.03.
- Feebate revenue base (net, incl. E-registered flow): OptionA
  139,489,050 (excl. E-shift 95,760,000 + delta 43,729,050); OptionB
  137,001,675 (excl. E-shift 98,377,500 + delta 38,624,175). Sensitivity
  range S1/S2: A 59,630,005 / 23,365,106; B 70,363,905 / 43,540,767.
- Renewal annual cost (full 2017-vintage cohort, PQP-only): no-feebate
  11,931,490,307.52 (A) / 11,926,237,506.23 (B); with-feebate
  11,414,274,707.52 (A) / 11,572,972,056.23 (B). Renewal delta vs
  no-feebate: -517,215,600 (A) / -353,265,450 (B) — a NET REBATE.
  Per-vehicle preA -12,628.77 (A) / -9,260.73 (B); preB +1,393.10 (A) /
  +1,587.45 (B). pre_A is the net winner, pre_B the net loser under
  fee-on; fee-off cells are ties by construction.

## 18. Batch H (Steps 16-18) — Verification suite, charts, final reports

### 18a. Verification suite design (`src/verify.py`, 88 checks, 10 groups)

Check groups per the Step 16 spec: (a) row-count reconciliation for
every fetched resource (provenance_log vs on-disk row counts); (b) time
anchors — COE last month 2026-10 has both biddings, registrations last
month 2025-05 — plus 8 spot prices against the reference set (2026-10
b1/b2, all five categories); (c) the 2026 A>B inversion set confirmed at
per-bidding resolution (exactly 4 rounds, all b2, spreads +1,500/+2,009/
+345/+103); (d) table-figure traceability of REPORT.md and
STATS_SUMMARY.md; (e) cross-foots — band shares sum to 100.0 (A) /
99.99 (B, 2dp rounding, documented exception) and net feebate revenue
independently recomputed to the dollar from band counts x quantums
(base diff 0.0; E-shift diff -26.0 within the 150.0 tolerance for the
6,400-vehicle batch count); (f) scenario invariants / negative controls
(INV-7 bounds, INV-8a/8b zero-effect controls, INV-9 C-quota +11.11%
identity, INV-10 label audit); (g) PQP MA-3 recheck against published
PQP; (h) scenario-label audit; (i) freeze-label audit; (j) provenance
audit (sha256 + row counts on disk for 11 archived/derived files).

Suite result on the final pass: 88 checks, 87 pass, 1 pass_documented
(the Option B 99.99% cross-foot exception), 0 fail. Output:
`tables/verification_report.csv` + `verification/report_traceability.csv`.

### 18b. Traceability engine (check d) — mechanics

- Citation tags in the documents: `[[t|<table>|<rowkey>|<cols>]]` where
  rowkey is a " / "-joined list of cell values (substring match against
  row cells) and cols are the cited columns. All numeric tokens in the
  cited cells become candidates for that paragraph.
- Granularity: PARAGRAPH-level citation (a numeric token is traceable
  if its paragraph carries at least one tag and the value matches a
  cited cell, a registered derived identity, or the allowlist). Line-
  level matching was rejected: markdown soft-wraps place tags on
  different physical lines than the numbers they cite, which made the
  check sensitive to formatting rather than content.
- Citation syntax is stripped from lines before token extraction
  (numbers inside `[[t|...]]` are not report content).
- Matching tolerances: |v - c| <= 0.011 + 1e-9 (absolute, covers 2dp
  rounding of full-precision cells); relative 2% for tiny values
  (p-values); magnitude matching |v - |c|| for signed deltas cited as
  magnitudes (e.g. "-517,215,600" cited as "517,215,600").
- Structural allowlist: integers 0..60 (counts, biddings, months) and
  years 2002..2027 blanket-allowed; a documented ALLOWLIST/
  ALLOWLIST_NOTE registry (~25 entries) covers provenance-only numbers
  (row counts, null shares, SINGSTAT cell values, section labels) —
  every entry cites provenance.md.
- DERIVED registry: values computed from cited cells (forward price
  drop, bid-gap equivalents, sensitivity totals, renewal deltas in M
  units, pulse PQP differences, typical-model row totals) — each
  registered with value, tolerance and derivation string.

Final pass: 720 numeric lines scanned, 0 untraceable numbers in
REPORT.md + STATS_SUMMARY.md combined.

### 18c. Freeze-label audit (check i) — mechanics

Mix-scale numbers (comma-grouped values >= 1,000 or 2dp percents) must
sit in a paragraph with an explicit data window: a standard window
marker in the paragraph text (e.g. "2025-01..2025-05", "frozen at
2025-05", "2017-01..2017-12") OR in the data_window/label cells of the
table rows the paragraph cites (tags carry the window via the cited
row's data_window column — every study table has one). Untagged
mix-scale paragraphs fail. Final pass: clean.

### 18d. Banding reconstruction (recap with data window + approximation)

- Data window: 2025-01..2025-05 (frozen at 2025-05), Jan-May 2025
  registration mix x Car Cost Aug-2026 catalog composition; labelled
  FALLBACK because the LTA 2025 model-level OMV *distribution* is not
  public (the 2025 edition reports model-month AVERAGE OMV only).
- Approximation statement: equal split within make (make-level mix x
  catalog model composition); catalog coverage 98.73% of the slice
  (19,073 of 19,318 valid rows; 21 makes excluded). Cut points are
  percentile positions of the weighted OMV grid; shares annualised
  (x12/5). Sensitivities: S1 = LTA 2025-edition average-OMV weights
  (3,366 model-month values); S2 = uniform model weights.
- Renewal-cohort banding: data window 2017-01..2017-12 (OBSERVED
  registration slice, 4,265 valid car rows, 56 makes) x LTA OMV 2017
  edition (5,178 model-month rows, 1,170 models, 99.98% cohort
  coverage). NOT the 2025 fallback (Car Cost 2017 PDFs unavailable,
  4x 404 — provenance s9.4). Approximation: same within-make equal
  split on the 2017 slice; class split per LTA annual statistics
  (2017 A=46,076 / B=45,699 = 91,775) with the 147-vehicle residual
  carried as an explicit E_residual class.

### 18e. Regime-start anchor and its source

2027-01-01 is an ASSUMPTION, not a paper parameter: the consultation
paper contains no implementation date (verified by full-text scan,
Batch A). The consultation window is 8 Oct - 2 Nov 2026 (s1.17,
comments due 2 Nov 2026) with a review due end-2026 (s4.3), making
1 Jan 2027 the earliest plausible start. Every scenario table carries
`regime_start: 2027-01-01`; the label audit (INV-10 / check h) fails
any renewal/E-C/master-matrix label missing it.

### 18f. Transition-year vintage derivation

2027 renewal cohort = vehicles whose initial COE was registered in
2027 - 10 = 2017 (10-year COE term, the regime's first full renewal
wave). The 2016 cohort is pre-regime (renews 2026, before the regime
starts) and is excluded. Every renewal table states `vintage: 2017`,
`vintage_derivation: 2027 - 10`.

### 18g. Per-cell PQP derivation and method validation

- Derivation: each master-matrix cell's PQP series = 3-month moving
  average (MA-3) of that cell's OWN merged-car with-fee price path
  (own-path MA — never a reused option-level PQP, never the clearing
  price). At the transition-year start (2027-01) the window spans the
  last three months with bidding before the regime: 2026-09; 2026-10;
  2027-01 — 6 biddings. E-removal cells show the one-round E-shift
  pulse (+1,428.14 S$ at 2027-01 b1) inside that window, hence their
  2027-01 PQP sits +238.02 (A) / +238.03 (B) S$ above the E-cars-only
  cells (pulse/6).
- Method validation (window 2002-02..2026-09 published PQP vs
  2010-01..2026-10 observed per-bidding premiums, pooled A+B):
  recomputed MA-3 matches LTA's published PQP within max 0.83 S$ / mean
  0.428 S$ over 392 months / 2,352 bids; per category A 0.83/0.41, B
  0.83/0.446 (max at 2026-09, a logged LTA-side -0.83 S$ deviation), C
  0.83/0.438, D 3,205.5/16.776 with exactly one explained outlier
  (SINGSTAT single-cell error 2010-01 b2: QP 852 vs LTA 20,090).
  Residual signature: published - MA3 in {0, 1/6, 2/6, 3/6, 4/6, 5/6}
  S$ for 783 of 784 category-months — i.e. LTA rounds the MA up to the
  next whole dollar. No E PQP is published (A-D only), so the merged
  PQP construction is validated on the A/B inputs only.

### 18h. Charts (Step 17)

`src/make_charts.py` renders 8 figures into `charts/` from the existing
tables only (no recomputation). Conventions: OBSERVED series solid,
SCENARIO series dashed; every title/legend carries the scenario label,
PROPOSED-vs-COMPUTED distinction and data window where applicable;
the 2026 inversion set is annotated on FIG 1; the E-shift pulse is
visible in the E-removal cells on FIG 2. Figures:
ab_convergence_perbidding.png, merged_price_paths.png,
omv_histogram_bands.png, fee_revenue.png, demand_shift_by_band.png,
ec_quota_price_paths.png, gaming_zones.png.

### 18i. Reports (Step 18)

REPORT.md (executive summary first; PROPOSED vs COMPUTED throughout;
assumptions flagged with sensitivities; transition-year vintage stated
in every renewal discussion; per-cell PQP derivation stated in the
master-matrix section; freeze-window tags on every mix-based number)
and STATS_SUMMARY.md (one page, every value cited inline). Both are
machine-checked by the traceability engine (check d) and the freeze
audit (check i) on the final pass — 0 untraceable numbers, clean label
audits.

## 19. Step 13b — 2028-start renewal sensitivity (added 2026-11-01,
review session)

**Why.** The base case anchors the regime at 2027-01-01, but the
consultation paper states no implementation date and LTA findings are
due 1H2027, so a 2028 start is the more probable real-world date. This
sensitivity re-derives the first-renewal cohort for a 2028-01-01 anchor
so the README (section 4.6, Table 7) can state both.

**Derivation.** `src/renewal_cohort_2028_sensitivity.py` mirrors
Step 13 exactly, with:
- vintage = 2028 - 10 = **2018** (config.transition_year_vintage with an
  explicit regime_start); the 2017 cohort renews 2027, PRE-regime under
  this anchor, and is excluded;
- official 2018 class split A 39,877 / B 40,216 (LTA Annual Vehicle
  Statistics 2025 edition, same file as s15's 2017 cross-check, 2018
  row);
- 2018 slice of data/raw/registrations.csv: 80,281 valid car
  registrations, 52 makes; 188-vehicle residual carried as E_residual
  with the Batch E composition;
- model-level OMV: LTA 2018 "Average OMV of New Cars Registered"
  edition (provenance.md s9.7; fetched 2026-11-01 after LTA's scheduled
  maintenance; 3,978 model-month rows, 875 models, 44 makes; coverage
  99.98% of the cohort; equal within-make allocation, same as Step 13);
- both cut-point bases: PROPOSED_2025pct (headline) and VINTAGE_2018pct
  (2018's own percentiles: Option A 22,799/27,183; Option B
  15,596/22,799/27,183/37,965).

**Results (quantum net = first-year feebate cost to the government;
PQP-independent).**
- PROPOSED basis: Option A -377,561,400 (-4,703/car; pre-A -11,971.69,
  pre-B +2,450.49); Option B -274,526,775 (-3,420/car; pre-A
  -9,017.68, pre-B +2,087.14).
- VINTAGE_2018pct basis: +135.2M (A) / +143.4M (B) — the sign flips,
  same cut-point-base effect as Step 13's VINTAGE_2017pct.
- vs base case (2017 cohort): -377.6M is 27% smaller than -517.2M
  (A); -274.5M is 22% smaller than -353.3M (B); sign unchanged.

**Method cross-check.** Re-running the Step 13 computation on the 2017
cohort from the shipped row-level files reproduces the shipped
-517,215,600 (A) / -353,265,450 (B) exactly before the 2018 figures
were accepted. (An earlier exploratory run that used unscaled
within-band allocation totals gave -331.2M/-238.8M; the scaled
per-class rows above are the method-consistent figures and the ones
reported in the README.)

**OMV-list sensitivity (affects the base case too).** Re-banding the
2017 cohort against the coarser 2025 edition (93% coverage instead of
99.98%) turns the Option A net from -517.2M into +124.9M — the
year-of-values and list-granularity effects are confounded in public
data. Reported in README section 4.6 as a magnitude caveat, not a
headline change.

**Status.** SENSITIVITY — additive; no base-case table, label or
verification check was modified. `src/verify.py` unchanged (its
invariants reference the 2027-01 base-case labels, which are untouched).
