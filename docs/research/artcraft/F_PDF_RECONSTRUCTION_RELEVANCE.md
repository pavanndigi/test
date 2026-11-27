# Report F — Relevance to PDF Reconstruction

| Field | Value |
| --- | --- |
| Date of research | 2026-11-28 |
| Repositories | pdfcraft `c34c6c5a0bd86d466f9f814c14b4cfdaa55cd7e2`; wordcraft `72ca96a27c795d6289775f6c12954c2cdbd62908`; craft-libs `0a6e42b8…` (pdfcraft pin) and `0b8bbaf4…` (wordcraft pin) |
| Basis | Source audit (Reports B–E) plus measured behaviour (Report H) |
| Confidence | High where a row cites both source and a Report H run; Medium where it rests on source alone |

## 1. Classification key

| Class | Meaning here |
| --- | --- |
| **Production-ready** | Shipped, tested in the repository, and behaved correctly on every relevant Report H case |
| **Functional but incomplete** | Works for common cases; measured or documented gaps |
| **Experimental** | Present, but self-described as early or narrow, or failed basic cases in Report H |
| **Dependency-only** | The capability comes from a third-party library, not ArtCraft code |
| **Not implemented** | No code found for it |
| **Unknown** | Not determinable from source or tests |

The "Our implementation gap" column assumes the reconstruction target: a DOCX that keeps each glyph's position, font, size and colour, with editable structure.

## 2. Relevance matrix

| Requirement | ArtCraft capability | Source evidence | Maturity | Reuse potential | Our implementation gap |
| --- | --- | --- | --- | --- | --- |
| **PDF parsing** | Own COS layer: lexer/parser, xref tables and streams, object streams, repair, R2–R6 decryption | `craft-libs/crates/pdf/src/cos/parser.rs:1–5`, `crypt.rs:1–14`; H: all 15 files opened, AES-256 with password | **Production-ready** (on the synthetic corpus) | Medium. MIT/Apache, few dependencies (8 crates in its graph), but Rust-only and duplicates PDFium | None. PDFium already covers this. |
| **PDF rendering** | Hayro interpreter + vello_cpu rasteriser, with ArtCraft patches | `pdfcraft/crates/render/src/lib.rs:1–6` ("bootstrap"); `Cargo.toml:184–206` patches; H: ink F1 0.980–1.000 vs Poppler | **Dependency-only** (Hayro); ArtCraft adds patches and wiring | Low. Use PDFium/MuPDF. | None |
| **Glyph extraction** | Per-line text, word ink boxes, glyph quads for selection; Unicode via ToUnicode/encodings | `crates/edit/src/text.rs:82–107` (`TextLine` with `ink`, `base_font`, `size`, `color`, `bold`, `italic`); H: 100% of strings on digital files; diagonal text whole | **Functional but incomplete**. No per-glyph font program access or outlines in the public model. | Medium as a reference for line/word assembly | Per-glyph origin and advance with font identity (PDFium gives these) |
| **Font identification** | `/BaseFont` name per line; bold/italic guessed from the name | `crates/engine/src/compare.rs:221–224` (`weight_and_slant`); `crates/fonts/src/lib.rs:1–5` (std-14 only, no embedded programs) | **Experimental**. Name heuristics only. | Low | Matching embedded subsets to installable fonts (glyph-outline fingerprinting), which ArtCraft does not attempt |
| **Font metrics** | Std-14 AFM metrics in PdfCraft. WordCraft: Word-style font resolution, metric-compatible twins, harfrust shaping. | `pdfcraft/crates/fonts/src/lib.rs`; `wordcraft/crates/fonts/src/word.rs:1–45` | Std-14: Production-ready. WordCraft resolver: Functional but incomplete (not run here). | Medium. WordCraft's Word-font mapping table is a useful reference. | Metrics of the DOCX target fonts as Word will lay them out |
| **Text reconstruction** | Lines → paragraphs → DOCX runs with size, bold, italic, colour | `crates/export/src/layout.rs:3–21`; `as_word.rs`; H: words complete, but every font → Arial (`as_docx.rs:46`) | **Functional but incomplete** | Low. Its single-font choice contradicts our goal. | Font-preserving run emission; per-line geometry kept |
| **Paragraph detection** | Spacing- and indent-based grouping (`text_paragraphs`) | `crates/edit/src/text/blocks.rs:399`; H: merged 2 paragraph pairs on file 4; split each paragraph after line 1 in DOCX | **Functional but incomplete** | Low–medium. Reference for heuristics. | Robust segmentation with confidence scores |
| **Reading order** | Column-walking order for text and export | `crates/export/src/layout.rs` (column walk, Report B); H: correct order on the two-column file | **Functional but incomplete** (one layout tested) | Medium. Reference. | Complex layouts (sidebars, floats, mixed columns) |
| **Column detection** | Used for ordering, but not emitted to DOCX (`w:cols num=1`) | H file 4: two columns → one | **Experimental** for reconstruction | Low | Column sections, or positioned frames |
| **Table reconstruction** | Alignment-plus-rules inference → `w:tbl` | `crates/export/src/layout.rs:385, 634`; H: 7-column grid for 5 columns, header cell lost, borders `nil`, ruled = borderless | **Experimental** | Low | Table structure (rows, columns, spans), borders and shading. Use a table model (Docling/PaddleOCR) plus rule geometry. |
| **Image extraction** | `page_images`; images exported at correct size | H file 7: 2 images found, sizes exact in DOCX | **Production-ready** (simple cases) | Low. PDFium does the same. | Position, cropping and masks in DOCX |
| **Vector extraction** | Object listing and rendering only; not exported | `crates/edit/src/objects.rs` (ObjectKind); `docs/gaps.md:193–216`; H file 8: all shapes lost in DOCX | **Not implemented** for export | Low | Paths → DrawingML/EMF. `craft-metafile` (an EMF writer) is a possible building block. |
| **Transparency** | Rendered (Hayro); not exported | H file 9: correct render; fills lost in DOCX | **Dependency-only** (render); **Not implemented** (export) | Low | Alpha fills in DrawingML, or rasterised fallbacks |
| **OCR** | `pdfcraft-ocr`: ocrs (Latin; CC-BY-SA models, not in source build) or an external Tesseract; writes invisible or editable text | `crates/ocr/src/lib.rs:1–19`, `ocrs.rs:35–85`; H: Tesseract CER 0.0 on one synthetic page | **Dependency-only** (ocrs/Tesseract do recognition); orchestration Functional | Low–medium. The searchable-layer writer is a reference. | Multilingual, layout-aware OCR at scale |
| **Layout detection** | Heuristics only (no ML layout model) | `crates/export/src/layout.rs` (heading levels from size ratios, lines 119–129) | **Experimental** | Low | Layout model (Docling, PP-StructureV3, LayoutLM family) |
| **DOCX generation** | Two writers: PdfCraft's exporter (`crates/export/src/as_docx.rs`), and craft-docx (full OOXML: anchors, text boxes, sections, tables, font table) | `craft-libs/crates/docx/src/write/story/object.rs:290, 410, 644`; `write/font_table.rs:1–5`; H: all exports passed `wordcraft-validate` and opened in LibreOffice and WordCraft; rotated text boxes carry `a:xfrm rot` | Exporter: Functional but incomplete. craft-docx: Functional (used by WordCraft; not run directly). | **High** for craft-docx (permissive, JSON-serialisable model) | Our emitter must drive absolute positioning, fonts and vectors. craft-docx could carry it. |
| **DOCX rendering** | WordCraft layout engine + vello_cpu | `wordcraft/crates/layout/src/lib.rs:1–8`; `docs/layout-parity.md:14` (~55% Word parity, self-estimated); H: rendered all 16 PdfCraft exports and honoured text-box rotation, unlike LibreOffice | **Functional but incomplete** (not compared with Word) | Medium as a fast preview; not as ground truth | Word-accurate rendering (Word itself remains the oracle) |
| **Visual comparison** | `compare_visual` (page rectangles that differ at a DPI), text compare | `crates/engine/src/compare.rs:58–120` | **Functional** (not run in H) | Low–medium. Concept only. | Region-level scores (SSIM, IoU, CER) tied to our IR |
| **Editable document structure** | WordCraft's own document model (floats, anchors, wrap, text boxes, sections, columns); craft-wordmodel serde model | `wordcraft/crates/doc/src/para/float.rs:136`; `section.rs:644, 762`; `craft-libs/crates/wordmodel/src/lib.rs:98–101` | **Functional but incomplete** (not run) | **Medium–high** as a model reference, or via the sidecar | Our own IR that maps to both PDF geometry and DOCX structure |

## 3. What this means for our project

| Bucket | Capabilities |
| --- | --- |
| Directly useful | DOCX writing with floats and text boxes (craft-docx), DOCX structural validation (wordcraft-validate), WordCraft's document model as a design reference |
| Useful as reference only | Line/word assembly, reading-order walk, paragraph heuristics, Word font mapping, OCR text-layer writing |
| Not useful | Parsing and rendering (PDFium is better and simpler), table, layout and vector export (absent or weak), font identification (names only) |

The capabilities that decide reconstruction quality are font identification and positioned, font-faithful DOCX emission. ArtCraft has no solution for the first and only a writer (no strategy) for the second.

## 4. Tests, dependencies and limitations

- **Tests relied on:** Report H's 15-file run, plus the targeted edit, OCR and WordCraft runs. Repository test suites were inspected (Report B), not executed.
- **Dependencies:** the classifications separate ArtCraft code from Hayro, vello_cpu, ocrs and Tesseract, per the brief's rule.
- **Limitations:** the test set is synthetic and Microsoft Word was not available, so "Production-ready" means "correct on these cases", not "proven at scale".

## 5. Open questions

- Would a release build with the ocrs models change the OCR row?
- Does Word reproduce WordCraft's correct rendering of rotated text boxes?
