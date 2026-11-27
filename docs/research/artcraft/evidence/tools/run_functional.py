"""Report H functional validation of pdfcraft-cli against the controlled corpus.

Usage: python3 -I run_functional.py <pdfcraft-cli> <corpus-dir> <out-dir>

For each PDF: open/info, render page 1 (compared with Poppler's pdftoppm by SSIM),
extract text (compared with the manifest's ground truth), run an automation script
(text_lines, text_paragraphs, page_images, Word export, edit the first line, save),
reopen the saved file, and score the exported DOCX (structure, text, LibreOffice
render SSIM).  Everything is written to <out-dir>/results.json plus per-file folders.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile

import numpy as np
from PIL import Image
from skimage.metrics import structural_similarity

CLI, CORPUS, OUT = sys.argv[1:4]
os.makedirs(OUT, exist_ok=True)
manifest = json.load(open(os.path.join(CORPUS, "manifest.json")))
PASSWORDS = {"15_password_protected.pdf": "secret"}
EDIT_TEXT = "EDITED BY TEST HARNESS"


def run(cmd, timeout=900, cwd=None):
    t0 = time.time()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd)
        return {"rc": p.returncode, "secs": round(time.time() - t0, 2),
                "stdout": p.stdout, "stderr": p.stderr[-4000:]}
    except subprocess.TimeoutExpired:
        return {"rc": "timeout", "secs": round(time.time() - t0, 2), "stdout": "", "stderr": "timeout"}


def ssim(a_path, b_path):
    if not (os.path.exists(a_path) and os.path.exists(b_path)):
        return None
    a = Image.open(a_path).convert("L")
    b = Image.open(b_path).convert("L").resize(a.size)
    return round(float(structural_similarity(np.asarray(a), np.asarray(b), data_range=255)), 4)


def norm(s):
    return re.sub(r"\s+", " ", s).strip().lower()


def truth_strings(entry):
    gt = entry["ground_truth"]
    out = []
    if isinstance(gt, list):
        for g in gt:
            out.append(g["text"] if isinstance(g, dict) else g)
    elif isinstance(gt, dict):
        for k in ("header", "page1"):
            if k in gt:
                out.append(gt[k])
        if "rows" in gt:
            out += [c for row in gt["rows"] for c in row]
        if "page2" in gt:
            out += gt["page2"]
    return [s for s in out if s and "N of" not in s]


def found_ratio(text, strings):
    if not strings:
        return None
    t = norm(text)
    return round(sum(1 for s in strings if norm(s) in t) / len(strings), 3)


def docx_stats(path):
    if not os.path.exists(path):
        return None
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf8", "replace")
        names = z.namelist()
        styles = z.read("word/styles.xml").decode("utf8", "replace") if "word/styles.xml" in names else ""
        fonttable = z.read("word/fontTable.xml").decode("utf8", "replace") if "word/fontTable.xml" in names else ""
    fonts = sorted(set(re.findall(r'w:rFonts[^>]*w:ascii="([^"]+)"', xml)))
    texts = re.findall(r"<w:t(?: [^>]*)?>([^<]*)</w:t>", xml)
    return {
        "paragraphs": xml.count("<w:p>") + xml.count("<w:p "),
        "tables": xml.count("<w:tbl>"),
        "text_boxes": xml.count("<w:txbxContent"),
        "anchored_drawings": xml.count("<wp:anchor"),
        "inline_drawings": xml.count("<wp:inline"),
        "sections": xml.count("<w:sectPr"),
        "fonts_named_in_runs": fonts,
        "fonts_in_styles": sorted(set(re.findall(r'w:rFonts[^>]*w:ascii="([^"]+)"', styles))),
        "font_table": sorted(set(re.findall(r'<w:font w:name="([^"]+)"', fonttable))),
        "bold_runs": xml.count("<w:b/>") + xml.count("<w:b "),
        "italic_runs": xml.count("<w:i/>") + xml.count("<w:i "),
        "font_sizes_half_pt": sorted(set(int(v) for v in re.findall(r'<w:sz w:val="(\d+)"', xml))),
        "headers": len([n for n in names if re.match(r"word/header\d*\.xml", n)]),
        "footers": len([n for n in names if re.match(r"word/footer\d*\.xml", n)]),
        "media_files": len([n for n in names if n.startswith("word/media/")]),
        "text": " ".join(texts),
    }


results = {}
pdfs = sorted(f for f in os.listdir(CORPUS) if f.endswith(".pdf"))
for name in pdfs:
    entry = manifest[name]
    if name.startswith("15_"):  # encrypted copy of 02: reuse 02's text ground truth
        entry = dict(manifest["02_multiple_fonts.pdf"], contains=entry["contains"])
    work = os.path.join(OUT, name[:-4])
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work)
    src = os.path.join(work, name)
    shutil.copy(os.path.join(CORPUS, name), src)
    pw = PASSWORDS.get(name)
    pwargs = ["--password", pw] if pw else []
    r = {"contains": entry["contains"]}

    r["info"] = run([CLI, "info", src] + pwargs)
    if pw:
        r["info_without_password"] = run([CLI, "info", src])
    r["opened"] = r["info"]["rc"] == 0

    ref_png = os.path.join(work, "ref_p1")
    run(["pdftoppm", "-r", "100", "-f", "1", "-l", "1", "-png", "-singlefile"]
        + (["-upw", pw] if pw else []) + [src, ref_png])
    out_png = os.path.join(work, "pdfcraft_p1.png")
    r["render"] = run([CLI, "render", src, "--page", "1", "--dpi", "100", "--out", out_png] + pwargs)
    r["render_ssim_vs_poppler"] = ssim(ref_png + ".png", out_png)

    r["text"] = run([CLI, "text", src] + pwargs)
    r["text_truth_found"] = found_ratio(r["text"]["stdout"], truth_strings(entry))

    docx = os.path.join(work, "export.docx")
    edited = os.path.join(work, "edited.pdf")
    steps = [
        {"tool": "doc_open", "args": dict({"path": src}, **({"password": pw} if pw else {}))},
        {"tool": "text_lines", "args": {"doc": 1, "page": 1}},
        {"tool": "text_paragraphs", "args": {"doc": 1, "page": 1}},
        {"tool": "page_images", "args": {"doc": 1, "page": 1}},
        {"tool": "doc_export_office", "args": {"doc": 1, "path": docx}},
        {"tool": "text_edit", "args": {"doc": 1, "page": 1, "line": 1, "text": EDIT_TEXT}},
        {"tool": "doc_save", "args": {"doc": 1, "path": edited}},
    ]
    script = os.path.join(work, "steps.json")
    json.dump(steps, open(script, "w"), indent=1)
    r["script"] = run([CLI, "run", "--script", script, "--root", work, "--report"])
    open(os.path.join(work, "script_report.json"), "w").write(r["script"]["stdout"])
    try:
        r["script_report"] = json.loads(r["script"]["stdout"])
    except Exception:
        r["script_report"] = None
    r["script"]["stdout"] = r["script"]["stdout"][:2000]
    if r["script_report"]:
        summ = []
        for stp in r["script_report"].get("steps", []):
            res = stp.get("result")
            res0 = res[0] if isinstance(res, list) and res else (res if isinstance(res, dict) else {})
            summ.append({"tool": stp.get("tool"), "status": stp.get("status"), "error": stp.get("error"),
                         "count": res0.get("count") if isinstance(res0, dict) else None,
                         "result_keys": sorted(res0.keys()) if isinstance(res0, dict) else None,
                         "export": {k: res0.get(k) for k in ("bytes", "truncated", "truncated_pages")} if stp.get("tool") == "doc_export_office" and isinstance(res0, dict) else None})
        r["script_report"] = {"ok": r["script_report"].get("ok"), "steps": summ}
    r["text"]["stdout_chars"] = len(r["text"]["stdout"])
    r["text"]["stdout"] = r["text"]["stdout"][:2000]

    if os.path.exists(edited):
        r["edited_info"] = run([CLI, "info", edited] + pwargs)
        ed_png = os.path.join(work, "edited_p1")
        run(["pdftoppm", "-r", "100", "-f", "1", "-l", "1", "-png", "-singlefile"]
            + (["-upw", pw] if pw else []) + [edited, ed_png])
        r["edited_ssim_vs_original"] = ssim(ref_png + ".png", ed_png + ".png")
        txt = run(["pdftotext"] + (["-upw", pw] if pw else []) + ["-f", "1", "-l", "1", edited, "-"])
        r["edit_text_present"] = EDIT_TEXT.lower() in txt["stdout"].lower()
        full_ed = run(["pdftotext"] + (["-upw", pw] if pw else []) + [edited, "-"])["stdout"]
        r["truth_found_after_edit"] = found_ratio(full_ed, truth_strings(entry))
        r["qpdf_check_edited"] = run(["qpdf", "--check"] + ([f"--password={pw}"] if pw else []) + [edited])["rc"]

    st = docx_stats(docx)
    if st:
        orig_text = run(["pdftotext"] + (["-upw", pw] if pw else []) + [src, "-"])["stdout"]
        st["truth_found_in_docx"] = found_ratio(st["text"], truth_strings(entry))
        st["pdf_words"] = len(orig_text.split())
        st["docx_words"] = len(st["text"].split())
        st.pop("text")
        lo = run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", work, docx], timeout=300)
        lo_pdf = os.path.join(work, "export.pdf")
        if os.path.exists(lo_pdf):
            lo_png = os.path.join(work, "docx_via_libreoffice_p1")
            run(["pdftoppm", "-r", "100", "-f", "1", "-l", "1", "-png", "-singlefile", lo_pdf, lo_png])
            st["libreoffice_render_ssim_vs_original"] = ssim(ref_png + ".png", lo_png + ".png")
            st["libreoffice_pages"] = run(["pdfinfo", lo_pdf])["stdout"].split("Pages:")[-1].split("\n")[0].strip()
        r["docx"] = st
    results[name] = r
    print(name, "opened", r["opened"], "ssim", r["render_ssim_vs_poppler"], "text", r["text_truth_found"],
          "docx", bool(st), flush=True)

json.dump(results, open(os.path.join(OUT, "results.json"), "w"), indent=1)
print("done")
