from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from sqlalchemy.exc import IntegrityError
from app.services import facade

api = Namespace("reviews", description="Review operations")

review_model = api.model("Review", {
    "text": fields.String(required=True, description="Review text"),
    "rating": fields.Integer(required=True, description="Rating (1-5)"),
    "place_id": fields.String(required=True, description="Reviewed place ID"),
})

review_update_model = api.model("ReviewUpdate", {
    "text": fields.String(description="Review text"),
    "rating": fields.Integer(description="Rating (1-5)"),
})

review_response = api.model("ReviewResponse", {
    "id": fields.String(description="Review ID"),
    "text": fields.String(description="Review text"),
    "rating": fields.Integer(description="Rating"),
    "user_id": fields.String(description="User ID"),
    "place_id": fields.String(description="Place ID"),
})


@api.route("/")
class ReviewList(Resource):
    @api.marshal_list_with(review_response)
    def get(self):
        """Retrieve all reviews (public)"""
        return [r.to_dict() for r in facade.get_all_reviews()]

    @api.doc(security="Bearer")
    @jwt_required()
    @api.expect(review_model, validate=True)
    @api.response(201, "Review created successfully")
    @api.response(400, "Validation error")
    @api.response(403, "Cannot review your own place")
    @api.response(404, "User or Place not found")
    @api.response(409, "Review already exists")
    def post(self):
        """Create a new review (authenticated)"""
        data = api.payload.copy()
        current_user_id = get_jwt_identity()
        data["user_id"] = current_user_id
        try:
            review = facade.create_review(data)
        except ValueError as e:
            msg = str(e)
            if "not found" in msg.lower():
                return {"error": msg}, 404
            if "own place" in msg.lower():
                return {"error": msg}, 403
            return {"error": msg}, 400
        except IntegrityError:
            return {"error": "You have already reviewed this place"}, 409
        return review.to_dict(), 201


@api.route("/<string:review_id>")
class ReviewResource(Resource):
    @api.marshal_with(review_response)
    @api.response(404, "Review not found")
    def get(self, review_id):
        """Get a review by ID (public)"""
        review = facade.get_review(review_id)
        if not review:
            return {"error": "Review not found"}, 404
        return review.to_dict()

    @api.doc(security="Bearer")
    @jwt_required()
    @api.expect(review_update_model, validate=True)
    @api.response(200, "Review updated successfully")
    @api.response(400, "Validation error")
    @api.response(403, "Unauthorized")
    @api.response(404, "Review not found")
    def put(self, review_id):
        """Update a review (admin or author only)"""
        review = facade.get_review(review_id)
        if not review:
            return {"error": "Review not found"}, 404
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        if not claims.get("is_admin") and review.user_id != current_user_id:
            return {"error": "Unauthorized"}, 403
        try:
            review = facade.update_review(review_id, api.payload)
        except ValueError as e:
            return {"error": str(e)}, 400
        return review.to_dict(), 200

    @api.doc(security="Bearer")
    @jwt_required()
    @api.response(200, "Review deleted successfully")
    @api.response(403, "Unauthorized")
    @api.response(404, "Review not found")
    def delete(self, review_id):
        """Delete a review (admin or author only)"""
        review = facade.get_review(review_id)
        if not review:
            return {"error": "Review not found"}, 404
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        if not claims.get("is_admin") and review.user_id != current_user_id:
            return {"error": "Unauthorized"}, 403
        if not facade.delete_review(review_id):
            return {"error": "Review not found"}, 404
        return {"message": "Review deleted successfully"}, 200