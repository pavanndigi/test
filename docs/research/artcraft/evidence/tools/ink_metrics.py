"""Ink-overlap metrics for Report H: binarise (grey < 160) and compare.
iou: |A&B|/|A|B| on dilated masks (1 px tolerance); ink_ratio: ink(B)/ink(A)."""
import json, os, sys
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation

def mask(p, size=None):
    im = Image.open(p).convert("L")
    if size: im = im.resize(size)
    return np.asarray(im) < 160, im.size

def metrics(a, b):
    if not (os.path.exists(a) and os.path.exists(b)): return None
    A, size = mask(a); B, _ = mask(b, size)
    Ad, Bd = binary_dilation(A, iterations=1), binary_dilation(B, iterations=1)
    inter = (A & Bd).sum() + (B & Ad).sum()
    tot = A.sum() + B.sum()
    return {"ink_f1_1px": round(float(inter / tot), 4) if tot else None,
            "ink_ratio": round(float(B.sum() / A.sum()), 3) if A.sum() else None}

root = sys.argv[1]
out = {}
for d in sorted(os.listdir(root)):
    w = os.path.join(root, d)
    if not os.path.isdir(w): continue
    ref = os.path.join(w, "ref_p1.png")
    out[d] = {"pdfcraft_render_vs_poppler": metrics(ref, os.path.join(w, "pdfcraft_p1.png")),
              "edited_vs_original": metrics(ref, os.path.join(w, "edited_p1.png")),
              "docx_libreoffice_vs_original": metrics(ref, os.path.join(w, "docx_via_libreoffice_p1.png"))}
json.dump(out, open(os.path.join(root, "ink_metrics.json"), "w"), indent=1)
for k, v in out.items(): print(k, json.dumps(v))
