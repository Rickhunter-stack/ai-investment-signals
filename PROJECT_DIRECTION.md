# AI Investment Signals - Direction produit

Date : 2026-09-10

Ce document complète le PRD v0.3.1 gelé sans le modifier.

## Ambition

Construire un radar de recherche prospectif sur trois grands domaines :

1. Intelligence artificielle et semi-conducteurs
2. Robotique et automatisation
3. Biotechnologies et medtech

L'objectif n'est pas de chercher uniquement les leaders visibles. Le radar doit couvrir simultanément :

- les **blockbusters / anchors** : sociétés qui créent la demande, imposent une plateforme, ouvrent un marché ou déplacent massivement du capital ;
- les **sous-traitants critiques / enablers** : sociétés indispensables à un goulet d'étranglement, un composant, une capacité de production, un procédé, une infrastructure ou un outil réglementaire ;
- les **challengers / emerging** : sociétés plus petites où un changement de relation, de client, de backlog, de marge, de capacité ou de validation clinique peut produire une rupture de trajectoire.

## Principe directeur

Le système ne doit pas demander seulement « quelle entreprise parle d'IA/robotique/biotech ? », mais :

> **Quelle chaîne de valeur est en train de se tendre, qui crée le goulet d'étranglement, et quelles sociétés cotées en profitent avant que le consensus ne l'intègre complètement ?**

## Les 3 graphes de chaîne de valeur

### IA / semi-conducteurs

Hyperscalers et modèles -> GPU / ASIC -> HBM -> advanced packaging -> réseau / photonique -> alimentation / refroidissement -> datacenters -> logiciels / agents / edge AI.

Anchors typiques : NVDA, GOOGL, AMZN, MSFT, META, AVGO.

Enablers recherchés : mémoire, packaging, équipementiers, optique, connectique, power management, refroidissement, datacenters, instrumentation.

### Robotique

Donneurs d'ordre / OEM -> compute embarqué -> capteurs / vision -> moteurs / réducteurs / servos -> contrôleurs -> batteries / puissance -> intégration -> logiciels de navigation / perception -> maintenance.

Anchors typiques : TSLA, ISRG, ABB, TER, grands logisticiens et industriels.

Enablers recherchés : motion control, capteurs, machine vision, composants de précision, edge compute, actionneurs, safety systems.

### Biotech / medtech

Blockbuster thérapeutique ou diagnostic -> cible / modalité -> biomarqueur -> essais cliniques -> CRO / CDMO -> bioproduction -> consommables -> instrumentation -> diagnostic compagnon -> distribution / remboursement.

Anchors typiques : LLY, NVO, REGN, VRTX, AMGN, AZN, TMO, DHR.

Enablers recherchés : CDMO, CRO, bioproduction, filtration, single-use, séquençage, diagnostics compagnons, imagerie, automation de laboratoire, fournisseurs de réactifs et consommables.

## Ce que nous voulons détecter

Priorité aux changements matériels et datés :

- nouveau client anchor nommé ;
- nouveau fournisseur critique ;
- relation fournisseur qui passe de new à expanded ;
- croissance / accélération du CA ou du RPO ;
- backlog ou commandes en rupture ;
- capacité de production saturée ou expansion disproportionnée ;
- hausse de marge cohérente avec un pouvoir de prix ;
- acquisition qui ouvre une nouvelle couche de chaîne de valeur ;
- validation clinique ou réglementaire d'une modalité ;
- biomarqueur qui devient décisionnel ;
- contrat public ou privé disproportionné par rapport à la taille ;
- changement de capex d'un anchor révélant des bénéficiaires en amont ;
- concentration client, dilution, financement ou risque réglementaire qui invalide la thèse.

## Ce qui ne doit pas être confondu avec un signal

- multiplication des mentions médiatiques ;
- simple association à un thème ;
- communiqué promotionnel sans métrique ;
- performance boursière seule ;
- avis du LLM ;
- score composite unique utilisé comme recommandation.

## Restitution cible

Le dashboard doit proposer deux angles complémentaires :

### 1. Blockbusters / Anchors

Objectif : comprendre **où va l'argent et où se crée la demande**.

Pour chaque anchor :
- capex ;
- nouveaux marchés / produits ;
- gros contrats ;
- fournisseurs nommés ;
- dépendances technologiques ;
- évolution du consensus et de la valorisation.

### 2. Critical Enablers

Objectif : détecter **les sociétés moins visibles qui deviennent indispensables**.

Pour chaque enabler :
- nombre d'anchors liés ;
- technologie ou maillon critique ;
- croissance des revenus / backlog / marge ;
- diversification de clientèle ;
- vélocité des nouveaux événements ;
- diversité des origines de preuve ;
- température de valorisation ;
- risques de dilution / dépendance / exécution.

## Discipline prospective

Tout signal détecté est figé avec : date, source primaire, événement, règle déclenchée, score par famille et prix au moment de la détection.

Les performances à M+1 / M+3 / M+6 / M+12 sont ajoutées ultérieurement sans jamais réécrire le signal initial.

La corrélation entre signal et performance est descriptive. Elle ne vaut ni causalité ni recommandation d'achat.
