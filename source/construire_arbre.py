#!/usr/bin/env python3
"""Dessine images/arbre.svg, l'arbre de toutes les branches du « Voleur de diamants ».

La position des cases et le tracé des flèches sont fixés à la main ci-dessous. Les titres viennent de
source/texte.md, et le script vérifie que les flèches dessinées correspondent exactement aux renvois du
texte : si le texte change, il s'arrête au lieu de dessiner un arbre faux.

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

# Couleurs du site : encre vert sous-bois, violet des campanules, bleu des diamants pour les fins
ENCRE, VIOLET, VIOLET_FONCE, VIOLET_PALE, BLEU = "#33321f", "#7868a8", "#564887", "#cfc6e6", "#2f74c8"
FOND = "#f1edf7"
GAUCHE, LARGEUR, HAUTEUR = -20, 1300, 1720
L_CASE, H_CASE = 240, 66

CASES = {
    "P1": (560, 40), "P2": (560, 170), 1: (560, 300),
    2: (860, 450), 3: (560, 600),
    4: (220, 770), 5: (800, 770),
    6: (540, 960), 7: (800, 960), 8: (1060, 960),
    9: (560, 1110),
    10: (300, 1280), 11: (820, 1280),
    12: (560, 1430),
    13: (300, 1580), 14: (820, 1580),
}
FINS = {13, 14}
TIRAGES = {1, 3, 5, 9, 12}
BAS = {c: CASES[c][1] + H_CASE + (48 if c in TIRAGES else 0) for c in CASES}   # où partent les flèches

FLECHES = [
    ("P1", "P2", [(560, 106), (560, 170)], []),
    ("P2", 1, [(560, 236), (560, 300)], []),
    (1, 3, [(560, BAS[1]), (560, 600)], [("1 à 3", 560, 470)]),
    (1, 2, [(560, BAS[1]), (560, 420), (860, 420), (860, 450)], [("4 à 6", 730, 420)]),
    (2, 3, [(860, 516), (860, 570), (680, 570), (680, 600)], []),
    (3, 4, [(560, BAS[3]), (560, 730), (220, 730), (220, 770)], [("1 à 3", 380, 730)]),
    (3, 5, [(560, BAS[3]), (560, 730), (800, 730), (800, 770)], [("4 à 6", 690, 730)]),
    (5, 6, [(800, BAS[5]), (800, 900), (540, 900), (540, 960)], [("1 ou 3", 640, 900)]),
    (5, 7, [(800, BAS[5]), (800, 960)], [("2 ou 4", 800, 932)]),
    (5, 8, [(800, BAS[5]), (800, 900), (1060, 900), (1060, 960)], [("5 ou 6", 960, 900)]),
    (4, 9, [(220, 836), (220, 1143), (440, 1143)], []),
    (6, 9, [(540, 1026), (540, 1110)], []),
    (7, 9, [(800, 1026), (800, 1068), (600, 1068), (600, 1110)], []),
    (8, 9, [(1060, 1026), (1060, 1086), (640, 1086), (640, 1110)], []),
    (9, 10, [(560, BAS[9]), (560, 1250), (300, 1250), (300, 1280)], [("1 à 3", 420, 1250)]),
    (9, 11, [(560, BAS[9]), (560, 1250), (820, 1250), (820, 1280)], [("4 à 6", 700, 1250)]),
    (10, 12, [(300, 1346), (300, 1400), (520, 1400), (520, 1430)], []),
    (11, 12, [(820, 1346), (820, 1400), (600, 1400), (600, 1430)], []),
    (12, 13, [(560, BAS[12]), (560, 1555), (300, 1555), (300, 1580)], [("1 à 3", 420, 1555)]),
    (12, 14, [(560, BAS[12]), (560, 1555), (820, 1555), (820, 1580)], [("4 à 6", 700, 1555)]),
]


def lire_texte():
    titres, renvois, ordre = {}, set(), []
    actuel = None
    for ligne in TEXTE.read_text(encoding="utf-8").split("\n"):
        m = re.match(r"## (Prologue (I+)|Chapitre (\d+))\. (.+)", ligne)
        if m:
            actuel = f"P{len(m.group(2))}" if m.group(2) else int(m.group(3))
            titres[actuel] = m.group(4)
            ordre.append(actuel)
        m = re.match(r"- .*[Pp]oursuis au chapitre (\d+)", ligne)
        if m:
            renvois.add((actuel, int(m.group(1))))
    renvois.add(("P1", "P2"))   # le prologue I mène au prologue II, sans renvoi écrit
    return titres, renvois


def couper(texte, largeur=24):
    lignes, ligne = [], ""
    for mot in texte.split():
        if ligne and len(ligne) + 1 + len(mot) > largeur:
            lignes.append(ligne)
            ligne = mot
        else:
            ligne = f"{ligne} {mot}".strip()
    return lignes + [ligne]


def case(cle, titre):
    cx, haut = CASES[cle]
    x = cx - L_CASE / 2
    contour = BLEU if cle in FINS else VIOLET_PALE
    svg = [f'<rect x="{x}" y="{haut}" width="{L_CASE}" height="{H_CASE}" rx="16" fill="#fff" stroke="{contour}" '
           f'stroke-width="2" filter="url(#ombre)"/>']
    # « Chapitre n » en petites capitales en haut de la case, le titre dessous
    etiquette = "" if cle in ("P1", "P2") else f"CHAPITRE {cle}"
    lignes = couper(titre)
    if etiquette:
        svg.append(f'<text x="{cx}" y="{haut + 18}" font-family="Fraunces" font-weight="600" font-size="11.5" '
                   f'letter-spacing="2" text-anchor="middle" fill="{VIOLET}">{etiquette}</text>')
        taille, interligne = (18, 0) if len(lignes) == 1 else (15.5, 17)
        y0 = haut + 44 if len(lignes) == 1 else haut + 37
    else:
        taille, interligne = (19, 21)
        y0 = haut + H_CASE / 2 - (len(lignes) - 1) * interligne / 2 + 6
    for i, l in enumerate(lignes):
        svg.append(f'<text x="{cx}" y="{y0 + i * interligne}" font-family="Fraunces" font-weight="500" font-size="{taille}" '
                   f'text-anchor="middle" fill="{ENCRE}">{html.escape(l)}</text>')
    if cle in FINS:
        svg.append(f'<text x="{cx}" y="{haut + H_CASE + 46}" font-family="Fraunces-i" font-size="34" text-anchor="middle" '
                   f'fill="{VIOLET_FONCE}">Fin</text>')
    return "\n".join(svg)


def diamant(cle, image):
    """Le diamant bleu sous les cases où l'on tire au sort"""
    cx, haut = CASES[cle]
    taille = 40
    y = haut + H_CASE + 4
    return f'<image href="data:image/png;base64,{image}" x="{cx - taille / 2}" y="{y}" width="{taille}" height="{taille}"/>'


def fleche(points, etiquettes):
    trace = " ".join(f"{x},{y}" for x, y in points)
    svg = [f'<polyline points="{trace}" fill="none" stroke="{FOND}" stroke-width="8"/>',
           f'<polyline points="{trace}" fill="none" stroke="{VIOLET}" stroke-width="2" stroke-linejoin="round" '
           'marker-end="url(#pointe)"/>']
    for texte, x, y in etiquettes:
        largeur = 8.4 * len(texte) + 20
        svg.append(f'<rect x="{x - largeur / 2}" y="{y - 12}" width="{largeur}" height="24" rx="12" fill="#fff" '
                   f'stroke="{VIOLET_PALE}" stroke-width="1.5"/>')
        svg.append(f'<text x="{x}" y="{y + 5}" font-family="Fraunces" font-weight="600" font-size="14" text-anchor="middle" '
                   f'fill="{VIOLET_FONCE}">{html.escape(texte)}</text>')
    return "\n".join(svg)


def construire():
    titres, renvois = lire_texte()
    dessinees = {(a, b) for a, b, _, _ in FLECHES}
    assert set(titres) == set(CASES), f"Chapitres du texte et cases de l'arbre différents : {set(titres) ^ set(CASES)}"
    assert renvois == dessinees, f"Renvois du texte et flèches de l'arbre différents : {renvois ^ dessinees}"

    polices = "".join(
        f'@font-face{{font-family:"{nom}";src:url(data:font/woff2;base64,{base64.b64encode(f.read_bytes()).decode()}) format("woff2");'
        f'{"font-style:italic;" if nom.endswith("-i") else ""}}}'
        for nom, f in POLICES.items())
    image = base64.b64encode(DIAMANT.read_bytes()).decode()
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{GAUCHE} 0 {LARGEUR} {HAUTEUR}" width="{LARGEUR}" height="{HAUTEUR}">',
           f'<defs><style>{polices} text{{font-variation-settings:"SOFT" 100;}}</style>',
           f'<filter id="ombre" x="-10%" y="-20%" width="120%" height="160%"><feDropShadow dx="0" dy="5" stdDeviation="6" flood-color="{VIOLET_FONCE}" flood-opacity="0.16"/></filter>',
           f'<marker id="pointe" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{VIOLET}"/></marker></defs>']
    svg.append(f'<rect x="{GAUCHE}" y="0" width="{LARGEUR}" height="{HAUTEUR}" rx="28" fill="{FOND}"/>')
    svg += [fleche(t, e) for _, _, t, e in FLECHES]
    svg += [diamant(c, image) for c in TIRAGES]
    svg += [case(c, titres[c]) for c in CASES]
    svg.append("</svg>")
    SORTIE.write_text("\n".join(svg), encoding="utf-8")
    print(f"{SORTIE} : {len(CASES)} cases, {len(FLECHES)} flèches")


if __name__ == "__main__":
    construire()
