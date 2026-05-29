import os
import random
import time
import re
import urllib.parse
from typing import Optional, List, Dict, Tuple
from bs4 import BeautifulSoup

import requests


# Domains we never scrape (per requirements)
UNSUPPORTED_HOSTS = {
    "youtube.com",
    "facebook.com",
    "instagram.com",
}

# File extensions we never scrape
UNSUPPORTED_PATH_EXTS = {".pdf"}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
]

def get_headers() -> Dict[str, str]:
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "close",
        "Referer": "https://www.google.com/",
    }


def search_via_serp_api(query: str, num_results: int = 3) -> list:
    """Use SerpAPI if SERP_API_KEY is available."""
    api_key = os.getenv("SERP_API_KEY")
    if not api_key:
        return []
    try:
        url = "https://serpapi.com/search"
        params = {
            "q": query,
            "api_key": api_key,
            "num": num_results,
            "engine": "google",
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        links = []
        for result in data.get("organic_results", []):
            link = result.get("link")
            if link:
                links.append(link)
        # Keep logs minimal; avoid print in production
        return links[:num_results]
    except Exception:
        return []


def search_bing(query: str, num_results: int = 3) -> list:
    """Search Bing (no API key needed for basic scraping)."""
    links = []
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://www.bing.com/search?q={encoded}&count={num_results * 2}"
        response = requests.get(url, headers=get_headers(), timeout=10)
        if response.status_code != 200:
            return []
        soup = BeautifulSoup(response.text, "html.parser")
        for a in soup.select("li.b_algo h2 a"):
            href = a.get("href", "")
            if href.startswith("http") and "bing.com" not in href and "microsoft.com" not in href:
                links.append(href)
                if len(links) >= num_results:
                    break
    except Exception:
        pass
    return links


def search_duckduckgo(query: str, num_results: int = 3) -> list:
    """Search DuckDuckGo HTML interface."""
    links = []
    try:
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        response = requests.get(url, headers=get_headers(), timeout=10)
        if response.status_code != 200:
            return []
        soup = BeautifulSoup(response.text, "html.parser")
        for elem in soup.find_all("a", class_="result__url"):
            href = elem.get("href", "")
            parsed = urllib.parse.urlparse(href)
            params = urllib.parse.parse_qs(parsed.query)
            link = params.get("uddg", [href])[0]
            if link and "duckduckgo.com" not in link and link.startswith("http"):
                links.append(link)
                if len(links) >= num_results:
                    break
        # Also try result__a links as fallback
        if not links:
            for elem in soup.find_all("a", class_="result__a"):
                href = elem.get("href", "")
                if href and href.startswith("http") and "duckduckgo.com" not in href:
                    links.append(href)
                    if len(links) >= num_results:
                        break
    except Exception:
        pass
    return links


def search_web(query: str, num_results: int = 3) -> list:
    """
    Try multiple search engines in order:
    1. SerpAPI (if key available)
    2. Bing scraping
    3. DuckDuckGo scraping
    Returns first successful result set.
    """
    links = search_via_serp_api(query, num_results)
    if links:
        return links

    links = search_bing(query, num_results)
    if links:
        return links

    links = search_duckduckgo(query, num_results)
    return links


def _is_unsupported_url(url: str) -> bool:
    try:
        parsed = urllib.parse.urlparse(url)
        host = (parsed.hostname or "").lower().strip()
        if any(host == h or host.endswith("." + h) for h in UNSUPPORTED_HOSTS):
            return True
        path = (parsed.path or "").lower()
        for ext in UNSUPPORTED_PATH_EXTS:
            if ext in path:
                return True
        return False
    except Exception:
        return True


def scrape_page(
    url: str,
    *,
    timeout: int = 8,
    max_chars: int = 2500,
    max_paragraphs: int = 25,
    max_retries: int = 2,
) -> str:
    """Scrape web page and extract clean paragraph text (bounded for stability)."""
    if not url or _is_unsupported_url(url):
        return ""

    # Small network retry policy for stability
    last_err = None
    for attempt in range(max_retries + 1):
        try:
            response = requests.get(
                url,
                headers=get_headers(),
                timeout=(3.5, timeout),  # (connect, read)
                allow_redirects=True,
            )
            if response.status_code != 200:
                # 429/503 often transient; retry
                if response.status_code in (429, 500, 502, 503, 504) and attempt < max_retries:
                    backoff = (2 ** attempt) + random.random()
                    time.sleep(backoff)
                    continue
                return ""

            content_type = (response.headers.get("Content-Type", "") or "").lower()
            if "text/html" not in content_type:
                return ""

            # Cap response size in memory by checking Content-Length (best-effort)
            try:
                if int(response.headers.get("Content-Length", "0") or 0) > 2_500_000:
                    return ""
            except Exception:
                pass

            soup = BeautifulSoup(response.text, "html.parser")
            for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside", "form"]):
                tag.decompose()

            main = (
                soup.find("main")
                or soup.find("article")
                or soup.find(id="content")
                or soup.find(class_="content")
            )
            target = main if main else soup

            paragraphs = target.find_all("p")
            kept = []
            for p in paragraphs:
                if len(kept) >= max_paragraphs:
                    break
                t = p.get_text(separator=" ").strip()
                if len(t) < 40:
                    continue
                # Additional per-paragraph cap to reduce RAM
                kept.append(t[:350])

            full_text = " ".join(kept)
            full_text = re.sub(r"\s+", " ", full_text).strip()
            return full_text[:max_chars]
        except Exception as e:
            last_err = e
            # Retry on transient request failures
            if attempt < max_retries:
                backoff = (2 ** attempt) + random.random()
                time.sleep(backoff)
                continue
            return ""
    return ""


def get_web_candidates(
    sentence_queries: list,
    max_pages: int = 5,
    *,
    max_candidates_total: int = 8,
    max_total_chars: int = 10_000,
    per_page_max_chars: int = 2500,
    deadline_seconds: Optional[float] = None,
) -> dict:
    """
    Search and scrape web candidates for a list of sentences.
    Returns dict mapping source URLs to their cleaned scraped text.

    Stability goals:
    - hard cap total scraped text length
    - hard cap number of candidate URLs
    - optional wall-clock deadline for the whole scraping phase
    """
    start = time.time()
    candidates: Dict[str, str] = {}
    searched_urls = set()
    total_chars = 0

    # Ensure we don't exceed caller's max_pages by accident
    max_pages = max(1, int(max_pages))
    max_candidates_total = max(1, int(max_candidates_total))
    max_pages = min(max_pages, max_candidates_total)

    for query in sentence_queries:
        if deadline_seconds is not None and (time.time() - start) > deadline_seconds:
            break

        query = (query or "").strip()
        if len(query) < 20:
            continue

        search_query = query[:120]
        urls = search_web(search_query, num_results=3)

        # Respect budgets while iterating results
        for url in urls:
            if deadline_seconds is not None and (time.time() - start) > deadline_seconds:
                break
            if not url or url in searched_urls:
                continue
            searched_urls.add(url)

            # Skip unsupported upfront to save network
            if _is_unsupported_url(url):
                continue

            # Reduce burst: small delay between requests
            time.sleep(0.15)

            text = scrape_page(url, max_chars=per_page_max_chars)
            if not text or len(text) <= 100:
                continue

            # Cap total chars (prevents embedding explosion)
            if total_chars + len(text) > max_total_chars:
                return candidates

            candidates[url] = text
            total_chars += len(text)

            if len(candidates) >= max_pages:
                return candidates

        # Small delay to be respectful
        time.sleep(0.25)

    return candidates
