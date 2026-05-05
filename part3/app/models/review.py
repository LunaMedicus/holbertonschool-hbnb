from sqlalchemy.orm import validates
from app.models.base_model import BaseModel
from app.extensions import db


class Review(BaseModel):
    __tablename__ = "reviews"

    text = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    place_id = db.Column(db.String(36), db.ForeignKey("places.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (
        db.UniqueConstraint("place_id", "user_id", name="uq_review_place_user"),
    )

    @validates("text")
    def validate_text(self, key, value):
        if not value:
            raise ValueError("text is required")
        return value

    @validates("rating")
    def validate_rating(self, key, value):
        if value is None or not (1 <= int(value) <= 5):
            raise ValueError("rating must be an integer between 1 and 5")
        return int(value)

    def __init__(self, text, rating, place_id, user_id):
        super().__init__()
        self.text = text
        self.rating = rating
        self.place_id = place_id
        self.user_id = user_id

    def to_dict(self):
        result = {
            "id": self.id,
            "text": self.text,
            "rating": self.rating,
            "place_id": self.place_id,
            "user_id": self.user_id,
        }
        if self.user:
            result["reviewer_name"] = f"{self.user.first_name} {self.user.last_name}"
        return result