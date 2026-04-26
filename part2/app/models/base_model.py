import uuid
from datetime import datetime, timezone


class BaseModel:
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def save(self):
        self.updated_at = datetime.now(timezone.utc)

    def update(self, data: dict):
        for key, value in data.items():
            if key not in ("id", "created_at", "updated_at") and hasattr(self, key):
                setattr(self, key, value)
        self.save()
