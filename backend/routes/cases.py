from flask import Blueprint, request, jsonify
from services.legal_fetcher import get_relevant_material
from services.ai_engine import analyze_with_gemini
from models import CaseAnalysis
from database.db import db

case_bp = Blueprint("cases", __name__)


@case_bp.route("/analyze", methods=["POST"])
def analyze_case():
    """Perform AI analysis and persist a CaseAnalysis record."""
    query = request.json.get("query")
    if not query:
        return jsonify({"error": "No query provided"}), 400

    material = get_relevant_material(query)
    if not material:
        return jsonify({"error": "No matching legal material found"}), 404

    result = analyze_with_gemini(material, query)

    case = CaseAnalysis(query=query, summary=result, citations="")
    db.session.add(case)
    db.session.commit()

    return jsonify({
        "query": query,
        "analysis": result,
        "case_id": case.id
    })


@case_bp.route("/", methods=["POST"])
def create_case():
    """Create a case record manually (without AI)."""
    data = request.json
    if not data or "query" not in data:
        return jsonify({"error": "Query text is required"}), 400

    case = CaseAnalysis(
        query=data.get("query"),
        summary=data.get("summary", ""),
        citations=data.get("citations", "")
    )
    db.session.add(case)
    db.session.commit()

    return jsonify({"message": "Case created", "id": case.id})


@case_bp.route("/", methods=["GET"])
def list_cases():
    # "query" is also a column name, so avoid the automatic query attribute
    cases = db.session.query(CaseAnalysis).all()
    return jsonify([
        {"id": c.id, "query": c.query, "summary": c.summary} for c in cases
    ])