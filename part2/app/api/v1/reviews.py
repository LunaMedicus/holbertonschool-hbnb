from flask_restx import Namespace, Resource, fields
from app.services import facade

api = Namespace("reviews", description="Review operations")

review_model = api.model("Review", {
    "text": fields.String(required=True, description="Review text"),
    "rating": fields.Integer(required=True, description="Rating (1-5)"),
    "user_id": fields.String(required=True, description="Reviewer user ID"),
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
        """Retrieve all reviews"""
        return [r.to_dict() for r in facade.get_all_reviews()]

    @api.expect(review_model, validate=True)
    @api.response(201, "Review created successfully")
    @api.response(400, "Validation error")
    @api.response(404, "User or Place not found")
    def post(self):
        """Create a new review"""
        try:
            review = facade.create_review(api.payload)
        except ValueError as e:
            msg = str(e)
            if "not found" in msg.lower():
                return {"error": msg}, 404
            return {"error": msg}, 400
        return review.to_dict(), 201


@api.route("/<string:review_id>")
class ReviewResource(Resource):
    @api.marshal_with(review_response)
    @api.response(404, "Review not found")
    def get(self, review_id):
        """Get a review by ID"""
        review = facade.get_review(review_id)
        if not review:
            return {"error": "Review not found"}, 404
        return review.to_dict()

    @api.expect(review_update_model, validate=True)
    @api.response(200, "Review updated successfully")
    @api.response(400, "Validation error")
    @api.response(404, "Review not found")
    def put(self, review_id):
        """Update a review"""
        try:
            review = facade.update_review(review_id, api.payload)
        except ValueError as e:
            return {"error": str(e)}, 400
        if not review:
            return {"error": "Review not found"}, 404
        return review.to_dict(), 200

    @api.response(200, "Review deleted successfully")
    @api.response(404, "Review not found")
    def delete(self, review_id):
        """Delete a review"""
        if not facade.delete_review(review_id):
            return {"error": "Review not found"}, 404
        return {"message": "Review deleted successfully"}, 200
