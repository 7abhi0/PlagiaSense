import os
import uuid
from datetime import datetime, timezone
import numpy as np
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.utils.file_handler import extract_text
from app.ml.semantic_search import perform_semantic_plagiarism_scan
from app.ml.transformer_classifier import predict_ai_generated, get_sentence_heatmap
from app.ml.stylometry import extract_stylometric_features
from app.ml.perplexity_analyzer import analyze_perplexity_and_burstiness

scan_bp = Blueprint('scan', __name__)

def make_json_safe(obj):
    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}

    if isinstance(obj, list):
        return [make_json_safe(i) for i in obj]

    if isinstance(obj, tuple):
        return [make_json_safe(i) for i in obj]

    if isinstance(obj, np.ndarray):
        return obj.tolist()

    # Numpy scalar types often appear in ML outputs (json.dumps/Flask may fail)
    if isinstance(obj, (np.float32, np.float64, np.float_)):
        return float(obj)

    if isinstance(obj, (np.int32, np.int64, np.int_)):
        return int(obj)

    if isinstance(obj, (np.bool_,)):
        return bool(obj)

    if isinstance(obj, (np.str_,)):
        return str(obj)

    # Generic numpy scalar fallback
    if hasattr(np, "generic") and isinstance(obj, np.generic):
        return obj.item()

    return obj

@scan_bp.route('/detect', methods=['POST'])
@jwt_required()
def detect():
    user_id = get_jwt_identity()
    text = ""
    
    # Handle file uploads or plain text JSON
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
        # Support both JSON ({ "text": "..." }) and multipart/form-data ({ text: "..." })
        data = request.get_json(silent=True) or {}
        text = data.get('text', '') or request.form.get('text', '') or ''
        
    if not text.strip():
        return jsonify({'error': 'No text provided'}), 400
        
    # 1. Perform Web-Scale Semantic Plagiarism Scan
    plag_results = perform_semantic_plagiarism_scan(text)
    
    # 2. Advanced Ensemble AI Classifier
    model_path = current_app.config['MODEL_PATH']
    is_ai, ai_confidence = predict_ai_generated(text, model_path)
    
    # 3. AI Likelihood Heatmap
    ai_heatmap = get_sentence_heatmap(text, model_path)
    
    # 4. Stylometric & Perplexity Metrics
    stylometry_metrics = extract_stylometric_features(text)
    perplexity_metrics = analyze_perplexity_and_burstiness(text)
    
    # Save scan to Firestore
    try:
        scan_doc = {
            'user_id': user_id,
            'text_excerpt': text[:500] + ('...' if len(text) > 500 else ''),
            'plagiarism_score': float(plag_results['plagiarism_score']),
            'matches': plag_results['matches'],
            'highlighted_sentences': plag_results['highlighted_sentences'],
            'ai_generated': bool(is_ai),
            'ai_confidence': float(ai_confidence),
            'ai_heatmap': ai_heatmap,
            'stylometry': stylometry_metrics,
            'perplexity': perplexity_metrics,
            # Firestore stores naive/aware datetimes; ensure tz-aware for consistent sorting.
            'created_at': datetime.now(timezone.utc)
        }

        result = db.scans.insert_one(scan_doc)
        scan_id = str(result.inserted_id)

        response_data = {
            'scan_id': scan_id,
            'plagiarism_score': scan_doc['plagiarism_score'],
            'matches': scan_doc['matches'],
            'highlighted_sentences': scan_doc['highlighted_sentences'],
            'ai_generated': scan_doc['ai_generated'],
            'ai_confidence': scan_doc['ai_confidence'],
            'ai_heatmap': scan_doc['ai_heatmap'],
            'stylometry': scan_doc['stylometry'],
            'perplexity': scan_doc['perplexity']
        }
        return jsonify(make_json_safe(response_data))
    except Exception as e:
        return jsonify({'error': 'Scan save/response failed', 'details': str(e)}), 500
