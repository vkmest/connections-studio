import json

import httpx
import pytest
from openai import OpenAI
from test_images import make_image
from test_models import WORDS, groups

from connections.config import Settings
from connections.images import prepare_image
from connections.models import SolveRequest
from connections.service import ServiceError, SolverService


@pytest.mark.parametrize(
    "provider,host", [("kimi", "api.moonshot.ai"), ("deepseek", "api.deepseek.com")]
)
@pytest.mark.parametrize("mode", ["budget", "extended"])
def test_cloud_chat_uses_own_key_and_validated_json(provider, host, mode):
    settings = Settings(provider=provider, api_key="provider-only")
    requests = []

    def handle(request):
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "id": "chat_test",
                "object": "chat.completion",
                "created": 0,
                "model": settings.model,
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {
                            "role": "assistant",
                            "content": json.dumps({"groups": [g.model_dump() for g in groups()]}),
                        },
                    }
                ],
                "usage": {"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300},
            },
        )

    from connections.providers import PROVIDERS

    client = OpenAI(
        api_key=settings.api_key,
        base_url=PROVIDERS[provider].base_url,
        max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(handle)),
    )
    service = SolverService(settings, client=client)
    result = service.solve(SolveRequest(words=WORDS, mode=mode))
    assert len(result.value.groups) == 4
    assert requests[0].url.host == host
    assert requests[0].headers["authorization"] == "Bearer provider-only"
    assert result.usage.estimated_cost_usd is None
    body = json.loads(requests[0].content)
    assert body["response_format"] == {"type": "json_object"}
    assert body["max_tokens"] == (16000 if mode == "extended" else 3500)
    assert requests[0].extensions["timeout"]["read"] == (300 if mode == "extended" else 90)
    if provider == "kimi":
        assert body["reasoning_effort"] == ("high" if mode == "extended" else "low")
    else:
        assert body["thinking"] == {"type": "enabled" if mode == "extended" else "disabled"}


def local_service(*, remote=False, malformed=False, solving=False):
    requests = []

    def handle(request):
        requests.append(request)
        if request.url.path == "/api/show":
            return httpx.Response(
                200,
                json={
                    "details": {"format": "gguf"},
                    "capabilities": ["completion", "vision"],
                    "remote_host": "https://ollama.com" if remote else "",
                },
            )
        return httpx.Response(
            200,
            json={
                "done": True,
                "done_reason": "stop",
                "message": {
                    "content": "{}"
                    if malformed
                    else json.dumps(
                        {"groups": [g.model_dump() for g in groups()]}
                        if solving
                        else {"words": WORDS, "warning": ""}
                    )
                },
                "prompt_eval_count": 100,
                "eval_count": 100,
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handle))
    return SolverService(
        Settings(provider="ollama", api_key="discard-me"), local_client=client
    ), requests


def test_local_images_never_have_cloud_credentials():
    service, requests = local_service()
    result = service.extract(prepare_image(make_image()))
    assert result.value.words == WORDS
    assert result.usage.estimated_cost_usd == 0
    assert [request.url.path for request in requests] == ["/api/show", "/api/chat"]
    for request in requests:
        assert request.url.host == "127.0.0.1"
        assert "authorization" not in request.headers
        assert b"discard-me" not in request.content
    body = json.loads(requests[1].content)
    assert body["stream"] is False
    assert body["format"]["type"] == "object"
    assert body["messages"][1]["images"]


def test_cloud_backed_ollama_alias_refused_before_puzzle_sent():
    service, requests = local_service(remote=True)
    with pytest.raises(ServiceError, match="local"):
        service.extract(prepare_image(make_image()))
    assert len(requests) == 1
    assert "messages" not in json.loads(requests[0].content)


def test_bad_local_output_never_reaches_the_grid():
    service, _ = local_service(malformed=True)
    with pytest.raises(ServiceError, match="valid"):
        service.extract(prepare_image(make_image()))


def test_extended_local_budget_has_enough_context_and_longer_request_timeout():
    service, requests = local_service(solving=True)
    result = service.solve(SolveRequest(words=WORDS, mode="extended"))
    assert len(result.value.groups) == 4
    body = json.loads(requests[-1].content)
    assert body["options"] == {"num_ctx": 20096, "num_predict": 16000}
    assert all(request.extensions["timeout"]["read"] == 300 for request in requests)


def chat_service(content):
    requests = []

    def handle(request):
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "id": "chat_format",
                "object": "chat.completion",
                "created": 0,
                "model": "deepseek-flash",
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {"role": "assistant", "content": content},
                    }
                ],
                "usage": {"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300},
            },
        )

    client = OpenAI(
        api_key="dummy-only",
        base_url="https://api.deepseek.com",
        max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(handle)),
    )
    return SolverService(
        Settings(provider="deepseek", api_key="dummy-only"), client=client
    ), requests


@pytest.mark.parametrize(
    "content,message",
    [
        ("   \n  ", "blank final answer"),
        ("not json sensitive-response-marker", "malformed JSON"),
        ('{"categories": []}', "JSON was readable"),
    ],
)
def test_chat_format_failures_are_specific_safe_and_never_retried(content, message):
    service, requests = chat_service(content)
    with pytest.raises(ServiceError, match=message) as error:
        service.solve(SolveRequest(words=WORDS))
    assert "sensitive-response-marker" not in str(error.value)
    assert error.value.usage.output_tokens == 200
    assert len(requests) == 1


def test_markdown_fenced_json_is_unwrapped_but_still_validated():
    payload = {"groups": [group.model_dump() for group in groups()]}
    service, requests = chat_service("```json\n" + json.dumps(payload) + "\n```")
    result = service.solve(SolveRequest(words=WORDS))
    assert result.value.groups == groups()
    prompt = json.loads(requests[0].content)["messages"][0]["content"]
    assert "Example JSON" in prompt
    assert '"confidence"' in prompt


def test_fenced_json_does_not_bypass_puzzle_validation():
    payload = {"groups": [group.model_dump() for group in groups()]}
    payload["groups"][0]["words"][0] = "INVENTED"
    service, _ = chat_service("```json\n" + json.dumps(payload) + "\n```")
    with pytest.raises(ServiceError, match="exactly once"):
        service.solve(SolveRequest(words=WORDS))
