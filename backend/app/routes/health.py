from flask import Blueprint, jsonify

health_bp = Blueprint('health', __name__)

@health_bp.route('/', methods=['GET', 'HEAD'])
def index():
    return jsonify({'service': 'plagiasense-backend', 'status': 'ok'}), 200


@health_bp.route('/health', methods=['GET', 'HEAD'])
def health():
    return jsonify({'status':'ok'}), 200
