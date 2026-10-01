# Note de décision — Univers v2 en parallèle de v1

**Date de décision :** 2026-10-01
**Statut :** pièce figée au merge sur `main`. Après merge, aucune modification ; une correction prend la forme d'une note datée ajoutée en fin de fichier.
**Portée :** cette note fige l'univers v2 et la justification de la décision. Les règles de mesure (benchmark détaillé, analyse, procédure de recherche) relèvent de `PREREGISTRATION_V2.md` et `docs/RESEARCH_PROTOCOL_V2.md`, en cours d'audit séparément.
**Documents liés :** `PREREGISTRATION.md` (v1, inchangé par cette note)

## 1. Décision

1. **v1 reste intacte.** Univers de 10 titres, protocole v1.0 à v1.3, journal `data/outcomes_v1.json` : rien n'est modifié. v1 devient explicitement l'expérience pilote.
2. **Une expérience v2 est préenregistrée en parallèle**, sur un univers plus large défini mécaniquement (§3), avec son propre journal de résultats.
3. **Motif :** obtenir davantage d'entreprises distinctes et davantage de dispersion transversale des scores à chaque semaine. Le motif n'est **pas** d'atteindre plus vite un N nominal : les observations hebdomadaires d'un même titre se chevauchent et ne sont pas indépendantes.
4. **Les résultats ne sont jamais concaténés.** Trois ensembles distincts :
   - v1 confirmatoire (10 titres, `outcomes_v1.json`) ;
   - v2 confirmatoire (univers v2, journal v2 dédié) ;
   - une comparaison exploratoire des 10 titres communs, étiquetée comme telle.

## 2. Ce qui a déjà été vu avant cette décision

Cette décision n'est pas prise en aveugle total. Ce qui suit a été observé avant le 2026-10-01 et est déclaré ici pour l'audit :

- **Snapshots hebdomadaires figés** des 2026-09-14, 2026-09-22 et 2026-09-29 (`data/weekly_signals.json`). Ils contiennent déjà les 33 titres du seed. Pour les 23 titres hors v1, seules les composantes financières (fundamental_strength, valuation) y figurent ; aucun score global n'a été calculé faute de recherche qualitative.
- **Scores complets des 10 titres v1** aux 2026-09-22 et 2026-09-29, et leurs **ancrages T0** du 2026-09-25 dans `data/outcomes_v1.json`.
- **Performances boursières à environ 8 séances des 10 titres v1**, commentées dans un rapport mensuel du 2026-10-01 produit par un assistant externe (ex. QCOM environ −7 %, ADI environ +1,6 %, MDT environ −5 %), calculées sur de mauvais T0 et benchmarks. Ces chiffres n'ont aucune valeur d'outcome.
- **Actualité de marché générale** citée dans ce même rapport (résultats Micron, rachats d'actions Nvidia), non vérifiée.
- **Aucun horizon M+1, M+3, M+6 ou M+12 n'est atteint** ; aucun rendement n'a été calculé dans un journal d'outcomes.

**Déclaration de l'assistant de rédaction (Claude Code).** En préparant les brouillons v2, il a affiché les composantes fundamental_strength et valuation des 33 titres du snapshot du 2026-09-29, ainsi que la couverture de `data/market_pit`. Il n'a consulté aucun cours ni aucune performance des 23 titres hors v1. Ces composantes n'ont servi qu'à constater les titres structurellement incomplets (NVO, SYM), pas à choisir l'univers, qui était déjà fixé par le seed.

**Déclaration de l'auteur du projet — À CONFIRMER avant merge, sans sur-déclarer ni sous-déclarer :** aucune performance boursière des 23 titres hors v1 n'a été examinée de façon ciblée entre le 2026-09-14 et la présente décision. Des cours ou actualités ont pu être vus de façon incidente ; cela n'a donné lieu à aucune sélection. _[Confirmer ou corriger cette phrase, puis retirer cette mention entre crochets.]_

**Engagement :** ni les performances observées, ni les scores ou composantes affichés, n'ont servi à choisir les titres de v2. La liste est reprise intégralement et telle quelle d'un fichier antérieur (§3). Aucun titre n'est ajouté, retiré ou remplacé pour équilibrer les buckets de score.

## 3. Règle d'inclusion : le seed du 16/09

L'univers v2 est **exactement** le contenu de `data/universe_seed.csv` à la version suivante :

| Élément | Valeur |
|---|---|
| Fichier | `data/universe_seed.csv` |
| Commit de référence | `b20a146afa102e8f35117bd4360c138c21b83516` (2026-09-16 20:09:00 UTC) |
| Blob Git | `b945cb29cb7eb7a135ebefccb210b7b4f95d1ff1` |
| SHA-256 du fichier | `4c18479456697125ef4c02dd90c3b018543b8944fc39858c4dc42facb1ab3768` |
| Nombre de titres | 33 |

**Preuve d'antériorité :**
- `b20a146` est le commit le plus ancien de l'historique contenant ce fichier. C'est un commit racine : l'historique Git ne permet pas de remonter avant le 2026-09-16.
- Ce même blob est identique dans les autres commits racines de l'historique (`9ef0682`, `6e0357a`, `1e204aa`) et sur `main` au 2026-10-01 : le fichier n'a jamais été modifié.
- Le snapshot hebdomadaire daté du 2026-09-14 (`captured_at` 2026-09-14T06:48:53Z) contient exactement ces 33 tickers, dans le même ordre. Ce timestamp est inscrit dans un fichier lui-même commité pour la première fois le 2026-09-16 : il corrobore mais ne prouve pas seul.
- La date de commit est déclarée par l'auteur Git, pas certifiée par un tiers. La date serveur la plus solide disponible est celle du premier push sur GitHub.

Dans tous les cas, le seed est antérieur au préenregistrement v1 (commit `4a133a5`, 2026-09-17), à tout T0 (premier T0 : 2026-09-25) et à toute observation de performance.

**Constitution du seed — limite déclarée :** le seed a été constitué **manuellement par l'auteur du projet**, selon une logique **thématique** (IA/semi-conducteurs, robotique, biotech/medtech) et un rôle par titre (anchor, enabler, emerging). Ce n'est ni un indice, ni un tirage, ni une règle de capitalisation. Conséquences :
- biais de sélection en faveur de sociétés connues, majoritairement des grandes capitalisations américaines ;
- les conclusions de v2 ne se généralisent qu'à cet ensemble thématique, pas au marché ;
- la dispersion des scores n'est pas garantie : le bucket 0-39 peut rester peu peuplé.

## 4. Décisions de principe prises le 2026-10-01

Elles orientent le préenregistrement v2 ; leur rédaction détaillée y est auditée séparément.

1. **Benchmark :** attribution par secteur GICS (Santé → SPY, autres secteurs → QQQ). Cette règle reproduit exactement le mapping v1 pour les 10 titres communs. La classification de chaque titre sera figée avec source et date de consultation avant l'activation. Le thème du seed décrit l'univers ; il ne sert pas à choisir le benchmark (il range MDT et ISRG en `robotics`, ce qui contredirait v1).
2. **Procédure de recherche :** une seule procédure pour les 33 titres, y compris les 10 titres v1. La date du changement de procédure sera documentée dans le protocole v1 par un amendement daté, sans modifier aucun score passé ; les analyses v1 pourront distinguer en sensibilité les périodes avant et après.
3. **Titres structurellement incomplets :** NVO (devise de reporting différente de la devise de cotation, donc valuation absente) et SYM (fundamental_strength absente au 2026-09-29) restent dans l'univers. Leur absence est rapportée ; aucune imputation.
4. **Collecte de marché des 23 titres hors v1 :** démarrée tôt, avant le scoring v2, dans une modification séparée et strictement isolée de v1 : un échec sur ces titres ne doit jamais bloquer ni modifier la collecte, les snapshots ou les outcomes v1. Cette collecte ne produit aucun signal confirmatoire ; elle fait démarrer l'historique nécessaire au baseline momentum 12-1.

## 5. Séquence

1. Cette note (figée au merge).
2. `PREREGISTRATION_V2.md`, `docs/RESEARCH_PROTOCOL_V2.md` et le prompt de recherche avec ses ancres : audit, puis merge. Ils ne sont pas figés par cette note.
3. Implémentation : collecte de marché des 23 titres isolée de v1, moteur `outcomes_v2`, champs de traçabilité de la recherche et leur validateur.
4. Enregistrement d'activation daté (porte d'activation, cf. B8 de v1).
5. Premier snapshot v2 éligible : le premier snapshot hebdomadaire officiel postérieur à l'activation. **Aucun backfill** : les snapshots du 14/09, 22/09, 29/09 et tous ceux antérieurs à l'activation ne produisent aucune observation v2.
