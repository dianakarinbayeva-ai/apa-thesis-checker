# Automated checks and evidence limits

Every review executes automatically, without a manual workflow. No overall
“compliant” certificate is issued. An insufficient-evidence outcome is never
counted as a pass. The JSON contains stable rule identifiers, method, guide
clause, physical PDF page, evidence, profile snapshot and original SHA-256.

| Rule | Automatic behaviour |
|---|---|
| R_SIZE | A4 dimensions, allowing 1 mm and landscape orientation |
| R_LENGTH | 40/60-page minimum; first recognised appendix excluded; ambiguous boundaries yield insufficient evidence |
| R_FONT | Dominant long-text font and size; 0.5 pt tolerance; mixed formatting is reported separately |
| R_COLOR | Non-black long body-text spans |
| R_MARGIN | Occupied text envelope against 30/10/20/20 mm with 2 mm tolerance; sparse envelopes remain inconclusive |
| R_NUMBER | Arabic numerals at bottom centre; sequence includes unnumbered title page |
| R_STRUCTURE | Contents, introduction, conclusion, references; headings recognised in all three languages |
| R_HEADING | Recognised structural heading boldness and location at start of page |
| R_FIGURE / R_TABLE | Numbered captions and non-empty titles; no detected captions is insufficient evidence |
| R_REFERENCE | Square-bracket numbered citations and first-appearance order; does not verify source truth |
| R_APPENDIX | Recognised appendix headings use Arabic numbers; boundary/complex nesting can be inconclusive |
| R_SPACING | Median adjacent long-line separation, normalised by body font, single-spacing band 0.95–1.30; short evidence sets inconclusive |
| R_VISUAL | Raster-image presence; vector illustrations and complete table/diagram area cannot reliably be established |

PDF coordinates represent glyph bounds rather than Word paragraph settings.
Single-spacing estimates are heuristic and do not prove a source-document setting.
Do not infer complete compliance from a dominant font or recognised caption.
Absent/ambiguous evidence is retained explicitly. Protected, damaged and mostly
scanned files fail processing with a translated explanation. Blank pages in an
otherwise readable PDF are flagged. Report count totals count findings, not rules.

Initial profile: Appendix 1, Order No. 586, 2024-09-13. Source:
https://www.apa.kz/wp-content/uploads/2024/09/Приложение-1-Требования-к-оформлению.docx
The older `download/cap/rukovodstvo-napisanie-magisterskoi.pdf` is not used.
