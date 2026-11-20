# Roadmap e Checklist de Execução — Patch Radar

Acompanhamento incremental das entregas do **Patch Radar**. Cada item representa um bloco verificável, validado por revisão de código e testes automatizados antes da transição para a etapa seguinte.

---

## Fase 0 — Governança, Documentação e Ambiente Dockerizado

### Etapa 0.1 — Base Documental e Repositório (Branch `main`)
- [x] Reestruturar `AGENTS.md` com diretrizes de engenharia, Clean Architecture e governança Git.
- [x] Criar especificação técnica completa em `docs/architecture.md`.
- [x] Criar checklist evolutiva em `docs/roadmap.md`.
- [x] Criar `README.md`, licença MIT (`LICENSE`) e `.gitignore`.

### Etapa 0.2 — Containerização, Empacotamento e CI Inicial
- [x] Configurar `pyproject.toml` (metadados, dependências, `ruff`, `pytest`, script `patch-radar`) e `.env.example`.
- [x] Criar `Dockerfile`, `.dockerignore` e `docker-compose.yml` (`python:3.12-slim` + `uv` em `/opt/venv`).
- [x] Criar estrutura base do pacote `src/patch_radar/` e primeiro teste smoke em `tests/`.
- [x] Configurar pipeline CI em `.github/workflows/ci.yml` (`ruff check`, `ruff format --check` e `pytest`).
- [x] Validar execução completa de `ruff` e `pytest` dentro do container e no GitHub Actions.

---

## Fase 1 — Domínio e Integrações Externas

- [ ] Implementar entidades Pydantic (`Repository`, `ReleaseRaw`, `ReleaseSummary`, `ChangelogChunk`, `ChangelogAnswer`) em `src/patch_radar/domain/entities.py`.
- [ ] Implementar exceções de domínio em `src/patch_radar/domain/exceptions.py`.
- [ ] Definir interfaces (`Protocol`) em `src/patch_radar/domain/ports.py`.
- [ ] Escrever testes unitários de domínio (`tests/unit/test_domain.py`).
- [ ] Implementar `src/patch_radar/adapters/github_client.py` com `httpx` (timeouts, tratamento de erros HTTP e rate limit) + testes unitários com mocks.
- [ ] Implementar `src/patch_radar/adapters/gemini_client.py` com `google-genai` (saída estruturada Pydantic e embeddings) + testes unitários com mocks.

---

## Fase 2 — Persistência SQL, RAG Local e Casos de Uso

- [ ] Implementar `src/patch_radar/adapters/sqlite_repository.py` (schema `repositories`/`releases`, idempotência via `UNIQUE`, consultas com `JOIN`, `WHERE` e `GROUP BY`).
- [ ] Escrever testes de integração SQLite em `:memory:` (`tests/integration/test_sqlite_repository.py`).
- [ ] Implementar `src/patch_radar/adapters/vector_store.py` (chunking determinístico e busca vetorial com ChromaDB).
- [ ] Escrever testes de integração do VectorStore (`tests/integration/test_vector_store.py`).
- [ ] Implementar casos de uso `manage_repos.py`, `check_releases.py` e `ask_changelog.py`.
- [ ] Escrever testes unitários dos casos de uso com fakes dos `Ports` (`tests/unit/test_use_cases.py`).

---

## Fase 3 — Orquestração LangGraph e Interface CLI

- [ ] Implementar `src/patch_radar/adapters/agent_graph.py` com LangGraph (`StateGraph`, estado tipado, roteamento condicional `check`/`ask` e limite de iterações).
- [ ] Escrever testes unitários/integração do grafo de estados (`tests/integration/test_agent_graph.py`).
- [ ] Implementar CLI em `src/patch_radar/interfaces/cli/main.py` (`typer` + `rich`) com comandos `add-repo`, `list-repos`, `check`, `ask` e `stats`.
- [ ] Validar execução ponta a ponta da CLI dentro do Docker.

---

## Fase 4 — Testes E2E, Robustez e Cobertura

- [ ] Implementar suíte E2E completa em `tests/e2e/` cobrindo cadastro de repositório → `check` → persistência SQLite → indexação RAG → consulta `ask` → `stats`.
- [ ] Revisar tratamento de edge cases (changelogs vazios, repositórios sem releases, duplicidade de tags, falhas parciais de API).
- [ ] Adicionar gate de cobertura mínima (`pytest-cov`) no `.github/workflows/ci.yml`.
- [ ] Atualizar `README.md` com instruções finais de uso, exemplos de saída e comandos Docker.

---

## Fase 5 — Interface Gráfica (Streamlit)

- [ ] Implementar `src/patch_radar/interfaces/ui/app.py` consumindo exclusivamente os `use_cases` e `agent_graph` (zero regra de negócio na UI).
- [ ] Disponibilizar telas de cadastro de repositórios, verificação de novidades com cards filtráveis por nível de impacto e chat RAG com citação de versões.
- [ ] Configurar serviço `ui` no `docker-compose.yml` (porta `8501`) e validar smoke tests da camada de interface.
