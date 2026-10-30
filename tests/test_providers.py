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
def test_cloud_chat_uses_own_key_and_validated_json(provider, host):
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
    result = service.solve(SolveRequest(words=WORDS))
    assert len(result.value.groups) == 4
    assert requests[0].url.host == host
    assert requests[0].headers["authorization"] == "Bearer provider-only"
    assert result.usage.estimated_cost_usd is None
    body = json.loads(requests[0].content)
    assert body["response_format"] == {"type": "json_object"}
    assert body["max_tokens"] == 3500
    assert (
        body["reasoning_effort"] == "low"
        if provider == "kimi"
        else body["thinking"] == {"type": "disabled"}
    )


def local_service(*, remote=False, malformed=False):
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
                    "content": "{}" if malformed else json.dumps({"words": WORDS, "warning": ""})
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
