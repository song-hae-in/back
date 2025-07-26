from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config

db = SQLAlchemy()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)
    CORS(app)

    from app.routes import auth, interview, info
    app.register_blueprint(auth.bp)
    app.register_blueprint(interview.bp)
    app.register_blueprint(info.bp)

    with app.app_context():
        db.create_all()

    return app
