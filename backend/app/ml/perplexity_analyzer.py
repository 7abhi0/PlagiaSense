import math
from collections import Counter
import re
from app.ml.stylometry import split_into_sentences, extract_words

def calculate_shannon_entropy(text: str) -> float:
    """Calculate character-level Shannon entropy (measures predictability)."""
    if not text:
        return 0.0
    counter = Counter(text)
    total = len(text)
    entropy = 0.0
    for count in counter.values():
        p = count / total
        entropy -= p * math.log2(p)
    return round(entropy, 4)

def calculate_word_entropy(words: list) -> float:
    """Calculate word-level entropy (richness/predictability)."""
    if not words:
        return 0.0
    counter = Counter(words)
    total = len(words)
    entropy = 0.0
    for count in counter.values():
        p = count / total
        entropy -= p * math.log2(p)
    return round(entropy, 4)

def compute_perplexity_proxy(text: str) -> float:
    """
    Compute a fast proxy for perplexity using word-level bigrams.
    In real NLP, perplexity is calculated via pre-trained model cross-entropy.
    Here we compute internal text predictability using bigram distributions.
    Low scores mean highly repetitive/predictable structures (typical of AI).
    """
    words = extract_words(text)
    if len(words) < 5:
        return 1.0
        
    bigrams = [(words[i], words[i+1]) for i in range(len(words)-1)]
    bigram_counts = Counter(bigrams)
    unigram_counts = Counter(words)
    
    # Calculate average log-probability of bigrams
    log_prob_sum = 0.0
    for bg, count in bigram_counts.items():
        w1, w2 = bg
        # Probability of w2 given w1
        p_w2_given_w1 = count / unigram_counts[w1]
        log_prob_sum += math.log2(p_w2_given_w1)
        
    avg_log_prob = log_prob_sum / len(bigrams)
    # Perplexity proxy is 2^(-avg_log_prob)
    perplexity = 2 ** (-avg_log_prob)
    return round(perplexity, 2)

def compute_repetition_metrics(text: str) -> dict:
    """Calculate duplicate n-gram metrics (AI tends to repeat phrases)."""
    words = extract_words(text)
    total_words = len(words)
    
    if total_words < 10:
        return {
            "duplicate_trigram_ratio": 0.0,
            "duplicate_bigram_ratio": 0.0
        }
        
    # Bigrams
    bigrams = [" ".join(words[i:i+2]) for i in range(total_words-1)]
    bigram_counter = Counter(bigrams)
    dup_bigrams = sum(count - 1 for count in bigram_counter.values() if count > 1)
    
    # Trigrams
    trigrams = [" ".join(words[i:i+3]) for i in range(total_words-2)]
    trigram_counter = Counter(trigrams)
    dup_trigrams = sum(count - 1 for count in trigram_counter.values() if count > 1)
    
    return {
        "duplicate_bigram_ratio": round(dup_bigrams / len(bigrams), 4),
        "duplicate_trigram_ratio": round(dup_trigrams / len(trigrams), 4)
    }

def analyze_perplexity_and_burstiness(text: str) -> dict:
    """
    Analyze text burstiness and perplexity.
    AI writing has lower burstiness (less variance in sentence structure)
    and lower perplexity (more predictable, uniform transitions).
    """
    sentences = split_into_sentences(text)
    sentence_lengths = [len(extract_words(s)) for s in sentences if s.strip()]
    
    if not sentence_lengths:
        sentence_lengths = [0]
        
    mean_len = np_mean = sum(sentence_lengths) / len(sentence_lengths)
    # Standard deviation of sentence lengths is the burstiness
    variance = sum((x - mean_len) ** 2 for x in sentence_lengths) / len(sentence_lengths)
    burstiness = math.sqrt(variance)
    
    words = extract_words(text)
    word_ent = calculate_word_entropy(words)
    char_ent = calculate_shannon_entropy(text)
    perp_proxy = compute_perplexity_proxy(text)
    rep_metrics = compute_repetition_metrics(text)
    
    return {
        "burstiness": round(burstiness, 2),
        "word_entropy": word_ent,
        "char_entropy": char_ent,
        "perplexity_proxy": perp_proxy,
        "duplicate_bigram_ratio": rep_metrics["duplicate_bigram_ratio"],
        "duplicate_trigram_ratio": rep_metrics["duplicate_trigram_ratio"]
    }
