"""Chaotic / Lab 03 — Streamlit application. Run: streamlit run app.py."""
import html
import json
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from src.laboratory import Laboratory, MODELS, TEMPERATURES

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="Chaotic · Laboratoire de texte", page_icon="🌿", layout="wide")
st.markdown(f"<style>{(ROOT / 'assets/style.css').read_text()}</style>", unsafe_allow_html=True)


@st.cache_resource
def get_lab():
    return Laboratory()


@st.cache_data(show_spinner=False)
def make_batch(model, temperature, seed, count):
    return get_lab().generate(model, temperature, seed, count)


@st.cache_data(show_spinner=False)
def sweep(seed, count):
    return pd.DataFrame([
        {"Température": t, "Modèle": MODELS[key], "Structure valide (%)": make_batch(key, t, seed, count).metrics["valid_tag_pattern"] * 100}
        for key in MODELS for t in TEMPERATURES
    ])


def metric_cards(metrics):
    columns = st.columns(4)
    specs = [
        ("Structure valide", "valid_tag_pattern", "Part des séquences de tags observées dans l’entraînement."),
        ("Sujet–verbe plausible", "plausible_subject_verb", "Couple premier nom / premier verbe observé à l’entraînement ; ce n’est pas un jugement de sens."),
        ("Phrases nouvelles", "novel_sentences", "Part des phrases absentes du corpus d’entraînement."),
        ("Diversité · distinct-2", "distinct_2", "Bigrammes distincts / nombre total de bigrammes. Dépend de la taille du lot."),
    ]
    for col, (label, key, help_text) in zip(columns, specs):
        col.metric(label, f"{metrics[key]:.3f}" if key == "distinct_2" else f"{metrics[key]:.1%}", help=help_text)


def comparison_frame(batches):
    return pd.DataFrame([{
        "Modèle": MODELS[b.model], "Structure valide": b.metrics["valid_tag_pattern"],
        "Sujet–verbe plausible": b.metrics["plausible_subject_verb"],
        "Phrases nouvelles": b.metrics["novel_sentences"], "Distinct-2": b.metrics["distinct_2"],
    } for b in batches])


lab = get_lab()
with st.sidebar:
    st.markdown('<div class="lab-brand">chaotic<span style="color:#a87832">.</span></div><div class="lab-overline">Le laboratoire du langage</div>', unsafe_allow_html=True)
    st.divider()
    st.markdown("### Paramètres de l’expérience")
    with st.form("generation_controls"):
        model_key = st.selectbox("Modèle génératif", list(MODELS), index=1, format_func=MODELS.get)
        temperature = st.slider("Température", 0.3, 3.0, 1.0, 0.1, help="Bas : plus répétitif. Haut : distributions plus uniformes et davantage de variété.")
        st.caption("0,3 · concentré  ↔  3,0 · exploratoire")
        count = st.slider("Nombre de phrases", 10, 500, 100, 10)
        seed = st.number_input("Graine aléatoire", min_value=0, max_value=2_147_483_647, value=42, step=1, help="Les mêmes paramètres et la même graine reproduisent le même lot.")
        generate = st.form_submit_button("Générer le lot  →", type="primary", width="stretch")
    st.caption("Les paramètres s’appliquent en cliquant sur Générer le lot.")
    st.divider()
    st.markdown("### Corpus d’étude")
    st.markdown(f"**{len(lab.train):,}** phrases d’entraînement  \n**{len(lab.test)}** phrases de test  \n**{len(lab.plain.vocab)}** mots · **{len(lab.patterns)}** structures")
    st.caption("Séparation par document · aucun document partagé entre entraînement et test.")
    with st.expander("Comprendre les modèles"):
        st.write("**HMM classique** : un état par catégorie grammaticale.\n\n**HMM à états séparés** : les rôles sujet (S), objet (O) et groupe prépositionnel (P) donnent de la mémoire au modèle.\n\n**Trigramme** : prédit le prochain mot à partir des deux précédents, avec repli bigramme/unigramme.")

if "batch" not in st.session_state or generate:
    with st.spinner("Génération et mesure du lot…"):
        st.session_state.batch = make_batch(model_key, temperature, int(seed), count)
batch = st.session_state.batch

st.markdown('<div class="lab-masthead"><span>NLP / LAB 03 — Modèles probabilistes</span><span class="lab-status">● &nbsp; Corpus synthétique</span></div>', unsafe_allow_html=True)
st.markdown('<div class="lab-overline">Observer · Générer · Comprendre</div>', unsafe_allow_html=True)
st.title("Chaotic Text Generator")
st.markdown('<p class="lab-intro">Entre règles et hasard, comment naît une phrase ? Explorez les états cachés, mesurez les erreurs et comparez trois modèles de langage.</p>', unsafe_allow_html=True)
st.markdown('<div class="lab-flow"><b>ÉTAT CACHÉ</b><span>→</span><b>MOT ÉMIS</b><span>→</span><b>PHRASE</b><span>→</span><b>ÉVALUATION</b></div>', unsafe_allow_html=True)

experiment, tagger, compare, real, notebook = st.tabs(["01 · Génération", "02 · Viterbi", "03 · Comparaison", "04 · Texte réel", "05 · Méthode"])

with experiment:
    st.subheader("Du hasard, sous observation.")
    st.markdown(f'<div class="lab-run">{MODELS[batch.model]} &nbsp; / &nbsp; T = {batch.temperature:.1f} &nbsp; / &nbsp; graine {batch.seed} &nbsp; / &nbsp; {batch.count} phrases</div>', unsafe_allow_html=True)
    metric_cards(batch.metrics)
    st.write("")
    left, right = st.columns([3, 1])
    left.markdown("### Carnet de génération")
    right.download_button("↓ Télécharger le CSV", data=batch.csv_bytes(), file_name=f"chaotic_{batch.model}_T{batch.temperature}_seed{batch.seed}.csv", mime="text/csv", width="stretch")
    filter_value = st.radio("Afficher les phrases", ["Toutes", "Structure invalide", "Paires non observées", "Copies du corpus"], horizontal=True)
    filtered = [row for row in batch.rows if filter_value == "Toutes" or
                (filter_value == "Structure invalide" and not row["valid"]) or
                (filter_value == "Paires non observées" and not row["plausible"]) or
                (filter_value == "Copies du corpus" and row["copied"])]
    st.caption(f"{len(filtered)} / {batch.count} phrases · ✓ = propriété vérifiée sur le corpus · le CSV contient toujours le lot complet.")
    if filtered:
        table = pd.DataFrame(filtered).rename(columns={"id": "N°", "sentence": "Phrase", "hidden_states": "États cachés", "tags": "Tags", "valid": "Structure valide", "plausible": "Paire observée", "copied": "Copie"})
        st.dataframe(table, hide_index=True, height=355, width="stretch", column_order=["N°", "Phrase", "Structure valide", "Paire observée", "Copie", "États cachés", "Tags"], column_config={"Phrase": st.column_config.TextColumn(width="large"), "États cachés": st.column_config.TextColumn(width="large")})
        with st.expander("Examiner une phrase et ses états"):
            selected = st.selectbox("Numéro de phrase", [row["id"] for row in filtered])
            row = batch.rows[selected - 1]
            st.markdown(f'<div class="lab-sentence">{html.escape(row["sentence"])}</div>', unsafe_allow_html=True)
            st.code(row["hidden_states"], language=None)
            if batch.model == "ngram":
                st.caption("Le trigramme n’a pas d’états cachés : ses tags sont inférés après génération par le HMM à états séparés.")
            else:
                st.caption("États réellement échantillonnés ; la validité est évaluée après suppression des suffixes de rôle.")
    else:
        st.info("Aucune phrase ne correspond à ce filtre dans le lot actuel.")
    st.markdown('<div class="lab-note"><strong>Limite du banc d’essai.</strong> Le corpus est synthétique et la grammaire est très réduite. Les métriques, notamment la validité des structures, sont définies par rapport à ce corpus et ne mesurent pas la qualité de l’anglais réel.<br><span lang="en">The corpus is synthetic and the grammar is tiny. Metrics such as valid tag pattern are defined relative to this corpus and do not measure the quality of real English.</span></div>', unsafe_allow_html=True)

with tagger:
    st.subheader("Retrouver la structure cachée.")
    st.write("Viterbi recherche la séquence de tags la plus probable en additionnant des log-probabilités.")
    with st.form("tag_form"):
        sentence = st.text_area("Votre phrase en anglais", "the farmers watch the birds.", height=100, max_chars=2000)
        role_split = st.checkbox("Utiliser les états séparés par rôle", value=True)
        submitted = st.form_submit_button("Analyser avec Viterbi  →", type="primary")
    if submitted or "tagged" not in st.session_state:
        st.session_state.tagged = lab.tag(sentence, role_split)
    words, tags, unknown = st.session_state.tagged
    if not words:
        st.info("Saisissez au moins un mot pour lancer l’analyse.")
    else:
        if unknown:
            st.warning("Mots hors vocabulaire : " + ", ".join(unknown) + ". Le lissage permet une prédiction, mais ces tags sont peu fiables.")
        tokens = []
        for word, tag in zip(words, tags):
            cls = "unknown" if word in unknown else "verb" if tag == "VERB" else ""
            tokens.append(f'<div class="lab-token {cls}"><strong>{html.escape(word)}</strong><small>{html.escape(tag)}</small></div>')
        st.markdown('<div class="lab-tokens">' + "".join(tokens) + '</div>', unsafe_allow_html=True)
        st.caption("DET · déterminant / ADJ · adjectif / NOUN · nom / VERB · verbe / PREP · préposition / PUNCT · ponctuation")
        st.dataframe(pd.DataFrame({"Mot": words, "Tag Viterbi": tags, "Dans le vocabulaire": [w not in unknown for w in words]}), hide_index=True, width="stretch")
    with st.expander("Explorer le vocabulaire et l’ambiguïté de watch"):
        st.write(", ".join(sorted(lab.plain.vocab)))
        st.write("Comparez « the farmers watch the birds. » et « the watch follows the birds. » : watch peut être un verbe ou un nom selon son contexte.")

with compare:
    st.subheader("Trois modèles. Une même expérience.")
    st.caption(f"Paramètres du lot affiché : T = {batch.temperature:.1f} · graine {batch.seed} · {batch.count} phrases par modèle. Chaque modèle repart de la même graine.")
    if st.button("Comparer les trois modèles", type="primary"):
        with st.spinner("Évaluation des trois modèles…"):
            st.session_state.comparison = [make_batch(key, batch.temperature, batch.seed, batch.count) for key in MODELS]
    comparisons = st.session_state.get("comparison")
    if comparisons:
        first = comparisons[0]
        st.caption(f"Résultat de comparaison : T = {first.temperature:.1f} · graine {first.seed} · {first.count} phrases / modèle.")
        st.dataframe(comparison_frame(comparisons).style.format({"Structure valide": "{:.1%}", "Sujet–verbe plausible": "{:.1%}", "Phrases nouvelles": "{:.1%}", "Distinct-2": "{:.3f}"}), hide_index=True, width="stretch")
    else:
        st.info("Lancez la comparaison pour mesurer les trois modèles sur les paramètres du lot actuel.")
    st.markdown("### La température change-t-elle la structure ?")
    st.caption("Balayage de T = 0,5 ; 1,0 ; 1,5 ; 2,5. Les points représentent des mesures indépendantes ; les lignes guident la lecture.")
    if st.button("Calculer la courbe de température"):
        with st.spinner("12 expériences en cours…"):
            st.session_state.sweep = (batch.seed, batch.count, sweep(batch.seed, batch.count))
    if "sweep" in st.session_state:
        sweep_seed, sweep_count, frame = st.session_state.sweep
        st.caption(f"Graine {sweep_seed} · {sweep_count} phrases par point")
        chart = alt.Chart(frame).mark_line(point=True, strokeWidth=2).encode(x=alt.X("Température:Q", scale=alt.Scale(zero=False)), y=alt.Y("Structure valide (%):Q", scale=alt.Scale(domain=[0, 105])), color=alt.Color("Modèle:N", scale=alt.Scale(range=["#176454", "#bb8839", "#62859a"])), tooltip=list(frame.columns)).properties(height=310)
        st.altair_chart(chart, width="stretch")
    st.markdown("### Les transitions apprises")
    which = st.selectbox("Matrice de transition", ["HMM classique", "HMM à états séparés"])
    matrix_model = lab.plain if which == "HMM classique" else lab.split
    labels, values = matrix_model.transition_matrix()
    matrix = pd.DataFrame([{"État actuel": a, "État suivant": b, "Probabilité": values[i][j]} for i, a in enumerate(labels) for j, b in enumerate(labels)])
    heatmap = alt.Chart(matrix).mark_rect().encode(x=alt.X("État suivant:N", sort=labels), y=alt.Y("État actuel:N", sort=labels), color=alt.Color("Probabilité:Q", scale=alt.Scale(domain=[0, 1], scheme="greens")), tooltip=["État actuel", "État suivant", alt.Tooltip("Probabilité:Q", format=".3f")]).properties(height=350)
    st.altair_chart(heatmap, width="stretch")
    st.caption("Fréquences normalisées, sans lissage. PUNCT n’a aucune transition sortante : la phrase est terminée.")

with real:
    st.subheader("Quand la grammaire rencontre le réel.")
    path = ROOT / "results/ewt_results.json"
    if path.exists():
        results = json.loads(path.read_text())
        provenance = results.get("provenance")
        if provenance:
            st.caption(f"Évaluation exécutée · UD English EWT · révision {provenance['revision'][:12]} · {provenance['train_sentences']:,} phrases d’entraînement / {provenance['test_sentences']:,} de test.")
        else:
            st.info("Ces résultats EWT sont fournis avec le TP. Relancez python -m src.evaluate_real pour produire une évaluation traçable.")
        real_rows = []
        for name, values in results["models"].items():
            real_rows.append({"Modèle": name, "Précision globale": values["accuracy"], "Mots connus": values["known_words"], "Mots inconnus": values["unknown_words"], "Phrase entièrement correcte": values["whole_sentence"]})
        df = pd.DataFrame(real_rows)
        st.dataframe(df.style.format({c: "{:.1%}" for c in df.columns if c != "Modèle"}), hide_index=True, width="stretch")
        m = results["models"]["HMM + Viterbi"]
        c1, c2, c3 = st.columns(3)
        c1.metric("Synthétique · Viterbi", "100 %", help="Précision mesurée sur les 240 phrases synthétiques de test par src.evaluate.")
        c2.metric("Texte réel · Viterbi", f"{m['accuracy']:.1%}")
        c3.metric("Tokens inconnus", f"{m['unknown_share_of_tokens']:.1%}")
        st.markdown("### Pourquoi cet écart ?")
        st.write("Le corpus synthétique utilise six catégories et seize structures régulières. Le texte réel comporte dix-sept catégories, de l’ambiguïté et de nombreux mots inconnus. Le lissage assure une probabilité non nulle, mais favorise parfois les catégories rares pour un mot inconnu. Une bonne structure ne garantit ni le sens ni un bon étiquetage sur un autre domaine.")
        st.write("La validité d’un patron synthétique ne se transpose pas aux milliers de structures différentes d’EWT. Sur texte réel, on mesure la précision des tags et la proportion de phrases entièrement correctes.")
        with st.expander("Confusions les plus fréquentes · référence → prédiction"):
            st.dataframe(pd.DataFrame(results["confusions"], columns=["Référence", "Prédiction", "Occurrences"]), hide_index=True, width="stretch")
        st.download_button("↓ Résultats EWT · JSON", path.read_bytes(), file_name="ewt_results.json", mime="application/json")
    else:
        st.info("Exécutez python -m src.evaluate_real pour télécharger et évaluer le corpus EWT.")
    st.markdown("Source : [Universal Dependencies · English EWT](https://github.com/UniversalDependencies/UD_English-EWT). Annotations sous licence CC BY-SA 4.0. Les mots sont convertis en minuscules ; les tokens multiples et nœuds vides sont ignorés.")

with notebook:
    st.subheader("Un protocole, des limites explicites.")
    st.markdown("**1. Observer.** 1 200 phrases synthétiques, 6 tags et 16 patrons. Les documents sont séparés avant tout comptage : 960 phrases pour entraîner, 240 pour tester.\n\n**2. Prédire.** Le HMM à états séparés devrait mieux respecter la structure : il distingue la position sujet, objet et prépositionnelle.\n\n**3. Mesurer.** Le protocole du rapport utilise 500 phrases par modèle, une graine de 42, et quatre températures : 0,5 ; 1,0 ; 1,5 ; 2,5.\n\n**4. Interpréter.** Structure, paire sujet–verbe et nouveauté sont trois propriétés différentes. Distinct-2 mesure une diversité de bigrammes et varie avec la taille de l’échantillon.")
    st.markdown("### Lire les échecs")
    st.write("**Structure** : le patron grammatical n’appartient pas aux patrons appris. **Sens** : patron valide, couple nom–verbe absent de l’entraînement (indicateur limité). **Mémorisation** : copie exacte d’une phrase d’entraînement. Plusieurs défauts peuvent coexister.")
    st.markdown("### À quoi sert la température ?")
    st.write("Pour un jouet d’écriture : T = 1,5, avec états séparés, pour varier les mots tout en préservant les structures. Pour l’autocomplétion : T = 0,5, avec trigramme, pour privilégier les continuations fréquentes, en acceptant davantage de répétitions et de copies.")
    with st.expander("Inspecter dix phrases d’entraînement"):
        st.dataframe(pd.DataFrame([{"Phrase": " ".join(w), "Tags": " ".join(t)} for w, t in lab.train[:10]]), hide_index=True, width="stretch")
    with st.expander("watch dans les données d’entraînement"):
        examples = [{"Phrase": " ".join(w), "Tags de watch": ", ".join(t[i] for i, word in enumerate(w) if word == "watch")} for w, t in lab.train if "watch" in w]
        st.dataframe(pd.DataFrame(examples), hide_index=True, width="stretch", height=250)
    st.caption("Les textes produits sont générés par un modèle probabiliste. Ils n’expriment aucune intention. Utiliser uniquement des corpus dont on a le droit d’usage ; ne pas entraîner sur des messages privés sans autorisation.")

st.markdown('<div class="lab-footer"><span>chaotic. / Laboratoire de génération probabiliste</span><span>HMM · Viterbi · Trigrammes &nbsp; / &nbsp; Lab 03</span></div>', unsafe_allow_html=True)
