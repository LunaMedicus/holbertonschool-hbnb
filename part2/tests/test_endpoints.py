import unittest
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app import create_app


class HBnBTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("development")
        self.client = self.app.test_client()
        self.app_ctx = self.app.app_context()
        self.app_ctx.push()

    def tearDown(self):
        self.app_ctx.pop()

    def _post(self, url, data):
        return self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

    def _put(self, url, data):
        return self.client.put(
            url, data=json.dumps(data), content_type="application/json"
        )

    # ------------------------------------------------------------------ Users

    def test_create_user_success(self):
        res = self._post("/api/v1/users/", {
            "first_name": "Alice", "last_name": "Smith", "email": "alice@example.com"
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertEqual(data["first_name"], "Alice")
        self.assertNotIn("password", data)

    def test_create_user_duplicate_email(self):
        self._post("/api/v1/users/", {
            "first_name": "Bob", "last_name": "Jones", "email": "bob@example.com"
        })
        res = self._post("/api/v1/users/", {
            "first_name": "Bob2", "last_name": "Jones2", "email": "bob@example.com"
        })
        self.assertEqual(res.status_code, 409)

    def test_create_user_invalid_email(self):
        res = self._post("/api/v1/users/", {
            "first_name": "Bad", "last_name": "Email", "email": "not-an-email"
        })
        self.assertEqual(res.status_code, 400)

    def test_get_user_not_found(self):
        res = self.client.get("/api/v1/users/nonexistent-id")
        self.assertEqual(res.status_code, 404)

    def test_get_all_users(self):
        self._post("/api/v1/users/", {
            "first_name": "Carol", "last_name": "Lee", "email": "carol@example.com"
        })
        res = self.client.get("/api/v1/users/")
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.get_json(), list)

    def test_update_user(self):
        res = self._post("/api/v1/users/", {
            "first_name": "Dave", "last_name": "King", "email": "dave@example.com"
        })
        uid = res.get_json()["id"]
        res2 = self._put(f"/api/v1/users/{uid}", {"first_name": "David"})
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.get_json()["first_name"], "David")

    # --------------------------------------------------------------- Amenities

    def test_create_amenity_success(self):
        res = self._post("/api/v1/amenities/", {"name": "WiFi"})
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.get_json()["name"], "WiFi")

    def test_create_amenity_missing_name(self):
        res = self._post("/api/v1/amenities/", {})
        self.assertIn(res.status_code, [400, 422])

    def test_get_amenity_not_found(self):
        res = self.client.get("/api/v1/amenities/bad-id")
        self.assertEqual(res.status_code, 404)

    def test_update_amenity(self):
        res = self._post("/api/v1/amenities/", {"name": "Pool"})
        aid = res.get_json()["id"]
        res2 = self._put(f"/api/v1/amenities/{aid}", {"name": "Swimming Pool"})
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.get_json()["name"], "Swimming Pool")

    # ----------------------------------------------------------------- Places

    def _create_user_and_amenity(self):
        u = self._post("/api/v1/users/", {
            "first_name": "Owner", "last_name": "Test", "email": f"owner_{id(self)}@test.com"
        }).get_json()
        a = self._post("/api/v1/amenities/", {"name": "Garden"}).get_json()
        return u["id"], a["id"]

    def test_create_place_success(self):
        uid, aid = self._create_user_and_amenity()
        res = self._post("/api/v1/places/", {
            "title": "Beach House",
            "description": "Nice view",
            "price": 120.0,
            "latitude": 34.0,
            "longitude": -118.0,
            "owner_id": uid,
            "amenities": [aid],
        })
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.get_json()["title"], "Beach House")

    def test_create_place_invalid_price(self):
        uid, _ = self._create_user_and_amenity()
        res = self._post("/api/v1/places/", {
            "title": "Cheap",
            "price": -5,
            "latitude": 0,
            "longitude": 0,
            "owner_id": uid,
        })
        self.assertEqual(res.status_code, 400)

    def test_create_place_invalid_latitude(self):
        uid, _ = self._create_user_and_amenity()
        res = self._post("/api/v1/places/", {
            "title": "Out of bounds",
            "price": 10,
            "latitude": 999,
            "longitude": 0,
            "owner_id": uid,
        })
        self.assertEqual(res.status_code, 400)

    def test_create_place_unknown_owner(self):
        res = self._post("/api/v1/places/", {
            "title": "Ghost House",
            "price": 50,
            "latitude": 0,
            "longitude": 0,
            "owner_id": "nonexistent",
        })
        self.assertEqual(res.status_code, 404)

    def test_get_place_detail_includes_owner_and_amenities(self):
        uid, aid = self._create_user_and_amenity()
        place_id = self._post("/api/v1/places/", {
            "title": "Villa",
            "price": 200,
            "latitude": 10.0,
            "longitude": 20.0,
            "owner_id": uid,
            "amenities": [aid],
        }).get_json()["id"]
        res = self.client.get(f"/api/v1/places/{place_id}")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("owner", data)
        self.assertIn("amenities", data)
        self.assertEqual(data["owner"]["id"], uid)

    def test_get_place_not_found(self):
        res = self.client.get("/api/v1/places/bad-id")
        self.assertEqual(res.status_code, 404)

    # --------------------------------------------------------------- Reviews

    def _create_place(self):
        uid, _ = self._create_user_and_amenity()
        p = self._post("/api/v1/places/", {
            "title": "Review Target",
            "price": 80,
            "latitude": 5.0,
            "longitude": 10.0,
            "owner_id": uid,
        }).get_json()
        return uid, p["id"]

    def test_create_review_success(self):
        uid, pid = self._create_place()
        res = self._post("/api/v1/reviews/", {
            "text": "Great place!", "rating": 5,
            "user_id": uid, "place_id": pid,
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertEqual(data["rating"], 5)

    def test_create_review_invalid_rating(self):
        uid, pid = self._create_place()
        res = self._post("/api/v1/reviews/", {
            "text": "Bad rating", "rating": 10,
            "user_id": uid, "place_id": pid,
        })
        self.assertEqual(res.status_code, 400)

    def test_create_review_unknown_user(self):
        _, pid = self._create_place()
        res = self._post("/api/v1/reviews/", {
            "text": "Ghost", "rating": 3,
            "user_id": "no-such-user", "place_id": pid,
        })
        self.assertEqual(res.status_code, 404)

    def test_get_reviews_for_place(self):
        uid, pid = self._create_place()
        self._post("/api/v1/reviews/", {
            "text": "Nice!", "rating": 4,
            "user_id": uid, "place_id": pid,
        })
        res = self.client.get(f"/api/v1/places/{pid}/reviews")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.get_json()), 1)

    def test_update_review(self):
        uid, pid = self._create_place()
        rid = self._post("/api/v1/reviews/", {
            "text": "OK", "rating": 3,
            "user_id": uid, "place_id": pid,
        }).get_json()["id"]
        res = self._put(f"/api/v1/reviews/{rid}", {"text": "Updated!", "rating": 5})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["rating"], 5)

    def test_delete_review(self):
        uid, pid = self._create_place()
        rid = self._post("/api/v1/reviews/", {
            "text": "Delete me", "rating": 2,
            "user_id": uid, "place_id": pid,
        }).get_json()["id"]
        res = self.client.delete(f"/api/v1/reviews/{rid}")
        self.assertEqual(res.status_code, 200)
        res2 = self.client.get(f"/api/v1/reviews/{rid}")
        self.assertEqual(res2.status_code, 404)

    def test_delete_review_not_found(self):
        res = self.client.delete("/api/v1/reviews/nonexistent")
        self.assertEqual(res.status_code, 404)


if __name__ == "__main__":
    unittest.main()
