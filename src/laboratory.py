"""Reproducible experiments shared by the UI and automated checks."""
import csv
import io
import random
import re
from dataclasses import dataclass

from src.pipeline import HMM, NGramGenerator, coarse, generation_metrics, load_tagged, sentence_features, split_by_document

MODELS = {"hmm": "HMM classique", "hmm_split": "HMM à états séparés", "ngram": "Trigramme"}
TEMPERATURES = (0.5, 1.0, 1.5, 2.5)


def tokenize(text):
    """Keep punctuation even when attached to a word; corpus is lower-cased."""
    return re.findall(r"\w+(?:['’\-]\w+)*|[^\w\s]", text.lower(), re.UNICODE)


@dataclass
class Batch:
    model: str
    temperature: float
    seed: int
    count: int
    rows: list
    metrics: dict

    def csv_bytes(self):
        stream = io.StringIO(newline="")
        columns = ["id", "sentence", "hidden_states", "tags", "valid", "plausible", "copied", "model", "temperature", "seed"]
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for row in self.rows:
            writer.writerow({**row, "model": self.model, "temperature": self.temperature, "seed": self.seed})
        return stream.getvalue().encode("utf-8-sig")


class Laboratory:
    def __init__(self):
        self.documents = load_tagged()
        self.train, self.test = split_by_document(self.documents)
        self.plain = HMM(self.train)
        self.split = HMM(self.train, split_states=True)
        self.trigram = NGramGenerator([words for words, _ in self.train])
        self.models = {"hmm": self.plain, "hmm_split": self.split, "ngram": self.trigram}
        self.patterns = {" ".join(tags) for _, tags in self.train}
        self.texts = {" ".join(words) for words, _ in self.train}
        self.pairs = {sentence_features(words, tags)[1] for words, tags in self.train}

    def generate(self, model="hmm_split", temperature=1.0, seed=42, count=100):
        if model not in self.models:
            raise ValueError("Modèle inconnu")
        if not 0.3 <= temperature <= 3.0 or not 10 <= count <= 500:
            raise ValueError("Température : 0,3 à 3,0 ; taille : 10 à 500")
        rng = random.Random(seed)
        samples, rows = [], []
        for i in range(count):
            if model == "ngram":
                words = self.trigram.sample_sentence(rng, temperature)
                tags = self.split.viterbi(words)
                states = tags
            else:
                words, states = self.models[model].sample_with_states(rng, temperature)
                tags = coarse(states)
            text = " ".join(words)
            pattern, pair = sentence_features(words, tags)
            samples.append((words, tags))
            rows.append(dict(id=i + 1, sentence=text, hidden_states=" → ".join(states),
                             tags=" ".join(tags), valid=pattern in self.patterns,
                             plausible=pair in self.pairs, copied=text in self.texts))
        return Batch(model, temperature, seed, count, rows, generation_metrics(samples, self.train, self.split))

    def tag(self, text, split=True):
        words = tokenize(text)
        model = self.split if split else self.plain
        return words, model.viterbi(words), sorted({w for w in words if w not in model.vocab})
