from flask_restx import Namespace, Resource, fields
from app.services import facade

api = Namespace("places", description="Place operations")

amenity_response = api.model("PlaceAmenity", {
    "id": fields.String(description="Amenity ID"),
    "name": fields.String(description="Amenity name"),
})

owner_response = api.model("PlaceOwner", {
    "id": fields.String(description="Owner ID"),
    "first_name": fields.String(description="Owner first name"),
    "last_name": fields.String(description="Owner last name"),
    "email": fields.String(description="Owner email"),
})

place_model = api.model("Place", {
    "title": fields.String(required=True, description="Place title"),
    "description": fields.String(description="Place description"),
    "price": fields.Float(required=True, description="Price per night"),
    "latitude": fields.Float(required=True, description="Latitude (-90 to 90)"),
    "longitude": fields.Float(required=True, description="Longitude (-180 to 180)"),
    "owner_id": fields.String(required=True, description="Owner user ID"),
    "amenities": fields.List(fields.String, description="List of amenity IDs"),
})

place_response = api.model("PlaceResponse", {
    "id": fields.String(description="Place ID"),
    "title": fields.String(description="Place title"),
    "description": fields.String(description="Place description"),
    "price": fields.Float(description="Price per night"),
    "latitude": fields.Float(description="Latitude"),
    "longitude": fields.Float(description="Longitude"),
    "owner_id": fields.String(description="Owner user ID"),
})

place_detail_response = api.model("PlaceDetailResponse", {
    "id": fields.String(description="Place ID"),
    "title": fields.String(description="Place title"),
    "description": fields.String(description="Place description"),
    "price": fields.Float(description="Price per night"),
    "latitude": fields.Float(description="Latitude"),
    "longitude": fields.Float(description="Longitude"),
    "owner_id": fields.String(description="Owner user ID"),
    "owner": fields.Nested(owner_response, description="Owner details"),
    "amenities": fields.List(fields.Nested(amenity_response), description="Amenities"),
})


@api.route("/")
class PlaceList(Resource):
    @api.marshal_list_with(place_response)
    def get(self):
        """Retrieve all places"""
        return [p.to_dict() for p in facade.get_all_places()]

    @api.expect(place_model, validate=True)
    @api.response(201, "Place created successfully")
    @api.response(400, "Validation error")
    @api.response(404, "Owner or amenity not found")
    def post(self):
        """Create a new place"""
        try:
            place = facade.create_place(api.payload)
        except ValueError as e:
            msg = str(e)
            if "not found" in msg.lower():
                return {"error": msg}, 404
            return {"error": msg}, 400
        return place.to_dict(), 201


@api.route("/<string:place_id>")
class PlaceResource(Resource):
    @api.response(200, "Place found")
    @api.response(404, "Place not found")
    def get(self, place_id):
        """Get a place by ID (includes owner and amenities)"""
        place = facade.get_place(place_id)
        if not place:
            return {"error": "Place not found"}, 404
        return place.to_dict_detailed(), 200

    @api.expect(place_model)
    @api.response(200, "Place updated successfully")
    @api.response(400, "Validation error")
    @api.response(404, "Place not found")
    def put(self, place_id):
        """Update a place"""
        try:
            place = facade.update_place(place_id, api.payload)
        except ValueError as e:
            msg = str(e)
            if "not found" in msg.lower():
                return {"error": msg}, 404
            return {"error": msg}, 400
        if not place:
            return {"error": "Place not found"}, 404
        return place.to_dict_detailed(), 200


@api.route("/<string:place_id>/reviews")
class PlaceReviewList(Resource):
    @api.response(200, "Reviews for place")
    @api.response(404, "Place not found")
    def get(self, place_id):
        """Get all reviews for a specific place"""
        reviews = facade.get_reviews_by_place(place_id)
        if reviews is None:
            return {"error": "Place not found"}, 404
        return [r.to_dict() for r in reviews], 200
