import os
import logging
from datetime import datetime, timezone
from functools import wraps
from jose import jwt, JWTError
from flask import Flask, render_template, jsonify, request, abort
from bson.objectid import ObjectId
from db import get_db
from auth import hash_password, verify_password, create_access_token

# ==========================================
# SYSTEM SETUP & LOGGING CONFIGURATION
# ==========================================
from dotenv import load_dotenv

# Load local environmental variables from your hidden secure .env asset file
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "dev_super_secret_key_change_in_production_32bytes_long")

logger = logging.getLogger("SparkMargCore")


# ==========================================
# AUTHENTICATION & MULTI-TENANCY MIDDLEWARE
# ==========================================
def token_required(f):
    """
    Enforces strict access control limits. Decodes the incoming JSON Web Token
    and injects the verified current user identifier context directly into protected routes.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Authentication credentials missing or malformed"}), 401
        
        try:
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user_id = str(payload.get("sub"))
            if not current_user_id:
                raise ValueError("Subject claim missing from token profile payload.")
        except (JWTError, ValueError) as token_err:
            logger.warning(f"Unauthorized intrusion blocked: {token_err}")
            return jsonify({"error": "Invalid access credentials context profile"}), 401
            
        return f(current_user_id, *args, **kwargs)
    return decorated


# ==========================================
# PAGE ROUTING VIEWS
# ==========================================
@app.route('/')
def index(): return render_template('index.html')

@app.route('/login')
def login(): return render_template('login.html')

@app.route('/register')
def register(): return render_template('register.html')

@app.route('/catalog')
def catalog(): return render_template('catalog.html')

@app.route('/dashboard')
def dashboard(): return render_template('dashboard.html')

@app.route('/simulation')
def simulation(): return render_template('simulation.html')


# ==========================================
# CORE IDENTITY & PROFILE API
# ==========================================
@app.route('/api/v1/auth/me', methods=['GET'], strict_slashes=False)
@app.route('/api/auth/me', methods=['GET'], strict_slashes=False)
@token_required
def auth_me(current_user_id):
    """Fetches full authenticated contextual profile records belonging strictly to the requester."""
    try:
        db = get_db()
        user = db["users"].find_one({"_id": ObjectId(current_user_id)})
        if not user:
            return jsonify({"error": "Associated security account context not found"}), 404
            
        return jsonify({
            "authenticated": True,
            "user": {
                "id": str(user["_id"]),
                "full_name": user.get("full_name", "Anonymous Developer"),
                "email": user.get("email")
            }
        })
    except Exception as e:
        logger.error(f"Failed to fetch profile: {e}")
        return jsonify({"error": "Internal profile processing engine error"}), 500


# ==========================================
# GLOBAL CAREER BLUEPRINT CATALOG ENDPOINTS
# ==========================================
@app.route('/api/v1/simulations', methods=['GET'], strict_slashes=False)
@token_required
def get_simulations(current_user_id):
    """Retrieves simulation scenarios dynamically with optional domain filtering and text search parameters."""
    try:
        db = get_db()
        
        # 1. Capture query parameter inputs from incoming requests URL query string
        domain = request.args.get('domain')
        search = request.args.get('search')
        
        # 2. Dynamically compile the MongoDB search query structure
        query = {}
        if domain and domain.upper() != "ALL":
            query["domain"] = domain

        if search:
            query["$or"] = [
                {"title": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}}
            ]
            
        # 3. Fetch matching data rows (excluding heavy nested tree paths for the summary list view)
        cursor = db["simulations"].find(query, {"steps": 0})
        
        simulations = []
        for sim in cursor:
            sim["id"] = str(sim.get("id", sim["_id"]))
            if "_id" in sim: 
                del sim["_id"]
            simulations.append(sim)
            
        return jsonify(simulations)
    except Exception as e:
        logger.error(f"Catalog collection gathering crash: {e}")
        return jsonify({"error": "Failed to compile the available track lists"}), 500


@app.route('/api/v1/simulations/<sim_id>', methods=['GET'], strict_slashes=False)
@token_required
def get_single_simulation(current_user_id, sim_id):
    """Fetches details for a specific simulation including its complete interactive node trees."""
    try:
        db = get_db()
        sim = db["simulations"].find_one({"id": sim_id})
        if not sim:
            return jsonify({"error": "Targeted simulation path not present within master definitions"}), 404
            
        sim["id"] = str(sim.get("id", sim["_id"]))
        if "_id" in sim: del sim["_id"]
        return jsonify(sim)
    except Exception as e:
        logger.error(f"Blueprint query crash on node {sim_id}: {e}")
        return jsonify({"error": "Failed to open selected trajectory schema"}), 500


# ==========================================
# USER-ISOLATED INTERACTIVE SIMULATION RUNNER
# ==========================================
@app.route('/api/v1/progress/start/<sim_id>', methods=['POST'], strict_slashes=False)
@token_required
def initialize_or_resume_session(current_user_id, sim_id):
    """Ensures a user-scoped, multi-tenant track logging profile instance starts accurately."""
    try:
        db = get_db()
        
        # Guard Constraint: Is there already an ongoing sandbox timeline for this user?
        existing_session = db["user_progress"].find_one({"user_id": current_user_id, "simulation_id": sim_id})
        if existing_session:
            existing_session["_id"] = str(existing_session["_id"])
            return jsonify(existing_session)
            
        # Target metadata blueprint definitions
        meta = db["simulations"].find_one({"id": sim_id})
        if not meta:
            return jsonify({"error": "Cannot establish track session. Core master blueprint missing."}), 404
            
        # Dynamically map initial step coordinates using entry index sequence pointers
        starting_step_id = "End"
        if meta.get("steps") and len(meta["steps"]) > 0:
            starting_step_id = meta["steps"][0]["step_id"]
            
        new_session = {
            "user_id": current_user_id, # Strict Ownership Binding Applied
            "simulation_id": sim_id,
            "title": meta.get("title", "Interactive Simulation Path"),
            "domain": meta.get("domain", "General Track"),
            "current_step_id": starting_step_id,
            "status": "IN_PROGRESS",
            "history": [],
            "scores": {"leadership": 0, "technical": 0, "problem_solving": 0, "communication": 0},
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        result = db["user_progress"].insert_one(new_session)
        new_session["_id"] = str(result.inserted_id)
        return jsonify(new_session), 201
    except Exception as e:
        logger.error(f"Session setup breakdown on node {sim_id}: {e}")
        return jsonify({"error": "Failed to create runtime simulation tracker environment"}), 500


@app.route('/api/v1/progress/<sim_id>/decision', methods=['POST'], strict_slashes=False)
@token_required
def submit_decision_choice(current_user_id, sim_id):
    """
    Evaluates branching logic options, validates step state alignment, 
    updates cumulative user-profile competencies, and shifts progression coordinates.
    """
    data = request.get_json(silent=True) or {}
    step_id = data.get("step_id")
    option_id = data.get("option_id")
    
    if not all([sim_id, step_id, option_id]):
        return jsonify({"error": "Missing required transaction payloads: simulation_id, step_id, and option_id."}), 400
        
    try:
        db = get_db()
        
        # 1. Pull user state record with strict tenant validation constraints
        session = db["user_progress"].find_one({
            "user_id": current_user_id, 
            "simulation_id": sim_id, 
            "status": "IN_PROGRESS"
        })
        if not session:
            return jsonify({"error": "No active simulation logs found for this targeted space context."}), 404
            
        if session["current_step_id"] != step_id:
            return jsonify({"error": "Out of sync state error. Node pointer synchronization mismatch."}), 409
            
        # 2. Fetch the master blueprint configuration definition map
        blueprint = db["simulations"].find_one({"id": sim_id})
        if not blueprint:
            return jsonify({"error": "Underlying simulation structural configuration mapping missing."}), 404
            
        # Find active node structures matching the timeline sequence
        step_node = next((s for s in blueprint.get("steps", []) if s["step_id"] == step_id), None)
        if not step_node:
            return jsonify({"error": "Targeted timeline step block details unavailable."}), 404
            
        # Find explicit details matching selected tracking action selections
        chosen_option = next((o for o in step_node.get("options", []) if o["option_id"] == option_id), None)
        if not chosen_option:
            return jsonify({"error": "Invalid alternative option node selection mapping reference code"}), 400
            
        # 3. Calculate competency increments and append to the user history ledger
        current_scores = session.get("scores", {"leadership": 0, "technical": 0, "problem_solving": 0, "communication": 0})
        impact_deltas = chosen_option.get("impact", {})
        for metric in current_scores:
            current_scores[metric] += impact_deltas.get(metric, 0)
            
        history_entry = {
            "step_id": step_id,
            "step_title": step_node.get("title", "Interactive Decision Step"),
            "chosen_option_id": option_id,
            "option_text": chosen_option.get("text"),
            "feedback": chosen_option.get("feedback"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        next_step_pointer = chosen_option.get("next_step_id")
        session_status = "IN_PROGRESS"
        completed_timestamp = None
        
        # Terminate running state records if tracking links resolve to null pointers
        if not next_step_pointer:
            session_status = "COMPLETED"
            completed_timestamp = datetime.now(timezone.utc).isoformat()
            
        # 4. Atomically commit updates down to MongoDB storage pools
        update_payload = {
            "$set": {
                "current_step_id": next_step_pointer,
                "status": session_status,
                "scores": current_scores,
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            "$push": {"history": history_entry}
        }
        if completed_timestamp:
            update_payload["$set"]["completed_at"] = completed_timestamp
            
        db["user_progress"].update_one({"_id": session["_id"]}, update_payload)
        
        # Build complete operational confirmation dictionary output object
        return jsonify({
            "status": session_status,
            "current_step_id": next_step_pointer,
            "feedback": chosen_option.get("feedback"),
            "updated_scores": current_scores
        })
        
    except Exception as e:
        logger.error(f"Transaction pipeline collapse during execution step evaluation processing: {e}")
        return jsonify({"error": "Failed to record user interaction selection"}), 500


# ==========================================
# USER DASHBOARD DATA & COMPETENCY ANALYTICS
# ==========================================
@app.route('/api/v1/progress/active', methods=['GET'], strict_slashes=False)
@token_required
def get_active_progress(current_user_id):
    """Fetches incomplete branching tracks currently underway for the active user only."""
    try:
        db = get_db()
        cursor = db["user_progress"].find({"user_id": current_user_id, "status": "IN_PROGRESS"})
        active_runs = []
        for run in cursor:
            active_runs.append({
                "simulation_id": run["simulation_id"],
                "title": run.get("title", "Active Running Pipeline"),
                "domain": run.get("domain", "General Track"),
                "current_step_id": run.get("current_step_id"),
                "updated_at": run.get("updated_at")
            })
        return jsonify(active_runs)
    except Exception as e:
        logger.error(f"Active tracking pull failure: {e}")
        return jsonify([]), 500


@app.route('/api/v1/progress/history', methods=['GET'], strict_slashes=False)
@token_required
def get_progress_history(current_user_id):
    """Fetches fully resolved tree logs for historical review for the active user only."""
    try:
        db = get_db()
        cursor = db["user_progress"].find({"user_id": current_user_id, "status": "COMPLETED"})
        history_logs = []
        for log in cursor:
            history_logs.append({
                "simulation_id": log["simulation_id"],
                "title": log.get("title", "Completed Path Log"),
                "completed_at": log.get("completed_at"),
                "scores": log.get("scores")
            })
        return jsonify(history_logs)
    except Exception as e:
        logger.error(f"Historical trace gathering exception: {e}")
        return jsonify([]), 500


@app.route('/api/v1/analytics/overview', methods=['GET'], strict_slashes=False)
@token_required
def get_analytics(current_user_id):
    """Calculates cumulative score matrices and totals unique to the requesting identity."""
    try:
        db = get_db()
        completed_runs = list(db["user_progress"].find({"user_id": current_user_id, "status": "COMPLETED"}))
        in_progress_count = db["user_progress"].count_documents({"user_id": current_user_id, "status": "IN_PROGRESS"})
        
        aggregated_scores = {"leadership": 0, "technical": 0, "problem_solving": 0, "communication": 0}
        for run in completed_runs:
            run_scores = run.get("scores", {})
            for competency in aggregated_scores:
                aggregated_scores[competency] += run_scores.get(competency, 0)
                
        return jsonify({
            "total_completed": len(completed_runs),
            "total_in_progress": in_progress_count,
            "scores": aggregated_scores
        })
    except Exception as e:
        logger.error(f"Global dynamic vector matrix metric generation exception: {e}")
        return jsonify({"error": "Failed to compile competency analytics maps"}), 500


# ==========================================
# SYSTEM AUTHENTICATION INTERACTION MANAGER
# ==========================================
@app.route('/api/auth/register', methods=['POST'], strict_slashes=False)
def api_register():
    try:
        db = get_db()
        data = request.get_json(silent=True) or {}
        full_name = data.get('username') or data.get('full_name')
        email = data.get('email')
        password = data.get('password')

        if not all([full_name, email, password]):
            return jsonify({"error": "Missing input registration elements: username/full_name, email, and password."}), 400

        if db["users"].find_one({"email": email}):
            return jsonify({"error": "An account linked with this email is already registered"}), 400

        user_dict = {
            "email": email,
            "password_hash": hash_password(password),
            "full_name": full_name,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        db["users"].insert_one(user_dict)
        return jsonify({"message": "User registered successfully."}), 201
    except Exception as e:
        logger.critical(f"Registration validation fault crash: {e}")
        return jsonify({"error": "Internal account configuration fault encountered"}), 500


@app.route('/api/auth/login', methods=['POST'], strict_slashes=False)
def api_login():
    try:
        db = get_db()
        data = request.get_json(silent=True) or {}
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"error": "Email and password inputs are required."}), 400

        user = db["users"].find_one({"email": email})
        if not user or not verify_password(password, user["password_hash"]):
            return jsonify({"error": "Incorrect email credentials or verification password mismatch"}), 401

        # Embed unique MongoDB Object ID signature into token subject string definition parameters
        access_token = create_access_token(data={"sub": str(user["_id"])})
        return jsonify({"access_token": access_token, "token_type": "bearer"}), 200
    except Exception as e:
        logger.error(f"Login operational engine failure execution trace: {e}")
        return jsonify({"error": "Internal system verification server failure"}), 500


# ==========================================
# GLOBAL CUSTOM ENGINE FAULT EXCEPTION OVERRIDES
# ==========================================
@app.errorhandler(404)
def page_not_found(e):
    if request.path.startswith('/api/'):
        return jsonify({"error": "Requested API route path not verified or registered within active schemas"}), 404
    return render_template('index.html'), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal application engine failure"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)