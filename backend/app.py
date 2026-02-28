from flask import Flask, send_from_directory
from database.db import db
from routes.auth import auth_bp
from routes.cases import case_bp
from routes.documents import doc_bp
from routes.ai import ai_bp
from flask_cors import CORS

app = Flask(__name__)
app.config.from_object("config.Config")

CORS(app)
db.init_app(app)

# Ensure models are imported so SQLAlchemy registers them
import models  # noqa: F401

for bp, prefix in [
    (auth_bp, "/api/auth"),
    (case_bp, "/api/cases"),
    (doc_bp, "/api/docs"),
    (ai_bp, "/api/ai"),
]:
    if bp.name not in app.blueprints:
        app.register_blueprint(bp, url_prefix=prefix)

@app.route("/")
def index():
    return send_from_directory("static", "wakili_wetu.html")

if __name__ == "__main__":
    # Create database tables 
    with app.app_context():
        db.create_all()

    app.run(debug=True)