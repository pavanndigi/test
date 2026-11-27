"""Generate the controlled PDF test set for Report H.

Each PDF is written to corpus/ with a manifest entry (what it contains and the
ground-truth strings) in corpus/manifest.json.  Only reportlab, PIL, pikepdf and
numpy are used.
"""
import json
import os
import random
import sys

import numpy as np
import pikepdf
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
W, H = A4
manifest = {}
LOREM = ("The quick brown fox jumps over the lazy dog. Reconstruction must keep every "
         "glyph where the author placed it, in the font the author chose. ")


def path(name):
    return os.path.join(OUT, name)


def note(name, contains, truth):
    manifest[name] = {"contains": contains, "ground_truth": truth}


# 1. Simple text
c = canvas.Canvas(path("01_simple_text.pdf"), pagesize=A4)
c.setFont("Helvetica", 12)
lines = ["Simple text test page.", "Second line of plain Helvetica 12 pt.", "Third line ends here."]
for i, t in enumerate(lines):
    c.drawString(72, H - 72 - i * 18, t)
c.save()
note("01_simple_text.pdf", "Three lines, standard Helvetica 12 pt, not embedded", lines)

# 2. Multiple fonts (standard 14)
c = canvas.Canvas(path("02_multiple_fonts.pdf"), pagesize=A4)
fonts = [("Helvetica", 12), ("Helvetica-Bold", 14), ("Times-Roman", 12), ("Times-Italic", 12),
         ("Courier", 11), ("Courier-BoldOblique", 11), ("Times-BoldItalic", 16)]
truth = []
for i, (f, s) in enumerate(fonts):
    c.setFont(f, s)
    t = f"Line in {f} at {s} pt"
    c.drawString(72, H - 72 - i * 24, t)
    truth.append({"text": t, "font": f, "size": s})
c.save()
note("02_multiple_fonts.pdf", "Seven standard-14 fonts, sizes 11-16 pt", truth)

# 3. Embedded TrueType fonts
pdfmetrics.registerFont(TTFont("DejaVuSans", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DejaVuSerif-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"))
pdfmetrics.registerFont(TTFont("LiberationSansNarrow-Italic",
                               "/usr/share/fonts/truetype/liberation/LiberationSansNarrow-Italic.ttf"))
c = canvas.Canvas(path("03_embedded_fonts.pdf"), pagesize=A4)
emb = [("DejaVuSans", 13, "Embedded DejaVu Sans: café, naïve, Œuvre, €"),
       ("DejaVuSerif-Bold", 15, "Embedded DejaVu Serif Bold heading"),
       ("LiberationSansNarrow-Italic", 12, "Embedded Liberation Sans Narrow Italic")]
for i, (f, s, t) in enumerate(emb):
    c.setFont(f, s)
    c.drawString(72, H - 80 - i * 28, t)
c.save()
note("03_embedded_fonts.pdf", "Three subset-embedded TrueType fonts with accented characters",
     [{"text": t, "font": f, "size": s} for f, s, t in emb])

# 4. Two columns of flowing text
styles = getSampleStyleSheet()
doc = BaseDocTemplate(path("04_two_columns.pdf"), pagesize=A4)
gap = 8 * mm
fw = (W - doc.leftMargin - doc.rightMargin - gap) / 2
frames = [Frame(doc.leftMargin, doc.bottomMargin, fw, H - doc.topMargin - doc.bottomMargin, id="c1"),
          Frame(doc.leftMargin + fw + gap, doc.bottomMargin, fw, H - doc.topMargin - doc.bottomMargin, id="c2")]
doc.addPageTemplates([PageTemplate(id="two", frames=frames)])
paras = [Paragraph(f"<b>Paragraph {i + 1}.</b> " + LOREM * 3, styles["BodyText"]) for i in range(14)]
doc.build(paras)
note("04_two_columns.pdf", "Two-column flowing body text, 14 paragraphs, reading order column 1 then 2",
     [f"Paragraph {i + 1}." for i in range(14)])

# 5. Ruled table / 6. Borderless table
data = [["Region", "Q1", "Q2", "Q3", "Total"],
        ["North", "1,200", "1,350", "1,410", "3,960"],
        ["South", "980", "1,020", "1,110", "3,110"],
        ["East", "1,500", "1,480", "1,620", "4,600"],
        ["West", "870", "910", "1,005", "2,785"]]
for name, ruled in (("05_ruled_table.pdf", True), ("06_borderless_table.pdf", False)):
    d = SimpleDocTemplate(path(name), pagesize=A4)
    t = Table(data, colWidths=[90, 70, 70, 70, 80])
    st = [("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("ALIGN", (1, 0), (-1, -1), "RIGHT")]
    if ruled:
        st += [("GRID", (0, 0), (-1, -1), 0.6, colors.black), ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey)]
    t.setStyle(TableStyle(st))
    d.build([Paragraph("Quarterly figures", styles["Heading2"]), Spacer(1, 8), t])
    note(name, ("Ruled 5x5 table with grid and header shading" if ruled else "Borderless 5x5 table"),
         {"rows": data})

# 7. Images
img = Image.new("RGB", (600, 400), "white")
dr = ImageDraw.Draw(img)
for i in range(0, 600, 20):
    dr.line([(i, 0), (600 - i, 400)], fill=(i % 255, 80, 200 - i % 200), width=3)
dr.ellipse([200, 100, 400, 300], fill=(240, 180, 30))
img.save(path("_photo.png"))
img.convert("RGB").save(path("_photo.jpg"), quality=85)
c = canvas.Canvas(path("07_images.pdf"), pagesize=A4)
c.setFont("Helvetica", 12)
c.drawString(72, H - 60, "Two raster images: PNG (lossless) and JPEG.")
c.drawImage(path("_photo.png"), 72, H - 360, width=300, height=200)
c.drawImage(path("_photo.jpg"), 72, H - 600, width=225, height=150)
c.save()
note("07_images.pdf", "One PNG and one JPEG image with a caption line", ["Two raster images: PNG (lossless) and JPEG."])

# 8. Vector graphics
c = canvas.Canvas(path("08_vector_graphics.pdf"), pagesize=A4)
c.setFont("Helvetica", 12)
c.drawString(72, H - 60, "Vector graphics: rectangle, circle, bezier, polygon, dashed line.")
c.setStrokeColor(colors.darkblue); c.setFillColor(colors.lightblue)
c.rect(72, H - 220, 150, 100, fill=1)
c.setFillColor(colors.orange); c.circle(330, H - 170, 50, fill=1)
c.setStrokeColor(colors.red); c.setLineWidth(3)
p = c.beginPath(); p.moveTo(72, H - 300); p.curveTo(150, H - 250, 250, H - 380, 400, H - 300); c.drawPath(p)
c.setFillColor(colors.green)
p = c.beginPath(); p.moveTo(100, H - 450); p.lineTo(200, H - 400); p.lineTo(260, H - 480); p.lineTo(150, H - 520); p.close()
c.drawPath(p, fill=1, stroke=1)
c.setDash(6, 3); c.setStrokeColor(colors.black); c.setLineWidth(1); c.line(72, H - 560, 500, H - 560)
c.save()
note("08_vector_graphics.pdf", "Filled rectangle, circle, cubic bezier, filled polygon, dashed rule", [])

# 9. Transparency
c = canvas.Canvas(path("09_transparency.pdf"), pagesize=A4)
c.setFont("Helvetica-Bold", 28)
c.drawString(72, H - 150, "Text under transparent shapes")
c.setFillColor(colors.red); c.setFillAlpha(0.5); c.rect(60, H - 200, 250, 90, fill=1, stroke=0)
c.setFillColor(colors.blue); c.setFillAlpha(0.35); c.circle(300, H - 160, 70, fill=1, stroke=0)
c.setFillAlpha(1.0)
c.save()
note("09_transparency.pdf", "Opaque text overlapped by 50% and 35% alpha fills", ["Text under transparent shapes"])

# 10. Rotated text
c = canvas.Canvas(path("10_rotated_text.pdf"), pagesize=A4)
c.setFont("Helvetica", 14)
c.drawString(72, H - 72, "Upright reference line")
for ang, x, y in ((90, 120, 300), (45, 250, 350), (-30, 330, 600), (180, 500, 200)):
    c.saveState(); c.translate(x, y); c.rotate(ang); c.drawString(0, 0, f"Rotated {ang} degrees"); c.restoreState()
c.save()
note("10_rotated_text.pdf", "Text at 0, 90, 45, -30 and 180 degrees",
     ["Upright reference line"] + [f"Rotated {a} degrees" for a in (90, 45, -30, 180)])

# 11. Headers and footers (3 pages)
c = canvas.Canvas(path("11_headers_footers.pdf"), pagesize=A4)
for pg in range(1, 4):
    c.setFont("Helvetica-Oblique", 9); c.drawString(72, H - 40, "ACME Corp. Annual Report 2026")
    c.drawRightString(W - 72, H - 40, "Confidential")
    c.setFont("Times-Roman", 12)
    for i in range(30):
        c.drawString(72, H - 90 - i * 18, f"Page {pg} body line {i + 1}: " + LOREM[:60])
    c.setFont("Helvetica", 9); c.drawCentredString(W / 2, 30, f"Page {pg} of 3")
    c.showPage()
c.save()
note("11_headers_footers.pdf", "Three pages, repeated header pair and centred page-number footer",
     {"header": "ACME Corp. Annual Report 2026", "footer": "Page N of 3"})

# 12. Scanned (image-only) PDF: render page text to an image, degrade it, place as a full page
def scan_image(text_lines, seed):
    rnd = random.Random(seed)
    im = Image.new("L", (1240, 1754), 255)  # A4 at 150 dpi
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", 30)
    for i, t in enumerate(text_lines):
        d.text((150, 150 + i * 48), t, font=f, fill=0)
    im = im.rotate(0.8, fillcolor=255, resample=Image.BICUBIC)
    arr = np.array(im).astype(np.int16)
    arr += np.array([[rnd.randint(-18, 18) for _ in range(arr.shape[1])] for _ in range(arr.shape[0])], dtype=np.int16)
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))
    return im

scan_lines = ["SCANNED MEMORANDUM", "To: All staff", "Subject: Office relocation",
              "The office moves to Building C on 12 March.", "Please pack your desk by Friday."]
im = scan_image(scan_lines, 7)
im.save(path("_scan.png"))
c = canvas.Canvas(path("12_scanned.pdf"), pagesize=A4)
c.drawImage(path("_scan.png"), 0, 0, width=W, height=H)
c.save()
note("12_scanned.pdf", "Image-only page (150 dpi greyscale, 0.8 degree skew, noise, blur); no text layer", scan_lines)

# 13. Hybrid: page 1 digital text, page 2 scanned image with an invisible text layer
c = canvas.Canvas(path("13_hybrid.pdf"), pagesize=A4)
c.setFont("Helvetica", 12)
c.drawString(72, H - 72, "Hybrid document: this first page is born-digital text.")
c.showPage()
c.drawImage(path("_scan.png"), 0, 0, width=W, height=H)
t = c.beginText(); t.setTextRenderMode(3); t.setFont("Helvetica", 14)
for i, s in enumerate(scan_lines):
    t.setTextOrigin(72, H - 80 - i * 23); t.textLine(s)
c.drawText(t)
c.showPage(); c.save()
note("13_hybrid.pdf", "Page 1 digital text; page 2 scanned image with invisible (mode 3) text layer",
     {"page1": "Hybrid document: this first page is born-digital text.", "page2": scan_lines})

# 14. Large multi-page PDF (300 pages)
c = canvas.Canvas(path("14_large_300_pages.pdf"), pagesize=A4)
for pg in range(1, 301):
    c.setFont("Helvetica-Bold", 14); c.drawString(72, H - 72, f"Section {pg}")
    c.setFont("Times-Roman", 11)
    for i in range(45):
        c.drawString(72, H - 100 - i * 15, f"{pg}.{i + 1} " + LOREM[:80])
    c.showPage()
c.save()
note("14_large_300_pages.pdf", "300 pages, about 46 text lines each", {"pages": 300})

# 15. Password-protected (AES-256, user password 'secret')
with pikepdf.open(path("02_multiple_fonts.pdf")) as pdf:
    pdf.save(path("15_password_protected.pdf"),
             encryption=pikepdf.Encryption(user="secret", owner="owner-secret", R=6))
note("15_password_protected.pdf", "Copy of 02 encrypted with AES-256 (R6); user password 'secret'", {"password": "secret"})

for tmp in ("_photo.png", "_photo.jpg", "_scan.png"):
    os.remove(path(tmp))
with open(os.path.join(OUT, "manifest.json"), "w") as fh:
    json.dump(manifest, fh, indent=2, ensure_ascii=False)
print(len(manifest), "PDFs written")
