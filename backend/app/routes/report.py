from flask import Blueprint, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
import io
from reportlab.pdfgen import canvas

report_bp = Blueprint('report', __name__)

@report_bp.route('', methods=['GET'])
@jwt_required()
def get_user_reports():
    user_id = get_jwt_identity()
    scans = list(db.scans.find({'user_id': user_id}).sort('created_at', -1))
    for s in scans:
        s['_id'] = str(s['_id'])
        s['user_id'] = str(s['user_id'])
        if 'created_at' in s:
            s['created_at'] = s['created_at'].isoformat()
    return jsonify(scans)

@report_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_user_stats():
    user_id = get_jwt_identity()
    total_scans = db.scans.count_documents({'user_id': user_id})
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": None, "avg_plag": {"$avg": "$plagiarism_score"}, "avg_ai": {"$avg": "$ai_confidence"}}}
    ]
    res = list(db.scans.aggregate(pipeline))
    avg_plag = res[0]['avg_plag'] if res else 0
    avg_ai = res[0]['avg_ai'] if res else 0
    return jsonify({
        'total_scans': total_scans,
        'avg_plagiarism': round(avg_plag, 2),
        'avg_ai_confidence': round(avg_ai, 2)
    })

@report_bp.route('/<scan_id>', methods=['GET'])
@jwt_required()
def get_report(scan_id):
    scan = db.scans.find_one({'_id': scan_id})
    if not scan:
        return jsonify({'error': 'Scan not found'}), 404
    scan['_id'] = str(scan['_id'])
    scan['user_id'] = str(scan['user_id'])
    if 'created_at' in scan:
        scan['created_at'] = scan['created_at'].isoformat()
    return jsonify(scan)

@report_bp.route('/<scan_id>/pdf', methods=['GET'])
@jwt_required()
def get_pdf(scan_id):
    scan = db.scans.find_one({'_id': scan_id})
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
