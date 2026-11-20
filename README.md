# Patch Radar

Agente em Python para monitoramento automatizado de releases no GitHub (emuladores, ports nativos, drivers e ferramentas do ecossistema Linux) e consulta semântica de changelogs históricos via **RAG**.

---

## Problema e Solução

Acompanhar atualizações em múltiplos projetos open source exige visitar diversos repositórios e interpretar changelogs extensos para identificar mudanças relevantes (correções no Wayland, ganhos de performance, suporte a controles, compatibilidade com drivers).

O **Patch Radar** automatiza esse fluxo com dois modos principais:

- **Modo Radar (`check`):** consulta a GitHub Releases API para repositórios cadastrados, verifica no **SQLite** o que ainda não foi lido, resume e classifica o impacto de cada release em português usando **Google Gemini + Pydantic (Structured Outputs)** e indexa o conteúdo para buscas futuras.
- **Modo Pergunta (`ask`):** responde dúvidas sobre versões anteriores via **RAG** (busca vetorial com **ChromaDB**), citando exatamente a versão e a fonte de origem.

---

## Arquitetura

O projeto segue **Clean Architecture** (`domain`, `use_cases`, `adapters`, `interfaces`), isolando as regras de negócio de detalhes de infraestrutura (HTTP, banco de dados, LLM, banco vetorial e interface), permitindo evoluir da CLI para a interface web (Streamlit) reutilizando os mesmos casos de uso e o mesmo grafo **LangGraph**.

- Especificação detalhada, diagramas Mermaid e contratos: [`docs/architecture.md`](docs/architecture.md)
- Acompanhamento de entregas e checklist de fases: [`docs/roadmap.md`](docs/roadmap.md)
- Diretrizes de engenharia e colaboração: [`AGENTS.md`](AGENTS.md)

---

## Stack Tecnológica

- **Linguagem e Container:** Python 3.12, Docker, Docker Compose, `uv`
- **APIs e Contratos:** `httpx`, `pydantic` v2
- **IA Aplicada e Orquestração:** `google-genai` (Google Gemini), `chromadb` (RAG), `langgraph` (`StateGraph`)
- **Persistência:** SQLite (`sqlite3` com SQL explícito)
- **Interfaces:** `typer` + `rich` (CLI) e `streamlit` (UI Web — Fase 5)
- **Qualidade e CI/CD:** `pytest`, `pytest-cov`, `ruff`, GitHub Actions

---

## Execução com Docker

Todo o ambiente de desenvolvimento, testes e lint roda isolado em container:

```bash
cp .env.example .env
docker compose build
docker compose run --rm app ruff check .
docker compose run --rm app ruff format --check .
docker compose run --rm app pytest --cov=patch_radar
```

---

## Status do Projeto

Em desenvolvimento incremental por fases. Acompanhe o progresso atualizado em [`docs/roadmap.md`](docs/roadmap.md).

---

## Licença

Distribuído sob a licença **MIT**. Consulte [`LICENSE`](LICENSE) para mais detalhes.
