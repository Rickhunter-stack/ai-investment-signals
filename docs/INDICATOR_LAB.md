# Indicator Lab

Objectif : tester prospectivement quels indicateurs précèdent réellement une surperformance future.

## Principe

Chaque signal est figé à sa date de détection. On conserve séparément :
- signal industriel ;
- confirmation financière ;
- criticité / substituabilité ;
- matérialité de l'exposition ;
- température de valorisation ;
- diversité des preuves ;
- catalyseur ;
- condition de falsification.

Puis on mesure les rendements futurs M1, M3, M6 et M12, en absolu et relativement à un benchmark.

## Visualisations prévues

1. **Cours + marqueurs de signaux** : courbe de prix avec événements datés superposés.
2. **Indicateur vs performance future** : nuage de points, un point par thèse figée.
3. **Heatmap des corrélations** : indicateurs en lignes, horizons en colonnes.
4. **Event study** : performance moyenne autour d'un type d'événement, par exemple nouveau client anchor, backlog en rupture ou validation réglementaire.
5. **Lead-lag** : recherche du décalage temporel où un indicateur est le plus informatif.
6. **Déciles** : comparaison de la performance future des 20 % de signaux les plus élevés avec les 20 % les plus faibles.

## Statistiques

Ne jamais conclure sur une corrélation visuelle seule.

Pour chaque couple indicateur / horizon :
- Pearson pour la relation linéaire ;
- Spearman pour la relation monotone et plus robuste aux valeurs extrêmes ;
- taille de l'échantillon ;
- médiane des rendements futurs ;
- taux de surperformance du benchmark ;
- intervalle de confiance par bootstrap lorsque l'échantillon devient suffisant.

## Garde-fous

- pas de look-ahead bias ;
- pas de réécriture des scores historiques ;
- date de disponibilité réelle de l'information, pas seulement date de période comptable ;
- distinguer corrélation et causalité ;
- corriger le problème des tests multiples quand beaucoup d'indicateurs sont comparés ;
- privilégier des indicateurs économiquement interprétables ;
- exiger un nombre minimal d'observations avant de qualifier un signal de prédictif.

## Indicateurs candidats par univers

### IA / semi-conducteurs
Capex hyperscalers, backlog, HBM, advanced packaging, réseau optique, MW disponibles, power/cooling, nombre d'anchors clients, RPO, marge incrémentale.

### Robotique
Unités déployées, cadence de production, commandes, nombre d'OEM qualifiés, délais de qualification fournisseur, coût par actionneur, vision/capteurs, réducteurs, vis à rouleaux, taux d'utilisation industriel.

### Biotech / medtech
Phase clinique, probabilité réglementaire, biomarqueur décisionnel, capacité CDMO, commandes de consommables, volumes de bioproduction, diagnostic compagnon, couverture remboursement, vitesse de recrutement des essais.

## Critère de valeur

Un bon indicateur n'est pas seulement corrélé au cours. Il doit :
1. être disponible avant le mouvement que l'on veut expliquer ;
2. avoir une logique économique plausible ;
3. rester utile sur plusieurs sociétés ou plusieurs épisodes ;
4. conserver une valeur prédictive hors échantillon.
