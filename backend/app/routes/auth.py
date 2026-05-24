from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
import bcrypt
from app.extensions import db

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
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        return jsonify({'msg': 'Invalid credentials'}), 401

    access_token = create_access_token(identity=str(user['_id']))
    return jsonify({
        'access_token': access_token,
        'email': user['email'],
        'name': user.get('name', email.split('@')[0]),
        'role': user.get('role', 'user')
    }), 200


@auth_bp.route('/me', methods=['GET'])
def me():
    from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
    from bson import ObjectId
    verify_jwt_in_request()
    user_id = get_jwt_identity()
    user = db.users.find_one({'_id': ObjectId(user_id)}, {'password': 0})
    if not user:
        return jsonify({'msg': 'User not found'}), 404
    user['_id'] = str(user['_id'])
    return jsonify(user), 200
