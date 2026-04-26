from flask_restx import Namespace, Resource, fields
from app.services import facade

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
        """Retrieve all amenities"""
        return [a.to_dict() for a in facade.get_all_amenities()]

    @api.expect(amenity_model, validate=True)
    @api.response(201, "Amenity created successfully")
    @api.response(400, "Validation error")
    def post(self):
        """Create a new amenity"""
        try:
            amenity = facade.create_amenity(api.payload)
        except ValueError as e:
            return {"error": str(e)}, 400
        return amenity.to_dict(), 201


@api.route("/<string:amenity_id>")
class AmenityResource(Resource):
    @api.marshal_with(amenity_response)
    @api.response(404, "Amenity not found")
    def get(self, amenity_id):
        """Get an amenity by ID"""
        amenity = facade.get_amenity(amenity_id)
        if not amenity:
            return {"error": "Amenity not found"}, 404
        return amenity.to_dict()

    @api.expect(amenity_model, validate=True)
    @api.response(200, "Amenity updated successfully")
    @api.response(400, "Validation error")
    @api.response(404, "Amenity not found")
    def put(self, amenity_id):
        """Update an amenity"""
        try:
            amenity = facade.update_amenity(amenity_id, api.payload)
        except ValueError as e:
            return {"error": str(e)}, 400
        if not amenity:
            return {"error": "Amenity not found"}, 404
        return amenity.to_dict(), 200
