from sqlalchemy.orm import validates
from app.models.base_model import BaseModel
from app.extensions import db


class Amenity(BaseModel):
    __tablename__ = "amenities"

    name = db.Column(db.String(50), nullable=False, unique=True)

    @validates("name")
    def validate_name(self, key, value):
        if not value or len(value) > 50:
            raise ValueError("name is required and must be at most 50 characters")
        return value

    def __init__(self, name):
        super().__init__()
        self.name = name

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
        }