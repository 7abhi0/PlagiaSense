# PlagiaSense Fix TODO

- [x] TASK 1: Rewrite `backend/app/utils/file_handler.py` to support PDF, DOCX, PPTX/PPT, TXT, DOC fallback.
- [x] TASK 5a: Update `backend/requirements.txt` to include python-pptx==0.6.23 (and ensure existing pinned libs remain).
- [x] TASK 2: Add chunking + weighted scoring + match/highlight dedup + chunk stats in `backend/app/ml/semantic_search.py`.

- [x] TASK 3: Add 10MB file size limit, 50k char truncation warning, and response fields in `backend/app/routes/scan.py`.
- [x] TASK 4: Update `frontend/src/pages/PlagiarismScan.jsx` UI (supported types, word count, chunks scanned, truncation banner, show match cards with URLs).


- [ ] After changes: run a local sanity test by tracing a ~5000-word input through chunking logic.
- [ ] Git: `git add -A`, `git commit -m "Fix long document and PPT plagiarism scanning"`, `git push`.
- [ ] Provide full contents of every changed file.
