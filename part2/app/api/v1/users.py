from flask_restx import Namespace, Resource, fields
from app.services import facade

api = Namespace("users", description="User operations")

user_model = api.model("User", {
    "first_name": fields.String(required=True, description="First name"),
    "last_name": fields.String(required=True, description="Last name"),
    "email": fields.String(required=True, description="Email address"),
    "password": fields.String(required=False, description="Password"),
})

user_response = api.model("UserResponse", {
    "id": fields.String(description="User ID"),
    "first_name": fields.String(description="First name"),
    "last_name": fields.String(description="Last name"),
    "email": fields.String(description="Email address"),
    "is_admin": fields.Boolean(description="Admin flag"),
})


@api.route("/")
class UserList(Resource):
    @api.marshal_list_with(user_response)
    def get(self):
        """Retrieve all users"""
        return [u.to_dict() for u in facade.get_all_users()]

    @api.expect(user_model, validate=True)
    @api.response(201, "User created successfully")
    @api.response(400, "Validation error")
    @api.response(409, "Email already registered")
    def post(self):
        """Register a new user"""
        data = api.payload
        try:
            user = facade.create_user(data)
        except ValueError as e:
            msg = str(e)
            if "already" in msg:
                return {"error": msg}, 409
            return {"error": msg}, 400
        return user.to_dict(), 201


@api.route("/<string:user_id>")
class UserResource(Resource):
    @api.marshal_with(user_response)
    @api.response(404, "User not found")
    def get(self, user_id):
        """Get a user by ID"""
        user = facade.get_user(user_id)
        if not user:
            return {"error": "User not found"}, 404
        return user.to_dict()

    @api.expect(user_model)
    @api.response(200, "User updated successfully")
    @api.response(400, "Validation error")
    @api.response(404, "User not found")
    @api.response(409, "Email already registered")
    def put(self, user_id):
        """Update a user"""
        data = api.payload
        try:
            user = facade.update_user(user_id, data)
        except ValueError as e:
            msg = str(e)
            if "already" in msg:
                return {"error": msg}, 409
            return {"error": msg}, 400
        if not user:
            return {"error": "User not found"}, 404
        return user.to_dict(), 200
