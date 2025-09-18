# Author - SirSevrus (https://github.com/sevruscorporations)

from flask import Flask, render_template, request, jsonify
from colorama import Fore, init
import os
import json
import tempfile
import posixpath

from libs.getQueries import get_queries
from libs.matchFiles import match_query
from libs.cloud import InfiniCloudClient   # your InfiniCLOUD library

app = Flask(__name__)
init(autoreset=True)
VERSION = "1.0.0-alpha"

QUERIES = None
Queries = None
cloud = InfiniCloudClient()   # initialize InfiniCLOUD client once


def init_app():
    """Initialize API and load queries."""
    print("[INFO] API Booting Up...")
    print(Fore.RED + "[ERR] " + Fore.YELLOW + "An Error occurred : Maybe you haven't slept today?")
    print(Fore.RED + "[ERR] " + Fore.YELLOW + "API Will Blast your PC in 5 Seconds... Just Kidding :)")
    print(Fore.GREEN + "[SUCCESS]" + Fore.YELLOW + " API Booted Up Successfully!")

    global Queries, QUERIES
    QUERIES = load_queries()
    Queries = get_queries(QUERIES)


def load_queries():
    """Load queries JSON file from /data/queries.json"""
    with open("data/queries.json", "r") as file:
        queries_json = json.load(file)
    return queries_json


@app.route("/version", methods=["GET"])
def version():
    return jsonify({"version": VERSION})


@app.route("/get_url=<query>", methods=["GET"])
def get_url(query):
    matched = match_query(Queries, query)
    return jsonify(matched)


@app.route("/upload_file")
def upload_file_page():
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

    # Prevent direct root uploads
    if remote_folder == "/":
        return jsonify({"error": "Cannot upload directly to root. Specify a folder path."}), 400

    # Build remote path safely
    remote_path = posixpath.join(remote_folder, file.filename)

    try:
        result = cloud.upload(local_path, remote_path)
    except Exception as e:
        result = {"success": False, "message": str(e)}

    # Cleanup local temp file
    if os.path.exists(local_path):
        os.remove(local_path)

    return jsonify({"result": result, "remote_path": remote_path})


if __name__ == "__main__":
    init_app()
    app.run(debug=True)
