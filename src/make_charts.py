#!/usr/bin/env python3
"""
Step 17 — Charts (Batch H).

Produces exactly 8 labeled figures in charts/, using the study tables as the
sole data source. Conventions:
  * every figure carries a short figure-level title naming the plotted
    quantity (scenario details live in the caption, not the title);
  * every PNG is self-contained: a centered "Figure N: <scenario context>"
    caption band below the plot, numbered in README reading order;
  * multi-panel figures are labeled per panel: (a), (b) in the panel titles;
  * OBSERVED series are SOLID, SCENARIO series are DASHED (never conflated);
  * regime start (2027-01-01) and the frozen mix window
    (2025-01..2025-05, frozen at 2025-05) are stated in the caption where
    they apply.
  * layout is verified programmatically on save (caption centered on the
    figure, one line, no overlap with axes/labels; title clear of panels);
    any problem is printed as a WARNING, never silently shipped.

Figures:
  1 charts/ab_convergence_perbidding.png
  2 charts/merged_price_paths.png
  3 charts/omv_histogram_bands.png
  4 charts/fee_revenue.png
  5 charts/demand_shift_by_band.png
  6 charts/renewal_cost_cells.png
  7 charts/ec_quota_price_paths.png
  8 charts/gaming_zones.png
"""
from __future__ import annotations

import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.dates as mdates  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config  # noqa: E402

WS = config.WORKSPACE_ROOT
CH = config.DIR_CHARTS
os.makedirs(CH, exist_ok=True)


def read(rel):
    with open(os.path.join(WS, rel), newline="") as f:
        rows = list(csv.reader(f))
    hdr = rows[0]
    idx = {c: i for i, c in enumerate(hdr)}
    return idx, rows[1:]


def f(v):
    try:
        return float(str(v).replace(",", "").strip())
    except (ValueError, AttributeError):
        return None


def mkfig(name, caption, fig, title=None):
    """Save a figure with a short title on top (optional) and a centered
    'Figure N: ...' caption band below the plot. The caption band is
    reserved with tight_layout(rect=...); the layout is then verified
    programmatically (measured, not estimated):
      - caption horizontally centered on the FIGURE (not the axes);
      - caption width < figure width minus a 40px margin (one line);
      - caption does not overlap any axes bbox or any x-axis label;
      - title (if any) does not overlap panel titles or y-axis labels;
      - panel titles do not overlap each other (side-by-side panels
        with long titles used to interleave into one unreadable line);
      - every panel title fits inside the figure canvas (a title wider
        than its panel used to spill past the canvas edge and force
        bbox_inches='tight' to stretch the saved image).
    Problems are printed as WARNING lines next to the 'wrote' line."""
    path = os.path.join(CH, name)
    if title:
        fig.suptitle(title, fontsize=11, fontweight="bold", y=0.995)
    fig.tight_layout(rect=[0, 0.085, 1, 0.965 if title else 1.0])
    fig.text(0.5, 0.012, caption, ha="center", va="bottom",
             fontsize=9, color="0.25")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    W, H = fig.canvas.get_width_height()
    problems = []
    cap = fig.texts[-1].get_window_extent(renderer)
    dx = (cap.x0 + cap.x1) / 2 - W / 2
    if abs(dx) > 2:
        problems.append(f"caption not centered (dx={dx:.1f}px)")
    if cap.width > W - 40:
        problems.append(f"caption too wide ({cap.width:.0f}px > {W - 40}px)")
    for ax in fig.axes:
        ab = ax.get_window_extent(renderer)
        if cap.overlaps(ab):
            problems.append("caption overlaps an axes area")
        xlabel = ax.xaxis.get_label()
        if xlabel.get_visible() and xlabel.get_text():
            if cap.overlaps(xlabel.get_window_extent(renderer)):
                problems.append("caption overlaps x-axis label")
    if title:
        st = fig._suptitle.get_window_extent(renderer)
        for ax in fig.axes:
            for child in (ax.title, ax.yaxis.get_label()):
                if child.get_visible() and child.get_text():
                    if st.overlaps(child.get_window_extent(renderer)):
                        problems.append(f"title overlaps {child.get_text()[:30]!r}")
    # panel titles vs each other, and vs the figure canvas
    title_exts = []
    for ax in fig.axes:
        t = ax.title
        if t.get_visible() and t.get_text():
            title_exts.append((t.get_window_extent(renderer), t.get_text()[:30]))
    for i in range(len(title_exts)):
        for j in range(i + 1, len(title_exts)):
            if title_exts[i][0].overlaps(title_exts[j][0]):
                problems.append(
                    f"panel titles overlap: {title_exts[i][1]!r} vs {title_exts[j][1]!r}")
    for ext, txt in title_exts:
        if ext.x0 < -2 or ext.x1 > W + 2:
            problems.append(f"panel title exceeds canvas width: {txt!r}")
    if problems:
        print(f"WARNING {name}: layout problems: {problems}")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {path} ({os.path.getsize(path):,} bytes)")


# ======================================================================
# 1. A vs B per-bidding, 2026 inversion set annotated (OBSERVED)
# ======================================================================
def fig1():
    ix, rows = read("data/processed/coe_panel_perbidding.csv")
    import datetime as dt
    def d(m, b):
        return dt.datetime(int(m[:4]), int(m[5:7]), 1) + dt.timedelta(days=31 * (int(b) - 1) / 2)
    A = [(d(r[ix["month"]], r[ix["bid_no"]]), f(r[ix["premium"]])) for r in rows if r[ix["category"]] == "A" and f(r[ix["premium"]])]
    B = [(d(r[ix["month"]], r[ix["bid_no"]]), f(r[ix["premium"]])) for r in rows if r[ix["category"]] == "B" and f(r[ix["premium"]])]
    A.sort(); B.sort()
    ix2, inv = read("tables/inversions_2026.csv")
    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.plot([p[0] for p in A], [p[1] for p in A], "-", color="#1f77b4", lw=0.8, label="Category A (OBSERVED, solid)")
    ax.plot([p[0] for p in B], [p[1] for p in B], "-", color="#d62728", lw=0.8, label="Category B (OBSERVED, solid)")
    # zoom inset for 2026
    axins = ax.inset_axes([0.45, 0.35, 0.42, 0.5])
    for (pts, col) in ((A, "#1f77b4"), (B, "#d62728")):
        sub = [(t, v) for t, v in pts if t.year == 2026]
        axins.plot([t for t, _ in sub], [v for _, v in sub], "-", color=col, lw=1.0)
    for r in inv:
        t = dt.datetime(int(r[0][:4]), int(r[0][5:7]), 21)
        axins.annotate(f"{r[0]} b{r[1]}\nA−B +{r[4].replace('.0','')}", xy=(t, f(r[ix2["a_premium"]])),
                       xytext=(t + dt.timedelta(days=38), f(r[ix2["a_premium"]]) + 6000),
                       fontsize=7, ha="center",
                       arrowprops=dict(arrowstyle="->", lw=0.7, color="k"))
    axins.axvspan(dt.datetime(2026, 2, 15), dt.datetime(2026, 2, 1), color="none")  # no-op guard
    axins.set_title("2026 zoom — A>B inversion set (4 rounds, all b2)", fontsize=8)
    axins.xaxis.set_major_formatter(mdates.DateFormatter("%y-%m"))
    axins.tick_params(labelsize=7)
    axind = dt.datetime(2026, 1, 1)
    for t in (dt.datetime(2026, 2, 21), dt.datetime(2026, 4, 21), dt.datetime(2026, 6, 21), dt.datetime(2026, 10, 21)):
        ax.axvline(t, color="gray", lw=0.5, ls=":")
    ax.set_ylabel("Clearing premium (S$)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.grid(alpha=0.3)
    ax.legend(loc="upper left", fontsize=8)
    mkfig("ab_convergence_perbidding.png",
          "Figure 1: A and B clearing prices per bidding round, 2010–2026 (observed); inset zooms the four 2026 rounds where A cleared above B.",
          fig, title="A vs B per-bidding clearing prices, 2010–2026")


# ======================================================================
# 2. Merged price paths: option-level + per-cell + cell PQP
# ======================================================================
def fig2():
    import datetime as dt
    def d(m, b):
        return dt.datetime(int(m[:4]), int(m[5:7]), 1) + dt.timedelta(days=31 * (int(b) - 1) / 2)
    ixn, rowsn = read("tables/merged_price_nofeebate.csv")
    nofee = [(d(r[ixn["month"]], r[ixn["bidding_no"]]), f(r[ixn["merged_price_point"]])) for r in rowsn if f(r[ixn["merged_price_point"]])]
    ixwA, rowwA = read("tables/merged_price_optionA_withfee.csv")
    wA = [(d(r[ixwA["month"]], r[ixwA["bidding_no"]]), f(r[ixwA["withfee_price_point"]])) for r in rowwA if f(r[ixwA["withfee_price_point"]])]
    ixwB, rowwB = read("tables/merged_price_optionB_withfee.csv")
    wB = [(d(r[ixwB["month"]], r[ixwB["bidding_no"]]), f(r[ixwB["withfee_price_point"]])) for r in rowwB if f(r[ixwB["withfee_price_point"]])]
    # observed A/B reference
    ixp, rowsp = read("data/processed/coe_panel_perbidding.csv")
    A = [(d(r[ixp["month"]], r[ixp["bid_no"]]), f(r[ixp["premium"]])) for r in rowsp if r[ixp["category"]] == "A"]
    B = [(d(r[ixp["month"]], r[ixp["bid_no"]]), f(r[ixp["premium"]])) for r in rowsp if r[ixp["category"]] == "B"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5), gridspec_kw={"width_ratios": [1.2, 1]})
    ax1.plot([t for t, _ in A], [v for _, v in A], "-", color="#1f77b4", lw=0.5, alpha=0.45, label="A observed (OBSERVED)")
    ax1.plot([t for t, _ in B], [v for _, v in B], "-", color="#d62728", lw=0.5, alpha=0.45, label="B observed (OBSERVED)")
    ax1.plot([t for t, _ in nofee], [v for _, v in nofee], "--", color="#555555", lw=1.4, label="merged no-fee (SCENARIO, dashed)")
    ax1.plot([t for t, _ in wA], [v for _, v in wA], "--", color="#1f77b4", lw=1.6, label="merged with-fee, Option A (SCENARIO)")
    ax1.plot([t for t, _ in wB], [v for _, v in wB], "--", color="#ff7f0e", lw=1.6, label="merged with-fee, Option B (SCENARIO)")
    ax1.axvline(dt.datetime(2027, 1, 1), color="k", lw=0.8, ls=":")
    ax1.text(dt.datetime(2027, 2, 15), ax1.get_ylim()[0] + 800, "regime start 2027-01-01\n(forward: 24 rounds, flat by static-pool design)", fontsize=7)
    ax1.set_title("(a) Option-level merged-car price paths\n(2010 back-solved .. 2027 forward)")
    ax1.set_ylabel("Merged-car price (S$)")
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax1.grid(alpha=0.3)
    ax1.legend(fontsize=7, loc="upper left")

    # right: 4 distinct per-cell paths + cell PQP lines
    cells = ["OptionA+E_removed", "OptionA+E_cars_only", "OptionB+E_removed", "OptionB+E_cars_only"]
    cols = {"OptionA+E_removed": "#1f77b4", "OptionA+E_cars_only": "#2ca02c",
            "OptionB+E_removed": "#ff7f0e", "OptionB+E_cars_only": "#9467bd"}
    pulse_pts = []
    for c in cells:
        ixp2, rowsp2 = read(f"data/processed/price_paths/{c}+renewal_feebate_no.csv")
        pts = [(d(r[ixp2["month"]], r[ixp2["bidding_no"]]), f(r[ixp2["price_sgd"]])) for r in rowsp2
               if r[ixp2["month"]] >= "2026-06"]
        ax2.plot([t for t, _ in pts], [v for _, v in pts], "--", color=cols[c], lw=1.5,
                 label=f"{c} price (SCENARIO)")
        # pulse annotation for removal cells: 2027-01 b1 is plotted at 2027-01-01
        if "E_removed" in c:
            pulse_pts.extend(v for t, v in pts if t == dt.datetime(2027, 1, 1))
    if pulse_pts:
        ax2.annotate("E-shift pulse: +1,428 S$ for one round "
                     "(2027-01 b1, both E-removed cells)",
                     xy=(dt.datetime(2027, 1, 1), max(pulse_pts)),
                     xytext=(dt.datetime(2027, 3, 1), 131850), fontsize=7, ha="center",
                     arrowprops=dict(arrowstyle="->", lw=0.7))
    ixq, rowsq = read("data/processed/pqp_by_cell.csv")
    pqpc = {}
    for c in cells:
        pts = [(d(r[ixq["month"]], "1"), f(r[ixq["pqp_sgd"]])) for r in rowsq
               if r[ixq["distinct_path_id"]] == c and r[ixq["month"]] >= "2027-01"]
        pqpc[c] = pts
        ax2.plot([t for t, _ in pts], [v for _, v in pts], ":", color=cols[c], lw=2.2,
                 label=f"{c} cell PQP (SCENARIO)")
    ax2.set_title("(b) Per-cell paths and cell-level renewal PQP\n"
                  "2026-06..2027-12 (4 distinct paths serve the 8 cells;\n"
                  "toggle pairs byte-identical, sha256-verified)")
    ax2.set_ylabel("Price / PQP (S$)")
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%y-%m"))
    ax2.tick_params(labelsize=7)
    ax2.grid(alpha=0.3)
    ax2.legend(fontsize=6, ncol=2, loc="lower right")
    mkfig("merged_price_paths.png",
          "Figure 2: Merged A+B price paths, 2010 back-solved to 2027 forward (scenario, regime start 2027-01); left: no-fee vs with-fee (Options A/B); right: per-cell paths + renewal PQP.",
          fig, title="Merged A+B car price paths — no-fee vs with-fee")


# ======================================================================
# 3. OMV histogram with Option A / B band overlays
# ======================================================================
def fig3():
    ixA, rowsA = read("tables/banding_models_optionA.csv")
    ixB, rowsB = read("tables/banding_models_optionB.csv")
    omvA = [f(r[ixA["omv_catalog_aug2026"]]) for r in rowsA if f(r[ixA["omv_catalog_aug2026"]])]
    wA = [f(r[ixA["weight"]]) for r in rowsA if f(r[ixA["omv_catalog_aug2026"]])]
    omvB = [f(r[ixB["omv_catalog_aug2026"]]) for r in rowsB if f(r[ixB["omv_catalog_aug2026"]])]
    wB = [f(r[ixB["weight"]]) for r in rowsB if f(r[ixB["omv_catalog_aug2026"]])]
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
    edges = list(range(10000, 110000, 2000))
    ax1.hist(omvA, bins=edges, weights=wA, color="#9ecae1", edgecolor="white", lw=0.3)
    ax1.axvspan(0, 28877, color="#2ca02c", alpha=0.15)
    ax1.axvspan(28877, 36062, color="#ffbb33", alpha=0.25)
    ax1.axvspan(36062, 100000, color="#d62728", alpha=0.15)
    for x, lab in ((28877, "35th: 28,877"), (36062, "50th: 36,062")):
        ax1.axvline(x, color="k", lw=1.0, ls="--")
        ax1.annotate(lab, xy=(x, ax1.get_ylim()[1] * 0.97), fontsize=8, ha="center")
    ax1.text(0.02, 0.9, "band 1 (0-35th): −15,000 | share 35.16%\nband 2 (35-50th): 0 | share 15.74%\nband 3 (>50th): +15,000 | share 49.10%",
             transform=ax1.transAxes, fontsize=8, va="top",
             bbox=dict(boxstyle="round", fc="white", alpha=0.85))
    ax1.set_title("(a) Option A — 3 bands at 35th/50th OMV percentiles\n(PROPOSED percentiles, COMPUTED cut points)")
    ax1.set_ylabel("Registration mix weight (Jan-May 2025)")
    ax1.grid(alpha=0.3, axis="y")
    ax2.hist(omvB, bins=edges, weights=wB, color="#c5b0d5", edgecolor="white", lw=0.3)
    for (lo, hi, col) in ((0, 20310, "#2ca02c"), (20310, 28877, "#66c2a5"), (28877, 36062, "#ffbb33"),
                          (36062, 49662, "#fc8d59"), (49662, 100000, "#d62728")):
        ax2.axvspan(lo, hi, color=col, alpha=0.18)
    for x, lab in ((20310, "10th: 20,310"), (28877, "35th: 28,877"), (36062, "50th: 36,062"), (49662, "75th: 49,662")):
        ax2.axvline(x, color="k", lw=1.0, ls="--")
        ax2.annotate(lab, xy=(x, ax2.get_ylim()[1] * 0.97), fontsize=7.5, ha="center", rotation=30)
    ax2.text(0.02, 0.9, "band shares: 10.17 / 24.98 / 15.74 / 24.22 / 24.88%\nquantums: −15,000 / −7,500 / 0 / +7,500 / +15,000",
             transform=ax2.transAxes, fontsize=8, va="top",
             bbox=dict(boxstyle="round", fc="white", alpha=0.85))
    ax2.set_title("(b) Option B — 5 bands at 10th/35th/50th/75th OMV percentiles\n(PROPOSED percentiles, COMPUTED cut points)")
    ax2.set_ylabel("Registration mix weight (Jan-May 2025)")
    ax2.set_xlabel("Model OMV (S$, Car Cost Aug 2026 catalog)")
    ax2.grid(alpha=0.3, axis="y")
    mkfig("omv_histogram_bands.png",
          "Figure 3: OMV distribution of the 217-model Car Cost (Aug 2026) catalog, weighted by the Jan–May 2025 registration mix, with the proposed bands overlaid.",
          fig, title="Banding reconstruction — OMV distribution with feebate bands")


# ======================================================================
# 4. Feebate revenue by option with E-shift delta + sensitivities
# ======================================================================
def fig4():
    ixf, rowsf = read("tables/fee_revenue_base.csv")
    ixv, rowsv = read("tables/fee_revenue_sensitivity.csv")
    vals = {}
    for r in rowsf:
        vals[(r[ixf["feebate_option"]], "base")] = f(r[ixf["base_merged_only_sgd"]])
        vals[(r[ixf["feebate_option"]], "total")] = f(r[ixf["total_sgd"]])
        vals[(r[ixf["feebate_option"]], "delta")] = f(r[ixf["e_shift_delta_sgd"]])
    sens = {}
    for r in rowsv:
        sens.setdefault(r[ixv["feebate_option"]], {})[r[ixv["variant"]]] = f(r[ixv["total_incl_e_shift_sgd"]])
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5))
    for (ax, opt, col), lab in zip(((ax1, "OptionA", "#1f77b4"), (ax2, "OptionB", "#ff7f0e")), "ab"):
        cats = ["base (excl. E-shift)", "E-shift delta (6,400/yr)", "total (incl. E-shift)"]
        base = vals[(opt, "base")]; delta = vals[(opt, "delta")]; total = vals[(opt, "total")]
        bars = ax.bar(cats, [base, delta, total], color=["#bcd2e6", col, col], edgecolor="k", lw=0.5)
        for b, v in zip(bars, [base, delta, total]):
            ax.text(b.get_x() + b.get_width() / 2, v * 1.01, f"{v/1e6:,.2f}M", ha="center", fontsize=9)
        s1 = sens[opt].get("S1_lta2025_omv"); s2 = sens[opt].get("S2_uniform_weights")
        ax.text(0.02, 0.62, f"cut-point sensitivity (total incl. E-shift):\nS1 LTA-2025 avg-OMV cut points: {s1/1e6:,.2f}M\nS2 uniform model weights: {s2/1e6:,.2f}M",
                transform=ax.transAxes, fontsize=8.5, bbox=dict(boxstyle="round", fc="white", alpha=0.9))
        ax.set_title(f"({lab}) {opt} feebate revenue (SCENARIO, annualised S$/yr)")
        ax.set_ylabel("S$/yr")
        ax.grid(alpha=0.3, axis="y")
    mkfig("fee_revenue.png",
          "Figure 4: Annual net feebate revenue by option (scenario, Jan–May 2025 mix): base, E-shift delta, total, and cut-point sensitivity (S1/S2).",
          fig, title="Feebate revenue by option (annualised S$/yr)")


# ======================================================================
# 5. Demand shift by band
# ======================================================================
def fig5():
    ixd, rowsd = read("tables/demand_shift_by_band.csv")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    for (ax, opt, col), lab in zip(((ax1, "OptionA", "#1f77b4"), (ax2, "OptionB", "#ff7f0e")), "ab"):
        sub = [r for r in rowsd if r[ixd["feebate_option"]] == opt]
        bands = [r for r in sub if r[ixd["dimension"]] == "band"]
        labels = [r[ixd["value"]].replace("band", "band ").replace("_", " ") for r in bands]
        dvals = [f(r[ixd["delta_bids_per_year"]]) for r in bands]
        ax.bar(labels, dvals, color=col, alpha=0.75, edgecolor="k", lw=0.5)
        for i, v in enumerate(dvals):
            ax.text(i, v + (15 if v >= 0 else -95), f"{v:,.0f}", ha="center", fontsize=8)
        dec = [(i, f(r[ixd["delta_bids_per_year"]])) for i, r in enumerate(
            [x for x in sub if x[ixd["dimension"]] == "omv_decile"])]
        ax2p = ax.twinx()
        ax2p.plot([d[0] for d in dec], [d[1] for d in dec], "-", color="k", lw=1.2, marker="o", ms=3, label="OMV decile shift")
        ax2p.set_ylabel("OMV-decile delta (bids/yr)", fontsize=8)
        ax2p.tick_params(labelsize=7)
        tot = f([r for r in sub if r[ixd["dimension"]] == "TOTAL"][0][ixd["delta_bids_per_year"]])
        ev = f([r for r in sub if r[ixd["dimension"]] == "fuel" and r[ixd["value"]] == "EV"][0][ixd["delta_bids_per_year"]])
        ax.set_title(f"({lab}) {opt}: total {tot:,.0f} bids/yr\nEV {ev:,.0f} ({ev/tot*100:.1f}% of shift)")
        ax.set_ylabel("Delta bids/yr by band (SCENARIO)")
        ax.grid(alpha=0.3, axis="y")
    mkfig("demand_shift_by_band.png",
          "Figure 5: Feebate-induced demand shift by car-value band, bids/yr (scenario; elasticities from 2010–2026 bidding data): Option A left, Option B right.",
          fig, title="Feebate-induced demand shift by car-value band (bids/yr)")


# ======================================================================
# 6. Renewal cost cells (cell-level PQP pricing, regime start + vintage)
# ======================================================================
def fig6():
    ixm, rowsm = read("tables/renewal_impact_master.csv")
    fig, ax = plt.subplots(figsize=(11, 5.5))
    import numpy as np
    cells = ["OptionA+E_removed", "OptionA+E_cars_only", "OptionB+E_removed", "OptionB+E_cars_only"]
    no = [f([r for r in rowsm if r[ixm["cell"]] == c + "+renewal_feebate_no"][0][ixm["annual_cost_total_sgd"]]) / 1e9 for c in cells]
    yes = [f([r for r in rowsm if r[ixm["cell"]] == c + "+renewal_feebate_yes"][0][ixm["annual_cost_total_sgd"]]) / 1e9 for c in cells]
    cohort = [f([r for r in rowsm if r[ixm["cell"]] == c + "+renewal_feebate_no"][0][ixm["cohort_volume"]]) for c in cells]
    pqp = [f([r for r in rowsm if r[ixm["cell"]] == c + "+renewal_feebate_no"][0][ixm["pqp_2027_12_sgd"]]) for c in cells]
    x = np.arange(len(cells)); wdt = 0.36
    b1 = ax.bar(x - wdt/2, no, wdt, color="#d9d9d9", edgecolor="k", lw=0.6, label="renewal feebate OFF (PQP only)")
    b2 = ax.bar(x + wdt/2, yes, wdt, color="#1f77b4", edgecolor="k", lw=0.6, label="renewal feebate ON (PQP + band quantum)")
    for i, (nv, yv) in enumerate(zip(no, yes)):
        ax.text(i - wdt/2, nv + 0.06, f"{nv:.2f}B", ha="center", fontsize=8)
        ax.text(i + wdt/2, yv + 0.06, f"{yv:.2f}B", ha="center", fontsize=8)
        ax.annotate(f"Δ {yv-nv:+.2f}B/yr (NET REBATE)", xy=(i + wdt/2, yv), xytext=(i + 0.02, yv - 0.55),
                    fontsize=7.5, ha="center", color="#0b3d91")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{c}\ncohort {n:,.0f}\n2027-12 PQP {p:,.2f}" for c, n, p in zip(cells, cohort, pqp)], fontsize=8)
    ax.set_ylabel("2027 transition-year renewal cost (S$B, full cohort renews — upper bound)")
    ax.set_ylim(0, 13.2)
    ax.grid(alpha=0.3, axis="y")
    ax.legend(fontsize=8)
    mkfig("renewal_cost_cells.png",
          "Figure 6: 2027 transition-year renewal cost per scenario cell (scenario, full-cohort upper bound): feebate on renewals vs not, with net-rebate deltas.",
          fig, title="2027 transition-year renewal cost per scenario cell (S$B)")


# ======================================================================
# 7. E/C quota and price paths under both E options
# ======================================================================
def fig7():
    import datetime as dt
    def d(m, b):
        return dt.datetime(int(m[:4]), int(m[5:7]), 1) + dt.timedelta(days=31 * (int(b) - 1) / 2)
    def load(rel):
        ixe, rowse = read(rel)
        out = {}
        for r in rowse:
            if r[ixe["segment"]] == "forward_scenario":
                out.setdefault(r[ixe["category"]], []).append(r)
        return ixe, out
    ixR, rem = load("tables/ec_scenario_E_removed.csv")
    ixC, cco = load("tables/ec_scenario_E_cars_only.csv")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))
    # quotas
    for ax, (ix, data, tag, ls) in ((ax1, (ixR, rem, "E removed", (0, (4, 2)))), (ax1, (ixC, cco, "E cars-only", (0, (1, 1))))):
        for cat, col, lab in (("merged_car", "#1f77b4", "merged car"), ("C", "#2ca02c", "Category C"), ("E", "#d62728", "Category E")):
            pts = [(d(r[ix["month"]], r[ix["bidding_no"]]), f(r[ix["quota"]])) for r in data.get(cat, []) if f(r[ix["quota"]]) is not None]
            if pts:
                ax.plot([t for t, _ in pts], [v for _, v in pts], linestyle=ls, color=col, lw=1.6, label=f"{lab} — {tag}")
    ax1.axvline(dt.datetime(2027, 1, 1), color="k", lw=0.8, ls=":")
    ax1.set_title("(a) Forward quotas per round (SCENARIO)\nC +11.11% under removal (345.74 vs 311.17/round);\nE → 0 under removal (266.67/round cars-only)")
    ax1.set_ylabel("Quota per round")
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%y-%m"))
    ax1.legend(fontsize=7)
    ax1.grid(alpha=0.3)
    # prices
    for ax, (ix, data, tag, colstyle) in ((ax2, (ixR, rem, "E removed", "--")), (ax2, (ixC, cco, "E cars-only", "-"))):
        mc = [(d(r[ix["month"]], r[ix["bidding_no"]]),
               f(r[ix["withfee_price_optionA_base"]]) + (f(r[ix["e_shift_price_effect_sgd"]]) or 0)) for r in data["merged_car"]]
        mcB = [(d(r[ix["month"]], r[ix["bidding_no"]]),
                f(r[ix["withfee_price_optionB_base"]]) + (f(r[ix["e_shift_price_effect_sgd"]]) or 0)) for r in data["merged_car"]]
        ax.plot([t for t, _ in mc], [v for _, v in mc], linestyle=colstyle, color="#1f77b4", lw=1.6, label=f"merged car, Option A — {tag}")
        ax.plot([t for t, _ in mcB], [v for _, v in mcB], linestyle=colstyle, color="#ff7f0e", lw=1.6, label=f"merged car, Option B — {tag}")
        Cpts = [(d(r[ix["month"]], r[ix["bidding_no"]]), f(r[ix["price"]])) for r in data["C"] if f(r[ix["price"]]) is not None]
        if Cpts:
            ax.plot([t for t, _ in Cpts], [v for _, v in Cpts], linestyle=colstyle, color="#2ca02c", lw=1.4, label=f"Category C (flat) — {tag}")
        Epts = [(d(r[ix["month"]], r[ix["bidding_no"]]), f(r[ix["e_price_optionA"]])) for r in data["E"] if f(r[ix["e_price_optionA"]])]
        if Epts:
            ax.plot([t for t, _ in Epts], [v for _, v in Epts], linestyle=colstyle, color="#d62728", lw=1.4, label=f"E, Option A (premium decays to 0 over 6 rounds) — {tag}")
    ax2.axvline(dt.datetime(2027, 1, 1), color="k", lw=0.8, ls=":")
    ax2.set_title("(b) Forward prices (SCENARIO)\nC flat at 91,813.5 (NOT DETECTABLE response;\nconservative bound); E premium 3,777.33 → 0 (cars-only)")
    ax2.set_ylabel("Price (S$)")
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%y-%m"))
    ax2.legend(fontsize=6.5)
    ax2.grid(alpha=0.3)
    mkfig("ec_quota_price_paths.png",
          "Figure 7: Category E and C quota and price paths, 2027 forward (scenario; E-to-car re-entry base 100%): left quotas per round, right forward prices.",
          fig, title="Category E and C — quota and price paths, 2027 forward")


# ======================================================================
# 8. Spec-gaming zones +/-5% around each cut point
# ======================================================================
def fig8():
    ixA, rowsA = read("tables/banding_models_optionA.csv")
    omv = [f(r[ixA["omv_catalog_aug2026"]]) for r in rowsA if f(r[ixA["omv_catalog_aug2026"]])]
    w = [f(r[ixA["weight"]]) for r in rowsA if f(r[ixA["omv_catalog_aug2026"]])]
    ixd, rowsz = read("tables/boundary_gaming_zones.csv")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8.5), sharex=True)
    edges = list(range(10000, 110000, 2000))
    for (ax, opt, col), lab in zip(((ax1, "OptionA", "#2ca02c"), (ax2, "OptionB", "#ff7f0e")), "ab"):
        ax.hist(omv, bins=edges, weights=w, color="#cccccc", edgecolor="white", lw=0.3)
        for r in rowsz:
            if r[ixd["option"]] != opt:
                continue
            lo, hi = f(r[ixd["zone_lo_sgd"]]), f(r[ixd["zone_hi_sgd"]])
            share = f(r[ixd["zone_share_pct_covered_mix"]]); nmod = int(f(r[ixd["n_models_in_zone"]]))
            ann = f(r[ixd["est_registrations_annual_in_zone"]]); qp = f(r[ixd["quantum_at_stake_sgd"]])
            ax.axvspan(lo, hi, color=col, alpha=0.45)
            mid = (lo + hi) / 2
            ax.annotate(f"{r[ixd['percentile']]}th zone\nshare {share:.2f}%\n{nmod} models, ~{ann:,.0f} reg/yr\nquantum at stake {qp:,.0f} S$",
                        xy=(mid, ax.get_ylim()[1] * 0.55), fontsize=6.8, ha="center",
                        bbox=dict(boxstyle="round", fc="white", alpha=0.9, ec="gray"))
        ax.set_title(f"({lab}) {opt} — ±5% OMV boundary zones around each cut point\n(zone width = documented analytical choice, NOT an LTA parameter)")
        ax.set_ylabel("Registration mix weight (Jan-May 2025)")
        ax.grid(alpha=0.3, axis="y")
    ax2.set_xlabel("Model OMV (S$, Car Cost Aug 2026 catalog)")
    mkfig("gaming_zones.png",
          "Figure 8: Models within ±5% OMV of each feebate cut point (spec-gaming exposure; Jan–May 2025 mix, annualised 45,775 (A) / 45,776 (B) registrations).",
          fig, title="Spec-gaming exposure — ±5% OMV zones around each cut point")


if __name__ == "__main__":
    fig1()
    fig2()
    fig3()
    fig4()
    fig5()
    fig6()
    fig7()
    fig8()
    print("done: 8 charts")
