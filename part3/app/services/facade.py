from sqlalchemy.exc import IntegrityError
from app.models.user import User
from app.models.amenity import Amenity
from app.models.place import Place
from app.models.review import Review
from app.persistence.repository import SQLAlchemyRepository
from app.extensions import db


class HBnBFacade:
    def __init__(self):
        self.user_repo = SQLAlchemyRepository(User)
        self.amenity_repo = SQLAlchemyRepository(Amenity)
        self.place_repo = SQLAlchemyRepository(Place)
        self.review_repo = SQLAlchemyRepository(Review)

    # ------------------------------------------------------------------ Auth

    def get_user_by_email(self, email: str):
        return self.user_repo.get_by_attribute("email", email)

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
        try:
            self.user_repo.add(user)
        except IntegrityError:
            db.session.rollback()
            raise ValueError("Email already registered")
        return user

    def get_user(self, user_id: str):
        return self.user_repo.get(user_id)

    def get_all_users(self):
        return self.user_repo.get_all()

    def update_user(self, user_id: str, data: dict):
        user = self.user_repo.get(user_id)
        if not user:
            return None
        new_email = data.get("email")
        if new_email and new_email != user.email:
            existing = self.user_repo.get_by_attribute("email", new_email)
            if existing and existing.id != user_id:
                raise ValueError("Email already registered")
        plain_password = data.pop("password", None)
        user.update(data)
        if plain_password:
            user.hash_password(plain_password)
            db.session.commit()
        return user

    # --------------------------------------------------------------- Amenities

    def create_amenity(self, data: dict) -> Amenity:
        amenity = Amenity(name=data["name"])
        try:
            self.amenity_repo.add(amenity)
        except IntegrityError:
            db.session.rollback()
            raise ValueError("Amenity name already exists")
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

        amenity_ids = data.get("amenities", [])
        amenity_objects = []
        for aid in amenity_ids:
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
        place.amenities = amenity_objects
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
        user = self.user_repo.get(data.get("user_id"))
        if not user:
            raise ValueError("User not found")
        place = self.place_repo.get(data.get("place_id"))
        if not place:
            raise ValueError("Place not found")
        if place.owner_id == data["user_id"]:
            raise ValueError("You cannot review your own place")

        review = Review(
            text=data["text"],
            rating=data["rating"],
            place_id=data["place_id"],
            user_id=data["user_id"],
        )
        try:
            self.review_repo.add(review)
        except IntegrityError:
            db.session.rollback()
            raise ValueError("You have already reviewed this place")
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
        data.pop("user_id", None)
        data.pop("place_id", None)
        review.update(data)
        return review

    def delete_review(self, review_id: str) -> bool:
        review = self.review_repo.get(review_id)
        if not review:
            return False
        self.review_repo.delete(review_id)
        return True