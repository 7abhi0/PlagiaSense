import os
import re
import time

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

def chunk_text(text, chunk_size: int = 400, overlap: int = 80) -> list:
    """Split text into overlapping chunks by word count."""
    # Normalize whitespace
    text = (text or "").replace("\n", " ")
    # Sentence-ish split. (We keep your original approach.)
    sentences = text.split(". ")

    chunks = []
    current_chunk = []
    current_len = 0

    def chunk_len(words_list):
        return sum(len(s.split()) for s in words_list)

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        words = sentence.split()
        if current_len + len(words) > chunk_size:
            if current_chunk:
                chunks.append(". ".join(current_chunk).strip() + ".")

            # Keep last overlap words for context continuity
            overlap_sentences = []
            overlap_len = 0
            for s in reversed(current_chunk):
                overlap_len += len(s.split())
                if overlap_len >= overlap:
                    break
                overlap_sentences.insert(0, s)

            current_chunk = overlap_sentences
            current_len = chunk_len(current_chunk)

        current_chunk.append(sentence)
        current_len += len(words)

    if current_chunk:
        chunks.append(". ".join(current_chunk).strip())

    return [c for c in chunks if len(c.strip()) > 50]


def _scan_chunk_semantic(
    chunk: str,
    *,
    max_input_sentences: int = 45,
    max_search_queries: int = 3,
    max_pages: int = 3,
    max_scraped_sentences: int = 220,
) -> dict:
    """
    Web-scale semantic scan logic for a chunk with hard memory/time caps.

    Key stability changes:
    - cap number of input sentences used for embedding/similarity
    - cap number of scraped sentences used for cosine similarity
    """
    input_sentences = split_into_sentences(chunk)
    if not input_sentences:
        return {
            "plagiarism_score": 0.0,
            "matches": [],
            "highlighted_sentences": [],
        }

    # Hard cap to control cosine similarity matrix size
    if len(input_sentences) > max_input_sentences:
        input_sentences = sorted(input_sentences, key=lambda s: len(s), reverse=True)[
            :max_input_sentences
        ]

    # Generate search queries for the longest N sentences
    sorted_sentences = sorted(input_sentences, key=lambda s: len(s), reverse=True)
    search_queries = [s for s in sorted_sentences[:max_search_queries] if len(s) > 30]

    if not search_queries:
        return {
            "plagiarism_score": 0.0,
            "matches": [],
            "highlighted_sentences": [
                {"text": s, "similarity": 0.0, "category": "unique"}
                for s in input_sentences
            ],
        }

    web_candidates = get_web_candidates(
        search_queries,
        max_pages=max_pages,
        max_candidates_total=max_pages,
        max_total_chars=12_000,
        per_page_max_chars=1800,
    )

    if not web_candidates:
        return {
            "plagiarism_score": 0.0,
            "matches": [],
            "highlighted_sentences": [
                {"text": s, "similarity": 0.0, "category": "unique"}
                for s in input_sentences
            ],
        }

    all_scraped_sentences = []
    sentence_sources = []  # (url, sentence)

    for url, body_text in web_candidates.items():
        if not body_text:
            continue
        scraped_sents = split_into_sentences(body_text)
        for s in scraped_sents:
            if len(s.strip()) > 15:
                all_scraped_sentences.append(s)
                sentence_sources.append((url, s))
            if len(all_scraped_sentences) >= max_scraped_sentences:
                break
        if len(all_scraped_sentences) >= max_scraped_sentences:
            break

    if not all_scraped_sentences:
        return {
            "plagiarism_score": 0.0,
            "matches": [],
            "highlighted_sentences": [
                {"text": s, "similarity": 0.0, "category": "unique"}
                for s in input_sentences
            ],
        }

    # Embed fewer sentences to reduce RAM/CPU
    input_embeddings = embedding_cache.get_embeddings(input_sentences)
    scraped_embeddings = embedding_cache.get_embeddings(all_scraped_sentences)

    # Similarity matrix size is bounded by max_input_sentences * max_scraped_sentences
    sim_matrix = cosine_similarity(input_embeddings, scraped_embeddings)

    matches = []
    highlighted_sentences = []

    total_len = sum(len(s) for s in input_sentences) or 1
    weighted_plagiarism_sum = 0.0

    for idx, sentence in enumerate(input_sentences):
        row = sim_matrix[idx]
        max_idx = int(np.argmax(row))
        max_score = float(row[max_idx])

        category = "unique"
        if max_score >= 0.90:
            category = "exact"
            weighted_plagiarism_sum += len(sentence)
        elif max_score >= 0.70:
            category = "paraphrased"
            weighted_plagiarism_sum += len(sentence) * 0.7
        elif max_score >= 0.55:
            category = "weak_paraphrased"
            weighted_plagiarism_sum += len(sentence) * 0.4

        url, matched_text = sentence_sources[max_idx]

        if category != "unique":
            matches.append(
                {
                    "original_text": sentence,
                    "matched_text": matched_text,
                    "similarity_score": round(max_score * 100, 2),
                    "source_url": url,
                    "category": category,
                }
            )

        highlighted_sentences.append(
            {
                "text": sentence,
                "similarity": round(max_score * 100, 2),
                "category": category,
                "source_url": url if category != "unique" else None,
                "matched_text": matched_text if category != "unique" else None,
            }
        )

    plagiarism_score = round((weighted_plagiarism_sum / total_len) * 100, 2)
    plagiarism_score = min(plagiarism_score, 100.0)

    return {
        "plagiarism_score": plagiarism_score,
        "matches": matches,
        "highlighted_sentences": highlighted_sentences,
    }


def perform_semantic_plagiarism_scan(
    text: str,
    google_key: str = None,
) -> dict:
    """
    Web-scale semantic plagiarism scan with stability caps.

    This function is designed to be safe for low RAM:
    - hard cap chunk count
    - enforce a wall-clock budget for scanning
    - bounded similarity matrix sizes via _scan_chunk_semantic caps
    """
    # Wall-clock budget per request for the entire web scan stage
    # (classifier + stylometry are handled elsewhere)
    scan_deadline_seconds = float(os.getenv("WEB_SCAN_DEADLINE_SECONDS", "12"))

    chunks = chunk_text(text)
    if not chunks:
        input_sentences = split_into_sentences(text)
        return {
            "plagiarism_score": 0.0,
            "matches": [],
            "highlighted_sentences": [
                {"text": s, "similarity": 0.0, "category": "unique"}
                for s in input_sentences
            ],
            "chunks_scanned": 0,
            "chunks_with_matches": 0,
        }

    # Cap number of chunks to reduce embedding/similarity workload
    max_chunks = int(os.getenv("MAX_WEB_SCAN_CHUNKS", "6"))
    chunks = chunks[:max_chunks]

    all_matches = []
    all_highlighted = []
    chunk_scores = []

    scan_start = time.time()

    for i, chunk in enumerate(chunks):
        if (time.time() - scan_start) > scan_deadline_seconds:
            break
        try:
            result = _scan_chunk_semantic(
                chunk,
                max_input_sentences=45,
                max_search_queries=3,
                max_pages=3,
                max_scraped_sentences=int(os.getenv("MAX_SCRAPED_SENTENCES", "220")),
            )
            chunk_scores.append(float(result.get("plagiarism_score", 0.0) or 0.0))

            # Deduplicate matches by URL (light dedupe)
            for match in result.get("matches", []):
                if not any(
                    m.get("source_url") == match.get("source_url") for m in all_matches
                ):
                    all_matches.append(match)

            all_highlighted.extend(result.get("highlighted_sentences", []))
        except Exception:
            # Best-effort: do not crash worker
            continue

    # Weighted score: use top decile-ish not max to avoid outliers
    if chunk_scores:
        sorted_scores = sorted(chunk_scores, reverse=True)
        top_scores = sorted_scores[: max(1, len(sorted_scores) // 5)]
        final_score = sum(top_scores) / len(top_scores)
    else:
        final_score = 0.0

    # Deduplicate highlighted sentences
    seen = set()
    unique_highlighted = []
    for s in all_highlighted:
        key = (s.get("text") or "")[:80]
        if key and key not in seen:
            seen.add(key)
            unique_highlighted.append(s)

    return {
        "plagiarism_score": round(float(final_score), 4),
        "matches": all_matches[:20],
        "highlighted_sentences": unique_highlighted,
        "chunks_scanned": len(chunks),
        "chunks_with_matches": sum(1 for s in chunk_scores if s > 0.1),
    }

