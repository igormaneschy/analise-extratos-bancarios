# Sistema de Análise de Extratos Bancários + MCP System

Este repositório contém:
- Uma aplicação Python para análise automatizada de extratos bancários (PDF, Excel e CSV)
- Um Servidor MCP autocontido (mcp_system) com indexação de código, busca híbrida (BM25 + semântica), empacotamento de contexto e memória de sessões

## Quick start

- Requisitos gerais: Python 3.11+
- MCP: requer a biblioteca FastMCP instalada no ambiente do servidor

Aplicação (CLI) de análise:
- Execute os testes ou comandos conforme sua automação local.

Servidor MCP:
- O servidor MCP é carregado como módulo Python: `mcp_system.mcp_server_enhanced`
- O cliente MCP/host é responsável por inicializar o servidor; durante o startup você deverá ver logs no stderr, por exemplo:
  - `[mcp_server_enhanced] 🚀 Iniciando indexação automática inicial...`
  - `[mcp_server_enhanced] ✅ Indexação inicial concluída`
  - `[mcp_server_enhanced] 🧠 Memory DB em uso: <...>/mcp_system/.mcp_memory/memory.db`

## Arquitetura e auto-contenção do MCP

Todos os artefatos do servidor MCP ficam dentro da pasta `mcp_system` por padrão:
- `mcp_system/.mcp_index/` — índices e métricas (ex.: `metrics_index.csv`, `metrics_context.csv`)
- `mcp_system/.mcp_memory/` — memória (SQLite) contendo a tabela `session_summaries`
- `mcp_system/.emb_cache/` — cache de embeddings/modelos (quando aplicável)

Mecanismos de proteção:
- O indexador ignora por padrão (`DEFAULT_EXCLUDE`): `**/.mcp_index/**`, `**/.mcp_memory/**`, `**/.emb_cache/**`, além de diretórios comuns (`.git`, `node_modules`, `dist`, `build`, `.venv`, `__pycache__`)
- O file watcher também filtra eventos provenientes desses diretórios internos para evitar reindexação de artefatos do próprio servidor

## Variáveis de ambiente (MCP)

- `INDEX_ROOT` (default: diretório pai de `mcp_system`)
  - Raiz do projeto a ser indexado. Não precisa ficar dentro de `mcp_system`; apenas os artefatos do servidor ficam.
- `INDEX_DIR` (default: `mcp_system/.mcp_index`)
  - Onde ficam os índices e métricas.
- `EMBEDDINGS_CACHE_DIR` (default: `mcp_system/.emb_cache`)
  - Diretório de cache para modelos (HuggingFace/Sentence-Transformers). O servidor também ajusta `SENTENCE_TRANSFORMERS_HOME`, `HF_HOME`, `HUGGINGFACE_HUB_CACHE` quando esse diretório é usado.
- `AUTO_INDEX_ON_START` (default: `1`)
  - Indexar automaticamente no startup.
- `AUTO_INDEX_PATHS` (default: `.`)
  - Caminhos (separados por `os.pathsep`) relativos a `INDEX_ROOT` a serem indexados no startup.
- `AUTO_INDEX_RECURSIVE` (default: `1`)
  - Indexação recursiva.
- `AUTO_ENABLE_SEMANTIC` (default: `1`)
  - Ativa re-rank semântico na busca (quando disponível).
- `AUTO_START_WATCHER` (default: `1`)
  - Inicia o file watcher após indexação.
- `MEMORY_DIR` (opcional)
  - Se definido, ajusta o diretório da memória. Pode ser relativo a `mcp_system` ou absoluto. Padrão é `mcp_system/.mcp_memory`.

## Inicialização e logs (MCP)

Fluxo no startup do servidor MCP:
1) Indexação automática (se habilitada)
2) Inicialização da memória (se disponível) e registro de um resumo da indexação inicial
3) Início do watcher (se habilitado)

Logs esperados:
- Disponibilidade da memória:
  - `[mcp_server_enhanced] 🧠 MemoryStore disponível`
  - ou (quando executado em contexto de pacote): `🧠 MemoryStore disponível (import relativo)`
  - em falhas: `⚠️ MemoryStore indisponível: abs=...; rel=...`
- Caminho do DB:
  - `[mcp_server_enhanced] 🧠 Memory DB em uso: <...>/mcp_system/.mcp_memory/memory.db`

## Ferramentas MCP expostas

- `index_path` — Indexa um caminho
- `search_code` — Busca híbrida (BM25 + semântica quando disponível)
- `context_pack` — Cria pacote de contexto com trechos relevantes
- `auto_index` — Controla sistema de auto-indexação (start/stop/status)
- `get_stats` — Estatísticas do indexador
- `cache_management` — Gerencia caches (ex.: limpar cache de embeddings)
- `where_we_stopped` — Resumo de últimos passos, próximos passos, bloqueios e pistas

## Scripts utilitários (MCP)

Executando via módulo Python:

- Listar estatísticas:
  - `python -m mcp_system.scripts.get_stats`
- Resumir métricas (lê CSVs dentro de `mcp_system/.mcp_index`):
  - `python -m mcp_system.scripts.summarize_metrics`
- Visualizar métricas (quando aplicável):
  - `python -m mcp_system.scripts.visual_metrics`
- Dump da memória (sem sqlite3 CLI):
  - JSON: `python -m mcp_system.scripts.memory_dump --limit 20`
  - Tabela: `python -m mcp_system.scripts.memory_dump --limit 20 --table`
  - Filtros: `--project`, `--scope`, `--contains`
  - Diretório alternativo de memória: `--memory-dir <path>`

## Resolução de problemas

- Não aparece o log do DB de memória
  - Verifique se há log de disponibilidade do MemoryStore
  - Se indisponível: confirme dependências do Python e que o módulo `mcp_system` está acessível (o servidor tenta import absoluto e relativo)
- Erro no watcher
  - Confirme que diretórios internos (`.mcp_index`, `.mcp_memory`, `.emb_cache`) estão sendo filtrados
- Busca semântica inativa
  - O servidor funciona com BM25 puro; a reordenação semântica é ativada quando bibliotecas de embeddings estão disponíveis

## Sobre a aplicação de análise de extratos

A aplicação extrai e analisa transações de PDF/Excel/CSV, calcula saldos e pode categorizar gastos. Consulte os testes e exemplos em `data/samples` para uso básico.
