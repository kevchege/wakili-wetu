import re
import os
from typing import List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

LEGAL_DOCS_PATH = os.environ.get("LEGAL_DOCS_PATH", "legal_docs")

class LocalLegalEngine:
    def __init__(self):
        self.documents = []
        self.sources = []
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.doc_vectors = None
        self._load_documents()

    def _load_documents(self):
        """Load legal texts from folder."""
        for file in os.listdir(LEGAL_DOCS_PATH):
            if file.endswith(".txt"):
                path = os.path.join(LEGAL_DOCS_PATH, file)
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()
                    chunks = self._chunk_text(text)
                    for chunk in chunks:
                        self.documents.append(chunk)
                        self.sources.append(file)

        if self.documents:
            self.doc_vectors = self.vectorizer.fit_transform(self.documents)

    def _chunk_text(self, text: str) -> List[str]:
        """Split legal text into usable paragraphs."""
        parts = re.split(r"\n\s*\n", text)
        return [p.strip() for p in parts if len(p.strip()) > 120]

    def search(self, query: str, k: int = 3) -> List[Tuple[str, str]]:
        """Return top-k relevant legal passages."""
        if not self.documents:
            return []

        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.doc_vectors)[0]
        top_idx = scores.argsort()[-k:][::-1]

        return [(self.documents[i], self.sources[i]) for i in top_idx]

engine = LocalLegalEngine()

def generate_legal_answer(contexts, question):
    """Create human-like legal explanation WITHOUT AI."""

    if not contexts:
        return "No relevant legal material found.", []

    explanation = []
    cites = set()

    explanation.append("Based on the provided legal materials:")

    for text, source in contexts:
        first_sentence = re.split(r'(?<=[.!?])\s+', text)[0]
        explanation.append(f"- {first_sentence}")
        cites.add(source)

    explanation.append("\nInterpretation:")
    explanation.append(
        "This means the law applies as described above. "
        "The outcome depends on the specific facts, but the cited provisions guide the decision."
    )

    return "\n".join(explanation), list(cites)