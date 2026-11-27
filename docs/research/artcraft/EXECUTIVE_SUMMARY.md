# Executive Summary — ArtCraft for PDF Reconstruction

| Field | Value |
| --- | --- |
| Date of research | 2026-11-28 |
| Repositories | https://github.com/storytold/pdfcraft `c34c6c5a0bd8…`; https://github.com/storytold/wordcraft `72ca96a27c79…`; https://github.com/storytold/craft-libs `0a6e42b8…` / `0b8bbaf4…` |
| Method | Source audit of pinned commits, plus from-source builds of `pdfcraft-cli` and `wordcraft-cli` run against a 15-file test PDF set (Report H) |
| Verdict | **Reference only**, with two optional tool-level uses |

## 1. What ArtCraft actually is

ArtCraft is the `storytold` GitHub organisation: a family of desktop "Craft" apps written in Rust (edition 2024). The apps include PdfCraft, WordCraft and others. They share a monorepo, `craft-libs` (242 crates), and an egui/eframe UI fork.

- **Licensing:** first-party code is MIT OR Apache-2.0; the brand is trademark-protected.
- **Status:** development is very active and heavily AI-agent-driven. Crates are at 0.1.0 and unpublished. Each app pins its own craft-libs commit. (Reports A, E.)

## 2. What PdfCraft actually implements

A genuine PDF editor, not just a viewer.

- **Native:**
  - A PDF object layer (craft-pdf COS): parser, xref, object streams, R2–R6 encryption, incremental and full writer.
  - Content-stream text editing that keeps positioning.
  - Pages, images, forms, annotations and redaction.
  - Text lines and paragraphs with font name, size and colour.
  - A heuristic PDF→DOCX/PPTX/HTML exporter.
  - About 217 automation tools exposed through a CLI and MCP.
- **Delegated:**
  - Rendering (Hayro + vello_cpu, patched).
  - OCR: ocrs models (not in source builds), or an installed Tesseract.

Report H results:
- 15/15 files opened.
- Renders matched Poppler within 1–2% ink.
- 100% of expected text was found on born-digital files.
- Edits saved to valid, reopenable files.
- The DOCX export was a baseline only. Every font became Arial, columns collapsed, vectors and transparency vanished, and headers and footers became body text. A ruled table got a 7-column grid. Invisible OCR text became visible.

## 3. What WordCraft actually implements

A word processor with:
- its own document model (floats, anchors, wrap, text boxes, sections, columns);
- its own layout engine (UAX #14 with Word exceptions; ~55% Word parity by its own estimate);
- Word-style font resolution with metric twins, and harfrust shaping;
- DOCX read/write through `craft-docx`;
- an OOXML validator (`wordcraft-validate`);
- a CLI for convert, render and validate (Report C).

## 4. Most valuable reusable components

1. **`craft-docx` + `craft-wordmodel`:** a permissive DOCX writer whose serde-serialisable model covers anchored text boxes, floats, sections, tables and the font table. Candidate sidecar.
2. **`wordcraft-validate`:** a spec-derived OOXML structural checker with stable rule ids. Candidate CI gate. In Report H it caught 3 of 5 injected defects. It skips `mc:AlternateContent`, so it misses drawing-level errors.
3. **Reference designs:** reading-order walking, paragraph heuristics, Word font-substitution tables, the searchable OCR text layer, and input hardening budgets.

## 5. Licensing risks

These need legal review; this is not legal advice.

- **Clean so far:** the crate graphs of pdfcraft-cli (476 packages), wordcraft-cli (330), craft-docx, craft-pdf and craft-metafile declare no copyleft licences.
- **Flags:**
  - ocrs OCR models are CC-BY-SA-4.0.
  - `deny.toml` permits MPL-2.0. `acadrust` (MPL-2.0) sits in craft-dwg only.
  - The ArtCraft brand is trademarked.
  - OFL and BSD font/CMap terms need attribution.
  - AI-authored code carries provenance uncertainty, and there is no CLA or DCO.

(Report G, `evidence/dependency-licences.txt`.)

## 6. Integration opportunities

| Use | How | Effort |
| --- | --- | --- |
| Benchmark baseline and extraction cross-check | `pdfcraft-cli run --script` (JSON) as an external process | ~0.5–1 week |
| DOCX structural QA | `wordcraft-cli validate` in CI | Days |
| Positioned DOCX writing | Optional `craft-docx` sidecar taking JSON | 2–3 weeks, only if a spike proves it |

Avoid copying crates into our tree: 3–5 weeks up front plus ongoing fork maintenance (Report I).

## 7. Major technical gaps

ArtCraft does not provide:
- font identification beyond `/BaseFont` names;
- font-faithful or position-faithful DOCX emission;
- vector or transparency export to DOCX;
- table structure recovery (borders, spans, correct grid);
- ML layout analysis;
- multilingual OCR in a source build;
- reflow after edits;
- Word-accurate rendering.

These are the capabilities that decide reconstruction quality. (Reports D, F, H.)

## 8. Recommended architecture

A Python-first modular monolith (Report K):
- PDFium (BSD-3) for parsing, rendering and per-glyph geometry with font identity;
- Docling / PaddleOCR / Tesseract for layout, tables and OCR;
- our own document IR;
- our own OOXML emitter, with an optional `craft-docx` sidecar;
- Microsoft Word rendering as ground truth;
- SSIM, ink-IoU and CER scoring with a confidence and fallback loop;
- `wordcraft-validate` and `pdfcraft-cli` used only as external tools in QA and benchmarking.

## 9. Final decision

**Reference only.** Study ArtCraft and build independently. Allow two optional tool-level uses (validator in CI; `craft-docx` sidecar spike). Upgrade to **Partially adopt** for `craft-docx` only if the spike beats our own emitter on measured Word-rendered fidelity. (Report L.)

## 10. Recommended next experiments

1. **`craft-docx` spike (2 days):** hand-built `craft-wordmodel` JSON for test files 2, 3, 5 and 10 (exact fonts, absolute positions, anchored and rotated text boxes, table borders). Render in Word and score against the PDF.
2. **PDFium glyph probe:** extract per-glyph origin, advance, font name and flags on the full test set. Measure font-identity coverage for embedded subsets.
3. **Word-rendering oracle:** automate DOCX→PDF via Word, and re-score Report H's exports and ours with the same metrics.
4. **Validator gate:** run `wordcraft-cli validate` on our emitter's output and on the PdfCraft exports. Record rule hits and false positives.
5. **Real-world corpus:** repeat Report H on real scans, CID/Type 3 fonts, RTL text, forms and damaged files. The current test set is synthetic.
