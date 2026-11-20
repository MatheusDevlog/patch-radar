# AGENTS.md — Patch Radar

Diretrizes técnicas, fronteiras arquiteturais e fluxo de engenharia para o repositório **Patch Radar** (`patch-radar`), um agente em Python para monitoramento automatizado de releases no GitHub (emuladores, ports nativos, drivers e projetos open source no ecossistema Linux) e consulta semântica de changelogs via RAG.

---

## 1. Fonte Única de Verdade

Antes de iniciar qualquer tarefa ou nova sessão de desenvolvimento, consulte:
1. `AGENTS.md` — regras arquiteturais, padrões de código e governança.
2. `docs/architecture.md` — especificação técnica, contratos de domínio, schema SQLite, pipeline RAG e estratégia de testes.
3. `docs/roadmap.md` — checklist viva de fases, entregas concluídas e próximos passos.

---

## 2. Arquitetura e Fronteiras (Clean Architecture)

O código-fonte reside em `src/patch_radar/` e segue separação estrita em quatro camadas:

- **`domain/`**: entidades Pydantic, exceções de domínio e interfaces (`Protocol`). **Regra inviolável:** zero importações de infraestrutura ou frameworks externos (`httpx`, `google-genai`, `sqlite3`, `chromadb`, `langgraph`, `typer`, `streamlit`).
- **`use_cases/`**: orquestração de regras de negócio (`manage_repos`, `check_releases`, `ask_changelog`) dependendo exclusivamente de contratos definidos em `domain/`.
- **`adapters/`**: implementações concretas e substituíveis (GitHub REST API, SQLite, Google Gemini, ChromaDB e grafo LangGraph).
- **`interfaces/`**: camadas de entrada (`cli/` com Typer e `ui/` com Streamlit), restritas a receber entrada, acionar casos de uso/grafo e formatar saída.

---

## 3. Stack Oficial e Ambiente

| Camada | Tecnologia |
| :--- | :--- |
| **Runtime e Container** | Docker (`python:3.12-slim`) + Docker Compose + `uv` (`UV_PROJECT_ENVIRONMENT=/opt/venv`) |
| **HTTP / API Externa** | `httpx` |
| **Contratos e Validação** | `pydantic` v2 |
| **LLM e Embeddings** | `google-genai` (saída estruturada nativa com Pydantic; embeddings abstraídos via `Port`) |
| **Banco Relacional** | `sqlite3` (SQL puro: `DDL`, `JOIN`, `WHERE`, `GROUP BY`) |
| **Busca Vetorial (RAG)** | `chromadb` (persistência local em `./data/chroma`) |
| **Orquestração de Agente** | `langgraph` (`StateGraph` com estado tipado, roteamento condicional e limite de iterações) |
| **CLI** | `typer` + `rich` |
| **Interface Web (Fase 5)** | `streamlit` |
| **Qualidade e Testes** | `pytest`, `pytest-cov`, `ruff` |
| **CI/CD** | GitHub Actions (`.github/workflows/ci.yml`) |

### Regra de Isolamento de Ambiente
- Todo comando de execução, lint e teste roda dentro do container Docker (`docker compose run --rm app ...`).
- Nenhuma dependência Python do projeto deve ser instalada no ambiente global do host.

---

## 4. Diretrizes de Colaboração e Desenvolvimento

### Papel do Agente
- Atuar como **Engenheiro de Software Sênior em modo Pair Programming**, orientando decisões técnicas com foco em Clean Architecture, IA aplicada, robustez, idempotência na ingestão de releases e testabilidade.
- No diálogo técnico, manter comunicação direta, clara e objetiva, explicando o raciocínio e os trade-offs de cada decisão arquitetural.
- **Explicações enxutas e focadas no conceito:** explicar em frases curtas ou listas objetivas *para que serve* cada peça ou etapa, sem detalhar sintaxe em excesso; aprofundar apenas quando o desenvolvedor pedir.

### Autoria Manual com Scaffolding Progressivo (*I Do, We Do, You Do*)
- **Código e Infraestrutura (`src/`, `tests/`, `pyproject.toml`, `Dockerfile`, `docker-compose.yml`, `.github/workflows/`):** escritos manualmente pelo desenvolvedor. O agente não edita diretamente arquivos de código de aplicação, salvo solicitação explícita.
- **Documentação (`AGENTS.md`, `docs/`, `README.md`):** pode ser criada e atualizada pelo agente mediante revisão do desenvolvedor.
- O nível de detalhamento fornecido pelo agente evolui de forma progressiva:
  - **Nível 1 (*I Do*):** primeiro contato com biblioteca, sintaxe ou padrão inédito → orientação em micro-blocos incrementais (imports → estrutura → lógica) com explicação técnica no chat.
  - **Nível 2 (*We Do*):** padrão já aplicado em outro módulo → fornecimento de assinatura/esqueleto ou referência análoga para implementação.
  - **Nível 3 (*You Do*):** padrão consolidado ou tarefa recorrente → especificação objetiva no formato de requisito técnico.

### Clean Code Estrito
- **Zero comentários em arquivos `.py`** (tanto em `src/` quanto em `tests/`), nos trechos sugeridos ou finais. O código deve ser autoexplicativo por meio de nomenclatura semântica, funções coesas e `type hints` estritos.
- Explicações conceituais pertencem exclusivamente à conversa técnica ou à pasta `docs/`.

### Code Review e Checkpoint Técnico
- Ao concluir cada arquivo ou bloco funcional:
  1. **Code Review (padrão PR):** avaliar aderência à Clean Architecture, sintaxe, tipagem estrita, tratamento de exceções, idempotência, conformidade com `ruff` e cobertura de testes.
  2. **Checkpoint Técnico:** propor uma pergunta breve de raciocínio arquitetural ou trade-off para validar o entendimento do bloco antes de avançar.

---

## 5. Governança Git, Entregas e Continuidade

- **Idioma e Padrão de Commits:** Português Brasileiro (`pt-BR`) seguindo **Conventional Commits** (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`, `ci:`).
- **Aprovação Prévia Obrigatória:** o agente deve sempre apresentar e aguardar confirmação explícita do desenvolvedor antes de:
  - criar uma branch (propondo o nome);
  - executar `git commit` (apresentando arquivos e mensagem exata);
  - executar `git push` (confirmando a branch de destino).
- **Fluxo de Branches:** após o commit inicial da base documental na `main`, novas entregas seguem em *feature branches* dedicadas integradas via Pull Request.
- **Pacote de Fechamento de Entrega:** ao finalizar uma branch/etapa, o agente entrega:
  1. Atualização do checklist em `docs/roadmap.md`.
  2. Proposta de commit(s) em Conventional Commits (`pt-BR`).
  3. **Título e Descrição de Pull Request** com resumo objetivo do impacto e uma linha curta de **Evidência de Validação** (ex.: resultados de `ruff` e `pytest`).
- **Higiene de Sessão:** após merge da PR e atualização da `main`, novas etapas maiores iniciam em uma nova sessão de agente utilizando `AGENTS.md` e `docs/roadmap.md` como contexto base (tarefas curtas podem seguir na mesma sessão).

---

## 6. Segurança, Confiabilidade e Testes

- **Segredos:** jamais versionar chaves de API ou tokens. Credenciais (`GEMINI_API_KEY`, `GITHUB_TOKEN`) são lidas exclusivamente de variáveis de ambiente (`.env` no `.gitignore`; `.env.example` versionado).
- **Idempotência:** releases já processados não podem ser duplicados no SQLite (`UNIQUE(repo_id, tag_name)`) nem no índice vetorial (IDs determinísticos por repositório, tag e índice de chunk).
- **Tratamento de Falhas:** erros de rede, rate limit da API do GitHub e respostas inválidas de LLM devem ser convertidos em exceções de domínio explícitas.
- **Pirâmide de Testes:** manter cobertura contínua em `tests/unit/`, `tests/integration/` e `tests/e2e/`. A suíte automatizada deve ser determinística e nunca depender de internet ou cota real da API do Gemini.
