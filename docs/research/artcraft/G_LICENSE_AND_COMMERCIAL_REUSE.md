# Report G — Open-Source Licence and Reuse Assessment

| Field | Value |
| --- | --- |
| Date of research | 2026-11-28 |
| Repositories and commits | pdfcraft `c34c6c5a0bd8…`; wordcraft `72ca96a27c79…`; craft-libs `0a6e42b8…` / `0b8bbaf4…` |
| Files inspected | `LICENSE-MIT`, `LICENSE-APACHE`, `NOTICE`, `LICENSES.toml`, `ATTRIBUTION.toml`/`.md`, `deny.toml`, `docs/brand/LICENSE-brand.txt`, `docs/licensing-self-check.md`, `AGENTS.md`, vendored crate manifests; dependency licence census in `evidence/dependency-licences.txt` |
| Confidence | High for first-party terms; Medium for the full transitive graph (census covers the `pdfcraft-cli` build graph) |

> This is a technical reading of licence files, **not legal advice**. Items marked ⚠ need legal review.

## 1. Bottom line

ArtCraft's own code is **dual-licensed MIT OR Apache-2.0** in all three repositories. Commercial use, modification and binary distribution are allowed with attribution, and source disclosure is not required. Choosing **Apache-2.0** adds an express patent licence. Everything else that needs attention sits outside the first-party code:

- trademarked ArtCraft brand assets;
- SIL OFL fonts;
- BSD-3-Clause Foxit fonts and Adobe CMaps bundled by Hayro;
- **CC-BY-SA-4.0 OCR model weights** (share-alike);
- MPL-2.0, which `deny.toml` permits in the dependency graph;
- ⚠ the copyright position of a codebase written largely with AI agents and contributed under no CLA or DCO.

## 2. First-party licences

| Repository | Declared licence | Evidence |
| --- | --- | --- |
| pdfcraft | MIT OR Apache-2.0 | `Cargo.toml:10`; `NOTICE` lines 1–4; `LICENSE-MIT`, `LICENSE-APACHE` |
| wordcraft | MIT OR Apache-2.0 | `Cargo.toml:18`; `LICENSE-MIT`, `LICENSE-APACHE`, `NOTICE` |
| craft-libs | MIT OR Apache-2.0 (workspace); `crates/http-url` Apache-2.0 only | `Cargo.toml:9`; `crates/http-url/Cargo.toml` |
| ArtCraft brand (name, wordmark, logos) | **Not open source**; limited permission for copies of the repo and official builds only | `pdfcraft/docs/brand/LICENSE-brand.txt` |

Contributor terms: no CLA, DCO or contributor-licence document was found (`contributors/` holds only `people.toml` and `contributors.json`). Contributions therefore fall under Apache-2.0 §5's default (inbound = outbound). **Verified (absence).**

## 3. Third-party material bundled or depended on

| Material | Licence | Where | Reuse note |
| --- | --- | --- | --- |
| Hayro (`hayro`, `-syntax`, `-interpret`, `-jbig2`, `-cmap`, `-postscript`) | Apache-2.0 OR MIT | `craft-libs/vendor/*/Cargo.toml` | Permissive. Patched fork. |
| Foxit standard-14 Type 1 substitute fonts (inside Hayro `embed-fonts`) | BSD-3-Clause ("Copyright 2014 PDFium Authors") | `pdfcraft/NOTICE` | Keep notice |
| Adobe CMap resources (hayro-cmap) | BSD-3-Clause | `pdfcraft/NOTICE` | Keep notice; no endorsement |
| Krilla (PDF writer), vello_cpu/vello_common, linesweeper | MIT OR Apache-2.0 | vendored manifests | Permissive |
| lopdf | MIT | `NOTICE` | Permissive |
| ICU4X segmenter data | Unicode-3.0 | `NOTICE` | Keep notice |
| CGATS001 ICC profile | CC0-1.0 | `NOTICE` | — |
| FOGRA39 characterisation data | Free redistribution if unmodified and Fogra credited | `craft-libs/NOTICE` | Conditions apply |
| Inter, JetBrains Mono, Dancing Script fonts | SIL OFL 1.1 (Dancing Script has a Reserved Font Name) | `pdfcraft/NOTICE`, `assets/fonts/OFL-*.txt` | Fonts may be bundled; not sold alone; renamed if modified |
| craft-fonts build input (BIZ UDPGothic, Shippori Mincho, BIZ UDMincho, Noto Sans Thai) | SIL OFL 1.1 | `pdfcraft/NOTICE` | Separate repository |
| egui default fonts | Ubuntu Font Licence 1.0, Hack, OFL (Noto Emoji), MIT | `pdfcraft/NOTICE` | UI only |
| Lucide icons | ISC and MIT | `NOTICE` | UI only |
| `ocrs` OCR engine | MIT/Apache-2.0 | `crates/ocr/src/lib.rs:4` | Permissive code |
| ⚠ **ocrs pre-trained models** | **CC-BY-SA-4.0**, fetched by `cargo xtask models` | `crates/ocr/src/lib.rs:4–5` | Share-alike on the model files: legal review before shipping them |
| ⚠ `acadrust` (in `craft-dwg`) | MPL-2.0 | `craft-libs/NOTICE` | File-level copyleft; irrelevant unless DWG is used |
| `aws-lc-rs` / `aws-lc-sys` (native signing) | See census (Apache-2.0 / ISC / OpenSSL-style) | `Cargo.lock`, `.cargo/config.toml` | Only for signatures |
| Policy | `deny.toml` allows MIT, MIT-0, Apache-2.0 (+LLVM exception), BSD-2/3, ISC, Zlib, Unicode-3.0, BSL-1.0, CC0-1.0, IJG, **MPL-2.0**, CDLA-Permissive-2.0 | `pdfcraft/deny.toml` | No GPL/LGPL/AGPL is allowed by policy |

The full census of crates in the build graph is in `evidence/dependency-licences.txt`.

## 4. Reuse matrix for the candidate components

Applies to `craft-docx`, `craft-wordmodel`, `craft-opc`, `craft-xml`, `craft-zip`, `craft-drawingml`, `craft-metafile`, `wordcraft-validate` and `pdfcraft-cli` used as a tool.

| Question | Answer under MIT OR Apache-2.0 |
| --- | --- |
| 1. Commercial use? | Yes |
| 2. Modify? | Yes |
| 3. Distribute binaries? | Yes |
| 4. Must disclose source? | No (for these crates; check MPL-2.0 files if any enter the graph) |
| 5. Attribution notices? | Yes: keep the copyright notice and licence text; with Apache-2.0, also carry the `NOTICE` content and mark modified files |
| 6. Patent provisions? | Apache-2.0 grants a patent licence that terminates on patent litigation; MIT has none, so pick Apache-2.0 |
| 7. Additional restrictions? | Trademark: do not use ArtCraft marks. ⚠ AI-assisted provenance (see §6). |
| 8. Separate terms for models or assets? | Yes: OCR models CC-BY-SA-4.0; fonts OFL; Foxit/Adobe data BSD-3-Clause |

## 5. Mode of reuse and what it implies

| Mode | Licence implication | Recommended for |
| --- | --- | --- |
| Reusing source code | Keep licence and NOTICE; mark changes; we own maintenance of a fast-moving fork | Small, stable pieces only |
| Linking a library (Cargo dependency) | Same attribution duties; transitive licences come with it (run `cargo deny` on our graph) | `craft-docx` + `craft-wordmodel` in a sidecar |
| Running an external application (`pdfcraft-cli`, `wordcraft-cli`) | No linking; distributing the binary still needs its notices (including Hayro's BSD fonts and data) | Research harness, benchmarking |
| Using an API | Not applicable; no hosted API | — |
| Reimplementing independently | No licence obligation for ideas and algorithms; keep clean-room records | Layout heuristics, reading order, font-metric matching |

## 6. Items flagged for legal review

1. ⚠ **AI-assisted authorship.** All three repositories carry `AGENTS.md`/`CLAUDE.md` agent instructions, and commit volumes are in the thousands per month. Copyright ownership and enforceability for AI-generated code vary by jurisdiction, which affects the strength of any licence we rely on. PdfCraft's `AGENTS.md` rules 23–26 require clean-room practice: no reading GPL/LGPL/AGPL source and no copying other products. That is a positive signal, but we cannot verify it.
2. ⚠ **CC-BY-SA-4.0 OCR models.** Do not ship them without review. We do not need them (PaddleOCR/Tesseract are alternatives).
3. ⚠ **MPL-2.0 allowed by policy.** Confirm whether any MPL-2.0 crate enters the graph of the components we would use (census).
4. **Brand assets:** exclude `docs/brand/` and any ArtCraft naming from our product.
5. **Patched third-party forks:** licences are permissive, but attribution must name both upstream and the ArtCraft patches.

## 7. Open questions

- No licence statement covers test fixtures in `tests/`. `AGENTS.md` rule 24 says provenance is recorded in `ATTRIBUTION.toml`; we would not reuse fixtures anyway.
- Whether ArtCraft would relicense or offer a commercial agreement is **Unknown**; it is not needed under MIT OR Apache-2.0.

## Limitations

- Licences were read from manifests, `LICENSE*`, `NOTICE`, `ATTRIBUTION.toml` and `deny.toml`. The `cargo tree` census in `evidence/dependency-licences.txt` reports declared SPDX expressions, not a file-by-file scan of vendored C code, fonts or data.
- None of this is legal advice. Every "Flag" above should go to counsel.
