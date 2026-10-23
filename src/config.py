"""
Single source of truth for the COE categorisation study (batch A, Steps 1-2).

Every downstream module imports from this file so that scenario tags,
data-window tags, and PROPOSED-vs-COMPUTED markers stay consistent across
tables, charts, and the report. Do NOT hardcode labels, paths, or parameter
values anywhere else.

Repository root: the directory containing src/ (this file's parent's
parent). All paths resolve relative to it, so the pipeline re-runs in
any clone of the repo.
Study: LTA public consultation on COE categorisation for cars
(8 Oct - 2 Nov 2026): (1) merge Category A + Category B into one
passenger-car category with a value-based fee-and-rebate ("feebate")
system; (2) review of Category E treatment.
"""
from __future__ import annotations

import os
from datetime import date
from typing import Dict, List, Optional

# ======================================================================
# 1. WORKSPACE
# ======================================================================
# Repo root = parent of src/ (this file). Relative to it, the pipeline
# re-runs in any clone.
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DIR_SRC = os.path.join(WORKSPACE_ROOT, "src")
DIR_DATA_RAW = os.path.join(WORKSPACE_ROOT, "data", "raw")
DIR_DATA_PROCESSED = os.path.join(WORKSPACE_ROOT, "data", "processed")
DIR_TABLES = os.path.join(WORKSPACE_ROOT, "tables")
DIR_CHARTS = os.path.join(WORKSPACE_ROOT, "charts")
DIR_DOCS = os.path.join(WORKSPACE_ROOT, "docs")
DIR_VERIFICATION = os.path.join(WORKSPACE_ROOT, "verification")

# Local documents (already in workspace; re-extract from these, never /tmp)
DOC_CONSULT_PAPER = os.path.join(DIR_DOCS, "consult_paper.pdf")
DOC_ANNEX_B = os.path.join(DIR_DOCS, "annex_b.pdf")
DOC_ANNEX_C = os.path.join(DIR_DOCS, "annex_c.pdf")
DOC_CAR_COST_AUG2026 = os.path.join(DIR_DOCS, "car_cost_aug2026.pdf")

# ======================================================================
# 2. METHOD PRECEDENT
# ======================================================================
# This study reuses the method precedent of the earlier coe-ev-rebate
# study (HAC errors, negative controls, graded evidence ratings). The
# precedent is documented in docs/methodology_notes.md; the repo has no
# runtime dependency on the other study's files.

# ======================================================================
# 3. DATA.GOV.SG
# ======================================================================
# Verified working endpoint (2026-10-22 probe). Versioned endpoints
# api.data.gov.sg/v1 and /v3 are DEAD - do not use.
DATA_GOVSG_API_ENDPOINT = "https://data.gov.sg/api/action/datastore_search"
DATA_GOVSG_MAX_ROWS_PER_REQUEST = 500  # large single fetches return HTTP 413

RESOURCES: Dict[str, str] = {
    # COE bidding results: ~1,990 rows, 2010 -> 2026-10;
    # fields: month, bidding_no, vehicle_class, quota, bids_success,
    #         bids_received, premium
    "coe_bids": "d_69b3380ad7e51aff3a7dcc84eba52b8a",
    # Vehicle registrations: ~51,669 rows, FROZEN at 2025-05;
    # fields: month, make, importer_type, fuel_type, vehicle_type, number
    "registrations": "d_d3f4d708e1d0a37b4365414e2fad3a07",
    # CPI (optional context only)
    "cpi": "d_bdaff844e3ef89d39fceb962ff8f0791",
}

# LTA OneMotoring (published PQP, historical Car Cost editions)
LTA_ONEMOTORING = "https://onemotoring.lta.gov.sg"

# ======================================================================
# 4. REGIME-START ANCHOR AND TRANSITION-YEAR VINTAGE
# ======================================================================
# Default: 2027-01. Consultation closes 2 Nov 2026; LTA findings expected
# 1H2027, so a new regime could plausibly start at the first bidding
# exercise of the new year. If the paper/annexes state an explicit
# implementation/effective date, REGIME_START_SOURCE will carry that
# citation instead; see methodology_notes.md.
REGIME_START_DATE = date(2027, 1, 1)
REGIME_START_SOURCE = (
    "default 2027-01 + reason: consultation closes 2 Nov 2026, LTA findings "
    "expected 1H2027, no explicit implementation date found in paper/annexes "
    "(see methodology_notes.md)"
)

# 10-year initial COE term: first-renewal cohort vintage = start year - 10.
INITIAL_COE_TERM_YEARS = 10


def transition_year_vintage(regime_start: Optional[date] = None) -> int:
    """First-renewal cohort vintage = regime start year - 10 (about 2017
    under the 2027-01 default). The vintage year marks registrations whose
    10-year initial COE term expires in the transition year."""
    rs = regime_start or REGIME_START_DATE
    return rs.year - INITIAL_COE_TERM_YEARS


TRANSITION_YEAR_VINTAGE = transition_year_vintage()  # 2017 under default

# The vintage - 1 cohort (about 2016) renews in 2026, BEFORE the regime
# starts: it is entirely pre-regime and is EXCLUDED from first-renewal-
# cycle analysis (usable as pre-regime context only).
PRE_REGIME_RENEWAL_VINTAGE = TRANSITION_YEAR_VINTAGE - 1  # 2016

# ======================================================================
# 5. DATA WINDOW / FREEZE
# ======================================================================
# Vehicle registration data on data.gov.sg is frozen at 2025-05.
# Every mix-based estimate uses the 2025-01..2025-05 window and must carry
# this data-window tag in every output.
REGISTRATION_FREEZE_MONTH = "2025-05"
REGISTRATION_MIX_WINDOW = "2025-01..2025-05"  # frozen window used for mix


def data_window_tag() -> str:
    """Standard data-window stamp for mix-based outputs
    (output_label() adds the 'data: ' prefix itself)."""
    return f"{REGISTRATION_MIX_WINDOW} (frozen at {REGISTRATION_FREEZE_MONTH})"


# ======================================================================
# 6. PROPOSED FEEBATE PARAMETERS (from consultation paper; cited in
#    tables/consultation_parameters.csv - never re-invented here)
# ======================================================================
# Option A: 3 bands, cut points at 35th / 50th OMV percentiles of 2025
# registrations.
FEEBATE_QUANTUMS_OPTION_A = [-15000, 0, 15000]
FEEBATE_PERCENTILES_OPTION_A = [35, 50]
# Option B: 5 bands, cut points at 10th / 35th / 50th / 75th OMV percentiles.
FEEBATE_QUANTUMS_OPTION_B = [-15000, -7500, 0, 7500, 15000]
FEEBATE_PERCENTILES_OPTION_B = [10, 35, 50, 75]

# PQP definition used for scenario derivation: 3-month moving average of
# the scenario merged-car price series (validated vs published PQP if
# fetchable in Step 4; else internal consistency only).
PQP_WINDOW_MONTHS = 3

# Category E options under review (per paper): "E removed" vs "E cars-only".
CATEGORY_E_OPTIONS = ["E_removed", "E_cars_only"]

# Open question in the consultation: whether renewal fees also apply the
# feebate (renewal feebate toggle: no/yes). Affects renewal quanta only -
# never the COE price path.
RENEWAL_FEEBATE_TOGGLE = ["renewal_feebate_no", "renewal_feebate_yes"]

# ======================================================================
# 7. MASTER SCENARIO MATRIX (8 cells)
# ======================================================================
FEEBATE_OPTIONS = ["OptionA", "OptionB"]


def master_matrix_cells() -> List[str]:
    """All 8 scenario cells: {Option A, B} x {E removed, cars-only} x
    {renewal feebate no, yes}. The two cells differing only in the
    renewal-feebate toggle share the identical price path (PQP/quantum
    toggle affects renewal quanta only)."""
    cells = []
    for opt in FEEBATE_OPTIONS:
        for e in CATEGORY_E_OPTIONS:
            for rf in RENEWAL_FEEBATE_TOGGLE:
                cells.append(f"{opt}+{e}+{rf}")
    return cells


MASTER_MATRIX_CELLS = master_matrix_cells()

# Spec-gaming zone width: +/-5% OMV around each band cut-off. Documented
# analytical choice, NOT an LTA parameter.
GAMING_ZONE_WIDTH_PCT = 5.0

# ======================================================================
# 8. LABEL HELPERS - stamp every output
# ======================================================================
# Conventions:
#   PROPOSED   - parameter as stated by LTA in the consultation paper
#                (cited to section/annex; never re-invented).
#   COMPUTED   - value derived in this study (scenario estimate unless
#                marked OBSERVED).
#   OBSERVED   - actual historical value from a fetched source.
#   SCENARIO   - forward-looking estimate under stated assumptions.
TYPE_PROPOSED = "PROPOSED"
TYPE_COMPUTED = "COMPUTED"
TYPE_OBSERVED = "OBSERVED"
TYPE_SCENARIO = "SCENARIO"
# Added in Batch G (Step 14d): directional-only statements where NO usable
# data exist to compute a number (used-car channel). Never carries a value.
TYPE_DIRECTIONAL = "DIRECTIONAL"


def output_label(
    value_type: str,
    scenario: Optional[str] = None,
    data_window: Optional[str] = None,
    citation: Optional[str] = None,
) -> str:
    """Build a standard label stamp for any output row/cell/figure title.

    Examples:
      output_label("PROPOSED", citation="Paper s.3.2")
      -> "PROPOSED | citation: Paper s.3.2"

      output_label("SCENARIO", scenario="OptionA+E_removed+renewal_feebate_no",
                   data_window=data_window_tag())
      -> "SCENARIO | scenario: OptionA+E_removed+renewal_feebate_no |
         data:2025-01..2025-05 (frozen at 2025-05) | regime_start: 2027-01 |
         vintage: 2017"

    Raises ValueError on an unknown value_type.
    """
    if value_type not in (TYPE_PROPOSED, TYPE_COMPUTED, TYPE_OBSERVED, TYPE_SCENARIO, TYPE_DIRECTIONAL):
        raise ValueError(
            f"Unknown value_type {value_type!r}; expected one of "
            f"{(TYPE_PROPOSED, TYPE_COMPUTED, TYPE_OBSERVED, TYPE_SCENARIO, TYPE_DIRECTIONAL)}"
        )
    parts = [value_type]
    if scenario:
        parts.append(f"scenario: {scenario}")
    if data_window:
        parts.append(f"data: {data_window}")
    if value_type in (TYPE_SCENARIO, TYPE_COMPUTED, TYPE_DIRECTIONAL):
        # Scenario/computed outputs carry the regime anchor + vintage.
        parts.append(f"regime_start: {REGIME_START_DATE.isoformat()}")
        parts.append(f"vintage: {TRANSITION_YEAR_VINTAGE}")
    if citation:
        parts.append(f"citation: {citation}")
    return " | ".join(parts)


def csv_label_columns() -> List[str]:
    """Extra columns that every deliverable table must carry."""
    return ["label", "value_type", "scenario", "data_window", "citation"]


# ======================================================================
# 9. SPOT-CHECK REFERENCE VALUES (verified live 2026-10-22; used by
#    downstream verification, not by this batch's modeling)
# ======================================================================
COE_SPOT_VALUES_2026_10 = {
    "b1": {"A": 130001, "B": 130100, "C": 91889, "D": 11012, "E": 137000},
    "b2": {"A": 132004, "B": 131901, "E": 135790},
}
# Per-bidding inversions where A cleared ABOVE B (observed 2026):
A_GT_B_INVERSIONS_2026 = [
    ("2026-02", "b2"),
    ("2026-04", "b2"),
    ("2026-06", "b2"),
    ("2026-10", "b2"),
]

# ======================================================================
# 10. RUN METADATA
# ======================================================================
BATCH = "A (Steps 1-2)"
BATCH_DATE = "2026-10-22"
STUDY_SCOPE = (
    "LTA public consultation (8 Oct - 2 Nov 2026) on COE categorisation "
    "for cars: merge Category A + B into one passenger-car category with a "
    "value-based feebate; review of Category E treatment."
)


def ensure_dirs() -> None:
    """Create the module layout if missing (idempotent)."""
    for d in (
        DIR_SRC, DIR_DATA_RAW, DIR_DATA_PROCESSED,
        DIR_TABLES, DIR_CHARTS, DIR_DOCS, DIR_VERIFICATION,
    ):
        os.makedirs(d, exist_ok=True)


if __name__ == "__main__":
    # Smoke test for the label helpers.
    ensure_dirs()
    print("WORKSPACE_ROOT:", WORKSPACE_ROOT)
    print("REGIME_START_DATE:", REGIME_START_DATE.isoformat())
    print("REGIME_START_SOURCE:", REGIME_START_SOURCE)
    print("TRANSITION_YEAR_VINTAGE:", TRANSITION_YEAR_VINTAGE)
    print("PRE_REGIME_RENEWAL_VINTAGE:", PRE_REGIME_RENEWAL_VINTAGE)
    print("MASTER_MATRIX_CELLS:", MASTER_MATRIX_CELLS)
    print()
    print("sample PROPOSED:", output_label(TYPE_PROPOSED, citation="Paper s.3.2"))
    print()
    print("sample SCENARIO:", output_label(
        TYPE_SCENARIO,
        scenario="OptionA+E_removed+renewal_feebate_no",
        data_window=data_window_tag(),
    ))
    print()
    print("sample OBSERVED:", output_label(TYPE_OBSERVED, citation="data.gov.sg coe_bids"))
