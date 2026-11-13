#!/usr/bin/env python3
"""Construit le livret imprimable du « Voleur de diamants » à partir de source/texte.md.

Même chaîne que les autres livres de l'atelier (pages de 124 × 186 mm, renvois avec le numéro de page,
imposition sur A4), avec la mise en forme du site de Nina : titres en Fraunces, texte en Literata,
violet des campanules, rose des diamants du chat. Chaque chapitre s'ouvre sur son image au format 3:2,
le numéro posé à cheval sur son bord bas ; les tirages sont dans un encart rose pâle.

Produit trois PDF dans le dossier Impression du livre :
- LeVoleurDeDiamants_Livret_lecture.pdf : les pages dans l'ordre de lecture ;
- LeVoleurDeDiamants_Livret_A4_bord_court.pdf et _bord_long.pdf : les pages imposées deux par deux sur
  A4 paysage, avec lignes de coupe et de pliure, pour une impression recto verso pliée en cahier.

Nécessite Google Chrome, pdftotext (poppler) et le module Python pypdf.
Usage, depuis la racine du dépôt : python3 source/construire_livret.py
"""
import html
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image
from pypdf import PageObject, PdfReader, PdfWriter, Transformation

sys.path.insert(0, str(Path(__file__).resolve().parent))
from construire_site import (AUTRICE, CAMPANULE, CHOIX, CITATION, CONTEXTE, RENVOI, SYNOPSIS, TITRE,  # noqa: E402
                             illustration, lire_chapitres)

RACINE = Path(__file__).resolve().parent.parent
IMPRESSION = RACINE.parent / "Impression"
NOM = "LeVoleurDeDiamants"

MM = 72 / 25.4
LARGEUR_PAGE, HAUTEUR_PAGE = 124, 186          # mm
A4_L, A4_H = 297 * MM, 210 * MM                  # A4 paysage, en points
ENCRE, DOUCE, VIOLET, VIOLET_FONCE, ROSE, ROSE_FONCE = "#1c2d24", "#4b5d52", "#2e6c66", "#1e4d48", "#d4664c", "#ad4a33"


def police(nom, fichier, italique=False):
    return (f'@font-face {{ font-family: "{nom}"; font-weight: 300 900; {"font-style: italic; " if italique else ""}'
            f'src: url("{(RACINE / "fonts" / fichier).as_uri()}"); }}')


CSS = "\n".join([police("Fraunces", "Fraunces.woff2"), police("Fraunces", "Fraunces-i.woff2", True),
                 police("Literata", "Literata.woff2"), police("Literata", "Literata-i.woff2", True)]) + f"""
@page {{
  size: {LARGEUR_PAGE}mm {HAUTEUR_PAGE}mm;
  margin: 12mm 12mm 15mm 12mm;
  @bottom-center {{ content: counter(page); font-family: "Fraunces"; font-size: 9pt; color: {DOUCE}; }}
}}
@page sans-numero {{ @bottom-center {{ content: none; }} }}

* {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; box-sizing: border-box; }}
html {{ font-family: "Literata", serif; font-size: 11pt; line-height: 1.45; color: {ENCRE}; }}
body {{ margin: 0; }}
p {{ margin: 0 0 0.55em; orphans: 2; widows: 2; }}
.page-seule {{ break-before: page; }}
.sans-numero {{ page: sans-numero; }}
.marque {{ font-size: 1pt; color: #ffffff; }}
h1, h2, .titre-livre, .consigne, .fin, .elan {{ font-family: "Fraunces", serif; font-variation-settings: "SOFT" 100; }}

/* Couverture : l'image en hauteur telle qu'elle a été pensée, le titre posé dans son blanc du haut */
@page couverture {{ margin: 0; @bottom-center {{ content: none; }} }}
.couverture {{ page: couverture; position: relative; height: 185.5mm; overflow: hidden; background: #fff; }}
.couverture img {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: contain; }}
.couverture .voile {{ position: absolute; left: 0; right: 0; top: 0; height: 75mm;
  background: linear-gradient(to bottom, rgba(16,26,38,0.72), rgba(16,26,38,0)); }}
.couverture .entete {{ position: absolute; top: 13mm; left: 0; right: 0; text-align: center; padding: 0 8mm; }}
.couverture .surtitre {{ font-family: "Fraunces"; font-weight: 600; font-size: 7.5pt; letter-spacing: 1.8pt;
  text-transform: uppercase; color: #f2b39f; text-shadow: 0 0 2mm rgba(0,0,0,0.6); }}
.couverture .titre-livre {{ font-weight: 600; font-size: 31pt; line-height: 1; color: #fff7ec; margin: 2mm 0 1.5mm;
  font-variation-settings: "SOFT" 100, "opsz" 144; text-shadow: 0 0 4mm rgba(0,0,0,0.6); }}
.couverture .autrice {{ font-family: "Fraunces"; font-style: italic; font-size: 13pt; color: #f6e6d4;
  text-shadow: 0 0 3mm rgba(0,0,0,0.7); }}

/* Quatrième de couverture du résumé, en page 2 */
.resume {{ display: flex; flex-direction: column; justify-content: center; height: 155mm; text-align: center; }}
.resume p {{ font-size: 10.5pt; line-height: 1.55; }}

/* Chapitres : l'image entière, jamais recadrée, fondue sur ses bords, le numéro à cheval sur son bord bas */
.illus {{ position: relative; margin: 0 0 7mm; }}
.illus img {{ display: block; width: 100%; height: auto; margin: 0 auto;
  filter: saturate(0.8) brightness(1.03);
  -webkit-mask-image: linear-gradient(to right, transparent 0, #000 4%, #000 96%, transparent 100%),
                      linear-gradient(to bottom, transparent 0, #000 4%, #000 92%, transparent 100%);
  -webkit-mask-composite: source-in; }}
/* Chapitres resserrés : seule l'image rapetisse, le texte reste à 11 pt */
.serre .illus {{ width: 82%; margin-left: auto; margin-right: auto; }}
.serre2 .illus {{ width: 50%; }}
/* Dernier cran : interligne un peu plus serré, le corps reste à 11 pt minimum */
.serre2 {{ line-height: 1.32; }}
.serre2 p {{ margin-bottom: 0.45em; }}
.illus.seconde {{ margin: 4mm 0 2mm; break-inside: avoid; }}
.illus img.portrait {{ width: 100%; }}
/* Image en hauteur : en pleine page, sans marge, avant le texte du chapitre ; le numéro à cheval sur son bas */
@page pleine {{ margin: 0; @bottom-center {{ content: none; }} }}
.pleine-page {{ page: pleine; position: relative; height: 185.5mm; overflow: hidden; break-before: page; }}
.pleine-page img {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: contain; filter: saturate(0.8) brightness(1.03); }}
.pleine-page .pastille {{ bottom: 8mm; transform: translate(-50%, 0); }}
.apres-pleine {{ break-before: page; }}
/* Une page qui commence par un titre, sans image, garde un grand blanc en haut */
.ouvre-titre::before {{ content: ""; display: block; height: 20mm; }}
.numero-chap {{ display: block; text-align: center; font-family: "Fraunces"; font-weight: 600; font-size: 7.5pt;
  letter-spacing: 1.6pt; text-transform: uppercase; color: {ROSE}; margin: 2mm 0 2mm; }}
.pastille {{ position: absolute; left: 50%; bottom: 0; transform: translate(-50%, 50%); background: #fff;
  border-radius: 10mm; padding: 1mm 3.5mm 0.8mm; font-family: "Fraunces"; font-weight: 600; font-size: 7.5pt;
  letter-spacing: 1.4pt; text-transform: uppercase; color: {ROSE}; box-shadow: 0 0.8mm 2.5mm rgba(173, 74, 51, 0.25); }}
h1 {{ font-weight: 500; font-size: 18pt; line-height: 1.1; text-align: center; color: {ENCRE}; margin: 0 0 4mm; }}

/* Séparateur, renvois, tirages, fin */
.separateur {{ display: flex; align-items: center; justify-content: center; gap: 2.5mm; margin: 3mm 0 3mm; break-after: avoid; }}
.separateur::before, .separateur::after {{ content: ""; width: 16mm; height: 0.25mm; background: linear-gradient(to right, transparent, {VIOLET}); }}
.separateur::after {{ background: linear-gradient(to left, transparent, {VIOLET}); }}
.separateur img {{ width: 6mm; }}
.suite {{ break-inside: avoid; break-before: avoid; }}
.elan {{ text-align: center; font-style: italic; font-weight: 500; font-size: 11.5pt; color: {VIOLET_FONCE}; }}
.elan::after {{ content: " →"; color: {ROSE}; }}
.de {{ margin-top: 4mm; padding: 3mm 4mm 2.5mm; border-radius: 4mm; background: #eef5f2;
  box-shadow: 0 1.5mm 4mm -1.5mm rgba(30, 77, 72, 0.35); font-size: 9.8pt; line-height: 1.38; }}
.consigne {{ font-style: italic; font-size: 10.5pt; color: {VIOLET_FONCE}; margin: 0 0 1.5mm; }}
.tirage {{ display: grid; grid-template-columns: 14mm 1fr; gap: 2mm; margin: 0 0 1.5mm; }}
.tirage b {{ align-self: start; text-align: center; background: #fff; border-radius: 10mm; padding: 0.2mm 0;
  font-family: "Fraunces"; font-weight: 600; font-size: 8.5pt; color: {ROSE_FONCE}; }}
.tirage .renvoi {{ display: block; font-family: "Fraunces"; font-style: italic; font-weight: 500; color: {VIOLET_FONCE}; }}
.fin {{ text-align: center; font-style: italic; font-size: 26pt; color: {VIOLET_FONCE}; margin-top: 1mm; }}

/* Pages de contexte, de l'arbre et dos */
.contexte h2 {{ font-weight: 500; font-size: 16pt; text-align: center; color: {ENCRE}; margin: 0 0 4mm; }}
.contexte p {{ font-size: 9.6pt; line-height: 1.4; }}
.dessins {{ display: flex; justify-content: space-between; align-items: flex-end; margin: 0 0 4mm; }}
.dessins figure {{ margin: 0; text-align: center; }}
.dessins img {{ display: block; height: 13mm; margin: 0 auto; }}
.dessins figcaption {{ font-family: "Fraunces"; font-style: italic; font-size: 6.5pt; color: {VIOLET_FONCE}; margin-top: 0.8mm; }}
.citation {{ font-family: "Fraunces"; font-style: italic; font-size: 12pt; line-height: 1.3; text-align: center;
  color: {VIOLET_FONCE}; margin: 3mm 4mm 4mm; }}
.contexte .credits {{ font-size: 8.8pt; color: {DOUCE}; }}
.fiches {{ display: grid; grid-template-columns: 1fr 1fr; gap: 3mm; }}
.fiches img {{ width: 100%; display: block; }}
.fiches .pleine {{ grid-column: 1 / -1; }}
@page arbre {{ margin: 8mm 6mm 9mm; @bottom-center {{ content: none; }} }}
.arbre {{ page: arbre; height: 168mm; display: flex; flex-direction: column; align-items: center; }}
.arbre img {{ flex: 1; min-height: 0; width: 100%; object-fit: contain; }}
.dos {{ display: flex; flex-direction: column; justify-content: flex-end; height: 156mm; text-align: center;
  font-size: 9pt; color: {DOUCE}; }}
"""

SEPARATEUR = f'<div class="separateur"><img src="{CAMPANULE}" alt=""></div>'


def e(texte):
    return html.escape(texte, quote=False)


def cle_de(nom):
    """Clé numérique de chaque partie : 0 et 100 pour les deux textes d'ouverture, le numéro pour un chapitre"""
    if nom.startswith("Prologue"):
        return 0 if nom.endswith(" I") else 100
    return int(nom.split()[-1])


def renvoi(cible, pages):
    return f"Poursuis au chapitre {cible}, page {pages.get(cible, '00')}"


def chapitre(ch, suivant, pages):
    cle = cle_de(ch["nom"])
    classe = "page-seule" + (" serre" if cle in SERRES else "") + (" serre2" if cle in SERRES2 else "")
    morceaux = []
    image = RACINE / "images" / "chapitres" / f"{illustration(ch['nom'])}.jpg"
    haut = image.exists() and Image.open(image).height > Image.open(image).width
    pastille = "" if ch["nom"].startswith("Prologue") else f'<span class="pastille">{e(ch["numero"])}</span>'
    if haut:
        # L'image en hauteur occupe toute une page ; le chapitre commence là (c'est la page des renvois)
        morceaux.append(f'<section class="pleine-page"><span class="marque">@@CH{cle}@@</span>'
                        f'<img src="{image.as_uri()}" alt=""></section>')
        morceaux.append(f'<section class="apres-pleine ouvre-titre{classe.replace("page-seule", "")}">')
    else:
        sans = "" if image.exists() else " ouvre-titre"
        morceaux.append(f'<section class="{classe}{sans}"><span class="marque">@@CH{cle}@@</span>')
        if image.exists():
            morceaux.append(f'<div class="illus"><img src="{image.as_uri()}" alt="">{pastille}</div>')
    if haut and pastille:
        # Après une image en pleine page, le numéro revient au-dessus du titre, comme un chapitre sans image
        morceaux.append(f'<span class="numero-chap">{e(ch["numero"])}</span>')
    morceaux.append(f'<h1>{e(ch["titre"])}</h1>')

    corps, consigne, tirages, cibles, fin = [], None, [], [], False
    for p in ch["paragraphes"]:
        if p.startswith("- "):
            for ligne in p.split("\n"):
                ligne = ligne[2:].strip()
                m = CHOIX.match(ligne)
                if m:
                    texte = m[2].rstrip(" .")
                    tirages.append((m[1], texte[0].upper() + texte[1:] + "." if texte else "", int(m[3])))
                else:
                    cibles.append(int(RENVOI.match(ligne)[1]))
        elif p == "FIN":
            fin = True
        elif p.startswith("**") and p.endswith("**"):
            consigne = p[2:-2]
        else:
            corps.append(f"<p>{e(p)}</p>")
    morceaux += corps
    # Deuxième image du chapitre, comme sur le site : à la fin du texte, avant les choix
    seconde = RACINE / "images" / "chapitres" / f"{illustration(ch['nom'])}b.jpg"
    if seconde.exists():
        haut = Image.open(seconde).height > Image.open(seconde).width
        morceaux.append(f'<div class="illus seconde"><img class="{"portrait" if haut else ""}" src="{seconde.as_uri()}" alt=""></div>')

    suite = []
    if consigne:
        suite.append(f'<div class="de"><p class="consigne">{e(consigne)}</p>' + "".join(
            f'<div class="tirage"><b>{e(n)}</b><span>{e(t)}<span class="renvoi">{e(renvoi(c, pages))}</span></span></div>'
            for n, t, c in tirages) + "</div>")
    # Dans un livre, inutile d'écrire « Poursuis au chapitre suivant » : on tourne simplement la page
    elif cibles and not (suivant is not None and cibles[0] == suivant):
        suite += [SEPARATEUR, f'<p class="elan">{e(renvoi(cibles[0], pages))}</p>']
    if fin:
        suite += [SEPARATEUR, '<div class="fin">Fin</div>']
    if suite:
        morceaux.append(f'<div class="suite">{"".join(suite)}</div>')
    morceaux.append("</section>")
    return "".join(morceaux)


def dessin(fichier, nom):
    return (f'<figure><img src="{(RACINE / "images" / "dessins" / fichier).as_uri()}" alt="">'
            f'<figcaption>{e(nom)}</figcaption></figure>')


def document(pages, blanches=0):
    couverture = (
        '<section class="couverture sans-numero">'
        f'<img src="{(RACINE / "images/couverture.png").as_uri()}" alt=""><div class="voile"></div>'
        '<div class="entete"><div class="surtitre">Une histoire dont le lecteur est le héros</div>'
        f'<div class="titre-livre">{e(TITRE)}</div><div class="autrice">{e(AUTRICE)}</div></div></section>'
        '<section class="page-seule sans-numero"><div class="resume">'
        + "".join(f"<p>{e(p)}</p>" for p in SYNOPSIS.split("\n\n")) + SEPARATEUR + "</div></section>"
    )
    chapitres_lus = lire_chapitres()
    cles = [cle_de(ch["nom"]) for ch in chapitres_lus]
    chapitres = "".join(chapitre(ch, cles[i + 1] if i + 1 < len(cles) else None, pages)
                        for i, ch in enumerate(chapitres_lus))

    paragraphes = [q for p in CONTEXTE for q in p.split("\n\n")]
    def para(p):
        return f"<p>{e(p).replace('&lt;b&gt;', '<b>').replace('&lt;/b&gt;', '</b>')}</p>"
    fiches = RACINE / "images" / "fiches"
    contexte = (
        '<section class="page-seule contexte"><div class="dessins">'
        + dessin("lapinette.png", "Lapinette") + dessin("chat-noir.png", "Le chat noir") + dessin("foret.png", "La forêt")
        + dessin("pivert.png", "Le pivert") + dessin("chat-blanc.png", "Le chat blanc") + dessin("renard.png", "Le renard blanc")
        + '</div><h2>Comment est née cette histoire</h2>'
        + "".join(para(p) for p in paragraphes[:4])
        + f'<p class="citation">« {e(CITATION)} »</p>'
        + "".join(para(p) for p in paragraphes[4:])
        + f'<p class="credits">Une histoire librement inspirée du récit de {e(AUTRICE)}.<br>Réalisation du livre : '
          "Laboratoire d’Aix-périmentation et de Bidouille.</p></section>"
        '<section class="page-seule contexte"><h2>Les fiches de l’atelier</h2><div class="fiches">'
        f'<img src="{(fiches / "fiche_recit.jpg").as_uri()}" alt="">'
        f'<img src="{(fiches / "fiche_personnage_lapinette.jpg").as_uri()}" alt="">'
        f'<img class="pleine" src="{(fiches / "fiche_situation_1.jpg").as_uri()}" alt="">'
        "</div></section>"
    )
    arbre = ('<section class="page-seule contexte arbre sans-numero"><h2>L’arbre de l’histoire</h2>'
             f'<img src="{(RACINE / "images/arbre.svg").as_uri()}" alt=""></section>')
    vides = '<section class="page-seule sans-numero">&nbsp;</section>' * blanches
    dos = ('<section class="page-seule sans-numero"><div class="dos">'
           f"<p><b>{e(TITRE)}</b>, une histoire librement inspirée du récit imaginé par {e(AUTRICE)} pendant l’atelier "
           "« La quête du curry, une histoire dont tu es le héros », à la bibliothèque des Deux Ormes "
           "(bibliothèques Méjanes, Aix-en-Provence), en octobre 2026.</p><p>Réalisation du livre : Laboratoire d’Aix-périmentation et de Bidouille.</p>"
           "</div></section>")
    return (f'<!doctype html><html lang="fr"><head><meta charset="utf-8"><style>{CSS}</style></head>'
            f"<body>{couverture}{chapitres}{arbre}{contexte}{vides}{dos}</body></html>")


def imprimer(source_html, pdf):
    subprocess.run(["google-chrome", "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--virtual-time-budget=8000", f"--print-to-pdf={pdf}", source_html.as_uri()],
                   check=True, capture_output=True)


def reperer_pages(pdf):
    """Numéro de page où commence chaque partie, d'après les marques invisibles."""
    pages = {}
    total = len(PdfReader(str(pdf)).pages)
    for n in range(1, total + 1):
        texte = subprocess.run(["pdftotext", "-f", str(n), "-l", str(n), str(pdf), "-"],
                               capture_output=True, text=True, check=True).stdout
        for cle in re.findall(r"@@CH(\d+)@@", texte):
            pages[int(cle)] = n
    return pages, total


# Une page de fin de chapitre qui ne porte que quelques lignes paraît coupée : ces chapitres sont resserrés
# (image moins haute) pour tenir sur une page de moins
SEUIL_QUEUE = 8
SERRES = set()
SERRES2 = set()


def queues_courtes(pdf, pages):
    debuts = sorted((page, cle) for cle, page in pages.items())
    courtes = set()
    for (debut, cle), (suivant, _) in zip(debuts, debuts[1:]):
        fin = suivant - 1
        if fin <= debut:
            continue
        texte = subprocess.run(["pdftotext", "-f", str(fin), "-l", str(fin), str(pdf), "-"],
                               capture_output=True, text=True, check=True).stdout
        lignes = [l for l in texte.splitlines() if l.strip() and not l.strip().isdigit()]
        if len(lignes) <= SEUIL_QUEUE:
            courtes.add(cle)
    return courtes


def stabiliser(source, pdf, pages):
    for _ in range(5):
        source.write_text(document(pages), encoding="utf-8")
        imprimer(source, pdf)
        nouvelles, total = reperer_pages(pdf)
        if nouvelles == pages:
            return pages, total
        pages = nouvelles
    raise SystemExit("Les numéros de page ne se stabilisent pas.")


def composer(dossier):
    source = Path(dossier) / "livret.html"
    pdf = Path(dossier) / "livret.pdf"
    pages = {}
    for _ in range(6):
        pages, total = stabiliser(source, pdf, pages)
        courtes = queues_courtes(pdf, pages)
        nouvelles = (courtes - SERRES) | {c for c in courtes & SERRES if c not in SERRES2}
        if not nouvelles:
            break
        SERRES2.update(courtes & SERRES)
        SERRES.update(courtes)
        pages = {}
    inutiles = queues_courtes(pdf, pages) & SERRES2
    if inutiles:
        SERRES.difference_update(inutiles)
        SERRES2.difference_update(inutiles)
        pages, total = stabiliser(source, pdf, {})
    blanches = (-total) % 4
    if blanches:
        source.write_text(document(pages, blanches), encoding="utf-8")
        imprimer(source, pdf)
        assert reperer_pages(pdf)[0] == pages
    return pdf, pages


def traits_de_coupe(dossier):
    x0, y0 = (297 - 2 * LARGEUR_PAGE) / 2, (210 - HAUTEUR_PAGE) / 2
    gauche, droite, haut, bas = x0, x0 + 2 * LARGEUR_PAGE, y0, y0 + HAUTEUR_PAGE
    coupe = [f'<line x1="0" y1="{y}" x2="297" y2="{y}"/>' for y in (haut, bas)]
    coupe += [f'<line x1="{x}" y1="0" x2="{x}" y2="210"/>' for x in (gauche, droite)]
    pli = x0 + LARGEUR_PAGE
    source = Path(dossier) / "traits.html"
    source.write_text(
        '<!doctype html><html><head><style>@page { size: 297mm 210mm; margin: 0; } body { margin: 0; }</style></head>'
        '<body><svg xmlns="http://www.w3.org/2000/svg" width="297mm" height="210mm" viewBox="0 0 297 210">'
        f'<g stroke="#c9c9c9" stroke-width="0.2">{"".join(coupe)}</g>'
        f'<line x1="{pli}" y1="0" x2="{pli}" y2="210" stroke="#bcd6d0" stroke-width="0.2"/>'
        '</svg></body></html>', encoding="utf-8")
    pdf = Path(dossier) / "traits.pdf"
    imprimer(source, pdf)
    return PdfReader(str(pdf)).pages[0]


def imposer(lecture, traits, sortie, bord_long):
    pages = PdfReader(str(lecture)).pages
    n = len(pages)
    assert n % 4 == 0
    x0 = (A4_L - 2 * LARGEUR_PAGE * MM) / 2
    y0 = (A4_H - HAUTEUR_PAGE * MM) / 2
    ecrivain = PdfWriter()

    def face(gauche, droite, retournee):
        feuille = PageObject.create_blank_page(width=A4_L, height=A4_H)
        feuille.merge_page(traits)
        for indice, x in ((gauche, x0), (droite, x0 + LARGEUR_PAGE * MM)):
            feuille.merge_transformed_page(pages[indice - 1], Transformation().translate(x, y0))
        if retournee:
            feuille.rotate(180)
        ecrivain.add_page(feuille)

    for i in range(n // 4):
        face(n - 2 * i, 1 + 2 * i, False)
        face(2 + 2 * i, n - 1 - 2 * i, bord_long)
    with open(sortie, "wb") as f:
        ecrivain.write(f)


def construire():
    IMPRESSION.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as dossier:
        pdf, pages = composer(dossier)
        lecture = IMPRESSION / f"{NOM}_Livret_lecture.pdf"
        lecture.write_bytes(pdf.read_bytes())
        traits = traits_de_coupe(dossier)
        imposer(lecture, traits, IMPRESSION / f"{NOM}_Livret_A4_bord_court.pdf", bord_long=False)
        imposer(lecture, traits, IMPRESSION / f"{NOM}_Livret_A4_bord_long.pdf", bord_long=True)
    total = len(PdfReader(str(lecture)).pages)
    print(f"{lecture} : {total} pages, soit {total // 4} feuilles A4 recto verso")
    print("Chapitres resserrés :", ", ".join(str(c) + ("+" if c in SERRES2 else "") for c in sorted(SERRES)) or "aucun")
    print("Fins de chapitre encore courtes :", ", ".join(str(c) for c in sorted(queues_courtes(lecture, pages))) or "aucune")
    print("Pages des chapitres :", ", ".join(f"{k}→{v}" for k, v in sorted(pages.items())))


if __name__ == "__main__":
    construire()
