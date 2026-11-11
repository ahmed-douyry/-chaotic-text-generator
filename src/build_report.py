"""Build the one-page summary and illustrated report from measured results.

Run after both evaluations: python -m src.build_report
Requires the optional report dependencies in requirements-report.txt.
"""
import csv
from copy import deepcopy
import html
import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak, Image

from src.laboratory import Laboratory, MODELS

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'report'
GREEN = colors.HexColor('#176454')
INK = colors.HexColor('#25342e')


def main():
    OUT.mkdir(exist_ok=True)
    metrics = json.loads((ROOT / 'results/metrics.json').read_text())
    real = json.loads((ROOT / 'results/ewt_results.json').read_text())
    lab = Laboratory()
    generated = lab.generate('hmm_split', 1., 42, 500)
    good = next(r for r in generated.rows if r['valid'] and r['plausible'] and not r['copied'] and r['sentence'].startswith('the children eat the bread'))
    bad = next(r for r in generated.rows if r['valid'] and not r['plausible'])
    gen_header = ['Modèle', 'Structure valide', 'Sujet–verbe', 'Nouveauté', 'Distinct-2']
    gen_rows = []
    for key, label in MODELS.items():
        m = metrics['generation'][key]['1.0']
        gen_rows.append([label, f"{m['valid_tag_pattern']:.1%}", f"{m['plausible_subject_verb']:.1%}", f"{m['novel_sentences']:.1%}", f"{m['distinct_2']:.3f}"])
    real_header = ['Corpus / modèle', 'Précision', 'Connus', 'Inconnus', 'Phrase correcte']
    real_rows = [['Synthétique / HMM + Viterbi', f"{metrics['viterbi_acc']['plain states']:.1%}", '100.0%', 'sans OOV', '100.0%']]
    for key in ('most-frequent tag', 'HMM + Viterbi'):
        m = real['models'][key]
        real_rows.append(['EWT / ' + ('tag majoritaire' if key == 'most-frequent tag' else key), *[f"{m[k]:.2%}" for k in ['accuracy', 'known_words', 'unknown_words', 'whole_sentence']]])
    problem = 'Générer une phrase ne suffit pas à prouver sa qualité : il faut mesurer structure, plausibilité et diversité. Le HMM estime des probabilités de départ, de transition et d’émission par comptage. Le trigramme utilise les deux mots précédents avec repli. Une application Streamlit compare les trois générateurs, affiche leurs états et exporte les lots. Viterbi retrouve les tags en espace logarithmique, avec lissage add-k (k = 0,01).'
    protocol = 'Protocole : séparation par document, 960 phrases d’entraînement et 240 de test ; 500 phrases générées par modèle et température, graine 42. Hypothèse : les états séparés devraient maximiser la validité structurelle. Les 10 premières phrases et les occurrences de watch sont consultables dans l’application ; watch est correctement étiqueté 37/37 fois au test.'
    split = 'Le HMM classique oublie si un nom est sujet ou objet : après NOUN, les probabilités VERB ≈ 0,39, PREP ≈ 0,22 et PUNCT ≈ 0,39 se mélangent. Les états S/O/P séparent ces rôles et restaurent les 16 patrons de la petite grammaire (100 % à T = 1). Ils ne modélisent pas le sens : seulement 60,6 % des couples sujet–verbe sont observés, contre 76,0 % pour le trigramme. Nouveauté et distinct-2 ne prouvent ni créativité ni correction.'
    temperatures = 'Jouet d’écriture : HMM à états séparés, T = 1,5 pour varier les mots en gardant une structure valide. Autocomplétion : trigramme, T = 0,5 pour privilégier les suites fréquentes ; sa validité baisse de 63,6 % à 44,2 % entre T = 0,5 et 2,5, tandis que distinct-2 augmente entre ces extrêmes (0,095 → 0,112), sans monotonie stricte. Le prix d’une température basse est davantage de répétitions et de copies.'
    examples = f'Exemple satisfaisant : « {good["sentence"]} » — patron valide, couple observé et phrase nouvelle ; cela reste un indicateur limité du sens. Limite sémantique : « {bad["sentence"]} » — patron valide mais couple sujet–verbe non observé (ce qui ne prouve pas une absurdité) : les émissions ne sont pas conditionnées par le sujet. Structure : un HMM classique peut terminer après le sujet. Mémorisation : « the girls leave the park . » est recopiée par le trigramme (T = 0,5).'
    m = real['models']['HMM + Viterbi']
    baseline = real['models']['most-frequent tag']
    interpretation = f'Le test réel utilise 12 544 phrases d’entraînement et 2 077 de test, 17 tags et 10 359 patrons, contre 6 tags et 16 patrons synthétiques. Les mots inconnus représentent {m["unknown_share_of_tokens"]:.1%} des tokens. Le HMM gagne {(m["accuracy"]-baseline["accuracy"])*100:.2f} points sur la baseline, mais ne réussit que {m["whole_sentence"]:.1%} des phrases entières. Pour un inconnu, k/(effectif du tag + kV) favorise les tags rares (X, INTJ) : la précision OOV reste faible. La métrique des 16 patrons ne se transpose pas à EWT. La mesure actuelle ({m["accuracy"]:.2%}, contre 88,1 % indicatif dans le guide) dépend de la révision du corpus ; le modèle ne garantit rien sur un autre domaine.'
    sections = [('Problème et solution', problem), ('Protocole et hypothèse', protocol), ('États séparés : apport et limites', split), ('Température et usages', temperatures), ('Exemples et causes des échecs', examples), ('Du synthétique au réel', interpretation)]
    def french_number(value):
        return value.replace('.', ',').replace('%', ' %')

    gen_rows = [[row[0], *map(french_number, row[1:])] for row in gen_rows]
    real_rows = [[row[0], *map(french_number, row[1:])] for row in real_rows]

    def md_table(header, rows):
        return '\n'.join(['| ' + ' | '.join(header) + ' |', '| ' + ' | '.join(['---']*len(header)) + ' |', *['| ' + ' | '.join(r) + ' |' for r in rows]])
    markdown = '# Lab 03 — Chaotic Text Generator\n\nAhmed Douyry · Master SDIA · 11 novembre 2026\n\n'
    for title, body in sections:
        markdown += f'## {title}\n\n{body}\n\n'
        if title == 'Protocole et hypothèse':
            markdown += md_table(gen_header, gen_rows) + '\n\n'
        if title == 'Du synthétique au réel':
            markdown += md_table(real_header, real_rows) + '\n\n'
    provenance = real.get('provenance', {})
    source = f"Source EWT : https://github.com/UniversalDependencies/UD_English-EWT · CC BY-SA 4.0 · révision {provenance.get('revision', 'fournie')}. Les résultats sont relatifs aux corpus ; ils ne mesurent pas la qualité de l’anglais réel."
    markdown += source + '\n'
    figures = [
        ('01-generation-desktop.png', 'Génération et mesure du lot',
         'HMM à états séparés, T = 1,0, graine 42, 100 phrases. La capture montre les quatre indicateurs, les filtres, les états cachés et l’export CSV. Les scores (100 % de structures valides, 65 % de couples observés, 99 % de nouveauté, distinct-2 = 0,332) portent sur ce lot de démonstration ; le tableau de synthèse utilise 500 phrases. Distinct-2 dépend notamment de la taille du lot.'),
        ('02-viterbi-desktop.png', 'Décodage Viterbi mot par mot',
         'Phrase analysée : « the farmers watch the birds. ». Le mot ambigu watch reçoit ici le tag VERB ; la ponctuation est séparée des mots. Le tableau indique l’appartenance au vocabulaire. Cette capture illustre une phrase connue, pas le traitement des inconnus : celui-ci est vérifié séparément par les tests automatisés.'),
    ]
    markdown += '\n## Annexe — Captures de l’application\n\n'
    for index, (filename, title, caption) in enumerate(figures, 1):
        markdown += f'### Figure {index} — {title}\n\n![{title}](../screenshots/{filename})\n\n{caption}\n\n'
    (OUT / 'rapport.md').write_text(markdown.rstrip() + '\n', encoding='utf-8')
    body_style = ParagraphStyle('body', fontName='Helvetica', fontSize=8.3, leading=11.1, textColor=INK, spaceAfter=5)
    heading_style = ParagraphStyle('heading', parent=body_style, fontName='Helvetica-Bold', fontSize=9.3, leading=12, textColor=GREEN, spaceBefore=6, spaceAfter=3)
    title_style = ParagraphStyle('title', parent=body_style, fontName='Times-Roman', fontSize=26, leading=30, spaceAfter=7)
    small_style = ParagraphStyle('small', parent=body_style, fontSize=6.6, leading=8.4, textColor=colors.HexColor('#5d6e63'))
    story = [Paragraph('CHAOTIC. / NLP — LAB 03', heading_style), Paragraph('Générer, mesurer, comprendre.', title_style), Paragraph('Ahmed Douyry · Master SDIA · 11 novembre 2026', small_style), Spacer(1, 3*mm)]
    def add_table(header, rows, widths):
        table_style = ParagraphStyle('cell', parent=body_style, fontSize=7.1, leading=9, spaceAfter=0)
        cells = [[Paragraph(html.escape(x), table_style) for x in row] for row in [header] + rows]
        table = Table(cells, colWidths=widths, hAlign=TA_LEFT)
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e3eadc')), ('TEXTCOLOR',(0,0),(-1,0),GREEN), ('LINEBELOW',(0,0),(-1,0),.6,GREEN), ('LINEBELOW',(0,1),(-1,-1),.25,colors.HexColor('#d8dfd2')), ('TOPPADDING',(0,0),(-1,-1),5), ('BOTTOMPADDING',(0,0),(-1,-1),5), ('VALIGN',(0,0),(-1,-1),'TOP')]))
        story.extend([table, Spacer(1, 2*mm)])
    for title, body in sections:
        story.append(KeepTogether([Paragraph(title, heading_style), Paragraph(html.escape(body), body_style)]))
        if title == 'Protocole et hypothèse':
            add_table(gen_header, gen_rows, [53*mm, 31*mm, 28*mm, 28*mm, 28*mm])
        if title == 'Du synthétique au réel':
            add_table(real_header, real_rows, [57*mm, 25*mm, 25*mm, 25*mm, 36*mm])
    story.extend([Spacer(1, 2*mm), Paragraph(html.escape(source), small_style)])
    def decorate(canvas, doc):
        canvas.setStrokeColor(GREEN)
        canvas.line(21*mm, 283*mm, 189*mm, 283*mm)
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(GREEN)
        canvas.drawString(21*mm, 12*mm, 'CHAOTIC / Rapport expérimental')
        canvas.drawRightString(189*mm, 12*mm, str(doc.page))
    def build_pdf(filename, content):
        SimpleDocTemplate(
            str(OUT / filename), pagesize=(210*mm, 297*mm),
            rightMargin=21*mm, leftMargin=21*mm, topMargin=18*mm,
            bottomMargin=18*mm, title='Lab 03 — Chaotic Text Generator',
            author='Ahmed Douyry',
        ).build(content, onFirstPage=decorate, onLaterPages=decorate)

    build_pdf('rapport_synthese.pdf', deepcopy(story))
    for index, (filename, title, caption) in enumerate(figures, 1):
        screenshot = Image(str(ROOT / 'screenshots' / filename))
        screenshot.drawHeight *= (168*mm / screenshot.drawWidth)
        screenshot.drawWidth = 168*mm
        story.extend([
            PageBreak(), Paragraph('ANNEXE / APPLICATION', heading_style),
            Paragraph(title, title_style),
            Paragraph(f'Figure {index} · Capture de l’application Streamlit', small_style),
            Spacer(1, 8*mm), screenshot, Spacer(1, 6*mm),
            Paragraph(html.escape(caption), body_style),
        ])
    build_pdf('rapport.pdf', story)
    # Classify every sentence from the supplied failure file, preserving multiple defects.
    failure_rows = []
    for line in (ROOT / 'results/failures.txt').read_text().splitlines():
        if not line.startswith('  - '):
            continue
        sentence = line[4:]
        words = sentence.split()
        tags = lab.split.viterbi(words)
        pattern = ' '.join(tags)
        pair = next(((w, v) for w, t in zip(words, tags) if t == 'NOUN' for v, u in zip(words, tags) if u == 'VERB'), (None, None))
        defects = []
        if pattern not in lab.patterns:
            defects.append('structure')
        if pair not in lab.pairs:
            defects.append('sens (couple non observé)')
        if sentence in lab.texts:
            defects.append('mémorisation')
        failure_rows.append({'phrase': sentence, 'tags': pattern, 'classe': '; '.join(defects) or 'aucun défaut détecté par les métriques'})
    with open(OUT / 'failures_classified.csv', 'w', encoding='utf-8-sig', newline='') as output:
        writer = csv.DictWriter(output, fieldnames=['phrase', 'tags', 'classe'])
        writer.writeheader()
        writer.writerows(failure_rows)
    print('Created report/rapport.pdf, report/rapport_synthese.pdf, report/rapport.md, report/failures_classified.csv')


if __name__ == '__main__':
    main()
