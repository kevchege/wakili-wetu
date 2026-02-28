from models import LegalDocument
from database.db import db


def ingest_text(title, source, content):
    """Store a legal document into the database."""
    doc = LegalDocument(title=title, source=source, content=content)
    db.session.add(doc)
    db.session.commit()
    return doc


def get_relevant_material(query):
    docs = LegalDocument.query.filter(
        LegalDocument.content.ilike(f"%{query}%")
    ).all()

    if not docs:
        return None

    combined = "\n\n".join([d.content for d in docs])
    return combined