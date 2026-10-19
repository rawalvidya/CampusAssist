
import json
import re
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


FAQ_FILE = Path(__file__).resolve().parent / "faqs.json"
MINIMUM_CONFIDENCE = 0.28


def normalize_text(text: str) -> str:
    """Normalize text for more reliable FAQ matching."""
    text = str(text or "").lower().strip()
    text = re.sub(r"[^a-z0-9\s']", " ", text)
    text = re.sub(r"\s+", " ", text)

    replacements = {
        "pls": "please",
        "u": "you",
        "ur": "your",
        "whats": "what is",
        "wanna": "want to",
        "gonna": "going to",
        "marks": "marks grades results",
    }

    words = [replacements.get(word, word) for word in text.split()]
    return " ".join(words)


class FAQEngine:
    """Search a local FAQ knowledge base using TF-IDF similarity."""

    def __init__(self, faq_path=FAQ_FILE):
        self.faq_path = Path(faq_path)
        self.faqs = []
        self.vectorizer = None
        self.matrix = None
        self.documents = []
        self.reload()

    def reload(self):
        """Load FAQs and build the searchable text index."""
        if not self.faq_path.exists():
            raise FileNotFoundError(
                f"FAQ file not found: {self.faq_path}"
            )

        with self.faq_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, dict):
            data = data.get("faqs", data.get("items", []))

        if not isinstance(data, list):
            raise ValueError(
                "faqs.json must contain a list or a 'faqs' list."
            )

        self.faqs = [
            item for item in data
            if isinstance(item, dict)
            and item.get("question")
            and item.get("answer")
        ]

        self.documents = []

        for faq in self.faqs:
            searchable = [
                faq.get("question", ""),
                faq.get("category", ""),
                faq.get("answer", ""),
            ]

            for field in ("variations", "keywords", "tags"):
                values = faq.get(field, [])
                if isinstance(values, str):
                    values = [values]
                if isinstance(values, list):
                    searchable.extend(str(value) for value in values)

            self.documents.append(
                normalize_text(" ".join(searchable))
            )

        if self.documents:
            self.vectorizer = TfidfVectorizer(
                ngram_range=(1, 2),
                sublinear_tf=True,
                strip_accents="unicode",
            )
            self.matrix = self.vectorizer.fit_transform(
                self.documents
            )

    def search(self, question: str):
        """Return the best FAQ match, or None if confidence is low."""
        question = normalize_text(question)

        if not question or self.matrix is None:
            return None

        query_vector = self.vectorizer.transform([question])
        scores = cosine_similarity(
            query_vector, self.matrix
        ).flatten()

        best_index = int(scores.argmax())
        confidence = float(scores[best_index])

        if confidence < MINIMUM_CONFIDENCE:
            return None

        result = dict(self.faqs[best_index])
        result["confidence"] = round(confidence, 3)
        return result

    def answer(self, question: str) -> str:
        """Return an answer string for simple integrations."""
        result = self.search(question)

        if result is None:
            return (
                "I couldn't confidently match that to my current "
                "knowledge base. Could you rephrase your question "
                "or choose one of the student service categories?"
            )

        return str(result["answer"])
