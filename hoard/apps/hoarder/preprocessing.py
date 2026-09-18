"""Preprocessors selectable via Category.preprocessors (dotted import paths)."""

import json

# OpenRouter OTLP attributes kept by flatten_openrouter, flattened to dotted keys.
OPENROUTER_KEYS = [
    "session.id",
    "trace.metadata.provider_responses",
    "trace.metadata.openrouter_generation.usage",
    "trace.metadata.openrouter_generation.usage_upstream",
    "trace.metadata.openrouter_generation.usage_cache",
    "span.type",
    "span.metadata.provider_responses",
    "span.metadata.openrouter_generation.upstream_raw_response_usage",
    "span.metadata.openrouter_generation.tokens_prompt",
    "span.metadata.openrouter_generation.tokens_completion",
    "span.input",
    "span.output",
    "gen_ai.request.model",
    "gen_ai.response.model",
    "gen_ai.response.id",
    "gen_ai.usage.input_tokens.cached",
]


def _unwrap(value):
    """Strip the OTel value wrapper and parse JSON-encoded strings."""
    if isinstance(value, dict):
        wrapped = [v for k, v in value.items() if k.endswith("Value")]
        if len(wrapped) == 1:
            value = wrapped[0]
    if isinstance(value, str) and value[:1] in ("{", "["):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def flatten_openrouter(payload):
    """Flatten OTLP resourceSpans attributes to one dict of OPENROUTER_KEYS.

    Attributes repeated across spans keep their first occurrence (the
    "LLM Generation" span comes first); absent attributes stay None.
    Non-OTLP payloads pass through unchanged.
    """
    if not isinstance(payload, dict) or "resourceSpans" not in payload:
        return payload
    result = dict.fromkeys(OPENROUTER_KEYS)
    seen = set()
    for rs in payload.get("resourceSpans") or []:
        for ss in rs.get("scopeSpans") or []:
            for span in ss.get("spans") or []:
                for attr in span.get("attributes") or []:
                    key = attr.get("key")
                    if key in result and key not in seen:
                        seen.add(key)
                        result[key] = _unwrap(attr.get("value"))
    return result
