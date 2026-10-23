"""
Step 2a - Extract docs/consult_paper.pdf (local copy; never /tmp) with
pymupdf into docs/consult_paper_text.md, with per-page markers.
Also renders the page-17 figure and the page-1 cover to PNG for reference
(extraction artifacts live under docs/).
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config  # noqa: E402
import fitz  # noqa: E402

OUT_MD = os.path.join(config.DIR_DOCS, "consult_paper_text.md")


def main() -> None:
    doc = fitz.open(config.DOC_CONSULT_PAPER)
    n = len(doc)
    blocks: list[str] = []
    blocks.append("# Consultation paper - full text extraction")
    blocks.append("")
    blocks.append(
        f"- Source: `{os.path.basename(config.DOC_CONSULT_PAPER)}` "
        f"(local copy, {os.path.getsize(config.DOC_CONSULT_PAPER)} bytes, "
        f"{n} pages)"
    )
    blocks.append("- Extracted with: pymupdf (fitz) " + fitz.version[0])
    blocks.append(
        "- Note: page 1 is a cover page (image-based, near-zero text layer); "
        "page 17 contains one embedded figure (rendered to "
        "docs/consult_paper_p17_figure.png)."
    )
    blocks.append("")

    total_chars = 0
    for i, page in enumerate(doc):
        text = page.get_text("text")
        total_chars += len(text.strip())
        blocks.append(f"\n---\n\n## Page {i + 1}\n")
        if len(text.strip()) < 50:
            blocks.append(f"*[near-empty page: {len(text.strip())} chars]*\n")
        else:
            blocks.append(text.rstrip() + "\n")

    doc.close()

    with open(OUT_MD, "w") as f:
        f.write("\n".join(blocks))

    # Render page 1 (cover) and page 17 (figure) for reference.
    doc = fitz.open(config.DOC_CONSULT_PAPER)
    for pno, name in [(0, "consult_paper_p1_cover.png"),
                      (16, "consult_paper_p17_figure.png")]:
        page = doc[pno]
        pix = page.get_pixmap(dpi=200)
        out = os.path.join(config.DIR_DOCS, name)
        pix.save(out)
        print(f"rendered {out} ({os.path.getsize(out)} bytes)")
    doc.close()

    print(f"WROTE {OUT_MD}: {n} pages, {total_chars} chars extracted")


if __name__ == "__main__":
    main()
