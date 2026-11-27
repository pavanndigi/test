# Evidence index

| Path | What it holds |
| --- | --- |
| `repo-heads.txt` | `git ls-remote` heads for 23 storytold repositories, plus the craft-libs pins used by PdfCraft and WordCraft |
| `git-activity.txt` | Per-repository first and last commit, commit counts, monthly activity and top authors |
| `dependency-licences.txt` | Licence census (`cargo tree`) for the pdfcraft-cli, wordcraft-cli, craft-docx, craft-pdf and craft-metafile graphs |
| `citation-check.json` | Output of `tools/verify_citations.py`. Every `path:line` citation in the reports was resolved against the pinned trees. |
| `functional/` | Report H runs, described below |
| `tools/` | Scripts that produced everything here, plus the test-set manifest (`corpus_manifest.json`) |

## `functional/` contents

- **`NN_name/` (one per test file):** the input PDF, `steps.json`, the full `script_report.json`, `export.docx`, `edited.pdf`, the LibreOffice conversion `export.pdf`, and page-1 renders (`ref_p1.png` Poppler, `pdfcraft_p1.png`, `edited_p1.png`, `docx_via_libreoffice_p1.png`).
- **Summary data:**
  - `results.json`: per-test summary.
  - `ink_metrics.json`: ink F1 scores.
  - `cli-tools.txt`: the 217 automation tool schemas.
  - `cli-version-help.txt`: CLI version and help output.
- **Targeted runs:**
  - `extra/`: paragraph-edit and glyph-coverage edit tests.
  - `ocr/`: Tesseract OCR run (searchable and editable outputs, DOCX).
  - `perf/`: timings (`timings.jsonl`) and the 300-page check report.
  - `wordcraft/`: `wordcraft-cli validate` and `convert` results, renders, and the `negative/` injected-defect controls.
- **Build logs:** `pdfcraft-cli-build.log`, `wordcraft-cli-build.log`.

## Known items in `citation-check.json`

Four entries show as "missing" but were confirmed by hand:

- **`crates/engine/src/cmd/fileio/pdfimport.rs`:** in the vectorcraft repository at `98b56f3d97ab` (blobless clone; confirmed with `git ls-tree`).
- **`results.json`, `ink_metrics.json`:** local evidence files under `functional/`.

## How to reproduce

```
python3 -I tools/make_corpus.py corpus
cargo build --locked -p pdfcraft-cli        # in pdfcraft @ c34c6c5a
cargo build --locked -p wordcraft-cli       # in wordcraft @ 72ca96a2
python3 -I tools/run_functional.py <pdfcraft-cli> corpus evidence/functional
python3 -I tools/ink_metrics.py evidence/functional
python3 -I tools/run_wordcraft.py <wordcraft-cli> evidence/functional
```

The harness needs Poppler, qpdf, LibreOffice, scikit-image, SciPy and Pillow. The OCR run also needs Tesseract.
