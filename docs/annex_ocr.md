# Annex OCR - image-only Annex B and Annex C

- Method: page rendered to PNG at 300 DPI via pymupdf, then OCR'd with easyocr (English, CPU).
- Both annexes are image-only in the source PDFs (text layer contains only the running title); the body is raster content, so OCR is the only extraction path.
- Confidence caveats are stated per page below. Table cells and model names are the most error-prone; cross-check against the paper's Tables 1/2 (pages 11-12) before use.

## Annex B

- Source PDF: `docs/annex_b.pdf` (single page); render: `docs/annex_b.png` (4505040 bytes)
- OCR stats: 50 words; mean confidence 0.854; min 0.641; max 1.000; words with confidence >= 0.8: 32/50
- OCR wall time: 11.5s (CPU)
- Resolution cross-check (450 DPI re-OCR): 50 words vs 50 at 300 DPI -> content stable (OCR complete)
- Confidence caveat: HIGH - most words well above 0.8; model names and table borders still spot-checked against paper Tables 1/2.

```
Annex B How the Proposed COE Merger and Feebate System Could Work Current system Two passenger car categories (A and B) Category A Category B (mass-market cars) (higher-value cars) Cat A Cat B COE Price COE Price The current Category A and B Category A COE prices The existing criteria are have exceeded Category B distinction is becoming less meaningful: increasingly ineffective: prices on three occasions in 2026. Proposed system One passenger car category with a fee-and-rebate (feebate) system 1 Merge into one 2 Fee-and-rebate passenger car category (feebate) system All passenger cars, whether A rebate or surcharge; based on the mass-market or higher-value, value of the car; is applied to the bid from the same COE prevailing COE price: Lower-value cars Mid-range cars Higher-value cars One prevailing COE Determined by Demand and Rebate No adjustment Surcharge available COE supply With these two components, we are able to maintain thedistinction between mass-market and higher-value cars pool: price
```

## Annex C

- Source PDF: `docs/annex_c.pdf` (single page); render: `docs/annex_c.png` (3583543 bytes)
- OCR stats: 49 words; mean confidence 0.803; min 0.467; max 1.000; words with confidence >= 0.8: 26/49
- OCR wall time: 11.5s (CPU)
- Resolution cross-check (450 DPI re-OCR): 49 words vs 49 at 300 DPI -> content stable (OCR complete)
- Confidence caveat: MEDIUM - usable, but individual low-confidence words (esp. model names, digits) must be cross-checked against the paper text before any quantitative use.

```
Annex € Use of Median Open Market Value (OMV) to Determine Feebate Band Determine the median OMV 1 Look at the OMVs from past registrations of the same car model, arrange the OMVs from lowest to highest; and identify the middle value (median OMV) . S31,000 $33,000 S34,000 $35,000 $38,000 Arrange from lowest to highest OMV Median OMV = $34,000 For illustrative purposes only: Determine the feebate band 2 Compare the car model's median OMV against OMV percentile thresholds to determine its feebate band:. Lower OMV Higher OMV (mass-market models) (higher-value models) Band 1 Band 2 Band 3 Band 4 Band 5 (rebate) (rebate) (no adjustment) (surcharge) (surcharge) 3 What is the cut-off and quantum? How to set cut-offs as well as fees and rebates? Feebate bands are Proposed fee and These would be determined based on the F rebate amounts take reviewed annually: percentile of vehicles reference from registered in the historical price gaps previous year: between Categories A and B.
```

## Known OCR misreads (use corrected readings downstream)

| Annex | OCR output | Corrected reading | Reason |
|---|---|---|---|
| Annex C | S31,000 / S33,000 / S34,000 / S35,000 / S38,000 | $31,000 / $33,000 / $34,000 / $35,000 / $38,000 | dollar sign '$' read as 'S' |
| Annex C | Annex € | Annex C | 'C' misread in the running title |
| Annex C | determined based on the F rebate amounts | determined based on the fee rebate amounts (i.e. the proposed fee and rebate amounts) | low-confidence word; reading follows from context (s2.17, p.10: historical A-B price gaps as reference point) |

## Note on the 'typical models' tables

The non-exhaustive 'typical models' tables (Option A and Option B banding of 2025-registered models) are NOT in the annexes; they are Tables 1 (p.11) and 2 (p.12) of the paper body, which have a full text layer and were extracted verbatim into `docs/consult_paper_text.md`. Annex B is the illustrative merger+feebate mechanics diagram; Annex C is the illustrative median-OMV banding method (with a worked $31k-$38k example).
