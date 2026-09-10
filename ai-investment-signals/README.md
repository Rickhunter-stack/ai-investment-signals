# AI Investment Signals

Projet de suivi prospectif de signaux faibles liés à l'IA et aux investissements.

## Objectif

Ne jamais réécrire l'histoire. Chaque signal est figé à sa date de détection avec :
- son score initial
- le cours au jour du signal
- la justification et la source
- son degré de nouveauté
- une estimation de ce qui est déjà pricé

Puis on mesure la performance à M+1, M+3, M+6 et M+12, en absolu et relativement au Nasdaq-100.

## Univers initial

NVDA, AVGO, QCOM, MU, GOOGL, AMZN, ADI, MDT, ISRG, GH.

## Fichiers

- `data/universe.csv` : univers suivi
- `data/signals.csv` : journal immuable des signaux
- `data/performance.csv` : performances futures
- `config.json` : règles de scoring
- `WORK_PROMPT.md` : prompt maître à utiliser dans ChatGPT Work
- `scripts/dashboard.py` : dashboard HTML local simple

## Règle de scoring

Score /100 :
- force fondamentale : 30
- nouveauté du signal : 20
- faible degré déjà pricé : 20
- valorisation : 15
- risque d'exécution inversé : 15

Le score ne constitue pas une recommandation d'achat.

## Discipline

1. Toute nouvelle entrée doit avoir une date et une source.
2. Le score d'origine ne doit jamais être modifié rétroactivement.
3. Les horizons futurs restent vides jusqu'à ce qu'ils soient réellement atteints.
4. Corrélation n'est pas causalité.
5. Le benchmark par défaut est le Nasdaq-100.
