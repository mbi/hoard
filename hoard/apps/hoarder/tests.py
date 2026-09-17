import json

from django.test import TestCase

from .models import Category, Header, Hoard


class RecordViewTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Logs", slug="logs")

    def post(self, slug="logs", body=None, **headers):
        if body is None:
            body = {"key": "value"}
        return self.client.post(
            f"/api/hoard/{slug}",
            data=json.dumps(body),
            content_type="application/json",
            **headers,
        )

    def test_stores_payload_and_returns_id(self):
        response = self.post(body={"event": "click", "count": 3})

        self.assertEqual(response.status_code, 200)
        hoard = Hoard.objects.get(pk=response.json()["id"])
        self.assertEqual(hoard.category, self.category)
        self.assertEqual(hoard.data, {"event": "click", "count": 3})
        self.assertIsNotNone(hoard.recorded)

    def test_stores_nested_json_unchanged(self):
        payload = {"outer": {"inner": [1, "two", None]}, "flag": False}

        response = self.post(body=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Hoard.objects.get(pk=response.json()["id"]).data, payload)

    def test_unknown_slug_returns_404(self):
        response = self.post(slug="missing")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(Hoard.objects.count(), 0)

    def test_get_returns_405(self):
        response = self.client.get("/api/hoard/logs")

        self.assertEqual(response.status_code, 405)
        self.assertEqual(Hoard.objects.count(), 0)

    def test_malformed_json_returns_400(self):
        response = self.client.post(
            "/api/hoard/logs", data="{not json", content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Hoard.objects.count(), 0)

    def test_empty_body_returns_400(self):
        response = self.client.post("/api/hoard/logs")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Hoard.objects.count(), 0)

    def test_missing_required_header_returns_400(self):
        Header.objects.create(category=self.category, key="X-Token", value="secret")

        response = self.post()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Hoard.objects.count(), 0)

    def test_wrong_header_value_returns_400(self):
        Header.objects.create(category=self.category, key="X-Token", value="secret")

        response = self.post(HTTP_X_TOKEN="nope")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Hoard.objects.count(), 0)

    def test_matching_header_is_case_insensitive(self):
        Header.objects.create(category=self.category, key="X-Token", value="secret")

        response = self.post(HTTP_X_TOKEN="secret")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Hoard.objects.count(), 1)

    def test_all_required_headers_must_match(self):
        Header.objects.create(category=self.category, key="X-Token", value="secret")
        Header.objects.create(category=self.category, key="X-Other", value="other")

        response = self.post(HTTP_X_TOKEN="secret")
        self.assertEqual(response.status_code, 400)

        response = self.post(HTTP_X_TOKEN="secret", HTTP_X_OTHER="other")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Hoard.objects.count(), 1)

    def test_category_without_headers_accepts_any_request(self):
        response = self.post()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Hoard.objects.count(), 1)
