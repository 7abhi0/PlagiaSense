import os
import time
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

def json_error(code: str, message: str, *, details=None, http_status: int = 400):
    payload = {"error": {"code": code, "message": message}}
    if details is not None:
        payload["error"]["details"] = details
    return jsonify(make_json_safe(payload)), http_status


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
    filepath = None

    request_start = time.time()

    # Hard deadline for the entire request pipeline (best-effort)
    # Keep it below Gunicorn --timeout to avoid worker kill.
    TOTAL_DEADLINE_SECONDS = float(os.getenv("SCAN_REQUEST_DEADLINE_SECONDS", "110"))

    def deadline_exceeded() -> bool:
        return (time.time() - request_start) > TOTAL_DEADLINE_SECONDS

    try:
        # Handle file uploads or plain text JSON
        truncated = False
        MAX_CHARS = int(os.getenv("MAX_INPUT_CHARS", "25000"))  # reduced for stability
        word_count = 0

        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename != '':
                # Reject files > 10MB
                file.seek(0, os.SEEK_END)
                size = file.tell()
                file.seek(0)
                if size > 10 * 1024 * 1024:
                    return jsonify({'error': 'File too large. Max 10MB allowed.'}), 413

                filename = str(uuid.uuid4()) + "_" + file.filename
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                try:
                    text = extract_text(filepath)
                except Exception as e:
                    current_app.logger.exception("File parse/extract failed")
                    return jsonify({'error': 'file parse error', 'details': str(e)}), 400
                finally:
                    if filepath and os.path.exists(filepath):
                        os.remove(filepath)
        else:
            # Support both JSON ({ "text": "..." }) and multipart/form-data ({ text: "..." })
            data = request.get_json(silent=True) or {}
            text = data.get('text', '') or request.form.get('text', '') or ''

        if not text or not text.strip():
            return json_error("bad_request", "No text provided", http_status=400)

        if deadline_exceeded():
            return json_error("timeout", "Request deadline exceeded", http_status=504)

        # Truncate extremely large inputs for token safety + memory stability.
        if len(text) > MAX_CHARS:
            text = text[:MAX_CHARS]
            truncated = True

        word_count = len(text.split())

        if deadline_exceeded():
            return json_error("timeout", "Request deadline exceeded", http_status=504)

        # 1. Perform Web-Scale Semantic Plagiarism Scan
        try:
            plag_results = perform_semantic_plagiarism_scan(text)
        except TimeoutError as e:
            current_app.logger.exception("Plagiarism scan timeout")
            return json_error("timeout", "Web plagiarism scan timed out", details=str(e), http_status=504)
        except Exception as e:
            current_app.logger.exception("Plagiarism scan failed")
            return json_error("internal_error", "Web plagiarism scan failed", details=str(e), http_status=500)

        # 2. Advanced Ensemble AI Classifier
        model_path = current_app.config['MODEL_PATH']
        try:
            if deadline_exceeded():
                return json_error("timeout", "Request deadline exceeded", http_status=504)
            is_ai, ai_confidence = predict_ai_generated(text, model_path)
        except Exception as e:
            current_app.logger.exception("AI classifier failed")
            return json_error("internal_error", "AI classifier failed", details=str(e), http_status=500)

        # 3. AI Likelihood Heatmap
        try:
            if deadline_exceeded():
                return json_error("timeout", "Request deadline exceeded", http_status=504)
            ai_heatmap = get_sentence_heatmap(text, model_path)
        except Exception as e:
            current_app.logger.exception("AI heatmap generation failed")
            return json_error("internal_error", "AI heatmap generation failed", details=str(e), http_status=500)

        # 4. Stylometric & Perplexity Metrics
        try:
            if deadline_exceeded():
                return json_error("timeout", "Request deadline exceeded", http_status=504)
            stylometry_metrics = extract_stylometric_features(text)
            perplexity_metrics = analyze_perplexity_and_burstiness(text)
        except Exception as e:
            current_app.logger.exception("Stylometry/perplexity analysis failed")
            return json_error("internal_error", "Stylometry/perplexity analysis failed", details=str(e), http_status=500)

        # Save scan to Firestore
        scan_doc = {
            'user_id': user_id,
            'text_excerpt': text[:500] + ('...' if len(text) > 500 else ''),
            'plagiarism_score': float(plag_results.get('plagiarism_score', 0)),
            'matches': plag_results.get('matches', []),
            'highlighted_sentences': plag_results.get('highlighted_sentences', []),
            'ai_generated': bool(is_ai),
            'ai_confidence': float(ai_confidence),
            'ai_heatmap': ai_heatmap,
            'stylometry': stylometry_metrics,
            'perplexity': perplexity_metrics,
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
            'perplexity': scan_doc['perplexity'],
            'truncated': truncated,
            'word_count': word_count,
            'chunks_scanned': plag_results.get('chunks_scanned', 1)
        }

        if deadline_exceeded():
            return json_error("timeout", "Request deadline exceeded", http_status=504)

        return jsonify(make_json_safe(response_data))

    except Exception as e:
        # Do not leak internal state/stack traces to clients.
        current_app.logger.exception("Unhandled scan detect error")
        return json_error("internal_error", "Unhandled scan error", details=str(e), http_status=500)

