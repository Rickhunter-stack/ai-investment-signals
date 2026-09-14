# Signal Score hebdomadaire V1

Le workflow collecte les fondamentaux puis exécute `scripts/generate_weekly_signals.py`
avant le builder. Le premier passage de chaque semaine ISO (normalement lundi à
21:15 UTC) fige un snapshot. Le premier passage après installation initialise
l'historique à la date UTC réelle. Les passages suivants ne modifient rien cette
semaine, même si les entrées changent. Aucun rattrapage historique n'est effectué.

## Méthode `weekly-v1.0`

Heuristique descriptive expérimentale, non calibrée par backtest et non destinée
à constituer une recommandation. Les seuils ci-dessous sont des choix V1, pas
des normes financières. La comparabilité sectorielle est limitée, notamment
pour les sociétés précommerciales. Changer la formule nécessite une nouvelle
version et ne doit jamais recalculer les snapshots antérieurs.

Chaque composante est sur 100. `clip(x)` borne x entre 0 et 100.

| Composante | Calcul ou entrée |
| --- | --- |
| fundamental_strength | moyenne de clip(marge FCF annuelle / 30 × 100) et clip(ROIC annuel / 20 × 100) |
| valuation | clip(FCF yield annuel / 5 × 100), rendement élevé = score élevé |
| novelty | analyse sourcée de la nouveauté d'un événement matériel |
| pricing_headroom | analyse sourcée de ce que le prix semble ne pas intégrer |
| execution_risk | analyse sourcée du risque, 100 = risque maximal |

Les ratios en entrée sont exprimés en pourcentage, par exemple 5 signifie 5 %.
Le score global est la moyenne des quatre premières composantes et de
`100 - execution_risk`. Il reste `null` si une composante manque. Le top3 contient
uniquement des scores complets, triés par score décroissant puis ticker.
Une absence de données n'est jamais convertie en zéro. Un ratio négatif connu
est en revanche borné à zéro selon la formule.

## Recherche sourcée

`data/signal_research.json` est indexé par ticker puis par composante qualitative.
Chaque composante fournie doit contenir `score` (0 à 100), `date` (YYYY-MM-DD),
`rationale` (texte non vide) et `sources` (liste non vide d'URL HTTP/HTTPS).
La date est celle de l'analyse disponible, sans anticipation. Une analyse de
plus de 35 jours est considérée indisponible. Les URL sont des références à
vérifier par l'auteur de l'analyse : le générateur ne vérifie pas leur contenu.

Le fichier commence vide : le générateur ne prétend pas déduire ces trois
dimensions des cours, d'un brief générique ou d'un avis automatique.
Les snapshots initiaux seront donc partiels : deux composantes financières
peuvent être affichées, mais aucun score global ni top3 tant que la recherche
n'est pas renseignée. La courbe apparaît avec les premiers scores complets.

## Intégrité

Le générateur conserve les octets des snapshots existants et ajoute seulement
un objet à la fin du tableau, par remplacement atomique. Il refuse les dates
désordonnées, les données financières collectées depuis plus de sept jours,
les entrées futures et les scores invalides. Il fige les valeurs d'entrée,
les références et leurs empreintes SHA-256 pour permettre un audit.
Il lit SQLite indirectement via les fichiers existants et ne la modifie pas.

Ne jamais éditer les objets existants de `data/weekly_signals.json`, même pour
une correction : documenter la correction dans les entrées futures.
La sérialisation des workflows évite deux refresh concurrents ; un push en
conflit échoue sans force-push. Le workflow reconstruit `index.html` et garde
les indicateurs de thèse, les briefs et les fondamentaux actuels.
