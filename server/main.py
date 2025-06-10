from flask import Flask, jsonify, make_response, request
from flask_cors import CORS
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import blueprints
from tasks import tasks_bp
from projects import projects_bp
from health import health_bp

# Import auth module
from auth import generate_tokens, refresh_access_token, require_auth
import jwt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configure CORS with more permissive settings for development
CORS(app, 
     resources={r"/*": {"origins": ["http://localhost:3000", "https://*.vercel.app"]}},
     allow_headers=['Content-Type', 'X-User-ID', 'Authorization'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     supports_credentials=True)

# Add explicit OPTIONS handler
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "http://localhost:3000")
        response.headers.add('Access-Control-Allow-Headers', "Content-Type, X-User-ID, Authorization")
        response.headers.add('Access-Control-Allow-Methods', "GET, POST, PUT, DELETE, OPTIONS")
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

# Add after_request handler to ensure headers are added
@app.after_request
def after_request(response):
    origin = request.headers.get('Origin')
    if origin in ['http://localhost:3000', 'http://localhost:3001']:
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# Register blueprints
app.register_blueprint(health_bp)
app.register_blueprint(tasks_bp)
app.register_blueprint(projects_bp)

# Authentication endpoints
@app.route('/api/auth/token', methods=['POST'])
def create_token():
    """Generate JWT tokens for authenticated Supabase user"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400
        
        # Generate tokens
        tokens = generate_tokens(user_id)
        return jsonify(tokens), 200
        
    except Exception as e:
        logger.error(f"Error creating token: {e}")
        return jsonify({'error': 'Failed to create token'}), 500

@app.route('/api/auth/refresh', methods=['POST'])
def refresh_token():
    """Refresh access token using refresh token"""
    try:
        data = request.get_json()
        refresh_token = data.get('refresh_token')
        
        if not refresh_token:
            return jsonify({'error': 'refresh_token is required'}), 400
        
        # Generate new access token
        result = refresh_access_token(refresh_token)
        return jsonify(result), 200
        
    except jwt.InvalidTokenError as e:
        return jsonify({'error': str(e)}), 401
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        return jsonify({'error': 'Failed to refresh token'}), 500

@app.route('/api/auth/verify', methods=['GET'])
@require_auth
def verify_token():
    """Verify the current token is valid"""
    return jsonify({
        'valid': True,
        'user_id': request.user_id
    }), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting Flask server on port {port}")
    logger.info(f"Debug mode: {debug}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
