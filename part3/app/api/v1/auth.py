from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import create_access_token
from app.services import facade

api = Namespace("auth", description="Authentication operations")

login_model = api.model("Login", {
    "email": fields.String(required=True, description="User email"),
    "password": fields.String(required=True, description="User password"),
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
        return {"access_token": access_token}, 200
