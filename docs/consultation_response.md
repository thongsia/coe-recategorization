# Response to the Public Consultation on COE Categorisation for Cars

**Consultation:** Public Consultation on Proposed Changes to Certificate of
Entitlement (COE) Categorisation for Cars (LTA; running 8 Oct 2026, 1700hrs
to 2 Nov 2026, 2359hrs).

**Official feedback form:**
<https://form.gov.sg/6abc6eca2c9198bbabff552c> (via
<https://go.gov.sg/coe-pcd-feedback>)

**Basis of this response.** Every figure below is drawn from an independent,
fully reproducible data study of the proposal:
<https://github.com/thongsia/coe-recategorization> ("COE Re-categorization: a
data-driven study"). The repository bundles the official data (COE bidding
results 2010–2026, vehicle registrations, LTA's published OMV catalogs),
every table and chart, the analysis code, and an automated verification
suite that re-checks every reported number from disk (88 checks). All
scenario figures are estimates under stated assumptions (2027-01-01 regime
start, registration mix pinned at Jan–May 2025, 100% Category E re-entry
base case, flat Category C price) — they are not predictions, and each is
labelled as such in the repository.

**How to use this document.** The official form carries three free-text
questions. Sections 1–3 below correspond to them one-for-one and can each be
pasted into the matching field; section 4 is the closing note.

---

## 1. Should Categories A and B be merged into a single passenger car
category, with a fee-and-rebate ("feebate") system based on the value of the
car, and if so, how it should be designed?

**The merge itself is low-risk; the design details are where the consultation
should focus.** The two categories already clear at nearly the same price —
S$132,004 (A) vs S$131,901 (B) in the second October 2026 round, a S$103
gap — and Category A actually cleared above B in four rounds during 2026.
Computed for the same round, a merged category would price at S$131,965,
i.e. right where both already are. The feebate would lower the merged price
by about 1.6% (about S$2,100 at the 2027 projection price), offset by fees
minus rebates, so the average car's total outlay (price + fee − rebate) is
unchanged. Within that, four design points deserve LTA's attention:

**1.1 The cut points are the policy, not an implementation detail.** The
feebate's revenue depends on band placement far more than on the quantum:
across the base placement and two sensitivity variants, total annual revenue
ranges from S$67.09M to S$139.49M (about twofold), and for Option A the
new-registration revenue alone ranges fourfold (S$23.37M to S$95.76M). The
base-case figure is therefore a menu entry, not a forecast. We suggest LTA
(a) publishes the derivation recipe — the reference mix window, the OMV
edition, the model weights, and the treatment of models no longer
catalogued — so the number is independently recomputable; (b) commits to a
placement rule in the consultation response; and (c) re-derives and
republishes the cut points at each annual review under the same fixed recipe.

**1.2 The indicative banding tables should be corrected before
finalisation.** Under LTA's own published OMVs, 2 of Option A's 32 listed
rows and 4 of Option B's 34 are internally impossible — no dollar value for
the band line is consistent with the models the paper itself lists. For
example, the paper's Option A table lists the Toyota Noah (OMV S$28,083)
below its 35th-percentile line while the cheaper Toyota Corolla Altis
(S$22,200) is listed above it; the same contradiction appears at Option A's
50th percentile (BYD Sealion 7 Dynamic S$36,062 below; Audi Q3 S$30,629
above) and at Option B's 10th, 35th, 50th and 75th percentiles. We suggest
the indicative tables be regenerated from the final cut points against the
latest published OMV catalog, so the published schedule is one that can
exist.

**1.3 Consider a buffer or ramp at the band boundaries.** About 13.79% of
the registration mix (≈6,312 cars/yr) sits within ±5% of Option A's
50th-percentile boundary, with S$15,000 of quantum at stake; a further 11.84%
sits near the 35th. Crossing a boundary requires a declared-value move of
only 5% of the cut point (about S$1,444 at Option A's 35th percentile) — a
roughly 10:1 payoff ratio that invites spec-trimming to just under the line.
Options, in rough order of intrusiveness: a narrow zero-quantum buffer band
(±1–2%) around each cut point; a quantum ramp near the boundary instead of a
hard step; or targeted OMV verification for registrations landing within ±5%
of a cut point (LTA's catalog makes the check cheap).

**1.4 Same car name, different bands.** 12 model families under Option A
(28 models; 12.90% of the catalog) and 20 families under Option B (55
models; 25.35%) span a band boundary, so buyers of the same car name can end
up in different bands with quantum differences up to S$15,000 — the largest
is the BYD SEAL family, whose two models straddle Option A's 50th-percentile
line at OMV S$34,833–37,458. We suggest LTA either disclose the straddling
families in the consultation response, or band at model-family level.

**1.5 The renewal question is a cost, and its sign depends on an
unspecified choice.** If the feebate applies to renewals, the first renewal
cohort (cars first registered in 2017; 91,922 under Option A) lands mostly
in the rebate bands — 77% under Option A — and the feebate would cost the
government S$517.2M in 2027 under Option A (S$353.3M under B), i.e. about
S$12,600 (A) / S$9,261 (B) returned per car. The pitfall: that sign is an
artifact of which year's values set the bands. Banded at the proposed 2025
cut points, the cohort is a large net cost; banded at its own 2017-vintage
percentiles, the net is largely neutralised, and the 2018 cohort (a 2028
start) flips to a net government revenue of S$135.2M / S$143.4M. We suggest
LTA (a) states explicitly which reference year's values band renewals; (b)
if renewals are included, grandfathers the first cohort or uses
vintage-matched banding; (c) does not present the renewal feebate as a
revenue stream — on new registrations it is a revenue, on renewals it is a
cost; and (d) states the intended effective date, since the first cohort (and
its cost) moves with it — a 2028 start shrinks the first-year cost by 22–27%.

**1.6 The demand effect is small; the bands need not be engineered against
it.** The net demand response to the feebate is about 673–691 bids/yr
(about 1% of the roughly 67,000 merged-category bids/yr) — rebate bands gain,
fee bands lose slightly more. This is a scenario-grade estimate, not a
causal claim, but at that magnitude the band design should serve
administrative simplicity rather than demand management.

## 2. How should Category E be adjusted?

The two options are less apart than they first appear.

**Under removal**, Category C is relieved: its quota rises 11.11%
(7,468 → 8,298/yr), and with the C price held flat (its price response is not
detectable in the data, so flat is a conservative revenue bound) C revenue
rises from S$685.66M to S$761.87M/yr. The 6,400 cars/yr that used E
re-enter the merged car pool — the price effect is a single one-round pulse
of about S$1,428 in the first round (≈+S$1,428.14 under Option A), i.e.
small and transitory. The real cost is the urgent-buyer channel: Category E
COEs are transferable three-month Temporary COEs, currently the only way for
a buyer who needs a car urgently to get a COE without waiting for the next
bidding round (at the price of the round's highest COE — in the last six
rounds E cleared on average S$3,777 above the priciest car COE). LTA's own
consultation paper records a focus-group participant's objection to losing
transferrable COEs. We suggest LTA (a) states the re-entry assumption
explicitly (the study's base is 100% re-entry with a 50% sensitivity — some
urgent demand may simply churn away) and (b) quantifies, or at least names,
the impact on urgent buyers in the consultation response.

**Under "cars-only"**, the channel is preserved in name, but the mechanism
that made it a fast lane — the premium — decays away: once an E COE is
functionally just a car COE, the study's model has its premium (S$3,777 above
the merged price at the 2026 anchor) decay to zero within about six rounds.
"Preserved" should therefore not be read as "unchanged": the urgent-buyer
mechanism survives, but so does its C-shield, and the price signal does not.

**Either way**, we suggest LTA model the Category C price response rather
than holding it flat — the +11.11% quota relief under removal is worth
something in C prices, and the current flat assumption is a documented upper
bound on C revenue, not an estimate.

## 3. Any other suggestions?

**3.1 Expect boundary bunching, and build the annual review for it.** With
≈14% of the mix within ±5% of a cut point and a ~10:1 payoff on crossing,
registrations will pile up just below the boundaries once the scheme is live.
That bunching shifts the very percentiles the cut points are defined from.
The annual review should re-derive cut points knowing the mix has been
distorted by the policy — and should report the bunching as a documented,
expected artefact rather than as a data quality issue.

**3.2 State the directional used-car effects in the response.** Three
directional (not quantified — no usable data) effects are worth naming:
upper-band new cars become relatively more expensive, making used cars
directionally more attractive in high-OMV segments; the renewal net-rebate
makes holding and renewing older low-OMV cars directionally cheaper; and
E-removal pushes time-constrained buyers directionally toward used cars.

**3.3 State the intended effective date.** The consultation closes 2 Nov 2026
with LTA's findings due in 1H2027, so a 1 Jan 2027 start is not feasible and
a real start is 2H2027 or 2028. Because the transition-year renewal cohort
(and its cost, section 1.5) depends on the start date, the response should
commit to a date rather than leaving it open.

**3.4 Keep the feebate revenue in proportion.** Even at the top of its range
(S$139M/yr base case including E-shifted demand), the feebate is modest next
to the renewal question (a five-figure cost in the first transition year if
applied to renewals) and next to the Category C revenue it would move
(S$761.87M/yr under removal). The consultation's findings should be
weighted accordingly.

---

## 4. Closing note

We support the direction of the proposal: the merge is a low-risk
administrative consolidation at today's prices, and a value-based
differentiation between mass-market and higher-value cars is a sensible
response to the narrowing A/B price gap. The comments above are about making
the details robust: fix the banding tables, pin the cut-point recipe, soften
the boundaries, specify the renewal treatment and reference year, be
explicit about Category E's fast lane, and state the effective date.

Every number in this response is reproducible from the public repository
<https://github.com/thongsia/coe-recategorization> — raw data, tables, code,
and the verification suite — and we are happy to walk LTA through any
derivation.
