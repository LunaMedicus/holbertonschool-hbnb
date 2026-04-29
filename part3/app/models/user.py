import re
from sqlalchemy.orm import validates
from app.models.base_model import BaseModel
from app.extensions import db, bcrypt

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class User(BaseModel):
    __tablename__ = "users"

    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False, default="")
    is_admin = db.Column(db.Boolean, default=False)

    places = db.relationship("Place", backref="owner", lazy=True,
                             cascade="all, delete-orphan",
                             passive_deletes=True)
    reviews = db.relationship("Review", backref="user", lazy=True,
                              cascade="all, delete-orphan",
                              passive_deletes=True)

    @validates("first_name")
    def validate_first_name(self, key, value):
        if not value or len(value) > 50:
            raise ValueError("first_name is required and must be at most 50 characters")
        return value

    @validates("last_name")
    def validate_last_name(self, key, value):
        if not value or len(value) > 50:
            raise ValueError("last_name is required and must be at most 50 characters")
        return value

    @validates("email")
    def validate_email(self, key, value):
        if not value or not EMAIL_REGEX.match(value):
            raise ValueError("A valid email address is required")
        return value

    def __init__(self, first_name, last_name, email, password="", is_admin=False):
        super().__init__()
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.is_admin = is_admin
        self.hash_password(password)

    def hash_password(self, password):
        if password:
            self.password = bcrypt.generate_password_hash(password).decode("utf-8")

    def verify_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

    def to_dict(self, include_email=False):
        result = {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "is_admin": self.is_admin,
        }
        if include_email:
            result["email"] = self.email
        return result