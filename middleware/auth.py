from functools import wraps
from flask import request, jsonify
import firebase_admin
from firebase_admin import auth, credentials
import os

# Initialize Firebase Admin SDK
cred = credentials.Certificate('medgenaifirebase.json')
firebase_admin.initialize_app(cred)


def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'No token provided'}), 401
            
        token = auth_header.split('Bearer ')[1]
        try:
            # Add clock tolerance of 5 seconds
            decoded_token = auth.verify_id_token(
                token,
                clock_skew_seconds=5  # Add this parameter
            )
            request.user_id = decoded_token['uid']
            return f(*args, **kwargs)
        except Exception as e:
            print("Auth error:", str(e))  # Debug print
            return jsonify({'error': 'Invalid token', 'details': str(e)}), 401
            
    return decorated_function
from flask import Blueprint, request, jsonify
from firebase_admin import auth
import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/auth/session', methods=['POST'])
def create_session():
    try:
        # Get the ID token from the request
        id_token = request.json.get('idToken')
        if not id_token:
            return jsonify({'error': 'No ID token provided'}), 400

        # Verify the ID token and create a session cookie
        # Set session expiration to 5 days
        expires_in = datetime.timedelta(days=5)
        
        # Create the session cookie using Firebase Admin SDK
        session_cookie = auth.create_session_cookie(id_token, expires_in=expires_in)
        
        response = jsonify({'sessionCookie': session_cookie})
        
        return response, 200

    except Exception as e:
        return jsonify({'error': str(e)}), 401