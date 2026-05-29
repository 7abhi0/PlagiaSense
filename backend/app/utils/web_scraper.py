import requests
from bs4 import BeautifulSoup
import re
import time
import urllib.parse
import os

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
]

def get_headers():
    import random
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Referer": "https://www.google.com/"
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
            "engine": "google"
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        links = []
        for result in data.get("organic_results", []):
            link = result.get("link")
            if link:
                links.append(link)
        print(f"SerpAPI returned {len(links)} results for: {query[:40]}")
        return links[:num_results]
    except Exception as e:
        print(f"SerpAPI error: {e}")
        return []


def search_bing(query: str, num_results: int = 3) -> list:
    """Search Bing (no API key needed for basic scraping)."""
    print(f"Searching Bing for: {query[:50]}...")
    links = []
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://www.bing.com/search?q={encoded}&count={num_results * 2}"
        response = requests.get(url, headers=get_headers(), timeout=10)
        if response.status_code != 200:
            print(f"Bing returned status {response.status_code}")
            return []
        soup = BeautifulSoup(response.text, "html.parser")
        for a in soup.select("li.b_algo h2 a"):
            href = a.get("href", "")
            if href.startswith("http") and "bing.com" not in href and "microsoft.com" not in href:
                links.append(href)
                if len(links) >= num_results:
                    break
        print(f"Bing returned {len(links)} results")
    except Exception as e:
        print(f"Bing search error: {e}")
    return links


def search_duckduckgo(query: str, num_results: int = 3) -> list:
    """Search DuckDuckGo HTML interface."""
    print(f"Searching DuckDuckGo for: {query[:50]}...")
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
            link = params.get('uddg', [href])[0]
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
        print(f"DuckDuckGo returned {len(links)} results")
    except Exception as e:
        print(f"DuckDuckGo search error: {e}")
    return links


def search_web(query: str, num_results: int = 3) -> list:
    """
    Try multiple search engines in order:
    1. SerpAPI (if key available)
    2. Bing scraping
    3. DuckDuckGo scraping
    Returns first successful result set.
    """
    # Try SerpAPI first (most reliable)
    links = search_via_serp_api(query, num_results)
    if links:
        return links

    # Try Bing
    links = search_bing(query, num_results)
    if links:
        return links

    # Try DuckDuckGo
    links = search_duckduckgo(query, num_results)
    return links


def scrape_page(url: str) -> str:
    """Scrape web page and extract clean paragraph text."""
    print(f"Scraping: {url[:80]}")
    try:
        response = requests.get(url, headers=get_headers(), timeout=8, allow_redirects=True)
        if response.status_code != 200:
            return ""
        # Skip non-HTML content
        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            return ""

        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside", "form"]):
            tag.decompose()

        # Try to get main content area first
        main = soup.find("main") or soup.find("article") or soup.find(id="content") or soup.find(class_="content")
        target = main if main else soup

        paragraphs = target.find_all("p")
        text_list = [p.get_text(separator=" ").strip() for p in paragraphs if len(p.get_text().strip()) > 40]

        full_text = " ".join(text_list)
        full_text = re.sub(r'\s+', ' ', full_text).strip()

        # Return up to 5000 chars per page to keep things fast
        return full_text[:5000]
    except Exception as e:
        print(f"Scrape error for {url}: {e}")
        return ""


def get_web_candidates(sentence_queries: list, max_pages: int = 5) -> dict:
    """
    Search and scrape web candidates for a list of sentences.
    Returns dict mapping source URLs to their cleaned scraped text.
    """
    candidates = {}
    searched_urls = set()

    for query in sentence_queries:
        query = query.strip()
        if len(query) < 20:
            continue

        # Use first 120 chars of query for search (avoid too-long queries)
        search_query = query[:120]
        urls = search_web(search_query, num_results=3)

        for url in urls:
            if url in searched_urls:
                continue
            searched_urls.add(url)
            text = scrape_page(url)
            if text and len(text) > 100:
                candidates[url] = text
                print(f"Got {len(text)} chars from {url[:60]}")
                if len(candidates) >= max_pages:
                    return candidates

        # Small delay to be respectful
        time.sleep(0.5)

    print(f"Total web candidates found: {len(candidates)}")
    return candidates
