import json
import os
from bottle import Bottle, request, response, HTTPError
from database import db
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Debugging support - enable when DEBUG_PYTHON=true
debug_python = os.getenv('DEBUG_PYTHON', 'false').lower() == 'true'
if debug_python:
    import debugpy
    debugpy.listen(("0.0.0.0", 5679))
    print("⏳ Debugger is listening on 0.0.0.0:5679")
    if os.getenv('DEBUG_WAIT', 'false').lower() == 'true':
        debugpy.wait_for_client()
        print("🔗 Debugger is attached!")

app = Bottle()

# Authentication decorator
def require_auth(f):
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            raise HTTPError(401, 'Unauthorized')
        
        token = token.split(' ')[1]
        user_id = db.get_session_user_id(token)
        
        if not user_id:
            raise HTTPError(401, 'Invalid or expired token')
        
        request.user_id = user_id
        return f(*args, **kwargs)
    
    return decorated

@app.route('/login', method='POST')
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        raise HTTPError(400, 'Username and password required')
    
    # Authenticate user
    user_id = db.authenticate_user(username, password)
    
    if not user_id:
        raise HTTPError(401, 'Invalid credentials')
    
    # Create session
    session = db.create_session(user_id)
    
    response.content_type = 'application/json'
    return json.dumps({
        'token': session['token'],
        'expires_at': session['expires_at'],
        'message': 'Login successful'
    })

@app.route('/logout', method='POST')
@require_auth
def logout():
    token = request.headers.get('Authorization').split(' ')[1]
    
    db.delete_session(token)
    
    response.content_type = 'application/json'
    return json.dumps({'message': 'Logout successful'})

@app.route('/profile', method='GET')
@require_auth
def get_profile():
    user_profile = db.get_user_profile(request.user_id)
    
    if not user_profile:
        raise HTTPError(404, 'User not found')
    
    response.content_type = 'application/json'
    return json.dumps(user_profile)

@app.route('/health', method='GET')
def health_check():
    response.content_type = 'application/json'
    return json.dumps({'status': 'ok', 'message': 'API is running'})

if __name__ == '__main__':
    host = os.getenv('HOST', 'localhost')
    port = int(os.getenv('PORT', '8080'))
    debug = os.getenv('DEBUG', 'true').lower() == 'true'
    
    # Force reloader to be disabled when debugging to prevent port conflicts
    reloader = False if debug_python else os.getenv('RELOADER', 'true').lower() == 'true'
    
    admin_username = os.getenv('DEFAULT_ADMIN_USERNAME', 'admin')
    admin_password = os.getenv('DEFAULT_ADMIN_PASSWORD', 'admin123')
    
    print(f"Database initialized with admin user (username: {admin_username}, password: {admin_password})")
    print(f"Starting server on http://{host}:{port}")
    print(f"Debug mode: {debug}")
    print(f"Reloader enabled: {reloader}")
    print(f"Python debugging: {debug_python}")
    
    app.run(host=host, port=port, debug=debug, reloader=reloader) 