from pathlib import Path
from io import BytesIO

from PIL import Image as PILImage
from pypdf import PdfReader
from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph


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

pdfmetrics.registerFont(TTFont("RD Body", r"C:\Windows\Fonts\arial.ttf"))
pdfmetrics.registerFont(TTFont("RD Bold", r"C:\Windows\Fonts\arialbd.ttf"))
pdfmetrics.registerFont(TTFont("RD Narrow", r"C:\Windows\Fonts\ARIALN.TTF"))
pdfmetrics.registerFont(TTFont("RD Narrow Bold", r"C:\Windows\Fonts\ARIALNB.TTF"))

MIN_FONT_SIZE = 12


class AccessibleCanvas(canvas.Canvas):
    def setFont(self, font_name, size, leading=None):
        safe_size = max(MIN_FONT_SIZE, size)
        safe_leading = None if leading is None else max(MIN_FONT_SIZE * 1.2, leading)
        return super().setFont(font_name, safe_size, safe_leading)


STYLES = {
    "body": ParagraphStyle("body", fontName="RD Body", fontSize=12.5, leading=16.2, textColor=INK),
    "small": ParagraphStyle("small", fontName="RD Body", fontSize=12, leading=15.2, textColor=GREY),
    "bold": ParagraphStyle("bold", fontName="RD Bold", fontSize=12.5, leading=16.2, textColor=INK),
    "h1": ParagraphStyle("h1", fontName="RD Narrow Bold", fontSize=25, leading=26, textColor=INK),
    "h1long": ParagraphStyle("h1long", fontName="RD Narrow Bold", fontSize=20.5, leading=22, textColor=INK),
    "h2": ParagraphStyle("h2", fontName="RD Narrow Bold", fontSize=19, leading=21, textColor=PINE),
    "h3": ParagraphStyle("h3", fontName="RD Bold", fontSize=14, leading=17, textColor=PINE),
    "center": ParagraphStyle("center", fontName="RD Body", fontSize=12, leading=15.2, alignment=TA_CENTER, textColor=GREY),
}


def esc(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def paragraph(c, text, x, y_top, width, style="body", color=None):
    st = STYLES[style]
    if color is not None:
        st = ParagraphStyle(f"{style}-{color}", parent=st, textColor=color)
    p = Paragraph(text, st)
    _, h = p.wrap(width, H)
    p.drawOn(c, x, y_top - h)
    return y_top - h


def rounded(c, x, y, w, h, fill, radius=4 * mm, stroke=None):
    c.setFillColor(fill)
    c.setStrokeColor(stroke or fill)
    c.setLineWidth(0.8)
    c.roundRect(x, y, w, h, radius, fill=1, stroke=1 if stroke else 0)


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
    im.save(buf, format="JPEG", quality=91)
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


def page_header(c, page_no, total, section, title, subtitle=""):
    c.setFillColor(CREAM)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(CORAL)
    c.setFont("RD Bold", 12)
    c.drawString(M, H - 14 * mm, section.upper())
    paragraph(c, esc(title), M, H - 21 * mm, W - 2 * M, "h1long" if len(title) > 40 else "h1")
    if subtitle:
        paragraph(c, esc(subtitle), M, H - 34 * mm, W - 2 * M, "small")
    c.setStrokeColor(CORAL)
    c.setLineWidth(2)
    c.line(M, H - 42 * mm, M + 18 * mm, H - 42 * mm)
    c.setFillColor(GREY)
    c.setFont("RD Body", 12)
    c.drawString(M, 10 * mm, "LE RÉFLEXE DOS  -  ÉDITION FINALE")
    c.setFont("RD Bold", 12)
    c.drawRightString(W - M, 10 * mm, f"{page_no} / {total}")


def card(c, x, y_top, w, h, number, title, body, tint=PALE_GREEN):
    rounded(c, x, y_top - h, w, h, tint, radius=4 * mm)
    c.setFillColor(CORAL)
    c.circle(x + 8 * mm, y_top - 9 * mm, 5 * mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("RD Bold", 12)
    c.drawCentredString(x + 8 * mm, y_top - 11 * mm, str(number))
    c.setFillColor(PINE)
    c.setFont("RD Bold", 12.5)
    c.drawString(x + 16 * mm, y_top - 8 * mm, title)
    paragraph(c, esc(body), x + 16 * mm, y_top - 14 * mm, w - 21 * mm, "small", INK)


def info_box(c, x, y, w, h, title, body, tint=PALE_CORAL):
    rounded(c, x, y, w, h, tint, radius=4 * mm)
    c.setFillColor(PINE)
    c.setFont("RD Bold", 12.5)
    c.drawString(x + 6 * mm, y + h - 9 * mm, title)
    paragraph(c, esc(body), x + 6 * mm, y + h - 15 * mm, w - 12 * mm, "small", INK)


PHOTOS = {
    "consultation": IMAGES / "consultation-kine.png",
    "crise": IMAGES / "douleur-dos-hero.png",
    "factures": IMAGES / "factures-pression.png",
    "marche": IMAGES / "bequilles-mobilite.png",
    "quotidien": IMAGES / "quotidien-chaussures.png",
    "mobilite": IMAGES / "exercice-mobilite.png",
    "lever": ILLUS / "sortie-lit-habillage-v1.png",
    "travail": ILLUS / "travail-deplacements-v1.png",
    "sequence": ILLUS / "mobilite-douce-sequence-v1.png",
}


GUIDE_PAGES = [
    ("Comprendre", "Une crise impressionnante, pas forcément dangereuse", "Mettre des mots simples sur ce qui arrive", "Une douleur vive peut donner l'impression que le dos est abîmé. L'intensité ressentie et la gravité médicale ne vont pourtant pas toujours ensemble. La première étape consiste à vérifier la sécurité, puis à retrouver des gestes tolérables.", [("Vérifier", "Reprenez les signes d'alerte avant toute activité."), ("Respirer", "Ralentissez l'expiration pour réduire la tension du moment."), ("Observer", "Notez ce qui reste possible sans tester vos limites."), ("Décider", "Choisissez une seule action utile pour l'heure qui vient.")], "Vous n'avez pas à tout résoudre aujourd'hui. Sécurité, confort puis mouvement progressif suffisent comme cap.", "crise"),
    ("Comprendre", "Douleur et capacité ne racontent pas la même chose", "Suivre ce que vous pouvez faire, pas seulement un chiffre", "Une échelle de douleur peut aider, mais elle ne résume pas votre journée. La capacité à vous lever, vous habiller, marcher quelques minutes ou préparer un repas donne aussi des repères utiles.", [("Nommer", "Décrivez l'activité difficile avec des mots concrets."), ("Comparer", "Regardez l'évolution d'une journée à l'autre, pas minute par minute."), ("Adapter", "Réduisez la durée ou l'amplitude avant d'abandonner."), ("Valoriser", "Notez une capacité préservée, même modeste.")], "Le progrès peut être une tâche plus simple, une récupération plus rapide ou une réaction plus prévisible.", None),
    ("Comprendre", "Pourquoi rester un peu actif aide", "Éviter le piège du repos prolongé", "Quand la situation est compatible avec une lombalgie commune, le maintien d'activités adaptées aide souvent à préserver la confiance et les capacités. Il ne s'agit ni de forcer ni d'ignorer la douleur.", [("Fractionner", "Transformez une tâche longue en plusieurs séquences courtes."), ("Varier", "Changez de position avant d'être épuisé."), ("Tester", "Essayez une petite dose, puis observez la réponse plus tard."), ("Récupérer", "Utilisez des pauses brèves sans passer toute la journée au lit.")], "Le bon mouvement est celui qui reste maîtrisé et vous permet de revenir à un niveau supportable.", "mobilite"),
    ("Comprendre", "Votre feu tricolore personnel", "Une règle simple pour ajuster sans paniquer", "Le feu tricolore ne remplace pas un avis médical. Il vous aide à décider quoi faire lorsqu'aucun signe d'alerte n'est présent.", [("Vert", "Gêne stable et geste maîtrisé: poursuivez à petite dose."), ("Orange", "Réaction plus forte ou durable: réduisez un seul paramètre."), ("Rouge", "Symptôme nouveau inquiétant: arrêtez et demandez un avis."), ("Noter", "Écrivez ce qui a été fait et la réponse observée.")], "Ne changez qu'une variable à la fois: durée, distance, charge ou vitesse.", None),
    ("Mode d'emploi", "Votre itinéraire sur sept jours", "Une progression souple, pas un examen à réussir", "Chaque journée propose un thème principal. Vous pouvez rester plus longtemps sur une étape, revenir en arrière ou demander conseil. Le calendrier sert à réduire la charge mentale.", [("Jour 0", "Sécuriser, s'installer et prévenir une personne."), ("Jours 1-2", "Retrouver les gestes de base et un peu de mobilité."), ("Jours 3-5", "Réintroduire tâches, déplacements et travail adapté."), ("Jours 6-7", "Préparer un avis et choisir la suite.")], "Votre objectif n'est pas zéro douleur en sept jours, mais une situation plus sûre, plus compréhensible et mieux organisée.", None),
    ("Jour 0", "Les trente premières minutes", "Réduire l'incertitude avant de chercher une solution", "Après la vérification de sécurité, installez-vous, dégagez votre environnement et prévenez une personne si nécessaire. Évitez les tests répétés pour savoir si le dos est débloqué.", [("Sécuriser", "Éloignez les obstacles et rapprochez téléphone, eau et traitement habituel."), ("S'installer", "Testez calmement deux positions de repos."), ("Prévenir", "Expliquez en une phrase ce dont vous avez besoin."), ("Reporter", "Différez la tâche non urgente qui vous met en difficulté.")], "Une première heure organisée diminue les décisions à prendre sous stress.", "crise"),
    ("Jour 0", "Trouver une position de répit", "Chercher le confort sans imposer une posture parfaite", "Il n'existe pas une position universelle. Une position de répit doit diminuer l'effort, rester facile à quitter et ne pas provoquer de symptôme nouveau.", [("Tester", "Essayez quelques minutes sur le côté, sur le dos ou assis soutenu."), ("Soutenir", "Placez un coussin là où il réduit réellement la tension."), ("Changer", "Variez dès que la position devient inconfortable."), ("Préparer", "Avant de vous reposer, organisez le prochain lever.")], "Le repos est un outil ponctuel. Il ne doit pas devenir la seule stratégie de la journée.", None),
    ("Jour 0", "Se relever avec des appuis", "Préparer le trajet avant le mouvement", "Un lever peut être impressionnant lorsque la douleur est vive. Ralentissez la séquence et utilisez les appuis disponibles plutôt que de chercher un geste parfait.", [("Regarder", "Repérez le support stable et le trajet dégagé."), ("Tourner", "Rapprochez-vous du bord avec de petits mouvements."), ("Pousser", "Utilisez les bras et les jambes pour répartir l'effort."), ("Attendre", "Une fois debout, stabilisez-vous avant de marcher.")], "Si vous vous sentez faible, étourdi ou en danger de chute, demandez une aide directe.", "lever"),
    ("Jour 1", "Construire un rythme supportable", "Alterner action courte et récupération", "La journée peut être découpée en petits blocs prévisibles. Cette organisation protège vos ressources et évite le cycle tout faire puis ne plus pouvoir bouger.", [("Choisir", "Gardez une priorité indispensable pour la matinée."), ("Limiter", "Fixez une durée courte avant de commencer."), ("Changer", "Alternez assis, debout, marche et repos."), ("Réévaluer", "Regardez la réponse après le bloc, pas à chaque seconde.")], "Une journée réussie protège l'essentiel; elle n'a pas besoin de ressembler à une journée habituelle.", None),
    ("Jour 1", "S'habiller avec moins d'effort", "Préparer les vêtements et utiliser un appui", "Réduisez les flexions répétées et les équilibres inutiles. S'asseoir pour enfiler le bas et rapprocher les vêtements permet souvent de conserver de l'énergie.", [("Préparer", "Posez les vêtements à hauteur de main."), ("S'asseoir", "Utilisez une chaise stable pour le pantalon et les chaussures."), ("Simplifier", "Choisissez des vêtements faciles à enfiler."), ("Accepter", "Demandez une aide ponctuelle si un geste reste risqué.")], "L'autonomie inclut le fait de choisir une aide utile au bon moment.", "quotidien"),
    ("Jour 1", "Toilette et salle de bains", "Prévenir la glissade et les gestes précipités", "La salle de bains combine sol humide, appuis parfois fragiles et mouvements contraints. Préparez l'espace avant d'entrer et gardez le nécessaire accessible.", [("Dégager", "Retirez tapis instable et objets au sol."), ("Rapprocher", "Placez serviette et produits à portée."), ("Soutenir", "Utilisez uniquement un appui réellement stable."), ("Reporter", "Choisissez une toilette simplifiée si la douche est risquée.")], "La sécurité compte davantage qu'une routine parfaite pendant quelques jours.", None),
    ("Jour 1", "Préparer un repas simple", "Économiser les déplacements et les charges", "Un repas nourrissant peut rester très simple. Rassemblez les ingrédients, travaillez à hauteur confortable et utilisez de petites quantités.", [("Rassembler", "Posez tout le nécessaire sur le plan de travail."), ("Alléger", "Préférez plusieurs petits contenants à une charge lourde."), ("S'asseoir", "Préparez une partie du repas assis si cela aide."), ("Déléguer", "Demandez les courses ou utilisez une livraison si possible.")], "Manger et boire régulièrement soutient la journée; la cuisine élaborée peut attendre.", None),
    ("Jour 2", "Faire un point au réveil", "Regarder l'ensemble avant de conclure", "Une nuit difficile ne signifie pas forcément que la situation s'aggrave. Vérifiez les symptômes nouveaux, puis observez les capacités concrètes disponibles ce matin.", [("Sécurité", "Reprenez les signes d'alerte en cas de changement."), ("Capacité", "Notez un geste plus facile, identique ou plus difficile."), ("Contexte", "Tenez compte du sommeil, du stress et de l'activité d'hier."), ("Plan", "Choisissez une dose d'activité adaptée à ce matin.")], "Décidez avec plusieurs repères, pas avec une sensation isolée au premier mouvement.", None),
    ("Jour 2", "Utiliser la respiration comme repère", "Créer un mouvement plus calme", "Respirer ne répare pas le dos, mais un souffle fluide aide à éviter le blocage volontaire et à observer si le geste reste maîtrisé.", [("Installer", "Choisissez une position où vous vous sentez soutenu."), ("Souffler", "Laissez l'expiration durer un peu plus longtemps."), ("Associer", "Gardez ce souffle pendant un petit changement de position."), ("Arrêter", "Interrompez si vous vous sentez étourdi ou mal.")], "Le souffle sert de témoin: si vous le bloquez, réduisez l'effort ou la durée.", None),
    ("Jour 2", "Explorer une mobilité douce", "Choisir une option, pas une série obligatoire", "Une petite mobilité peut être réalisée assis, debout avec appui ou allongé selon votre confort. L'objectif est d'explorer, pas de gagner de l'amplitude.", [("Choisir", "Prenez une seule direction qui paraît accessible."), ("Réduire", "Faites un mouvement plus petit que votre maximum."), ("Répéter", "Restez sur quelques répétitions lentes."), ("Observer", "Regardez la réponse pendant et après l'essai.")], "Aucune douleur ne doit être prouvée ou vaincue. Le test reste facultatif.", "sequence"),
    ("Jour 2", "Tester une marche très courte", "Préparer le retour avant le départ", "La marche est une activité quotidienne modulable. Commencez sur un trajet plat, connu et suffisamment court pour conserver une marge au retour.", [("Tracer", "Choisissez un aller-retour simple et sans obstacle."), ("Équiper", "Portez des chaussures stables et gardez le téléphone."), ("Doser", "Arrêtez avant l'épuisement plutôt qu'après."), ("Noter", "Écrivez la distance ou la durée réellement tolérée.")], "Le prochain essai peut rester identique. Progresser n'oblige pas à augmenter chaque jour.", "marche"),
    ("Jour 3", "Choisir une tâche utile", "Reprendre une part de la vie réelle", "Une petite tâche concrète donne souvent plus d'informations qu'un test abstrait. Choisissez une action importante pour vous et rendez-la plus facile.", [("Prioriser", "Sélectionnez une seule tâche qui change réellement la journée."), ("Préparer", "Rassemblez outils et objets avant de commencer."), ("Fractionner", "Découpez la tâche en étapes courtes."), ("Terminer tôt", "Gardez de l'énergie pour la suite de la journée.")], "Une tâche adaptée n'est pas un échec: c'est une manière de rester acteur.", None),
    ("Jour 3", "Utiliser les escaliers", "Réduire le risque avant de chercher la fluidité", "Si les escaliers sont indispensables, utilisez la rampe, évitez de porter une charge et prenez votre temps. Si vous ne vous sentez pas stable, demandez une aide.", [("Dégager", "Vérifiez l'éclairage et retirez les objets des marches."), ("Appuyer", "Gardez une main disponible pour la rampe."), ("Ralentir", "Posez le pied complètement avant l'étape suivante."), ("Reporter", "Évitez les allers-retours non nécessaires.")], "La priorité est d'arriver en sécurité, pas de monter comme d'habitude.", None),
    ("Jour 3", "Entrer et sortir d'une voiture", "Organiser le pivot et limiter la torsion", "Préparez le siège et ouvrez largement la portière. Une séquence lente avec les pieds et le bassin qui tournent ensemble peut être plus confortable.", [("Régler", "Reculez le siège avant de vous installer."), ("S'asseoir", "Placez d'abord le bassin sur le siège."), ("Regrouper", "Faites entrer les jambes avec un mouvement progressif."), ("Interrompre", "Faites une pause avant de démarrer si nécessaire.")], "Pour un trajet, prévoyez aussi l'arrivée, le stationnement et la possibilité de faire une pause.", "travail"),
    ("Jour 3", "Prendre les transports", "Choisir le trajet le plus prévisible", "Les attentes, les marches et les mouvements du véhicule peuvent peser davantage que la durée. Préparez un itinéraire simple et une solution de repli.", [("Éviter", "Choisissez si possible une heure moins chargée."), ("Soutenir", "Gardez une main libre pour un appui."), ("S'asseoir", "Utilisez une place accessible sans culpabilité."), ("Revenir", "Prévoyez comment rentrer si la tolérance diminue.")], "La meilleure option est celle qui réduit les surprises et vous laisse une marge.", None),
    ("Jour 4", "Sortir de chez soi", "Transformer la sortie en mission simple", "Une première sortie peut servir à prendre l'air, récupérer un objet ou voir une personne. Gardez un objectif unique, proche et facultatif.", [("Définir", "Écrivez le but concret de la sortie."), ("Préparer", "Vérifiez chaussures, téléphone, clés et moyen de retour."), ("Limiter", "Choisissez une durée courte et un trajet connu."), ("Récupérer", "Prévoyez un temps calme après le retour.")], "Une sortie courte et maîtrisée vaut mieux qu'un défi qui épuise la journée.", None),
    ("Jour 4", "Travailler assis", "Varier plutôt que chercher la posture parfaite", "Aucune posture ne doit être tenue sans fin. Ajustez l'écran, soutenez les pieds et organisez des changements de position réguliers.", [("Rapprocher", "Placez clavier, téléphone et documents dans la zone facile."), ("Soutenir", "Ajustez pieds et dossier sans vous rigidifier."), ("Varier", "Alternez assis, debout et quelques pas."), ("Planifier", "Mettez les tâches les plus exigeantes au meilleur moment.")], "Le poste idéal n'existe pas; une journée modulable est souvent plus utile.", "travail"),
    ("Jour 4", "Travailler debout ou manipuler", "Réduire charge, portée et répétition", "Pour une activité physique, les contraintes importantes sont la charge, la distance au corps, la répétition et l'urgence. Modifiez au moins l'un de ces paramètres.", [("Rapprocher", "Gardez l'objet près du corps avant de le déplacer."), ("Diviser", "Répartissez une charge en plusieurs éléments."), ("Alterner", "Changez de tâche avant la fatigue marquée."), ("Demander", "Sollicitez un collègue pour le geste non adaptable.")], "Un aménagement temporaire protège la reprise; il ne définit pas vos capacités futures.", None),
    ("Jour 4", "Faire des pauses qui aident", "Une pause n'est pas forcément l'immobilité", "La pause utile change la contrainte dominante. Après être resté assis, quelques pas peuvent aider; après une activité debout, un appui ou une assise peut convenir.", [("Anticiper", "Faites la pause avant d'être complètement bloqué."), ("Changer", "Choisissez une position différente de l'activité précédente."), ("Respirer", "Relâchez les épaules et gardez un souffle fluide."), ("Reprendre", "Revenez avec une durée ou une tâche clairement limitée.")], "Une pause réussie facilite la suite; elle n'a pas besoin de supprimer toute douleur.", None),
    ("Jour 5", "Préparer une reprise", "Décrire les exigences réelles du travail", "Avant de fixer une date ou un volume, listez les tâches, les trajets, les horaires et les possibilités d'alternance. Cette description facilite une décision adaptée avec les professionnels concernés.", [("Lister", "Notez les trois contraintes principales du poste."), ("Identifier", "Repérez les tâches temporairement adaptables."), ("Proposer", "Préparez une demande simple et limitée dans le temps."), ("Coordonner", "Demandez un avis médical ou du travail si nécessaire.")], "La reprise n'est pas seulement une date: c'est une organisation concrète.", None),
    ("Jour 5", "Demander un aménagement", "Parler de la tâche plutôt que de se justifier", "Une demande claire associe une difficulté observable, une adaptation précise et une durée de réévaluation. Vous n'avez pas à raconter tous les détails médicaux.", [("Décrire", "Indiquez le geste ou la durée qui pose problème."), ("Proposer", "Suggérez alternance, charge réduite ou pause planifiée."), ("Limiter", "Précisez que la mesure sera réévaluée."), ("Confirmer", "Résumez l'accord par écrit si possible.")], "Exemple: pendant une semaine, j'ai besoin d'alterner assis et debout toutes les trente minutes.", None),
    ("Jour 5", "Quand les factures s'accumulent", "Réduire la charge mentale administrative", "La douleur rend les démarches plus lourdes. Regroupez les documents, demandez les conditions de prise en charge avant une dépense importante et choisissez une personne ressource.", [("Rassembler", "Créez un seul dossier pour ordonnances, factures et justificatifs."), ("Vérifier", "Demandez devis, remboursement et reste à charge."), ("Appeler", "Préparez une question précise avant chaque contact."), ("Déléguer", "Autorisez une personne à vous aider pour une démarche ciblée.")], "Une démarche administrative par jour peut suffire. Le reste peut attendre.", "factures"),
    ("Jour 5", "Organiser la vie familiale", "Préserver l'essentiel sans tout porter", "Expliquez ce qui est temporairement difficile et ce qui reste possible. Répartissez les tâches visibles afin que l'aide ne dépende pas de demandes répétées.", [("Nommer", "Dites les deux tâches actuellement les plus difficiles."), ("Répartir", "Attribuez courses, repas, enfants ou animaux."), ("Simplifier", "Choisissez des standards plus légers pour quelques jours."), ("Remercier", "Reconnaissez l'aide sans vous sentir obligé de compenser.")], "Recevoir de l'aide aujourd'hui peut soutenir votre retour à l'autonomie demain.", None),
    ("Jour 6", "Préparer la consultation", "Donner les informations qui changent la décision", "Un résumé bref aide le professionnel à comprendre l'évolution, les limitations et les symptômes associés. Apportez aussi la liste des traitements et examens déjà réalisés.", [("Chronologie", "Notez le début, les changements et les épisodes précédents."), ("Zone", "Décrivez l'endroit et une éventuelle irradiation."), ("Capacités", "Citez ce que vous ne pouvez plus et pouvez encore faire."), ("Questions", "Choisissez deux questions prioritaires.")], "Montrez votre carnet plutôt que d'essayer de tout retenir sous stress.", "consultation"),
    ("Jour 6", "Décrire la douleur utilement", "Passer d'un mot général à des observations", "Le professionnel a besoin de connaître le contexte, les symptômes associés et l'impact fonctionnel. Une description simple est suffisante; vous n'avez pas à trouver vous-même le diagnostic.", [("Début", "Précisez quand et dans quelles circonstances cela a commencé."), ("Évolution", "Expliquez ce qui a changé depuis le premier jour."), ("Associés", "Signalez faiblesse, engourdissement, fièvre ou autre changement."), ("Impact", "Nommez les activités devenues impossibles ou limitées.")], "Dites d'abord ce qui vous inquiète le plus; cela oriente la conversation.", None),
    ("Jour 6", "Les questions à poser", "Quitter le rendez-vous avec un plan compréhensible", "Avant la fin de la consultation, vérifiez que vous savez quoi faire, ce qui doit vous faire reconsulter et comment progresser.", [("Comprendre", "Quelle est l'hypothèse principale et que faut-il surveiller?"), ("Agir", "Quelles activités sont encouragées ou temporairement adaptées?"), ("Réévaluer", "Dans quel délai attendre une évolution?"), ("Reconsulter", "Quels changements justifient un nouvel avis rapidement?")], "Demandez au professionnel de reformuler si une consigne reste vague.", None),
    ("Jour 6", "Parler des médicaments", "Sécuriser les informations sans improviser", "Ce guide ne recommande aucun médicament. Préparez la liste de ce que vous prenez, des allergies, des effets ressentis et des autres maladies afin d'en parler au médecin ou au pharmacien.", [("Lister", "Notez nom, dose, horaire et automédication."), ("Signaler", "Mentionnez grossesse, maladie chronique, allergie ou interaction connue."), ("Questionner", "Demandez durée, effet attendu et signes nécessitant un arrêt."), ("Éviter", "Ne cumulez pas des produits sans vérifier leurs substances actives.")], "En cas de doute, demandez au pharmacien ou au médecin plutôt que de modifier seul le traitement.", None),
    ("Jour 7", "Faire le bilan de la semaine", "Transformer les observations en une décision", "Relisez les capacités, les réactions et les changements importants. Le bilan sert à choisir la prochaine étape, pas à juger vos efforts.", [("Comparer", "Choisissez deux activités mesurables du jour 1 et du jour 7."), ("Repérer", "Notez la stratégie qui vous aide le plus."), ("Classer", "Décidez: amélioration, plateau ou aggravation."), ("Choisir", "Gardez une seule priorité pour la semaine suivante.")], "Une évolution irrégulière peut rester une amélioration si les capacités reviennent globalement.", None),
    ("Jour 7", "Si vous vous améliorez", "Consolider avant d'accélérer", "Quand les gestes deviennent plus faciles ou la récupération plus rapide, conservez les adaptations utiles et augmentez un seul paramètre à la fois.", [("Stabiliser", "Répétez une dose bien tolérée avant de l'augmenter."), ("Choisir", "Augmentez seulement durée, distance, charge ou fréquence."), ("Observer", "Regardez la réponse le jour même et le lendemain."), ("Continuer", "Gardez sommeil, pauses et organisation simples.")], "Le mieux n'impose pas de rattraper tout ce qui a été reporté.", None),
    ("Jour 7", "Si la situation stagne", "Chercher un avis et préciser les obstacles", "Une stagnation mérite d'être replacée dans le contexte: durée, sommeil, travail, inquiétudes, ressources et symptômes associés. Un professionnel peut aider à ajuster le plan.", [("Résumer", "Préparez votre chronologie sur une page."), ("Identifier", "Nommez l'activité la plus limitée."), ("Demander", "Sollicitez un avis selon la durée et votre situation."), ("Maintenir", "Conservez les mouvements et tâches tolérables.")], "Stagner ne signifie pas échouer; cela indique que le plan mérite d'être réévalué.", None),
    ("Jour 7", "Si la situation s'aggrave", "Revenir à la sécurité avant toute progression", "Une aggravation nette, un symptôme nouveau ou un changement général doit faire interrompre le programme et demander un avis adapté. En cas de signe d'alerte, utilisez les numéros d'urgence.", [("Arrêter", "Suspendez les nouveaux exercices et efforts non indispensables."), ("Vérifier", "Reprenez la liste des signes d'alerte."), ("Contacter", "Appelez le professionnel ou le service approprié."), ("Préparer", "Gardez adresse, traitements et début des symptômes à portée.")], "Vous ne perdez pas le bénéfice de la semaine en demandant de l'aide; vous sécurisez la suite.", None),
    ("Au quotidien", "Préparer la nuit", "Chercher du confort sans imposer une position", "La nuit peut être plus simple si le trajet, les objets utiles et le prochain lever sont anticipés. Une mauvaise nuit isolée ne prédit pas la suite.", [("Préparer", "Dégagez le trajet et gardez téléphone et eau accessibles."), ("Tester", "Choisissez une position et un coussin réellement confortables."), ("Changer", "Si vous vous réveillez, variez ou levez-vous brièvement si cela aide."), ("Signaler", "Demandez un avis si la douleur nocturne est inhabituelle ou persistante.")], "Le but est une nuit gérable, pas une immobilité parfaite.", None),
    ("Prévention", "Préparer le prochain épisode", "Écrire le plan quand vous allez mieux", "Un plan simple réduit la panique lors d'une récidive. Conservez les contacts, les signes d'alerte et les premières actions qui vous ont aidé.", [("Archiver", "Gardez le résumé de cet épisode et les avis reçus."), ("Lister", "Notez les trois premières actions utiles."), ("Équiper", "Conservez les objets pratiques faciles à retrouver."), ("Partager", "Expliquez le plan à une personne de confiance.")], "Un épisode futur pourra être différent: recommencez toujours par la vérification de sécurité.", None),
    ("Confiance", "Apprivoiser la peur du mouvement", "Distinguer prudence et évitement durable", "Après une crise, certains gestes deviennent inquiétants avant même d'être essayés. La reprise peut se faire par étapes, avec une dose choisie et un droit à l'arrêt.", [("Nommer", "Écrivez le geste qui vous inquiète et pourquoi."), ("Réduire", "Créez une version plus courte, plus légère ou soutenue."), ("Tester", "Essayez dans un contexte sûr, sans chercher le maximum."), ("Répéter", "Gardez la même étape jusqu'à ce qu'elle soit plus prévisible.")], "Le courage n'est pas de forcer; c'est d'avancer avec des repères fiables.", None),
    ("Entourage", "Construire votre cercle d'aide", "Une personne, une mission, un délai", "Les demandes générales sont difficiles à entendre et à organiser. Une demande précise facilite l'aide et préserve la relation.", [("Urgence", "Choisissez la personne à appeler si la situation change."), ("Quotidien", "Attribuez une course, un trajet ou un repas."), ("Administratif", "Demandez une aide pour un appel ou un dossier."), ("Moral", "Identifiez la personne avec qui parler sans devoir vous justifier.")], "Écrivez les noms et numéros maintenant, pas au moment où tout devient difficile.", None),
    ("Carnet", "Votre tableau de bord sur sept jours", "Suivre capacités, dose et décision suivante", "Utilisez une ligne par jour. Notez une activité, sa dose, la réponse plus tard et l'ajustement choisi. Deux minutes suffisent.", [("Activité", "Exemple: marche, douche, trajet ou temps assis."), ("Dose", "Durée, distance ou nombre de séquences."), ("Réponse", "Plus facile, stable, plus difficile ou symptôme nouveau."), ("Suite", "Identique, réduire, augmenter un paramètre ou demander conseil.")], "Photographiez cette page pour la montrer lors d'une consultation ou garder votre repère.", None),
]


FICHES = [
    ("Sécurité", "Quand demander de l'aide", "Décider avant toute routine", ["Vérifiez difficulté à uriner ou fuites nouvelles.", "Repérez perte de sensibilité autour du périnée.", "Signalez faiblesse importante ou progressive.", "Après traumatisme important ou malaise, demandez un avis."], "En France, appelez le 15 ou le 112 en cas d'urgence. Cette fiche ne pose pas de diagnostic."),
    ("Crise", "Les trente premières minutes", "Sécuriser avant de bouger davantage", ["Dégagez le trajet et rapprochez le téléphone.", "Testez une position de répit pendant quelques minutes.", "Prévenez une personne si une tâche urgente reste à faire.", "Évitez les tests répétés et les gestes brusques."], "Une action courte et maîtrisée suffit pour commencer."),
    ("Repos", "Trouver une position de répit", "Chercher le confort sans posture obligatoire", ["Essayez le côté, le dos ou une assise soutenue.", "Utilisez un coussin seulement s'il améliore réellement le confort.", "Changez de position avant l'inconfort marqué.", "Préparez le prochain lever avant de vous reposer."], "Le repos est ponctuel; conservez de petits changements de position."),
    ("Lever", "Sortir du lit", "Utiliser les appuis et ralentir la séquence", ["Rapprochez-vous du bord par petits mouvements.", "Tournez le tronc et les jambes ensemble si cela vous convient.", "Poussez avec les bras pendant que les jambes descendent.", "Stabilisez-vous assis puis debout avant de marcher."], "Demandez une aide directe si vous vous sentez faible ou en danger de chute."),
    ("Habillage", "S'habiller", "Réduire flexions et équilibre inutile", ["Préparez les vêtements à portée de main.", "Asseyez-vous sur une chaise stable.", "Choisissez des vêtements et chaussures faciles à enfiler.", "Demandez une aide ponctuelle pour le geste risqué."], "Simplifier pendant quelques jours protège votre énergie."),
    ("Toilette", "Organiser la salle de bains", "Prévenir la glissade et la précipitation", ["Retirez tapis instable et objets au sol.", "Placez serviette et produits à portée.", "Utilisez uniquement un appui stable.", "Choisissez une toilette simplifiée si la douche est risquée."], "La sécurité compte davantage que la routine habituelle."),
    ("Repas", "Préparer à manger", "Limiter déplacements et charges", ["Rassemblez les ingrédients avant de commencer.", "Travaillez à hauteur confortable ou assis.", "Utilisez plusieurs petits contenants.", "Demandez les courses ou une livraison si besoin."], "Un repas simple et régulier est suffisant."),
    ("Maison", "Monter ou descendre un escalier", "Sécuriser chaque étape", ["Allumez la lumière et dégagez les marches.", "Gardez une main disponible pour la rampe.", "Évitez de porter une charge.", "Réduisez les allers-retours non indispensables."], "Si vous n'êtes pas stable, demandez de l'aide et reportez le trajet."),
    ("Sortie", "Sortir de chez soi", "Une mission simple et réversible", ["Choisissez un objectif unique et proche.", "Vérifiez téléphone, clés et chaussures stables.", "Préparez un trajet court et connu.", "Gardez une solution de retour ou d'annulation."], "Une sortie courte peut déjà être une réussite."),
    ("Voiture", "Entrer et sortir d'une voiture", "Préparer le siège et le pivot", ["Reculez le siège et ouvrez largement la portière.", "Asseyez d'abord le bassin.", "Faites entrer ou sortir les jambes progressivement.", "Prévoyez une pause avant de conduire."], "Ne conduisez pas si la douleur, la faiblesse ou un traitement altère votre sécurité."),
    ("Travail", "Bouger quand on travaille assis", "Varier plutôt que tenir une posture parfaite", ["Rapprochez clavier, écran et téléphone.", "Soutenez les pieds et utilisez le dossier sans vous rigidifier.", "Alternez assis, debout et quelques pas.", "Planifiez les tâches exigeantes au meilleur moment."], "La variation régulière compte plus qu'une posture idéale."),
    ("Travail", "Adapter une activité debout", "Réduire charge, portée et répétition", ["Gardez l'objet près du corps.", "Divisez une charge en plusieurs éléments.", "Alternez les tâches avant la fatigue marquée.", "Demandez un collègue pour le geste non adaptable."], "Modifiez un paramètre à la fois et réévaluez."),
    ("Quotidien", "Ménage et courses", "Protéger l'essentiel de la journée", ["Choisissez une seule priorité domestique.", "Utilisez un panier léger ou plusieurs sacs.", "Fractionnez le ménage par zones courtes.", "Déléguez ce qui implique charge ou position prolongée."], "Une maison moins parfaite pendant quelques jours est une adaptation, pas un échec."),
    ("Entourage", "Demander de l'aide", "Une personne, une mission, un délai", ["Décrivez la tâche précise qui pose problème.", "Dites quand l'aide est nécessaire.", "Proposez une alternative si la personne n'est pas disponible.", "Confirmez ce que vous pouvez encore faire seul."], "Exemple: peux-tu prendre les courses aujourd'hui avant 18 h?"),
    ("Consultation", "Préparer le rendez-vous", "Donner les informations utiles", ["Notez date, circonstances et évolution.", "Décrivez zone, irradiation et symptômes associés.", "Listez traitements, examens et allergies.", "Choisissez deux questions prioritaires."], "Commencez par ce que la douleur vous empêche de faire."),
    ("Nuit", "Préparer le sommeil", "Chercher le confort sans position unique", ["Dégagez le trajet jusqu'aux toilettes.", "Gardez téléphone et eau accessibles.", "Testez le coussin avant l'heure du coucher.", "Préparez la manière de vous relever."], "Une mauvaise nuit isolée ne signifie pas forcément une aggravation."),
    ("Matin", "Faire le point au réveil", "Regarder plusieurs repères", ["Vérifiez tout symptôme nouveau.", "Notez un geste plus facile, identique ou plus difficile.", "Tenez compte du sommeil et de l'activité d'hier.", "Choisissez la dose du matin sans rattrapage."], "Décidez avec l'ensemble de la situation, pas avec la première sensation."),
    ("Calme", "Respirer pendant un geste", "Garder un souffle fluide", ["Installez-vous dans une position soutenue.", "Laissez l'expiration durer tranquillement.", "Associez le souffle à un petit changement de position.", "Réduisez l'effort si vous bloquez votre respiration."], "Arrêtez si vous vous sentez étourdi ou mal."),
    ("Mobilité", "Tester un mouvement doux", "Explorer sans chercher le maximum", ["Choisissez une seule direction accessible.", "Gardez une amplitude petite et confortable.", "Faites quelques répétitions lentes.", "Observez la réponse pendant et plus tard."], "Un mouvement reste facultatif et doit pouvoir être interrompu facilement."),
    ("Progression", "Augmenter sans se précipiter", "Une seule variable à la fois", ["Répétez d'abord une dose bien tolérée.", "Choisissez durée, distance, charge ou fréquence.", "Faites une petite augmentation.", "Revenez à la dose précédente si la réponse devient trop forte."], "La stabilité est déjà un progrès utile."),
    ("Marche", "Utiliser une aide à la marche", "Faire régler et expliquer le matériel", ["Vérifiez embouts, hauteur et stabilité.", "Portez des chaussures stables.", "Dégagez le sol et l'itinéraire.", "Demandez la séquence de marche à un professionnel."], "Une première utilisation doit être expliquée; arrêtez si l'aide augmente le risque de chute."),
    ("Budget", "Réduire la charge administrative", "Une démarche utile à la fois", ["Regroupez ordonnances, factures et justificatifs.", "Demandez devis et prise en charge avant une dépense importante.", "Préparez une seule question par appel.", "Choisissez la personne qui peut vous aider."], "Conservez une trace écrite des réponses et des dates."),
    ("Travail", "Préparer une reprise", "Décrire les contraintes et l'adaptation", ["Listez les trois exigences principales du poste.", "Repérez les tâches temporairement adaptables.", "Formulez une demande précise et limitée dans le temps.", "Demandez un avis médical ou du travail si nécessaire."], "Une reprise est une organisation, pas seulement une date."),
    ("Bilan", "Faire le point de la semaine", "Choisir la prochaine décision", ["Comparez deux activités entre le début et aujourd'hui.", "Notez le réglage qui vous aide le plus.", "Classez l'évolution: mieux, stable ou moins bien.", "Décidez: continuer, ajuster ou demander conseil."], "Un bilan sert à décider, pas à juger vos efforts."),
]


def cover(c, total, kind):
    c.setFillColor(CREAM)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    photo = IMAGES / ("couverture-sos-lumbago.png" if kind == "guide" else "consultation-kine.png")
    draw_crop(c, photo, 0, H - 132 * mm, W, 132 * mm)
    c.setFillColor(PINE)
    c.roundRect(M, 24 * mm, W - 2 * M, 108 * mm, 6 * mm, fill=1, stroke=0)
    c.setFillColor(CORAL)
    c.setFont("RD Bold", 12)
    c.drawString(M + 9 * mm, 116 * mm, "GUIDE PRATIQUE ILLUSTRÉ" if kind == "guide" else "COLLECTION EXTRACTIBLE")
    c.setFillColor(white)
    if kind == "guide":
        paragraph(c, "SOS Lumbago", M + 9 * mm, 103 * mm, W - 2 * M - 18 * mm, "h1", white)
        paragraph(c, "Le protocole rassurant des sept premiers jours", M + 9 * mm, 88 * mm, W - 2 * M - 18 * mm, "h2", white)
        paragraph(c, "Comprendre, sécuriser et reprendre progressivement les gestes du quotidien.", M + 9 * mm, 70 * mm, W - 2 * M - 18 * mm, "body", white)
        label = "48 PAGES  -  ÉDITION FINALE"
    else:
        paragraph(c, "Fiches pratiques", M + 9 * mm, 103 * mm, W - 2 * M - 18 * mm, "h1", white)
        paragraph(c, "Le Réflexe Dos", M + 9 * mm, 88 * mm, W - 2 * M - 18 * mm, "h2", white)
        paragraph(c, "24 fiches autonomes à imprimer, détacher ou conserver sur téléphone.", M + 9 * mm, 70 * mm, W - 2 * M - 18 * mm, "body", white)
        label = "32 PAGES  -  24 FICHES"
    c.setFillColor(CORAL)
    c.roundRect(M + 9 * mm, 38 * mm, 76 * mm, 12 * mm, 6 * mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("RD Bold", 12)
    c.drawCentredString(M + 47 * mm, 42 * mm, label)
    c.setFont("RD Body", 12)
    c.drawRightString(W - M, 12 * mm, f"1 / {total}")
    c.showPage()


def guide_intro(c, page_no, total):
    page_header(c, page_no, total, "Bienvenue", "Vous accompagner sans vous infantiliser", "Un guide de décision, pas une promesse miracle")
    y = H - 53 * mm
    y = paragraph(c, "Quand le dos se bloque, les conseils contradictoires arrivent vite. Ce guide rassemble un chemin simple: vérifier la sécurité, retrouver une marge de confort, puis reprendre des activités adaptées.", M, y, W - 2 * M, "body")
    y -= 9 * mm
    for i, (t, b) in enumerate([
        ("Accessible", "Des phrases courtes, des actions concrètes et aucun langage culpabilisant."),
        ("Progressif", "Une seule étape à la fois, avec le droit de réduire ou de demander conseil."),
        ("Pratique", "Travail, sommeil, déplacements, famille, factures et consultation sont intégrés."),
        ("Prudent", "Les signes d'alerte et limites du guide restent visibles."),
    ], 1):
        card(c, M, y, W - 2 * M, 28 * mm, i, t, b, PALE_GREEN if i % 2 else white)
        y -= 32 * mm
    info_box(c, M, 24 * mm, W - 2 * M, 30 * mm, "Votre place", "Vous connaissez votre contexte. Utilisez ce support pour préparer vos décisions et vos échanges avec les professionnels, jamais pour remplacer un diagnostic.")
    c.showPage()


def guide_contents(c, page_no, total):
    page_header(c, page_no, total, "Sommaire", "Un parcours en quatre parties", "Accédez directement à la page utile")
    sections = [
        ("1. Sécurité et repères", "Pages 4 à 10", "Quand demander de l'aide, comprendre la crise et choisir une dose."),
        ("2. Protocole des sept jours", "Pages 11 à 41", "Gestes de base, mobilité, déplacements, travail et rendez-vous."),
        ("3. Nuit, confiance et prévention", "Pages 42 à 45", "Sommeil, récidive, peur du mouvement et entourage."),
        ("4. Outils et références", "Pages 46 à 48", "Tableau de bord, sources, validation et notes."),
    ]
    y = H - 56 * mm
    for i, (name, pages, desc) in enumerate(sections, 1):
        rounded(c, M, y - 39 * mm, W - 2 * M, 34 * mm, white if i % 2 == 0 else PALE_GREEN, radius=4 * mm)
        c.setFillColor(CORAL)
        c.setFont("RD Bold", 12)
        c.drawString(M + 7 * mm, y - 10 * mm, pages)
        c.setFillColor(PINE)
        c.setFont("RD Bold", 14)
        c.drawString(M + 45 * mm, y - 10 * mm, name)
        paragraph(c, esc(desc), M + 45 * mm, y - 17 * mm, W - 2 * M - 52 * mm, "small", INK)
        y -= 42 * mm
    info_box(c, M, 28 * mm, W - 2 * M, 35 * mm, "Lecture sur téléphone", "Enregistrez les pages 4, 5, 11, 33, 38 et 46. Elles regroupent la sécurité, le début de crise, la consultation, le bilan et le tableau de bord.")
    c.showPage()


def safety_page(c, page_no, total, urgent=True):
    if urgent:
        page_header(c, page_no, total, "Sécurité", "Les signes qui imposent d'agir", "Avant les exercices, les tâches et les déplacements")
        intro = "Appelez les urgences si vous présentez un trouble urinaire ou intestinal nouveau, une perte de sensibilité autour du périnée, une faiblesse importante ou progressive, ou un état général inquiétant."
        y = paragraph(c, intro, M, H - 53 * mm, W - 2 * M, "body") - 8 * mm
        items = [
            ("15 ou 112", "En France, en cas d'urgence ou de doute sur la gravité immédiate."),
            ("Ne restez pas seul", "Si vous vous sentez faible, confus ou en danger de chute."),
            ("Préparez", "Adresse, heure de début, symptômes, traitements et allergies."),
            ("N'utilisez pas ce guide", "Suspendre les exercices et suivre les consignes du service contacté."),
        ]
        for i, (t, b) in enumerate(items, 1):
            card(c, M, y, W - 2 * M, 29 * mm, i, t, b, PALE_CORAL if i in (1, 4) else white)
            y -= 33 * mm
        info_box(c, M, 23 * mm, W - 2 * M, 31 * mm, "Important", "Cette liste ne couvre pas toutes les situations. Une personne enceinte, immunodéprimée, atteinte d'un cancer, sous anticoagulant ou ayant subi un traumatisme important doit demander un avis adapté.")
    else:
        page_header(c, page_no, total, "Sécurité", "Quand demander un avis rapidement", "Une situation qui change mérite une réévaluation")
        y = H - 54 * mm
        paragraph(c, "Sans urgence évidente, contactez un professionnel si la douleur s'accompagne de fièvre ou d'altération générale, s'aggrave nettement, persiste au repos, apparaît après un traumatisme, ou s'associe à une faiblesse ou un engourdissement nouveau.", M, y, W - 2 * M, "body")
        y -= 28 * mm
        for i, (t, b) in enumerate([
            ("Avant l'appel", "Notez le début, la zone, les symptômes associés et ce qui a changé."),
            ("Pendant l'attente", "Évitez un déplacement risqué et gardez téléphone et traitements à portée."),
            ("Pendant l'échange", "Dites d'abord le symptôme qui vous inquiète et votre niveau d'autonomie."),
            ("Après l'avis", "Reformulez les consignes, le délai et les motifs de reconsultation."),
        ], 1):
            card(c, M, y, W - 2 * M, 29 * mm, i, t, b, PALE_GREEN if i % 2 else white)
            y -= 33 * mm
        info_box(c, M, 24 * mm, W - 2 * M, 30 * mm, "Votre décision", "Si votre intuition vous dit que la situation est inhabituelle ou que vous ne pouvez pas assurer votre sécurité, demandez conseil. Vous n'avez pas à attendre d'être certain.")
    c.showPage()


def guide_content_page(c, page_no, total, item):
    section, title, subtitle, intro, actions, takeaway, photo_key = item
    page_header(c, page_no, total, section, title, subtitle)
    y = H - 53 * mm
    y = paragraph(c, esc(intro), M, y, W - 2 * M, "body") - 7 * mm
    if photo_key:
        draw_crop(c, PHOTOS[photo_key], M, y - 48 * mm, W - 2 * M, 44 * mm, radius=4 * mm)
        y -= 54 * mm
    else:
        info_box(c, M, y - 34 * mm, W - 2 * M, 31 * mm, "Ce que l'on cherche", takeaway, PALE_GREEN)
        y -= 40 * mm
    gap = 7 * mm
    cw = (W - 2 * M - gap) / 2
    ch = 41 * mm
    for idx, (name, body) in enumerate(actions):
        row, col = divmod(idx, 2)
        x = M + col * (cw + gap)
        yt = y - row * (ch + 6 * mm)
        card(c, x, yt, cw, ch, idx + 1, name, body, PALE_GREEN if (idx + page_no) % 2 else white)
    if photo_key:
        info_box(c, M, 24 * mm, W - 2 * M, 31 * mm, "À retenir", takeaway, PALE_CORAL)
    else:
        info_box(c, M, 24 * mm, W - 2 * M, 31 * mm, "Ma prochaine action", "Écrivez une action assez petite pour être faite aujourd'hui, puis indiquez quand vous réévaluerez sa réponse.", PALE_CORAL)
    c.showPage()


def sources_page(c, page_no, total, product):
    page_header(c, page_no, total, "Sources", "Repères institutionnels et validation", "Une édition traçable et révisable")
    refs = [
        ("Haute Autorité de santé", "Prise en charge du patient présentant une lombalgie commune", "has-sante.fr"),
        ("Assurance Maladie", "Lombalgie ou mal de dos: messages patients", "ameli.fr"),
        ("Assurance Maladie", "Lombalgie aiguë: traitement et prévention", "ameli.fr"),
        ("Organisation mondiale de la Santé", "Guideline for non-surgical management of chronic primary low back pain", "who.int"),
    ]
    y = H - 55 * mm
    for org, title, url in refs:
        rounded(c, M, y - 29 * mm, W - 2 * M, 26 * mm, white, radius=4 * mm)
        c.setFillColor(PINE)
        c.setFont("RD Bold", 12.5)
        c.drawString(M + 6 * mm, y - 9 * mm, org)
        paragraph(c, esc(title), M + 6 * mm, y - 14 * mm, W - 2 * M - 12 * mm, "small", INK)
        c.setFillColor(GREY)
        c.setFont("RD Body", 12)
        c.drawRightString(W - M - 6 * mm, y - 22 * mm, url)
        y -= 33 * mm
    info_box(c, M, 38 * mm, W - 2 * M, 48 * mm, "Avant commercialisation", "Le contenu et les illustrations de mouvement doivent être relus par un médecin ou un kinésithérapeute. Ajouter ensuite le nom du relecteur, sa qualité, la date de validation et la prochaine date de révision. Ce support informe et accompagne; il ne remplace ni diagnostic ni consultation.", PALE_CORAL)
    c.setFillColor(GREY)
    c.setFont("RD Body", 12)
    c.drawString(M, 26 * mm, f"Produit: {product}")
    c.drawString(M, 20 * mm, "Sources consultées le 4 octobre 2026")
    c.showPage()


def final_page(c, page_no, total, kind):
    page_header(c, page_no, total, "Fin du support", "Votre prochain pas peut rester simple", "Conserver les repères utiles et demander conseil en cas de changement")
    draw_crop(c, IMAGES / "consultation-kine.png", M, H - 126 * mm, W - 2 * M, 66 * mm, radius=5 * mm)
    y = H - 136 * mm
    paragraph(c, "Vous venez de construire un plan plus clair. Gardez les pages de sécurité, le résumé de votre évolution et les coordonnées de vos personnes ressources. Utilisez-les lors d'un prochain rendez-vous ou épisode.", M, y, W - 2 * M, "body")
    info_box(c, M, 74 * mm, W - 2 * M, 39 * mm, "Validation professionnelle", "Nom et qualité du relecteur: ____________________  -  Date de validation: ______________  -  Prochaine révision: ______________", PALE_GREEN)
    info_box(c, M, 26 * mm, W - 2 * M, 38 * mm, "Mentions", "© 2026 Le Réflexe Dos. Usage personnel. Reproduction ou diffusion commerciale interdite sans autorisation. Version 1.0 - édition finale de travail.", PALE_CORAL)
    c.showPage()


def build_guide():
    path = OUT / "SOS-Lumbago-guide-illustre-edition-finale-48-pages.pdf"
    c = AccessibleCanvas(str(path), pagesize=A4, pageCompression=1)
    c.setTitle("SOS Lumbago - Guide illustré - édition finale 48 pages")
    c.setAuthor("Le Réflexe Dos")
    total = 48
    cover(c, total, "guide")
    guide_intro(c, 2, total)
    guide_contents(c, 3, total)
    safety_page(c, 4, total, True)
    safety_page(c, 5, total, False)
    assert len(GUIDE_PAGES) == 41
    for page_no, item in enumerate(GUIDE_PAGES, 6):
        guide_content_page(c, page_no, total, item)
    sources_page(c, 47, total, "SOS Lumbago - guide illustré 48 pages")
    final_page(c, 48, total, "guide")
    c.save()
    assert len(PdfReader(str(path)).pages) == total
    return path


def sheets_mode(c, page_no, total):
    page_header(c, page_no, total, "Mode d'emploi", "Une fiche pour une décision", "Imprimer, détacher ou enregistrer la page utile")
    y = H - 55 * mm
    for i, (t, b) in enumerate([
        ("Commencez par la sécurité", "La fiche 01 reste prioritaire si la situation change."),
        ("Choisissez un seul besoin", "Prenez la fiche correspondant à la prochaine décision concrète."),
        ("Personnalisez", "Cochez, écrivez un nom et photographiez la page complétée."),
        ("Réévaluez", "Si un symptôme nouveau apparaît, revenez à la sécurité et demandez conseil."),
    ], 1):
        card(c, M, y, W - 2 * M, 30 * mm, i, t, b, PALE_GREEN if i % 2 else white)
        y -= 35 * mm
    info_box(c, M, 29 * mm, W - 2 * M, 40 * mm, "Format mobile", "Chaque fiche tient sur une page autonome. Enregistrez les fiches 01, 02, 15, 21 et 24 dans vos favoris: urgence, début de crise, consultation, aide à la marche et bilan.")
    c.showPage()


def sheets_index(c, page_no, total):
    page_header(c, page_no, total, "Index", "Vingt-quatre fiches autonomes", "Pages 4 à 27")
    cols = [FICHES[:12], FICHES[12:]]
    for col, entries in enumerate(cols):
        x = M + col * (82 * mm + 10 * mm)
        y = H - 57 * mm
        for offset, (_, title, _, _, _) in enumerate(entries):
            num = offset + 1 + col * 12
            rounded(c, x, y - 14 * mm, 82 * mm, 11 * mm, white if num % 2 else PALE_GREEN, radius=2.5 * mm)
            c.setFillColor(CORAL)
            c.setFont("RD Bold", 12)
            c.drawString(x + 4 * mm, y - 9 * mm, f"{num:02d}")
            c.setFillColor(PINE)
            c.setFont("RD Bold", 12)
            c.drawString(x + 16 * mm, y - 9 * mm, title[:31])
            y -= 15 * mm
    info_box(c, M, 24 * mm, W - 2 * M, 32 * mm, "Repérage rapide", "Crise: 01 à 04  -  Quotidien: 05 à 10  -  Travail et entourage: 11 à 15  -  Nuit et mouvement: 16 à 21  -  Organisation et bilan: 22 à 24")
    c.showPage()


def fiche_page(c, page_no, total, fiche_no, data):
    section, title, subtitle, actions, caution = data
    page_header(c, page_no, total, f"Fiche {fiche_no:02d} - {section}", title, subtitle)
    y = H - 55 * mm
    for i, action in enumerate(actions, 1):
        card(c, M, y, W - 2 * M, 29 * mm, i, ["Vérifier", "Préparer", "Agir", "Observer"][i - 1], action, PALE_GREEN if i % 2 else white)
        y -= 34 * mm
    info_box(c, M, 73 * mm, W - 2 * M, 38 * mm, "Point de vigilance", caution, PALE_CORAL)
    rounded(c, M, 25 * mm, W - 2 * M, 38 * mm, white, radius=4 * mm, stroke=LIGHT_GREY)
    c.setFillColor(PINE)
    c.setFont("RD Bold", 12)
    c.drawString(M + 6 * mm, 53 * mm, "Ma prochaine action")
    c.setStrokeColor(LIGHT_GREY)
    c.line(M + 6 * mm, 45 * mm, W - M - 6 * mm, 45 * mm)
    c.line(M + 6 * mm, 36 * mm, W - M - 6 * mm, 36 * mm)
    c.showPage()


def memo_cards(c, page_no, total):
    page_header(c, page_no, total, "Aide-mémoire", "Trois cartes à garder près de vous", "Découpez ou photographiez")
    entries = [
        (CORAL, "MAINTENANT", ["Je vérifie la sécurité", "Je choisis une position de répit", "Je préviens quelqu'un si besoin"]),
        (PINE_2, "PENDANT", ["Je garde un souffle fluide", "Je réduis la durée si nécessaire", "Je ne me teste pas"]),
        (GREEN, "APRÈS", ["Je note une capacité", "Je garde le réglage utile", "Je demande conseil en cas de doute"]),
    ]
    y = H - 60 * mm
    for color, label, lines in entries:
        rounded(c, M, y - 51 * mm, W - 2 * M, 46 * mm, white, radius=4 * mm, stroke=GREY)
        rounded(c, M + 6 * mm, y - 44 * mm, 40 * mm, 34 * mm, color, radius=4 * mm)
        c.setFillColor(white)
        c.setFont("RD Bold", 12)
        c.drawCentredString(M + 26 * mm, y - 29 * mm, label)
        paragraph(c, "<br/>".join([f"- {esc(v)}" for v in lines]), M + 54 * mm, y - 13 * mm, W - 2 * M - 62 * mm, "body")
        y -= 57 * mm
    c.showPage()


def weekly_tracker(c, page_no, total):
    page_header(c, page_no, total, "Suivi", "Une semaine en un coup d'oeil", "Capacité, dose, réponse, décision")
    y = H - 56 * mm
    headers = ["Jour", "Activité", "Dose", "Réponse", "Suite"]
    widths = [18, 47, 34, 43, 34]
    x = M
    for header, width in zip(headers, widths):
        rounded(c, x, y - 13 * mm, width * mm, 11 * mm, PINE, radius=1.5 * mm)
        c.setFillColor(white)
        c.setFont("RD Bold", 12)
        c.drawCentredString(x + width * mm / 2, y - 9 * mm, header)
        x += width * mm + 1 * mm
    y -= 16 * mm
    for day in range(1, 8):
        x = M
        for col, width in enumerate(widths):
            rounded(c, x, y - 22 * mm, width * mm, 20 * mm, white if day % 2 else PALE_GREEN, radius=1.5 * mm, stroke=LIGHT_GREY)
            if col == 0:
                c.setFillColor(PINE)
                c.setFont("RD Bold", 12)
                c.drawCentredString(x + width * mm / 2, y - 13 * mm, f"J{day}")
            x += width * mm + 1 * mm
        y -= 24 * mm
    info_box(c, M, 21 * mm, W - 2 * M, 32 * mm, "Règle de lecture", "Cherchez une tendance globale. Une journée plus difficile n'annule pas les capacités retrouvées. Si un symptôme nouveau apparaît, revenez à la fiche 01.")
    c.showPage()


def contacts_page(c, page_no, total):
    page_header(c, page_no, total, "Contacts", "Les personnes que je peux appeler", "Écrire avant d'en avoir besoin")
    fields = ["Urgence ou service à contacter", "Médecin traitant", "Kinésithérapeute", "Pharmacien", "Personne de confiance", "Aide pour les courses ou trajets"]
    y = H - 58 * mm
    for label in fields:
        rounded(c, M, y - 26 * mm, W - 2 * M, 23 * mm, white, radius=3 * mm, stroke=LIGHT_GREY)
        c.setFillColor(PINE)
        c.setFont("RD Bold", 12)
        c.drawString(M + 6 * mm, y - 9 * mm, label)
        c.setStrokeColor(LIGHT_GREY)
        c.line(M + 6 * mm, y - 18 * mm, W - M - 6 * mm, y - 18 * mm)
        y -= 29 * mm
    info_box(c, M, 22 * mm, W - 2 * M, 31 * mm, "À photographier", "Complétez cette page, puis conservez-la dans vos favoris avec la fiche 01. Ajoutez votre adresse exacte et la liste de vos traitements dans une note sécurisée.")
    c.showPage()


def print_page(c, page_no, total):
    page_header(c, page_no, total, "Utilisation", "Imprimer, classer et partager", "Faire vivre la collection")
    y = H - 56 * mm
    for i, (t, b) in enumerate([
        ("Impression", "Utilisez le format A4 à 100 %. Les fiches sont conçues avec des marges compatibles avec une perforation simple."),
        ("Classement", "Rangez la fiche sécurité en premier, puis les fiches correspondant à votre quotidien."),
        ("Téléphone", "Photographiez seulement les pages complétées et ajoutez-les aux favoris."),
        ("Partage", "Montrez les observations utiles au professionnel; elles ne remplacent pas son évaluation."),
    ], 1):
        card(c, M, y, W - 2 * M, 31 * mm, i, t, b, PALE_GREEN if i % 2 else white)
        y -= 36 * mm
    info_box(c, M, 35 * mm, W - 2 * M, 42 * mm, "Version", "© 2026 Le Réflexe Dos. Version 1.0 - édition finale de travail, 32 pages. Usage personnel. Validation par un médecin ou un kinésithérapeute requise avant commercialisation.", PALE_CORAL)
    c.showPage()


def build_sheets():
    path = OUT / "Fiches-pratiques-Le-Reflexe-Dos-edition-finale-32-pages.pdf"
    c = AccessibleCanvas(str(path), pagesize=A4, pageCompression=1)
    c.setTitle("Fiches pratiques Le Réflexe Dos - édition finale 32 pages")
    c.setAuthor("Le Réflexe Dos")
    total = 32
    cover(c, total, "sheets")
    sheets_mode(c, 2, total)
    sheets_index(c, 3, total)
    assert len(FICHES) == 24
    for fiche_no, data in enumerate(FICHES, 1):
        fiche_page(c, fiche_no + 3, total, fiche_no, data)
    memo_cards(c, 28, total)
    weekly_tracker(c, 29, total)
    contacts_page(c, 30, total)
    sources_page(c, 31, total, "Collection de 24 fiches pratiques")
    print_page(c, 32, total)
    c.save()
    assert len(PdfReader(str(path)).pages) == total
    return path


if __name__ == "__main__":
    print(build_guide())
    print(build_sheets())
