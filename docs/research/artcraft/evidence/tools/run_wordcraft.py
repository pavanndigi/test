"""Run wordcraft-cli validate + convert(pdf) on PdfCraft's DOCX exports; score page 1 vs the original PDF."""
import json, os, subprocess, sys, time
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation
WC, FUNC = sys.argv[1], sys.argv[2]
OUT = os.path.join(FUNC, "wordcraft"); os.makedirs(OUT, exist_ok=True)
def ink(a, b):
    A = np.asarray(Image.open(a).convert("L")) < 160
    im = Image.open(b).convert("L").resize((A.shape[1], A.shape[0])); B = np.asarray(im) < 160
    Ad, Bd = binary_dilation(A), binary_dilation(B)
    tot = A.sum() + B.sum()
    return round(float(((A & Bd).sum() + (B & Ad).sum()) / tot), 4) if tot else None
res = {}
docs = [(d, os.path.join(FUNC, d, "export.docx")) for d in sorted(os.listdir(FUNC)) if os.path.isfile(os.path.join(FUNC, d, "export.docx"))]
docs.append(("ocr_12_searchable", os.path.join(FUNC, "ocr", "12_searchable.docx")))
for name, docx in docs:
    r = {}
    t0 = time.time(); v = subprocess.run([WC, "validate", docx, "--json"], capture_output=True, text=True)
    r["validate_rc"] = v.returncode; r["validate_secs"] = round(time.time() - t0, 2)
    try: r["validate"] = json.loads(v.stdout)
    except Exception: r["validate"] = v.stdout[:3000]; r["validate_stderr"] = v.stderr[:2000]
    pdf = os.path.join(OUT, name + "_wordcraft.pdf")
    t0 = time.time(); c = subprocess.run([WC, "convert", docx, pdf], capture_output=True, text=True)
    r["convert_rc"] = c.returncode; r["convert_secs"] = round(time.time() - t0, 2); r["convert_stderr"] = c.stderr[-1500:]
    ref = os.path.join(FUNC, name, "ref_p1.png")
    if os.path.exists(pdf):
        r["pages"] = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout.split("Pages:")[-1].split("\n")[0].strip()
        png = os.path.join(OUT, name + "_wordcraft_p1")
        subprocess.run(["pdftoppm", "-r", "100", "-f", "1", "-l", "1", "-png", "-singlefile", pdf, png])
        if os.path.exists(ref): r["ink_f1_vs_original"] = ink(ref, png + ".png")
    res[name] = r
    print(name, "validate", r["validate_rc"], "convert", r["convert_rc"], "pages", r.get("pages"), "ink", r.get("ink_f1_vs_original"), flush=True)
json.dump(res, open(os.path.join(OUT, "wordcraft_results.json"), "w"), indent=1)
