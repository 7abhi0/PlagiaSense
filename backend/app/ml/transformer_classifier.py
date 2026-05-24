import os
import joblib
import numpy as np
from app.ml.stylometry import get_stylometry_vector, extract_stylometric_features, split_into_sentences
from app.ml.perplexity_analyzer import analyze_perplexity_and_burstiness

_model = None

def get_ensemble_model(model_path: str):
    """Load model lazily."""
    global _model
    if _model is None:
        if os.path.exists(model_path):
            try:
                _model = joblib.load(model_path)
            except Exception as e:
                print(f"Error loading model from {model_path}: {e}")
                _model = None
    return _model

def extract_hybrid_features(text: str, vectorizer=None) -> np.ndarray:
    """Extract and concatenate TF-IDF, stylometric, and perplexity features."""
    # 1. Stylometry (10 features)
    sty_vec = get_stylometry_vector(text)
    
    # 2. Perplexity/Burstiness (6 features)
    perp_info = analyze_perplexity_and_burstiness(text)
    perp_vec = [
        perp_info["burstiness"],
        perp_info["word_entropy"],
        perp_info["char_entropy"],
        perp_info["perplexity_proxy"],
        perp_info["duplicate_bigram_ratio"],
        perp_info["duplicate_trigram_ratio"]
    ]
    
    combined_feats = sty_vec + perp_vec
    
    if vectorizer is not None:
        # TF-IDF vector
        tfidf_vec = vectorizer.transform([text]).toarray()[0]
        # Concatenate TF-IDF and hand-crafted features
        return np.concatenate([tfidf_vec, combined_feats])
        
    return np.array(combined_feats)

def heuristic_ai_prediction(text: str) -> tuple:
    """Fallback heuristic classifier if trained model is missing."""
    perp_info = analyze_perplexity_and_burstiness(text)
    sty_info = extract_stylometric_features(text)
    
    # Heuristics based on common AI text footprints:
    # 1. Low burstiness (very uniform sentence lengths)
    # 2. High stopword density
    # 3. Low perplexity / high repetition ratios
    score = 50.0
    
    if perp_info["burstiness"] < 3.0:
        score += 15
    if sty_info["stopword_density"] > 0.45:
        score += 10
    if perp_info["duplicate_bigram_ratio"] > 0.15:
        score += 15
    if perp_info["word_entropy"] < 4.0:
        score += 10
        
    # Subtract score for human writing signs (high variation/burstiness, rich vocabulary)
    if perp_info["burstiness"] > 10.0:
        score -= 15
    if sty_info["vocabulary_richness"] > 0.70:
        score -= 10
        
    score = max(5.0, min(95.0, score))
    is_ai = score > 50.0
    return is_ai, round(score, 2)

def predict_ai_generated(text: str, model_path: str) -> tuple:
    """
    Predict probability of text being AI generated.
    Returns (is_ai: bool, confidence: float).
    """
    model_data = get_ensemble_model(model_path)
    
    if model_data is None:
        # Fallback to rule-based heuristic
        return heuristic_ai_prediction(text)
        
    try:
        vectorizer = model_data.get("vectorizer")
        classifier = model_data.get("classifier")
        
        feats = extract_hybrid_features(text, vectorizer)
        # Predict probability
        prob = classifier.predict_proba([feats])[0][1] # Probability of class 1 (AI)
        is_ai = prob > 0.5
        confidence = prob * 100 if is_ai else (1 - prob) * 100
        return bool(is_ai), round(float(confidence), 2)
    except Exception as e:
        print(f"Prediction error: {e}")
        return heuristic_ai_prediction(text)

def get_sentence_heatmap(text: str, model_path: str) -> list:
    """
    Analyze sentence-level AI likelihood.
    Returns list of {"text": sentence, "ai_likelihood": score}.
    """
    sentences = split_into_sentences(text)
    heatmap = []
    
    for sent in sentences:
        if len(sent.strip()) < 10:
            heatmap.append({"text": sent, "ai_likelihood": 0.0})
            continue
            
        # Run prediction on single sentence
        _, score = predict_ai_generated(sent, model_path)
        heatmap.append({
            "text": sent,
            "ai_likelihood": score
        })
        
    return heatmap
