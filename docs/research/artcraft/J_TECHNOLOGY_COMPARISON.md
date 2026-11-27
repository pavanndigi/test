# Report J — Competitor and Technology Comparison

| Field | Value |
| --- | --- |
| Date of research | 2026-11-28 |
| ArtCraft basis | pdfcraft `c34c6c5a0bd8…`, wordcraft `72ca96a27c79…`, craft-libs `0a6e42b8…`; measured behaviour in Report H |
| Other tools | Facts from project documentation and licences (links below); not re-benchmarked here except where Report H says so |
| Confidence | High for licences and feature presence; Medium for qualitative strength ratings (informed judgement, labelled) |

## 1. Bottom line

As a **foundation** for a reconstruction engine, ArtCraft is not competitive with PDFium or MuPDF for parsing, rendering and glyph geometry. Its renderer is itself the third-party Hayro library, described in its own source as a "bootstrap" (`pdfcraft/crates/render/src/lib.rs:3`). ArtCraft is **genuinely distinctive in two places**:

1. A **permissively licensed Rust PDF object layer** that edits content streams and saves incrementally.
2. A **permissively licensed Rust DOCX writer** (`craft-docx`) whose model covers floats, page-anchored text boxes, sections and tables. The Python ecosystem's python-docx has no high-level API for floating shapes or text boxes.

## 2. Comparison table

| Technology | Parsing | Rendering | Text geometry | Fonts | Editing | DOCX generation | Licence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **ArtCraft PdfCraft / craft-pdf** | Own COS parser, xref/object streams, R2–R6 encryption (Verified); page interpretation via Hayro | Hayro + vello_cpu, CPU (third-party, patched) | Lines, words, paragraphs with base font, size, colour, baseline, rotation; glyph quads for selection (Verified) | Std-14 metrics; does not read embedded programs in its own crates (Verified) | Content-stream text edits, images, pages, annotations, forms, redaction (Verified) | Heuristic exporter: one fixed body font (Arial), no vector art (Verified); behaviour in Report H | MIT OR Apache-2.0 |
| **ArtCraft craft-docx / WordCraft** | n/a | WordCraft layout + vello_cpu (~55% Word parity, self-estimated) | n/a | Word-style resolver, metric twins, harfrust shaping | Full word processor | Native OOXML read/write incl. anchors, text boxes, sections, tables, encryption | MIT OR Apache-2.0 |
| [PDFium](https://pdfium.googlesource.com/pdfium/) | Mature (Chrome's engine, Foxit lineage) | Mature, CPU (Skia/AGG) | Per-char box, origin, font name, flags, size, colour via `FPDFText_*` | Renders embedded and substitutes non-embedded | Page objects API (text, path, image), save | None | BSD-3-Clause |
| [MuPDF](https://mupdf.readthedocs.io/en/1.27.0/license.html) | Mature, repairs damaged files | Mature, fast | Structured text with chars, spans, fonts, bboxes | Full font handling | Redaction, page/object edits, save | None in the core | AGPL or commercial |
| [PyMuPDF](https://pymupdf.readthedocs.io/) | MuPDF | MuPDF | `rawdict` per-char origin, bbox, font, flags, colour; `get_drawings()` for vectors | MuPDF | MuPDF | None | AGPL or commercial |
| [Apache PDFBox](https://pdfbox.apache.org/) | Mature (Java) | Good | `TextPosition` per glyph | Good | Object-level edit, save | None | Apache-2.0 |
| [Poppler](https://poppler.freedesktop.org/) | Mature | Mature | `pdftotext -bbox`, glib APIs | Good | Limited | None | GPL |
| [pdfplumber](https://github.com/jsvine/pdfplumber) / pdfminer.six | Pure Python, slower | Debug images only | Char objects with font name and size; lines, rects | Metrics from dicts | No | None | MIT |
| [pdf2docx](https://github.com/ArtifexSoftware/pdf2docx) | PyMuPDF | — | PyMuPDF | — | — | Rule-based converter (PyMuPDF + python-docx); no longer actively maintained by Artifex | MIT from 0.5.13 (earlier releases AGPL); depends on PyMuPDF (AGPL or commercial) |
| [LibreOffice](https://www.libreoffice.org/) | Poppler-based import into Draw | — | — | — | Draw: one text box per line | Writes DOCX from its own model; DOCX import and render are good but not Word | MPL-2.0 |
| [Docling](https://arxiv.org/abs/2408.09869) | pypdfium2 or own backends | — | Uses backend geometry | — | — | Exports Markdown/JSON/HTML, not layout-faithful DOCX | MIT (models Apache-2.0 / CDLA) |
| [Hayro](https://github.com/LaurenzV/hayro) (discovered: PdfCraft's renderer) | Own Rust parser (hayro-syntax) | CPU rasteriser; in PdfCraft via vello_cpu, with ArtCraft patches | Glyph callbacks via `Device::draw_glyph` (vendored copy: `craft-libs/vendor/hayro-interpret/src/device.rs:9, 33`) | Renders embedded fonts | No | None | MIT OR Apache-2.0 |
| [PaddleOCR 3.x](https://arxiv.org/abs/2507.05595) | — (images) | — | OCR boxes; PP-StructureV3 layout and tables | — | — | No | Apache-2.0 |

## 3. Where ArtCraft is genuinely competitive

| Area | Why | Label |
| --- | --- | --- |
| Permissive PDF **editing** in Rust | Content-stream rewrites that keep positioning, incremental saves, encryption create/decrypt, all MIT OR Apache-2.0. PDFium is permissive too but lower-level for text edits; MuPDF is AGPL. | Verified |
| Permissive **DOCX writing** with floats and text boxes | `craft-docx` writes `wp:anchor` drawings, text-box stories, sections, tables, font tables | Verified |
| DOCX **structural validation** | `wordcraft-validate`: a spec-derived checker with stable rule ids; few open-source equivalents exist | Verified (existence); effectiveness Unknown |
| Hostile-input hardening | Budgets on decode, ZIP, XML and form depth throughout | Verified |

## 4. Where established tools are stronger

| Area | Stronger choice | Reason |
| --- | --- | --- |
| Rendering fidelity and robustness | PDFium, MuPDF | Years of production use; ArtCraft's renderer is Hayro "bootstrap", whose own diagnostics are "not a fidelity certificate" (`craft-pdf/README.md`) |
| Per-glyph font identity for reconstruction | PDFium, PyMuPDF | They expose font name, flags and size per char. PdfCraft's line model carries base font per line, but its exporter discards it. |
| Layout, table and OCR models | Docling, PaddleOCR, Tesseract | ArtCraft has heuristics only, and Latin-only CC-BY-SA OCR models |
| DOCX layout truth | Microsoft Word | WordCraft self-reports ~55% parity and no page-for-page comparison with Word |
| PDF→DOCX conversion quality | Commercial converters (Acrobat, ABBYY, Apryse) | PdfCraft's own gap register calls its Office export "weak" (`docs/gaps.md:193`) |

## 5. Best technical foundation (recommendation)

- **Parsing, rendering, glyph geometry:** PDFium (BSD-3, via pypdfium2) as the default. MuPDF/PyMuPDF if we buy a commercial licence and want its richer Python API.
- **Analysis:** our own geometric rules, plus Docling/PaddleOCR layout and table models and Tesseract/PaddleOCR for OCR.
- **DOCX:** our own OOXML emitter; prototype a `craft-docx` sidecar only if floats and text boxes become a bottleneck.
- **Verification:** Microsoft Word rendering as truth; WordCraft or LibreOffice as fast previews; `wordcraft-validate` as a structural gate.
- **ArtCraft:** reference implementation, baseline in benchmarks, and two optional tools (validator, DOCX writer sidecar).

## 6. Limitations and open questions

- **Limitations:**
  - Only ArtCraft and Poppler were run here (Report H).
  - Other rows come from project documentation, so strength ratings are informed judgement.
  - Licences change; pdf2docx changed from AGPL to MIT in 0.5.13.
- **Open question:** how do PDFium and PyMuPDF compare with PdfCraft on the same 15-file test set? Re-run the Report H harness with them as a baseline.
