import json
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from .models import Category, Header, Hoard
from .preprocessing import OPENROUTER_KEYS, flatten_openrouter


def add_one(data):
    return {"value": data["value"] + 1}


def double(data):
    return {"value": data["value"] * 2}


def broken(data):
    raise ValueError("boom")


def returns_list(data):
    return [1, 2]


class FlattenOpenrouterTests(TestCase):
    def otlp(self, spans):
        return {"resourceSpans": [{"scopeSpans": [{"spans": spans}]}]}

    def attr(self, key, value):
        return {"key": key, "value": value}

    def test_flattens_multi_span_payload(self):
        payload = self.otlp(
            [
                {
                    "name": "LLM Generation",
                    "attributes": [
                        self.attr("session.id", {"stringValue": "sess-1"}),
                        self.attr(
                            "trace.metadata.provider_responses",
                            {"stringValue": '[{"id": "req_1", "status": 200}]'},
                        ),
                        self.attr(
                            "trace.metadata.openrouter_generation.usage",
                            {"doubleValue": 0.00188},
                        ),
                        self.attr(
                            "trace.metadata.openrouter_generation.usage_upstream",
                            {"doubleValue": 0.00188},
                        ),
                        self.attr("span.type", {"stringValue": "generation"}),
                        self.attr(
                            "span.metadata.provider_responses",
                            {"stringValue": '[{"id": "req_1", "status": 200}]'},
                        ),
                        self.attr(
                            "span.metadata.openrouter_generation"
                            ".upstream_raw_response_usage",
                            {"stringValue": '{"prompt_tokens": 10}'},
                        ),
                        self.attr(
                            "span.metadata.openrouter_generation.tokens_prompt",
                            {"intValue": 42547},
                        ),
                        self.attr(
                            "span.metadata.openrouter_generation.tokens_completion",
                            {"intValue": 555},
                        ),
                        self.attr("span.input", {"stringValue": '{"messages": []}'}),
                        self.attr(
                            "span.output",
                            {"stringValue": '{"completion": "hi", "reasoning": null}'},
                        ),
                        self.attr("gen_ai.request.model", {"stringValue": "m1"}),
                        self.attr("gen_ai.response.model", {"stringValue": "m1"}),
                        self.attr("gen_ai.response.id", {"stringValue": "gen-1"}),
                        self.attr(
                            "gen_ai.usage.input_tokens.cached", {"intValue": 53568}
                        ),
                    ],
                },
                {
                    "name": "provider attempt 1: Relace",
                    "attributes": [
                        self.attr("span.type", {"stringValue": "span"}),
                        self.attr(
                            "gen_ai.response.id", {"stringValue": "gen-1:attempt-0"}
                        ),
                    ],
                },
            ]
        )

        result = flatten_openrouter(payload)

        self.assertEqual(
            result,
            {
                "session.id": "sess-1",
                "trace.metadata.provider_responses": [{"id": "req_1", "status": 200}],
                "trace.metadata.openrouter_generation.usage": 0.00188,
                "trace.metadata.openrouter_generation.usage_upstream": 0.00188,
                "trace.metadata.openrouter_generation.usage_cache": None,
                "span.type": "generation",
                "span.metadata.provider_responses": [{"id": "req_1", "status": 200}],
                "span.metadata.openrouter_generation.upstream_raw_response_usage": {
                    "prompt_tokens": 10
                },
                "span.metadata.openrouter_generation.tokens_prompt": 42547,
                "span.metadata.openrouter_generation.tokens_completion": 555,
                "span.input": {"messages": []},
                "span.output": {"completion": "hi", "reasoning": None},
                "gen_ai.request.model": "m1",
                "gen_ai.response.model": "m1",
                "gen_ai.response.id": "gen-1",
                "gen_ai.usage.input_tokens.cached": 53568,
            },
        )

    def test_empty_resource_spans_yields_all_null(self):
        expected = dict.fromkeys(OPENROUTER_KEYS)
        self.assertEqual(flatten_openrouter({"resourceSpans": []}), expected)

    def test_plain_and_invalid_json_strings_are_kept(self):
        payload = self.otlp(
            [
                {
                    "attributes": [
                        self.attr("span.output", {"stringValue": "plain text"}),
                        self.attr("span.input", {"stringValue": "{not json"}),
                        self.attr("session.id", {"stringValue": ""}),
                    ]
                }
            ]
        )

        result = flatten_openrouter(payload)

        self.assertEqual(result["span.output"], "plain text")
        self.assertEqual(result["span.input"], "{not json")
        self.assertEqual(result["session.id"], "")

    def test_non_dict_payload_passes_through(self):
        self.assertEqual(flatten_openrouter([1, 2]), [1, 2])

    def test_non_otlp_dict_passes_through(self):
        payload = {"event": "click"}
        self.assertEqual(flatten_openrouter(payload), payload)


class BackfillPreprocessorsTests(TestCase):
    def test_backfill_flattens_existing_hoards_once(self):
        category = Category.objects.create(
            name="OpenRouter",
            slug="orl",
            preprocessors=["apps.hoarder.preprocessing.flatten_openrouter"],
        )
        otlp = Hoard.objects.create(
            category=category,
            data={
                "resourceSpans": [
                    {
                        "scopeSpans": [
                            {
                                "spans": [
                                    {
                                        "attributes": [
                                            {
                                                "key": "session.id",
                                                "value": {"stringValue": "sess-1"},
                                            },
                                            {
                                                "key": "span.type",
                                                "value": {"stringValue": "generation"},
                                            },
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            },
        )
        already_flat = Hoard.objects.create(
            category=category,
            data={**dict.fromkeys(OPENROUTER_KEYS), "session.id": "sess-1"},
        )

        call_command("backfill_preprocessors", stdout=StringIO())

        otlp.refresh_from_db()
        already_flat.refresh_from_db()
        expected = {
            **dict.fromkeys(OPENROUTER_KEYS),
            "session.id": "sess-1",
            "span.type": "generation",
        }
        self.assertEqual(otlp.data, expected)
        self.assertEqual(already_flat.data["session.id"], "sess-1")


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

    def test_preprocessors_applied_in_configured_order(self):
        self.category.preprocessors = [
            "apps.hoarder.tests.add_one",
            "apps.hoarder.tests.double",
        ]
        self.category.save()

        response = self.post(body={"value": 3})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Hoard.objects.get(pk=response.json()["id"]).data, {"value": 8})

        self.category.preprocessors = [
            "apps.hoarder.tests.double",
            "apps.hoarder.tests.add_one",
        ]
        self.category.save()

        response = self.post(body={"value": 3})

        self.assertEqual(Hoard.objects.get(pk=response.json()["id"]).data, {"value": 7})

    def test_failing_preprocessor_is_skipped(self):
        self.category.preprocessors = [
            "apps.hoarder.tests.broken",
            "apps.hoarder.tests.add_one",
        ]
        self.category.save()

        response = self.post(body={"value": 3})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Hoard.objects.get(pk=response.json()["id"]).data, {"value": 4})

    def test_unimportable_preprocessor_is_skipped(self):
        self.category.preprocessors = ["apps.hoarder.tests.does_not_exist"]
        self.category.save()

        response = self.post(body={"value": 3})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Hoard.objects.get(pk=response.json()["id"]).data, {"value": 3})

    def test_non_dict_return_is_skipped(self):
        self.category.preprocessors = ["apps.hoarder.tests.returns_list"]
        self.category.save()

        response = self.post(body={"value": 3})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Hoard.objects.get(pk=response.json()["id"]).data, {"value": 3})
