from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.services import facade
from app.api.v1 import admin_required

api = Namespace("amenities", description="Amenity operations")

amenity_model = api.model("Amenity", {
    "name": fields.String(required=True, description="Amenity name"),
})

amenity_response = api.model("AmenityResponse", {
    "id": fields.String(description="Amenity ID"),
    "name": fields.String(description="Amenity name"),
})


@api.route("/")
class AmenityList(Resource):
    @api.marshal_list_with(amenity_response)
    def get(self):
        """Retrieve all amenities (public)"""
        return [a.to_dict() for a in facade.get_all_amenities()]

    @api.doc(security="Bearer")
    @jwt_required()
    @admin_required
    @api.expect(amenity_model, validate=True)
    @api.response(201, "Amenity created successfully")
    @api.response(400, "Validation error")
    @api.response(403, "Admin access required")
    @api.response(409, "Amenity name already exists")
    def post(self):
        """Create a new amenity (admin only)"""
        try:
            amenity = facade.create_amenity(api.payload)
        except ValueError as e:
            msg = str(e)
            if "already" in msg.lower():
                return {"error": msg}, 409
            return {"error": msg}, 400
        return amenity.to_dict(), 201


@api.route("/<string:amenity_id>")
class AmenityResource(Resource):
    @api.marshal_with(amenity_response)
    @api.response(404, "Amenity not found")
    def get(self, amenity_id):
        """Get an amenity by ID (public)"""
        amenity = facade.get_amenity(amenity_id)
        if not amenity:
            return {"error": "Amenity not found"}, 404
        return amenity.to_dict()

    @api.doc(security="Bearer")
    @jwt_required()
    @admin_required
    @api.expect(amenity_model, validate=True)
    @api.response(200, "Amenity updated successfully")
    @api.response(400, "Validation error")
    @api.response(403, "Admin access required")
    @api.response(404, "Amenity not found")
    def put(self, amenity_id):
        """Update an amenity (admin only)"""
        try:
            amenity = facade.update_amenity(amenity_id, api.payload)
        except ValueError as e:
            return {"error": str(e)}, 400
        if not amenity:
            return {"error": "Amenity not found"}, 404
        return amenity.to_dict(), 200
