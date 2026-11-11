# Déploiement et remise du TP

Le projet Streamlit doit être placé **à la racine du dépôt GitHub**, avec `app.py` à côté de `requirements.txt` et du dossier `data/`.

1. Ouvrir https://share.streamlit.io/ et se connecter avec le compte ayant accès au dépôt.
2. Choisir « Create app » / dépôt `ahmed-douyry/-chaotic-text-generator` / branche `main` / `app.py`.
3. Dans les paramètres avancés, choisir Python 3.12. Aucun secret nécessaire.
4. Déployer, attendre le démarrage, puis ouvrir l’URL publique en navigation privée.
5. Générer 500 phrases avec chacun des trois modèles, tester `the farmers watch the birds.` puis `the astronaut dances!`, et télécharger un CSV.
6. Copier l’URL obtenue dans le README et dans les éléments de remise. Ne pas présenter l’adresse localhost comme publique.

Le lancement à froid ne télécharge pas EWT : les métriques réelles et le rapport sont déjà inclus. Le calcul complet EWT est une commande séparée ; le cache `data/ewt/` est volontairement exclu du dépôt.

## État des livrables

| Exigence | Fichier / emplacement |
|---|---|
| Application complète | `app.py`, `src/laboratory.py`, `assets/style.css` |
| Modèles fournis | `src/pipeline.py` |
| Corpus inclus | `data/corpus.csv` |
| Évaluation synthétique | `results/metrics.json`, `results/run_log.txt` |
| Évaluation réelle exécutée | `results/ewt_results.json`, `results/ewt_run_log.txt` |
| Synthèse PDF d’une page (consigne du TP) | `report/rapport_synthese.pdf` |
| Rapport illustré avec les deux captures en annexe | `report/rapport.pdf` |
| Deux captures de l’application | `screenshots/01-generation-desktop.png`, `screenshots/02-viterbi-desktop.png` |
| Tests | `python -m unittest discover -s tests -v` |
| URL du dépôt | https://github.com/ahmed-douyry/-chaotic-text-generator |
| URL publique | À renseigner après déploiement Streamlit |
