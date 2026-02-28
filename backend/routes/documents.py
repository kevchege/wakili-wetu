from flask import Blueprint, request, jsonify
from models import LegalDocument
from database.db import db

doc_bp = Blueprint("documents", __name__)

# Add a legal document manually (admin ingestion)
@doc_bp.route("/add", methods=["POST"])
def add_document():
    data = request.json

    doc = LegalDocument(
        title=data.get("title"),
        source=data.get("source"),
        content=data.get("content")
    )

    db.session.add(doc)
    db.session.commit()

    return jsonify({"message": "Document added", "id": doc.id})


# Retrieve all documents
@doc_bp.route("/", methods=["GET"])
def get_documents():
    docs = LegalDocument.query.all()

    return jsonify([
        {
            "id": d.id,
            "title": d.title,
            "source": d.source
        } for d in docs
    ])


# Basic keyword search (we upgrade to semantic search later)
@doc_bp.route("/search", methods=["POST"])
def search_documents():
    keyword = request.json.get("keyword")

    results = LegalDocument.query.filter(
        LegalDocument.content.contains(keyword)
    ).all()

    return jsonify([
        {
            "id": r.id,
            "title": r.title,
            "source": r.source
        } for r in results
    ])