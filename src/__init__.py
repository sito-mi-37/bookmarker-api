from flask import Flask, redirect,jsonify
import os
from .auth import auth
from .bookmark import bookmarks
from src.model import db, Bookmark
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager
from flasgger import Swagger, swag_from
from src.config.swagger import template, swagger_config

load_dotenv()

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    if test_config is None:
        app.config.from_mapping(
            SECRET_KEY = os.getenv("SECRET_KEY"),
            SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL"),
            JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY"),

            SWAGGER = {
                "title": "Bookmark Api",
                "uiversion": 3
            }
        )

    else: 
        app.config.from_mapping(test_config)

    @app.get("/<short_url>")
    @swag_from("./docs/short_url.yml")
    def redirect_to_url(short_url):
        bookmark = Bookmark.query.filter_by(short_url= short_url).first_or_404()

        if bookmark:
            bookmark.visited = bookmark.visited + 1
            db.session.commit()
        return redirect(bookmark.url)
    
    @app.errorhandler(404)
    def handle_404(e):
        return jsonify({"error": "404 NOT FOUND"}),404
    
    @app.errorhandler(500)
    def handle_500(e):
        return jsonify({"error": "Internal server error, we are currently working on it"}),500

    db.app = app
    db.init_app(app)
    JWTManager(app)
    with app.app_context():
        db.create_all()
    app.register_blueprint(auth)
    app.register_blueprint(bookmarks)

    Swagger(app, config=swagger_config, template=template)

    return app