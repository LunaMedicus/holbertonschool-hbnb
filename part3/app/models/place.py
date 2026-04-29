from sqlalchemy.orm import validates
from app.models.base_model import BaseModel
from app.extensions import db


place_amenity = db.Table(
    "place_amenity",
    db.Column("place_id", db.String(36), db.ForeignKey("places.id", ondelete="CASCADE"),
              primary_key=True),
    db.Column("amenity_id", db.String(36), db.ForeignKey("amenities.id", ondelete="CASCADE"),
              primary_key=True),
)


class Place(BaseModel):
    __tablename__ = "places"

    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, default="")
    price = db.Column(db.Float, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    owner_id = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    amenities = db.relationship(
        "Amenity", secondary=place_amenity, lazy="subquery",
        backref=db.backref("places", lazy=True),
    )
    reviews = db.relationship(
        "Review", backref="place", lazy=True, cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @validates("title")
    def validate_title(self, key, value):
        if not value or len(value) > 100:
            raise ValueError("title is required and must be at most 100 characters")
        return value

    @validates("price")
    def validate_price(self, key, value):
        if value is None or float(value) < 0:
            raise ValueError("price must be a non-negative number")
        return float(value)

    @validates("latitude")
    def validate_latitude(self, key, value):
        if value is None or not (-90.0 <= float(value) <= 90.0):
            raise ValueError("latitude must be between -90 and 90")
        return float(value)

    @validates("longitude")
    def validate_longitude(self, key, value):
        if value is None or not (-180.0 <= float(value) <= 180.0):
            raise ValueError("longitude must be between -180 and 180")
        return float(value)

    def __init__(self, title, description, price, latitude, longitude, owner_id):
        super().__init__()
        self.title = title
        self.description = description or ""
        self.price = price
        self.latitude = latitude
        self.longitude = longitude
        self.owner_id = owner_id

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "price": self.price,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "owner_id": self.owner_id,
        }

    def to_dict_detailed(self):
        result = self.to_dict()
        if self.owner:
            result["owner"] = {
                "id": self.owner.id,
                "first_name": self.owner.first_name,
                "last_name": self.owner.last_name,
            }
        result["amenities"] = [a.to_dict() for a in self.amenities]
        return result