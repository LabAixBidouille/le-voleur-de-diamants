#!/usr/bin/env python3
"""Dessine images/arbre.svg, l'arbre de toutes les branches du « Voleur de diamants ».

Dessin propre au livre de Nina : pas de cadre ni de cases. Chaque chapitre est une petite pierre ronde
portant son numéro, avec son titre dessous, et les chemins sont des tiges vert mousse qui descendent en
courbes, comme les campanules des illustrations. Un diamant bleu marque les tirages ; les nombres du dé
sont écrits en italique le long des tiges. Le fond est transparent : l'arbre est posé sur la page blanche.

La position des pierres est fixée à la main. Les titres viennent de source/texte.md, et les tiges sont
tracées d'après les renvois du texte.

Usage, depuis la racine du dépôt : python3 source/construire_arbre.py
"""
import base64
import html
import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
TEXTE = RACINE / "source" / "texte.md"
SORTIE = RACINE / "images" / "arbre.svg"
POLICES = {"Fraunces": RACINE / "fonts" / "Fraunces.woff2", "Fraunces-i": RACINE / "fonts" / "Fraunces-i.woff2"}
DIAMANT = RACINE / "images" / "diamant.png"

ENCRE, VIOLET, VIOLET_FONCE, VIOLET_PALE, BLEU, MOUSSE = "#33321f", "#7868a8", "#564887", "#ece8f5", "#2f74c8", "#d6587f"
GAUCHE, HAUT, LARGEUR, HAUTEUR = 150, 0, 820, 1560
R = 21   # rayon des pierres

# Centre de chaque pierre
CASES = {
    "P1": (560, 30), "P2": (560, 150), 1: (560, 250),
    2: (800, 385), 3: (560, 515),
    4: (330, 660), 5: (790, 660),
    6: (330, 840), 7: (560, 840), 8: (790, 840),
    9: (560, 1000),
    10: (340, 1145), 11: (780, 1145),
    12: (560, 1290),
    13: (340, 1430), 14: (780, 1430),
}
FINS = {13, 14}
TIRAGES = {1, 3, 9, 12}
# Les chapitres 4 et 5 tirent le même dé : leurs tiges se rejoignent en un carrefour, marqué du diamant,
# d'où partent les trois chemins vers le pivert, le chat blanc et le renard
CARREFOUR = (560, 748)
# Les nombres du dé, posés le long des tiges ou au-dessus de la pierre visée
ETIQUETTES = [
    ("1 à 3", 528, 395), ("4 à 6", 700, 318),
    ("1 à 3", 420, 590), ("4 à 6", 700, 590),
    ("1 ou 3", 270, 812), ("2 ou 4", 604, 808), ("5 ou 6", 850, 812),
    ("1 à 3", 430, 1075), ("4 à 6", 690, 1075),
    ("1 à 3", 430, 1362), ("4 à 6", 690, 1362),
]


def lire_texte():
    titres, renvois = {}, set()
    actuel = None
    for ligne in TEXTE.read_text(encoding="utf-8").split("\n"):
        m = re.match(r"## (Prologue (I+)|Chapitre (\d+))\. (.+)", ligne)
        if m:
            actuel = f"P{len(m.group(2))}" if m.group(2) else int(m.group(3))
            titres[actuel] = m.group(4)
        m = re.match(r"- .*[Pp]oursuis au chapitre (\d+)", ligne)
        if m:
            renvois.add((actuel, int(m.group(1))))
    renvois.add(("P1", "P2"))   # le premier texte mène au second, sans renvoi écrit
    return titres, renvois


def couper(texte, largeur=22):
    lignes, ligne = [], ""
    for mot in texte.split():
        if ligne and len(ligne) + 1 + len(mot) > largeur:
            lignes.append(ligne)
            ligne = mot
        else:
            ligne = f"{ligne} {mot}".strip()
    return lignes + [ligne]


def bas(cle, titres):
    """Point de départ des tiges : sous le titre de la pierre"""
    cx, cy = CASES[cle]
    return cx, cy + R + 10 + 19 * len(couper(titres[cle])) + (26 if cle in FINS else 0)


def pierre(cle, titre, diamant):
    cx, cy = CASES[cle]
    svg = []
    if cle in ("P1", "P2"):
        # Les deux textes d'ouverture : une petite pierre pleine, sans numéro
        svg.append(f'<circle cx="{cx}" cy="{cy}" r="{R - 9}" fill="{VIOLET_PALE}" stroke="{VIOLET}" stroke-width="2"/>')
    else:
        contour = BLEU if cle in FINS else VIOLET
        svg.append(f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="#fff" stroke="{contour}" stroke-width="2.2"/>')
        svg.append(f'<text x="{cx}" y="{cy + 6.5}" font-family="Fraunces" font-weight="600" font-size="18" '
                   f'text-anchor="middle" fill="{VIOLET_FONCE}">{cle}</text>')
    for i, l in enumerate(couper(titre)):
        svg.append(f'<text x="{cx}" y="{cy + R + 22 + i * 19}" font-family="Fraunces" font-weight="500" font-size="16.5" '
                   f'text-anchor="middle" fill="{ENCRE}" class="halo">{html.escape(l)}</text>')
    if cle in FINS:
        y = cy + R + 22 + 19 * len(couper(titre)) + 12
        svg.append(f'<text x="{cx}" y="{y}" font-family="Fraunces-i" font-size="26" text-anchor="middle" '
                   f'fill="{VIOLET_FONCE}">Fin</text>')
    if cle in TIRAGES:
        svg.append(f'<image href="data:image/png;base64,{diamant}" x="{cx + R + 4}" y="{cy - 15}" width="30" height="30"/>')
    return "\n".join(svg)


def tige(depart, arrivee, pointe=True):
    (x1, y1), (x2, y2) = depart, arrivee
    y2 -= (R + 3) if pointe else 14
    h = (y2 - y1) * 0.55
    return (f'<path d="M{x1},{y1} C{x1},{y1 + h} {x2},{y2 - h} {x2},{y2}" fill="none" stroke="{MOUSSE}" '
            f'stroke-width="2.2" stroke-linecap="round"{' marker-end="url(#pointe)"' if pointe else ''}/>')


def construire():
    titres, renvois = lire_texte()
    assert set(titres) == set(CASES), f"Chapitres du texte et pierres de l'arbre différents : {set(titres) ^ set(CASES)}"
    polices = "".join(
        f'@font-face{{font-family:"{nom}";src:url(data:font/woff2;base64,{base64.b64encode(f.read_bytes()).decode()}) format("woff2");'
        f'{"font-style:italic;" if nom.endswith("-i") else ""}}}'
        for nom, f in POLICES.items())
    diamant = base64.b64encode(DIAMANT.read_bytes()).decode()
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{GAUCHE} {HAUT} {LARGEUR} {HAUTEUR}" width="{LARGEUR}" height="{HAUTEUR}">',
           f'<defs><style>{polices} text{{font-variation-settings:"SOFT" 100;}} '
           '.halo{paint-order:stroke;stroke:#fff;stroke-width:5px;stroke-linejoin:round;}</style>',
           f'<marker id="pointe" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto">'
           f'<path d="M1,1 L8,5 L1,9" fill="none" stroke="{MOUSSE}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></marker></defs>']
    communs = {(a, b) for a, b in renvois if a in (4, 5)}
    assert communs == {(a, b) for a in (4, 5) for b in (6, 7, 8)}, "Les chapitres 4 et 5 ne mènent plus aux mêmes chapitres"
    svg += [tige(bas(a, titres), CASES[b]) for a, b in sorted(renvois - communs, key=str)]
    cx, cy = CARREFOUR
    svg += [tige(bas(a, titres), (cx, cy - 2), pointe=False) for a in (4, 5)]
    svg += [tige((cx, cy + 16), CASES[b]) for b in (6, 7, 8)]
    svg.append(f'<image href="data:image/png;base64,{diamant}" x="{cx - 17}" y="{cy - 17}" width="34" height="34"/>')
    for texte, x, y in ETIQUETTES:
        svg.append(f'<text x="{x}" y="{y}" font-family="Fraunces-i" font-size="15" text-anchor="middle" fill="{VIOLET_FONCE}" '
                   f'class="halo">{html.escape(texte)}</text>')
    svg += [pierre(c, titres[c], diamant) for c in CASES]
    svg.append("</svg>")
    SORTIE.write_text("\n".join(svg), encoding="utf-8")
    print(f"{SORTIE} : {len(CASES)} pierres, {len(renvois)} tiges")


if __name__ == "__main__":
    construire()
