from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.extensions import db
from app.services import facade
from app.models.user import User

api = Namespace("users", description="User operations")

user_model = api.model("User", {
    "first_name": fields.String(required=True, description="First name"),
    "last_name": fields.String(required=True, description="Last name"),
    "email": fields.String(required=True, description="Email address"),
    "password": fields.String(required=False, description="Password"),
})

user_update_model = api.model("UserUpdate", {
    "first_name": fields.String(description="First name"),
    "last_name": fields.String(description="Last name"),
    "email": fields.String(description="Email address"),
    "password": fields.String(description="New password"),
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
    @api.doc(security="Bearer")
    @jwt_required()
    @api.marshal_list_with(user_response)
    def get(self):
        """Retrieve all users (admin only)"""
        claims = get_jwt()
        if not claims.get("is_admin"):
            return {"error": "Admin access required"}, 403
        return [u.to_dict(include_email=True) for u in facade.get_all_users()]

    @api.expect(user_model, validate=True)
    @api.response(201, "User created successfully")
    @api.response(400, "Validation error")
    @api.response(409, "Email already registered")
    def post(self):
        """Register a new user (public)"""
        data = api.payload
        try:
            user = facade.create_user(data)
        except ValueError as e:
            msg = str(e)
            if "already" in msg:
                return {"error": msg}, 409
            return {"error": msg}, 400
        except Exception:
            from sqlalchemy.exc import IntegrityError
            raise
        return user.to_dict(include_email=True), 201


@api.route("/<string:user_id>")
class UserResource(Resource):
    @api.doc(security="Bearer")
    @jwt_required()
    @api.marshal_with(user_response)
    @api.response(404, "User not found")
    def get(self, user_id):
        """Get a user by ID (authenticated)"""
        claims = get_jwt()
        user = facade.get_user(user_id)
        if not user:
            return {"error": "User not found"}, 404
        return user.to_dict(include_email=claims.get("is_admin", False))

    @api.doc(security="Bearer")
    @jwt_required()
    @api.expect(user_update_model)
    @api.response(200, "User updated successfully")
    @api.response(400, "Validation error")
    @api.response(403, "Unauthorized")
    @api.response(404, "User not found")
    @api.response(409, "Email already registered")
    def put(self, user_id):
        """Update a user (admin or self)"""
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        if not claims.get("is_admin") and current_user_id != user_id:
            return {"error": "Unauthorized"}, 403
        data = api.payload.copy()
        if not claims.get("is_admin"):
            data.pop("is_admin", None)
            data.pop("email", None)
        else:
            new_email = data.get("email")
            if new_email:
                existing = facade.get_user_by_email(new_email)
                if existing and existing.id != user_id:
                    return {"error": "Email already registered"}, 409
        try:
            user = facade.update_user(user_id, data)
        except ValueError as e:
            msg = str(e)
            if "already" in msg:
                return {"error": msg}, 409
            return {"error": msg}, 400
        except Exception:
            from sqlalchemy.exc import IntegrityError
            raise
        if not user:
            return {"error": "User not found"}, 404
        return user.to_dict(include_email=True), 200