from typing import Any

import httpx
from pydantic import ValidationError

from patch_radar.domain.entities import ReleaseRaw
from patch_radar.domain.exceptions import (
    ExternalServiceError,
    GitHubRateLimitError,
    RepositoryNotFoundError,
)

GITHUB_API_BASE_URL = "https://api.github.com"
GITHUB_API_VERSION = "2022-11-28"
DEFAULT_TIMEOUT_SECONDS = 15.0


class GitHubClient:
    def __init__(
        self,
        token: str | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        base_url: str = GITHUB_API_BASE_URL,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._token = token
        self._timeout = timeout
        self._base_url = base_url
        self._transport = transport

    def _build_headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
            "User-Agent": "patch-radar",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def fetch_releases(
        self, owner: str, name: str, limit: int = 10
    ) -> list[ReleaseRaw]:
        endpoint = f"/repos/{owner}/{name}/releases"
        try:
            with httpx.Client(
                base_url=self._base_url,
                headers=self._build_headers(),
                timeout=self._timeout,
                transport=self._transport,
            ) as client:
                response = client.get(endpoint, params={"per_page": limit})
        except httpx.HTTPError as exc:
            raise ExternalServiceError(
                f"Falha de comunicação com o GitHub para {owner}/{name}: {exc}"
            ) from exc

        self._handle_response_errors(response, owner, name)

        try:
            payload = response.json()
        except ValueError as exc:
            raise ExternalServiceError(
                f"Resposta JSON inválida do GitHub para {owner}/{name}."
            ) from exc

        return self._parse_releases(f"{owner}/{name}", payload)

    def _handle_response_errors(
        self, response: httpx.Response, owner: str, name: str
    ) -> None:
        if response.status_code == 404:
            raise RepositoryNotFoundError(
                f"Repositório não encontrado no GitHub: {owner}/{name}."
            )
        is_rate_limit = response.status_code == 429 or (
            response.status_code == 403
            and response.headers.get("X-ratelimit-remaining") == "0"
        )
        if is_rate_limit:
            raise GitHubRateLimitError(
                f"Limite de requisições da API do GitHub excedido para {owner}/{name}."
            )
        if response.status_code >= 400:
            raise ExternalServiceError(
                f"Erro HTTP {response.status_code} ao consultar GitHub para "
                f"{owner}/{name}"
            )

    def _parse_releases(self, repo_name: str, payload: Any) -> list[ReleaseRaw]:
        if not isinstance(payload, list):
            raise ExternalServiceError(
                f"Formato inesperado na resposta do GitHub para {repo_name}."
            )

        releases: list[ReleaseRaw] = []
        for item in payload:
            if not isinstance(item, dict):
                raise ExternalServiceError(
                    f"Item de release inválido recebido do GitHub para {repo_name}."
                )
            if item.get("draft"):
                continue
            releases.append(self._parse_release(repo_name, item))
        return releases

    def _parse_release(self, repo_name: str, item: dict[str, Any]) -> ReleaseRaw:
        try:
            return ReleaseRaw(
                repo_name=repo_name,
                tag_name=item["tag_name"],
                published_at=item.get("published_at") or item["created_at"],
                body=item.get("body") or "",
                url=item["html_url"],
            )
        except (KeyError, TypeError, ValidationError) as exc:
            raise ExternalServiceError(
                f"Payload de release malformado do GitHub para {repo_name}: {exc}"
            ) from exc
