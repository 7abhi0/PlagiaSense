import numpy as np

# Try to load SentenceTransformer, fall back to TF-IDF Sentence Encoder if PyTorch DLL errors occur
_model = None
use_fallback = False

try:
    from sentence_transformers import SentenceTransformer
except (ImportError, OSError) as e:
    print(f"Warning: SentenceTransformers failed to import ({e}). Switching to robust TF-IDF sentence encoder fallback.")
    use_fallback = True

# Fallback Encoder using TF-IDF for sentence-level semantic representations
class TFIDF_SentenceEncoderFallback:
    def __init__(self):
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words='english')
        # Seed with some general vocabulary
        self.vectorizer.fit([
            "artificial intelligence and machine learning in modern computer science",
            "plagiarism detection algorithms search the web and compare sentence similarities",
            "the quick brown fox jumps over the lazy dog",
            "academic research essays and scientific studies require original references"
        ])
        
    def encode(self, sentences: list, show_progress_bar: bool = False) -> np.ndarray:
        """
        Return TF-IDF vectors with a *stable* feature dimension across calls.

        IMPORTANT: Do NOT re-fit a TF-IDF vectorizer per request, otherwise different
        sentences produce different vocabulary sizes -> inconsistent embedding shapes,
        which breaks cosine_similarity.
        """
        try:
            return self.vectorizer.transform(sentences).toarray()
        except Exception:
            # Absolute fallback (still may be inconsistent, but should rarely happen)
            from sklearn.feature_extraction.text import TfidfVectorizer
            temp_vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words='english')
            temp_vectorizer.fit(sentences)
            return temp_vectorizer.transform(sentences).toarray()

def get_transformer_model():
    global _model, use_fallback
    if _model is None:
        if use_fallback:
            print("Loading Fallback TFIDF Sentence Encoder...")
            _model = TFIDF_SentenceEncoderFallback()
        else:
            try:
                print("Loading SentenceTransformer model 'all-MiniLM-L6-v2'...")
                _model = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception as e:
                print(f"Error loading SentenceTransformer: {e}. Switching to TF-IDF sentence encoder fallback.")
                use_fallback = True
                _model = TFIDF_SentenceEncoderFallback()
    return _model

class EmbeddingCache:
    def __init__(self):
        self.cache = {}

    def get_embeddings(self, sentences: list) -> np.ndarray:
        """
        Encode a list of sentences, caching them to avoid redundant computation.
        Returns a numpy array of embeddings.
        """
        model = get_transformer_model()
        results = []
        to_encode = []
        indices_to_encode = []
        
        # Check cache
        for idx, sentence in enumerate(sentences):
            if sentence in self.cache:
                results.append(self.cache[sentence])
            else:
                results.append(None)
                to_encode.append(sentence)
                indices_to_encode.append(idx)
                
        # Encode missing
        if to_encode:
            print(f"Encoding {len(to_encode)} new sentences...")
            encoded = model.encode(to_encode, show_progress_bar=False)
            for idx, emb in zip(indices_to_encode, encoded):
                self.cache[sentences[idx]] = emb
                results[idx] = emb
                
        return np.array(results)

# Global embedding cache
embedding_cache = EmbeddingCache()
