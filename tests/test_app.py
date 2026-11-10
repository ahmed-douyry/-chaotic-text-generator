"""UI regressions using Streamlit's own runner; no browser dependency."""
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / 'app.py'


class AppTests(unittest.TestCase):
    def test_generate_analyze_compare_and_empty_filter(self):
        app = AppTest.from_file(str(APP), default_timeout=60).run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.metric), 7)
        self.assertEqual(app.session_state['batch'].count, 100)
        # Generation form; metrics must belong to the selected model.
        next(v for v in app.selectbox if v.label == 'Modèle génératif').select('hmm')
        next(b for b in app.button if b.label.startswith('Générer le lot')).click().run()
        self.assertEqual(app.session_state['batch'].model, 'hmm')
        self.assertFalse(app.exception)
        # Unknown and empty input are both normal UI states.
        app.text_area[0].input('the astronaut dances!')
        next(b for b in app.button if b.label.startswith('Analyser')).click().run()
        self.assertTrue(app.warning)
        self.assertFalse(app.exception)
        app.text_area[0].input('   ')
        next(b for b in app.button if b.label.startswith('Analyser')).click().run()
        self.assertEqual(app.session_state['tagged'], ([], [], []))
        next(b for b in app.button if b.label == 'Comparer les trois modèles').click().run()
        self.assertEqual(len(app.session_state['comparison']), 3)
        next(b for b in app.button if b.label == 'Calculer la courbe de température').click().run()
        self.assertEqual(len(app.session_state['sweep'][2]), 12)
        self.assertFalse(app.exception)
        next(v for v in app.selectbox if v.label == 'Modèle génératif').select('hmm_split')
        next(b for b in app.button if b.label.startswith('Générer le lot')).click().run()
        app.radio[0].set_value('Structure invalide').run()
        self.assertTrue(any('Aucune phrase' in v.value for v in app.info))
        self.assertFalse(app.exception)


if __name__ == '__main__':
    unittest.main()
