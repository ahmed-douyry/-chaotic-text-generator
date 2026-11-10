import csv
import io
import itertools
import math
import unittest

from src.laboratory import Laboratory, MODELS, tokenize
from src.pipeline import HMM, coarse, generation_metrics


class LaboratoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lab = Laboratory()

    def test_document_split_and_held_out_accuracy(self):
        self.assertEqual((len(self.lab.train), len(self.lab.test), len(self.lab.patterns)), (960, 240, 16))
        correct_watch = 0
        for words, gold in self.lab.test:
            self.assertEqual(self.lab.plain.viterbi(words), gold)
            self.assertEqual(self.lab.split.viterbi(words), gold)
            correct_watch += words.count('watch')
        self.assertEqual(correct_watch, 37)

    def test_batches_reproduce_protocol_and_preserve_states(self):
        expected = {'hmm': .162, 'hmm_split': 1., 'ngram': .57}
        for key in MODELS:
            batch = self.lab.generate(key, 1., 42, 500)
            self.assertEqual(batch.metrics['valid_tag_pattern'], expected[key])
            self.assertEqual(batch.rows, self.lab.generate(key, 1., 42, 500).rows)
            samples = [(r['sentence'].split(), r['tags'].split()) for r in batch.rows]
            self.assertEqual(batch.metrics, generation_metrics(samples, self.lab.train, self.lab.split))
            self.assertEqual(sum(r['copied'] for r in batch.rows), round(500 * (1 - batch.metrics['novel_sentences'])))
            for row in batch.rows:
                self.assertEqual(len(row['sentence'].split()), len(row['tags'].split()))
                self.assertEqual(coarse(row['hidden_states'].split(' → ')), row['tags'].split())

    def test_export_roundtrip(self):
        batch = self.lab.generate('hmm_split', 1., 42, 10)
        rows = list(csv.DictReader(io.StringIO(batch.csv_bytes().decode('utf-8-sig'))))
        self.assertEqual(len(rows), 10)
        self.assertEqual(rows[0]['sentence'], batch.rows[0]['sentence'])
        self.assertEqual(rows[0]['model'], 'hmm_split')
        self.assertIn('hidden_states', rows[0])

    def test_tokenization_empty_and_unknown_words(self):
        self.assertEqual(tokenize('THE farmers watch the birds.'), ['the', 'farmers', 'watch', 'the', 'birds', '.'])
        self.assertEqual(self.lab.tag('   '), ([], [], []))
        words, tags, unknown = self.lab.tag('the astronaut dances!')
        self.assertEqual(len(words), len(tags))
        self.assertEqual(unknown, ['!', 'astronaut', 'dances'])
        words, tags, unknown = self.lab.tag('<script>alert(1)</script>')
        self.assertEqual(len(words), len(tags))
        self.assertTrue(unknown)

    def test_viterbi_matches_exhaustive_log_probability(self):
        model = HMM([(['a', 'b'], ['A', 'B']), (['b', 'a'], ['B', 'A']), (['a', 'a'], ['A', 'A'])])
        for words in (['a', 'b', 'a'], ['unknown', 'b'], ['a']):
            def probability(path):
                return math.log(model.p_start(path[0])) + sum(math.log(model.p_emit(t, w)) for t, w in zip(path, words)) + sum(math.log(model.p_trans(a, b)) for a, b in zip(path, path[1:]))
            expected = max(itertools.product(model.tags, repeat=len(words)), key=probability)
            self.assertEqual(model.viterbi(words), list(expected))

    def test_parameter_validation(self):
        for args in [('bad', 1., 42, 10), ('hmm', 0., 42, 10), ('hmm', 1., 42, 501)]:
            with self.assertRaises(ValueError):
                self.lab.generate(*args)


if __name__ == '__main__':
    unittest.main()
