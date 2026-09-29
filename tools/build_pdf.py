#!/usr/bin/env python3
"""Génère Formation_Power_BI_NEXORA.pdf à partir de FORMATION_POWER_BI.md.

- Annexe C (lexique) injectée depuis app.js (source unique de vérité).
- Couverture, table des liens cliquable (avec numéros de page) et signets PDF.
Usage : python3 tools/build_pdf.py
"""
import re
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape as xesc

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, HRFlowable, KeepTogether,
                                ListFlowable, ListItem, NextPageTemplate, PageBreak,
                                PageTemplate, Paragraph, Preformatted, Spacer, Table,
                                TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "Formation_Power_BI_NEXORA.pdf"
FONT = "/usr/share/fonts/truetype/dejavu/"

pdfmetrics.registerFont(TTFont("DJ", FONT + "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DJ-B", FONT + "DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("DJM", FONT + "DejaVuSansMono.ttf"))
pdfmetrics.registerFontFamily("DJ", normal="DJ", bold="DJ-B", italic="DJ", boldItalic="DJ-B")

NAVY = colors.HexColor("#111b38")
INK = colors.HexColor("#17203b")
MUTED = colors.HexColor("#5f6884")
CORAL = colors.HexColor("#f46b4f")
PEACH = colors.HexColor("#fff0eb")
PAPER = colors.HexColor("#f7f8fc")
LINE = colors.HexColor("#e5e7ef")
RED = colors.HexColor("#a44a3a")

M = 18 * mm
PAGE_W, PAGE_H = A4
FRAME_W = PAGE_W - 2 * M

S = {
    "H1": ParagraphStyle("H1", fontName="DJ-B", fontSize=18, leading=23, textColor=NAVY,
                         spaceBefore=0, spaceAfter=10),
    "H2": ParagraphStyle("H2", fontName="DJ-B", fontSize=13, leading=17, textColor=INK,
                         spaceBefore=14, spaceAfter=6),
    "H3": ParagraphStyle("H3", fontName="DJ-B", fontSize=10.8, leading=14.5, textColor=RED,
                         spaceBefore=10, spaceAfter=4),
    "body": ParagraphStyle("body", fontName="DJ", fontSize=9.4, leading=14.4,
                           textColor=colors.HexColor("#3c4663"), spaceAfter=6),
    "li": ParagraphStyle("li", fontName="DJ", fontSize=9.4, leading=14,
                         textColor=colors.HexColor("#3c4663")),
    "quote": ParagraphStyle("quote", fontName="DJ", fontSize=9.2, leading=14, textColor=RED,
                            backColor=PEACH, borderPadding=(8, 10, 8, 10),
                            spaceBefore=4, spaceAfter=9, leftIndent=4, rightIndent=4),
    "code": ParagraphStyle("code", fontName="DJM", fontSize=7.5, leading=11,
                           textColor=colors.HexColor("#e7ecf9"), backColor=NAVY,
                           borderPadding=(9, 10, 9, 10), spaceBefore=4, spaceAfter=9),
    "th": ParagraphStyle("th", fontName="DJ-B", fontSize=7.6, leading=10, textColor=colors.white),
    "td": ParagraphStyle("td", fontName="DJ", fontSize=8, leading=11.5, textColor=INK),
    "toc1": ParagraphStyle("toc1", fontName="DJ-B", fontSize=10.5, leading=17,
                           textColor=NAVY, spaceBefore=4),
    "doctitle": ParagraphStyle("doctitle", fontName="DJ-B", fontSize=22, leading=28,
                               textColor=NAVY, spaceAfter=4),
    "docsub": ParagraphStyle("docsub", fontName="DJ", fontSize=11, leading=16,
                             textColor=MUTED, spaceAfter=16),
}


def inline(text: str) -> str:
    t = xesc(text)
    t = re.sub(r"`([^`]+)`", r'<font face="DJM" size="8.2" color="#b03a5b">\1</font>', t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<link href="\2" color="#f46b4f">\1</link>', t)
    return t


def glossary_appendix() -> str:
    app = (ROOT / "app.js").read_text(encoding="utf-8")
    block = re.search(r"const glossary = \[([\s\S]*?)\n\];", app)
    terms = re.findall(r"\{t:'([\s\S]*?)',\s*d:'([\s\S]*?)'\}", block.group(1)) if block else []
    rows = "\n".join(f"| {t} | {d} |" for t, d in terms)
    return (
        f"\n# Annexe C — Lexique illustré ({len(terms)} termes)\n\n"
        "Cette annexe est **générée automatiquement** depuis le lexique de l’application "
        "NEXORA (`app.js`) à chaque construction du manuel.\n\n"
        "| TERME | DÉFINITION SIMPLE |\n|---|---|\n" + rows + "\n\n"
        "> Retrouvez ces termes interactivement dans l’application, onglet **Ressources → Lexique**.\n"
    )


def make_table(rows):
    sep = re.compile(r"^\|[\s:\-|]+\|$")
    if len(rows) > 1 and sep.match(rows[1].strip()):
        rows = [rows[0]] + rows[2:]
    data = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    width = max(len(r) for r in data)
    data = [r + [""] * (width - len(r)) for r in data]
    weights = [max((len(re.sub(r"[`*]", "", data[r][c])) for r in range(len(data))), default=10)
               for c in range(width)]
    total = sum(weights) or 1
    col_w = [max(40, FRAME_W * w / total) for w in weights]
    scale = FRAME_W / sum(col_w)
    col_w = [w * scale for w in col_w]
    tbl_data = [[Paragraph(inline(c), S["th"]) for c in data[0]]]
    for row in data[1:]:
        tbl_data.append([Paragraph(inline(c), S["td"]) for c in row])
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("GRID", (0, 0), (-1, -1), 0.5, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for i in range(2, len(tbl_data), 2):
        style.append(("BACKGROUND", (0, i), (-1, i), PAPER))
    return Table(tbl_data, colWidths=col_w, repeatRows=1, style=TableStyle(style))


def special(line: str) -> bool:
    return bool(re.match(r"^(#{1,4}\s|```|\||-\s|\d+\.\s|>\s|---\s*$)", line))


def parse_markdown(md: str):
    lines = md.splitlines()
    out = []
    first_h1 = True
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith("# "):
            i += 1
            if first_h1:  # titre du document : remplacé par la couverture
                first_h1 = False
                continue
            out.append(PageBreak())
            out.append(Paragraph(inline(line[2:].strip()), S["H1"]))
            out.append(HRFlowable(width="100%", thickness=1.4, color=CORAL,
                                  spaceBefore=2, spaceAfter=8))
            continue
        if line.startswith("### "):
            out.append(Paragraph(inline(line[4:].strip()), S["H3"]))
            i += 1
            continue
        if line.startswith("## "):
            out.append(Paragraph(inline(line[3:].strip()), S["H2"]))
            i += 1
            continue
        if line.startswith("#### "):
            out.append(Paragraph(inline(line[5:].strip()), S["H3"]))
            i += 1
            continue
        if line.strip() == "---":
            out.append(HRFlowable(width="100%", thickness=0.7, color=LINE,
                                  spaceBefore=6, spaceAfter=6))
            i += 1
            continue
        if line.startswith("```"):
            i += 1
            buf = []
            while i < n and not lines[i].startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            out.append(Preformatted("\n".join(buf), S["code"], maxLineLength=104))
            continue
        if line.startswith("|") and i + 1 < n and re.match(r"^\|[\s:\-|]+\|$", lines[i + 1].strip()):
            buf = [line]
            i += 1
            while i < n and lines[i].strip().startswith("|"):
                buf.append(lines[i])
                i += 1
            out.append(KeepTogether([Spacer(1, 3), make_table(buf), Spacer(1, 7)]))
            continue
        if line.startswith("> "):
            buf = [line[2:].strip()]
            i += 1
            while i < n and lines[i].startswith("> "):
                buf.append(lines[i][2:].strip())
                i += 1
            out.append(Paragraph(inline(" ".join(buf)), S["quote"]))
            continue
        if re.match(r"^-\s", line) or re.match(r"^\d+\.\s", line):
            ordered = bool(re.match(r"^\d+\.\s", line))
            items = []
            checklist = False
            while i < n and (re.match(r"^-\s", lines[i]) or re.match(r"^\d+\.\s", lines[i])):
                raw = lines[i]
                if re.match(r"^-\s\[[ xX]\]\s", raw):
                    checklist = True
                    txt = re.sub(r"^-\s\[[ xX]\]\s", "", raw)
                    items.append((txt, "☐"))
                else:
                    txt = re.sub(r"^(-\s|\d+\.\s)", "", raw)
                    items.append((txt, None))
                i += 1
            flow_items = []
            for txt, box in items:
                kw = {"bulletText": box} if box else {}
                flow_items.append(ListItem(Paragraph(inline(txt), S["li"]),
                                           leftIndent=16, **kw))
            out.append(ListFlowable(
                flow_items,
                bulletType="bullet" if (checklist or not ordered) else "1",
                start="1" if ordered and not checklist else ("☐" if checklist else "•"),
                bulletFontName="DJ", bulletFontSize=9,
                leftIndent=16, bulletDedent=8, spaceBefore=2, spaceAfter=6))
            continue
        buf = [line.strip()]
        i += 1
        while i < n and lines[i].strip() and not special(lines[i]):
            buf.append(lines[i].strip())
            i += 1
        out.append(Paragraph(inline(" ".join(buf)), S["body"]))
    return out


class ManualDoc(BaseDocTemplate):
    def __init__(self, filename, **kw):
        super().__init__(filename, **kw)
        self._h = 0

    def beforeDocument(self):
        # compteur remis à zéro à chaque passe de multiBuild (convergence du sommaire)
        self._h = 0

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name in ("H1", "H2", "H3"):
            level = {"H1": 0, "H2": 1, "H3": 2}[flowable.style.name]
            text = flowable.getPlainText()
            self._h += 1
            key = f"h{self._h}"
            self.canv.bookmarkPage(key)
            if level == 0:
                self.notify("TOCEntry", (0, text, self.page, key))
            try:
                self.canv.addOutlineEntry(text, key, level=level, closed=(level > 0))
            except Exception:
                pass


def draw_cover(canvas, doc):
    canvas.saveState()
    canvas.setTitle("Formation Power BI — NEXORA")
    canvas.setAuthor("NEXORA Data Academy")
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    canvas.setFillColor(CORAL)
    canvas.rect(0, PAGE_H - 10 * mm, PAGE_W, 3.5 * mm, fill=1, stroke=0)
    x, y = 24 * mm, PAGE_H - 46 * mm
    canvas.setFillColor(CORAL)
    canvas.rect(x, y - 14 * mm, 4.5 * mm, 16 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#f7c95f"))
    canvas.rect(x + 7 * mm, y - 8 * mm, 4.5 * mm, 10 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#52bc94"))
    canvas.rect(x + 14 * mm, y - 2 * mm, 4.5 * mm, 4 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("DJ-B", 26)
    canvas.drawString(x, y - 32 * mm, "NEXORA")
    canvas.setFillColor(colors.HexColor("#9fb0d8"))
    canvas.setFont("DJ", 11)
    canvas.drawString(x + 1, y - 39 * mm, "DATA ACADEMY")
    canvas.setFillColor(colors.white)
    canvas.setFont("DJ-B", 30)
    canvas.drawString(x, y - 64 * mm, "Formation Power BI")
    canvas.setFillColor(colors.HexColor("#f7c95f"))
    canvas.setFont("DJ-B", 17)
    canvas.drawString(x, y - 76 * mm, "De zéro absolu au dashboard professionnel")
    canvas.setFillColor(colors.HexColor("#c9d1e8"))
    canvas.setFont("DJ", 11)
    canvas.drawString(x, y - 92 * mm, "Manuel pédagogique complet — 12 chapitres, exercices corrigés,")
    canvas.drawString(x, y - 99 * mm, "mini-projets, annexes DAX, checklist de publication et lexique.")
    canvas.setStrokeColor(colors.HexColor("#2c3a66"))
    canvas.setLineWidth(1)
    canvas.line(x, y - 112 * mm, PAGE_W - x, y - 112 * mm)
    canvas.setFillColor(colors.HexColor("#9fb0d8"))
    canvas.setFont("DJ", 10)
    months = {1: "janvier", 2: "février", 3: "mars", 4: "avril", 5: "mai", 6: "juin",
              7: "juillet", 8: "août", 9: "septembre", 10: "octobre", 11: "novembre", 12: "décembre"}
    d = date.today()
    canvas.drawString(x, y - 122 * mm, f"Édition du {d.day} {months[d.month]} {d.year}")
    canvas.setFont("DJ", 9)
    canvas.setFillColor(colors.HexColor("#6c7ba6"))
    canvas.drawString(x, 18 * mm, "nayxuspro-sketch/NEXORA · manuel généré depuis FORMATION_POWER_BI.md")
    canvas.restoreState()


def draw_body(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.6)
    canvas.line(M, 14 * mm, PAGE_W - M, 14 * mm)
    canvas.setFont("DJ", 7.4)
    canvas.setFillColor(MUTED)
    canvas.drawString(M, 9.5 * mm, "NEXORA · Data Academy — Formation Power BI")
    canvas.drawRightString(PAGE_W - M, 9.5 * mm, f"Page {canvas.getPageNumber()}")
    canvas.restoreState()


def main():
    md = (ROOT / "FORMATION_POWER_BI.md").read_text(encoding="utf-8") + glossary_appendix()
    doc = ManualDoc(str(OUT), pagesize=A4,
                    leftMargin=M, rightMargin=M, topMargin=M, bottomMargin=20 * mm)
    cover_frame = Frame(0, 0, PAGE_W, PAGE_H, id="cover")
    body_frame = Frame(M, 18 * mm, FRAME_W, PAGE_H - M - 20 * mm, id="body")
    doc.addPageTemplates([
        PageTemplate(id="cover", frames=[cover_frame], onPage=draw_cover),
        PageTemplate(id="body", frames=[body_frame], onPage=draw_body),
    ])
    toc = TableOfContents()
    toc.dotsMinLevel = 0
    toc.levelStyles = [S["toc1"]]

    story = [NextPageTemplate("body"), PageBreak()]
    story += [Paragraph("Sommaire", S["doctitle"]),
              Paragraph("Cliquez sur un chapitre pour y accéder ; les signets PDF "
                        "reproduisent la même navigation dans votre lecteur.", S["docsub"]),
              toc, PageBreak()]
    story += parse_markdown(md)
    doc.multiBuild(story)

    data = OUT.read_bytes()
    print(f"PDF généré : {OUT.name} — {len(data):,} octets".replace(",", " "))
    from pypdf import PdfReader
    r = PdfReader(str(OUT))
    print(f"Pages : {len(r.pages)} | Signets : {len(r.outline) if r.outline else 0}")
    sample = r.pages[2].extract_text()[:120].replace("\n", " ")
    print("Extrait p.3 :", sample)


if __name__ == "__main__":
    main()
