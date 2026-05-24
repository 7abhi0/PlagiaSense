import re
import bcrypt
import jwt
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from pymongo import MongoClient

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Mongo client
client = MongoClient(current_app.config['MONGO_URI'])
 db = client.get_default_database()
users_coll = db['users']

def create_jwt(user_id):
    payload = {
        'sub': str(user_id),
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    token = jwt.encode(payload, current_app.config['JWT_SECRET'], algorithm='HS256')
    return token

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({'msg': 'Email and password required'}), 400
    if users_coll.find_one({'email': email}):
        return jsonify({'msg': 'User already exists'}), 409
    # Simple email validation
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify({'msg': 'Invalid email'}), 400
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    user = {'email': email, 'password': hashed, 'created_at': datetime.utcnow()}
    result = users_coll.insert_one(user)
    token = create_jwt(result.inserted_id)
    return jsonify({'token': token}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({'msg': 'Email and password required'}), 400
    user = users_coll.find_one({'email': email})
    if not user:
        return jsonify({'msg': 'Invalid credentials'}), 401
    if not bcrypt.checkpw(password.encode('utf-8'), user['password']):
        return jsonify({'msg': 'Invalid credentials'}), 401
    token = create_jwt(user['_id'])
    return jsonify({'token': token}), 200
