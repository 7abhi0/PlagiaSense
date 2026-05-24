import re
import numpy as np

# A list of common English stopwords to calculate density
STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't", "as", "at",
    "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can", "can't", "cannot",
    "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during", "each", "few",
    "for", "from", "further", "had", "hadn't", "has", "hasn't", "have", "haven't", "having", "he", "he'd", "he'll",
    "he's", "her", "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i", "i'd", "i'll",
    "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself", "let's", "me", "more", "most",
    "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our",
    "ours", "ourselves", "out", "over", "own", "same", "shan't", "she", "she'd", "she'll", "she's", "should",
    "shouldn't", "so", "some", "such", "than", "that", "that's", "the", "their", "theirs", "them", "themselves",
    "then", "there", "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this", "those",
    "through", "to", "too", "under", "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've",
    "were", "weren't", "what", "what's", "when", "when's", "where", "where's", "which", "while", "who", "who's",
    "whom", "why", "why's", "with", "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've",
    "your", "yours", "yourself", "yourselves"
}

def extract_words(text: str) -> list:
    """Extract clean words from text."""
    return re.findall(r'\b[a-zA-Z]+\b', text.lower())

def split_into_sentences(text: str) -> list:
    """Split text into sentences, handling basic abbreviations."""
    text = text.replace('\n', ' ').strip()
    abbreviations = ["e.g.", "i.e.", "Dr.", "Mr.", "Mrs.", "Ms.", "Prof.", "vs.", "al."]
    masked_text = text
    for abbr in abbreviations:
        placeholder = abbr.replace('.', '___DOT___')
        masked_text = re.sub(re.escape(abbr), placeholder, masked_text, flags=re.IGNORECASE)
        
    sentences = re.split(r'(?<=[.!?])\s+', masked_text)
    
    unmasked_sentences = []
    for sent in sentences:
        if sent.strip():
            sent = sent.replace('___DOT___', '.')
            unmasked_sentences.append(sent)
            
    return unmasked_sentences


def extract_stylometric_features(text: str) -> dict:
    """
    Extract key stylometric features from text for classification.
    Returns a dictionary of metrics.
    """
    words = extract_words(text)
    total_words = len(words)
    
    if total_words == 0:
        return {
            "avg_sentence_length": 0.0,
            "sentence_length_variance": 0.0,
            "avg_word_length": 0.0,
            "word_length_variance": 0.0,
            "vocabulary_richness": 0.0,
            "stopword_density": 0.0,
            "comma_density": 0.0,
            "semicolon_density": 0.0,
            "exclamation_density": 0.0,
            "question_density": 0.0
        }
        
    # Split sentences (using simple re.split)
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    sentence_lengths = [len(extract_words(s)) for s in sentences]
    
    if not sentence_lengths:
        sentence_lengths = [0]
        
    avg_sent_len = float(np.mean(sentence_lengths))
    sent_len_var = float(np.var(sentence_lengths))
    
    # Word lengths
    word_lengths = [len(w) for w in words]
    avg_word_len = float(np.mean(word_lengths))
    word_len_var = float(np.var(word_lengths))
    
    # Vocabulary Richness (Type-Token Ratio)
    unique_words = set(words)
    ttr = len(unique_words) / total_words
    
    # Stopword density
    stopword_count = sum(1 for w in words if w in STOPWORDS)
    stopword_density = stopword_count / total_words
    
    # Punctuation counts normalized by word count
    char_len = len(text)
    comma_density = text.count(',') / char_len if char_len > 0 else 0
    semicolon_density = text.count(';') / char_len if char_len > 0 else 0
    exclamation_density = text.count('!') / char_len if char_len > 0 else 0
    question_density = text.count('?') / char_len if char_len > 0 else 0
    
    return {
        "avg_sentence_length": round(avg_sent_len, 2),
        "sentence_length_variance": round(sent_len_var, 2),
        "avg_word_length": round(avg_word_len, 2),
        "word_length_variance": round(word_len_var, 2),
        "vocabulary_richness": round(ttr, 4),
        "stopword_density": round(stopword_density, 4),
        "comma_density": round(comma_density, 5),
        "semicolon_density": round(semicolon_density, 5),
        "exclamation_density": round(exclamation_density, 5),
        "question_density": round(question_density, 5)
    }

def get_stylometry_vector(text: str) -> list:
    """Converts extracted stylometric dictionary to flat list for ML training."""
    feats = extract_stylometric_features(text)
    return [
        feats["avg_sentence_length"],
        feats["sentence_length_variance"],
        feats["avg_word_length"],
        feats["word_length_variance"],
        feats["vocabulary_richness"],
        feats["stopword_density"],
        feats["comma_density"],
        feats["semicolon_density"],
        feats["exclamation_density"],
        feats["question_density"]
    ]
