from flask import make_response
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from app.services import facade

api = Namespace("auth", description="Authentication operations")

login_model = api.model("Login", {
    "email": fields.String(required=True, description="User email"),
    "password": fields.String(required=True, description="User password"),
})

user_auth_response = api.model("UserAuthResponse", {
    "id": fields.String(description="User ID"),
    "first_name": fields.String(description="First name"),
    "last_name": fields.String(description="Last name"),
    "email": fields.String(description="Email address"),
    "is_admin": fields.Boolean(description="Admin flag"),
})


@api.route("/login")
class Login(Resource):
    @api.expect(login_model, validate=True)
    @api.response(200, "Login successful")
    @api.response(401, "Invalid credentials")
    def post(self):
        """Authenticate and get a JWT access token"""
        data = api.payload
        user = facade.get_user_by_email(data["email"])
        if not user or not user.verify_password(data["password"]):
            return {"error": "Invalid email or password"}, 401
        access_token = create_access_token(
            identity=user.id,
            additional_claims={"is_admin": user.is_admin},
        )
        response = make_response({
            "access_token": access_token,
            "user": user.to_dict(include_email=True),
        }, 200)
        response.set_cookie(
            "token", access_token,
            httponly=True, samesite="Lax",
            max_age=900, path="/",
        )
        return response


@api.route("/me")
@api.doc(security="Bearer")
class AuthMe(Resource):
    @jwt_required()
    @api.marshal_with(user_auth_response)
    def get(self):
        """Get current authenticated user info"""
        user = facade.get_user(get_jwt_identity())
        if not user:
            return {"error": "User not found"}, 404
        return user.to_dict(include_email=True)