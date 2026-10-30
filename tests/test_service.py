import json

import httpx
import pytest
from openai import OpenAI
from test_models import WORDS, groups

from connections.config import Settings
from connections.models import SolveRequest
from connections.service import ServiceError, SolverService


def response_body(payload, status="completed"):
    return {
        "id": "resp_test",
        "created_at": 0,
        "model": "gpt-5.4-mini",
        "object": "response",
        "status": status,
        "error": None,
        "incomplete_details": None,
        "output": [
            {
                "id": "msg_test",
                "type": "message",
                "role": "assistant",
                "status": "completed",
                "content": [
                    {"type": "output_text", "text": json.dumps(payload), "annotations": []}
                ],
            }
        ],
        "usage": {
            "input_tokens": 1000,
            "output_tokens": 500,
            "total_tokens": 1500,
            "input_tokens_details": {"cached_tokens": 200},
            "output_tokens_details": {"reasoning_tokens": 100},
        },
    }


def make_service(body, status=200):
    requests = []

    def handle(request):
        requests.append(json.loads(request.content))
        return httpx.Response(status, json=body)

    client = OpenAI(
        api_key="test-key",
        max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(handle)),
    )
    return SolverService(Settings(api_key="test-key"), client=client), requests


def test_sdk_structured_roundtrip_cache_and_billing():
    service, requests = make_service(response_body({"groups": [g.model_dump() for g in groups()]}))
    request = SolveRequest(words=WORDS)
    result = service.solve(request)
    assert result.value.groups[0].words == WORDS[:4]
    assert result.usage.estimated_cost_usd == pytest.approx(0.002865)
    assert result.usage.output_tokens == 500
    cached = service.solve(request)
    assert cached.cached and cached.usage.estimated_cost_usd == 0
    assert len(requests) == 1
    assert requests[0]["store"] is False
    assert requests[0]["max_output_tokens"] == 3500
    assert requests[0]["text"]["format"]["strict"] is True
    assert requests[0]["reasoning"]["effort"] == "low"


def test_invalid_partition_is_not_returned_or_cached():
    bad = groups()
    bad[0].words[0] = "INVENTED"
    service, requests = make_service(response_body({"groups": [g.model_dump() for g in bad]}))
    for _ in range(2):
        with pytest.raises(ServiceError, match="valid"):
            service.solve(SolveRequest(words=WORDS))
    assert len(requests) == 2


@pytest.mark.parametrize(
    "status,code,match",
    [
        (401, "invalid_api_key", "API key"),
        (429, "insufficient_quota", "billing"),
        (429, "rate_limit_exceeded", "limit"),
        (500, "server_error", "OpenAI"),
    ],
)
def test_api_errors_are_actionable_and_not_retried(status, code, match):
    service, requests = make_service(
        {"error": {"message": "sensitive server body", "type": code, "code": code}}, status
    )
    with pytest.raises(ServiceError, match=match) as error:
        service.solve(SolveRequest(words=WORDS))
    assert "sensitive" not in str(error.value)
    assert len(requests) == 1


def test_incomplete_response_has_no_partial_solution():
    body = response_body({}, status="incomplete")
    body["output"] = []
    body["incomplete_details"] = {"reason": "max_output_tokens"}
    service, _ = make_service(body)
    with pytest.raises(ServiceError, match="budget"):
        service.solve(SolveRequest(words=WORDS))


def test_refusal_has_no_partial_solution():
    body = response_body({})
    body["output"][0]["content"] = [{"type": "refusal", "refusal": "No"}]
    service, _ = make_service(body)
    with pytest.raises(ServiceError, match="declined"):
        service.solve(SolveRequest(words=WORDS))


def test_all_locked_returns_without_network():
    service, requests = make_service({})
    result = service.solve(SolveRequest(words=WORDS, locked=groups()))
    assert len(result.value.groups) == 4
    assert not requests


def test_missing_key_is_local_error():
    with pytest.raises(ServiceError, match="API key"):
        SolverService(Settings(api_key="")).solve(SolveRequest(words=WORDS))


def test_deeper_mode_uses_larger_explicit_budget():
    service, requests = make_service(response_body({"groups": [g.model_dump() for g in groups()]}))
    service.solve(SolveRequest(words=WORDS, mode="deeper"))
    assert requests[0]["max_output_tokens"] == 6500
    assert requests[0]["reasoning"]["effort"] == "medium"


def test_key_is_never_redirected_by_sdk_base_url_environment(monkeypatch):
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.invalid/v1")
    service = SolverService(Settings(api_key="test-key"))
    try:
        assert str(service._get_client().base_url) == "https://api.openai.com/v1/"
    finally:
        service.close()


def test_extraction_sends_image_and_preserves_warning():
    from test_images import make_image

    from connections.images import prepare_image

    service, requests = make_service(
        response_body({"words": WORDS[:15], "warning": "One tile blurry"})
    )
    result = service.extract(prepare_image(make_image()))
    assert result.value.words == WORDS[:15]
    assert result.value.warning == "One tile blurry"
    content = requests[0]["input"][0]["content"]
    assert content[1]["type"] == "input_image"
    assert content[1]["image_url"].startswith("data:image/png;base64,")
    assert content[1]["detail"] == "high"
    assert requests[0]["reasoning"]["effort"] == "none"
    assert requests[0]["max_output_tokens"] == 1200
