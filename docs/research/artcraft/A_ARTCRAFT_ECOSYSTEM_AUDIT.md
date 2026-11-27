# Report A — ArtCraft Ecosystem and Repository Audit

| Field | Value |
| --- | --- |
| Date of research | 2026-11-28 |
| Primary repositories | `storytold/pdfcraft`, `storytold/wordcraft`, `storytold/craft-libs` |
| Commits audited | pdfcraft `c34c6c5a0bd86d466f9f814c14b4cfdaa55cd7e2` (2026-11-27) · wordcraft `72ca96a27c795d6289775f6c12954c2cdbd62908` (2026-11-27) · craft-libs `0a6e42b80bfd586aee6ee1144aa98cf1ea37a844` (pinned by PdfCraft) and `0b8bbaf4c842da2d47de7b3fddd7170ba6115541` (pinned by WordCraft); craft-libs HEAD was `c88d044c0f848706f552b9759ec49f5a39b63848` |
| Method | Read-only clones; source, manifests, lockfiles, docs and git history inspected. No ArtCraft code was copied into any project. |
| Confidence | High for the three audited repositories; Low for other apps (descriptions and file listings only) |

Evidence labels used throughout: **Verified** (source, tests, config), **Observed** (ran it), **Inferred**, **Hypothesis**, **Unknown**.

## 1. Bottom line

ArtCraft is a family of Rust desktop applications published by the GitHub organisation `storytold`, all built on one shared library monorepo, `craft-libs`. For PDF reconstruction only three repositories matter: **PdfCraft** (PDF viewer/editor), **WordCraft** (Word-compatible word processor) and **craft-libs** (shared PDF, DOCX, font and text crates). The codebase is very large, very young (first commits in late September and early October 2026) and changes extremely fast.

## 2. How the official repositories were verified

| Step | Finding | Label |
| --- | --- | --- |
| Official site footer and buttons | getartcraft.com links the `storytold` organisation, `storytold/craft-launcher` and `storytold/artcraft` | Verified (site) |
| PdfCraft app page | Links `https://github.com/storytold/pdfcraft`, release `v0.22.0`, "Early alpha" | Verified (site) |
| WordCraft app page | Links `https://github.com/storytold/wordcraft`, release `v0.19.1`, "In development" | Verified (site) |
| craft-libs | Not linked from the site directly; reached through PdfCraft's `Cargo.toml` (`git = "https://github.com/storytold/craft-libs"`, 30+ pins) and WordCraft's (38 pins) | Verified (manifests) |
| Name alias | `storytold/printcraft` resolves to the same HEAD SHA as `storytold/pdfcraft` (`c34c6c5a0bd8`), so it is a redirect or alias of PdfCraft | Verified (`git ls-remote`) |

No fork or look-alike repository was used. Everything audited was reached from links on getartcraft.com or from manifests inside those repositories.

## 3. Repository inventory

| Repository | Commit (HEAD on 2026-11-28) | Main language | Licence (from source) | Maturity signal | Relevance to PDF reconstruction |
| --- | --- | --- | --- | --- | --- |
| [pdfcraft](https://github.com/storytold/pdfcraft) | `c34c6c5a0bd8` | Rust (562k lines excl. vendor; +125k vendored) | MIT OR Apache-2.0 (`Cargo.toml:10`, `NOTICE`) | v0.22.0, site says "Early alpha"; 9,513 `#[test]` functions; 10 CI workflows; 4 fuzz targets | **High**: PDF object layer, text-line extraction, reading-order heuristics, PDF→DOCX exporter |
| [wordcraft](https://github.com/storytold/wordcraft) | `72ca96a27c79` | Rust (371k lines) | MIT OR Apache-2.0 (`Cargo.toml:18`) | Workspace says 0.18.1 while the site lists v0.19.1; site says "In development"; 5,786 tests; 14 workflows | **Medium**: DOCX model, Word-like layout engine, DOCX validator |
| [craft-libs](https://github.com/storytold/craft-libs) | `c88d044c0f84` (audited at the two pins above) | Rust (1.83M lines excl. vendor; 242 crates) | MIT OR Apache-2.0 workspace (`Cargo.toml:9`); one crate Apache-2.0 only (`crates/http-url`); `craft-dwg` depends on MPL-2.0 `acadrust` (`NOTICE`) | 16,017 tests; 32 workflows; 5 fuzz targets | **High**: `craft-pdf`, `craft-docx`, `craft-wordmodel`, `craft-opc`, `craft-drawingml`, `craft-metafile`, font crates |
| [designcraft](https://github.com/storytold/designcraft) | `cc0dd6625e7a` | Rust | Apache-2.0 shown on GitHub (not checked in source) | Crates include `idml`, `pdf` (export), `epub`, `compose` | Low–Medium: page-layout model; PDF is export only (file list) |
| [vectorcraft](https://github.com/storytold/vectorcraft) | `98b56f3d97ab` | Rust | Apache-2.0 shown on GitHub (not checked in source) | `crates/engine/src/cmd/fileio/pdfimport.rs` imports PDF pages as vector art | Medium for vector extraction (not audited) |
| photocraft, lightcraft, filmcraft, effectcraft, anicraft, deckcraft, gridcraft, figcraft, texturecraft, materialcraft, soundcraft, cadcraft | SHAs in `evidence/repo-heads.txt` | Rust (per GitHub listing) | Not checked in source | Not audited | Low |
| artcraft, craft-launcher, autocraft | SHAs in `evidence/repo-heads.txt` | Rust / TypeScript | GitHub shows "Other" for `artcraft` | Not audited | None (AI studio, launcher) |

The org page reported 83 repositories, but GitHub's repository list only rendered a partial, older view, so this inventory covers the repositories linked from the website plus those named in it. **Unknown:** whether other repositories hold PDF-relevant code.

## 4. Ecosystem map by creative-software category

| Category | ArtCraft app | Status of the mapping |
| --- | --- | --- |
| Acrobat-like PDF workflows | PdfCraft | **Verified** from source (Report B) |
| Word-like document editing | WordCraft | **Verified** from source (Report C) |
| InDesign-like page layout | DesignCraft | **Inferred** from crate names (`idml`, `compose`, `pdf` export) |
| Illustrator-like vector editing | VectorCraft | **Inferred** from crate names (`pathops`, `svg`, `eps`, `affinity`, `pdf`) and `pdfimport.rs` header |
| Photoshop-like image editing | PhotoCraft (and LightCraft for non-destructive) | Unknown (GitHub description only) |
| PowerPoint / Excel-like | DeckCraft / GridCraft | Unknown (website names only) |
| Video, motion, animation, 3D, audio, CAD | FilmCraft, EffectCraft, AniCraft, TextureCraft, MaterialCraft, SoundCraft, CADCraft | Not relevant; not audited |

See `diagrams/ecosystem.md` for the dependency picture.

## 5. Build systems, languages and shared infrastructure

- **Language and build:** Rust edition 2024, Cargo workspaces, `rust-version = "1.95"` in all three manifests. The website says "Rust 1.90 or newer", which the manifests contradict. **Verified.**
- **UI:** egui/eframe 0.37 from a `storytold/egui` fork (`pdfcraft/Cargo.toml:195–202`). **Verified.**
- **Shared crates:** apps pin `craft-libs` by full commit, and each app pins a different revision (PdfCraft `0a6e42b8…`, WordCraft `0b8bbaf4…`). **Verified.** Consequence: the "shared" libraries are versioned per app, not as releases.
- **Vendored and patched third-party code:** PdfCraft vendors and patches `lopdf`, `vello_cpu`, `vello_common`, `winit`, `egui-wgpu`, `edit-session`; craft-libs vendors patched `hayro`, `hayro-syntax`, `hayro-interpret`, `krilla` and others (`craft-libs/Cargo.toml` `exclude`, `crates/pdf/README.md`). **Verified.**
- **Policy files:** `AGENTS.md` and `CLAUDE.md` exist in all three repositories, and PdfCraft's `AGENTS.md` (rules 23–26) sets clean-room and licence rules for contributors and agents. **Verified.**

## 6. Activity, contributors, issues and CI

| Metric | PdfCraft | WordCraft | craft-libs |
| --- | --- | --- | --- |
| First commit | 2026-09-30 | 2026-10-05 | 2026-10-05 |
| Commits on default branch | 7,816 | 3,730 | 10,324 |
| Distinct author names | 430 | 301 | 193 |
| Commits in Nov 2026 (to the 27th/28th) | 3,269 | 1,069 | 9,346 |
| Open issues / PRs (GitHub page) | ~1.8k / ~1.2k | ~1k / 846 | not read |
| Stars / forks (GitHub page) | 20.6k / 7.6k | 16.2k / 4.4k | 478 stars (org listing) |
| CI workflows | 10 (CI, fuzz, FreeBSD, Nix, nightly macOS, release, SonarCloud, Windows ARM64…) | 14 | 32 |

Sources: full (unshallow) git histories; GitHub pages for [PdfCraft](https://github.com/storytold/pdfcraft) and [WordCraft](https://github.com/storytold/wordcraft).

**Interpretation (Inferred):** thousands of commits a month across hundreds of contributor names in two months, plus agent-instruction files in every repository, indicate heavily automated, AI-agent-assisted development. That explains the breadth. It also means APIs churn constantly and no crate has a stable release. Star counts at this scale for two-month-old projects were not used as evidence of quality.

## 7. Documentation quality

- **Strong:** module-level Rust docs are dense and specific (many cite ISO 32000-2 and ECMA-376 sections), each crate states its limitations, and parity documents (`wordcraft/docs/layout-parity.md`, `pdfcraft/docs/gaps.md`) record what is and is not matched. **Verified.**
- **Weak:** documents are enormous change logs. PdfCraft's `ROADMAP.md` is 305 KB, and a single heading in `layout-parity.md` carries several kilobytes of "previously trivial" entries. Marketing claims ("written from scratch in pure Rust", [GitHub About](https://github.com/storytold/pdfcraft)) are contradicted by the code: rendering bootstraps on third-party Hayro, and native signing uses `aws-lc` (C). **Verified.**

## 8. Licensing summary

Application and library code: **MIT OR Apache-2.0** (dual). Exceptions and separate terms are covered in Report G: trademarked brand assets, OFL fonts, BSD-3-Clause Foxit/Adobe data inside Hayro, CC-BY-SA-4.0 OCR models (fetched separately), and an MPL-2.0 dependency in `craft-dwg`.

## 9. Limitations and open questions

- Only three repositories were audited in depth; DesignCraft and VectorCraft were inspected by file listing and one header only.
- The org's full repository list could not be enumerated: the GitHub API is restricted in this environment, and the rendered list was incomplete.
- Release artefacts were not downloaded; behaviour was tested by building from source (Report H).
- **Open question:** will the craft-libs crates ever be published as versioned releases? Today they are consumed by git commit only.
