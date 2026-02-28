from flask import Blueprint, request, jsonify
from services.ai_engine import summarize_document
from services.legal_fetcher import ingest_text
from werkzeug.utils import secure_filename
import os

ai_bp = Blueprint("ai", __name__)

# ensure upload directory exists relative to backend
UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


@ai_bp.route("/analyze", methods=["POST"])
def analyze():
    """Summarize raw text passed in JSON."""
    text = request.json.get("text")
    if not text:
        return jsonify({"error": "No text provided"}), 400
    summary = summarize_document(text)
    # summary is expected to be a dict {text, cites}
    if isinstance(summary, dict):
        return jsonify({"text": summary.get("text"), "cites": summary.get("cites", [])})
    else:
        return jsonify({"text": str(summary), "cites": []})


@ai_bp.route("/upload", methods=["POST"])
def upload_file():
    """Accept a file upload, read content and summarize it."""
    if "file" not in request.files:
        return jsonify({"error": "No file was uploaded"}), 400
    f = request.files["file"]
    if f.filename == "":
        return jsonify({"error": "Filename must not be empty"}), 400
    filename = secure_filename(f.filename)
    path = os.path.join(UPLOAD_FOLDER, filename)
    f.save(path)

    # attempt to read as text
    try:
        with open(path, "r", encoding="utf-8") as fh:
            content = fh.read()
    except Exception as e:
        return jsonify({"error": "Failed to read uploaded file", "details": str(e)}), 500

    # Persist the uploaded document to the DB
    try:
        doc = ingest_text(title=filename, source="upload", content=content)
        doc_id = doc.id
    except Exception:
        doc_id = None

    summary = summarize_document(content)
    if isinstance(summary, dict):
        resp = {"text": summary.get("text"), "cites": summary.get("cites", [])}
    else:
        resp = {"text": str(summary), "cites": []}

    resp.update({"filename": filename, "doc_id": doc_id})
    return jsonify(resp)