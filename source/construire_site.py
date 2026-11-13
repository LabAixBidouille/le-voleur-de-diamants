#!/usr/bin/env python3
"""Construit index.html du « Voleur de diamants » à partir de source/texte.md.

Le moteur Harlowe (repris du site de L'île aux dragons) est conservé tel quel dans index.html : seules les
pages et la feuille de style du livre sont régénérées.

Mise en page propre au livre de Nina : un album qui s'ouvre sur l'image. Chaque chapitre commence par son
illustration, sans cadre, qui se fond dans le papier ; une deuxième image vient en vignette fondue à la fin
du texte. La page est blanche partout.

Usage, depuis la racine du dépôt : python3 source/construire_site.py
"""
import html
import re
import uuid
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
TEXTE = RACINE / "source" / "texte.md"
SORTIE = RACINE / "index.html"
NOINDEX = '<meta name="robots" content="noindex, nofollow, noarchive">'
FAVICON = ('<link rel="icon" type="image/png" sizes="48x48" href="images/favicon-48.png">'
           '<link rel="icon" type="image/png" sizes="180x180" href="images/favicon.png">'
           '<link rel="apple-touch-icon" href="images/favicon.png">')

TITRE = "Le voleur de diamants"
AUTRICE = "Nina"

# Résumé provisoire, à remplacer par celui de Manon
SYNOPSIS = (
    "Lapinette est née de la forêt pour veiller sur cinq diamants d'eau. Un matin, elle n'en compte plus "
    "que quatre, et des poils noirs pendent aux ronces.\n\n"
    "Le voleur a de grands yeux si doux qu'on en oublie de se méfier. Mais la forêt l'a prévenu : s'il "
    "garde encore le trésor d'un autre au lever de la lune, le vent l'emportera sur la Lune.\n\n"
    "Lance le dé et suis Lapinette sur la piste du voleur."
)

# Texte de Manon, modèle commun aux livres de l'atelier ; la phrase sur le genre est provisoire
CONTEXTE = [
    "En octobre 2026, le L.A.B a animé l’atelier « La quête du curry, une histoire dont tu es le héros » "
    "dans les bibliothèques Méjanes d’Aix-en-Provence. Les enfants ont été accompagnés dans la création "
    "d’un récit complet, depuis l’invention des personnages jusqu’à la construction d’une intrigue "
    "reliant les différentes étapes de leur aventure.",
    "Nous leur avons proposé d’introduire une part de hasard dans leur récit. Le résultat d’un lancer de "
    "dé pouvait modifier le déroulement de certains passages et conduire le lecteur vers un chapitre ou "
    "un autre.",
    "Les enfants ont ainsi exploré, sans écran, des notions liées à la pensée computationnelle, une "
    "manière de décomposer un problème et d’organiser les étapes pour le résoudre. Ils ont formulé des "
    "règles de type « si… alors… », créé des embranchements et réfléchi à la façon dont les chemins se "
    "rejoignent pour former une histoire cohérente.",
    "Nina a choisi d’écrire un conte, où une forêt vivante donne naissance à ses gardiens. Un défi pour "
    "une histoire à embranchements, puisque chaque chemin doit garder la magie du conte et conduire à une "
    "fin qui ait un sens.",
    "L’atelier ne durant que deux heures, nous tenions à offrir à chaque enfant un livre complet pour "
    "illustrer leur travail et les rendre fiers de leurs productions. Le L.A.B a donc prolongé et mis en "
    "forme leur récit à l’aide d’outils numériques (l’intelligence artificielle a notamment permis "
    "d’aboutir à une histoire achevée et à un ensemble de visuels correspondant à leurs descriptions mais "
    "uniformes tout au long de la lecture).\n\n<b>À son origine, il y a avant tout les idées et les "
    "personnages de Nina.</b>",
]
# La morale de sa fiche récit, à peine remise au propre
CITATION = "Voler, ce n’est pas gentil, ça ne sert à rien."

# Moment de la journée de chaque passage : il donne la teinte du papier
MOMENTS = {
    "Prologue I": "matin", "Prologue II": "matin",
    **{f"Chapitre {n}": "matin" for n in range(1, 9)},
    **{f"Chapitre {n}": "grotte" for n in (9, 10, 11)},
    "Chapitre 12": "soir", "Chapitre 13": "nuit", "Chapitre 14": "crepuscule",
}

# Une campanule, la fleur qui pousse sur presque toutes les images du livre
CAMPANULE = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 40 40'%3E"
             "%3Cpath d='M20 36 C20 26 21 16 24 5' fill='none' stroke='%232e6c66' stroke-width='1.6' stroke-linecap='round'/%3E"
             "%3Cg fill='%232e6c66'%3E%3Cpath d='M20.4 30 C15 29 11 26 9 22 C14 23 18 25 20.4 30Z'/%3E%3Cpath d='M20.6 30 C26 29 30 26 32 22 C27 23 23 25 20.6 30Z'/%3E"
             "%3Cpath d='M21 22 C16.5 21 13.5 18 12.5 14.5 C16.5 15.5 19.5 18 21 22Z'/%3E%3Cpath d='M21.4 22 C26 21 29 18 30 14.5 C26 15.5 23 18 21.4 22Z'/%3E"
             "%3Cpath d='M22.4 14.5 C19.5 13.5 17.5 11 17 8 C20 9 22 11.5 22.4 14.5Z'/%3E%3C/g%3E"
             "%3Cpath d='M23 14 C26 13 28 10.5 28.5 7.5 C25.5 8.5 23.5 11 23 14Z' fill='%23d4664c'/%3E"
             "%3C/svg%3E")

CSS = """
@font-face { font-family: "Fraunces"; font-style: normal; font-weight: 300 800; font-display: swap; src: url("fonts/Fraunces.woff2") format("woff2"); }
@font-face { font-family: "Fraunces"; font-style: italic; font-weight: 300 800; font-display: swap; src: url("fonts/Fraunces-i.woff2") format("woff2"); }
@font-face { font-family: "Literata"; font-style: normal; font-weight: 200 900; font-display: swap; src: url("fonts/Literata.woff2") format("woff2"); }
@font-face { font-family: "Literata"; font-style: italic; font-weight: 200 900; font-display: swap; src: url("fonts/Literata-i.woff2") format("woff2"); }

/* Couleurs prises aux images : encre vert sous-bois, violet des campanules, bleu des diamants de Lapinette,
   rose de la grotte, vert mousse. Le papier est blanc partout. */
:root {
  --encre: #1c2d24;
  --encre-douce: #4b5d52;
  --violet: #2e6c66;
  --violet-fonce: #1e4d48;
  --violet-pale: #e4efec;
  --bleu: #5c8fb0;
  --bleu-fonce: #2f5f7e;
  --rose: #d4664c;
  --rose-fonce: #ad4a33;
  --rose-pale: #fbe9e2;
  --mousse: #5d6e34;
  --papier: #ffffff;
}
html, body, tw-story { background-color: var(--papier); color: var(--encre); transition: background-color 1.2s ease; }

tw-story {
  font-family: "Literata", Georgia, serif;
  font-size: 1em;
  line-height: 1.7;
  padding: 0.8em 1.2em 3em;
  font-variation-settings: "opsz" 14;
}
tw-passage { max-width: 1120px; margin: 0 auto; }
tw-sidebar { display: none; }
tw-story { overflow: clip; }

/* Chapitres centrés : l'image en tête, aussi large que possible, ses bords à peine fondus dans la page
   blanche ; le texte dessous, au centre. Une deuxième image vient à la fin du texte, avec le même fondu. */
.page { max-width: 1000px; margin: 0 auto; }
.cote { position: relative; display: flex; justify-content: center; max-width: 40em; margin: 0 auto; }
/* Chaque image est dans une « toile » : c'est elle qui porte le fondu, pour que le grain de papier posé
   par-dessus s'efface avec l'image. Les couleurs sont un peu adoucies. */
.toile {
  position: relative;
  display: inline-block;
  max-width: 100%;
  vertical-align: top;
  -webkit-mask-image: linear-gradient(to right, transparent 0, #000 3.5%, #000 96.5%, transparent 100%),
                      linear-gradient(to bottom, transparent 0, #000 3.5%, #000 92%, transparent 100%);
  -webkit-mask-composite: source-in;
  mask-image: linear-gradient(to right, transparent 0, #000 3.5%, #000 96.5%, transparent 100%),
              linear-gradient(to bottom, transparent 0, #000 3.5%, #000 92%, transparent 100%);
  mask-composite: intersect;
}
.toile::after, .garde-image::after {
  content: "";
  position: absolute;
  inset: 0;
  background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='220' height='220'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 0.45 0 0 0 0 0.4 0 0 0 0 0.3 0 0 0 0.55 0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  mix-blend-mode: multiply;
  opacity: 0.55;
  pointer-events: none;
}
.toile img, .garde-image img { filter: saturate(0.75) brightness(1.04) contrast(0.95); }
.toile img { display: block; max-width: 100%; height: auto; }
/* Toutes les images au même format, paysage 3:2, à la largeur du texte : celles qui sont en hauteur sont
   recadrées, un peu au-dessus du centre pour garder les visages */
.cote, .suite-image { width: 100%; }
.toile { width: 100%; }
/* Images entières, jamais recadrées, toujours à la largeur du texte, même en hauteur */
.cote img, .suite-image img { width: 100%; height: auto; }
.toile { width: 100%; }
.texte { max-width: 40em; margin: 1.5em auto 0; }
.page:not(:has(.cote)) .texte { margin-top: 1.5em; }
.suite-image { display: flex; justify-content: center; margin: 1.4em auto 0; max-width: 40em; }

.chapitre { text-align: center; margin: 0 0 1.4em; font-weight: 400; font-size: 1em; line-height: 1.1; }
.chapitre .numero {
  display: block;
  font-family: "Fraunces", Georgia, serif;
  font-variation-settings: "SOFT" 100, "opsz" 14;
  font-weight: 500;
  font-size: 0.82em;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--rose);
  margin-bottom: 0.45em;
}
.chapitre .titre {
  display: block;
  font-family: "Fraunces", Georgia, serif;
  font-variation-settings: "SOFT" 100, "opsz" 72;
  font-weight: 500;
  font-size: 2.35em;
  line-height: 1.12;
  color: var(--encre);
}

/* Numéro du chapitre à cheval sur le bas de l'image, sur une pastille blanche */
.numero-image {
  position: absolute;
  left: 50%;
  bottom: 0;
  transform: translate(-50%, 50%);
  padding: 0.35em 1.1em 0.3em;
  border-radius: 999px;
  background: #fff;
  box-shadow: 0 4px 14px -6px rgba(173, 74, 51, 0.28);
  font-family: "Fraunces", Georgia, serif;
  font-weight: 600;
  font-size: 0.8em;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  white-space: nowrap;
  color: var(--rose);
}

/* Séparateur : une campanule entre deux traits violets */
.separateur { display: flex; align-items: center; justify-content: center; gap: 0.6em; margin: 1.8em 0 1.4em; }
.separateur::before, .separateur::after { content: ""; width: 4.5em; height: 1px; background: linear-gradient(to right, transparent, var(--violet)); }
.separateur::after { background: linear-gradient(to left, transparent, var(--violet)); }
.separateur .embleme { width: 1.9em; height: 1.9em; background: url("CAMPANULE") no-repeat center / contain; }

/* Lien Couverture */
.retour { max-width: 1120px; margin: 0 auto 0.6em; text-align: left; }
.retour tw-link, .retour .enchantment-link, .lien-retour tw-link, .lien-retour .enchantment-link {
  font-family: "Fraunces", Georgia, serif;
  font-style: italic;
  font-weight: 400;
  font-size: 0.9em;
  color: var(--encre-douce);
}
.retour tw-link::before, .lien-retour tw-link::before { content: "← "; }
.retour tw-link:hover, .lien-retour tw-link:hover { color: var(--violet); }

tw-link, .enchantment-link { color: var(--violet-fonce); font-weight: 600; text-decoration: none; }
tw-link:hover, .enchantment-link:hover { color: var(--violet); }

/* Poursuis : en italique violet, la flèche avance au survol */
.elan { text-align: center; margin-top: 0.4em; }
.elan tw-link, .elan .enchantment-link {
  font-family: "Fraunces", Georgia, serif;
  font-variation-settings: "SOFT" 100;
  font-style: italic;
  font-weight: 500;
  font-size: 1.25em;
  color: var(--violet-fonce);
  text-decoration: none;
  transition: color 0.2s ease;
}
.elan tw-link::after, .elan .enchantment-link::after { content: "→"; color: var(--rose); display: inline-block; margin-left: 0.35em; transition: transform 0.2s ease; }
.elan tw-link:hover::after, .elan .enchantment-link:hover::after { transform: translateX(5px); }
.elan tw-link:hover, .elan .enchantment-link:hover { color: var(--rose-fonce); }

/* Le tirage : un encart clair, les choix à gauche, le diamant bleu à droite */
.de {
  display: flex;
  align-items: center;
  gap: 1.2em;
  margin-top: 1.6em;
  padding: 0.9em 1.3em;
  border-radius: 18px;
  font-size: 0.95em;
  line-height: 1.5;
  background: #eef5f2;
  box-shadow: 0 14px 30px -14px rgba(30, 77, 72, 0.4);
}
.de-texte { flex: 1; min-width: 0; }
.de .consigne {
  display: block;
  font-family: "Fraunces", Georgia, serif;
  font-variation-settings: "SOFT" 100;
  font-style: italic;
  font-size: 1.05em;
  color: var(--violet-fonce);
  margin-bottom: 0.45em;
}
.choix { display: flex; flex-direction: column; align-items: flex-start; gap: 0.35em; }
.tirage { display: inline-flex; align-items: baseline; gap: 0.65em; }
.tirage b {
  flex: none;
  display: inline-block;
  width: 4.4em;
  box-sizing: border-box;
  padding: 0.05em 0.6em;
  border-radius: 999px;
  background: #fff;
  color: var(--rose-fonce);
  font-family: "Fraunces", Georgia, serif;
  font-weight: 600;
  font-size: 0.88em;
  text-align: center;
  white-space: nowrap;
}
.de .choix tw-link, .de .choix .enchantment-link { display: block; line-height: 1.35; white-space: nowrap; font-family: "Fraunces", Georgia, serif; font-style: italic; color: var(--violet-fonce); font-weight: 500; text-decoration: none; transition: color 0.2s ease; }
.de .choix tw-link:hover, .de .choix .enchantment-link:hover { color: var(--rose-fonce); }

/* Le diamant bleu de Lapinette sert de dé : il scintille tant qu'on ne l'a pas touché, tourne sur lui-même
   puis laisse voir le nombre tiré. Le résultat écrit n'est lu que par les lecteurs d'écran. */
.lancer { flex: none; display: flex; flex-direction: column; align-items: center; gap: 0.3em; }
.diamant {
  position: relative;
  width: 4.8em;
  height: 4.8em;
  padding: 0;
  border: none;
  background: none;
  font: inherit;
  cursor: pointer;
  perspective: 400px;
}
.diamant .pierre { position: absolute; inset: 0; background: url("images/diamant.png") no-repeat center / contain; transition: opacity 0.4s ease, filter 0.2s ease; }
.diamant:not(.touche) .pierre { animation: scintille 2.2s ease-in-out infinite; }
@keyframes scintille {
  0%, 100% { transform: scale(1); filter: drop-shadow(0 0 0 rgba(47, 116, 200, 0)); }
  50% { transform: scale(1.06); filter: drop-shadow(0 0 12px rgba(47, 116, 200, 0.7)) brightness(1.1); }
}
.diamant:hover .pierre { filter: drop-shadow(0 0 10px rgba(47, 116, 200, 0.6)) brightness(1.12); }
.diamant.roule .pierre { animation: tourne 0.9s cubic-bezier(.4, 0, .2, 1); }
@keyframes tourne { from { transform: rotateY(0) scale(1); } 50% { transform: rotateY(360deg) scale(1.12); } to { transform: rotateY(720deg) scale(1); } }
.diamant.montre .pierre { opacity: 0.35; }
.diamant .face {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: "Fraunces", Georgia, serif;
  font-variation-settings: "SOFT" 100, "opsz" 72;
  font-weight: 700;
  font-size: 3em;
  color: var(--bleu-fonce);
  text-shadow: 0 0 8px #fff, 0 0 18px #fff;
  opacity: 0;
  transition: opacity 0.4s ease 0.1s;
}
.diamant.montre .face { opacity: 1; }
.lancer .aide { font-family: "Fraunces", Georgia, serif; font-style: italic; font-size: 0.8em; color: var(--encre-douce); }
.resultat { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }

/* Fin */
.fin { text-align: center; margin-top: 0.4em; }
.fin .mot-fin {
  display: block;
  font-family: "Fraunces", Georgia, serif;
  font-variation-settings: "SOFT" 100, "opsz" 144;
  font-style: italic;
  font-weight: 400;
  font-size: 3.2em;
  color: var(--violet-fonce);
  margin-bottom: 0.4em;
}
.secondaires { display: flex; flex-wrap: wrap; justify-content: center; gap: 0.5em 1.4em; }
.secondaires tw-link, .secondaires .enchantment-link {
  font-family: "Fraunces", Georgia, serif;
  font-style: italic;
  font-weight: 500;
  font-size: 1em;
  color: var(--violet-fonce);
  text-decoration: underline 1px var(--violet);
  text-underline-offset: 0.3em;
}

/* Couverture sur deux colonnes, tout visible sans défiler : l'image à gauche, rognée de son blanc du haut et
   fondue sur ses bords dans la page blanche ; à droite le titre, le résumé et les boutons. */
tw-story:has(.garde) { padding-top: 0; padding-bottom: 0; }
.garde {
  height: 100vh;
  display: grid;
  grid-template-columns: auto minmax(20em, 27em);
  gap: 3.5em;
  align-items: center;
  justify-content: center;
  padding: 2vh 0;
  box-sizing: border-box;
}
.garde-image { position: relative; display: flex; justify-content: center; }
.garde-image img { display: block; width: auto; max-width: 100%; height: 94vh; object-fit: contain; filter: none; }
.garde-image::after { display: none; }
.garde-texte { display: flex; flex-direction: column; align-items: center; text-align: center; gap: clamp(0.7em, 2.2vh, 1.3em); }
.garde-entete { display: flex; flex-direction: column; align-items: center; }
.garde .surtitre {
  font-family: "Fraunces", Georgia, serif;
  font-weight: 500;
  font-size: 0.78em;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--rose);
}
.garde .grand-titre {
  margin: 0.15em 0 0.12em;
  font-family: "Fraunces", Georgia, serif;
  font-variation-settings: "SOFT" 100, "opsz" 144;
  font-weight: 500;
  font-size: clamp(2.4em, 7.2vh, 3.6em);
  line-height: 1;
  color: var(--encre);
}
.garde .nom-auteur { font-family: "Fraunces", Georgia, serif; font-style: italic; font-size: 1.25em; color: var(--encre-douce); }
.garde .separateur { margin: 0; }
.garde .synopsis { font-size: clamp(0.88em, 2.1vh, 1em); line-height: 1.7; }
.garde .commencer tw-link, .garde .commencer .enchantment-link {
  display: inline-flex;
  align-items: center;
  gap: 0.5em;
  font-family: "Fraunces", Georgia, serif;
  font-variation-settings: "SOFT" 100;
  font-style: italic;
  font-weight: 500;
  font-size: 1.6em;
  color: var(--violet-fonce);
  text-decoration: none;
  transition: color 0.2s ease;
}
.garde .commencer tw-link::before, .garde .commencer .enchantment-link::before,
.garde .commencer tw-link::after, .garde .commencer .enchantment-link::after {
  content: "";
  width: 1.15em;
  height: 1.15em;
  background: url("images/diamant.png") no-repeat center / contain;
  transition: transform 0.3s ease;
}
.garde .commencer tw-link:hover { color: var(--violet); }
.garde .commencer tw-link:hover::before { transform: rotate(-14deg) scale(1.12); }
.garde .commencer tw-link:hover::after { transform: rotate(14deg) scale(1.12); }
/* Les deux liens secondaires, sans soulignement, séparés par un point */
.garde .secondaires { gap: 0; font-size: 0.95em; }
.garde .secondaires tw-link, .garde .secondaires .enchantment-link { text-decoration: none; font-weight: 400; color: var(--encre-douce); transition: color 0.2s ease; }
.garde .secondaires tw-link:hover { color: var(--violet-fonce); }
.garde .secondaires .point { margin: 0 0.8em; color: var(--violet); }
@media (max-width: 860px) {
  .garde { height: auto; grid-template-columns: minmax(0, 1fr); gap: 1.2em; padding-top: 1em; }
  .garde-image img { height: auto; width: 100%; }

}

/* Page de l'arbre */
.arbre .lien-retour { display: block; font-size: 0.9em; }
.arbre-tete { text-align: center; margin: 0.5em 0 1.5em; }
.arbre h1 {
  margin: 0;
  font-family: "Fraunces", Georgia, serif;
  font-variation-settings: "SOFT" 100, "opsz" 72;
  font-weight: 500;
  font-size: 2.2em;
  color: var(--encre);
}
.arbre .arbre-sous-titre { display: block; font-style: italic; color: var(--encre-douce); margin-top: 0.3em; }
.arbre img { display: block; width: 100%; max-width: 900px; height: auto; margin: 0 auto; }

/* Page « Comment est née cette histoire » */
.contexte { max-width: 40em; margin: 1em auto 0; text-align: center; }
.contexte .lien-retour { display: block; text-align: left; margin-bottom: 1em; }
.contexte h1 {
  font-family: "Fraunces", Georgia, serif;
  font-variation-settings: "SOFT" 100, "opsz" 72;
  font-weight: 500;
  font-size: 2.2em;
  line-height: 1.15;
  color: var(--encre);
  margin: 1.4em 0 0;
}
.contexte-texte { text-align: left; }
.citation {
  margin: 1.8em auto;
  max-width: 28em;
  text-align: center;
  font-family: "Fraunces", Georgia, serif;
  font-variation-settings: "SOFT" 100;
  font-style: italic;
  font-size: 1.4em;
  line-height: 1.4;
  color: var(--violet-fonce);
}
.citation .source { display: block; margin-top: 0.5em; font-style: normal; font-size: 0.55em; letter-spacing: 0.14em; text-transform: uppercase; color: var(--mousse); }
.dessins { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: flex-end; gap: 1em 0.8em; margin: 0.6em auto 0.4em; }
.dessins figure { margin: 0; }
.dessins img { display: block; height: 5.6em; width: auto; margin: 0 auto; }
.dessins img.large { height: 6.2em; }
.dessins figcaption { margin-top: 0.4em; font-family: "Fraunces", Georgia, serif; font-style: italic; font-size: 0.92em; color: var(--violet-fonce); }
@media (max-width: 600px) { .dessins { gap: 0.8em 1.2em; } .dessins img { height: 5em; } .dessins img.large { height: 5.5em; } }
.table-fiches { margin: 2.6em auto 0; }
.table-fiches .titre-table { display: block; font-family: "Fraunces", Georgia, serif; font-style: italic; font-size: 1.3em; color: var(--encre); margin-bottom: 1.2em; }
.miniatures { display: flex; justify-content: center; align-items: flex-start; flex-wrap: wrap; gap: 1.8em; }
.miniatures figure { margin: 0; }
.miniatures figcaption { margin-top: 0.7em; font-family: "Fraunces", Georgia, serif; font-style: italic; color: var(--encre-douce); }
.miniature { display: block; padding: 0; border: none; background: none; cursor: zoom-in; }
.miniature img { display: block; height: 14em; width: auto; border-radius: 6px; box-shadow: 0 8px 22px -10px rgba(28, 45, 36, 0.5); transition: transform 0.2s ease; }
.miniature:hover img { transform: scale(1.04); }
.contexte .credits { display: block; margin-top: 2em; font-size: 0.9em; color: var(--encre-douce); }
.contexte .secondaires { margin-top: 1.4em; }
.agrandi { position: fixed; inset: 0; z-index: 100; display: flex; align-items: center; justify-content: center; padding: 2vh 2vw; background: rgba(51, 50, 31, 0.85); cursor: zoom-out; }
.agrandi img { max-width: 100%; max-height: 96vh; border-radius: 4px; }

@media (max-width: 600px) {
  tw-story { font-size: 1.04em; padding: 0.8em 1em 3em; }
  .chapitre .titre { font-size: 1.9em; }
  .de { flex-direction: column-reverse; align-items: stretch; }
  .lancer { align-self: center; }
  .miniature img { height: 10em; }
}
""".replace("CAMPANULE", CAMPANULE)


def e(texte):
    return html.escape(texte, quote=True)


def lire_chapitres():
    blocs = re.split(r"^## ", TEXTE.read_text(encoding="utf-8"), flags=re.M)[1:]
    chapitres = []
    for bloc in blocs:
        lignes = bloc.strip().split("\n")
        numero, titre = lignes[0].strip().split(". ", 1)
        paragraphes = [p.strip() for p in "\n".join(lignes[1:]).split("\n\n") if p.strip()]
        chapitres.append({"nom": numero, "numero": numero, "titre": titre, "paragraphes": paragraphes})
    return chapitres


SEPARATEUR = '<div class="separateur"><span class="embleme"></span></div>'

DE_VIRTUEL = (
    '<div class="lancer"><button class="diamant" type="button" aria-label="Toucher le diamant pour lancer le dé">'
    '<span class="pierre"></span><span class="face"></span></button>'
    '<span class="aide">touche le diamant</span>'
    '<span class="resultat" aria-live="polite"></span></div>'
)

SCRIPT = """
// Le diamant tourne sur lui-même puis montre le nombre tiré ; il ne choisit jamais à la place du lecteur
document.addEventListener('click', function (evenement) {
  var diamant = evenement.target.closest('.diamant');
  if (!diamant || diamant.classList.contains('roule')) return;
  var resultat = diamant.parentNode.querySelector('.resultat');
  var face = 1 + Math.floor(Math.random() * 6);
  diamant.classList.add('touche');
  diamant.classList.remove('montre');
  diamant.classList.add('roule');
  resultat.textContent = '';
  setTimeout(function () {
    diamant.classList.remove('roule');
    diamant.querySelector('.face').textContent = face;
    diamant.classList.add('montre');
    resultat.textContent = 'Le diamant montre ' + face + '.';
  }, 900);
});

// Page de contexte : une miniature s'ouvre en grand, un clic referme
document.addEventListener('click', function (evenement) {
  var ouvert = document.querySelector('.agrandi');
  if (ouvert) { ouvert.remove(); return; }
  var miniature = evenement.target.closest('.miniature');
  if (!miniature) return;
  var fond = document.createElement('div');
  fond.className = 'agrandi';
  var image = document.createElement('img');
  image.src = miniature.querySelector('img').src;
  image.alt = miniature.querySelector('img').alt;
  fond.appendChild(image);
  document.body.appendChild(fond);
});
document.addEventListener('keydown', function (evenement) {
  var ouvert = document.querySelector('.agrandi');
  if (ouvert && evenement.key === 'Escape') ouvert.remove();
});
"""


def lien(texte, cible):
    return f"[[{texte}->{cible}]]"


CHOIX = re.compile(r"^(?:De )?(\d(?: à | ou )\d) : (.*?)\s*[Pp]oursuis au chapitre (\d+)\.?$")
RENVOI = re.compile(r"^Poursuis au chapitre (\d+)\.?$")


def images(ch):
    base = illustration(ch["nom"])
    trouvees = []
    for suffixe in ("", "b"):
        chemin = RACINE / f"images/chapitres/{base}{suffixe}.jpg"
        if chemin.exists():
            from struct import unpack
            portrait = hauteur_largeur(chemin)
            trouvees.append((f"images/chapitres/{base}{suffixe}.jpg", portrait))
    return trouvees


def hauteur_largeur(chemin):
    """Vrai si l'image JPEG est plus haute que large (lecture de l'en-tête SOF, sans dépendance)."""
    donnees = chemin.read_bytes()
    i = 2
    while i < len(donnees):
        marqueur, taille = donnees[i + 1], int.from_bytes(donnees[i + 2:i + 4], "big")
        if marqueur in (0xC0, 0xC1, 0xC2):
            h, l = int.from_bytes(donnees[i + 5:i + 7], "big"), int.from_bytes(donnees[i + 7:i + 9], "big")
            return h > l
        i += 2 + taille
    return False


def passage_chapitre(ch, suivant):
    corps, choix, consigne, fin = [], [], None, False
    for p in ch["paragraphes"]:
        if p.startswith("- "):
            for ligne in p.split("\n"):
                ligne = ligne[2:].strip()
                m = CHOIX.match(ligne)
                if m:
                    # Le résultat du dé, ce qui arrive, puis le renvoi écrit comme dans le livre
                    texte = m[2].rstrip(" .")
                    texte = (texte[0].upper() + texte[1:] + ". ") if texte else ""
                    choix.append(f'<span class="tirage"><b>{m[1]}</b><span>{texte}'
                                 f'{lien(f"Poursuis au chapitre {m[3]}", f"Chapitre {m[3]}")}</span></span>')
                    continue
                m = RENVOI.match(ligne)
                assert m, f"Choix illisible dans {ch['nom']} : {ligne}"
                choix.append(lien(f"Poursuis au chapitre {m[1]}", f"Chapitre {m[1]}"))
        elif p == "FIN":
            fin = True
        elif p.startswith("**") and p.endswith("**"):
            consigne = p[2:-2].replace("Lance le dé", "Touche le diamant", 1)
        else:
            corps.append(p)
    # Le prologue I n'a pas de renvoi dans Notion : il mène au prologue II
    if not choix and not fin and suivant:
        choix.append(lien("Poursuis la lecture", suivant))

    # Colonne de gauche : les images du chapitre, l'une sous l'autre
    imgs = images(ch)
    cote = suite_image = ""
    if imgs:
        src, portrait = imgs[0]
        numero = "" if ch["nom"].startswith("Prologue") else f'<span class="numero-image">{ch["numero"]}</span>'
        cote = (f'<div class="cote"><span class="toile"><img class="{"portrait" if portrait else ""}" src="{src}" '
                f'alt="{ch["titre"]}"></span>{numero}</div>')
    if len(imgs) > 1:
        suite_image = (f'<div class="suite-image"><span class="toile"><img class="{"portrait" if imgs[1][1] else ""}" '
                       f'src="{imgs[1][0]}" alt=""></span></div>')

    suite = []
    if consigne:
        suite.append(f'<div class="de"><div class="de-texte"><span class="consigne">{consigne}</span>'
                     f'<div class="choix">{"".join(choix)}</div></div>{DE_VIRTUEL}</div>')
    else:
        suite.append(SEPARATEUR)
        if choix:
            suite.append(f'<div class="elan">{"".join(choix)}</div>')
    if fin:
        suite.append('<div class="fin"><span class="mot-fin">Fin</span>'
                     f'<div class="secondaires">{lien("Comment est née cette histoire", "Comment est née cette histoire")}'
                     f'{lien("Relire depuis le début", "Prologue I")}</div></div>')
    texte = ('<div class="texte">'
             # Les deux textes d'ouverture n'ont que leur titre, sans « Prologue I » ni « Prologue II »
             # Le numéro est sur l'image ; il ne reste au-dessus du titre que s'il n'y a pas d'image
             + ('<h1 class="chapitre">' if ch["nom"].startswith("Prologue") or imgs
                else f'<h1 class="chapitre"><span class="numero">{ch["numero"]}</span>')
             + f'<span class="titre">{ch["titre"]}</span></h1>'
             + "\n\n".join(corps) + suite_image + "".join(suite) + "</div>")
    moment = MOMENTS.get(ch["nom"], "matin")
    return f'<div class="page moment-{moment}">{cote}{texte}</div>'


def illustration(nom):
    """prologue-1, prologue-2, chapitre-01…"""
    if nom.startswith("Prologue"):
        return f"prologue-{len(nom.split()[-1])}"
    return f"chapitre-{int(nom.split()[-1]):02d}"


def passage_garde():
    return (
        '<div class="garde"><div class="garde-image"><img src="images/couverture.png" '
        'alt="Lapinette et le chat noir au pied d’un vieil arbre, les cinq diamants bleus devant eux"></div>'
        '<div class="garde-texte"><div class="garde-entete">'
        '<span class="surtitre">Une histoire dont le lecteur est le héros</span>'
        f'<span class="grand-titre">{TITRE}</span>'
        f'<span class="nom-auteur">{AUTRICE}</span></div>'
        f'<div class="synopsis">{SYNOPSIS.replace("Lance le dé", "Touche le diamant")}</div>'
        f'<div class="commencer">{lien("Commencer l’histoire", "Prologue I")}</div>{SEPARATEUR}'
        f'<div class="secondaires">{lien("Comment est née cette histoire", "Comment est née cette histoire")}'
        f'<span class="point">·</span>{lien("L’arbre de l’histoire", "L’arbre de l’histoire")}</div>'
        "</div></div>"
    )


def version_arbre():
    import hashlib
    return hashlib.md5((RACINE / "images" / "arbre.svg").read_bytes()).hexdigest()[:8]


def passage_arbre():
    return (
        f'<div class="arbre"><span class="lien-retour">{lien("Couverture", "Page de garde")}</span>'
        f'<div class="arbre-tete"><h1>{TITRE}</h1>'
        f'<span class="arbre-sous-titre">Tous les chemins de l’histoire imaginée par {AUTRICE}</span></div>'
        # Le numéro de version force le navigateur à recharger l'arbre quand il change
        f'<img src="images/arbre.svg?v={version_arbre()}" alt="L’arbre de toutes les branches de l’histoire"></div>'
    )


def miniature(fichier, legende, description):
    return (f'<figure><button class="miniature" type="button" aria-label="Agrandir {description}">'
            f'<img src="images/fiches/{fichier}" alt="{description}"></button>'
            f'<figcaption>{legende}</figcaption></figure>')


def dessin(fichier, nom, classe=""):
    return (f'<figure><img class="{classe}" src="images/dessins/{fichier}" alt="{nom}, dessiné par Nina">'
            f'<figcaption>{nom}</figcaption></figure>')


def passage_contexte():
    return (
        '<div class="contexte moment-matin"><span class="lien-retour">[[Couverture->Page de garde]]</span>\n'
        # Les personnages dessinés par Nina sur ses fiches, détourés
        '<div class="dessins">'
        + dessin("lapinette.png", "Lapinette") + dessin("chat-noir.png", "Le chat noir")
        + dessin("foret.png", "La forêt", "large") + dessin("pivert.png", "Le pivert")
        + dessin("chat-blanc.png", "Le chat blanc") + dessin("renard.png", "Le renard blanc")
        + '</div>'
        f'<h1>Comment est née cette histoire</h1>{SEPARATEUR}'
        '<div class="contexte-texte">'
        + "\n\n".join(CONTEXTE[:4])
        + f'<div class="citation">« {CITATION} »<span class="source">Nina, sur sa fiche récit</span></div>'
        + CONTEXTE[4]
        + '</div><div class="table-fiches"><span class="titre-table">Les fiches de l’atelier</span>'
        '<div class="miniatures">'
        + miniature("fiche_recit.jpg", "Le récit", "la fiche récit de Nina")
        + miniature("fiche_personnage_lapinette.jpg", "Une fiche personnage", "la fiche personnage de Lapinette")
        + miniature("fiche_situation_1.jpg", "Une fiche à embranchement", "la fiche situation n° 1, avec ses choix au dé")
        + '</div></div>'
        + '<span class="credits">Une histoire librement inspirée du récit de Nina.\nRéalisation du livre : '
        "Laboratoire d’Aix-périmentation et de Bidouille.</span>"
        + f'<div class="secondaires">{lien("Commencer le livre", "Prologue I")}</div>\n</div>'
    )


def construire():
    modele = SORTIE.read_text(encoding="utf-8")
    debut = modele[: modele.index("<tw-storydata")]
    moteur = modele[modele.index("</tw-storydata>"):]
    if NOINDEX not in debut:
        debut = debut.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n' + NOINDEX)
    debut = re.sub(r"<link rel=\"(?:icon|apple-touch-icon)\"[^>]*>", "", debut)
    debut = debut.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n' + FAVICON)
    debut = re.sub(r"<title>[^<]*</title>", f"<title>{TITRE}</title>", debut)
    lire = re.compile(r"JavaScript (?:needs to be enabled to play|doit être activé pour lire) [^<.]*\.")
    debut = lire.sub(f"JavaScript doit être activé pour lire {TITRE}.", debut)
    moteur = lire.sub(f"JavaScript doit être activé pour lire {TITRE}.", moteur)

    passages = [
        ("Bouton couverture", "header",
         '(unless: (a: "Page de garde", "Comment est née cette histoire", "L’arbre de l’histoire") contains (passage:)\'s name)'
         '[<div class="retour">[[Couverture->Page de garde]]</div>]'),
        ("Page de garde", "", passage_garde()),
        ("Comment est née cette histoire", "", passage_contexte()),
        ("L’arbre de l’histoire", "", passage_arbre()),
    ]
    chapitres = lire_chapitres()
    for i, ch in enumerate(chapitres):
        suivant = chapitres[i + 1]["nom"] if i + 1 < len(chapitres) else None
        passages.append((ch["nom"], "", passage_chapitre(ch, suivant)))

    # Espaces insécables de la typographie française
    insecables = [("« ", "« "), (" »", " »"), (" :", " :"), (" ?", " ?"),
                  (" !", " !"), (" ;", " ;")]
    for i, (nom, tags, contenu) in enumerate(passages):
        if tags != "header":
            contenu = contenu.replace("'", "’")  # apostrophe typographique
            for avant, apres in insecables:
                contenu = contenu.replace(avant, apres)
            passages[i] = (nom, tags, contenu)

    noms = {p[0] for p in passages}
    for nom, _, contenu in passages:
        for cible in re.findall(r"->([^\]]+)\]\]", contenu):
            assert cible in noms, f"Lien cassé dans {nom} : {cible}"

    xml = [f'<tw-storydata name="{e(TITRE)}" startnode="2" creator="Twine" creator-version="2.12.1" '
           f'format="Harlowe" format-version="3.3.9" ifid="{str(uuid.uuid5(uuid.NAMESPACE_URL, TITRE)).upper()}" '
           'options="" tags="" zoom="1" hidden>',
           f'<style role="stylesheet" id="twine-user-stylesheet" type="text/twine-css">{CSS}</style>',
           '<script role="script" id="twine-user-script" type="text/twine-javascript">' + SCRIPT + '</script>']
    for pid, (nom, tags, contenu) in enumerate(passages, start=1):
        xml.append(f'<tw-passagedata pid="{pid}" name="{e(nom)}" tags="{tags}" '
                   f'position="{pid * 150},0" size="100,100">{e(contenu)}</tw-passagedata>')
    SORTIE.write_text(debut + "".join(xml) + moteur, encoding="utf-8")
    print(f"{SORTIE} : {len(passages)} passages")


if __name__ == "__main__":
    construire()
