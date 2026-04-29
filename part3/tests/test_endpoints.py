import unittest
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app import create_app
from app.extensions import db
from app.models.user import User


class HBnBTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()
        self.app_ctx = self.app.app_context()
        self.app_ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_ctx.pop()

    def _post(self, url, data, headers=None):
        return self.client.post(
            url, data=json.dumps(data), content_type="application/json",
            headers=headers or {},
        )

    def _put(self, url, data, headers=None):
        return self.client.put(
            url, data=json.dumps(data), content_type="application/json",
            headers=headers or {},
        )

    def _delete(self, url, headers=None):
        return self.client.delete(url, headers=headers or {})

    def _get(self, url, headers=None):
        return self.client.get(url, headers=headers or {})

    def _login(self, email, password):
        res = self._post("/api/v1/auth/login", {"email": email, "password": password})
        return res.get_json().get("access_token") if res.status_code == 200 else None

    def _create_admin(self):
        from app.services import facade
        existing = facade.user_repo.get_by_attribute("email", "admin@test.com")
        if not existing:
            admin = User(
                first_name="Admin", last_name="User",
                email="admin@test.com", password="admin123", is_admin=True,
            )
            facade.user_repo.add(admin)
        return facade.user_repo.get_by_attribute("email", "admin@test.com")

    def _admin_headers(self):
        self._create_admin()
        token = self._login("admin@test.com", "admin123")
        return {"Authorization": f"Bearer {token}"}

    def _create_regular_user(self, email="regular@test.com", password="pass123"):
        res = self._post("/api/v1/users/", {
            "first_name": "Regular", "last_name": "User",
            "email": email, "password": password,
        })
        return res

    def _regular_headers(self, email="regular@test.com", password="pass123"):
        self._create_regular_user(email, password)
        token = self._login(email, password)
        return {"Authorization": f"Bearer {token}"}

    # ------------------------------------------------------------------ Auth

    def test_login_success(self):
        self._create_regular_user()
        res = self._post("/api/v1/auth/login", {
            "email": "regular@test.com", "password": "pass123",
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn("access_token", res.get_json())

    def test_login_invalid_password(self):
        self._create_regular_user()
        res = self._post("/api/v1/auth/login", {
            "email": "regular@test.com", "password": "wrong",
        })
        self.assertEqual(res.status_code, 401)

    def test_login_nonexistent_user(self):
        res = self._post("/api/v1/auth/login", {
            "email": "nobody@test.com", "password": "whatever",
        })
        self.assertEqual(res.status_code, 401)

    # ------------------------------------------------------------------ Users

    def test_create_user_success(self):
        res = self._post("/api/v1/users/", {
            "first_name": "Alice", "last_name": "Smith",
            "email": "alice@example.com", "password": "pass123",
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertEqual(data["first_name"], "Alice")
        self.assertNotIn("password", data)

    def test_create_user_duplicate_email(self):
        self._post("/api/v1/users/", {
            "first_name": "Bob", "last_name": "Jones",
            "email": "bob@example.com", "password": "pass",
        })
        res = self._post("/api/v1/users/", {
            "first_name": "Bob2", "last_name": "Jones2",
            "email": "bob@example.com", "password": "pass",
        })
        self.assertEqual(res.status_code, 409)

    def test_create_user_invalid_email(self):
        res = self._post("/api/v1/users/", {
            "first_name": "Bad", "last_name": "Email",
            "email": "not-an-email", "password": "pass",
        })
        self.assertEqual(res.status_code, 400)

    def test_get_user_not_found(self):
        headers = self._admin_headers()
        res = self._get("/api/v1/users/nonexistent-id", headers=headers)
        self.assertEqual(res.status_code, 404)

    def test_get_all_users_admin(self):
        headers = self._admin_headers()
        self._post("/api/v1/users/", {
            "first_name": "Carol", "last_name": "Lee",
            "email": "carol@example.com", "password": "pass",
        })
        res = self._get("/api/v1/users/", headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.get_json(), list)

    def test_get_all_users_unauthorized(self):
        headers = self._regular_headers()
        res = self._get("/api/v1/users/", headers=headers)
        self.assertEqual(res.status_code, 403)

    def test_get_all_users_no_token(self):
        res = self._get("/api/v1/users/")
        self.assertEqual(res.status_code, 401)

    def test_update_user_by_admin(self):
        admin_headers = self._admin_headers()
        res = self._post("/api/v1/users/", {
            "first_name": "Dave", "last_name": "King",
            "email": "dave@example.com", "password": "pass",
        })
        uid = res.get_json()["id"]
        res2 = self._put(f"/api/v1/users/{uid}", {"first_name": "David"},
                         headers=admin_headers)
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.get_json()["first_name"], "David")

    def test_update_user_by_self(self):
        self._post("/api/v1/users/", {
            "first_name": "Self", "last_name": "Update",
            "email": "self@test.com", "password": "pass123",
        })
        token = self._login("self@test.com", "pass123")
        uid = self._get("/api/v1/users/", headers={"Authorization": f"Bearer {token}"}).get_json()[0]["id"] if False else self._post("/api/v1/users/", {
            "first_name": "Self2", "last_name": "Update2",
            "email": "self2@test.com", "password": "pass123",
        }).get_json()["id"]
        token2 = self._login("self2@test.com", "pass123")
        headers = {"Authorization": f"Bearer {token2}"}
        res = self._put(f"/api/v1/users/{uid}", {"first_name": "Updated"},
                        headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["first_name"], "Updated")

    def test_update_user_by_other_forbidden(self):
        self._create_regular_user("user_a@test.com", "pass123")
        self._create_regular_user("user_b@test.com", "pass456")
        res_b = self._post("/api/v1/users/", {
            "first_name": "UserB", "last_name": "Test",
            "email": "user_b2@test.com", "password": "pass456",
        })
        uid_b = res_b.get_json()["id"]
        token_a = self._login("user_a@test.com", "pass123")
        headers_a = {"Authorization": f"Bearer {token_a}"}
        res = self._put(f"/api/v1/users/{uid_b}", {"first_name": "Hacked"},
                        headers=headers_a)
        self.assertEqual(res.status_code, 403)

    def test_update_user_cannot_escalate_to_admin(self):
        self._post("/api/v1/users/", {
            "first_name": "Normal", "last_name": "User",
            "email": "normal@test.com", "password": "pass123",
        })
        token = self._login("normal@test.com", "pass123")
        uid = self._post("/api/v1/users/", {
            "first_name": "Normal2", "last_name": "User2",
            "email": "normal2@test.com", "password": "pass123",
        }).get_json()["id"]
        token2 = self._login("normal2@test.com", "pass123")
        headers = {"Authorization": f"Bearer {token2}"}
        res = self._put(f"/api/v1/users/{uid}", {"is_admin": True},
                        headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertFalse(res.get_json().get("is_admin", True))

    def test_update_user_password_is_hashed(self):
        self._post("/api/v1/users/", {
            "first_name": "Pass", "last_name": "Test",
            "email": "passupd@test.com", "password": "oldpass",
        })
        uid = self._post("/api/v1/users/", {
            "first_name": "Pass2", "last_name": "Test2",
            "email": "passupd2@test.com", "password": "oldpass",
        }).get_json()["id"]
        token = self._login("passupd2@test.com", "oldpass")
        headers = {"Authorization": f"Bearer {token}"}
        self._put(f"/api/v1/users/{uid}", {"password": "newpass"},
                   headers=headers)
        login_res = self._post("/api/v1/auth/login", {
            "email": "passupd2@test.com", "password": "newpass",
        })
        self.assertEqual(login_res.status_code, 200)

    # --------------------------------------------------------------- Amenities

    def test_create_amenity_success(self):
        headers = self._admin_headers()
        res = self._post("/api/v1/amenities/", {"name": "WiFi"}, headers=headers)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.get_json()["name"], "WiFi")

    def test_create_amenity_unauthorized_no_token(self):
        res = self._post("/api/v1/amenities/", {"name": "Pool"})
        self.assertIn(res.status_code, [401, 403])

    def test_create_amenity_unauthorized_regular_user(self):
        headers = self._regular_headers()
        res = self._post("/api/v1/amenities/", {"name": "Pool"}, headers=headers)
        self.assertIn(res.status_code, [401, 403])

    def test_create_amenity_duplicate_name(self):
        headers = self._admin_headers()
        self._post("/api/v1/amenities/", {"name": "Sauna"}, headers=headers)
        res = self._post("/api/v1/amenities/", {"name": "Sauna"}, headers=headers)
        self.assertEqual(res.status_code, 409)

    def test_get_amenity_not_found(self):
        res = self._get("/api/v1/amenities/bad-id")
        self.assertEqual(res.status_code, 404)

    def test_update_amenity_by_admin(self):
        headers = self._admin_headers()
        res = self._post("/api/v1/amenities/", {"name": "Pool"}, headers=headers)
        aid = res.get_json()["id"]
        res2 = self._put(f"/api/v1/amenities/{aid}",
                         {"name": "Swimming Pool"}, headers=headers)
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.get_json()["name"], "Swimming Pool")

    def test_update_amenity_by_regular_user(self):
        admin_h = self._admin_headers()
        reg_h = self._regular_headers()
        res = self._post("/api/v1/amenities/", {"name": "Gym"}, headers=admin_h)
        aid = res.get_json()["id"]
        res2 = self._put(f"/api/v1/amenities/{aid}", {"name": "Hacked"}, headers=reg_h)
        self.assertIn(res2.status_code, [401, 403])

    # ----------------------------------------------------------------- Places

    def _setup_place_fixtures(self):
        admin_h = self._admin_headers()
        uid = self._post("/api/v1/users/", {
            "first_name": "Owner", "last_name": "Test",
            "email": f"owner{os.getpid()}@test.com", "password": "pass123",
        }).get_json()["id"]
        aid = self._post("/api/v1/amenities/", {"name": "Garden"}, headers=admin_h).get_json()["id"]
        token = self._login("admin@test.com", "admin123")
        return uid, aid, {"Authorization": f"Bearer {token}"}

    def test_create_place_success(self):
        uid, aid, headers = self._setup_place_fixtures()
        res = self._post("/api/v1/places/", {
            "title": "Beach House", "description": "Nice view",
            "price": 120.0, "latitude": 34.0, "longitude": -118.0,
            "owner_id": uid, "amenities": [aid],
        }, headers=headers)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.get_json()["title"], "Beach House")

    def test_create_place_invalid_price(self):
        uid, _, headers = self._setup_place_fixtures()
        res = self._post("/api/v1/places/", {
            "title": "Cheap", "price": -5, "latitude": 0,
            "longitude": 0, "owner_id": uid,
        }, headers=headers)
        self.assertEqual(res.status_code, 400)

    def test_create_place_invalid_latitude(self):
        uid, _, headers = self._setup_place_fixtures()
        res = self._post("/api/v1/places/", {
            "title": "Out of bounds", "price": 10, "latitude": 999,
            "longitude": 0, "owner_id": uid,
        }, headers=headers)
        self.assertEqual(res.status_code, 400)

    def test_create_place_unknown_owner(self):
        _, _, headers = self._setup_place_fixtures()
        res = self._post("/api/v1/places/", {
            "title": "Ghost House", "price": 50, "latitude": 0,
            "longitude": 0, "owner_id": "nonexistent",
        }, headers=headers)
        self.assertEqual(res.status_code, 404)

    def test_create_place_sets_owner_from_jwt_for_regular_user(self):
        admin_h = self._admin_headers()
        uid = self._post("/api/v1/users/", {
            "first_name": "PlaceOwner", "last_name": "User",
            "email": "placeownertest@test.com", "password": "pass123",
        }).get_json()["id"]
        aid = self._post("/api/v1/amenities/", {"name": "WiFi2"}, headers=admin_h).get_json()["id"]
        token = self._login("placeownertest@test.com", "pass123")
        headers = {"Authorization": f"Bearer {token}"}
        res = self._post("/api/v1/places/", {
            "title": "My Place", "price": 100, "latitude": 10.0,
            "longitude": 20.0, "owner_id": uid, "amenities": [aid],
        }, headers=headers)
        self.assertEqual(res.status_code, 201)

    def test_get_place_detail_no_email_leak(self):
        uid, aid, headers = self._setup_place_fixtures()
        place_id = self._post("/api/v1/places/", {
            "title": "Villa", "price": 200, "latitude": 10.0,
            "longitude": 20.0, "owner_id": uid, "amenities": [aid],
        }, headers=headers).get_json()["id"]
        res = self._get(f"/api/v1/places/{place_id}")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("owner", data)
        self.assertIn("amenities", data)
        self.assertNotIn("email", data["owner"])

    def test_get_place_not_found(self):
        res = self._get("/api/v1/places/bad-id")
        self.assertEqual(res.status_code, 404)

    def test_create_place_requires_auth(self):
        res = self._post("/api/v1/places/", {
            "title": "No Auth", "price": 10, "latitude": 0,
            "longitude": 0, "owner_id": "fake",
        })
        self.assertEqual(res.status_code, 401)

    def test_update_place_by_non_owner(self):
        uid, _, headers = self._setup_place_fixtures()
        place_id = self._post("/api/v1/places/", {
            "title": "Owner Place", "price": 100, "latitude": 10.0,
            "longitude": 20.0, "owner_id": uid,
        }, headers=headers).get_json()["id"]
        other_headers = self._regular_headers("other@test.com", "pass123")
        res = self._put(f"/api/v1/places/{place_id}",
                        {"title": "Hacked"}, headers=other_headers)
        self.assertEqual(res.status_code, 403)

    # --------------------------------------------------------------- Reviews

    def _setup_review_fixtures(self):
        admin_h = self._admin_headers()
        uid = self._post("/api/v1/users/", {
            "first_name": "ReviewOwner", "last_name": "Test",
            "email": "revowner@test.com", "password": "pass123",
        }).get_json()["id"]
        token = self._login("admin@test.com", "admin123")
        headers = {"Authorization": f"Bearer {token}"}
        p = self._post("/api/v1/places/", {
            "title": "Review Target", "price": 80,
            "latitude": 5.0, "longitude": 10.0, "owner_id": uid,
        }, headers=headers).get_json()
        return uid, p["id"], token

    def test_create_review_success(self):
        uid, pid, token = self._setup_review_fixtures()
        res = self._post("/api/v1/reviews/", {
            "text": "Great place!", "rating": 5,
            "user_id": uid, "place_id": pid,
        }, headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.get_json()["rating"], 5)

    def test_create_review_sets_user_from_jwt(self):
        uid, pid, _ = self._setup_review_fixtures()
        reviewer_uid = self._post("/api/v1/users/", {
            "first_name": "Reviewer", "last_name": "Test",
            "email": "rev_test@test.com", "password": "pass123",
        }).get_json()["id"]
        token = self._login("rev_test@test.com", "pass123")
        res = self._post("/api/v1/reviews/", {
            "text": "From JWT!", "rating": 4,
            "user_id": reviewer_uid, "place_id": pid,
        }, headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.get_json()["user_id"], reviewer_uid)

    def test_create_review_invalid_rating(self):
        uid, pid, token = self._setup_review_fixtures()
        res = self._post("/api/v1/reviews/", {
            "text": "Bad rating", "rating": 10,
            "user_id": uid, "place_id": pid,
        }, headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(res.status_code, 400)

    def test_create_review_unauthorized(self):
        uid, pid, _ = self._setup_review_fixtures()
        res = self._post("/api/v1/reviews/", {
            "text": "No Auth", "rating": 3,
            "user_id": uid, "place_id": pid,
        })
        self.assertEqual(res.status_code, 401)

    def test_get_reviews_for_place(self):
        uid, pid, token = self._setup_review_fixtures()
        self._post("/api/v1/reviews/", {
            "text": "Nice!", "rating": 4,
            "user_id": uid, "place_id": pid,
        }, headers={"Authorization": f"Bearer {token}"})
        res = self._get(f"/api/v1/places/{pid}/reviews")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.get_json()), 1)

    def test_update_review(self):
        uid, pid, token = self._setup_review_fixtures()
        rid = self._post("/api/v1/reviews/", {
            "text": "OK", "rating": 3,
            "user_id": uid, "place_id": pid,
        }, headers={"Authorization": f"Bearer {token}"}).get_json()["id"]
        res = self._put(f"/api/v1/reviews/{rid}",
                        {"text": "Updated!", "rating": 5},
                        headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["rating"], 5)

    def test_update_review_by_non_author(self):
        uid, pid, token = self._setup_review_fixtures()
        rid = self._post("/api/v1/reviews/", {
            "text": "OK", "rating": 3,
            "user_id": uid, "place_id": pid,
        }, headers={"Authorization": f"Bearer {token}"}).get_json()["id"]
        other_headers = self._regular_headers("other_rev@test.com", "pass123")
        res = self._put(f"/api/v1/reviews/{rid}",
                        {"text": "Hacked!"}, headers=other_headers)
        self.assertEqual(res.status_code, 403)

    def test_delete_review(self):
        uid, pid, token = self._setup_review_fixtures()
        rid = self._post("/api/v1/reviews/", {
            "text": "Delete me", "rating": 2,
            "user_id": uid, "place_id": pid,
        }, headers={"Authorization": f"Bearer {token}"}).get_json()["id"]
        res = self._delete(f"/api/v1/reviews/{rid}",
                           headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(res.status_code, 200)
        res2 = self._get(f"/api/v1/reviews/{rid}")
        self.assertEqual(res2.status_code, 404)

    def test_delete_review_not_found(self):
        admin_h = self._admin_headers()
        res = self._delete("/api/v1/reviews/nonexistent", headers=admin_h)
        self.assertEqual(res.status_code, 404)

    def test_delete_review_unauthorized(self):
        uid, pid, token = self._setup_review_fixtures()
        rid = self._post("/api/v1/reviews/", {
            "text": "Delete me", "rating": 2,
            "user_id": uid, "place_id": pid,
        }, headers={"Authorization": f"Bearer {token}"}).get_json()["id"]
        res = self._delete(f"/api/v1/reviews/{rid}")
        self.assertIn(res.status_code, [401, 403])

    def test_delete_review_by_non_author(self):
        uid, pid, token = self._setup_review_fixtures()
        rid = self._post("/api/v1/reviews/", {
            "text": "Protected", "rating": 4,
            "user_id": uid, "place_id": pid,
        }, headers={"Authorization": f"Bearer {token}"}).get_json()["id"]
        other_headers = self._regular_headers("other_del@test.com", "pass123")
        res = self._delete(f"/api/v1/reviews/{rid}", headers=other_headers)
        self.assertEqual(res.status_code, 403)


if __name__ == "__main__":
    unittest.main()