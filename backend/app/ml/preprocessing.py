import os
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer

def load_reference_corpus(corpus_path: str) -> list:
    if not os.path.exists(corpus_path):
        return []
    with open(corpus_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def get_vectorizer(corpus_path: str, vectorizer_path: str) -> TfidfVectorizer:
    if os.path.exists(vectorizer_path):
        return joblib.load(vectorizer_path)
    corpus = load_reference_corpus(corpus_path)
    if not corpus:
        corpus = ["fallback text to avoid crash"]
    vectorizer = TfidfVectorizer(stop_words='english')
    vectorizer.fit(corpus)
    os.makedirs(os.path.dirname(vectorizer_path), exist_ok=True)
    joblib.dump(vectorizer, vectorizer_path)
    return vectorizer

def get_reference_matrix(corpus_path: str, vectorizer_path: str):
    vectorizer = get_vectorizer(corpus_path, vectorizer_path)
    corpus = load_reference_corpus(corpus_path)
    if not corpus:
        corpus = ["fallback text to avoid crash"]
    return vectorizer.transform(corpus)

def vectorize_text(text: str, vectorizer: TfidfVectorizer):
    return vectorizer.transform([text])
