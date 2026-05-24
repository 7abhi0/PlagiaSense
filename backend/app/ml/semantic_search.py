import re
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from app.ml.embeddings import embedding_cache
from app.utils.web_scraper import get_web_candidates

def split_into_sentences(text: str) -> list:
    """Split text into sentences, handling basic abbreviations."""
    # Simplified sentence tokenization
    text = text.replace('\n', ' ').strip()
    # Mask common abbreviations to prevent incorrect splitting
    abbreviations = ["e.g.", "i.e.", "Dr.", "Mr.", "Mrs.", "Ms.", "Prof.", "vs.", "al."]
    masked_text = text
    for abbr in abbreviations:
        # Replace dot temporarily with unique token
        placeholder = abbr.replace('.', '___DOT___')
        masked_text = re.sub(re.escape(abbr), placeholder, masked_text, flags=re.IGNORECASE)
        
    sentences = re.split(r'(?<=[.!?])\s+', masked_text)
    
    # Unmask abbreviations
    unmasked_sentences = []
    for sent in sentences:
        if sent.strip():
            sent = sent.replace('___DOT___', '.')
            unmasked_sentences.append(sent)
            
    return unmasked_sentences

def perform_semantic_plagiarism_scan(text: str, google_key: str = None) -> dict:
    """
    Perform a web-scale semantic plagiarism scan by checking sentences
    against the web and comparing sentence embeddings.
    """
    input_sentences = split_into_sentences(text)
    if not input_sentences:
        return {
            "plagiarism_score": 0.0,
            "matches": [],
            "highlighted_sentences": []
        }
        
    # Generate search queries for the longest 3 sentences (most likely to contain copy-paste footprints)
    sorted_sentences = sorted(input_sentences, key=lambda s: len(s), reverse=True)
    search_queries = [s for s in sorted_sentences[:3] if len(s) > 30]
    
    # Retrieve web candidates (dict: url -> cleaned text)
    web_candidates = get_web_candidates(search_queries, max_pages=3)
    
    # If no web candidates found, return 0% plagiarism
    if not web_candidates:
        return {
            "plagiarism_score": 0.0,
            "matches": [],
            "highlighted_sentences": [{"text": s, "similarity": 0.0, "category": "unique"} for s in input_sentences]
        }
        
    # Extract all sentences from scraped pages
    all_scraped_sentences = []
    sentence_sources = [] # list of (url, sentence)
    
    for url, body_text in web_candidates.items():
        scraped_sents = split_into_sentences(body_text)
        for s in scraped_sents:
            if len(s.strip()) > 15:
                all_scraped_sentences.append(s)
                sentence_sources.append((url, s))
                
    if not all_scraped_sentences:
        return {
            "plagiarism_score": 0.0,
            "matches": [],
            "highlighted_sentences": [{"text": s, "similarity": 0.0, "category": "unique"} for s in input_sentences]
        }
        
    # Calculate embeddings
    input_embeddings = embedding_cache.get_embeddings(input_sentences)
    scraped_embeddings = embedding_cache.get_embeddings(all_scraped_sentences)
    
    # Compute similarity matrix (len(input) x len(scraped))
    sim_matrix = cosine_similarity(input_embeddings, scraped_embeddings)
    
    matches = []
    highlighted_sentences = []
    plagiarized_count = 0
    total_len = sum(len(s) for s in input_sentences)
    weighted_plagiarism_sum = 0.0
    
    for idx, sentence in enumerate(input_sentences):
        # Find the best match for this sentence in all scraped content
        max_idx = np.argmax(sim_matrix[idx])
        max_score = float(sim_matrix[idx][max_idx])
        
        category = "unique"
        if max_score >= 0.90:
            category = "exact"
            plagiarized_count += 1
            weighted_plagiarism_sum += len(sentence)
        elif max_score >= 0.70:
            category = "paraphrased"
            plagiarized_count += 1
            weighted_plagiarism_sum += len(sentence) * 0.7
        elif max_score >= 0.55:
            category = "weak_paraphrased"
            weighted_plagiarism_sum += len(sentence) * 0.4
            
        url, matched_text = sentence_sources[max_idx]
        
        if category != "unique":
            matches.append({
                "original_text": sentence,
                "matched_text": matched_text,
                "similarity_score": round(max_score * 100, 2),
                "source_url": url,
                "category": category
            })
            
        highlighted_sentences.append({
            "text": sentence,
            "similarity": round(max_score * 100, 2),
            "category": category,
            "source_url": url if category != "unique" else None,
            "matched_text": matched_text if category != "unique" else None
        })
        
    # Calculate overall score weighted by sentence lengths
    plagiarism_score = round((weighted_plagiarism_sum / total_len) * 100, 2) if total_len > 0 else 0.0
    # Bound to 100% max
    plagiarism_score = min(plagiarism_score, 100.0)
    
    return {
        "plagiarism_score": plagiarism_score,
        "matches": matches,
        "highlighted_sentences": highlighted_sentences
    }
