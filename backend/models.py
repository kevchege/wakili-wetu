from database.db import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(50))  # lawyer | citizen | policymaker

class LegalDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    source = db.Column(db.String(200))
    content = db.Column(db.Text)

class CaseAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    query = db.Column(db.Text)
    summary = db.Column(db.Text)
    citations = db.Column(db.Text)