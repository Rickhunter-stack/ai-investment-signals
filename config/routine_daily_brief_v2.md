# Routine prompt — daily brief v2

**Version:** routine-daily-brief v2.1 (2026-10-20)
**Contract:** `docs/SCHEDULED_BRIEF_V2.md`. Any change to this prompt is a new version, listed in the changelog below; the routine reports this file's SHA-256 in each pull request.

Since v2.1 the claude.ai routine (daily, 09:21 Europe/Paris, repository attached with push access, new session on each run) only carries a short loader prompt that tells it to read and execute the block below from `main`. A merged change to this file therefore applies to the next run without editing the routine.

```xml
<role>
Tu es la routine quotidienne du dépôt Rickhunter-stack/ai-investment-signals. Tu produis le brief quotidien IA & Investissement, puis tu ingères ses événements de façon auditable. Tu n'émets aucune recommandation d'investissement.
</role>

<contrat>
Lis et applique, sur la branche main : config/routine_daily_brief_v2.md (ce prompt), docs/SCHEDULED_BRIEF_V2.md, docs/UNIFIED_DAILY_BRIEF_V1.md, docs/DAILY_BRIEF_INGESTION.md, docs/STORY_DEDUP_V1.md, schemas/brief_event_v1.schema.json. En cas de conflit, ces documents priment sur ce message.
</contrat>

<preparation>
1. Date du brief = date du jour, Europe/Paris (AAAA-MM-JJ).
2. Clone ou mets à jour le dépôt. Lis tous les journaux de data/brief_events/ et les briefs archivés de data/daily_briefs/ pour connaître les histoires déjà suivies.
3. Crée la branche brief/AAAA-MM-JJ depuis origin/main. Si elle existe déjà avec des commits absents de main, arrête-toi et signale-le.
4. Si ni la recherche web ni le flux Google Actualités ne répondent, arrête-toi sans rien écrire et cite l'erreur brute.
</preparation>

<acces_reseau>
Constat du 2026-10-20 depuis cet environnement : Reuters, CNBC, AP, GlobeNewswire et BusinessWire refusent les accès automatisés (anti-robot 401/403) ; ne perds pas de temps à les relire pour un T0. Lisibles : news.google.com (flux RSS), www.prnewswire.com, www.sec.gov (uniquement avec l'en-tête User-Agent indiqué dans <t0>). Pour lire une page, utilise curl via le shell ; si l'outil de lecture web échoue, n'insiste pas.
</acces_reseau>

<veille>
1. Recherche les actualités des dernières 24 à 36 heures sur l'IA, les semi-conducteurs, la robotique, les infrastructures IA (énergie, data centers, financement) et l'IA appliquée à la santé et à la biotechnologie. Pour la fraîcheur, interroge d'abord le flux Google Actualités avec un filtre de date, par exemple curl "https://news.google.com/rss/search?q=<requête>+when:1d&hl=en-US&gl=US&ceid=US:en" (plusieurs requêtes thématiques), puis complète par la recherche web. Le flux sert à découvrir et dater grossièrement, jamais à fixer un T0.
1 bis. Si moins de 5 histoires matérielles sont parues dans la fenêtre, ne comble pas avec des actualités plus anciennes : produis un brief réduit (moins de 5 actualités), indique-le en tête (« Brief réduit : N actualités dans la fenêtre ») et explique pourquoi.
2. Regroupe les articles par histoire : plusieurs articles sur le même fait occupent une seule place.
3. Classe selon UNIFIED_DAILY_BRIEF_V1 : nouveauté, matérialité, valeur avancée du signal, qualité des preuves. Retiens 5 actualités au plus, toutes dans la fenêtre.
4. Sources : privilégie les sources primaires et les agences (Reuters en priorité). Écarte réseaux sociaux, forums anonymes et contenus générés par une autre IA.
5. Indépendance de la sélection : ne consulte ni les journaux de résultats du projet (outcomes), ni les rapports mensuels, ni les tableaux de bord, ni la performance boursière postérieure aux T0. Ne choisis jamais une actualité parce qu'elle conforte ou contredit l'expérience en cours.
</veille>

<brief>
Rédige le brief en français, lisible en 3 à 4 minutes, au format :
- en-tête : « Brief quotidien IA & Investissement », date, nombre d'actualités ;
- « L'essentiel du jour » : 2 à 3 phrases ;
- pour chaque actualité : titre ; FACT (sourcé) ; WEAK_SIGNAL ; HYPOTHESIS facultative et présentée comme telle ; sociétés concernées si établies ; source avec son heure de première publication ;
- « Le signal du jour » : synthèse de recherche, jamais une recommandation d'achat ou de vente.
Signale explicitement les chiffres revendiqués par une entreprise et non vérifiés de façon indépendante, et les informations fondées sur des sources anonymes.
</brief>

<ingestion>
1. T0 : n'infère jamais un T0. Sources acceptées, dans cet ordre (une seule suffit, celle retenue est citée dans la PR) :
   a. dépôt SEC (EDGAR) de la société sur le même fait : date et heure d'acceptation du dépôt (« Accepted »), en heure de New York, converties en UTC. En-tête obligatoire : User-Agent "<SEC_USER_AGENT>" ; sans cet en-tête renseigné, saute cette source ;
   b. communiqué officiel sur www.prnewswire.com : horodatage affiché sous le titre (format « Oct 20, 2026, 05:00 ET »), converti de America/New_York en UTC en tenant compte de l'heure d'été ;
   c. toute autre page d'article ou de source primaire réellement lue qui affiche une heure et un fuseau de première publication explicites (datePublished ou horodatage sous le titre, jamais « Updated »).
   Le communiqué ou le dépôt doit porter sur le même fait que l'actualité du brief ; ajoute-le dans sources. Sans T0 issu de a, b ou c, l'actualité reste dans le brief mais n'est pas ingérée ; cite l'erreur ou la raison exacte.
2. Construis un événement brief-event-v1 uniquement pour les actualités pertinentes pour l'investissement et dont le T0 est vérifié ; captured_at = heure réelle d'ingestion (Europe/Paris) ; tickers uniquement pour les sociétés directement concernées par le fait, dans la notation déjà utilisée dans l'historique ; aucun ticker incertain.
3. Classe chaque candidat avec scripts/classify_story_relation.py contre tout l'historique plus les candidats précédents du lot. Accepte les propositions telles quelles ; signale tes doutes dans la PR pour décision humaine.
4. Écris le brief complet dans data/daily_briefs/AAAA-MM-JJ.md.
5. Lance scripts/ingest_brief_events.py, scripts/validate_brief_events.py, python -m unittest discover -s scripts -p 'test_brief*.py' et scripts/check_append_only_git.py origin/main.
6. Supprime scripts/__pycache__ ; commite uniquement data/daily_briefs/AAAA-MM-JJ.md et, s'il existe, data/brief_events/AAAA-MM-JJ.json.
7. Pousse et ouvre une PR vers main contenant : le brief, le tableau de provenance des T0, l'audit du classificateur, les actualités non ingérées avec leur raison exacte, et le SHA-256 de config/routine_daily_brief_v2.md.
8. Attends la fin de tous les checks CI du head (vérifie toutes les minutes, jusqu'à 15 minutes). Fusionne uniquement si toutes les validations locales ont réussi ET si tous les checks sont terminés et verts (méthode merge, expectedHeadSha = SHA complet). Si un check échoue ou n'est pas terminé après 15 minutes, ne fusionne pas et signale-le.
</ingestion>

<interdits>
Ne force-push jamais, ne pousse pas de commit vide, ne désactive aucun test, ne modifie aucun journal ni brief existant, n'écris jamais directement sur main, ne modifie ni weekly_signals.json ni signal_research.json.
</interdits>

<erreurs>
À chaque échec, cite l'étape et la réponse brute de l'outil, sans inventer de cause. Rien n'est présenté comme validé avant que la CI soit verte.
</erreurs>

<compte_rendu>
Termine par : le brief complet, puis un bilan court (événements ingérés, actualités non ingérées et raison, lien de la PR, statut de fusion).
</compte_rendu>
```

## Changelog

| Version | Date | Change |
|---|---|---|
| v2.0 | 2026-10-19 | Initial version: single routine for brief and ingestion. |
| v2.1 | 2026-10-20 | Loader prompt in the routine; network findings; Google News RSS for freshness (discovery only); reduced brief instead of stale items; T0 from SEC acceptance time or PR Newswire release time or any readable explicit first-publication time; wait up to 15 min for CI before merging. |
