from flask import Flask
from flask_restx import Api
from sqlalchemy.exc import IntegrityError
from app.extensions import db, jwt, bcrypt
from config import config


def create_app(config_class="default"):
    app = Flask(__name__)
    cfg = config[config_class] if isinstance(config_class, str) else config_class
    app.config.from_object(cfg)

    if config_class == "production":
        cfg.validate()

    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)

    api = Api(
        app,
        version="1.0",
        title="HBnB API",
        description="HBnB Application API",
        doc="/api/v1/",
        authorizations={
            "Bearer": {
                "type": "apiKey",
                "in": "header",
                "name": "Authorization",
                "description": "JWT token: Bearer <token>",
            }
        },
        security="Bearer",
    )

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(e):
        return {"error": "A record with these values already exists"}, 409

    from app.services import init_facade
    init_facade()

    from app.api.v1.users import api as users_ns
    from app.api.v1.amenities import api as amenities_ns
    from app.api.v1.places import api as places_ns
    from app.api.v1.reviews import api as reviews_ns
    from app.api.v1.auth import api as auth_ns

    api.add_namespace(users_ns, path="/api/v1/users")
    api.add_namespace(amenities_ns, path="/api/v1/amenities")
    api.add_namespace(places_ns, path="/api/v1/places")
    api.add_namespace(reviews_ns, path="/api/v1/reviews")
    api.add_namespace(auth_ns, path="/api/v1/auth")

    with app.app_context():
        db.create_all()

    return app