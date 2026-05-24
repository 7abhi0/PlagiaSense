import requests
from bs4 import BeautifulSoup
import re
import time
import urllib.parse

# List of realistic user agents
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
        "Referer": "https://www.google.com/"
    }

def search_duckduckgo(query: str, num_results: int = 3) -> list:
    """Search DuckDuckGo HTML/lite interface for links matching the query."""
    print(f"Searching DuckDuckGo for query: {query[:50]}...")
    links = []
    # Using html.duckduckgo.com which is lighter and doesn't require Javascript
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    
    try:
        response = requests.get(url, headers=get_headers(), timeout=10)
        if response.status_code != 200:
            print(f"Search failed with status: {response.status_code}")
            return []
            
        soup = BeautifulSoup(response.text, "html.parser")
        # Links are inside 'a' elements with class 'result__url' or similar in DuckDuckGo HTML
        result_elements = soup.find_all("a", class_="result__url")
        for elem in result_elements:
            href = elem.get("href")
            if href:
                # DuckDuckGo HTML links are wrapped: /l/?kh=-1&uddg=https%3A%2F%2Fexample.com
                parsed = urllib.parse.urlparse(href)
                query_params = urllib.parse.parse_qs(parsed.query)
                if 'uddg' in query_params:
                    link = query_params['uddg'][0]
                else:
                    link = href
                
                # Filter out search engines / common exclusions
                if "duckduckgo.com" not in link and "google.com" not in link:
                    links.append(link)
                    if len(links) >= num_results:
                        break
    except Exception as e:
        print(f"Error in search_duckduckgo: {e}")
        
    return links

def scrape_page(url: str) -> str:
    """Scrape web page and extract clean paragraph text."""
    print(f"Scraping page: {url}")
    try:
        response = requests.get(url, headers=get_headers(), timeout=8)
        if response.status_code != 200:
            return ""
            
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove script and style elements
        for script in soup(["script", "style", "noscript", "header", "footer", "nav"]):
            script.decompose()
            
        # Get paragraphs
        paragraphs = soup.find_all("p")
        text_list = []
        for p in paragraphs:
            text = p.get_text().strip()
            # Simple length threshold to filter out empty/boilerplate lines
            if len(text) > 30:
                text_list.append(text)
                
        full_text = " ".join(text_list)
        # Normalize whitespace
        full_text = re.sub(r'\s+', ' ', full_text)
        return full_text
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return ""

def get_web_candidates(sentence_queries: list, max_pages: int = 3) -> dict:
    """
    Search and scrape web candidates for a list of sentences.
    Returns a dict mapping source URLs to their cleaned scraped text.
    """
    candidates = {}
    searched_urls = set()
    
    for query in sentence_queries:
        if len(query.strip()) < 15:
            continue
        # Search web for the sentence chunk
        urls = search_duckduckgo(query, num_results=2)
        for url in urls:
            if url not in searched_urls:
                searched_urls.add(url)
                text = scrape_page(url)
                if text:
                    candidates[url] = text
                    if len(candidates) >= max_pages:
                        return candidates
        # Throttling/delay to be gentle
        time.sleep(1)
        
    return candidates
