from datetime import UTC, datetime
from typing import Any

import pytest
from google.genai import errors

from patch_radar.adapters.gemini_client import (
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_GENERATION_MODEL,
    GeminiClient,
)
from patch_radar.domain.entities import (
    ChangelogAnswer,
    ChangelogChunk,
    ReleaseRaw,
    ReleaseSummary,
)
from patch_radar.domain.exceptions import ExternalServiceError, LLMResponseError


class _FakeResponse:
    def __init__(self, *, parsed: Any = None, text: str | None = None) -> None:
        self.parsed = parsed
        self.text = text


class _FakeEmbeddingItem:
    def __init__(self, values: list[float] | None) -> None:
        self.values = values


class _FakeEmbedResponse:
    def __init__(self, embeddings: list[_FakeEmbeddingItem] | None) -> None:
        self.embeddings = embeddings


class _FakeModels:
    def __init__(
        self,
        *,
        generate_response: Any = None,
        embed_response: Any = None,
        error: Exception | None = None,
    ) -> None:
        self._generate_response = generate_response
        self._embed_response = embed_response
        self._error = error
        self.generate_calls: list[dict[str, Any]] = []
        self.embed_calls: list[dict[str, Any]] = []

    def generate_content(self, **kwargs: Any) -> Any:
        self.generate_calls.append(kwargs)
        if self._error is not None:
            raise self._error
        return self._generate_response

    def embed_content(self, **kwargs: Any) -> Any:
        self.embed_calls.append(kwargs)
        if self._error is not None:
            raise self._error
        return self._embed_response


class _FakeGenAIClient:
    def __init__(self, models: _FakeModels) -> None:
        self.models = models


def _make_release() -> ReleaseRaw:
    return ReleaseRaw(
        repo_name="PCSX2/pcsx2",
        tag_name="v2.2.0",
        published_at=datetime(2026, 1, 15, 12, 0, tzinfo=UTC),
        body="Improved Vulkan renderer and DualSense support.",
        url="https://github.com/PCSX2/pcsx2/releases/tag/v2.2.0",
    )


def _make_chunk() -> ChangelogChunk:
    return ChangelogChunk(
        chunk_id="PCSX2/pcsx2:v2.2.0:0",
        repo_name="PCSX2/pcsx2",
        tag_name="v2.2.0",
        content="Improved Vulkan renderer and DualSense support.",
        url="https://github.com/PCSX2/pcsx2/releases/tag/v2.2.0",
    )


def test_summarize_release_returns_parsed_summary() -> None:
    expected = ReleaseSummary(
        repo_name="PCSX2/pcsx2",
        version="v2.2.0",
        impact_level="alto",
        categories=["Vulkan", "Controles"],
        summary_pt="Melhorias importantes no Vulkan e suporte a DualSense.",
        highlights=["Renderizador Vulkan otimizado"],
    )
    models = _FakeModels(generate_response=_FakeResponse(parsed=expected))
    client = GeminiClient(client=_FakeGenAIClient(models))

    result = client.summarize_release(_make_release())

    assert result == expected
    assert len(models.generate_calls) == 1
    assert models.generate_calls[0]["model"] == DEFAULT_GENERATION_MODEL
    assert models.generate_calls[0]["config"].response_schema is ReleaseSummary


def test_answer_from_context_returns_no_evidence_without_calling_api() -> None:
    models = _FakeModels()
    client = GeminiClient(client=_FakeGenAIClient(models))

    result = client.answer_from_context("Quando corrigiram Vulkan?", [])

    assert result.question == "Quando corrigiram Vulkan?"
    assert result.cited_versions == []
    assert result.sources == []
    assert models.generate_calls == []


def test_init_raises_value_error_without_api_key_or_client() -> None:
    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        GeminiClient()


def test_init_creates_genai_client_with_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_client_factory(*, api_key: str) -> _FakeGenAIClient:
        captured["api_key"] = api_key
        return _FakeGenAIClient(_FakeModels())

    monkeypatch.setattr(
        "patch_radar.adapters.gemini_client.genai.Client",
        fake_client_factory,
    )

    GeminiClient(api_key="test-key")

    assert captured["api_key"] == "test-key"


def test_summarize_release_falls_back_to_validating_json_text() -> None:
    expected = ReleaseSummary(
        repo_name="PCSX2/pcsx2",
        version="v2.2.0",
        impact_level="medio",
        categories=["Linux"],
        summary_pt="Correções de compatibilidade no Linux.",
        highlights=["Ajuste no Wayland"],
    )
    models = _FakeModels(
        generate_response=_FakeResponse(text=expected.model_dump_json())
    )
    client = GeminiClient(client=_FakeGenAIClient(models))

    result = client.summarize_release(_make_release())

    assert result == expected


def test_summarize_release_raises_llm_error_on_empty_response() -> None:
    models = _FakeModels(generate_response=_FakeResponse(parsed=None, text=""))
    client = GeminiClient(client=_FakeGenAIClient(models))

    with pytest.raises(LLMResponseError):
        client.summarize_release(_make_release())


def test_summarize_release_raises_llm_error_on_invalid_json() -> None:
    models = _FakeModels(generate_response=_FakeResponse(text='{"invalido": true}'))
    client = GeminiClient(client=_FakeGenAIClient(models))

    with pytest.raises(LLMResponseError):
        client.summarize_release(_make_release())


def test_summarize_release_raises_external_error_on_api_error() -> None:
    api_error = errors.APIError(503, {"error": {"message": "service unavailable"}})
    models = _FakeModels(error=api_error)
    client = GeminiClient(client=_FakeGenAIClient(models))

    with pytest.raises(ExternalServiceError):
        client.summarize_release(_make_release())


def test_answer_from_context_sends_chunks_and_returns_structured_answer() -> None:
    expected = ChangelogAnswer(
        question="Quando melhoraram o Vulkan?",
        answer_pt="O renderizador Vulkan foi otimizado na versão v2.2.0.",
        cited_versions=["v2.2.0"],
        sources=["https://github.com/PCSX2/pcsx2/releases/tag/v2.2.0"],
    )
    models = _FakeModels(generate_response=_FakeResponse(parsed=expected))
    client = GeminiClient(client=_FakeGenAIClient(models))

    result = client.answer_from_context("Quando melhoraram o Vulkan?", [_make_chunk()])

    assert result == expected
    assert len(models.generate_calls) == 1
    sent_prompt = models.generate_calls[0]["contents"]
    assert "PCSX2/pcsx2" in sent_prompt
    assert "v2.2.0" in sent_prompt
    assert models.generate_calls[0]["config"].response_schema is ChangelogAnswer


def test_embed_texts_returns_empty_list_without_calling_api() -> None:
    models = _FakeModels()
    client = GeminiClient(client=_FakeGenAIClient(models))

    assert client.embed_texts([]) == []
    assert models.embed_calls == []


def test_embed_texts_returns_vectors_for_each_text() -> None:
    embed_response = _FakeEmbedResponse(
        embeddings=[
            _FakeEmbeddingItem([0.1, 0.2]),
            _FakeEmbeddingItem([0.3, 0.4]),
        ]
    )
    models = _FakeModels(embed_response=embed_response)
    client = GeminiClient(client=_FakeGenAIClient(models))

    vectors = client.embed_texts(["Vulkan fix", "DualSense support"])

    assert vectors == [[0.1, 0.2], [0.3, 0.4]]
    assert len(models.embed_calls) == 1
    assert models.embed_calls[0]["model"] == DEFAULT_EMBEDDING_MODEL
    assert models.embed_calls[0]["contents"] == ["Vulkan fix", "DualSense support"]


def test_embed_texts_raises_external_error_on_api_error() -> None:
    api_error = errors.APIError(429, {"error": {"message": "quota exceeded"}})
    models = _FakeModels(error=api_error)
    client = GeminiClient(client=_FakeGenAIClient(models))

    with pytest.raises(ExternalServiceError):
        client.embed_texts(["Vulkan fix"])


def test_embed_texts_raises_llm_error_on_mismatched_embedding_count() -> None:
    embed_response = _FakeEmbedResponse(embeddings=[_FakeEmbeddingItem([0.1, 0.2])])
    models = _FakeModels(embed_response=embed_response)
    client = GeminiClient(client=_FakeGenAIClient(models))

    with pytest.raises(LLMResponseError):
        client.embed_texts(["texto 1", "texto 2"])


def test_embed_texts_raises_llm_error_on_empty_embedding_values() -> None:
    embed_response = _FakeEmbedResponse(embeddings=[_FakeEmbeddingItem([])])
    models = _FakeModels(embed_response=embed_response)
    client = GeminiClient(client=_FakeGenAIClient(models))

    with pytest.raises(LLMResponseError):
        client.embed_texts(["texto 1"])
