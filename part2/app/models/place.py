from app.models.base_model import BaseModel


class Place(BaseModel):
    def __init__(self, title, description, price, latitude, longitude, owner_id):
        super().__init__()

        if not title or len(title) > 100:
            raise ValueError("title is required and must be at most 100 characters")
        if price is None or float(price) < 0:
            raise ValueError("price must be a non-negative number")
        if latitude is None or not (-90.0 <= float(latitude) <= 90.0):
            raise ValueError("latitude must be between -90 and 90")
        if longitude is None or not (-180.0 <= float(longitude) <= 180.0):
            raise ValueError("longitude must be between -180 and 180")
        if not owner_id:
            raise ValueError("owner_id is required")

        self.title = title
        self.description = description or ""
        self.price = float(price)
        self.latitude = float(latitude)
        self.longitude = float(longitude)
        self.owner_id = owner_id
        self.owner = None        # populated by facade
        self.amenities = []      # list of Amenity objects
        self.reviews = []        # list of Review objects

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
                "email": self.owner.email,
            }
        result["amenities"] = [a.to_dict() for a in self.amenities]
        return result
