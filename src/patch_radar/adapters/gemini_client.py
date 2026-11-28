from typing import Any

from google import genai
from google.genai import errors, types
from pydantic import BaseModel, ValidationError

from patch_radar.domain.entities import (
    ChangelogAnswer,
    ChangelogChunk,
    ReleaseRaw,
    ReleaseSummary,
)
from patch_radar.domain.exceptions import ExternalServiceError, LLMResponseError

DEFAULT_GENERATION_MODEL = "gemini-4-hydrogen"
DEFAULT_EMBEDDING_MODEL = "gemini-embedding-2"
DEFAULT_TEMPERATURE = 0.2


class GeminiClient:
    def __init__(
        self,
        api_key: str | None = None,
        generation_model: str = DEFAULT_GENERATION_MODEL,
        embedding_model: str = DEFAULT_EMBEDDING_MODEL,
        client: Any | None = None,
    ) -> None:
        if client is not None:
            self._client = client
        elif not api_key:
            raise ValueError(
                "GEMINI_API_KEY é obrigatória quando nenhum client é injetado."
            )
        else:
            self._client = genai.Client(api_key=api_key)
        self._generation_model = generation_model
        self._embedding_model = embedding_model

    def summarize_release(self, release: ReleaseRaw) -> ReleaseSummary:
        changelog = release.body or "Sem notas de release informadas."
        prompt = (
            "Você é um engenheiro de software analisando changelogs de projetos "
            "open source.\n"
            "Resuma o release abaixo em português brasileiro, classificando o "
            "impacto como 'baixo', 'medio' ou 'alto'.\n"
            f"Repositório: {release.repo_name}\n"
            f"Versão: {release.tag_name}\n"
            f"Publicado em: {release.published_at.isoformat()}\n"
            f"Changelog:\n{changelog}"
        )
        return self._generate_structured(prompt, ReleaseSummary)

    def _generate_structured[T: BaseModel](self, prompt: str, schema: type[T]) -> T:
        config = types.GenerateContentConfig(
            temperature=DEFAULT_TEMPERATURE,
            response_mime_type="application/json",
            response_schema=schema,
        )
        try:
            response = self._client.models.generate_content(
                model=self._generation_model,
                contents=prompt,
                config=config,
            )
        except errors.APIError as exc:
            raise ExternalServiceError(
                f"Falha ao comunicar com a API do Gemini: {exc}"
            ) from exc

        parsed = getattr(response, "parsed", None)
        if isinstance(parsed, schema):
            return parsed

        raw_text = getattr(response, "text", None)
        if not raw_text:
            raise LLMResponseError(
                "O Gemini retornou uma resposta vazia ou sem conteúdo estruturado."
            )

        try:
            return schema.model_validate_json(raw_text)
        except ValidationError as exc:
            raise LLMResponseError(
                f"Resposta do Gemini fora do contrato {schema.__name__}: {exc}"
            ) from exc

    def answer_from_context(
        self, question: str, chunks: list[ChangelogChunk]
    ) -> ChangelogAnswer:
        if not chunks:
            return ChangelogAnswer(
                question=question,
                answer_pt=(
                    "Não há evidências indexadas no histórico de changelogs para "
                    "responder a esta pergunta"
                ),
                cited_versions=[],
                sources=[],
            )
        context_blocks = [
            (
                f"Repositório: {chunk.repo_name}\n"
                f"Versão: {chunk.tag_name}\n"
                f"Fonte: {chunk.url}\n"
                f"Trecho:\n{chunk.content}"
            )
            for chunk in chunks
        ]
        context = "\n\n".join(context_blocks)
        prompt = (
            "Você responde perguntas sobre changelogs usando exclusivamente "
            "as evidências abaixo. \n"
            "Responda em português brasileiro, preenchendo 'cited_versions' e "
            "'sources' com base nos trechos fornecidos.\n"
            "Se os trechos não contiverem a resposta, informe isso claramente "
            "sem inventar dados.\n"
            f"Pergunta: {question}\n\n"
            f"Evidências:\n{context}"
        )
        return self._generate_structured(prompt, ChangelogAnswer)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        try:
            response = self._client.models.embed_content(
                model=self._embedding_model,
                contents=texts,
            )
        except errors.APIError as exc:
            raise ExternalServiceError(
                f"Falha ao gerar embeddings no Gemini: {exc}"
            ) from exc

        embeddings = getattr(response, "embeddings", None)
        if not embeddings or len(embeddings) != len(texts):
            raise LLMResponseError(
                "Quantidade de embeddings retornada pelo Gemini é inválida."
            )

        vectors: list[list[float]] = []
        for item in embeddings:
            values = getattr(item, "values", None)
            if not values:
                raise LLMResponseError("Embedding vazio retornado pelo Gemini")
            vectors.append(list(values))
        return vectors
