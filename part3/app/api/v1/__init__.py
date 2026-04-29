from flask_jwt_extended import get_jwt, jwt_required
from functools import wraps


def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if not claims.get("is_admin"):
            return {"error": "Admin access required"}, 403
        return fn(*args, **kwargs)
    return wrapper