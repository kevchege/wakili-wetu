import os

# keep track of the directory containing this config file
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = "wakili-wetu-secret"
    # form an absolute path so the database file is always created under backend/
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "wakili.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False