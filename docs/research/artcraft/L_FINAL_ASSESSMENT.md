# Report L — Final Strategic Assessment

| Field | Value |
| --- | --- |
| Date of research | 2026-11-28 |
| Repositories | https://github.com/storytold/pdfcraft `c34c6c5a0bd86d466f9f814c14b4cfdaa55cd7e2`; https://github.com/storytold/wordcraft `72ca96a27c795d6289775f6c12954c2cdbd62908`; https://github.com/storytold/craft-libs `0a6e42b8…` (pdfcraft pin) and `0b8bbaf4…` (wordcraft pin) |
| Basis | Reports A–K; source citations are given in those reports and repeated here where they carry the argument |
| Confidence | High on the verdict; Medium on effort estimates (Report I) |

## Verdict: **Reference only**

Study ArtCraft's architecture and implement our engine independently. Two optional, **tool-level** uses are allowed alongside the verdict; neither links ArtCraft code into our engine:

1. Run `wordcraft-cli validate` as a DOCX structural check in CI, as an external process.
2. Prototype a `craft-docx` sidecar for positioned DOCX writing. Keep it only if it beats our own emitter on the benchmark.

If the prototype wins, the verdict becomes **Partially adopt** for that one component.

### Why not Adopt or Partially adopt now

- **The parts that decide reconstruction quality are missing or weak.**
  - Font identification is name-based only (`pdfcraft/crates/engine/src/compare.rs:221–224`).
  - The exporter writes a single body font, Arial (`pdfcraft/crates/export/src/as_docx.rs:46`).
  - Report H measured this on every file, along with lost vectors, collapsed columns and a broken table grid.
- **The strong parts duplicate better-established engines.** Parsing and rendering work, and PdfCraft matched Poppler within 1–2% ink on every page in Report H. But PDFium does the same job with years of production use, and PdfCraft's renderer is the third-party Hayro library, described in its own source as a "bootstrap" (`pdfcraft/crates/render/src/lib.rs:3`).
- **The code moves too fast to vendor.** Two apps pin different craft-libs commits. Every crate is version 0.1.0 and unpublished. The code is heavily AI-agent-developed with no CLA (Reports A, E, G).

### Why not Avoid

The project has genuine value as a reference:
- a permissive, hardened PDF object layer;
- a DOCX writer whose model already covers floats, anchored text boxes, sections and tables (`craft-libs/crates/docx/src/write/story/object.rs:290, 410, 644`);
- a spec-derived OOXML validator (`wordcraft/crates/validate/src/lib.rs:1–12`);
- a word processor that documents its own Word-parity gaps (`wordcraft/docs/layout-parity.md:14`).

## Answers to the 15 questions

**1. Is ArtCraft technically mature enough to be useful?**
Partly. PdfCraft is a substantial, well-tested application: 9,513 `#[test]` functions in the repository (Report B), and no crashes on the Report H corpus.
- Its rendering, text extraction, editing and saving behaved correctly on the corpus.
- Its PDF→DOCX conversion is self-described as weak (`pdfcraft/docs/gaps.md:193`) and measured as weak in Report H.
- WordCraft self-estimates ~55% Word layout parity.

It is mature enough to learn from, not to build on.

**2. Is PdfCraft a real PDF editor or primarily a viewer/annotation application?**
A real editor. It rewrites content streams in place and keeps positioning operators (`pdfcraft/crates/edit/src/text/rewrite.rs`). It also edits images, pages, forms, redactions and annotations, and saves incrementally. Report H confirmed:
- in-place line edits;
- a 1,199-byte incremental save on a 300-page file;
- encryption preserved on save.

Its limits:
- **No reflow:** longer text overlapped the next column or paragraph.
- **Font switching:** characters outside WinAnsi switch the edit to a generated Type 3 Inter font.
- **No CJK edits** in a source build.
- **No vector-path editing.**

**3. Does it have a reusable PDF document model?**
At the object level, yes. The `craft-pdf` COS layer (parser, xref, object streams, encryption, writer) is a standalone crate with 8 packages in its dependency graph, all MIT/Apache. PdfCraft uses it through `pdfcraft/crates/cos/src/lib.rs:1–2`.

At the page level, no. PdfCraft's text model (`TextLine` in `pdfcraft/crates/edit/src/text.rs:82`) is internal to the editor, not a published, reconstruction-grade IR.

**4. Does it implement PDF parsing or wrap existing engines?**
Both:
- **Parsing and writing:** its own (craft-pdf COS).
- **Page interpretation and rendering:** delegated to the third-party Hayro library (vendored and patched in `craft-libs/vendor/hayro*`), rasterised by vello_cpu.
- **Fallback:** lopdf (vendored).
- **Krilla** (PDF writing) is used by WordCraft, not by PdfCraft: its patch is unused in PdfCraft's build.

**5. Does it have useful typography infrastructure?**
For DOCX layout, yes: WordCraft has Word-style font resolution with metric-compatible twins (`wordcraft/crates/fonts/src/word.rs:1–45`), harfrust shaping and UAX #14 line breaking with Word exceptions.

For PDF reconstruction, no. Nothing identifies embedded fonts or maps glyph metrics to installable fonts (Report D).

**6. Can WordCraft contribute to DOCX generation?**
Yes, through `craft-docx` and `craft-wordmodel`, which WordCraft uses to read and write OOXML. Their model covers what python-docx lacks:
- page-anchored text boxes and floating drawings;
- section properties and columns;
- tables;
- a font table.

PdfCraft's own exporter produced well-formed anchored text boxes with rotation in Report H. WordCraft rendered the rotation; LibreOffice did not. `wordcraft-validate` can act as a structural QA gate: it caught malformed XML, dangling relationships and missing content types. It skips anything inside `mc:AlternateContent`, though, so drawings and text boxes need checks of our own (Report H §9).

**7. Are its Rust components reusable independently?**
Technically, yes: each crate is a Cargo package with a permissive licence and its own tests.

Practically, it is costly:
- `craft-docx` depends on six sibling crates.
- `craft-pdf` readers need workspace patch pins.
- APIs are unversioned (0.1.0) and unpublished.
- ArtCraft's own apps pin different commits (Reports E, I).

**8. What is the most valuable component for our project?**
`craft-docx` with `craft-wordmodel`, as a candidate positioned-DOCX writer behind a JSON sidecar. Runner-up: `wordcraft-validate`.

**9. What should we avoid?**
- PdfCraft's DOCX exporter as a foundation.
- Copying crates into our tree.
- Hayro, or ArtCraft's rendering stack, as our renderer.
- The ocrs models (CC-BY-SA-4.0) in any shipped product.
- Linking the GUI or egui fork.
- Depending on unpinned craft-libs revisions.

**10. What can we legally reuse in a commercial product?**
On the face of the licences:
- **First-party code:** MIT OR Apache-2.0, so it can be used, modified and distributed with attribution and NOTICE handling.
- **Crate graphs** of pdfcraft-cli, wordcraft-cli, craft-docx, craft-pdf and craft-metafile: no copyleft licences declared (`evidence/dependency-licences.txt`).

Flags for legal review (not legal advice):
- **ArtCraft brand:** under trademark terms.
- **ocrs models:** CC-BY-SA-4.0.
- **MPL-2.0:** allowed by `deny.toml`; the one MPL crate, `acadrust`, sits in `craft-dwg` only.
- **Fonts:** OFL and BSD terms.
- **Provenance:** AI-generated code, and no CLA (Report G).

**11. Would integrating ArtCraft save engineering time?**
Only in two places:
- **Positioned DOCX writing:** perhaps 2–4 weeks saved if `craft-docx` works as a sidecar.
- **DOCX validation:** days saved.

Everywhere else, PDFium plus our own logic is as fast to build and simpler to own. Direct reuse would cost 3–5 weeks up front plus ongoing fork maintenance (Report I).

**12. Would integration introduce more complexity than value?**
Yes for anything beyond the two tool-level uses. A Rust toolchain at edition 2024, a fast-moving pinned monorepo, a patched dependency set, and a JSON contract on an internal model are real complexity. Only a measured gain in DOCX fidelity would justify them.

**13. Should we reuse code, integrate libraries, or only study the architecture?**
Study the architecture. Integrate only as external tools (validator, benchmark baseline, optional writer sidecar). Do not reuse code.

**14. What should we prototype first?**
A two-day spike that answers both open questions:

1. Hand-write a `craft-wordmodel` JSON for corpus files 2, 3, 5 and 10. Use exact fonts, absolute positions, anchored text boxes and table borders. Write it with a tiny `craft-docx` sidecar, render in Word, and score against the PDF.
2. Run `wordcraft-cli validate` on those outputs and on our own emitter's output.

**15. What is the recommended next step?**
Build our pipeline skeleton on PDFium:
- glyph extraction with font identity;
- our own IR;
- our own minimal OOXML emitter;
- the Report H harness, extended with Word rendering, as the benchmark.

Run the `craft-docx` spike in parallel, then decide sidecar or own emitter on measured scores.

## Evidence summary for the verdict

| Claim | Evidence |
| --- | --- |
| Rendering is Hayro, not ArtCraft-native | `pdfcraft/crates/render/src/lib.rs:1–6`; `pdfcraft/Cargo.toml:184–188` patches |
| DOCX export uses one font | `pdfcraft/crates/export/src/as_docx.rs:46`; Report H §8.4: Arial in every export |
| Font identity is name-based | `pdfcraft/crates/engine/src/compare.rs:221–224` |
| Vector, columns, headers and tables are weak in export | Report H §7, files 4, 5, 6, 8, 9, 11; `pdfcraft/docs/gaps.md:193–216` |
| Editing is real but does not reflow | Report H §8.3; `pdfcraft/crates/edit/src/text/fallback.rs:35` |
| craft-docx covers anchors and text boxes | `craft-libs/crates/docx/src/write/story/object.rs:290, 410, 644` |
| Licences are permissive, with flagged exceptions | Report G; `evidence/dependency-licences.txt` |
| WordCraft parity is partial | `wordcraft/docs/layout-parity.md:14` |

## Open questions

- Does `craft-docx` output render in Word as positioned? The spike in Q14 answers this.
- Will storytold publish versioned crates? If they do, the maintenance cost in Report I falls.
- What does legal review say on AI-authored code provenance and on the absence of a CLA?

## Limitations

- **Test set:** the verdict rests on a synthetic 15-file test set.
- **No Word rendering:** WordCraft and LibreOffice stood in for Word.
- **Licences:** licence conclusions need legal review.
- **Shelf life:** the codebases change daily, so findings hold for the pinned commits only.
