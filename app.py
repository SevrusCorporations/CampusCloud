# Author - SirSevrus (https://github.com/sevruscorporations)

from flask import Flask, render_template, request, jsonify, session, redirect
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from colorama import Fore, init
import os
import json
import tempfile
import posixpath
import logging

from libs.getQueries import get_queries
from libs.matchFiles import match_query
from libs.encryptor import Encryptor
from libs.db_utils import db_utils
from libs.cloud import InfiniCloudClient   # your InfiniCLOUD library
from libs.time_utils import *

from cryptography.fernet import Fernet

# set up simple logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

limiter = Limiter(
    key_func=get_remote_address,  # identify client by IP
    app=app,
)

CORS(app, supports_credentials=True)
app.secret_key = os.getenv("SECRET_KEY", "change-me-in-prod")  # replace in prod
init(autoreset=True)
VERSION = "1.0.0-alpha"

QUERIES = None
Queries = None
cloud = InfiniCloudClient()   # initialize InfiniCLOUD client once

# Initialize DB (use env var for port if provided)
db = db_utils(
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    port=int(os.getenv("DB_PORT", "6543")),
    sslmode=os.getenv("DB_SSLMODE", "require")
)

def get_encryptor():
    """Load key from DB and return Encryptor instance."""
    # use parameterized queries and fetch_output=True for consistent return format
    result = db.execute("SELECT key FROM keys WHERE id = %s", (1,), fetch_output=True)
    if not result:
        raise ValueError("No key found in DB")
    key_str = result[0][0]
    return Encryptor(str(key_str).strip())

def init_app():
    """Initialize API and load queries."""
    logger.info("API Booting Up...")
    print(Fore.RED + "[ERR] " + Fore.YELLOW + "An Error occurred : Maybe you haven't slept today?")
    print(Fore.RED + "[ERR] " + Fore.YELLOW + "API Will Blast your PC in 5 Seconds... Just Kidding :)")
    print(Fore.GREEN + "[SUCCESS]" + Fore.YELLOW + " API Booted Up Successfully!")

    global Queries, QUERIES
    QUERIES = load_queries()
    Queries = get_queries(QUERIES)

def authenticate_user(username: str, password: str) -> bool:
    """
    Check if username/password are correct.
    Passwords are stored encrypted with Fernet.
    """
    sql = """
        SELECT password
        FROM entities
        WHERE LOWER(name) = LOWER(%s)
        LIMIT 1
    """
    try:
        result = db.execute(sql, (username,), fetch_output=True)
    except Exception as e:
        logger.exception("DB error during authenticate_user")
        return False

    if not result:
        return False

    stored_password = str(result[0][0]).strip()
    encryptor = get_encryptor()

    # Try decrypt → compare
    try:
        plain = encryptor.decrypt(stored_password)
        return plain == password
    except Exception:
        # Maybe stored as plaintext (legacy case)
        return stored_password == password


def load_queries():
    """Load queries JSON file from /data/queries.json"""
    with open("data/queries.json", "r") as file:
        queries_json = json.load(file)
    return queries_json


@app.route("/version", methods=["GET"])
def version():
    return jsonify({"version": VERSION})


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/logout", methods=["POST", "GET"])
@limiter.limit("5 per minute")
def logout():
    # Clear everything in session
    session.clear()
    return redirect("/login")


@app.route("/auth", methods=["POST"])
@limiter.limit("5 per minute")  # Rate limited the /auth
def auth():
    # Accept JSON or form-encoded body
    if request.is_json:
        payload = request.get_json()
        username = payload.get("username")
        password = payload.get("password")
    else:
        username = request.form.get("username")
        password = request.form.get("password")

    if not username or not password:
        return jsonify({"success": False, "message": "Missing username or password"}), 400

    # Authenticate against InfiniCLOUD
    if authenticate_user(username, password):
        session['logged_in'] = True

        # Get user_id using parameterized query (avoid f-strings)
        try:
            res = db.execute("SELECT user_id FROM entities WHERE name = %s LIMIT 1", (username,), fetch_output=True)
            if not res:
                return jsonify({"success": False, "message": "User not found after authentication"}), 500
            userId = res[0][0]
        except Exception as e:
            logger.exception("DB error fetching user_id")
            return jsonify({"success": False, "message": "Internal error"}), 500

        # store under consistent session key 'user_id'
        session['user_id'] = userId
        session['expires_at'] = create_expiry_timestamp(24)
        return jsonify({"success": True, "message": "Login successful"})
    else:
        return jsonify({"success": False, "message": "Invalid credentials"}), 401


@app.route("/dashboard")
def dashboard():
    if not session.get('logged_in') or is_expired(session.get('expires_at')):
        return redirect("/login")
    return render_template("dashboard.html")


@app.route("/get_url=<query>", methods=["GET"])
def get_url(query):
    matched = match_query(Queries, query)
    return jsonify(matched)


@app.route("/upload_file")
@limiter.limit("10 per minute")
def upload_file_page():
    if not session.get('logged_in') or is_expired(session.get('expires_at')):
        return redirect("/login")
    return render_template("upload.html")


allowed_files = ['png', 'ppt', 'pdf', 'jpg', 'jpeg', 'docx', 'doc', 'xlsx', 'xls', 'csv']

@app.route("/upload", methods=["POST"])
def upload():
    """
    Upload a file to InfiniCLOUD.
    Send using multipart/form-data:
      file=<uploaded file>
      path=<remote folder path>
    """
    if not session.get('logged_in') or is_expired(session.get('expires_at')):
        return redirect("/login")
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    elif file.filename.split('.')[-1].lower() not in allowed_files:
        return jsonify({"error": "File type not allowed"}), 400

    # Save to a unique temp file
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        local_path = tmp.name
        file.save(local_path)

    # Get remote folder (default "/")
    remote_folder = request.form.get("path", "/").rstrip("/")
    if remote_folder == "":
        remote_folder = "/"

    # normalize path: ensure starts with /
    if not remote_folder.startswith("/"):
        remote_folder = "/" + remote_folder

    # Prevent direct root uploads
    if remote_folder == "/":
        # cleanup temp file
        if os.path.exists(local_path):
            os.remove(local_path)
        return jsonify({"error": "Cannot upload directly to root. Specify a folder path."}), 400

    # Build remote path safely
    remote_path = posixpath.join(remote_folder, file.filename)

    try:
        result = cloud.upload(local_path, remote_path)
    except Exception as e:
        logger.exception("Cloud upload failed")
        result = {"success": False, "message": str(e)}

    # Cleanup local temp file
    if os.path.exists(local_path):
        os.remove(local_path)

    return jsonify({"result": result, "remote_path": remote_path})


@app.route("/fetch/userData")
def fetchUserData():
    """
    Returns user data for the logged-in user.
    Response: { user_id, name, role }
    """
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    try:
        # parameterized query, expect fetch_output=True to return list of tuples
        result = db.execute("SELECT user_id, name, role FROM entities WHERE user_id = %s LIMIT 1", (user_id,), fetch_output=True)
    except Exception as e:
        logger.exception("DB error fetching user data")
        return jsonify({"error": "Internal error"}), 500

    if not result:
        return jsonify({"error": "User not found"}), 404

    row = result[0]
    # return a clean JSON object (avoid returning DB-specific row objects)
    return jsonify({
        "user_id": row[0],
        "name": row[1],
        "role": row[2]
    })


if __name__ == "__main__":
    init_app()
    # In production use a WSGI server (gunicorn/uwsgi). For local dev:
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
