# PlagiaSense – AI‑Powered Plagiarism & AI Content Detector

## Overview
PlagiaSense is a full‑stack web application that detects:
1. **Plagiarism** – compares uploaded or pasted text against a reference corpus using TF‑IDF + cosine similarity and highlights copied sentences.
2. **AI‑generated content** – classifies text as human‑written or AI‑generated with a trained Scikit‑learn model.

It provides a modern, glass‑morphic UI built with **React**, **Tailwind CSS**, and **Framer Motion**, and a secure **Flask** API with **JWT** authentication, **MongoDB** persistence, and rate‑limiting.

## Tech Stack
| Layer | Technology |
|-------|------------|
| Frontend | React 18, Vite, Tailwind CSS, Axios, React Router, Chart.js, Framer Motion |
| Backend | Python 3.12, Flask, Flask‑CORS, Flask‑JWT‑Extended, Flask‑Limiter, PyMongo |
| Database | MongoDB Atlas |
| AI/ML | Scikit‑learn, spaCy, NLTK, TensorFlow (optional), Sentence‑Transformers |
| Deployment | Vercel (frontend), Render (backend) |

## Quick Start (Local Development)
### Prerequisites
- **Node.js** (>=20)
- **Python** (>=3.10)
- **MongoDB** instance (local or Atlas). You can use the provided free Atlas cluster.

### 1. Clone the repository (or copy the generated files)
```bash
# Assuming you are in the parent folder
git clone <repo‑url> PlagiaSense
cd PlagiaSense
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate   # on Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # edit with your MongoDB URI and JWT secret
python run.py               # runs on http://localhost:5000
```
The server will automatically train the AI model if `models/model.pkl` is missing.

### 3. Frontend Setup
```bash
cd ../frontend
npm install
npm run dev                # Vite dev server on http://localhost:5173
```
The frontend proxies API calls to `http://localhost:5000` (see `vite.config.js`).

### 4. Sample Credentials
A demo user is created automatically on first run:
```
Email: demo@plagiasense.com
Password: Password123
```
Use these to log in.

## Running Tests
- Backend: `pytest -q`
- Frontend: `npm test`

## Deployment
### Frontend (Vercel)
- Connect the `frontend/` folder to Vercel.
- Vercel will use the `vercel.json` config for SPA routing.

### Backend (Render)
- Create a new **Web Service** on Render.
- Set the build command to `pip install -r requirements.txt` and the start command to `gunicorn -w 4 -b 0.0.0.0:10000 run:app`.
- Add the environment variables (`MONGO_URI`, `JWT_SECRET`, `MODEL_PATH`).

## API Documentation
See the **API_DOCS.md** file in the `backend/` folder for detailed request/response examples.

## Project Structure
```
PlagiaSense/
├─ frontend/                 # React app (Vite)
├─ backend/                  # Flask API
├─ models/                   # Trained ML models (model.pkl, plagiarism_tfidf.pkl)
├─ datasets/                 # Sample data for training
├─ .gitignore
├─ README.md
├─ requirements.txt
├─ package.json
├─ .env.example
├─ render.yaml
└─ vercel.json
```

---
*Happy hacking!*
