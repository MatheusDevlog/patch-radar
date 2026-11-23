from typing import Protocol

from patch_radar.domain.entities import (
    ChangelogAnswer,
    ChangelogChunk,
    ImpactLevel,
    ReleaseRaw,
    ReleaseSummary,
    RepoCategory,
    Repository,
)


class GitHubClientPort(Protocol):
    def fetch_releases(
        self, owner: str, name: str, limit: int = 10
    ) -> list[ReleaseRaw]: ...


class LLMClientPort(Protocol):
    def summarize_release(self, release: ReleaseRaw) -> ReleaseSummary: ...

    def answer_from_context(
        self, question: str, chunks: list[ChangelogChunk]
    ) -> ChangelogAnswer: ...


class EmbeddingClientPort(Protocol):
    def embed_texts(self, texts: list[str]) -> list[list[float]]: ...


class ReleaseRepositoryPort(Protocol):
    def add_repository(self, repository: Repository) -> Repository: ...

    def list_repositories(
        self, category: RepoCategory | None = None
    ) -> list[Repository]: ...

    def get_repository(self, owner: str, name: str) -> Repository | None: ...

    def release_exists(self, repo_id: int, tag_name: str) -> bool: ...

    def save_release(
        self, repo_id: int, release: ReleaseRaw, summary: ReleaseSummary
    ) -> None: ...

    def list_releases(
        self,
        repo_name: str | None = None,
        impact_level: ImpactLevel | None = None,
    ) -> list[ReleaseSummary]: ...

    def get_stats(self) -> dict[str, int]: ...


class VectorStorePort(Protocol):
    def index_chunks(self, chunks: list[ChangelogChunk]) -> None: ...

    def search(
        self, query: str, top_k: int = 5, repo_name: str | None = None
    ) -> list[ChangelogChunk]: ...
