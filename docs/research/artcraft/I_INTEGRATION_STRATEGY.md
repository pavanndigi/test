# Report I — Integration Strategies

| Field | Value |
| --- | --- |
| Date of research | 2026-11-28 |
| Inputs | Reports B–H; commits pdfcraft `c34c6c5a0bd8…`, wordcraft `72ca96a27c79…`, craft-libs `0a6e42b8…` |
| Confidence | Medium: effort figures are engineering estimates, not measurements |

## 1. Recommendation

Use **Option 4 (architectural reference)** as the default. Add two narrow pieces of **Option 2 (external process)**:

- `pdfcraft-cli` as a **baseline converter and extraction cross-check** in our benchmark harness;
- `wordcraft-cli validate` as a **DOCX structural QA gate**.

Consider **Option 3** only if we decide our DOCX writer should be Rust. Then build a thin sidecar around `craft-docx` + `craft-wordmodel`, pinned to one craft-libs commit. Avoid **Option 1** (copying crates into our tree): the churn and coupling cost more than writing what we need.

## 2. Options compared

| Criterion | 1. Direct source reuse | 2. External process | 3. Library integration (FFI/PyO3/WASM) | 4. Reference only |
| --- | --- | --- | --- | --- |
| What we would take | `craft-docx`, `craft-wordmodel`, `craft-opc`, `craft-xml`, `craft-zip`, `craft-drawingml`, `craft-metafile` (~110k lines incl. their deps) | `pdfcraft-cli run <tool>` (JSON), `wordcraft-cli validate/render/convert` | `craft-docx` behind a Rust sidecar or PyO3 module taking `craft-wordmodel` JSON | Algorithms and design choices only |
| Coupling | High: the crates depend on each other and on craft-libs' patch set | Low: JSON and files | Medium: the serde shape of `craft-wordmodel` becomes our contract | None |
| API stability | None: 0.1.0, unpublished, ~9k commits/month in craft-libs | CLI flags and tool schemas also change, but are documented and introspectable (`pdfcraft-cli tools`) | Low: model JSON is an internal format | n/a |
| Dependency conflicts | Moderate (quick-xml, chrono, zip versions; Rust edition 2024, rustc ≥ 1.95) | None | Moderate (inside the sidecar only) | None |
| Licence implications | MIT/Apache attribution; NOTICE handling (Report G) | Attribution if we redistribute binaries; none if research-only | Same as 1 for the linked crates | None (keep clean-room notes) |
| Performance overhead | None | Process start plus JSON per call; fine for batch, poor per-glyph | Small (one process or in-process) | n/a |
| Failure handling | Our responsibility | Excellent isolation: a crash in a converter does not kill our engine | Good with a sidecar; in-process FFI panics are contained by Rust, but resource exhaustion is shared | n/a |
| Initial effort (estimate) | 3–5 engineer-weeks | 0.5–1 week | 2–3 weeks | ~1 week of study, then part of normal build |
| Maintenance burden | High: we own a fork of fast-moving code | Low–Medium: re-pin binaries occasionally | Medium: re-pin the craft-libs commit; adapt to model changes | Low |
| Long-term flexibility | Low | High | Medium | High |
| Expected benefit | DOCX writer with floats, text boxes, tables, sections, font table | Baseline numbers; second-opinion extraction; DOCX validation | Same writer, isolated | Faster design of our own reading-order, table and font-substitution logic |

## 3. Option details

### Option 1: direct source reuse

- **Coupling evidence:** `craft-docx` depends on six craft-libs crates (`crates/docx/Cargo.toml`). `craft-pdf` readers need root `[patch.crates-io]` entries pinned to the same craft-libs revision (`crates/pdf/README.md`, "Backend provenance and consumer pins").
- **Maintenance:** ArtCraft's own apps already disagree on which craft-libs commit to use (PdfCraft `0a6e42b8`, WordCraft `0b8bbaf4`).
- **Verdict:** not recommended.

### Option 2: external process

- **PdfCraft CLI surface (Verified, `apps/pdfcraft-cli/src/main.rs`):** `info`, `render`, `text`, `edit`, `combine`, `extract`, `split`, `check`, `batch`, `run <tool>` with JSON scripts (`--report`), and an `mcp` server. Useful tools: `text_lines`, `text_paragraphs`, `page_images`, `doc_export_office`.
- **WordCraft CLI surface (Verified, `apps/wordcraft-cli/src/main.rs:20–55`):** `convert`, `info`, `text`, `inspect`, `render`, `validate` (exit 0 pass / 1 fail / 2 incomplete), `run`, `mcp`.
- **Interchange:** files plus JSON on stdout. Timeouts and crash isolation come for free.
- **Overhead (Observed, Report H §10; dev build, 2 vCPU):**
  - Small single-page calls (`info`, `render`, `text`, or a 7-step script) finish in 0.01–0.14 s each, including process start.
  - Opening and exporting a 300-page PDF to DOCX takes 0.8–1.0 s at 42 MB peak RSS.
  - A full 7-step script on that file takes 1.26 s.
  - Fine for batch benchmarking; too slow for per-glyph calls.
- **Failure handling (Observed):** errors come back as JSON (`"status": "error"` with a message), and later steps are marked `skipped`. The process exits non-zero. No crashes or hangs occurred in any run.

### Option 3: library integration

- `craft_wordmodel::Document` derives `Serialize`/`Deserialize` (`crates/wordmodel/src/lib.rs:98–101`). A ~200-line Rust binary could read model JSON and call `craft_docx::write`. This is the lowest-risk way to use the writer from Python.
- PyO3 or a C ABI would avoid process start but bind us to Rust build tooling in our main build.
- WASM is possible (PdfCraft and WordCraft ship web builds), but it offers no advantage for a server-side engine.

### Option 4: architectural reference

Worth studying, with file pointers:

- Reading order across columns: `pdfcraft/crates/export/src/layout.rs:627–700`.
- Table inference from aligned blocks plus ruled lines: `layout.rs:385` onward.
- "Positioned page" decision rule: `export/src/as_word.rs:320–345`.
- Paragraph grouping from lines, including inline-run continuation: `layout.rs:140–270`; `edit/src/text/blocks.rs`.
- Word metric-twin substitution list: `wordcraft/crates/fonts/src/word.rs:20–45`.
- Floating-object model mapped to OOXML: `wordcraft/crates/doc/src/para/float.rs`.
- Hostile-input budgets (decode limits, visit caps): `craft-pdf/README.md`.

## 4. Decision rules

- If our engine is **Python**: use Option 4 plus Option 2 (validator and baseline). Write DOCX with our own OOXML layer, adding the Option 3 sidecar only if python-docx's lack of floating shapes and text boxes becomes the bottleneck.
- If our engine is **Rust**: still prefer Option 4. Take `craft-docx` as a git dependency (Option 3 in-process) only after a two-week spike proves it round-trips our generated documents through Word cleanly.

## Limitations and open questions

- **Limitations:** effort figures are estimates. Only the Option 2 timings were measured (Report H §10, dev build). Options 1 and 3 were not prototyped.
- **Open question:** will storytold publish versioned crates? That would lower the maintenance cost of Options 1 and 3.
- **Open question:** does a `craft-docx` sidecar produce Word-faithful positioned output? The spike in Report L, Q14, answers this.
