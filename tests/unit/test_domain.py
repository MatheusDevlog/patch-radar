from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from patch_radar.domain.entities import (
    ChangelogAnswer,
    ChangelogChunk,
    ReleaseRaw,
    ReleaseSummary,
    Repository,
)
from patch_radar.domain.exceptions import (
    ExternalServiceError,
    GitHubRateLimitError,
    LLMResponseError,
    PatchRadarError,
    RepositoryNotFoundError,
)


def test_repository_strips_whitespace_and_builds_full_name() -> None:
    repo = Repository(owner="  PCSX2  ", name="  pcsx2  ", category="emulador")

    assert repo.owner == "PCSX2"
    assert repo.name == "pcsx2"
    assert repo.full_name == "PCSX2/pcsx2"
    assert repo.id is None
    assert repo.created_at is None


def test_repository_rejects_invalid_category() -> None:
    with pytest.raises(ValidationError):
        Repository(owner="PCSX2", name="pcsx2", category="android")


@pytest.mark.parametrize(
    ("owner", "name"),
    [("", "pcsx2"), ("   ", "pcsx2"), ("PCSX2", ""), ("PCSX2", "   ")],
)
def test_repository_rejects_blank_owner_or_name(owner: str, name: str) -> None:
    with pytest.raises(ValidationError):
        Repository(owner=owner, name=name, category="emulador")


def test_release_raw_allows_empty_body_by_default() -> None:
    release = ReleaseRaw(
        repo_name="PCSX2/pcsx2",
        tag_name="v2.2.0",
        published_at=datetime(2026, 1, 15, 12, 0, tzinfo=UTC),
        url="https://github.com/PCSX2/pcsx2/releases/tag/v2.2.0",
    )

    assert release.body == ""
    assert release.tag_name == "v2.2.0"


def test_changelog_chunk_rejects_blank_content() -> None:
    with pytest.raises(ValidationError):
        ChangelogChunk(
            chunk_id="PCSX2/pcsx2:v2.2.0:0",
            repo_name="PCSX2/pcsx2",
            tag_name="v2.2.0",
            content="   ",
            url="https://github.com/PCSX2/pcsx2/releases/tag/v2.2.0",
        )


def test_release_summary_validates_impact_level_and_defaults() -> None:
    summary = ReleaseSummary(
        repo_name="PCSX2/pcsx2",
        version="v2.2.0",
        impact_level="alto",
        summary_pt="Melhorias importantes de desempenho no Vulkan.",
    )

    assert summary.categories == []
    assert summary.highlights == []

    with pytest.raises(ValidationError):
        ReleaseSummary(
            repo_name="PCSX2/pcsx2",
            version="v2.2.0",
            impact_level="critico",
            summary_pt="Impacto inválido.",
        )


def test_changelog_answer_defaults_empty_citations() -> None:
    answer = ChangelogAnswer(
        question="Quando adicionaram suporte ao Wayland?",
        answer_pt="Não há evidência indexada sobre esse tema.",
    )

    assert answer.cited_versions == []
    assert answer.sources == []


def test_exception_hierarchy() -> None:
    assert issubclass(ExternalServiceError, PatchRadarError)
    assert issubclass(GitHubRateLimitError, ExternalServiceError)
    assert issubclass(GitHubRateLimitError, PatchRadarError)
    assert issubclass(RepositoryNotFoundError, PatchRadarError)
    assert issubclass(LLMResponseError, PatchRadarError)
