from app.models.user import User
from app.models.amenity import Amenity
from app.models.place import Place
from app.models.review import Review
from app.persistence.repository import InMemoryRepository


class HBnBFacade:
    def __init__(self):
        self.user_repo = InMemoryRepository()
        self.amenity_repo = InMemoryRepository()
        self.place_repo = InMemoryRepository()
        self.review_repo = InMemoryRepository()

    # ------------------------------------------------------------------ Users

    def create_user(self, data: dict) -> User:
        if self.user_repo.get_by_attribute("email", data.get("email")):
            raise ValueError("Email already registered")
        user = User(
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data["email"],
            password=data.get("password", ""),
            is_admin=data.get("is_admin", False),
        )
        self.user_repo.add(user)
        return user

    def get_user(self, user_id: str):
        return self.user_repo.get(user_id)

    def get_all_users(self):
        return self.user_repo.get_all()

    def update_user(self, user_id: str, data: dict):
        user = self.user_repo.get(user_id)
        if not user:
            return None
        # if email changes, ensure uniqueness
        new_email = data.get("email")
        if new_email and new_email != user.email:
            if self.user_repo.get_by_attribute("email", new_email):
                raise ValueError("Email already registered")
        user.update(data)
        return user

    # --------------------------------------------------------------- Amenities

    def create_amenity(self, data: dict) -> Amenity:
        amenity = Amenity(name=data["name"])
        self.amenity_repo.add(amenity)
        return amenity

    def get_amenity(self, amenity_id: str):
        return self.amenity_repo.get(amenity_id)

    def get_all_amenities(self):
        return self.amenity_repo.get_all()

    def update_amenity(self, amenity_id: str, data: dict):
        amenity = self.amenity_repo.get(amenity_id)
        if not amenity:
            return None
        amenity.update(data)
        return amenity

    # ----------------------------------------------------------------- Places

    def create_place(self, data: dict) -> Place:
        owner = self.user_repo.get(data.get("owner_id"))
        if not owner:
            raise ValueError("Owner not found")

        amenity_objects = []
        for aid in data.get("amenities", []):
            amenity = self.amenity_repo.get(aid)
            if not amenity:
                raise ValueError(f"Amenity {aid} not found")
            amenity_objects.append(amenity)

        place = Place(
            title=data["title"],
            description=data.get("description", ""),
            price=data["price"],
            latitude=data["latitude"],
            longitude=data["longitude"],
            owner_id=data["owner_id"],
        )
        place.owner = owner
        place.amenities = amenity_objects
        owner.places.append(place)
        self.place_repo.add(place)
        return place

    def get_place(self, place_id: str):
        return self.place_repo.get(place_id)

    def get_all_places(self):
        return self.place_repo.get_all()

    def update_place(self, place_id: str, data: dict) -> Place:
        place = self.place_repo.get(place_id)
        if not place:
            return None

        if "amenities" in data:
            amenity_objects = []
            for aid in data.pop("amenities"):
                amenity = self.amenity_repo.get(aid)
                if not amenity:
                    raise ValueError(f"Amenity {aid} not found")
                amenity_objects.append(amenity)
            place.amenities = amenity_objects

        place.update(data)
        return place

    # --------------------------------------------------------------- Reviews

    def create_review(self, data: dict) -> Review:
        if not self.user_repo.get(data.get("user_id")):
            raise ValueError("User not found")
        place = self.place_repo.get(data.get("place_id"))
        if not place:
            raise ValueError("Place not found")

        review = Review(
            text=data["text"],
            rating=data["rating"],
            place_id=data["place_id"],
            user_id=data["user_id"],
        )
        place.reviews.append(review)
        self.review_repo.add(review)
        return review

    def get_review(self, review_id: str):
        return self.review_repo.get(review_id)

    def get_all_reviews(self):
        return self.review_repo.get_all()

    def get_reviews_by_place(self, place_id: str):
        place = self.place_repo.get(place_id)
        if not place:
            return None
        return place.reviews

    def update_review(self, review_id: str, data: dict):
        review = self.review_repo.get(review_id)
        if not review:
            return None
        review.update(data)
        return review

    def delete_review(self, review_id: str) -> bool:
        review = self.review_repo.get(review_id)
        if not review:
            return False
        # remove from the parent place's list
        place = self.place_repo.get(review.place_id)
        if place:
            place.reviews = [r for r in place.reviews if r.id != review_id]
        self.review_repo.delete(review_id)
        return True
