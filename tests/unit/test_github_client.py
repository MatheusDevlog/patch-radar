from datetime import UTC, datetime
from typing import Any

import httpx
import pytest

from patch_radar.adapters.github_client import GitHubClient
from patch_radar.domain.exceptions import (
    ExternalServiceError,
    GitHubRateLimitError,
    RepositoryNotFoundError,
)


def _make_release_payload(
    *,
    tag_name: str = "v2.2.0",
    published_at: str | None = "2026-01-15T12:00:00Z",
    created_at: str = "2026-01-15T11:00:00Z",
    body: str | None = "Melhorias no renderizador Vulkan.",
    html_url: str = "https://github.com/PCSX2/pcsx2/releases/tag/v2.2.0",
    draft: bool = False,
) -> dict[str, Any]:
    return {
        "tag_name": tag_name,
        "published_at": published_at,
        "created_at": created_at,
        "body": body,
        "html_url": html_url,
        "draft": draft,
    }


def test_fetch_releases_returns_parsed_releases_and_ignores_draft() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/repos/PCSX2/pcsx2/releases"
        assert request.url.params["per_page"] == "5"
        assert request.headers["authorization"] == "Bearer secret-token"
        assert request.headers["accept"] == "application/vnd.github+json"
        return httpx.Response(
            200,
            json=[
                _make_release_payload(),
                _make_release_payload(tag_name="v2.3.0-draft", draft=True),
                _make_release_payload(
                    tag_name="v2.1.0",
                    body=None,
                    published_at=None,
                    created_at="2026-01-10T08:00:00Z",
                    html_url="https://github.com/PCSX2/pcsx2/releases/tag/v2.1.0",
                ),
            ],
        )

    client = GitHubClient(token="secret-token", transport=httpx.MockTransport(handler))

    releases = client.fetch_releases("PCSX2", "pcsx2", limit=5)

    assert len(releases) == 2
    assert releases[0].repo_name == "PCSX2/pcsx2"
    assert releases[0].tag_name == "v2.2.0"
    assert releases[0].published_at == datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
    assert releases[1].tag_name == "v2.1.0"
    assert releases[1].body == ""
    assert releases[1].published_at == datetime(2026, 1, 10, 8, 0, tzinfo=UTC)


def test_fetch_releases_raises_rate_limit_on_403_with_zero_remaining() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, headers={"X-RateLimit-Remaining": "0"})

    client = GitHubClient(transport=httpx.MockTransport(handler))

    with pytest.raises(GitHubRateLimitError):
        client.fetch_releases("PCSX2", "pcsx2")


def test_fetch_releases_omits_authorization_header_without_token() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "authorization" not in request.headers
        return httpx.Response(200, json=[])

    client = GitHubClient(transport=httpx.MockTransport(handler))

    assert client.fetch_releases("PCSX2", "pcsx2") == []


def test_fetch_releases_raises_not_found_on_404() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404)

    client = GitHubClient(transport=httpx.MockTransport(handler))

    with pytest.raises(RepositoryNotFoundError):
        client.fetch_releases("PCSX2", "nao-existe")


def test_fetch_releases_raises_rate_limit_on_429() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429)

    client = GitHubClient(transport=httpx.MockTransport(handler))

    with pytest.raises(GitHubRateLimitError):
        client.fetch_releases("PCSX2", "pcsx2")


def test_fetch_releases_raises_external_error_on_403_without_rate_limit_header() -> (
    None
):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, headers={"X-RateLimit-Remaining": "50"})

    client = GitHubClient(transport=httpx.MockTransport(handler))

    with pytest.raises(ExternalServiceError) as exc_info:
        client.fetch_releases("PCSX2", "pcsx2")

    assert not isinstance(exc_info.value, GitHubRateLimitError)


def test_fetch_releases_raises_external_error_on_server_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    client = GitHubClient(transport=httpx.MockTransport(handler))

    with pytest.raises(ExternalServiceError):
        client.fetch_releases("PCSX2", "pcsx2")


def test_fetch_releases_raises_external_error_on_network_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timeout", request=request)

    client = GitHubClient(transport=httpx.MockTransport(handler))

    with pytest.raises(ExternalServiceError):
        client.fetch_releases("PCSX2", "pcsx2")


def test_fetch_releases_raises_external_error_on_invalid_json() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html>erro</html>")

    client = GitHubClient(transport=httpx.MockTransport(handler))

    with pytest.raises(ExternalServiceError):
        client.fetch_releases("PCSX2", "pcsx2")


@pytest.mark.parametrize(
    "payload",
    [
        {"message": "formato inesperado"},
        ["item-nao-dicionario"],
        [{"tag_name": "v2.2.0"}],
    ],
)
def test_fetch_releases_raises_external_error_on_malformed_payload(
    payload: Any,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    client = GitHubClient(transport=httpx.MockTransport(handler))

    with pytest.raises(ExternalServiceError):
        client.fetch_releases("PCSX2", "pcsx2")
