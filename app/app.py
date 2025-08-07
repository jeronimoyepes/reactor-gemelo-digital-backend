import json
import os
import uuid
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

# Create uploads directory if it doesn't exist
UPLOADS_DIR = os.getenv('UPLOADS_DIR', 'uploads')
os.makedirs(UPLOADS_DIR, exist_ok=True)

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

# Reactor Experiment Endpoints
@app.route('/reactor/upload', method='POST')
@require_auth
def upload_reactor_experiment():
    """Upload Excel file and store reactor experiment parameters"""
    
    # Get form data
    experiment_name = request.forms.get('experiment_name')
    if not experiment_name:
        raise HTTPError(400, 'Experiment name is required')
    
    # Get Excel file
    excel_file = request.files.get('excel_file')
    if not excel_file:
        raise HTTPError(400, 'Excel file is required')
    
    # Validate file type
    if not excel_file.filename.lower().endswith(('.xlsx', '.xls')):
        raise HTTPError(400, 'Only Excel files (.xlsx, .xls) are allowed')
    
    # Generate unique filename
    file_extension = os.path.splitext(excel_file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOADS_DIR, unique_filename)
    
    # Save file
    try:
        excel_file.save(file_path)
    except Exception as e:
        raise HTTPError(500, f'Failed to save file: {str(e)}')
    
    # Create experiment in database
    try:
        experiment_id = db.create_reactor_experiment(request.user_id, experiment_name, file_path)
    except Exception as e:
        # Clean up file if database operation fails
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPError(500, f'Failed to create experiment: {str(e)}')
    
    # Store parameters
    parameters = {}
    
    # Time parameters
    t_add = request.forms.get('t_add')
    if t_add:
        parameters['t_add'] = float(t_add)
    
    t_span_start = request.forms.get('t_span_start')
    t_span_end = request.forms.get('t_span_end')
    if t_span_start and t_span_end:
        parameters['t_span'] = [float(t_span_start), float(t_span_end)]
    
    dt = request.forms.get('dt')
    if dt:
        parameters['dt'] = float(dt)
    
    # Adjustment factors
    f_j1 = request.forms.get('f_j1')
    f_j2 = request.forms.get('f_j2')
    if f_j1 and f_j2:
        parameters['adj_factor'] = [float(f_j1), float(f_j2)]
    
    # Initial conditions (optional - will use defaults if not provided)
    initial_conditions = [
        'L_0i', 'CVAM_r0i', 'CBA_r0i', 'CNaPS_r0i', 'CTBHP_r0i', 
        'CCRD_r0i', 'CMPOL_r0i', 'Np_r0i', 'T1_0i', 'T3_0i'
    ]
    
    for param in initial_conditions:
        value = request.forms.get(param)
        if value:
            parameters[param] = float(value)
    
    # Store parameters in database
    if parameters:
        if not db.store_reactor_parameters(experiment_id, parameters):
            raise HTTPError(500, 'Failed to store experiment parameters')
    
    response.content_type = 'application/json'
    return json.dumps({
        'experiment_id': experiment_id,
        'experiment_name': experiment_name,
        'status': 'pending',
        'message': 'Experiment uploaded successfully and queued for processing'
    })

@app.route('/reactor/experiments', method='GET')
@require_auth
def get_user_experiments():
    """Get all experiments for the current user"""
    experiments = db.get_user_experiments(request.user_id)
    
    response.content_type = 'application/json'
    return json.dumps({
        'experiments': experiments
    })

@app.route('/reactor/experiments/<experiment_id:int>', method='GET')
@require_auth
def get_experiment_details(experiment_id):
    """Get experiment details and status"""
    experiment = db.get_experiment_by_id(experiment_id)
    
    if not experiment:
        raise HTTPError(404, 'Experiment not found')
    
    # Check if user owns this experiment
    if experiment['user_id'] != request.user_id:
        raise HTTPError(403, 'Access denied')
    
    # Get parameters and results if available
    parameters = db.get_reactor_parameters(experiment_id)
    results = {}
    
    if experiment['status'] == 'completed':
        results = db.get_reactor_results(experiment_id)
    
    response.content_type = 'application/json'
    return json.dumps({
        'experiment': experiment,
        'parameters': parameters,
        'results': results
    })

@app.route('/reactor/experiments/<experiment_id:int>/results', method='GET')
@require_auth
def get_experiment_results(experiment_id):
    """Get experiment results (if completed)"""
    experiment = db.get_experiment_by_id(experiment_id)
    
    if not experiment:
        raise HTTPError(404, 'Experiment not found')
    
    # Check if user owns this experiment
    if experiment['user_id'] != request.user_id:
        raise HTTPError(403, 'Access denied')
    
    if experiment['status'] != 'completed':
        raise HTTPError(400, 'Experiment is not completed yet')
    
    results = db.get_reactor_results(experiment_id)
    
    response.content_type = 'application/json'
    return json.dumps({
        'experiment_id': experiment_id,
        'results': results
    })

@app.route('/reactor/experiments/<experiment_id:int>/retry', method='POST')
@require_auth
def retry_experiment(experiment_id):
    """Retry a failed experiment (if not permanently failed)"""
    experiment = db.get_experiment_by_id(experiment_id)
    
    if not experiment:
        raise HTTPError(404, 'Experiment not found')
    
    # Check if user owns this experiment
    if experiment['user_id'] != request.user_id:
        raise HTTPError(403, 'Access denied')
    
    # Check if experiment can be retried
    if experiment['status'] == 'failed_permanently':
        raise HTTPError(400, 'Experiment cannot be retried - permanently failed')
    
    if experiment['status'] == 'completed':
        raise HTTPError(400, 'Experiment is already completed')
    
    if experiment['status'] == 'running':
        raise HTTPError(400, 'Experiment is currently running')
    
    # Reset experiment to pending
    db.update_experiment_status(experiment_id, 'pending')
    
    response.content_type = 'application/json'
    return json.dumps({
        'experiment_id': experiment_id,
        'message': 'Experiment reset to pending for retry'
    })

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
    
    admin_username = os.getenv('DEFAULT_ADMIN_USERNAME')
    admin_password = os.getenv('DEFAULT_ADMIN_PASSWORD')
    
    print(f"Database initialized with admin user (username: {admin_username}, password: {admin_password})")
    print(f"Starting server on http://{host}:{port}")
    print(f"Debug mode: {debug}")
    print(f"Reloader enabled: {reloader}")
    print(f"Python debugging: {debug_python}")
    print(f"Uploads directory: {UPLOADS_DIR}")
    
    app.run(host=host, port=port, debug=debug, reloader=reloader) 