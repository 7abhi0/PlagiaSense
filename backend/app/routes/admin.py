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
