# Chaotic Text Generator

Application Streamlit réalisée pour le Lab 03 de NLP — Master SDIA, Ahmed Douyry.

Elle compare trois générateurs de phrases anglaises : HMM classique, HMM à états séparés par rôle et trigramme. Elle permet aussi d’étiqueter une phrase avec Viterbi.

## Installation

Python 3.11 ou 3.12. Depuis le dossier contenant `app.py` :

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Ouvrir http://localhost:8501. Sous Windows, utiliser `.venv\Scripts\activate` pour activer l’environnement. Le corpus et les résultats EWT nécessaires à l’interface sont inclus.

## Fonctionnalités

- Génération de 10 à 500 phrases avec modèle, température et graine configurables.
- Affichage des états cachés, filtres d’échecs et export CSV.
- Mesure de la structure, des couples sujet–verbe observés, de la nouveauté et de distinct-2.
- Décodage Viterbi avec signalement des mots inconnus.
- Comparaison des modèles, effet de la température et matrice des transitions.
- Consultation des résultats sur le corpus réel UD English EWT.

Le trigramme n’a pas d’états cachés : ses tags sont inférés après génération par Viterbi.

## Structure

```text
app.py              Interface Streamlit
assets/             Styles
src/                Modèles, logique métier et évaluations
data/              Corpus synthétique et script de génération
results/           Résultats EWT utilisés par l’application
tests/             Tests automatisés
```

## Tests et évaluations

```bash
python -m unittest discover -s tests -v
python -m src.evaluate
python -m src.evaluate_real
```

L’évaluation synthétique utilise 960 phrases d’entraînement, 240 de test et des lots de 500 phrases avec la graine 42. L’évaluation réelle télécharge EWT au premier lancement, puis utilise un cache local. Les fichiers produits par les évaluations sont ignorés par Git, sauf `results/ewt_results.json`, nécessaire à l’interface.

## Données et limites

Le corpus synthétique comporte 1 200 phrases et une grammaire réduite. Les métriques sont relatives à ce corpus et ne mesurent pas la qualité de l’anglais réel. Un couple sujet–verbe non observé n’est pas nécessairement incorrect ; nouveauté et diversité ne garantissent pas le sens.

Données réelles : [UD English EWT](https://github.com/UniversalDependencies/UD_English-EWT), annotations © Stanford et contributeurs sous [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). La révision et les empreintes des données évaluées figurent dans `results/ewt_results.json`.
