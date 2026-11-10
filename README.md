# Le voleur de diamants

Une histoire dont le lecteur est le héros, librement inspirée du récit imaginé par Nina pendant l'atelier « La quête du curry, une histoire dont tu es le héros » du L.A.B, à la bibliothèque des Deux Ormes (bibliothèques Méjanes, Aix-en-Provence), en octobre 2026.

## Modifier le livre

Le texte se trouve dans `source/texte.md`, recopié de la page Notion de référence. Chaque partie commence par `## Chapitre n. Titre` (ou `## Prologue I. Titre`), les renvois s'écrivent comme dans Notion (« Poursuis au chapitre n. », « De 1 à 3 : … Poursuis au chapitre n. ») et une fin se termine par `FIN`. La couverture, la page « Comment est née cette histoire » et la mise en forme sont dans `source/construire_site.py`.

Les illustrations vont dans `images/chapitres/` (`prologue-1.jpg`, `chapitre-01.jpg`, puis `chapitre-01b.jpg` pour une deuxième image, affichée en vignette à la fin du texte). L’arbre se redessine avec `python3 source/construire_arbre.py`.

```
python3 source/construire_site.py
```

Réalisation du livre : Laboratoire d'Aix-périmentation et de Bidouille.
