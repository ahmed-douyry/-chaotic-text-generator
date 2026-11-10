# chaotic. — Chaotic Text Generator

Banc d’essai NLP réalisé pour le Lab 03 : génération HMM classique, HMM à états séparés et trigramme, décodage Viterbi, évaluation et comparaison. Interface Streamlit en français, modèles et corpus anglais fournis avec le TP.

## Lancer l’application

Python 3.11 ou 3.12 recommandé. Depuis la racine de ce dépôt :

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Ouvrir http://localhost:8501. L’application fonctionne sans téléchargement de corpus ni service externe. Les résultats EWT et le corpus synthétique sont inclus.

## Fonctions

- Paramètres : trois modèles, température 0,3–3,0, graine et lots de 10 à 500 phrases.
- Une ligne par phrase : texte, états réellement échantillonnés, tags, structure valide, paire sujet–verbe observée et copie exacte du corpus.
- Quatre métriques calculées sur l’intégralité du lot, filtres d’échecs et téléchargement CSV UTF-8 avec paramètres de génération.
- Viterbi mot par mot avec ponctuation séparée, mots inconnus signalés et gestion des saisies vides ; le lissage ne garantit pas un bon tag pour un inconnu.
- Comparaison à paramètres identiques, courbe de température recalculable et matrice des transitions interactive.
- Évaluation réelle EWT avec provenance et téléchargement des résultats ; rapport PDF accessible dans Méthode.

Pour le trigramme, il n’existe pas de séquence cachée générative : les tags affichés sont inférés a posteriori avec le HMM à états séparés. Pour le HMM à états séparés, la structure est évaluée après suppression des suffixes S/O/P. Les paramètres sont appliqués à la soumission du formulaire ; le lot et ses métriques restent associés aux paramètres affichés même après une autre interaction.

## Reproduire les expériences

```bash
python -m src.evaluate
python -m src.evaluate_real
python -m unittest discover -s tests -v
```

`src.evaluate` mesure 500 phrases par modèle, graine 42 et T = 0,5 / 1,0 / 1,5 / 2,5, après séparation par document (960/240 phrases). Les résultats sont dans `results/metrics.json`, le journal dans `results/run_log.txt`.

`src.evaluate_real` télécharge les données publiques EWT au premier lancement (Internet requis), puis utilise le cache ignoré par Git. La révision est figée dans le script ; les tailles et empreintes SHA-256 sont enregistrées dans `results/ewt_results.json`. Les résultats mesurés sur cette révision sont légèrement différents des chiffres indicatifs du guide : **88,04 %** de précision HMM réelle, contre 88,1 % dans le guide. Les mêmes scores ne sont pas garantis sur une autre version de données.

| Modèle, T = 1 | Structure valide | Sujet–verbe observé | Phrases nouvelles | Distinct-2 |
|---|---:|---:|---:|---:|
| HMM classique | 16,2 % | 14,8 % | 99,8 % | 0,198 |
| HMM à états séparés | 100 % | 60,6 % | 99,4 % | 0,148 |
| Trigramme | 57,0 % | 76,0 % | 91,2 % | 0,105 |

Les modèles et le lissage du TP sont conservés. Seuls les logarithmes constants de Viterbi sont précalculés par décodage pour accélérer le test réel ; les transitions, les émissions, l’objectif et le départage des ex æquo restent identiques.

## Livrables

- `report/rapport.pdf` : rapport A4 d’une page, auteur Ahmed Douyry.
- `report/rapport.md` : source lisible du rapport.
- `report/failures_classified.csv` : classification des six phrases du fichier d’échecs.
- `screenshots/01-generation-desktop.png`, `screenshots/02-viterbi-desktop.png` : captures de l’application réelle.
- `screenshots/03-mobile.png` : contrôle complémentaire à 390 px.
- `results/` : mesures et journaux d’exécution.
- `DEPLOYMENT.md` : configuration de publication et vérifications.

Pour régénérer le rapport à partir des résultats :

```bash
pip install -r requirements-report.txt
python -m src.build_report
```

## Publier sur Streamlit Community Cloud

Le dépôt prévu est [ahmed-douyry/-chaotic-text-generator](https://github.com/ahmed-douyry/-chaotic-text-generator). Dans [Streamlit Community Cloud](https://share.streamlit.io/), créer une application depuis ce dépôt, branche `main`, fichier `app.py`, Python 3.12. `requirements.txt`, `.streamlit/config.toml` et `data/corpus.csv` doivent rester inclus. Voir [la documentation de déploiement officielle](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app).

**URL publique : en attente de déploiement sur le compte Streamlit.** Une URL locale ne remplace pas le livrable public. Une fois déployée, ouvrir l’application dans une fenêtre privée et vérifier génération, Viterbi et téléchargement CSV.

## Limites et données

Le corpus est synthétique et la grammaire est très réduite. La validité des patrons et la plausibilité sujet–verbe sont définies relativement à ce corpus : elles ne mesurent pas la qualité de l’anglais réel. Un couple absent n’est pas nécessairement absurde ; un couple observé ne prouve pas que la phrase a du sens. Distinct-2 dépend de la taille du lot ; la nouveauté n’est pas une preuve de créativité. La génération peut reproduire les données d’entraînement.

- Corpus synthétique : `data/corpus.csv`, 1 200 phrases, généré par `data/make_data.py` (graine 42).
- [Universal Dependencies English EWT](https://github.com/UniversalDependencies/UD_English-EWT), annotations © Stanford et contributeurs, licence [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Les textes sous-jacents ont diverses origines décrites dans le dépôt source. Prétraitement : minuscules, exclusion des lignes multi-tokens et nœuds vides.
- Révision EWT utilisée : `491be069d36e378f67c29f183699eea88308ea42` ; 12 544 phrases d’entraînement, 2 077 de test, 17 tags. Un seul domaine/langue est évalué.

Ne pas entraîner sur des messages privés sans autorisation. Les phrases générées sont des sorties probabilistes, pas des propos humains.
