# PlagiaSense Stability Refactor — Checklist

## Step 1: Web scraping hardening
- [ ] Update `backend/app/utils/web_scraper.py`
  - [ ] Skip unsupported URLs/domains: youtube.com, facebook.com, instagram.com, plus PDF links
  - [ ] Add strict scraping budgets (max pages, max candidates, max total scraped chars)
  - [ ] Enforce per-request timeout protection (connect/read via requests)
  - [ ] Add retry-safe scraping (2 retries with exponential backoff)
  - [ ] Reduce extracted text size per page (lower cap)

## Step 2: Semantic pipeline memory + performance caps
- [ ] Update `backend/app/ml/semantic_search.py`
  - [ ] Limit chunks count and/or chunk size
  - [ ] Cap max input sentences / scraped sentences per chunk
  - [ ] Prevent cosine similarity matrix blowups by bounding scraped sentences
  - [ ] Add wall-clock budget for whole web candidate fetching + per chunk best-effort
  - [ ] Ensure consistent return schema on failures/timeouts

## Step 3: API stability + clean JSON errors + deadline
- [ ] Update `backend/app/routes/scan.py`
  - [ ] Add request-level deadline checks (wall clock) around the entire pipeline
  - [ ] Return clean JSON errors with consistent shape
  - [ ] Ensure no internal exception leaks stack traces/details

## Step 4: Gunicorn + Render free-tier crash reduction
- [ ] Update `backend/start.sh`
  - [ ] Set gunicorn workers/threads/max-requests/timeout for low RAM stability
- [ ] Update `render.yaml`
  - [ ] Add env vars for scraping/text/scan caps where applicable

## Step 5: Logging improvements
- [ ] Add structured logs in scraper + scan route for timings and skip reasons

## Step 6: Quick validation
- [ ] Run a smoke test locally (single small request) and confirm JSON response shape
- [ ] Ensure skipped URLs/pdfs are not scraped
- [ ] Confirm no crashes on large inputs (text truncation + caps respected)
