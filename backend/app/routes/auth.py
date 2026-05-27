from flask import Blueprint, current_app, request, jsonify
from flask_jwt_extended import create_access_token
import bcrypt
from app.extensions import db
from app.utils.firebase_auth import verify_firebase_id_token

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    name = data.get('name', email.split('@')[0])

    if not email or not password:
        return jsonify({'msg': 'Email and password are required'}), 400

    if db.users.find_one({'email': email}):
        return jsonify({'msg': 'User already exists'}), 409

    pw_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user = {'email': email, 'password': pw_hash, 'name': name, 'role': 'user'}
    result = db.users.insert_one(user)
    access_token = create_access_token(identity=str(result.inserted_id))
    return jsonify({'access_token': access_token, 'email': email, 'name': name}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'msg': 'Email and password are required'}), 400

    user = db.users.find_one({'email': email})
    if not user or not user.get('password') or not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        return jsonify({'msg': 'Invalid credentials'}), 401

    access_token = create_access_token(identity=str(user['_id']))
    return jsonify({
        'access_token': access_token,
        'email': user['email'],
        'name': user.get('name', email.split('@')[0]),
        'role': user.get('role', 'user')
    }), 200


@auth_bp.route('/firebase', methods=['POST', 'OPTIONS'])
def firebase_login():
    # Ensure CORS preflight doesn't 404 when calling this endpoint
    if request.method == 'OPTIONS':
        return ('', 204)

    data = request.get_json() or {}
    id_token = data.get('id_token', '')
    requested_name = data.get('name', '')

    if not id_token:
        return jsonify({'msg': 'Firebase ID token is required'}), 400

    try:
        decoded = verify_firebase_id_token(id_token, current_app.config['FIREBASE_PROJECT_ID'])
    except Exception as exc:
        return jsonify({'msg': 'Invalid Firebase token', 'details': str(exc)}), 401

    firebase_uid = decoded.get('sub')
    email = (decoded.get('email') or '').strip().lower()
    name = requested_name or decoded.get('name') or (email.split('@')[0] if email else 'Firebase User')

    if not firebase_uid or not email:
        return jsonify({'msg': 'Firebase token is missing required user claims'}), 400

    user = db.users.find_one({'firebase_uid': firebase_uid}) or db.users.find_one({'email': email})
    if user:
        updates = {'firebase_uid': firebase_uid, 'email': email, 'name': user.get('name') or name}
        db.users.update_one({'_id': user['_id']}, {'$set': updates})
        user.update(updates)
    else:
        user_doc = {
            'firebase_uid': firebase_uid,
            'email': email,
            'name': name,
            'role': 'user',
            'auth_provider': 'firebase',
        }
        result = db.users.insert_one(user_doc)
        user = {**user_doc, '_id': result.inserted_id}

    access_token = create_access_token(identity=str(user['_id']))
    return jsonify({
        'access_token': access_token,
        'email': user['email'],
        'name': user.get('name', name),
        'role': user.get('role', 'user')
    }), 200


@auth_bp.route('/me', methods=['GET'])
def me():
    from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
    verify_jwt_in_request()
    user_id = get_jwt_identity()
    user = db.users.find_one({'_id': user_id}, {'password': 0})
    if not user:
        return jsonify({'msg': 'User not found'}), 404
    user['_id'] = str(user['_id'])
    return jsonify(user), 200
