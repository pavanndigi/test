# Report D — Typography, Fonts and Layout Engineering

| Field | Value |
| --- | --- |
| Date of research | 2026-11-28 |
| Repositories and commits | pdfcraft `c34c6c5a0bd8…`; wordcraft `72ca96a27c79…`; craft-libs `0a6e42b8…` and `0b8bbaf4…` |
| Method | Lockfile scans (`Cargo.lock` of all three) for every typography library named in the brief; source reading of the font and layout crates |
| Confidence | High on what libraries are present; Medium on behaviour |

## 1. Bottom line

ArtCraft's typography is built on Google's **fontations** stack (`skrifa`/`read-fonts`/`write-fonts`) and **HarfRust** (the Rust port of HarfBuzz shaping). There is no C HarfBuzz and no FreeType. WordCraft has a serious Word-oriented font resolver with metric-compatible substitutes and a Word-imitating line breaker. PdfCraft's font crate is deliberately thin: it does **not** read embedded font programs. **No ArtCraft component solves our core problem**, which is choosing DOCX parameters so that Word reproduces a PDF's glyph positions. A few pieces (the font resolver, shaping wrapper and metric-twin table) are useful **references** for building that ourselves.

## 2. Libraries actually present

From the three `Cargo.lock` files (versions as locked):

| Library | Present? | Versions | Used for (where verified) |
| --- | --- | --- | --- |
| HarfBuzz (C, `harfbuzz-sys`, `harfbuzz_rs`) | **No** | — | — |
| FreeType | **No** | — | — |
| fontdue | **No** | — | — |
| cosmic-text | **No** | — | — |
| swash | **No** | — | — |
| **skrifa** / **read-fonts** / write-fonts | Yes | skrifa 0.42–0.49; read-fonts 0.39–0.46 | Outlines, metrics, tables (`pdfcraft/crates/fonts`, `wordcraft/crates/fonts`, `craft-font-catalog`) |
| **harfrust** | Yes | 0.12.0, 0.13.3 | OpenType shaping (GSUB/GPOS: kerning, ligatures, complex scripts) in both apps' font crates |
| rustybuzz | Yes (craft-libs only) | 0.20.1 | `craft-font-subset` |
| ttf-parser | craft-libs dev/test | 0.25.1 | Tests |
| fontique | Yes | 0.11.1 | System font enumeration in `craft-font-catalog` |
| fontdb | craft-libs | 0.23/0.24 | Via usvg/resvg (SVG text) |
| subsetter | Yes | 0.2.6 | Font subsetting in Krilla-based PDF writing |
| wuff | Yes | 0.2.x | WOFF/WOFF2 decoding (`wordcraft-fonts`) |
| unicode-bidi, unicode-linebreak, icu_segmenter, hypher | Yes | — | Bidi, UAX #14 breaking, Thai/Lao/Khmer/Burmese word breaks, hyphenation |

## 3. Typography capabilities

| Topic | PdfCraft | WordCraft / craft-libs | Label |
| --- | --- | --- | --- |
| Font discovery | Viewer-only CJK last resort from installed fonts (`render/src/system_font.rs:1–11`) | `craft-font-catalog`: discovery "on every platform, family, style and PostScript lookup"; `wordcraft-fonts::FontDb` (bundled OFL + system) | Verified |
| Loading and parsing | Std-14 metrics exact; **document font programs are not read** (`fonts/src/lib.rs:1–5`). Rendering reads them inside Hayro. | skrifa-based; WOFF/WOFF2 via wuff | Verified |
| Fallback and substitution | Missing glyphs in edited text fall back to Helvetica (WinAnsi) or Type 3 glyphs from bundled faces (`edit/src/text/fallback.rs`) | Metric-compatible substitutes first: Carlito↔Calibri, Caladea↔Cambria, Liberation↔Arial/Times New Roman/Courier New (`wordcraft/crates/fonts/src/word.rs:20–30`); synthetic bold/italic flags (`word.rs:9–17`) | Verified |
| Shaping, kerning, ligatures | `shape_latin`, `shape_arabic`, `shape_hebrew`, `shape_thai` for **added** text (`fonts/src/lib.rs` exports) | `wordcraft-fonts::shape`: glyph ids, clusters, advances in font units (`fonts/src/lib.rs:4–6`) | Verified (API); output not measured |
| Character and word spacing | Preserved in place: edits keep `Tc`/`Tw`/`TJ` positioning operators | Character spacing, scaling and justification applied above shaping in layout | Verified |
| Baselines | `TextLine::baseline()` gives the PDF user-space baseline origin (`edit/src/text.rs`) | "Word-style line metrics (Windows ascent/descent)" (`word.rs:1–3`) | Verified |
| Text measurement | `helvetica_width` and `Std14::text_width` | Shaped advances; layout cache per paragraph revision | Verified |
| Line breaking, paragraph layout | Greedy wrap within a paragraph's existing frame for rewrites (`edit/src/text/blocks.rs:439–446`) | UAX #14 plus Word exceptions, kinsoku, first-fit (`layout/src/lib.rs:3`) | Verified |
| Text direction, complex scripts | Bidi recovery and visual-order Indic handling when reading lines (`TextLine::logical_order`, `visual_order`) | Cursive joining across runs; Myanmar syllable breaking; Khmer/Thai/Lao break only at spaces (`docs/layout-parity.md`) | Verified (as documented) |
| Variable fonts | Not found | Supported: variation coordinates per face (`wordcraft/crates/fonts/src/lib.rs:281, 467–470`) | Verified |
| Embedded fonts | Read for rendering (Hayro); `pdfcraft-fonts` cannot subset or re-embed | DOCX: reads embedded fonts; writing new embedded fonts not found (Report C) | Verified / Inferred |

## 4. Layout and coordinate systems

| Topic | Finding | Evidence |
| --- | --- | --- |
| PDF coordinates | PDF user space (y up) in the edit layer; "page view space (points, y down)" for selection glyphs; export converts to "the visible page in points, y up" after CropBox, `/Rotate` and `/UserUnit` | `edit/src/text.rs`; `render/src/text.rs:66`; `engine/src/compare.rs:259–265` |
| Word units | `wordcraft-geom`: points, twips, EMU, inches, centimetres | `wordcraft/crates/geom/Cargo.toml` description |
| Bounding boxes | Per glyph: rect and rotated quad plus writing direction (`TextGlyph`); per line: rect, word ink boxes, rotated frame (`TextLine`) | `render/src/text.rs:63–74`; `edit/src/text.rs:84–160` |
| Columns | PdfCraft export: reading-order heuristic walks columns (continue up to 3.5 line heights, then the next column right; `layout.rs:627–634`). WordCraft: section columns | Verified |
| Tables | PdfCraft export: alignment-based detection plus ruled lines. WordCraft: full Word table layout (AutoFit, split rows, repeated headers) | Verified |
| Floating objects, z-order, anchoring | WordCraft `Float` (z = `relativeHeight`); PdfCraft export uses page-anchored text boxes on "positioned" pages | Verified |
| Clipping | PdfCraft reading respects clip regions when deciding what text shows (`edit/src/text.rs` tests `clip_regions_intersect_and_show_what_they_cover`) | Verified |
| Pagination | WordCraft layout: keep/widow rules, page breaks, headers/footers, page-number fields | Verified (module doc) |

## 5. Critical question: can any of this reproduce PDF text positioning in DOCX?

**Not directly.** Three ArtCraft pieces help, each only partly:

1. **PdfCraft's line extraction** (`text_lines`, `reading_blocks`) yields per-line boxes, word ink boxes, `/BaseFont`, size, colour and baseline. That is useful **input**. Its use in PdfCraft's own exporter throws the font family away (Report B §7).
2. **WordCraft's font resolver and shaper** can measure how wide a run would be in the font Word will use (including metric twins). That is the measurement we need to choose `w:spacing` (character spacing) or font substitution so lines keep their width.
3. **WordCraft's layout engine** can predict line breaks, but only to its own ~55% Word-parity estimate. Final verification still has to render in Microsoft Word.

The missing piece, which we must build, is an **optimiser** that maps measured PDF geometry to DOCX controls (indents, tab stops, exact line spacing, character spacing, text-box frames) and checks the result by rendering in Word.

## 6. Why PDF positions do not translate directly into DOCX

| Model | Who decides where a glyph goes | Consequence for reconstruction |
| --- | --- | --- |
| **PDF glyph positioning** | The producer, at write time. Each glyph's position is the text matrix plus advances from the font's `/Widths`, adjusted by `Tc`, `Tw`, `Tz` and `TJ` offsets. There are no lines or paragraphs, only drawn glyphs. | Exact geometry is known; structure has to be inferred. |
| **DOCX paragraph layout** | The reader (Word), at open time. Word breaks lines from paragraph width, its own font metrics, spacing, justification and compatibility rules; positions are emergent. Controls are coarse: indents, tab stops, line spacing (exact or at-least), character spacing in 1/20 pt, character scale, kerning threshold, frames and text boxes. | We can only **steer** Word. Matching requires the same font metrics and verification in Word. |
| **Browser layout** | The browser's CSS engine (line breaking, HarfBuzz-class shaping, box model); absolute positioning per element is possible. | HTML can pin each line, but that is not DOCX; useful only as a preview. |
| **Canvas positioning** | The application, per glyph, immediately (like PDF). | WordCraft's and PdfCraft's renderers work this way; it does not help produce editable DOCX. |

## 7. Limitations and open questions

- Shaping and metric outputs were not compared numerically against Word or HarfBuzz in this research.
- **Open:** whether the WordCraft metric-twin list matches Word's own substitution on Windows; WordCraft notes Word for Mac as its target.
- **Open:** licences of bundled fonts in WordCraft builds (OFL per NOTICE; craft-fonts is a separate build input) need checking per font if we ever ship them (Report G).
