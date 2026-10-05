from pathlib import Path
from io import BytesIO
from PIL import Image as PILImage
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, Color, white, black
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.utils import ImageReader
from pypdf import PdfReader


ROOT = Path(r"C:\Users\Administrator\Downloads\Projets\reflexe-dos")
IMAGES = ROOT / "assets" / "images"
ILLUS = IMAGES / "illustrations"
OUT = ROOT / "output" / "pdf"
OUT.mkdir(parents=True, exist_ok=True)

W, H = A4
M = 17 * mm

PINE = HexColor("#103F36")
PINE_2 = HexColor("#235B50")
CORAL = HexColor("#DE7358")
CREAM = HexColor("#F6F1E8")
CREAM_2 = HexColor("#EDE6DA")
PALE_GREEN = HexColor("#E7EFEA")
PALE_CORAL = HexColor("#F7E5DE")
INK = HexColor("#202725")
GREY = HexColor("#66706D")
LIGHT_GREY = HexColor("#CDD3D0")
RED = HexColor("#B8473D")
AMBER = HexColor("#C68A2B")
GREEN = HexColor("#3B7D61")

FONT_REG = r"C:\Windows\Fonts\arial.ttf"
FONT_BOLD = r"C:\Windows\Fonts\arialbd.ttf"
FONT_NARROW = r"C:\Windows\Fonts\ARIALN.TTF"
FONT_NARROW_BOLD = r"C:\Windows\Fonts\ARIALNB.TTF"
pdfmetrics.registerFont(TTFont("RD Body", FONT_REG))
pdfmetrics.registerFont(TTFont("RD Bold", FONT_BOLD))
pdfmetrics.registerFont(TTFont("RD Narrow", FONT_NARROW))
pdfmetrics.registerFont(TTFont("RD Narrow Bold", FONT_NARROW_BOLD))

MIN_FONT_SIZE = 12


class AccessibleCanvas(canvas.Canvas):
    """Guarantee that directly drawn text is never smaller than 12 pt."""

    def setFont(self, psfontname, size, leading=None):
        safe_size = max(MIN_FONT_SIZE, size)
        safe_leading = None if leading is None else max(MIN_FONT_SIZE * 1.2, leading)
        return super().setFont(psfontname, safe_size, safe_leading)


STYLES = {
    "body": ParagraphStyle("body", fontName="RD Body", fontSize=12.5, leading=16.2, textColor=INK, spaceAfter=5),
    "small": ParagraphStyle("small", fontName="RD Body", fontSize=12, leading=15.2, textColor=GREY),
    "bold": ParagraphStyle("bold", fontName="RD Bold", fontSize=12.5, leading=16.2, textColor=INK),
    "h2": ParagraphStyle("h2", fontName="RD Narrow Bold", fontSize=19, leading=21, textColor=PINE, spaceAfter=5),
    "h3": ParagraphStyle("h3", fontName="RD Bold", fontSize=14, leading=17, textColor=PINE, spaceAfter=4),
    "bullet": ParagraphStyle("bullet", fontName="RD Body", fontSize=12, leading=15.2, leftIndent=12, firstLineIndent=-8, bulletIndent=0, bulletFontName="RD Body", bulletFontSize=12, textColor=INK, spaceAfter=2.8),
    "number": ParagraphStyle("number", fontName="RD Body", fontSize=12, leading=15.2, leftIndent=14, firstLineIndent=-11, textColor=INK, spaceAfter=3),
    "center": ParagraphStyle("center", fontName="RD Body", fontSize=12, leading=15.2, alignment=TA_CENTER, textColor=GREY),
}


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def paragraph(c, text, x, y_top, width, style="body", color=None):
    st = STYLES[style]
    if color is not None:
        st = ParagraphStyle(f"{style}-{color}", parent=st, textColor=color)
    p = Paragraph(text, st)
    _, h = p.wrap(width, H)
    p.drawOn(c, x, y_top - h)
    return y_top - h


def bullets(c, items, x, y, width, color=INK, gap=0):
    for item in items:
        st = ParagraphStyle("b", parent=STYLES["bullet"], textColor=color)
        p = Paragraph(esc(item), st, bulletText="•")
        _, h = p.wrap(width, H)
        p.drawOn(c, x, y - h)
        y -= h + gap
    return y


def numbered(c, items, x, y, width):
    for i, item in enumerate(items, 1):
        p = Paragraph(f"<b>{i}</b>&nbsp;&nbsp;{esc(item)}", STYLES["number"])
        _, h = p.wrap(width, H)
        p.drawOn(c, x, y - h)
        y -= h + 2
    return y


def rounded(c, x, y, w, h, fill, radius=4*mm, stroke=None, line=0.8):
    c.setFillColor(fill)
    if stroke:
        c.setStrokeColor(stroke)
        c.setLineWidth(line)
    else:
        c.setStrokeColor(fill)
    c.roundRect(x, y, w, h, radius, fill=1, stroke=1 if stroke else 0)


def checkbox(c, x, y, label, checked=False, size=4*mm, font=9):
    c.setStrokeColor(PINE)
    c.setLineWidth(0.8)
    c.roundRect(x, y-size+1, size, size, 1.3, fill=0, stroke=1)
    if checked:
        c.setStrokeColor(CORAL)
        c.setLineWidth(1.5)
        c.line(x+1.1*mm, y-1.2*mm, x+1.8*mm, y-2.2*mm)
        c.line(x+1.8*mm, y-2.2*mm, x+3.2*mm, y-0.4*mm)
    c.setFillColor(INK)
    c.setFont("RD Body", font)
    c.drawString(x+size+2*mm, y-size+1.1*mm, label)


def write_line(c, x, y, w, label, lines=1):
    c.setFillColor(INK)
    c.setFont("RD Bold", 8.8)
    c.drawString(x, y, label)
    y -= 5*mm
    c.setStrokeColor(LIGHT_GREY)
    c.setLineWidth(0.55)
    for _ in range(lines):
        c.line(x, y, x+w, y)
        y -= 7*mm
    return y


def draw_crop(c, path, x, y, w, h, radius=0, overlay=None):
    im = PILImage.open(path).convert("RGB")
    target = w / h
    source = im.width / im.height
    if source > target:
        new_w = int(im.height * target)
        left = (im.width - new_w) // 2
        im = im.crop((left, 0, left + new_w, im.height))
    else:
        new_h = int(im.width / target)
        top = (im.height - new_h) // 2
        im = im.crop((0, top, im.width, top + new_h))
    buf = BytesIO()
    im.save(buf, format="JPEG", quality=92)
    buf.seek(0)
    c.saveState()
    if radius:
        p = c.beginPath()
        p.roundRect(x, y, w, h, radius)
        c.clipPath(p, stroke=0, fill=0)
    c.drawImage(ImageReader(buf), x, y, w, h, mask="auto")
    if overlay:
        c.setFillColor(overlay)
        c.rect(x, y, w, h, fill=1, stroke=0)
    c.restoreState()


def draw_contain(c, path, x, y, w, h):
    im = PILImage.open(path)
    iw, ih = im.size
    scale = min(w/iw, h/ih)
    dw, dh = iw*scale, ih*scale
    c.drawImage(str(path), x+(w-dw)/2, y+(h-dh)/2, dw, dh, mask="auto")


def base_page(c, page_no, section, title, subtitle=None, dark=False, total=None):
    c.setFillColor(PINE if dark else CREAM)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    if dark:
        fg, sub = white, HexColor("#DCE8E3")
    else:
        fg, sub = INK, GREY
    c.setFillColor(CORAL)
    c.setFont("RD Bold", 8.2)
    c.drawString(M, H-15*mm, section.upper())
    c.setFillColor(fg)
    c.setFont("RD Narrow Bold", 25)
    c.drawString(M, H-28*mm, title)
    if subtitle:
        c.setFillColor(sub)
        c.setFont("RD Body", 10.4)
        c.drawString(M, H-36*mm, subtitle)
    c.setStrokeColor(CORAL)
    c.setLineWidth(2)
    c.line(M, H-40*mm, M+18*mm, H-40*mm)
    c.setFillColor(sub)
    c.setFont("RD Body", 7.2)
    c.drawString(M, 10*mm, "LE RÉFLEXE DOS   •   ÉDITION COMPLÈTE 2.0")
    page_txt = f"{page_no}" if total is None else f"{page_no} / {total}"
    c.setFont("RD Bold", 8)
    c.drawRightString(W-M, 10*mm, page_txt)


def page_done(c):
    c.showPage()


def pill(c, text, x, y, bg=PINE, fg=white, width=None):
    c.setFont("RD Bold", 12)
    tw = c.stringWidth(text, "RD Bold", 12)
    w = width or tw + 8*mm
    rounded(c, x, y-7*mm, w, 9*mm, bg, radius=4.5*mm)
    c.setFillColor(fg)
    c.drawCentredString(x+w/2, y-4.7*mm, text)
    return w


def step_card(c, num, title, body, x, y, w, h, tint=PALE_GREEN):
    rounded(c, x, y-h, w, h, tint, radius=4*mm)
    c.setFillColor(CORAL)
    c.circle(x+8*mm, y-9*mm, 5*mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("RD Bold", 8.7)
    c.drawCentredString(x+8*mm, y-11*mm, str(num))
    c.setFillColor(PINE)
    c.setFont("RD Bold", 9.8)
    c.drawString(x+16*mm, y-7*mm, title)
    paragraph(c, esc(body), x+16*mm, y-12*mm, w-20*mm, "small", INK)


def traffic_card(c, label, title, body, x, y, w, h, color):
    rounded(c, x, y-h, w, h, white, radius=3*mm, stroke=CREAM_2)
    c.setFillColor(color)
    c.circle(x+7*mm, y-8*mm, 3.1*mm, fill=1, stroke=0)
    c.setFont("RD Bold", 7.8)
    c.drawString(x+13*mm, y-6*mm, label.upper())
    c.setFillColor(PINE)
    c.setFont("RD Bold", 9.6)
    c.drawString(x+7*mm, y-15*mm, title)
    paragraph(c, esc(body), x+7*mm, y-20*mm, w-14*mm, "small", INK)


def info_strip(c, title, body, x, y, w, h=27*mm, fill=PALE_GREEN):
    rounded(c, x, y, w, h, fill, radius=4*mm)
    c.setFillColor(PINE)
    c.setFont("RD Bold", 12)
    c.drawString(x+6*mm, y+h-8*mm, title)
    paragraph(c, esc(body), x+6*mm, y+h-13*mm, w-12*mm, "small", INK)


def sources_page(c, page_no, total, product):
    base_page(c, page_no, "Sources", "Repères et validation", "Une version traçable et révisable", total=total)
    y = H-52*mm
    paragraph(c, "<b>Sources institutionnelles consultées</b>", M, y, W-2*M, "h2")
    y -= 13*mm
    refs = [
        ("Haute Autorité de santé", "Prise en charge de la lombalgie commune", "has-sante.fr - recommandation lombalgie"),
        ("Assurance Maladie", "Lombalgie ou mal de dos", "ameli.fr - dossier lombalgie aiguë"),
        ("Assurance Maladie", "Le bon traitement est le mouvement", "ameli.fr - traitement et prévention"),
        ("Organisation mondiale de la Santé", "Guide sur la lombalgie chronique primaire", "who.int - ISBN 978-92-4-008178-9"),
    ]
    for org, label, url in refs:
        rounded(c, M, y-21*mm, W-2*M, 18*mm, white, radius=3*mm)
        c.setFillColor(PINE)
        c.setFont("RD Bold", 9.1)
        c.drawString(M+5*mm, y-7*mm, org)
        c.setFillColor(INK)
        c.setFont("RD Body", 8.2)
        c.drawString(M+5*mm, y-12*mm, label)
        c.setFillColor(GREY)
        c.setFont("RD Body", 6.4)
        c.drawString(M+5*mm, y-16*mm, url)
        y -= 21*mm
    y -= 3*mm
    rounded(c, M, y-43*mm, W-2*M, 40*mm, PALE_CORAL, radius=4*mm)
    c.setFillColor(CORAL)
    c.setFont("RD Bold", 8.6)
    c.drawString(M+6*mm, y-9*mm, "AVANT COMMERCIALISATION")
    paragraph(c, "Ce support doit être relu par un médecin ou un kinésithérapeute. Les consignes, illustrations de mouvement et règles d’arrêt doivent être validées. Afficher ensuite le nom du relecteur, sa qualité, la date de validation et la prochaine date de révision.", M+6*mm, y-15*mm, W-2*M-12*mm, "body")
    c.setFillColor(GREY)
    c.setFont("RD Body", 12)
    c.drawString(M, 31*mm, f"Produit  {product}")
    c.drawString(M, 25*mm, "Sources consultées le 4 octobre 2026")
    c.drawString(M, 19*mm, "Illustrations originales générées pour Le Réflexe Dos")


def build_guide():
    path = OUT / "SOS-Lumbago-7-jours-guide-illustre-complet-v2.pdf"
    c = AccessibleCanvas(str(path), pagesize=A4, pageCompression=1)
    c.setTitle("SOS Lumbago 7 jours - Guide illustré complet")
    c.setAuthor("Le Réflexe Dos")
    total = 14

    # 1 Cover
    draw_crop(c, IMAGES / "couverture-praticien-patiente.png", 0, 0, W, H, overlay=Color(0.03,0.12,0.10,alpha=0.18))
    c.setFillColor(Color(0.02,0.12,0.10,alpha=0.72))
    c.rect(0, 0, W, 104*mm, fill=1, stroke=0)
    c.setFillColor(CORAL)
    c.setFont("RD Bold", 8)
    c.drawString(M, 91*mm, "GUIDE PRATIQUE ILLUSTRÉ")
    c.setFillColor(white)
    c.setFont("RD Narrow Bold", 33)
    c.drawString(M, 77*mm, "SOS Lumbago")
    c.setFont("RD Narrow Bold", 25)
    c.drawString(M, 66*mm, "7 jours pour retrouver des repères")
    paragraph(c, "Des décisions simples, des options de mouvement et un carnet court pour traverser les premiers jours sans rester seul face au doute.", M, 57*mm, 150*mm, "body", white)
    pill(c, "14 PAGES", M, 31*mm, CORAL)
    pill(c, "8 ILLUSTRATIONS", M+31*mm, 31*mm, PINE_2)
    pill(c, "FORMAT A4", M+75*mm, 31*mm, PINE_2)
    c.setFillColor(white)
    c.setFont("RD Bold", 7)
    c.drawString(M, 14*mm, "LE RÉFLEXE DOS")
    c.drawRightString(W-M, 14*mm, "ÉDITION COMPLÈTE 2.0   •   VALIDATION SANTÉ REQUISE")
    page_done(c)

    # 2 Safety
    base_page(c, 2, "Sécurité", "Avant de commencer", "Votre douleur mérite d’être prise au sérieux", total=total)
    y = H-51*mm
    paragraph(c, "La plupart des douleurs lombaires ne sont pas liées à une maladie grave. Ce guide ne peut cependant pas vérifier votre situation. Utilisez cette page avant toute proposition d’activité.", M, y, W-2*M, "body")
    y -= 20*mm
    rounded(c, M, y-75*mm, 84*mm, 72*mm, PALE_CORAL, radius=5*mm)
    c.setFillColor(RED); c.circle(M+10*mm, y-12*mm, 5*mm, fill=1, stroke=0)
    c.setFillColor(white); c.setFont("RD Bold", 9); c.drawCentredString(M+10*mm, y-15*mm, "!")
    c.setFillColor(RED); c.setFont("RD Bold", 11); c.drawString(M+19*mm, y-10*mm, "Aide urgente")
    bullets(c, [
        "nouveau trouble urinaire ou intestinal",
        "perte de sensibilité du périnée",
        "faiblesse importante ou progressive d’une jambe",
        "traumatisme important, malaise ou symptôme inhabituel",
    ], M+7*mm, y-20*mm, 69*mm, RED)
    c.setFillColor(RED); c.setFont("RD Bold", 12); c.drawString(M+7*mm, y-68*mm, "En France  15 ou 112")

    rounded(c, M+91*mm, y-75*mm, 85*mm, 72*mm, PALE_GREEN, radius=5*mm)
    c.setFillColor(AMBER); c.circle(M+101*mm, y-12*mm, 5*mm, fill=1, stroke=0)
    c.setFillColor(white); c.setFont("RD Bold", 8); c.drawCentredString(M+101*mm, y-15*mm, "?")
    c.setFillColor(PINE); c.setFont("RD Bold", 11); c.drawString(M+110*mm, y-10*mm, "Avis rapide")
    bullets(c, [
        "fièvre ou altération de l’état général",
        "douleur qui s’aggrave régulièrement ou persiste au repos",
        "engourdissement ou faiblesse nouvelle",
        "perte de poids inexpliquée ou antécédent médical important",
        "activités très limitées sans amélioration",
    ], M+98*mm, y-20*mm, 70*mm)
    y -= 88*mm
    rounded(c, M, y-46*mm, W-2*M, 43*mm, white, radius=4*mm)
    c.setFillColor(PINE); c.setFont("RD Bold", 10); c.drawString(M+6*mm, y-10*mm, "Vous hésitez")
    paragraph(c, "Vous n’avez pas à décider seul. Un pharmacien, votre médecin, le 15 ou le 112 peuvent vous aider à choisir le bon niveau de recours selon la situation.", M+6*mm, y-16*mm, W-2*M-12*mm, "body")
    c.setStrokeColor(LIGHT_GREY); c.line(M+6*mm, y-34*mm, W-M-6*mm, y-34*mm)
    c.setFillColor(GREY); c.setFont("RD Body", 7.4); c.drawString(M+6*mm, y-40*mm, "Un signe isolé ne suffit pas à conclure. Il mérite d’être évalué dans son contexte.")
    page_done(c)

    # 3 Quick start
    base_page(c, 3, "Jour 0", "Les trente premières minutes", "Réduire l’incertitude avant de chercher un exercice", total=total)
    y = H-53*mm
    steps = [
        ("Vérifier", "Reprenez la page de sécurité et notez tout symptôme nouveau."),
        ("S’installer", "Testez deux positions sûres. Gardez celle qui facilite le souffle."),
        ("Sécuriser", "Dégagez le trajet vers les toilettes et gardez le téléphone près de vous."),
        ("Prévenir", "Demandez une aide pour les charges, les enfants ou une tâche urgente."),
    ]
    for i,(t,b) in enumerate(steps):
        yy = y - i*32*mm
        step_card(c, i+1, t, b, M, yy, W-2*M, 27*mm, PALE_GREEN if i%2==0 else white)
    y -= 132*mm
    rounded(c, M, y-49*mm, W-2*M, 45*mm, PALE_CORAL, radius=5*mm)
    c.setFillColor(CORAL); c.setFont("RD Bold", 8); c.drawString(M+6*mm, y-9*mm, "MON PROCHAIN PETIT PAS")
    c.setFillColor(INK); c.setFont("RD Body", 8.5); c.drawString(M+6*mm, y-17*mm, "Aujourd’hui, l’action la plus utile est")
    c.setStrokeColor(CORAL); c.line(M+6*mm, y-26*mm, W-M-6*mm, y-26*mm)
    c.setFillColor(INK); c.drawString(M+6*mm, y-35*mm, "La personne que je peux prévenir est")
    c.line(M+6*mm, y-43*mm, W-M-6*mm, y-43*mm)
    info_strip(c, "Votre objectif aujourd’hui", "Retrouver un peu de contrôle sur la journée : une position de répit, un trajet sécurisé et une personne joignable suffisent.", M, 26*mm, W-2*M, fill=PALE_GREEN)
    page_done(c)

    # 4 Day 1 rhythm
    base_page(c, 4, "Jour 1", "Protéger sans s’immobiliser", "Alterner repos bref et activité tolérable", total=total)
    y = H-52*mm
    paragraph(c, "Rester au lit toute la journée n’aide généralement pas une lombalgie commune. Cela ne veut pas dire ignorer la douleur. Cherchez un rythme que vous pouvez répéter.", M, y, W-2*M, "body")
    y -= 24*mm
    c.setStrokeColor(PINE); c.setLineWidth(2); c.line(M+12*mm, y-12*mm, W-M-12*mm, y-12*mm)
    times = [("MATIN", "Se lever en plusieurs temps"), ("MIDI", "Changer de position"), ("APRÈS-MIDI", "Faire un trajet court"), ("SOIR", "Préparer la nuit")]
    xs = [M+12*mm, M+55*mm, M+101*mm, M+148*mm]
    for x,(lab,body) in zip(xs,times):
        c.setFillColor(CORAL); c.circle(x, y-12*mm, 5*mm, fill=1, stroke=0)
        c.setFillColor(PINE); c.setFont("RD Bold", 7.2); c.drawCentredString(x, y-22*mm, lab)
        paragraph(c, body, x-17*mm, y-27*mm, 34*mm, "center")
    y -= 63*mm
    paragraph(c, "<b>Le repère du jour</b>", M, y, W-2*M, "h2")
    y -= 12*mm
    traffic_card(c, "Vert", "Je continue", "Le mouvement reste contrôlable et la récupération est prévisible.", M, y, 54*mm, 49*mm, GREEN)
    traffic_card(c, "Orange", "Je réduis", "La réponse devient nettement plus forte ou dure plus que prévu.", M+61*mm, y, 54*mm, 49*mm, AMBER)
    traffic_card(c, "Rouge", "Je demande de l’aide", "Un symptôme nouveau apparaît ou la situation devient inquiétante.", M+122*mm, y, 54*mm, 49*mm, RED)
    y -= 63*mm
    rounded(c, M, y-43*mm, W-2*M, 40*mm, white, radius=4*mm)
    y2 = y-8*mm
    y2 = write_line(c, M+6*mm, y2, W-2*M-12*mm, "Le déplacement le plus facile", 1)
    write_line(c, M+6*mm, y2+2*mm, W-2*M-12*mm, "Le réglage que je garde demain", 1)
    page_done(c)

    # 5 Bed and dressing illustration
    base_page(c, 5, "Jour 1", "Se lever et s’habiller", "Utiliser des appuis temporaires sans chercher la technique parfaite", total=total)
    draw_contain(c, ILLUS / "sortie-lit-habillage-v1.png", M, H-152*mm, W-2*M, 100*mm)
    labels = [
        ("1  Sortir du lit", "Roulez sur le côté si cela vous aide, rapprochez les jambes du bord puis poussez avec les bras."),
        ("2  S’habiller assis", "Rapprochez le vêtement ou la chaussure plutôt que de chercher une grande amplitude."),
        ("3  Accepter un appui", "Utilisez un meuble stable ou l’aide d’un proche pendant quelques jours si nécessaire."),
    ]
    y = H-160*mm
    for i,(t,b) in enumerate(labels):
        x = M+i*59*mm
        rounded(c, x, y-50*mm, 53*mm, 47*mm, white, radius=4*mm)
        c.setFillColor(PINE); c.setFont("RD Bold", 8.8); c.drawString(x+5*mm, y-10*mm, t)
        paragraph(c, b, x+5*mm, y-17*mm, 43*mm, "small")
    rounded(c, M, 19*mm, W-2*M, 23*mm, PALE_CORAL, radius=3*mm)
    paragraph(c, "<b>Règle de sécurité</b>  Une canne ou des béquilles utilisées pour la première fois doivent être réglées et expliquées par un professionnel.", M+5*mm, 37*mm, W-2*M-10*mm, "small")
    info_strip(c, "Si un geste bloque", "Raccourcissez le mouvement, asseyez-vous ou acceptez un appui. Le but est de réaliser l’action utile sans chercher une technique parfaite.", M, 47*mm, W-2*M, fill=PALE_GREEN)
    page_done(c)

    # 6 Mobility illustrations
    base_page(c, 6, "Jour 2", "Retrouver un peu de mobilité", "Quatre options courtes à choisir selon votre journée", total=total)
    draw_contain(c, ILLUS / "mobilite-douce-sequence-v1.png", M, H-145*mm, W-2*M, 89*mm)
    y = H-151*mm
    labels = [("Souffler", "Relâcher les épaules"), ("S’appuyer", "Transférer le poids"), ("Marcher", "Faire un trajet court"), ("Observer", "Noter la réponse")]
    for i,(a,b) in enumerate(labels):
        x = M+i*44*mm
        c.setFillColor(CORAL); c.circle(x+4*mm, y, 3*mm, fill=1, stroke=0)
        paragraph(c, f"<b>{a}</b><br/>{b}", x+9*mm, y+4*mm, 34*mm, "small", PINE)
    y -= 29*mm
    rounded(c, M, y-67*mm, 110*mm, 62*mm, white, radius=4*mm)
    c.setFillColor(PINE); c.setFont("RD Bold", 10); c.drawString(M+6*mm, y-12*mm, "Routine courte")
    yb = numbered(c, [
        "Choisissez une position confortable.",
        "Réalisez un petit mouvement connu.",
        "Marchez une à trois minutes dans un espace sûr.",
        "Reposez-vous brièvement puis observez la réponse.",
    ], M+6*mm, y-20*mm, 97*mm)
    rounded(c, M+117*mm, y-67*mm, 59*mm, 62*mm, PALE_GREEN, radius=4*mm)
    c.setFillColor(PINE); c.setFont("RD Bold", 9); c.drawString(M+123*mm, y-12*mm, "Vous choisissez")
    yy = y-22*mm
    for lab in ["Souffler", "S’appuyer", "Marcher", "Observer"]:
        checkbox(c, M+123*mm, yy, lab)
        yy -= 9*mm
    info_strip(c, "Votre dose du jour", "Choisissez une seule option, testez-la brièvement puis observez la réponse plus tard. Une petite dose répétable est déjà une progression.", M, 19*mm, W-2*M, fill=PALE_CORAL)
    page_done(c)

    # 7 Task
    base_page(c, 7, "Jour 3", "Reprendre une tâche utile", "Mesurer votre capacité dans la vraie vie", total=total)
    y = H-52*mm
    draw_crop(c, IMAGES / "quotidien-chaussures.png", M, y-82*mm, 79*mm, 78*mm, radius=5*mm)
    rounded(c, M+87*mm, y-82*mm, 89*mm, 78*mm, white, radius=5*mm)
    c.setFillColor(PINE); c.setFont("RD Bold", 11); c.drawString(M+94*mm, y-15*mm, "La règle en quatre temps")
    numbered(c, [
        "Préparer les objets à hauteur accessible.",
        "Réaliser une première partie.",
        "Changer de position ou faire une pause.",
        "Terminer, déléguer ou reporter sans culpabiliser.",
    ], M+94*mm, y-25*mm, 75*mm)
    y -= 96*mm
    paragraph(c, "<b>Votre tâche du jour</b>", M, y, W-2*M, "h2")
    y -= 11*mm
    rounded(c, M, y-81*mm, W-2*M, 76*mm, PALE_GREEN, radius=5*mm)
    yy = y-11*mm
    yy = write_line(c, M+7*mm, yy, W-2*M-14*mm, "La tâche choisie", 1)
    yy = write_line(c, M+7*mm, yy+2*mm, W-2*M-14*mm, "La version plus courte", 1)
    yy = write_line(c, M+7*mm, yy+2*mm, W-2*M-14*mm, "L’aide que j’accepte", 1)
    write_line(c, M+7*mm, yy+2*mm, W-2*M-14*mm, "Ce que j’ai réellement réussi", 1)
    info_strip(c, "Mesurer autrement", "Notez la tâche accomplie, même partiellement, ainsi que le réglage qui l’a rendue possible. La capacité compte autant que la douleur.", M, 27*mm, W-2*M, fill=PALE_CORAL)
    page_done(c)

    # 8 travel
    base_page(c, 8, "Jour 4", "Sortir et se déplacer", "Préparer le trajet avant de tester la distance", total=total)
    draw_contain(c, ILLUS / "travail-deplacements-v1.png", M, H-148*mm, W-2*M, 95*mm)
    y = H-155*mm
    cards = [
        ("Au travail", "Alternez assis et debout. Un changement de position peut durer moins de deux minutes."),
        ("En voiture", "Asseyez-vous d’abord puis tournez les jambes ensemble si cette option vous convient."),
        ("En transport", "Choisissez un horaire moins chargé et acceptez de vous asseoir."),
    ]
    for i,(t,b) in enumerate(cards):
        x=M+i*59*mm
        rounded(c,x,y-49*mm,53*mm,46*mm,white,radius=4*mm)
        c.setFillColor(PINE); c.setFont("RD Bold",9); c.drawString(x+5*mm,y-11*mm,t)
        paragraph(c,b,x+5*mm,y-18*mm,43*mm,"small")
    y -= 62*mm
    rounded(c,M,y-35*mm,W-2*M,31*mm,PALE_CORAL,radius=4*mm)
    c.setFillColor(CORAL); c.setFont("RD Bold",8); c.drawString(M+6*mm,y-9*mm,"AVANT DE PARTIR")
    xx=M+6*mm
    for label in ["Point de retour", "Lieu de pause", "Charge réduite", "Personne prévenue"]:
        checkbox(c,xx,y-17*mm,label,size=3.4*mm,font=7.1)
        xx += 42*mm
    page_done(c)

    # 9 work
    base_page(c, 9, "Jour 5", "Préparer la reprise du travail", "Décrire les contraintes avant de choisir une date", total=total)
    y = H-53*mm
    paragraph(c, "La reprise dépend de votre état, du trajet, des horaires et des tâches réelles. Des adaptations temporaires peuvent être discutées avec le médecin traitant et le médecin du travail.", M, y, W-2*M, "body")
    y -= 23*mm
    rows = [
        ["Contrainte", "Aujourd’hui", "Adaptation possible"],
        ["Trajet", "Durée  mode  station debout", "horaire calme  pause  télétravail"],
        ["Position", "assis  debout  conduite", "alternance  appui  micro-pause"],
        ["Charge", "poids  répétition  hauteur", "réduire  rapprocher  déléguer"],
        ["Rythme", "cadence  imprévus  pauses", "fractionner  changer de tâche"],
    ]
    table = Table(rows, colWidths=[43*mm, 60*mm, 73*mm], rowHeights=[10*mm, 18*mm, 18*mm, 18*mm, 18*mm])
    table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),PINE),("TEXTCOLOR",(0,0),(-1,0),white),
        ("FONTNAME",(0,0),(-1,0),"RD Bold"),("FONTSIZE",(0,0),(-1,-1),12),
        ("FONTNAME",(0,1),(-1,-1),"RD Body"),("TEXTCOLOR",(0,1),(-1,-1),INK),
        ("BACKGROUND",(0,1),(-1,-1),white),("GRID",(0,0),(-1,-1),0.5,CREAM_2),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),("LEFTPADDING",(0,0),(-1,-1),4*mm),
    ]))
    tw,th=table.wrap(W-2*M,H); table.drawOn(c,M,y-th)
    y -= th+12*mm
    rounded(c,M,y-66*mm,W-2*M,61*mm,PALE_GREEN,radius=5*mm)
    c.setFillColor(PINE); c.setFont("RD Bold",10); c.drawString(M+6*mm,y-12*mm,"Ma demande claire")
    yy=y-21*mm
    yy=write_line(c,M+6*mm,yy,W-2*M-12*mm,"L’adaptation temporaire qui m’aiderait",1)
    yy=write_line(c,M+6*mm,yy+2*mm,W-2*M-12*mm,"La personne à contacter",1)
    write_line(c,M+6*mm,yy+2*mm,W-2*M-12*mm,"La date de réévaluation",1)
    info_strip(c, "Formuler une demande", "Décrivez une contrainte observable et proposez une adaptation temporaire : horaire, trajet, alternance des positions, charge ou rythme.", M, 26*mm, W-2*M, fill=PALE_CORAL)
    page_done(c)

    # 10 consultation
    base_page(c, 10, "Jour 6", "Préparer une consultation", "Donner les informations qui changent la décision", total=total)
    draw_crop(c, IMAGES / "consultation-kine.png", M, H-142*mm, 80*mm, 87*mm, radius=5*mm)
    x=M+88*mm; y=H-57*mm
    c.setFillColor(PINE); c.setFont("RD Bold",10); c.drawString(x,y,"À apporter")
    yy=y-10*mm
    for lab in ["date et circonstances", "zone et éventuelle douleur dans la jambe", "symptômes associés", "traitements et examens", "deux questions prioritaires"]:
        checkbox(c,x,yy,lab,size=3.5*mm,font=7.2); yy-=9*mm
    y=H-155*mm
    rounded(c,M,y-91*mm,W-2*M,87*mm,white,radius=5*mm)
    c.setFillColor(PINE); c.setFont("RD Bold",10); c.drawString(M+6*mm,y-11*mm,"Ma synthèse en une minute")
    yy=y-20*mm
    yy=write_line(c,M+6*mm,yy,W-2*M-12*mm,"Ce qui a changé",1)
    yy=write_line(c,M+6*mm,yy+2*mm,W-2*M-12*mm,"Ce que je ne peux plus faire",1)
    yy=write_line(c,M+6*mm,yy+2*mm,W-2*M-12*mm,"Ce que je peux encore faire",1)
    yy=write_line(c,M+6*mm,yy+2*mm,W-2*M-12*mm,"Ma question prioritaire",1)
    info_strip(c, "Pendant le rendez-vous", "Montrez cette synthèse, précisez ce qui a changé et demandez quel signe doit conduire à reconsulter. Notez la décision avec vos mots.", M, 20*mm, W-2*M, fill=PALE_GREEN)
    page_done(c)

    # 11 Day 7 decision
    base_page(c, 11, "Jour 7", "Faire le bilan et choisir la suite", "Amélioration  stagnation  aggravation", total=total)
    y=H-55*mm
    branches=[
        (GREEN,"ÇA S’AMÉLIORE","Conservez les activités tolérées. Augmentez un seul paramètre à la fois.","Je poursuis"),
        (AMBER,"ÇA STAGNE","Regardez les capacités autant que la douleur. Demandez un avis si les activités restent très limitées.","Je réévalue"),
        (RED,"ÇA S’AGGRAVE","Revenez à la page de sécurité. Un symptôme nouveau mérite une évaluation adaptée.","Je demande de l’aide"),
    ]
    for i,(col,lab,body,action) in enumerate(branches):
        yy=y-i*52*mm
        rounded(c,M,yy-45*mm,W-2*M,41*mm,white,radius=5*mm,stroke=CREAM_2)
        c.setFillColor(col); c.rect(M,yy-45*mm,7*mm,41*mm,fill=1,stroke=0)
        c.setFillColor(col); c.setFont("RD Bold",8); c.drawString(M+13*mm,yy-12*mm,lab)
        paragraph(c,body,M+13*mm,yy-18*mm,111*mm,"small")
        pill(c,action,M+128*mm,yy-16*mm,col,width=48*mm)
    y-=165*mm
    rounded(c,M,y-44*mm,W-2*M,40*mm,PALE_GREEN,radius=4*mm)
    yy=y-9*mm
    yy=write_line(c,M+6*mm,yy,W-2*M-12*mm,"Ce qui a progressé",1)
    write_line(c,M+6*mm,yy+2*mm,W-2*M-12*mm,"Ma décision pour la prochaine semaine",1)
    page_done(c)

    # 12 constraints
    base_page(c, 12, "Vie quotidienne", "Quand les contraintes s’accumulent", "Douleur  organisation  pression financière", total=total)
    draw_crop(c, IMAGES / "factures-pression.png", M, H-147*mm, 76*mm, 92*mm, radius=5*mm)
    x=M+84*mm; y=H-58*mm
    y = paragraph(c,"<b>Faites une liste courte des conséquences des sept prochains jours.</b>",x,y,92*mm,"h3") - 6*mm
    for lab in ["À faire aujourd’hui", "À déléguer", "À reporter"]:
        y=write_line(c,x,y,92*mm,lab,1)+2*mm
    y=H-161*mm
    rounded(c,M,y-84*mm,W-2*M,80*mm,white,radius=5*mm)
    c.setFillColor(PINE); c.setFont("RD Bold",10); c.drawString(M+6*mm,y-12*mm,"Démarches utiles")
    bullets(c,[
        "regrouper ordonnances, arrêts, factures et justificatifs",
        "demander les conditions de prise en charge avant une dépense importante",
        "prévenir rapidement si un rendez-vous ou un paiement ne peut pas être tenu",
        "solliciter un service social si le logement, le revenu ou l’accès aux soins sont en difficulté",
    ],M+6*mm,y-21*mm,W-2*M-12*mm)
    rounded(c,M+6*mm,y-78*mm,W-2*M-12*mm,17*mm,PALE_CORAL,radius=3*mm)
    paragraph(c,"Ce guide ne fournit pas de conseil juridique ou financier personnalisé. Les droits dépendent de votre situation.",M+11*mm,y-66*mm,W-2*M-22*mm,"small")
    page_done(c)

    # 13 weekly journal
    base_page(c, 13, "Carnet", "Votre semaine en un coup d’œil", "Suivre les capacités sans surveiller chaque sensation", total=total)
    y=H-55*mm
    cols=[21*mm,42*mm,42*mm,36*mm,35*mm]
    data=[["Jour","Action","Aide utile","Réponse","Décision"]]
    for d in range(1,8): data.append([str(d),"","","",""])
    t=Table(data,colWidths=cols,rowHeights=[11*mm]+[23*mm]*7)
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),PINE),("TEXTCOLOR",(0,0),(-1,0),white),
        ("FONTNAME",(0,0),(-1,0),"RD Bold"),("FONTSIZE",(0,0),(-1,0),12),
        ("BACKGROUND",(0,1),(-1,-1),white),("GRID",(0,0),(-1,-1),0.6,CREAM_2),
        ("FONTNAME",(0,1),(-1,-1),"RD Body"),("FONTSIZE",(0,1),(-1,-1),12),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),("ALIGN",(0,0),(0,-1),"CENTER"),
    ]))
    tw,th=t.wrap(W-2*M,H); t.drawOn(c,M,y-th)
    y-=th+8*mm
    paragraph(c,"Une journée plus difficile n’efface pas les capacités gagnées. Cherchez ce qui est devenu plus prévisible.",M,y,W-2*M,"small")
    page_done(c)

    # 14 sources
    sources_page(c,14,total,"SOS Lumbago 7 jours")
    page_done(c)
    c.save()
    assert len(PdfReader(str(path)).pages)==14
    return path


def build_sheets():
    path = OUT / "Fiches-pratiques-Le-Reflexe-Dos-lot-01-complet-v2.pdf"
    c=AccessibleCanvas(str(path),pagesize=A4,pageCompression=1)
    c.setTitle("Fiches pratiques Le Réflexe Dos - Lot 01 complet")
    c.setAuthor("Le Réflexe Dos")
    total=12

    # 1 cover
    c.setFillColor(CREAM); c.rect(0,0,W,H,fill=1,stroke=0)
    draw_crop(c,IMAGES/"consultation-kine.png",0,H-142*mm,W,142*mm,overlay=Color(0.03,0.12,0.10,alpha=0.10))
    rounded(c,M,24*mm,W-2*M,113*mm,PINE,radius=7*mm)
    c.setFillColor(CORAL); c.setFont("RD Bold",8); c.drawString(M+9*mm,121*mm,"COLLECTION DÉTACHABLE")
    c.setFillColor(white); c.setFont("RD Narrow Bold",29); c.drawString(M+9*mm,104*mm,"Fiches pratiques")
    c.setFont("RD Narrow Bold",24); c.drawString(M+9*mm,92*mm,"Le Réflexe Dos")
    paragraph(c,"Huit fiches pour les premiers jours, la consultation, le travail, la nuit, les déplacements et le bilan.",M+9*mm,81*mm,W-2*M-18*mm,"body",white)
    pill(c,"8 FICHES",M+9*mm,55*mm,CORAL)
    pill(c,"IMPRESSION A4",M+45*mm,55*mm,PINE_2)
    pill(c,"USAGE MOBILE",M+94*mm,55*mm,PINE_2)
    c.setFillColor(white); c.setFont("RD Body",12); c.drawString(M+9*mm,34*mm,"ÉDITION COMPLÈTE 2.0   •   VALIDATION SANTÉ REQUISE")
    page_done(c)

    # 2 map + safety
    base_page(c,2,"Mode d’emploi","Une fiche pour une décision","Commencez par la sécurité puis choisissez votre besoin",total=total)
    y=H-53*mm
    rounded(c,M,y-51*mm,W-2*M,47*mm,PALE_CORAL,radius=5*mm)
    c.setFillColor(RED); c.setFont("RD Bold",9); c.drawString(M+7*mm,y-10*mm,"DEMANDEZ UNE AIDE URGENTE")
    bullets(c,["trouble urinaire ou intestinal nouveau","perte de sensibilité du périnée","faiblesse importante ou progressive","traumatisme important ou malaise marqué"],M+7*mm,y-18*mm,W-2*M-14*mm,RED)
    c.setFillColor(RED); c.setFont("RD Bold",8); c.drawRightString(W-M-7*mm,y-42*mm,"France  15 ou 112")
    y-=63*mm
    paragraph(c,"<b>Choisissez ensuite une seule fiche</b>",M,y,W-2*M,"h2")
    y-=14*mm
    items=[("01","Maintenant"),("02","Demander de l’aide"),("03","Consultation"),("04","Journée difficile"),("05","Travail assis"),("06","Nuit"),("07","Aide à la marche"),("08","Bilan")]
    for i,(n,t) in enumerate(items):
        col=i%2; row=i//2; x=M+col*89*mm; yy=y-row*24*mm
        rounded(c,x,yy-19*mm,82*mm,17*mm,white,radius=3*mm)
        c.setFillColor(CORAL); c.setFont("RD Bold",8); c.drawString(x+5*mm,yy-10*mm,n)
        c.setFillColor(PINE); c.setFont("RD Bold",8.5); c.drawString(x+16*mm,yy-10*mm,t)
    y-=105*mm
    paragraph(c,"Vous n’avez pas à tout lire ni à tout faire. Une fiche doit simplifier votre prochaine décision, pas ajouter une obligation.",M,y,W-2*M,"body")
    info_strip(c, "Pour une lecture sur téléphone", "Photographiez la fiche utile ou enregistrez sa page. Commencez par la sécurité, puis gardez uniquement l’action adaptée au moment.", M, 24*mm, W-2*M, fill=PALE_GREEN)
    page_done(c)

    # 3 sheet 1
    base_page(c,3,"Fiche 01","Les trente premières minutes","Vérifier  s’installer  sécuriser  prévenir",total=total)
    y=H-54*mm
    for i,(t,b) in enumerate([("Vérifier","Reprenez les signes d’alerte de la page 2."),("S’installer","Testez deux positions sûres pendant quelques minutes."),("Sécuriser","Dégagez le trajet et rapprochez les objets utiles."),("Prévenir","Demandez de l’aide pour une tâche urgente.")]):
        step_card(c,i+1,t,b,M,y-i*32*mm,W-2*M,27*mm,white if i%2 else PALE_GREEN)
    y-=134*mm
    rounded(c,M,y-61*mm,W-2*M,57*mm,PALE_CORAL,radius=5*mm)
    yy=y-10*mm
    yy=write_line(c,M+7*mm,yy,W-2*M-14*mm,"Ma position de répit",1)
    yy=write_line(c,M+7*mm,yy+2*mm,W-2*M-14*mm,"La prochaine action utile",1)
    write_line(c,M+7*mm,yy+2*mm,W-2*M-14*mm,"La personne à prévenir",1)
    info_strip(c, "Le bon niveau d’effort", "Une action brève et maîtrisée suffit. Si la situation change ou si un signe d’alerte apparaît, revenez à la fiche de sécurité.", M, 22*mm, W-2*M, fill=PALE_GREEN)
    page_done(c)

    # 4 sheet 2
    base_page(c,4,"Fiche 02","Quand demander de l’aide","Une décision de sécurité avant toute routine",total=total)
    y=H-54*mm
    rounded(c,M,y-78*mm,84*mm,74*mm,PALE_CORAL,radius=5*mm)
    c.setFillColor(RED); c.setFont("RD Bold",10); c.drawString(M+7*mm,y-12*mm,"Aide urgente")
    bullets(c,["difficulté à uriner ou fuites nouvelles","perte de sensibilité autour du périnée","faiblesse marquée ou progressive","traumatisme important","malaise ou symptôme inquiétant"],M+7*mm,y-22*mm,69*mm,RED)
    c.setFillColor(RED); c.setFont("RD Bold",8); c.drawString(M+7*mm,y-68*mm,"15 ou 112 en France")
    rounded(c,M+92*mm,y-78*mm,84*mm,74*mm,PALE_GREEN,radius=5*mm)
    c.setFillColor(PINE); c.setFont("RD Bold",10); c.drawString(M+99*mm,y-12*mm,"Avis rapide")
    bullets(c,["fièvre ou altération générale","douleur qui s’aggrave ou persiste au repos","engourdissement ou faiblesse nouvelle","perte de poids inexpliquée","forte limitation sans amélioration"],M+99*mm,y-22*mm,69*mm)
    y-=92*mm
    rounded(c,M,y-70*mm,W-2*M,66*mm,white,radius=5*mm)
    c.setFillColor(PINE); c.setFont("RD Bold",10); c.drawString(M+7*mm,y-12*mm,"Ce que je peux dire au téléphone")
    yy=y-21*mm
    yy=write_line(c,M+7*mm,yy,W-2*M-14*mm,"La douleur a commencé ou changé",1)
    yy=write_line(c,M+7*mm,yy+2*mm,W-2*M-14*mm,"Le symptôme qui m’inquiète",1)
    write_line(c,M+7*mm,yy+2*mm,W-2*M-14*mm,"Je suis seul ou accompagné",1)
    info_strip(c, "En attendant un rappel", "Gardez le téléphone près de vous, évitez un déplacement risqué et préparez votre adresse, vos traitements et l’heure de début des symptômes.", M, 28*mm, W-2*M, fill=PALE_CORAL)
    page_done(c)

    # 5 sheet 3
    base_page(c,5,"Fiche 03","Préparer une consultation","Donner au professionnel les informations utiles",total=total)
    draw_crop(c,IMAGES/"consultation-kine.png",M,H-145*mm,77*mm,91*mm,radius=5*mm)
    x=M+85*mm; y=H-58*mm
    c.setFillColor(PINE); c.setFont("RD Bold",10); c.drawString(x,y,"Avant le rendez-vous")
    yy=y-10*mm
    for lab in ["date et circonstances", "zone et irradiation", "symptômes associés", "traitements et examens", "deux questions"]:
        checkbox(c,x,yy,lab,size=3.5*mm,font=7.3); yy-=10*mm
    y=H-158*mm
    rounded(c,M,y-79*mm,W-2*M,75*mm,white,radius=5*mm)
    yy=y-10*mm
    yy=write_line(c,M+7*mm,yy,W-2*M-14*mm,"Ce que je ne peux plus faire",1)
    yy=write_line(c,M+7*mm,yy+2*mm,W-2*M-14*mm,"Ce que je peux encore faire",1)
    yy=write_line(c,M+7*mm,yy+2*mm,W-2*M-14*mm,"Ma question prioritaire",1)
    write_line(c,M+7*mm,yy+2*mm,W-2*M-14*mm,"Quand dois-je reconsulter",1)
    info_strip(c, "Pendant la consultation", "Commencez par ce que la douleur vous empêche de faire, puis décrivez ce qui reste possible. Cela aide à choisir une réponse adaptée.", M, 22*mm, W-2*M, fill=PALE_GREEN)
    page_done(c)

    # 6 sheet 4
    base_page(c,6,"Fiche 04","Organiser une journée difficile","Préserver l’essentiel sans rester immobile toute la journée",total=total)
    draw_crop(c,IMAGES/"factures-pression.png",M,H-141*mm,73*mm,87*mm,radius=5*mm)
    x=M+81*mm; y=H-58*mm
    for lab in ["Indispensable aujourd’hui","Peut être délégué","Peut attendre"]:
        y=write_line(c,x,y,95*mm,lab,1)+2*mm
    y=H-154*mm
    rounded(c,M,y-82*mm,W-2*M,78*mm,PALE_GREEN,radius=5*mm)
    c.setFillColor(PINE); c.setFont("RD Bold",10); c.drawString(M+7*mm,y-12*mm,"Créer un rythme")
    bullets(c,["alterner une tâche courte et un repos bref","changer de position avant une longue période figée","garder un déplacement simple","préparer les objets avant la tâche"],M+7*mm,y-22*mm,78*mm)
    c.setFillColor(PINE); c.setFont("RD Bold",12); c.drawString(M+94*mm,y-12*mm,"Réduire la charge mentale")
    paragraph(c,"Regroupez les justificatifs et demandez les conditions de prise en charge avant une dépense importante.",M+94*mm,y-22*mm,75*mm,"body")
    write_line(c,M+94*mm,y-56*mm,75*mm,"La personne que je peux appeler",1)
    info_strip(c, "Une journée suffisamment réussie", "Vous avez protégé l’essentiel, changé de position au moins une fois et demandé une aide utile. Le reste peut attendre.", M, 26*mm, W-2*M, fill=PALE_CORAL)
    page_done(c)

    # 7 sheet 5
    base_page(c,7,"Fiche 05","Bouger quand on travaille assis","Varier plutôt que chercher la posture parfaite",total=total)
    draw_contain(c,ILLUS/"travail-deplacements-v1.png",M,H-151*mm,W-2*M,97*mm)
    y=H-158*mm
    rounded(c,M,y-72*mm,85*mm,68*mm,white,radius=5*mm)
    c.setFillColor(PINE); c.setFont("RD Bold",10); c.drawString(M+7*mm,y-12*mm,"Plan de la demi-journée")
    yy=y-23*mm
    for lab in ["pieds soutenus", "changement de position", "appel debout", "courte marche"]:
        checkbox(c,M+7*mm,yy,lab,size=3.5*mm,font=7.4); yy-=10*mm
    rounded(c,M+92*mm,y-72*mm,84*mm,68*mm,PALE_GREEN,radius=5*mm)
    c.setFillColor(PINE); c.setFont("RD Bold",10); c.drawString(M+99*mm,y-12*mm,"Adaptation à discuter")
    bullets(c,["alterner les tâches","réduire les charges","adapter temporairement les horaires","contacter le médecin du travail"],M+99*mm,y-22*mm,70*mm)
    info_strip(c, "Le rappel utile", "Il n’existe pas une posture parfaite à tenir. Le plus utile est de varier, de fractionner et d’organiser une courte reprise de mouvement.", M, 23*mm, W-2*M, fill=PALE_CORAL)
    page_done(c)

    # 8 sheet 6
    base_page(c,8,"Fiche 06","Préparer la nuit","Chercher le confort sans imposer une position unique",total=total)
    y=H-55*mm
    rounded(c,M,y-76*mm,82*mm,72*mm,white,radius=5*mm)
    c.setFillColor(PINE); c.setFont("RD Bold",10); c.drawString(M+7*mm,y-12*mm,"Avant de vous coucher")
    yy=y-23*mm
    for lab in ["trajet éclairé", "objets à portée", "coussin testé", "lever préparé"]:
        checkbox(c,M+7*mm,yy,lab,size=3.5*mm,font=7.5); yy-=10*mm
    rounded(c,M+90*mm,y-76*mm,86*mm,72*mm,PALE_GREEN,radius=5*mm)
    c.setFillColor(PINE); c.setFont("RD Bold",10); c.drawString(M+97*mm,y-12*mm,"Si le sommeil est interrompu")
    paragraph(c,"Changez de position ou levez-vous quelques instants si cela vous aide. Une mauvaise nuit ne prouve pas une aggravation. Demandez un avis si la douleur nocturne est incessante ou s’accompagne d’un signe d’alerte.",M+97*mm,y-22*mm,72*mm,"small")
    y-=91*mm
    draw_crop(c,IMAGES/"douleur-dos-hero.png",M,y-63*mm,64*mm,59*mm,radius=5*mm)
    rounded(c,M+72*mm,y-63*mm,104*mm,59*mm,PALE_CORAL,radius=5*mm)
    yy=y-10*mm
    yy=write_line(c,M+79*mm,yy,90*mm,"La position la plus confortable",1)
    yy=write_line(c,M+79*mm,yy+2*mm,90*mm,"Ce qui facilite le lever",1)
    write_line(c,M+79*mm,yy+2*mm,90*mm,"Le changement à signaler",1)
    info_strip(c, "Un réveil n’est pas un échec", "Changez de position, faites quelques pas si cela vous aide, puis revenez au repos. Une seule nuit ne résume pas votre évolution.", M, 28*mm, W-2*M, fill=PALE_GREEN)
    page_done(c)

    # 9 sheet 7
    base_page(c,9,"Fiche 07","Utiliser une aide à la marche","Sécuriser le déplacement avant de chercher la distance",total=total)
    draw_crop(c,IMAGES/"bequilles-mobilite.png",M,H-150*mm,82*mm,96*mm,radius=5*mm)
    x=M+90*mm; y=H-58*mm
    c.setFillColor(PINE); c.setFont("RD Bold",10); c.drawString(x,y,"Avant l’utilisation")
    yy=y-11*mm
    for lab in ["embouts et stabilité", "chaussures stables", "sol dégagé", "consignes reçues"]:
        checkbox(c,x,yy,lab,size=3.5*mm,font=7.3); yy-=10*mm
    rounded(c,x,y-88*mm,86*mm,39*mm,PALE_CORAL,radius=4*mm)
    paragraph(c,"<b>Première utilisation</b><br/>La hauteur, le côté et la séquence de marche doivent être expliqués par un professionnel.",x+6*mm,y-58*mm,74*mm,"small")
    y=H-166*mm
    rounded(c,M,y-69*mm,W-2*M,65*mm,white,radius=5*mm)
    c.setFillColor(RED); c.setFont("RD Bold",9); c.drawString(M+7*mm,y-12*mm,"ARRÊTEZ ET DEMANDEZ DE L’AIDE SI")
    bullets(c,["l’aide augmente le risque de chute","un malaise ou une faiblesse nouvelle apparaît","vous devez utiliser un escalier sans avoir appris la technique","le réglage vous oblige à vous pencher ou vous déséquilibre"],M+7*mm,y-23*mm,W-2*M-14*mm,RED)
    info_strip(c, "La première utilisation", "Demandez à un professionnel de régler la hauteur, le côté et la séquence de marche. Vérifiez ensuite les embouts et le sol.", M, 25*mm, W-2*M, fill=PALE_GREEN)
    page_done(c)

    # 10 sheet 8
    base_page(c,10,"Fiche 08","Faire le bilan de la semaine","Transformer les observations en une seule décision",total=total)
    y=H-55*mm
    rounded(c,M,y-101*mm,W-2*M,97*mm,white,radius=5*mm)
    yy=y-11*mm
    for lab in ["Une activité devenue plus facile","Une activité encore évitée","Une réponse devenue plus prévisible","Le réglage qui m’aide","Le signe qui justifie un avis"]:
        yy=write_line(c,M+7*mm,yy,W-2*M-14*mm,lab,1)+1*mm
    y-=116*mm
    c.setFillColor(PINE); c.setFont("RD Bold",10); c.drawString(M,y,"Ma décision")
    yy=y-12*mm
    for lab in ["Je conserve la même dose.","J’augmente un seul paramètre.","Je réduis et je demande conseil.","Je consulte car la situation a changé."]:
        checkbox(c,M,yy,lab,size=4*mm,font=8.1); yy-=11*mm
    rounded(c,M+100*mm,y-56*mm,76*mm,52*mm,PALE_GREEN,radius=5*mm)
    c.setFillColor(PINE); c.setFont("RD Bold",9); c.drawString(M+106*mm,y-13*mm,"Mon prochain rendez-vous")
    write_line(c,M+106*mm,y-23*mm,64*mm,"Date",1)
    write_line(c,M+106*mm,y-41*mm,64*mm,"Action choisie",1)
    info_strip(c, "Un bilan sert à décider", "Choisissez une seule suite : continuer, ajuster un paramètre ou demander conseil. Vous n’avez pas à tout corriger en même temps.", M, 27*mm, W-2*M, fill=PALE_CORAL)
    page_done(c)

    # 11 cut-out mini cards
    base_page(c,11,"Aide-mémoire","Trois cartes à garder près de vous","Découpez ou photographiez la carte utile",total=total)
    y=H-55*mm
    cards=[
        ("MAINTENANT",CORAL,["Je vérifie la sécurité","Je choisis une position de répit","Je fais un déplacement court","Je préviens quelqu’un si besoin"]),
        ("PENDANT",PINE_2,["Je garde un souffle fluide","Je réduis la durée si nécessaire","Je ne me teste pas","J’observe la réponse plus tard"]),
        ("APRÈS",GREEN,["Je note une capacité","Je garde le réglage utile","J’augmente un seul paramètre","Je demande conseil en cas de doute"]),
    ]
    for i,(title,col,items) in enumerate(cards):
        yy=y-i*62*mm
        c.setDash(3,2); c.setStrokeColor(GREY); c.roundRect(M,yy-55*mm,W-2*M,51*mm,4*mm,fill=0,stroke=1); c.setDash()
        c.setFillColor(col); c.roundRect(M+5*mm,yy-48*mm,44*mm,37*mm,4*mm,fill=1,stroke=0)
        c.setFillColor(white); c.setFont("RD Narrow Bold",14); c.drawCentredString(M+27*mm,yy-28*mm,title)
        bullets(c,items,M+57*mm,yy-14*mm,110*mm)
    page_done(c)

    # 12 sources
    sources_page(c,12,total,"Fiches pratiques Le Réflexe Dos  Lot 01")
    page_done(c)
    c.save()
    assert len(PdfReader(str(path)).pages)==12
    return path


if __name__ == "__main__":
    for output in (build_guide(), build_sheets()):
        print(output)
