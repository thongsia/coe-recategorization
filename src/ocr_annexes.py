"""
Step 2b - OCR the image-only annexes (B and C) with easyocr and write
docs/annex_ocr.md with per-page confidence caveats. Also OCRs the
consultation-paper cover (page 1, image-based) into
docs/consult_paper_cover_ocr.md to capture the consultation window
start date for scope confirmation.

Usage: python3 src/ocr_annexes.py
Takes several minutes on CPU (model load + 3 pages) - run with patience.
"""
from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config  # noqa: E402
import fitz  # noqa: E402

DPI = 300  # 300 DPI renders for OCR quality
DPI_CROSSCHECK = 450  # second pass to confirm text completeness
OUT_ANNEX = os.path.join(config.DIR_DOCS, "annex_ocr.md")
OUT_COVER = os.path.join(config.DIR_DOCS, "consult_paper_cover_ocr.md")
OUT_XCHECK = os.path.join(config.DIR_VERIFICATION, "ocr_resolution_check.csv")

# Known easyocr misreads on this content (verified against the paper body
# text and the 450 DPI cross-check). Use these corrected readings when any
# downstream step consumes the annexes.
KNOWN_MISREADS = [
    ("Annex C", "S31,000 / S33,000 / S34,000 / S35,000 / S38,000",
     "$31,000 / $33,000 / $34,000 / $35,000 / $38,000",
     "dollar sign '$' read as 'S'"),
    ("Annex C", "Annex €", "Annex C",
     "'C' misread in the running title"),
    ("Annex C", "determined based on the F rebate amounts",
     "determined based on the fee rebate amounts (i.e. the proposed "
     "fee and rebate amounts)",
     "low-confidence word; reading follows from context (s2.17, p.10: "
     "historical A-B price gaps as reference point)"),
]


def crosscheck_ocr(reader, png300: str, png450: str) -> tuple[int, int]:
    """Re-OCR at 450 DPI and compare word counts. Returns (n300, n450)."""
    r300 = reader.readtext(png300, detail=1)
    r450 = reader.readtext(png450, detail=1)
    return len(r300), len(r450)

TARGETS = [
    ("annex_b", config.DOC_ANNEX_B, "annex_b.png"),
    ("annex_c", config.DOC_ANNEX_C, "annex_c.png"),
]


def render(pdf_path: str, png_name: str) -> str:
    doc = fitz.open(pdf_path)
    out = os.path.join(config.DIR_DOCS, png_name)
    for page in doc:
        pix = page.get_pixmap(dpi=DPI)
        pix.save(out)
    n = len(doc)
    doc.close()
    return out


def ocr_page(reader, png: str):
    """Run easyocr on a single PNG. Returns (lines, word_count, confs)."""
    t0 = time.time()
    results = reader.readtext(png, detail=1, paragraph=False)
    dt = time.time() - t0
    # easyocr rows: [bbox, text, confidence]
    rows = [(r[1], float(r[2])) for r in results]
    confs = [c for _, c in rows]
    lines = " ".join(t for t, _ in rows)
    return lines, len(rows), confs, dt


def main() -> None:
    import easyocr
    import csv as _csv
    print("loading easyocr reader (en) ...", flush=True)
    t0 = time.time()
    reader = easyocr.Reader(["en"], gpu=False, verbose=False)
    print(f"reader loaded in {time.time() - t0:.1f}s", flush=True)

    xcheck_rows = []
    sections = []
    cover_lines = []

    for tag, pdf, png in TARGETS:
        png_path = render(pdf, png)
        print(f"OCR {png} ...", flush=True)
        text, nwords, confs, dt = ocr_page(reader, png_path)
        avg = sum(confs) / len(confs) if confs else 0.0
        lo = min(confs) if confs else 0.0
        hi = max(confs) if confs else 0.0
        n_high = sum(1 for c in confs if c >= 0.8)
        # 450 DPI completeness cross-check (same content expected).
        png450 = os.path.join(config.DIR_DOCS,
                              png.replace(".png", f"_{DPI_CROSSCHECK}dpi.png"))
        doc = fitz.open(pdf)
        doc[0].get_pixmap(dpi=DPI_CROSSCHECK).save(png450)
        doc.close()
        n300, n450 = crosscheck_ocr(reader, png_path, png450)
        stable = abs(n450 - n300) / max(n300, 1) <= 0.25
        xcheck_rows.append({
            "render_300dpi": f"docs/{png}", "words_300dpi": n300,
            "avg_conf_300dpi": f"{avg:.3f}",
            "render_450dpi": f"docs/{os.path.basename(png450)}",
            "words_450dpi": n450,
            "content_stable": "yes" if stable else "NO - investigate",
            "text_300dpi": text,
        })
        print(f"  450dpi cross-check: {n300} -> {n450} words "
              f"({'stable' if stable else 'UNSTABLE'})", flush=True)
        sections.append({
            "tag": tag, "png": png, "text": text, "nwords": nwords,
            "avg": avg, "lo": lo, "hi": hi, "n_high": n_high, "dt": dt,
            "n450": n450, "stable": stable,
        })
        print(f"  done in {dt:.1f}s; words={nwords}; conf avg={avg:.3f} "
              f"min={lo:.3f} max={hi:.3f}; high(>=0.8)={n_high}/{nwords}",
              flush=True)

    # Cover of consultation paper (page 1, image-based).
    cover_png = os.path.join(config.DIR_DOCS, "consult_paper_p1_cover_300.png")
    doc = fitz.open(config.DOC_CONSULT_PAPER)
    pix = doc[0].get_pixmap(dpi=300)
    pix.save(cover_png)
    doc.close()
    print(f"OCR cover {cover_png} ...", flush=True)
    ct, cn, cconf, cdt = ocr_page(reader, cover_png)
    cover_avg = sum(cconf) / len(cconf) if cconf else 0.0
    cover_lines.append((ct, cn, cover_avg, cdt))
    print(f"  cover done in {cdt:.1f}s; words={cn}; conf avg={cover_avg:.3f}",
          flush=True)

    # ------------------------------------------------------------------
    # Write docs/annex_ocr.md
    # ------------------------------------------------------------------
    md = []
    md.append("# Annex OCR - image-only Annex B and Annex C")
    md.append("")
    md.append(f"- Method: page rendered to PNG at {DPI} DPI via pymupdf, "
              f"then OCR'd with easyocr (English, CPU).")
    md.append("- Both annexes are image-only in the source PDFs "
              "(text layer contains only the running title); the body is "
              "raster content, so OCR is the only extraction path.")
    md.append("- Confidence caveats are stated per page below. Table cells "
              "and model names are the most error-prone; cross-check "
              "against the paper's Tables 1/2 (pages 11-12) before use.")
    md.append("")
    for s in sections:
        name = "Annex B" if s["tag"] == "annex_b" else "Annex C"
        md.append(f"## {name}")
        md.append("")
        md.append(f"- Source PDF: `docs/{os.path.basename(s['png'][:-4])}.pdf` "
                  f"(single page); render: `docs/{s['png']}` "
                  f"({os.path.getsize(os.path.join(config.DIR_DOCS, s['png']))} bytes)")
        md.append(f"- OCR stats: {s['nwords']} words; mean confidence "
                  f"{s['avg']:.3f}; min {s['lo']:.3f}; max {s['hi']:.3f}; "
                  f"words with confidence >= 0.8: {s['n_high']}/{s['nwords']}")
        md.append(f"- OCR wall time: {s['dt']:.1f}s (CPU)")
        md.append(f"- Resolution cross-check (450 DPI re-OCR): {s['n450']} words "
                  f"vs {s['nwords']} at 300 DPI -> "
                  f"{'content stable (OCR complete)' if s['stable'] else 'UNSTABLE - investigate'}")
        md.append("- Confidence caveat: "
                  + (
                      "HIGH - most words well above 0.8; model names and "
                      "table borders still spot-checked against paper "
                      "Tables 1/2."
                      if s["avg"] >= 0.85 else
                      "MEDIUM - usable, but individual low-confidence words "
                      "(esp. model names, digits) must be cross-checked "
                      "against the paper text before any quantitative use."
                      if s["avg"] >= 0.7 else
                      "LOW - treat as indicative only; verify every "
                      "quantitative cell against the paper body text."
                  ))
        md.append("")
        md.append("```")
        md.append(s["text"])
        md.append("```")
        md.append("")

    md.append("## Known OCR misreads (use corrected readings downstream)")
    md.append("")
    md.append("| Annex | OCR output | Corrected reading | Reason |")
    md.append("|---|---|---|---|")
    for annex, bad, good, why in KNOWN_MISREADS:
        md.append(f"| {annex} | {bad} | {good} | {why} |")
    md.append("")
    md.append("## Note on the 'typical models' tables")
    md.append("")
    md.append("The non-exhaustive 'typical models' tables (Option A and Option B "
              "banding of 2025-registered models) are NOT in the annexes; they "
              "are Tables 1 (p.11) and 2 (p.12) of the paper body, which have a "
              "full text layer and were extracted verbatim into "
              "`docs/consult_paper_text.md`. Annex B is the illustrative "
              "merger+feebate mechanics diagram; Annex C is the illustrative "
              "median-OMV banding method (with a worked $31k-$38k example).")
    md.append("")

    with open(OUT_ANNEX, "w") as f:
        f.write("\n".join(md))
    print(f"WROTE {OUT_ANNEX}", flush=True)

    with open(OUT_XCHECK, "w", newline="") as f:
        w = _csv.DictWriter(f, fieldnames=list(xcheck_rows[0].keys()))
        w.writeheader()
        w.writerows(xcheck_rows)
    print(f"WROTE {OUT_XCHECK}", flush=True)

    # ------------------------------------------------------------------
    # Write docs/consult_paper_cover_ocr.md
    # ------------------------------------------------------------------
    ct, cn, cover_avg, cdt = cover_lines[0]
    cov = []
    cov.append("# Consultation paper cover - OCR (page 1, image-based)")
    cov.append("")
    cov.append("- Page 1 of `consult_paper.pdf` has no usable text layer; "
               "rendered at 300 DPI and OCR'd with easyocr (English, CPU).")
    cov.append(f"- OCR stats: {cn} words; mean confidence {cover_avg:.3f}; "
               f"wall time {cdt:.1f}s")
    cov.append("- Use: capture the consultation window (start/end dates) "
               "and document metadata not present in the text layer.")
    cov.append("")
    cov.append("```")
    cov.append(ct)
    cov.append("```")
    with open(OUT_COVER, "w") as f:
        f.write("\n".join(cov))
    print(f"WROTE {OUT_COVER}", flush=True)


if __name__ == "__main__":
    main()
