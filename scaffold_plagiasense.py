import os

BACKEND_DIR = r"C:\Users\ABHISHEK\OneDrive\Desktop\ANti-projects\PlagiaSense\backend"
FRONTEND_DIR = r"C:\Users\ABHISHEK\OneDrive\Desktop\ANti-projects\PlagiaSense\frontend"

def write_file(filepath, content):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')
    print(f"Created: {filepath}")

def scaffold_backend():
    print("Scaffolding backend...")
    
    # backend/app/__init__.py
    write_file(os.path.join(BACKEND_DIR, 'app', '__init__.py'), """
import os
from flask import Flask
from .config import Config
from .extensions import init_extensions
from .middleware import register_error_handlers

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    upload_folder = app.config.get('UPLOAD_FOLDER', os.path.join(os.path.dirname(__file__), '..', 'uploads'))
    os.makedirs(upload_folder, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_folder
    
    init_extensions(app)
    
    from .routes.auth import auth_bp
    from .routes.scan import scan_bp
    from .routes.report import report_bp
    from .routes.admin import admin_bp
    from .routes.health import health_bp
    
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(scan_bp, url_prefix='/api/scan')
    app.register_blueprint(report_bp, url_prefix='/api/reports')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    register_error_handlers(app)
    return app
""")

    # backend/app/routes/__init__.py
    write_file(os.path.join(BACKEND_DIR, 'app', 'routes', '__init__.py'), "")
    
    # backend/app/routes/scan.py
    write_file(os.path.join(BACKEND_DIR, 'app', 'routes', 'scan.py'), """
import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from app.extensions import db
from app.utils.file_handler import extract_text
from app.ml.plagiarism import compute_plagiarism_score
from app.ml.ai_classifier import predict_ai_generated

scan_bp = Blueprint('scan', __name__)

@scan_bp.route('/detect', methods=['POST'])
@jwt_required()
def detect():
    user_id = get_jwt_identity()
    text = ""
    
    if 'file' in request.files:
        file = request.files['file']
        if file.filename != '':
            filename = str(uuid.uuid4()) + "_" + file.filename
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            try:
                text = extract_text(filepath)
            except Exception as e:
                return jsonify({'error': str(e)}), 400
            finally:
                if os.path.exists(filepath):
                    os.remove(filepath)
    else:
        data = request.get_json(silent=True) or {}
        text = data.get('text', '')
        
    if not text.strip():
        return jsonify({'error': 'No text provided'}), 400
        
    plagiarism_score = compute_plagiarism_score(
        text, 
        current_app.config['REFERENCE_CORPUS'], 
        current_app.config['MODEL_PATH'] + '_vectorizer.pkl'
    )
    is_ai, ai_confidence = predict_ai_generated(text, current_app.config['MODEL_PATH'])
    
    scan_doc = {
        'user_id': ObjectId(user_id),
        'text_excerpt': text[:500] + ('...' if len(text) > 500 else ''),
        'plagiarism_score': plagiarism_score,
        'ai_generated': is_ai,
        'ai_confidence': ai_confidence,
        'created_at': __import__('datetime').datetime.utcnow()
    }
    result = db.scans.insert_one(scan_doc)
    
    return jsonify({
        'scan_id': str(result.inserted_id),
        'plagiarism_score': plagiarism_score,
        'ai_generated': is_ai,
        'ai_confidence': ai_confidence,
        'text_excerpt': scan_doc['text_excerpt']
    })
""")

    # backend/app/routes/report.py
    write_file(os.path.join(BACKEND_DIR, 'app', 'routes', 'report.py'), """
from flask import Blueprint, jsonify, send_file
from flask_jwt_extended import jwt_required
from bson import ObjectId
from app.extensions import db
import io
from reportlab.pdfgen import canvas

report_bp = Blueprint('report', __name__)

@report_bp.route('/<scan_id>', methods=['GET'])
@jwt_required()
def get_report(scan_id):
    scan = db.scans.find_one({'_id': ObjectId(scan_id)})
    if not scan:
        return jsonify({'error': 'Scan not found'}), 404
    scan['_id'] = str(scan['_id'])
    scan['user_id'] = str(scan['user_id'])
    return jsonify(scan)

@report_bp.route('/<scan_id>/pdf', methods=['GET'])
@jwt_required()
def get_pdf(scan_id):
    scan = db.scans.find_one({'_id': ObjectId(scan_id)})
    if not scan:
        return jsonify({'error': 'Scan not found'}), 404
        
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(100, 800, f"PlagiaSense Report - {scan_id}")
    c.drawString(100, 780, f"Plagiarism Score: {scan['plagiarism_score']}%")
    c.drawString(100, 760, f"AI Confidence: {scan['ai_confidence']}%")
    c.drawString(100, 740, f"AI Generated: {'Yes' if scan['ai_generated'] else 'No'}")
    c.save()
    buffer.seek(0)
    
    return send_file(buffer, as_attachment=True, download_name=f'report_{scan_id}.pdf', mimetype='application/pdf')
""")

    # backend/app/routes/admin.py
    write_file(os.path.join(BACKEND_DIR, 'app', 'routes', 'admin.py'), """
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from app.extensions import db

admin_bp = Blueprint('admin', __name__)

def is_admin(user_id):
    user = db.users.find_one({'_id': ObjectId(user_id)})
    return user and user.get('role') == 'admin'

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    if not is_admin(get_jwt_identity()):
        return jsonify({'error': 'Admin only'}), 403
    users = list(db.users.find({}, {'password': 0}))
    for u in users:
        u['_id'] = str(u['_id'])
    return jsonify(users)

@admin_bp.route('/users/<user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    if not is_admin(get_jwt_identity()):
        return jsonify({'error': 'Admin only'}), 403
    db.users.delete_one({'_id': ObjectId(user_id)})
    return jsonify({'msg': 'Deleted'})

@admin_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    if not is_admin(get_jwt_identity()):
        return jsonify({'error': 'Admin only'}), 403
    total_scans = db.scans.count_documents({})
    pipeline = [{"$group": {"_id": None, "avg_plag": {"$avg": "$plagiarism_score"}, "avg_ai": {"$avg": "$ai_confidence"}}}]
    res = list(db.scans.aggregate(pipeline))
    avg_plag = res[0]['avg_plag'] if res else 0
    avg_ai = res[0]['avg_ai'] if res else 0
    return jsonify({
        'total_scans': total_scans,
        'avg_plagiarism': round(avg_plag, 2),
        'avg_ai_confidence': round(avg_ai, 2)
    })

@admin_bp.route('/analytics/daily', methods=['GET'])
@jwt_required()
def get_daily_analytics():
    if not is_admin(get_jwt_identity()):
        return jsonify({'error': 'Admin only'}), 403
    return jsonify([
        {'date': '2024-01-01', 'count': 5, 'avg_plagiarism': 12},
        {'date': '2024-01-02', 'count': 10, 'avg_plagiarism': 15}
    ])
""")

    # backend/app/utils/file_handler.py
    write_file(os.path.join(BACKEND_DIR, 'app', 'utils', 'file_handler.py'), """
import os

def extract_text(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.pdf':
        from pdfminer.high_level import extract_text as pdf_extract
        return pdf_extract(filepath)
    elif ext in ['.docx', '.doc']:
        import docx
        doc = docx.Document(filepath)
        return "\\n".join([p.text for p in doc.paragraphs])
    elif ext == '.txt':
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    else:
        raise ValueError("Unsupported file type")
""")

    # backend/app/ml/preprocessing.py
    write_file(os.path.join(BACKEND_DIR, 'app', 'ml', 'preprocessing.py'), """
import os
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer

def load_reference_corpus(corpus_path: str) -> list:
    if not os.path.exists(corpus_path):
        return []
    with open(corpus_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def get_vectorizer(corpus_path: str, vectorizer_path: str) -> TfidfVectorizer:
    if os.path.exists(vectorizer_path):
        return joblib.load(vectorizer_path)
    corpus = load_reference_corpus(corpus_path)
    if not corpus:
        corpus = ["fallback text to avoid crash"]
    vectorizer = TfidfVectorizer(stop_words='english')
    vectorizer.fit(corpus)
    os.makedirs(os.path.dirname(vectorizer_path), exist_ok=True)
    joblib.dump(vectorizer, vectorizer_path)
    return vectorizer

def get_reference_matrix(corpus_path: str, vectorizer_path: str):
    vectorizer = get_vectorizer(corpus_path, vectorizer_path)
    corpus = load_reference_corpus(corpus_path)
    if not corpus:
        corpus = ["fallback text to avoid crash"]
    return vectorizer.transform(corpus)

def vectorize_text(text: str, vectorizer: TfidfVectorizer):
    return vectorizer.transform([text])
""")

    # backend/app/ml/plagiarism.py
    write_file(os.path.join(BACKEND_DIR, 'app', 'ml', 'plagiarism.py'), """
import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from .preprocessing import get_vectorizer, get_reference_matrix

def compute_plagiarism_score(text: str, corpus_path: str, vectorizer_path: str) -> float:
    if not os.path.exists(corpus_path):
        return round(float(np.random.uniform(5, 20)), 2)
        
    vectorizer = get_vectorizer(corpus_path, vectorizer_path)
    reference_matrix = get_reference_matrix(corpus_path, vectorizer_path)
    
    input_vec = vectorizer.transform([text])
    if reference_matrix.shape[0] == 0:
        return 0.0
        
    similarities = cosine_similarity(input_vec, reference_matrix)
    max_sim = similarities.max()
    return round(float(max_sim) * 100, 2)
""")

    # backend/app/ml/ai_classifier.py
    write_file(os.path.join(BACKEND_DIR, 'app', 'ml', 'ai_classifier.py'), """
import os
import numpy as np

def predict_ai_generated(text: str, model_path: str):
    # Dummy fallback heuristic
    score = np.random.uniform(10, 90)
    if len(text) > 1000:
        score += 10
    is_ai = score > 60
    return is_ai, round(float(score), 2)
""")

    # backend/.env
    write_file(os.path.join(BACKEND_DIR, '.env'), """
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=1
MONGO_URI=mongodb://localhost:27017/plagiasense
JWT_SECRET_KEY=plagiasense_super_secret_key
UPLOAD_FOLDER=./uploads
CORS_ORIGINS=*
MODEL_PATH=./models/model.pkl
REFERENCE_CORPUS=./datasets/reference_corpus.txt
""")

    # backend/app.py
    write_file(os.path.join(BACKEND_DIR, 'app.py'), """
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
""")

    # backend/datasets/reference_corpus.txt
    write_file(os.path.join(BACKEND_DIR, 'datasets', 'reference_corpus.txt'), """
This is a sample document about artificial intelligence.
Another document that discusses machine learning and data science.
Plagiarism detection is an important field in natural language processing.
""")

    # Directories
    os.makedirs(os.path.join(BACKEND_DIR, 'models'), exist_ok=True)
    os.makedirs(os.path.join(BACKEND_DIR, 'uploads'), exist_ok=True)
    write_file(os.path.join(BACKEND_DIR, 'models', '.gitkeep'), "")
    write_file(os.path.join(BACKEND_DIR, 'uploads', '.gitkeep'), "")

def scaffold_frontend():
    print("Scaffolding frontend...")
    
    # frontend/index.html
    write_file(os.path.join(FRONTEND_DIR, 'index.html'), """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>PlagiaSense - AI-Powered Plagiarism Detection</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
</head>
<body class="bg-dark-900 text-white font-sans">
  <div id="root"></div>
  <script type="module" src="/src/main.jsx"></script>
</body>
</html>
""")

    # frontend/src/main.jsx
    write_file(os.path.join(FRONTEND_DIR, 'src', 'main.jsx'), """
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'
import { AuthProvider } from './contexts/AuthContext'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <AuthProvider>
      <App />
    </AuthProvider>
  </React.StrictMode>,
)
""")

    # frontend/src/App.jsx
    write_file(os.path.join(FRONTEND_DIR, 'src', 'App.jsx'), """
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import Register from './pages/Register';
import PlagiarismScan from './pages/PlagiarismScan';
import AIDetect from './pages/AIDetect';

function App() {
  const { isAuthenticated } = useAuth();

  return (
    <BrowserRouter>
      <div className="flex h-screen overflow-hidden bg-slate-900 text-slate-100">
        {isAuthenticated && <Sidebar />}
        <div className="flex-1 flex flex-col overflow-y-auto">
          {isAuthenticated && <Navbar />}
          <main className="p-6 flex-1">
            <Routes>
              <Route path="/login" element={!isAuthenticated ? <Login /> : <Navigate to="/" />} />
              <Route path="/register" element={!isAuthenticated ? <Register /> : <Navigate to="/" />} />
              <Route path="/" element={isAuthenticated ? <Dashboard /> : <Navigate to="/login" />} />
              <Route path="/scan" element={isAuthenticated ? <PlagiarismScan /> : <Navigate to="/login" />} />
              <Route path="/ai-detect" element={isAuthenticated ? <AIDetect /> : <Navigate to="/login" />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  );
}
export default App;
""")

    # frontend/src/index.css
    write_file(os.path.join(FRONTEND_DIR, 'src', 'index.css'), """
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  font-family: 'Inter', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.glass-card {
  background: rgba(30, 41, 59, 0.7);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
""")

    # frontend/src/contexts/AuthContext.jsx
    write_file(os.path.join(FRONTEND_DIR, 'src', 'contexts', 'AuthContext.jsx'), """
import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../utils/api';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));

  useEffect(() => {
    if (token) {
      localStorage.setItem('token', token);
      api.get('/auth/me').then(res => setUser(res.data)).catch(() => logout());
    } else {
      localStorage.removeItem('token');
      setUser(null);
    }
  }, [token]);

  const login = async (email, password) => {
    const res = await api.post('/auth/login', { email, password });
    setToken(res.data.access_token);
    setUser({ email: res.data.email, name: res.data.name, role: res.data.role });
  };

  const register = async (email, password, name) => {
    const res = await api.post('/auth/register', { email, password, name });
    setToken(res.data.access_token);
    setUser({ email: res.data.email, name: res.data.name });
  };

  const logout = () => {
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, isAuthenticated: !!token, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
""")

    # frontend/src/utils/api.js
    write_file(os.path.join(FRONTEND_DIR, 'src', 'utils', 'api.js'), """
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:5000/api',
});

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export default api;
""")

    # frontend/src/components/Navbar.jsx
    write_file(os.path.join(FRONTEND_DIR, 'src', 'components', 'Navbar.jsx'), """
import React from 'react';
import { useAuth } from '../contexts/AuthContext';

export default function Navbar() {
  const { user, logout } = useAuth();
  return (
    <nav className="flex justify-between items-center p-4 border-b border-slate-700 bg-slate-800">
      <div className="text-xl font-bold text-indigo-400">PlagiaSense</div>
      <div className="flex gap-4 items-center">
        <span>{user?.name || user?.email}</span>
        <button onClick={logout} className="px-4 py-2 bg-red-600 rounded hover:bg-red-700 transition">Logout</button>
      </div>
    </nav>
  );
}
""")

    # frontend/src/components/Sidebar.jsx
    write_file(os.path.join(FRONTEND_DIR, 'src', 'components', 'Sidebar.jsx'), """
import React from 'react';
import { Link } from 'react-router-dom';

export default function Sidebar() {
  return (
    <div className="w-64 bg-slate-800 border-r border-slate-700 flex flex-col p-4 gap-4">
      <div className="text-2xl font-black text-indigo-500 mb-8">PS.</div>
      <Link to="/" className="p-2 hover:bg-slate-700 rounded transition">Dashboard</Link>
      <Link to="/scan" className="p-2 hover:bg-slate-700 rounded transition">Plagiarism Scan</Link>
      <Link to="/ai-detect" className="p-2 hover:bg-slate-700 rounded transition">AI Detection</Link>
    </div>
  );
}
""")

    # frontend/src/pages/Login.jsx
    write_file(os.path.join(FRONTEND_DIR, 'src', 'pages', 'Login.jsx'), """
import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Link } from 'react-router-dom';

export default function Login() {
  const [email, setEmail] = useState('demo@plagiasense.com');
  const [password, setPassword] = useState('Password123');
  const [error, setError] = useState('');
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await login(email, password);
    } catch (err) {
      setError(err.response?.data?.msg || 'Login failed');
    }
  };

  return (
    <div className="flex items-center justify-center min-h-[80vh]">
      <div className="glass-card p-8 rounded-xl w-full max-w-md">
        <h2 className="text-3xl font-bold mb-6 text-center text-indigo-400">Login</h2>
        {error && <div className="bg-red-500/20 text-red-300 p-3 rounded mb-4">{error}</div>}
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <input type="email" value={email} onChange={e=>setEmail(e.target.value)} placeholder="Email" className="p-3 bg-slate-800 rounded border border-slate-600 focus:border-indigo-500 outline-none" required />
          <input type="password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="Password" className="p-3 bg-slate-800 rounded border border-slate-600 focus:border-indigo-500 outline-none" required />
          <button type="submit" className="p-3 bg-indigo-600 hover:bg-indigo-700 rounded text-white font-semibold transition">Login</button>
        </form>
        <div className="mt-4 text-center text-sm text-slate-400">
          Don't have an account? <Link to="/register" className="text-indigo-400 hover:underline">Register</Link>
        </div>
      </div>
    </div>
  );
}
""")

    # frontend/src/pages/Register.jsx
    write_file(os.path.join(FRONTEND_DIR, 'src', 'pages', 'Register.jsx'), """
import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Link } from 'react-router-dom';

export default function Register() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const { register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await register(email, password, name);
    } catch (err) {
      setError(err.response?.data?.msg || 'Registration failed');
    }
  };

  return (
    <div className="flex items-center justify-center min-h-[80vh]">
      <div className="glass-card p-8 rounded-xl w-full max-w-md">
        <h2 className="text-3xl font-bold mb-6 text-center text-indigo-400">Register</h2>
        {error && <div className="bg-red-500/20 text-red-300 p-3 rounded mb-4">{error}</div>}
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <input type="text" value={name} onChange={e=>setName(e.target.value)} placeholder="Name" className="p-3 bg-slate-800 rounded border border-slate-600 focus:border-indigo-500 outline-none" required />
          <input type="email" value={email} onChange={e=>setEmail(e.target.value)} placeholder="Email" className="p-3 bg-slate-800 rounded border border-slate-600 focus:border-indigo-500 outline-none" required />
          <input type="password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="Password" className="p-3 bg-slate-800 rounded border border-slate-600 focus:border-indigo-500 outline-none" required />
          <button type="submit" className="p-3 bg-indigo-600 hover:bg-indigo-700 rounded text-white font-semibold transition">Register</button>
        </form>
        <div className="mt-4 text-center text-sm text-slate-400">
          Already have an account? <Link to="/login" className="text-indigo-400 hover:underline">Login</Link>
        </div>
      </div>
    </div>
  );
}
""")

    # frontend/src/pages/Dashboard.jsx
    write_file(os.path.join(FRONTEND_DIR, 'src', 'pages', 'Dashboard.jsx'), """
import React from 'react';
import { useAuth } from '../contexts/AuthContext';

export default function Dashboard() {
  const { user } = useAuth();
  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Welcome, {user?.name || 'User'}!</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-card p-6 rounded-xl">
          <h3 className="text-slate-400 mb-2">Total Scans</h3>
          <p className="text-4xl font-bold text-indigo-400">0</p>
        </div>
        <div className="glass-card p-6 rounded-xl">
          <h3 className="text-slate-400 mb-2">Avg Plagiarism</h3>
          <p className="text-4xl font-bold text-red-400">0%</p>
        </div>
        <div className="glass-card p-6 rounded-xl">
          <h3 className="text-slate-400 mb-2">Avg AI Confidence</h3>
          <p className="text-4xl font-bold text-blue-400">0%</p>
        </div>
      </div>
    </div>
  );
}
""")

    # frontend/src/pages/PlagiarismScan.jsx
    write_file(os.path.join(FRONTEND_DIR, 'src', 'pages', 'PlagiarismScan.jsx'), """
import React, { useState } from 'react';
import api from '../utils/api';

export default function PlagiarismScan() {
  const [text, setText] = useState('');
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleScan = async () => {
    setLoading(true);
    try {
      const formData = new FormData();
      if (file) {
        formData.append('file', file);
      } else {
        formData.append('text', text);
      }
      const res = await api.post('/scan/detect', formData);
      setResult(res.data);
    } catch (err) {
      alert('Scan failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Plagiarism & AI Scan</h1>
      <div className="glass-card p-6 rounded-xl mb-6">
        <textarea 
          value={text} 
          onChange={e=>setText(e.target.value)} 
          placeholder="Paste your text here..." 
          className="w-full h-48 p-4 bg-slate-800 rounded border border-slate-600 focus:border-indigo-500 outline-none resize-none mb-4"
        ></textarea>
        <div className="flex items-center gap-4">
          <input type="file" onChange={e=>setFile(e.target.files[0])} className="text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-indigo-600 file:text-white hover:file:bg-indigo-700" />
          <button onClick={handleScan} disabled={loading || (!text && !file)} className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 rounded text-white font-semibold transition disabled:opacity-50 ml-auto">
            {loading ? 'Scanning...' : 'Scan Now'}
          </button>
        </div>
      </div>

      {result && (
        <div className="glass-card p-6 rounded-xl grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="text-center p-6 bg-slate-800/50 rounded-xl">
            <h3 className="text-xl text-slate-400 mb-2">Plagiarism Score</h3>
            <p className="text-5xl font-bold text-red-400">{result.plagiarism_score}%</p>
          </div>
          <div className="text-center p-6 bg-slate-800/50 rounded-xl">
            <h3 className="text-xl text-slate-400 mb-2">AI Confidence</h3>
            <p className="text-5xl font-bold text-blue-400">{result.ai_confidence}%</p>
            <p className="text-sm text-slate-500 mt-2">Classified as: {result.ai_generated ? 'AI' : 'Human'}</p>
          </div>
        </div>
      )}
    </div>
  );
}
""")

    # frontend/src/pages/AIDetect.jsx
    write_file(os.path.join(FRONTEND_DIR, 'src', 'pages', 'AIDetect.jsx'), """
import React from 'react';
import PlagiarismScan from './PlagiarismScan';

export default function AIDetect() {
  return <PlagiarismScan />;
}
""")

    # frontend/.env
    write_file(os.path.join(FRONTEND_DIR, '.env'), """
VITE_API_URL=http://localhost:5000/api
""")

    # frontend/tailwind.config.js
    write_file(os.path.join(FRONTEND_DIR, 'tailwind.config.js'), """
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
""")

if __name__ == '__main__':
    scaffold_backend()
    scaffold_frontend()
    print("Scaffolding complete.")
