[2025-09-07] - Assistant
Arquivos: mcp_system/mcp_server_enhanced.py
Ação/Tipo: Correção
Descrição: Corrige parêntese não fechado e valor padrão na atribuição do modelo em _apply_budget_to_pack.
Detalhes:
Problema: Erro de sintaxe causado por parêntese não fechado em chamada a os.getenv dentro de _apply_budget_to_pack, levando a SyntaxError e falha no parse do módulo.
Causa: Linha truncada durante edição anterior que removeu o fechamento do parêntese e o valor padrão.
Solução: Fecha o parêntese e adiciona valor padrão "gpt-4o" em os.getenv("MCP_DEFAULT_MODEL", "gpt-4o"). Também revisei o bloco para garantir que a função retorne o pack mesmo em erro.
Observações: Correção sintática simples; recomendo rodar a suíte de testes para validar efeitos colaterais.

[2025-09-06] - Assistant
Arquivos: mcp_system/mcp_server_enhanced.py
Ação/Tipo: Correção
Descrição: Substitui chamadas a __update_metrics_from_pack por _update_metrics_from_pack para evitar NameError.
Detalhes:
Problema: NameError em __update_metrics_from_pack após unificação de função.
Causa: Call sites ainda usavam o nome antigo.
Solução: Troca das chamadas nas branches de cache e normal em _handle_context_pack.
Observações: Sem mudança de comportamento, apenas correção de referência.
        
[2025-09-06] - Assistant
Arquivos: mcp_system/mcp_server_enhanced.py
Ação/Tipo: Correção
Descrição: Corrige inicialização preguiçosa do MemoryStore para usar db_path canonizado (MCP_DATA_DIR/.mcp_memory/session_store.sqlite3) e unifica função de métricas.
Detalhes:
Problema: Em cenários de fallback, MemoryStore podia ser criado com argumento incorreto (Path como db_path), resultando em instância "muda" e perda de registros.
Causa: _get_memory usava MemoryStore(root) em vez de um caminho de DB; duplicidade de __update_metrics_from_pack e _update_metrics_from_pack.
Solução: Passar db_path explícito derivado de MCP_DATA_DIR; criar alias de __update_metrics_from_pack -> _update_metrics_from_pack para um único ponto de atualização.
Observações: Sem alterações de API; apenas robustez e consistência de gravação.

[2025-09-02] - Assistant
Arquivos: mcp_system/scripts/get_stats.py
Ação/Tipo: Melhoria
Descrição: Adiciona suporte a --data-dir, imprime o caminho do DB do MemoryStore e do metrics_context.csv para diagnosticar origem das métricas.
Detalhes:
Problema: Métricas de uso de LLM apareciam baixas por leitura de diretórios/arquivos diferentes dos usados pelo servidor.
Causa: Divergência entre MCP_DATA_DIR do servidor e do script; ausência de logs de paths.
Solução: Novo argumento --data-dir que sobrescreve MCP_DATA_DIR; impressão do DB do MemoryStore e do caminho do metrics_context.csv no fallback.
Observações: Mudança de observabilidade apenas; não afeta lógica de coleta.

[2025-09-05] - Assistant
Arquivos: tests/unit/test_domain_interfaces.py, src/domain/interfaces.py
Ação/Tipo: Teste
Descrição: Adiciona testes abrangentes para todas as interfaces do domínio, melhorando a cobertura de testes do projeto.
Detalhes:
Problema: Baixa cobertura de testes para as interfaces do domínio (78%)
Causa: Falta de testes específicos para as interfaces abstratas e suas implementações
Solução: Criação de um novo arquivo de teste que verifica a estrutura das interfaces abstratas e testa implementações concretas, aumentando a cobertura geral do projeto para 90%
Observações: Foram criadas implementações de teste para cada interface a fim de garantir que todos os métodos sejam cobertos, e foram adicionados testes para verificar se as implementações concretas herdam corretamente das interfaces


[2025-09-05] - Assistant
Arquivos: mcp_system/mcp_server_enhanced.py
Ação/Tipo: Melhoria
Descrição: Habilita persistência de caches (search e embeddings) usando MCP_DATA_DIR ou .mcp_data por padrão; define persist_path e limites de tamanho (max_size) para reduzir volatilidade entre reinícios.
Detalhes:
Problema: Caches em memória eram voláteis entre reinícios, dificultando continuidade de hits/evictions.
Causa: get_cache era usado sem persist_path por padrão.
Solução: Ao importar get_cache, o servidor agora calcula DATA_DIR (MCP_DATA_DIR ou .mcp_data), cria o diretório e inicializa _search_cache e _emb_cache com persist_path apontando para arquivos JSON dentro de DATA_DIR e com max_size sensível.
Observações: Persistência é best-effort (DeterministicCache salva JSON); se persistência falhar, cache continua funcionando em memória. Testes locais recomendados para verificar arquivos search_cache.json / emb_cache.json.

[2025-09-05] - Assistant
Arquivos: mcp_system/mcp_server_enhanced.py
Ação/Tipo: Melhoria
Descrição: Adiciona logs verbosos no bootstrap do MemoryStore para registrar o caminho do DB e a contagem inicial de session summaries.
Detalhes:
Problema: Nem sempre era claro qual DB estava sendo usado nem quantos resumos já existiam no startup, dificultando diagnóstico.
Causa: O bootstrap inicial apenas criava a instância sem registrar métricas iniciais além do path.
Solução: Após instanciar MemoryStore durante o bootstrap, faz chamada segura a get_memory_store_stats(store) e loga session_summaries_count (INFO). Falhas na coleta de estatísticas são capturadas e logadas como warnings, sem interromper o startup.
Observações: Mudança de observabilidade somente; não afetou a lógica de persistência.

[2025-09-02] - Assistant
Arquivos: mcp_system/mcp_server_enhanced.py
Ação/Tipo: Melhoria
Descrição: Registra available inicial (binfo['available']) antes do truncamento dos snippets para diagnóstico de decisões de budget.
Detalhes:
Problema: Dificuldade em diagnosticar por que snippets eram truncados ou removidos, uma vez que apenas o "available_after" era logado.
Causa: O log anterior registrava apenas o available remanescente após truncamento, ocultando o valor inicial estimado que orientou as decisões de corte.
Solução: Adiciona logging de available_initial e inclui available_initial em pack['budget_info']; melhora a linha de debug para exibir available_initial e available_after.
Observações: Melhoria de observabilidade não altera lógica de truncamento; útil para tuning e troubleshooting.

[2025-09-04] - Assistant
Arquivos: mcp_system/memory_store.py
Ação/Tipo: Melhoria
Descrição: Adiciona TTLs por namespace, LRU com limite de tamanho e persistência opcional; expõe reset_metrics() no cache.
Detalhes:
Problema: Caches anteriores não suportavam TTLs por namespace, não tinham controle de tamanho nem métricas resetáveis.
Causa: Implementação inicial do cache era simples e sem opções de produção (persistência/LRU/metrics management).
Solução:
- Introduz DEFAULT_TTLS e mapeamento de TTLs por namespace (search, embeddings, metadata, context).
- Implementa DeterministicCache com suporte a max_size (LRU eviction), persist_path (salva/carrega JSON) e default_ttl por namespace.
- Adiciona método reset_metrics() que zera e retorna os counters anteriores.
- Atualiza get_cache(name, max_size=None, persist_path=None, default_ttl=None) para criar caches configuráveis por namespace.
Observações: Persistência é "best-effort" (JSON) e ignora valores não-serializáveis; LRU é baseado em OrderedDict e evicções incrementam contador _evictions.

[2025-09-01] - Assistant
Arquivos: mcp_validation_suite/adapter.py
Ação/Tipo: Melhoria
Descrição: Consolida métricas MCP no adapter e remove duplicidades, melhorando observabilidade sem alterar API externa.
Detalhes:
Problema: Duplicidade de get_stats, cálculo de hit-rate de queries inconsistente e cold_start_ms não persistido nas métricas.
Causa: Código duplicado e retorno antecipado em search; ausência de persistência explícita de cold_start_ms.
Solução: Unificação de get_stats com bloco mcp_metrics, cálculo de query_hit antes do retorno, normalização de _cache_hits (inclui packs_total) e persistência de cold_start_ms em _metrics.
Observações: Compatível com a suíte atual; não expõe dados sensíveis.

[2025-09-01] - Assistant
Arquivos: mcp_system/README.md
Ação/Tipo: Documentação
Descrição: Reescreve README consolidando conteúdo do "README 2.md" com foco em produção e sem referências à suíte de validação.
Detalhes:
Problema: README fragmentado entre dois arquivos e com referências a artefatos de desenvolvimento.
Causa: Evolução incremental da documentação em múltiplos arquivos.
Solução: Documento único com funcionalidades, requisitos, execução, variáveis, tools, observabilidade, memória, scripts, proteções e troubleshooting; removidas referências à suíte de validação.
Observações: "README 2.md" mantido como fonte histórica; README principal agora é fonte de verdade.

[2025-09-01] - Assistant
Arquivos: mcp_system/code_indexer_enhanced.py
Ação/Tipo: Correção
Descrição: Corrige index_files para inicializar variáveis, executar indexação base e garantir index_dir serializável.
Detalhes:
Problema: Variáveis não inicializadas (result/pre_map/meta_path) e PosixPath não serializável no report causavam falhas.
Causa: Referências a variáveis antes da atribuição e retorno de Path em index_dir; bloco duplicado causava erro de sintaxe.
Solução: Adicionados pre_map/meta_path; chamada a index_repo_paths; ajuste de t_index_end; enriquecimento de result com métricas; index_dir convertido para string em sucesso/erro; remoção de bloco duplicado.
Observações: Suíte de validação executou com sucesso após a correção.

[2025-09-01] - Assistant
Arquivos: mcp_validation_suite/adapter.py
Ação/Tipo: Melhoria
Descrição: Fallback de index_dir no last_index, cold_start_ms real no warmup, economia de tokens no pack e métricas de tokens expostas.
Detalhes:
Problema: index_dir vazio no last_index; cold_start_ms medido sem carregar backend; pack não limitava previews; métricas de tokens não atualizadas.
Causa: Adapter não aplicava fallback e não forçava embed mínima; previews não recortadas; métricas não persistidas.
Solução: warmup acrescenta fallback de index_dir e força _call_hybrid_search para cold start; cálculo de embeddings_hit usa total de chunks; pack_context atualiza prompt_tokens_last/completion_tokens_last e permite recorte de previews (800 chars) para melhor orçamento.
Observações: Valores de cold_start podem variar por ambiente; limite de preview pode ser ajustado conforme necessidade.

[2025-09-01] - Assistant
Arquivos: mcp_validation_suite/adapter.py
Ação/Tipo: Melhoria
Descrição: Exposição de updated_* e métricas de fase de index em warmup/index_repo e inclusão de index_ms em get_stats.
Detalhes:
Problema: last_index não refletia delta e fases da indexação; cache.embeddings_hit não era ajustado.
Causa: adapter não propagava campos retornados pelo indexador.
Solução: warmup/index_repo atualizam updated_files/updated_chunks, index_discovery_ms/index_embed_ms e embeddings_hit (ratio). get_stats passa a retornar index_ms.
Observações: Compatível com a suíte; métrica embeddings_hit é aproximada ao nível de arquivo.

[2025-09-01] - Assistant
Arquivos: mcp_system/code_indexer_enhanced.py, mcp_validation_suite/adapter.py
Ação/Tipo: Melhoria
Descrição: Implementa delta incremental e métricas por fase no indexador; adiciona tiktoken e cold_start no adapter.
Detalhes:
Problema: Indexação não reportava updated_* reais nem métricas de descoberta/embedding; contagem de tokens heurística.
Causa: Ausência de assinatura por arquivo/chunk e medições por fase; falta integração de tiktoken no adapter.
Solução: Snapshot de assinaturas pré/pós para delta; persistência em index_meta.json; métricas index_discovery_ms/index_embed_ms/embeddings_hit; no adapter, contagem via tiktoken (fallback) e cold_start_ms.
Observações: Mantida compatibilidade com a suíte MCP e com a API existente.

[2025-09-01] - Assistant
Arquivos: mcp_validation_suite/adapter.py
Ação/Tipo: Refatoração
Descrição: Reescreve adapter com fallback BM25 leve, mapeamento correto de chunk_data e get_stats implementado.
Detalhes:
Problema: Falhas na chamada de hybrid_search por parâmetros ausentes/estruturas incorretas e ausência de get_stats.
Causa: Diferença entre contratos esperados pelo engine e dados do indexador; lacuna de métricas.
Solução: Implementação de _bm25_fallback, normalização consistente de chunks, aliases de top-k e função get_stats com p50/p95.
Observações: Compatível com checks de indexação, observabilidade e orçamento de contexto.

[2025-09-01] - Assistant
Arquivos: mcp_validation_suite/adapter.py
Ação/Tipo: Melhoria
Descrição: Ajusta adapter da suíte MCP para compatibilidade com EnhancedCodeIndexer e adiciona get_stats.
Detalhes:
Problema: Adapter inicial usava parâmetro incorreto (cache_dir) no EnhancedCodeIndexer e não expunha métricas via get_stats.
Causa: Divergência entre a API esperada e a implementação real do indexador/buscador.
Solução: Inicialização corrigida com index_dir e repo_root; normalização de candidatos incluindo file_path/combined_score; implementação de get_stats com p50/p95 e hit-rate de cache.
Observações: Warmup indexa mcp_system por padrão; compatível com checks de latência, cache e orçamento de contexto.

[2025-08-31] - Assistant
Arquivos: src/infrastructure/readers/excel_reader.py
Ação/Tipo: Correção
Descrição: Tornar leitura de Excel (BPI) mais robusta com detecção de cabeçalho e busca tolerante de colunas; suporte a Crédito/Débito separados.
Detalhes:
Problema: Teste de CLI para Excel falhava (ParsingError) por não identificar colunas devido a cabeçalhos deslocados e variações de nomes.
Causa: Leitura usando header fixo e busca estrita por igualdade nos nomes das colunas; planilhas do BPI trazem preâmbulo e colunas "Crédito/Débito" separadas.
Solução: Implementada normalização de DataFrame com header=None e heurística de cabeçalho; _find_column com matching fuzzy (substring); leituras com fallbacks; mapeamentos ampliados e suporte a colunas separadas.
Observações: Suíte completa de testes passou (110 passed).

[2025-08-31] - Assistant
Arquivos: .codellm/rules/00-context.retrieval.mdc
Ação/Tipo: Documentação
Descrição: Adiciona seção de escalonamento de alto contexto com confirmação explícita ou tag [allow-high-context].
Detalhes:
Problema: Risco de aumento de tokens sem controle em tarefas de pesquisa/arquitetura.
Causa: Falta de gate explícito para limites 3000/8.
Solução: Exigir confirmação ou tag para usar perfil de alto contexto e evitar escalonamentos repetidos.
Observações: Mantém previsibilidade e controle de custos.

[2025-09-01] - Assistant
Arquivos: mcp_system/scripts/get_stats.py
Ação/Tipo: Correção
Descrição: Inicializa variável `res` em get_stats.main() para evitar NameError quando ocorre exceção antes da coleta de stats.
Detalhes:
Problema: Em alguns cenários de falha (ex.: import do servidor ou exceção antes da chamada _handle_get_stats), o script referenciava `res` sem que ele tivesse sido definido, causando NameError na saída e código de retorno inválido.
Causa: `res` era atribuído somente após operações suscetíveis a exceção.
Solução: Inicializa `res = {}` no início de main(), garantindo que o script possa terminar graficamente mesmo em erro.
Observações: Mudança mínima e segura; não altera o comportamento normal quando o servidor responde corretamente.

[2025-08-31] - Assistant
Arquivos: .codellm/rules/00-context.retrieval.mdc
Ação/Tipo: Documentação
Descrição: Especifica fallback grep_search com janela fixa (80–120 linhas), limite de 5 arquivos por consulta e uma única escalada opcional.
Detalhes:
Problema: Sem MCP, a busca poderia injetar grandes blobs de código, elevando o custo de tokens e ruído.
Causa: Falta de limites prescritivos para grep_search quando MCP está indisponível.
Solução: Definição explícita de janelas por arquivo (80–120 linhas), limite de 5 arquivos e política de escalonamento controlada (7 arquivos ou +30 linhas) mediante confirmação.
Observações: Mantém foco, previsibilidade de custo e segurança de contexto no fallback.

[2025-08-31] - Assistant
Arquivos: .codellm/rules/00-context.retrieval.mdc
Ação/Tipo: Documentação
Descrição: Refina a rule de Context Retrieval para usar MCP (searchCode/context_pack), com parâmetros padrão, cache e globs de exclusão.
Detalhes:
Problema: Regra genérica não especificava orçamento de tokens, empacotamento de contexto nem políticas de cache, reduzindo a eficácia e a economia.
Causa: Ausência de diretrizes prescritivas alinhadas ao mcp_system (indexador, pack MMR, recência, exclusões).
Solução: Adicionadas seções de fluxo recomendado, parâmetros (token_budget/max_chunks), cache TTL e invalidação, formatação padronizada, globs include/exclude, fallback sem MCP e integração com dev_history.
Observações: Ajustes visam reduzir tokens no prompt e padronizar uso do servidor MCP.

[2025-08-31] - Assistant
Arquivos: mcp_system/mcp_server_enhanced.py
Ação/Tipo: Correção
Descrição: Registra elapsed_s real nas métricas de indexação (initial_index e index_path) usando time.perf_counter.
Detalhes:
Problema: metrics_index.csv registrava elapsed_s=0.0, distorcendo latências de indexação nos relatórios.
Causa: Tempo de execução não era medido; valor resgatado do result não era populado.
Solução: Medição com time.perf_counter em _initial_index e _handle_index_path; inclusão de elapsed_s no dict result e na linha do CSV.
Observações: summarize_metrics já converte elapsed_s para latency_ms; após reiniciar o servidor, novos registros terão latência correta.

[2025-08-31] - Assistant
Arquivos: mcp_system/scripts/summarize_metrics.py, mcp_system/scripts/visual_metrics.py
Ação/Tipo: Melhoria
Descrição: Normaliza budget_utilization para %, separa contexto e indexação; adiciona --include-index, --ignore-zero-latency e baseline configurável no visual.
Detalhes:
Problema: Relatórios misturavam contexto e index com tokens estimados; latência p95/mediana iam a 0 por valores zerados; utilização aparecia subestimada (fração em vez de %).
Causa: Inclusão automática de metrics_index.csv; ausência de normalização de unidades; baseline fixo de tokens sem MCP.
Solução: summarize lê contexto por padrão, inclui index só com flag e em seção separada; normaliza utilização (0..1 -> 0..100); opção para ignorar zeros em estatísticas robustas; visual aceita --baseline e MCP_BASELINE_TOKENS e mostra últimas consultas quando não há tendência.
Observações: Métricas de index ainda têm elapsed_s=0.0 na fonte; futura melhoria no servidor poderá registrar tempo real de indexação.

[2025-08-31] - Assistant
Arquivos: mcp_system/scripts/memory_dump.py
Ação/Tipo: Documentação
Descrição: Adiciona script de dump de memória para listar registros recentes do MemoryStore sem sqlite3 CLI.
Detalhes:
Problema: Dificuldade em inspecionar registros da memória sem sqlite3.
Causa: Ausência de utilitário dedicado.
Solução: Novo script memory_dump.py com filtros e saída JSON/tabela; usa MemoryStore diretamente.
Observações: Suporta --limit, --json/--table, --project, --scope, --contains e --memory-dir.

[2025-08-31] - Assistant
Arquivos: mcp_system/mcp_server_enhanced.py
Ação/Tipo: Melhoria
Descrição: Adiciona logs de disponibilidade do MemoryStore e aviso quando desativado; mantém log do caminho do DB ao inicializar.
Detalhes:
Problema: Mensagem do caminho do DB não aparecia e ausência de logs sobre disponibilidade da memória gerava confusão.
Causa: _get_memory só logava no sucesso; não havia log no import nem quando _HAS_MEMORY=False.
Solução: Loga sucesso/falha no import; em _get_memory, emite aviso único quando desativado; mantém log do caminho ao inicializar.
Observações: Sem alteração funcional além de logging e diagnóstico.

[2025-08-31] - Assistant
Arquivos: mcp_system/mcp_server_enhanced.py
Ação/Tipo: Melhoria
Descrição: Inicializa memória e registra resumo no final da indexação automática; garante emissão do log de caminho do DB.
Detalhes:
Problema: Mensagem de caminho do DB não aparecia no startup porque _get_memory() não era chamado.
Causa: Inicialização preguiçosa só ocorria em handlers.
Solução: Chamar _get_memory() ao final de _initial_index e gravar um session_summary com estatísticas.
Observações: Sem impacto funcional negativo; apenas logging e histórico inicial.

[2025-08-31] - Assistant
Arquivos: mcp_system/memory_store.py, mcp_system/mcp_server_enhanced.py
Ação/Tipo: Documentação
Descrição: Atualiza docstring do MemoryStore para refletir caminho fixo .mcp_memory; adiciona log do caminho do DB na inicialização da memória.
Detalhes:
Problema: Confusão sobre local do memory.db e falta de visibilidade no startup.
Causa: Docstring mencionava fallback antigo; servidor não logava caminho do DB.
Solução: Docstring atualizada e stderr log com o caminho efetivo do DB ao inicializar _get_memory.
Observações: Sem mudanças de comportamento no caminho do DB; apenas documentação e logging.

[2025-08-31] - Assistant
Arquivos: mcp_system/utils/file_watcher.py, mcp_system/scripts/summarize_metrics.py
Ação/Tipo: Melhoria
Descrição: Reforça auto-contenção: watcher ignora .mcp_index/.mcp_memory/.emb_cache; summarize_metrics só lê métricas de mcp_system.
Detalhes:
Problema: Watcher e summarize_metrics podiam interagir com artefatos fora de mcp_system, gerando ruído.
Causa: Falta de filtros completos no watcher e fallbacks para ROOT_DIR.parent em summarize.
Solução: Adicionados filtros no watcher; removidos fallbacks externos no summarize_metrics.
Observações: Mantém comportamento consistente e auto-contido do servidor MCP.

[2025-08-31] - Assistant
Arquivos: mcp_system/code_indexer_enhanced.py
Ação/Tipo: Melhoria
Descrição: Inclui **/.emb_cache/** no DEFAULT_EXCLUDE para impedir indexação de caches de embeddings.
Detalhes:
Problema: Cache de embeddings poderia ser indexado acidentalmente.
Causa: Padrão de exclusão não cobria .emb_cache.
Solução: Adição do padrão **/.emb_cache/** ao DEFAULT_EXCLUDE.
Observações: Complementa exclusões de .mcp_index e .mcp_memory já aplicadas.

[2025-08-31] - Assistant
Arquivos: mcp_system/code_indexer_enhanced.py
Ação/Tipo: Melhoria
Descrição: Adiciona **/.mcp_index/** e **/.mcp_memory/** ao DEFAULT_EXCLUDE do indexador para evitar indexar artefatos internos.
Detalhes:
Problema: Possibilidade de indexar diretórios internos do servidor MCP.
Causa: Faltavam entradas .mcp_index e .mcp_memory no DEFAULT_EXCLUDE.
Solução: Inclusão explícita dos padrões no DEFAULT_EXCLUDE.
Observações: Watcher já ignorava .mcp_index; reforço agora também no indexador e inclui .mcp_memory.

[2025-08-31] - Assistant
Arquivos: mcp_system/memory_store.py
Ação/Tipo: Correção
Descrição: Define caminho fixo para memória em mcp_system/.mcp_memory/memory.db com suporte opcional a MEMORY_DIR relativo ao pacote.
Detalhes:
Problema: Local do DB inconsistente (raiz do projeto vs pasta do pacote), causando confusão e schema ausente.
Causa: Estratégia anterior dependia de INDEX_ROOT e variações de diretório.
Solução: Basear o caminho no diretório do pacote mcp_system; fallback via MEMORY_DIR.
Observações: Compatível com setups existentes ao manter MEMORY_DIR como override.

[2025-08-31] - Assistant
Arquivos: mcp_system/memory_store.py, mcp_system/mcp_server_enhanced.py
Ação/Tipo: Melhoria
Descrição: Implementa MemoryStore mínimo com SQLite (memory.db) e ativa HAS_CONTEXT_MEMORY para registrar resumos de sessão.
Detalhes:
Problema: memory.db estava vazio/inexistente porque MemoryStore não existia; HAS_MEMORY estava False e nada era persistido.
Causa: Ausência de implementação de MemoryStore no pacote.
Solução: Criação de mcp_system/memory_store.py com add_session_summary e schema SQLite; import no servidor já existente passa a habilitar o recurso.
Observações: Armazena em <INDEX_ROOT>/.mcp_index/memory.db com PRAGMA WAL e lock simples.

[2025-08-31] - Assistant
Arquivos: mcp_system/scripts/get_stats.py
Ação/Tipo: Melhoria
Descrição: Adiciona flags de indexação (--index, --no-recursive, --no-semantic, --no-watcher, --exclude) ao get_stats antes de exibir estatísticas.
Detalhes:
Problema: Necessidade de forçar uma indexação pontual e logo em seguida obter estatísticas em um único comando.
Causa: get_stats não possuía integração com o handler de indexação.
Solução: Integração com _handle_index_path, parsing de argumentos via argparse e impressão de feedback de indexação.
Observações: Mantida compatibilidade com execução por módulo e defaults de ambiente.

[2025-08-31] - Assistant
Arquivos: mcp_system/utils/file_watcher.py, mcp_system/embeddings/semantic_search.py, mcp_system/code_indexer_enhanced.py
Ação/Tipo: Melhoria
Descrição: Habilita auto-index (watcher por polling/Watchdog) e busca semântica com sentence-transformers (fallback TF-IDF).
Detalhes:
Problema: Recursos avançados apareciam como desabilitados no runtime e não havia implementação local.
Causa: Ausência de arquivos utils/file_watcher.py e embeddings/semantic_search.py no pacote.
Solução: Implementado SimpleFileWatcher com factory para watchdog e SemanticSearchEngine com ST e fallback TF-IDF; imports já compatíveis no indexador.
Observações: Para qualidade máxima, instale sentence-transformers; sem ST, fallback TF-IDF ainda habilita semântica.

[2025-08-31] - Assistant
Arquivos: mcp_system/code_indexer_enhanced.py, mcp_system/scripts/get_stats.py
Ação/Tipo: Melhoria
Descrição: Adiciona suporte a last_updated no indexador e ajusta get_stats.py para exibir campos corretos.
Detalhes:
Problema: get_stats exibindo n/a por diferenças de chaves e ausência de last_updated.
Causa: Indexador não persistia meta de atualização e chaves divergiam (total_files/total_chunks vs files_indexed/chunks).
Solução: Persistência de meta.json com last_updated em _save; leitura em _load; inclusão em get_stats(). Ajuste do script para usar total_files/total_chunks e mostrar index_size_mb/last_updated.
Observações: last_updated é ISO8601 UTC e atualiza a cada _save.

[2025-08-31] - Assistant
Arquivos: mcp_system/scripts/mcp_client_stats.py, mcp_system/scripts/summarize_metrics_enhanced.py
Ação/Tipo: Refatoração
Descrição: Remoção de scripts redundantes em favor das versões consolidadas.
Detalhes:
Problema: Sobreposição de funcionalidades entre scripts, gerando manutenção desnecessária.
Causa: Evolução do servidor e padronização das métricas.
Solução: Remoção de mcp_client_stats.py e summarize_metrics_enhanced.py; funcionalidades cobertas por get_stats.py, summarize_metrics.py e visual_metrics.py.
Observações: Se necessário, reintroduzir via histórico do VCS.

[2025-08-31] - Assistant
Arquivos: mcp_system/scripts/get_stats.py, mcp_system/scripts/summarize_metrics.py, mcp_system/scripts/visual_metrics.py
Ação/Tipo: Melhoria
Descrição: Atualiza scripts auxiliares para funcionar no contexto atual, invocando handlers locais e lendo métricas padronizadas.
Detalhes:
Problema: Scripts dependiam de clientes MCP externos ou formatos antigos, dificultando uso local e automação.
Causa: Adoção do servidor mcp_server_enhanced com handlers diretos e mudança no esquema de métricas.
Solução:
- get_stats.py: invoca _handle_get_stats e imprime resumo amigável.
- summarize_metrics.py: consolida metrics_context/metrics_index, melhora parsing e CLI.
- visual_metrics.py: moderniza leitura de métricas e gráficos ASCII.
Observações: Scripts não impactam testes; dependem apenas de CSVs em .mcp_index.

[2025-08-31] - Assistant
Arquivos: tests/test_mcp_server.py
Ação/Tipo: Teste
Descrição: Adiciona testes mínimos para indexação, busca, context_pack e where_we_stopped do servidor MCP.
Detalhes:
Problema: Ausência de validação automatizada das funcionalidades principais do MCP server.
Causa: Não havia testes cobrindo handlers principais.
Solução: Criado test_mcp_server.py com isolamento via env temporário (INDEX_ROOT/INDEX_DIR/EMBEDDINGS_CACHE_DIR) e asserts básicos.
Observações: Execução rápida; usa semantic desativado por padrão nos testes.

[2025-08-31] - Assistant
Arquivos: .vscode/mcp.json
Ação/Tipo: Configuração
Descrição: Ajusta INDEX_ROOT e CODELLM_PROJECT_PATH para mcp_system para conter todos os recursos do MCP na pasta do projeto.
Detalhes:
Problema: memory.db e índices eram criados na raiz do workspace por INDEX_ROOT antigo.
Causa: INDEX_ROOT configurado como ${workspaceFolder}.
Solução: Atualizar INDEX_ROOT e CODELLM_PROJECT_PATH para ${workspaceFolder}/mcp_system; manter INDEX_DIR e EMBEDDINGS_CACHE_DIR já dentro de mcp_system.
Observações: Reinicie o servidor MCP para aplicar o novo ambiente.

[2025-08-31] - Assistant
Arquivos: mcp_system/code_indexer_enhanced.py, mcp_system/mcp_server_enhanced.py
Ação/Tipo: Correção
Descrição: Corrige erros ao lidar com resultados de busca como objetos (EmbeddingResult) no context pack e where_we_stopped.
Detalhes:
Problema: 'EmbeddingResult' object is not subscriptable ao construir contexto; AttributeError em where_we_stopped ao varrer TODOs.
Causa: Acesso tipo dict em resultados possivelmente objetos.
Solução: build_context_pack da classe enhanced removeu bloco de mock; where_we_stopped normaliza hits via _normalize_hit.
Observações: Mantida compatibilidade com BM25 e híbrido; evita suposições de formato.

[2025-08-31] - Assistant
Arquivos: mcp_system/memory_store.py, mcp_system/mcp_server_enhanced.py, mcp_system/README.md
Ação/Tipo: Melhoria
Descrição: Implementa memória operacional mínima (SQLite) com integração no servidor e documentação.
Detalhes:
Problema: where_we_stopped não consolida memória persistente; nenhuma sessão/ação é registrada automaticamente.
Causa: Ausência de um store mínimo e de hooks no servidor.
Solução: Criação do MemoryStore (SQLite), inicialização preguiçosa; após index_path gera session_summary; where_we_stopped registra next_action com TODOs e inclui memória recente no last_done; README atualizado.
Observações: Memória é opcional e habilita automaticamente se sqlite3 estiver disponível; DB salvo em .mcp_memory/memory.db.

[2025-08-31] - Assistant
Arquivos: mcp_system/README.md
Ação/Tipo: Documentação
Descrição: Atualiza README com fallback do where_we_stopped, memória opcional e exemplos corrigidos.
Detalhes:
Problema: README não refletia fallback do where_we_stopped e exemplo de strategy desatualizado.
Causa: Implementação recente do fallback e ajustes na API de context pack.
Solução: Marca memória como opcional, documenta fallback (git+TODO+mini context), corrige strategy para "mmr" e adiciona notas de troubleshooting.
Observações: Requer git para melhor resultado do fallback; sem git, usa dev_history.md.

[2025-08-31] - Assistant
Arquivos: mcp_system/mcp_server_enhanced.py
Ação/Tipo: Melhoria
Descrição: Enriquecido get_stats com flags reais e implementado where_we_stopped com fallback (git + TODO scan + mini context).
Detalhes:
Problema: get_stats não refletia flags reais do indexador; where_we_stopped retornava not_available.
Causa: Handler minimalista sem integração leve; capabilities estáticas.
Solução: Coleta de flags de runtime (enable_semantic/enable_auto_indexing) e fallback de resumo via git log, varredura de TODO/FIXME e mini context_pack.
Observações: A funcionalidade de memória operacional completa continua opcional; fallback não requer memory_store.

[2025-08-31] - Assistant
Arquivos: mcp_system/code_indexer_enhanced.py
Ação/Tipo: Melhoria
Descrição: Evita logs de warning ruidosos quando auto-reindexação não encontrou mudanças (0 arquivos/0 chunks).
Detalhes:
Problema: Logs frequentes de auto-reindexação com 0 arquivos e 0 chunks poluíam a saída.
Causa: Callback do watcher sempre escrevia no stderr, mesmo sem mudanças.
Solução: Registrar no stderr apenas quando files>0 ou chunks>0; mantém logs de erro.
Observações: Mantida mensagem 🔄 quando há mudanças e ❌ em caso de erro.

[2025-08-31] - Assistant
Arquivos: mcp_system/code_indexer_enhanced.py
Ação/Tipo: Correção
Descrição: Corrige build_context_pack base, retorno da busca semântica e chamada compatível no indexador enhanced.
Detalhes:
Problema: Context packs quebravam por uso de variável inexistente e argumento incorreto; busca híbrida não retornava resultados.
Causa: Confusão entre parâmetros limit e max_chunks; ausência de return no caminho de sucesso; chamada com parâmetro errado.
Solução: Ajuste de limit->max_chunks no build_context_pack base; inclusão de return semantic_results; passagem correta de max_chunks no wrapper enhanced.
Observações: where_we_stopped permanece desativado (not_available) até integração com memória operacional.

[2025-08-31] - Assistant
Arquivos: mcp_system/mcp_server_enhanced.py
Ação/Tipo: Correção
Descrição: Corrige SyntaxError e estabiliza inicialização do servidor MCP com imports robustos e flags de capacidade unificadas.
Detalhes:
Problema: Erro de sintaxe em bloco except desalinhado e variáveis HAS_ENHANCED_FEATURES/HAS_CONTEXT_MEMORY inconsistentes causavam falha ao iniciar.
Causa: Bloco try/except mal formatado na seção de helpers semânticos e uso de import relativo com fallback frágil.
Solução: Reorganizado imports para absolutos, separados entre base e enhanced; unificadas flags com defaults seguros; removido bloco except solto; adicionada implementação mínima para where_we_stopped para evitar NameError.
Observações: Mantida compatibilidade com FastMCP e indexação inicial em thread background; logs mais claros para capacidades disponíveis.

[2025-08-27] - Assistant
Arquivos: mcp_system/code_indexer_enhanced.py
Ação/Tipo: Correção
Descrição: Normaliza caminhos de arquivos para evitar loop de indexação e duplicação de chunks.
Detalhes:
Problema: Caminhos de arquivos inconsistentes causavam falhas na deleção de chunks, resultando em acúmulo excessivo de chunks indexados.
Causa: Uso de caminhos absolutos e relativos não normalizados levava a identificadores de chunks inconsistentes.
Solução: Implementada normalização de caminhos em relação ao repo_root em todos os pontos críticos do processo de indexação e deleção.
Observações: Afeta criação de chunks, indexação lexical, deleção de chunks e callbacks do file watcher.


[2025-08-26] - Assistant
Arquivos: mcp_system/storage/file_storage.py, mcp_system/code_indexer_enhanced.py, mcp_system/tests/test_search_code_hybrid_semantic_e2e.py
Ação/Tipo: Teste
Descrição: Adiciona teste E2E de busca híbrida com sentence-transformers e consolida suporte a deleções e FileStorage persistente.
Detalhes:
Problema: Falta de validação end-to-end do fluxo semântico real; FileStorage não persistia dados e deleções não limpavam índices.
Causa: Ausência de testes de integração e implementação incompleta do backend de arquivo; helpers de deleção não implementados.
Solução: Implementado FileStorage com JSONL + tombstones; adicionados helpers para remoção (_remove_from_lexical_by_chunk_id e _delete_file_chunks); criado teste E2E que valida busca híbrida com embeddings reais (skip se sentence-transformers ausente).
Observações: Teste marcado como slow e condicional à presença do pacote sentence-transformers.

[2025-08-26] - Assistant
Arquivos: mcp_system/code_indexer_enhanced.py, mcp_system/EXECUTION_PLAN.md
Ação/Tipo: Melhoria
Descrição: Implementa chunking consciente de linhas e linguagem com parâmetros configuráveis e fallback seguro.
Detalhes:
Problema: Chunking por janela de caracteres cortava funções/blocos no meio, reduzindo coerência semântica.
Causa: Estratégia simples sem considerar limites lógicos e quebras de linha.
Solução: Novo algoritmo que ajusta o fim do chunk para linhas em branco ou padrões por linguagem (def/class/etc.), com sobreposição alinhada a início de linha; ENV para configurar tamanho/overlap e preferência.
Observações: Chaves ENV: MCP_CHUNK_SIZE, MCP_CHUNK_OVERLAP, MCP_PREFER_LINE_CHUNKING.

[2025-08-26] - Assistant
Arquivos: mcp_system/utils/file_watcher.py, mcp_system/code_indexer_enhanced.py, mcp_system/EXECUTION_PLAN.md
Ação/Tipo: Melhoria
Descrição: Implementa fallback por polling no watcher (SimpleFileWatcher) com suporte a deleções e integra via factory no indexador.
Detalhes:
Problema: Auto-indexação dependia exclusivamente de watchdog; sem watchdog, não havia monitoramento.
Causa: Falta de mecanismo de polling e de integração por factory no indexador.
Solução: SimpleFileWatcher agora detecta created/modified e deleted (via hashes e diff); create_file_watcher escolhe entre watchdog e polling; indexador passa a usar a factory e loga o tipo de watcher.
Observações: Intervalo padrão de polling 30s; pode ser parametrizado futuramente via env.

[2025-08-26] - Assistant
Arquivos: mcp_system/tests/test_search_code_hybrid.py
Ação/Tipo: Teste
Descrição: Adiciona teste unitário para validar mapeamento e scores da busca híbrida em search_code.
Detalhes:
Problema: Necessidade de garantir que campos (chunk_id, file_path, content, score, semantic_score, combined_score) e tipos estejam corretos, com score=combined_score.
Causa: Integração recente do hybrid_search com chunk_data poderia ter mapeamentos inconsistentes.
Solução: Teste com FakeSemanticEngine para controlar pontuações e evitar dependência de modelos reais.
Observações: Usa storage_backend=file para evitar sqlite.

[2025-08-26] - Assistant
Arquivos: mcp_system/storage/sqlite_vec.py, mcp_system/code_indexer_enhanced.py
Ação/Tipo: Correção
Descrição: Corrige erro de threads ao armazenar chunks no SQLite e torna submissão de corrotinas thread-safe.
Detalhes:
Problema: "SQLite objects created in a thread can only be used in that same thread" ao persistir chunks.
Causa: Conexão SQLite criada numa thread sendo usada em outra via callbacks/threads do watcher.
Solução: Usado check_same_thread=False na conexão SQLite; no indexador, _submit_coro passou a usar run_coroutine_threadsafe para agendar sempre no event loop principal quando chamado de outras threads.
Observações: Para alta concorrência, ideal adotar fila/worker único para IO; mudança atual resolve cenário do watcher e indexação assíncrona básica.

[2025-08-26] - Assistant
Arquivos: mcp_system/mcp_server_enhanced.py
Ação/Tipo: Melhoria
Descrição: Ajusta log da auto-indexação para confirmar is_running antes de informar que iniciou.
Detalhes:
Problema: Log informava "Auto-indexação iniciada" mesmo quando watcher não estava ativo.
Causa: Falta de verificação do estado do watcher após start_auto_indexing.
Solução: Verifica file_watcher.is_running; se falso, loga warning em vez de info.
Observações: Evita logs enganosos em ambientes sem watchdog ou com falha de inicialização.

[2025-08-26] - Assistant
Arquivos: mcp_system/utils/file_watcher.py, mcp_system/code_indexer_enhanced.py
Ação/Tipo: Melhoria
Descrição: Implementa remoção automática de chunks ao deletar arquivos via delete_callback no FileWatcher e callbacks no indexador.
Detalhes:
Problema: Arquivos deletados não eram removidos do índice, causando lixo e resultados inconsistentes.
Causa: FileWatcher não possuía callback para deleções e indexador não recebia eventos de remoção em lote.
Solução: Adicionado delete_callback ao FileWatcher, enfileirando eventos 'deleted' e chamando _on_files_deleted no indexador para remover chunks do storage e índice.
Observações: Logs do watcher agora mostram 🗑️ para deleções processadas; filtros aplicados também a paths deletados.


[2025-08-26] - Assistant
Arquivos: mcp_system/code_indexer_enhanced.py
Ação/Tipo: Correção
Descrição: Implementa chunking sensível a linhas com fallback por caracteres para atender testes de chunking.
Detalhes:
Problema: _create_chunks criava apenas janelas por caracteres, falhando nos testes que exigem boundaries por linhas quando prefer_line_chunking=True.
Causa: Implementação simplificada inicial não considerava estratégia line-aware e metadados associados.
Solução: Adicionada estratégia line-aware com tentativa de boundary em linha em branco, cálculo de linhas de início/fim e fallback char_window quando prefer_line_chunking=False.
Observações: Metadados incluem boundary_strategy, language, chunk_start_line e chunk_end_line.

[2025-08-26] - Assistant
Arquivos: mcp_system/code_indexer_enhanced.py
Ação/Tipo: Correção
Descrição: Corrige assinatura do callback do FileWatcher para evitar erro de argumento ausente.
Detalhes:
Problema: FileWatcher chamava indexer_callback(files: list), mas o indexador registrava _on_file_change(file_path, event_type), causando TypeError.
Causa: Incompatibilidade de assinatura entre o callback esperado pelo watcher e o método do indexador.
Solução: Alterado start_auto_indexing para usar _on_files_modified(files: list) e implementado o método para reindexar em lote (sem recursão) apenas arquivos válidos.
Observações: A remoção de índices em deleções permanece como melhoria futura no watcher (callback dedicado).

[2025-08-26] - Assistant
Arquivos: mcp_system/code_indexer_enhanced.py, mcp_system/embeddings/semantic_search.py, mcp_system/mcp_server_enhanced.py
Ação/Tipo: Melhoria
Descrição: Integra .gitignore (opcional), filtra diretórios ocultos, corrige decorador de notificações MCP, implementa remoção de chunks ao deletar arquivos e adiciona prompts de métricas.
Detalhes:
Problema: Embeddings gerados para caminhos ignoráveis e crash por handle_notification. Falta de remoção de chunks em deleção e ausência de prompts de métricas.
Causa: Filtros incompletos, API MCP variante, e lacuna de funcionalidade para deletar e expor métricas.
Solução: Suporte pathspec ao .gitignore, whitelist mínima de dotdirs, fallback para progress_notification, métodos _delete_file_chunks/_remove_from_lexical_by_chunk_id, e prompts get-cache-stats, get-storage-stats, get-perf-stats.
Observações: Se pathspec não estiver instalado, .gitignore será ignorado sem erro; prompts retornam JSON formatado.

[2025-08-26] - Assistant
Arquivos: mcp_system/code_indexer_enhanced.py, mcp_system/mcp_server_enhanced.py
Ação/Tipo: Correção
Descrição: Corrige erros de asyncio.run em loop ativo e ausência de índice lexical; ajusta servidor MCP para tipos corretos e segurança de recursos.
Detalhes:
Problema: RuntimeWarning de corrotinas não aguardadas, erro 'asyncio.run() cannot be called from a running event loop' e AttributeError '_index_lexical_chunk' impediam indexação; servidor referenciava tipos inexistentes (PrompMessage) e não restringia leitura.
Causa: Uso de asyncio.run dentro de loop já em execução, métodos de índice lexical faltando e imports/tipos MCP incorretos.
Solução: Implementado _submit_coro para agendar corrotinas com loop ativo, adicionado índice BM25 (_tokenize, _index_lexical_chunk, _bm25_score_query) e get_indexed_files; no servidor, importados PromptMessage/InitializationOptions/NotificationOptions, corrigido uso de PromptMessage e restrita read_resource ao repo_root.
Observações: Fallback para FileStorage permanece; estatísticas do storage retornam vazio quando chamado sob loop ativo para evitar bloqueio.

[2025-08-26] - Assistant
Arquivos: mcp_system/mcp_server_enhanced.py
Ação/Tipo: Correção
Descrição: Corrige importações do pacote MCP no servidor para usar mcp.server.Server e remove símbolos não utilizados.
Detalhes:
Problema: ImportError ao importar Server de mcp (namespace incorreto), impedindo o servidor de responder ao initialize.
Causa: Uso de API errada/desatualizada do pacote MCP (importando de mcp em vez de mcp.server).
Solução: Ajuste dos imports para from mcp.server import Server e limpeza de NotificationOptions/InitializationOptions. Mantidos apenas tipos usados de mcp.types.
Observações: Startup do servidor deve prosseguir; caso novas quebras surjam, verificar compatibilidade da versão do pacote MCP instalado.

[2025-08-26] - Assistant
Arquivos: mcp_system/__init__.py
Ação/Tipo: Correção
Descrição: Remove exportações inexistentes e padroniza imports no pacote para evitar ImportError durante o startup do servidor MCP.
Detalhes:
Problema: __init__.py importava símbolos inexistentes (BaseCodeIndexer, funções auxiliares) causando ImportError ao inicializar o pacote.
Causa: Divergência entre interface planejada e implementação atual do code_indexer_enhanced.
Solução: Importações restritas a EnhancedCodeIndexer, DEFAULT_INDEX_DIR e DEFAULT_REPO_ROOT; recursos opcionais importados de forma tolerante; atualização de __all__.
Observações: Garante que mcp_system possa ser importado com segurança pelo servidor.

[2025-08-26] - Assistant
Arquivos: mcp_system/code_indexer_enhanced.py
Ação/Tipo: Correção
Descrição: Corrige falha de importação no startup do servidor MCP removendo import de migração no topo e eliminando fallback para imports absolutos.
Detalhes:
Problema: Servidor encerrava com ImportError/ModuleNotFoundError (migrate_from_file_to_sqlite inexistente e pacote 'storage' não encontrado) durante a inicialização.
Causa: Importação antecipada de migrate_from_file_to_sqlite e bloco de fallback para imports absolutos ('storage.*') que não existem no ambiente do servidor.
Solução: Padronização para imports relativos somente; import tardio de migrate_from_file_to_sqlite dentro do método migrate_to_sqlite; remoção do fallback para imports absolutos.
Observações: Reinicialização do servidor deve prosseguir sem erro de import. Se a função de migração não existir, retorna False sem quebrar o startup.

[2025-08-26] - Assistant
Arquivos: mcp_system/code_indexer_enhanced.py, mcp_system/EXECUTION_PLAN.md
Ação/Tipo: Melhoria
Descrição: Integra hybrid_search com chunk_data e inclui combined_score nos resultados; atualiza estado do plano (MCP-005/006/007).
Detalhes:
Problema: hybrid_search exigia chunk_data e resultados não incluíam combined_score consistentemente; plano desatualizado.
Causa: Saída da busca não mapeava todos os campos e o plano não refletia progresso real.
Solução: Construído chunk_data a partir do índice em memória; resultados agora incluem combined_score em ambas as ramificações; atualização das seções DOING/OK no EXECUTION_PLAN.md.
Observações: Fallback por polling (MCP-006) ainda pendente.

[2025-08-26] - Assistant
Arquivos: mcp_system/EXECUTION_PLAN.md
Ação/Tipo: Documentação
Descrição: Cria plano de execução com fases, backlog e controle de status para o servidor MCP aprimorado.
Detalhes:
Problema: Ausência de um plano consolidado para guiar correções críticas (busca híbrida, cache, performance, watcher) e acompanhar progresso.
Causa: Evolução incremental sem um documento único de controle de escopo e prioridades.
Solução: Adicionado EXECUTION_PLAN.md com objetivos, métricas, fases, tarefas identificáveis (IDs), critérios de aceite e checklist de controle.
Observações: Plano cobre curto prazo (desbloqueio da busca) e médio prazo (híbrido, chunking, observabilidade, testes).

[2025-08-25] - Assistant
Arquivos: tests/unit/test_readers_phase1.py, src/infrastructure/readers/excel_reader.py
Ação/Tipo: Teste
Descrição: Adiciona testes de leitores (Excel/CSV) para cenários de erro e extração de saldos. Ajuste em Excel _parse_amount.
Detalhes:
Problema: Baixa cobertura e falta de validação de fluxos de erro e extração de saldos nos readers.
Causa: Ausência de testes específicos e assinatura limitada de _parse_amount no Excel reader para reutilização.
Solução: Criados testes unitários para erros de colunas ausentes e métodos auxiliares; _parse_amount passou a retornar (valor, tipo) e foi ajustado nos pontos de uso.
Observações: Cobertura do excel_reader subiu para 92% e csv_reader para 76%; suíte total agora com 69% de cobertura.

[2025-08-25] - Assistant
Arquivos: tests/unit/test_basic_analyzer.py, tests/unit/test_text_report.py
Ação/Tipo: Teste
Descrição: Adiciona testes unitários para BasicStatementAnalyzer e TextReportGenerator, elevando cobertura.
Detalhes:
Problema: Cobertura baixa em analyzer e reports, com risco de regressões não detectadas.
Causa: Ausência de testes unitários específicos para alertas, insights e conteúdo de relatórios.
Solução: Criados testes que validam resumos, alerts, insights e geração/gravação de relatórios em texto.
Observações: Cobertura total do basic_analyzer atingiu 100% e text_report subiu para 55%.

[2025-08-25] - Assistant
Arquivos: mcp_system/scripts/summarize_metrics.py, mcp_system/mcp_server_enhanced.py, mcp_system/reindex.py, mcp_system/code_indexer_enhanced.py
Ação/Tipo: Melhoria
Descrição: Separa métricas de contexto e indexação em arquivos distintos, adiciona agrupamento por fuso horário e registra métricas na indexação inicial do servidor.
Detalhes:
Problema: Métricas misturadas em um único CSV e ausência de registros na indexação automática inicial impediam ver dados do dia atual.
Causa: build_context_pack e reindex compartilhavam o mesmo arquivo; _initial_index não registrava métricas.
Solução: summarize_metrics agora lê múltiplas fontes (metrics_context.csv, metrics_index.csv, metrics.csv); code_indexer grava em metrics_context.csv; reindex grava em metrics_index.csv; servidor passa a registrar initial_index em metrics_index.csv; adicionado parâmetro --tz (local/utc) para agrupamento diário.
Observações: Env MCP_METRICS_FILE continua suportado para sobrescrever o destino de métricas.

[2025-08-25] - Assistant
Arquivos: mcp_system/embeddings/semantic_search.py
Ação/Tipo: Melhoria
Descrição: Implementa lazy-load do modelo de embeddings para reduzir latência de startup.
Detalhes:
Problema: Tempo de inicialização elevado devido ao carregamento do SentenceTransformer no startup.
Causa: Modelo era inicializado no __init__ do SemanticSearchEngine.
Solução: Removida inicialização no __init__; adicionada inicialização sob demanda em get_embedding, search_similar e hybrid_search (já chamava _initialize_model). Mantidos logs de carregamento via stderr.
Observações: Caso sentence-transformers não esteja instalado, funções fazem fallback silencioso para BM25.

[2025-08-25] - Assistant
Arquivos: mcp_system/mcp_server_enhanced.py
Ação/Tipo: Correção
Descrição: Corrige NameError por falta de import de threading e remove duplicações no disparo da indexação inicial.
Detalhes:
Problema: Erro NameError: 'threading' is not defined ao iniciar thread de indexação inicial e duplicidade de chamadas.
Causa: Ausência de import threading e múltiplas tentativas de iniciar a thread (helper redundante e no main fallback).
Solução: Importado threading, consolidado _initial_index() e disparo único em cada caminho (FastMCP e fallback), removendo duplicações.
Observações: Initialize não é bloqueado; logs informam progresso da indexação.

[2025-08-25] - Assistant
Arquivos: mcp_system/mcp_server_enhanced.py
Ação/Tipo: Melhoria
Descrição: Ativa indexação automática no início do servidor com opções via variáveis de ambiente.
Detalhes:
Problema: Era necessário chamar manualmente index_path antes de usar o servidor; sem indexação inicial, as primeiras buscas retornavam vazio.
Causa: Ausência de rotina de indexação no startup do servidor.
Solução: Implementada função _initial_index() e disparo em thread daemon no startup (FastMCP e fallback). Variáveis de ambiente: AUTO_INDEX_ON_START (default=1), AUTO_INDEX_PATHS (default=.), AUTO_INDEX_RECURSIVE (default=1), AUTO_ENABLE_SEMANTIC (default=1), AUTO_START_WATCHER (default=1).
Observações: Execução em background evita bloquear a handshake initialize do MCP.

[2025-08-25] - Assistant
Arquivos: mcp_system/mcp_server_enhanced.py
Ação/Tipo: Correção
Descrição: Corrige término prematuro do servidor FastMCP adicionando chamada de execução (mcp.run()).
Detalhes:
Problema: Servidor encerrava antes de responder ao `initialize` quando FastMCP estava disponível.
Causa: Bloco FastMCP não iniciava o loop de servidor (faltava chamada de `mcp.run()` no __main__).
Solução: Adicionada execução condicional `if HAS_FASTMCP and __name__ == "__main__": mcp.run()` para manter o servidor em execução.
Observações: Mantido fallback para MCP tradicional com asyncio.run(main()).

[2025-08-25] - Assistant
Arquivos: .vscode/mcp.json, mcp_system/mcp_server_enhanced.py, mcp_system/code_indexer_enhanced.py, mcp_system/embeddings/semantic_search.py
Ação/Tipo: Refatoração
Descrição: Encapsula totalmente o servidor MCP no pacote mcp_system e garante que o diretório .mcp_index fique sob mcp_system.
Detalhes:
Problema: Arquivos de índice (.mcp_index) eram criados na raiz e imports não eram estritamente relativos ao pacote, dificultando isolar o MCP como ferramenta separada.
Causa: Configuração do .vscode/mcp.json apontava INDEX_DIR para .mcp_index na raiz e havia imports absolutos e paths relativos frágeis (../../) no código.
Solução: Ajuste do .vscode/mcp.json para usar INDEX_DIR=mcp_system/.mcp_index; padronização de paths no código para usar CURRENT_DIR/CURRENT_DIR.parent; correção de imports para a forma relativa (from .module import ...); definição de defaults de index_dir/metrics/embeddings sob mcp_system.
Observações: Compatível com CodeLLM (Abacus.ai) e execução automática do servidor MCP; métricas e embeddings também ficam contidos em mcp_system/.mcp_index.

[2025-04-05] - Assistant
Arquivos: src/utils/currency_utils.py, src/infrastructure/readers/csv_reader.py, src/infrastructure/readers/excel_reader.py
Ação/Tipo: Correção
Descrição: Corrige erros na detecção de moeda e chamadas duplicadas em leitores de extratos.
Detalhes:
Problema: Erros de 'classmethod' object is not callable, NameError: name 'pd' is not defined e detecção incorreta de moeda (CAD em vez de EUR)
Causa: Linhas em branco extras entre decoradores @classmethod, imports faltando no escopo correto e lógica de detecção de moeda muito permissiva
Solução: Remoção de linhas em branco extras, movimentação do import pandas para o método extract_currency_from_dataframe e refinamento da lógica de detecção de moeda usando delimitadores de palavra
Observações: Todos os testes passando após as correções

[2025-04-05] - Assistant
Arquivos: src/utils/currency_utils.py
Ação/Tipo: Correção
Descrição: Corrige erro de definição de método na classe CurrencyUtils.
Detalhes:
Problema: TypeError: 'classmethod' object is not callable ao chamar extract_currency_from_dataframe
Causa: Linha em branco extra entre decoradores @classmethod na definição do método
Solução: Remoção da linha em branco extra entre os decoradores @classmethod
Observações: Problema identificado na definição do método extract_currency_from_dataframe

[2025-04-05] - Assistant
Arquivos: src/utils/currency_utils.py
Ação/Tipo: Correção
Descrição: Corrige erro de importação do pandas no método extract_currency_from_dataframe.
Detalhes:
Problema: NameError: name 'pd' is not defined ao executar o método extract_currency_from_dataframe
Causa: O import pandas as pd não estava disponível no escopo do método
Solução: Movimentação do import pandas como pd para dentro do método extract_currency_from_dataframe
Observações: O import foi movido para garantir que esteja disponível no escopo correto

[2025-04-05] - Assistant
Arquivos: src/infrastructure/readers/csv_reader.py, src/infrastructure/readers/excel_reader.py
Ação/Tipo: Correção
Descrição: Remove chamadas duplicadas ao método extract_currency_from_dataframe.
Detalhes:
Problema: Chamadas duplicadas ao método extract_currency_from_dataframe em ambos os leitores
Causa: Código redundante com chamadas repetidas ao mesmo método
Solução: Remoção das chamadas duplicadas mantendo apenas a chamada inicial
Observações: Melhoria de eficiência removendo processamento redundante

[2025-04-05] - Assistant
Arquivos: src/utils/currency_utils.py
Ação/Tipo: Correção
Descrição: Corrige lógica de detecção de moeda para evitar falsos positivos.
Detalhes:
Problema: Detecção incorreta de CAD em vez de EUR quando não há informações de moeda explícitas
Causa: Procura por códigos de moeda como substrings simples, causando falsos positivos
Solução: Uso de delimitadores de palavra (\b) para procurar apenas por códigos de moeda como palavras completas
Observações: A detecção agora usa expressões regulares com \b para evitar encontrar códigos de moeda como substrings
[2025-09-02] - Assistant
Arquivos: mcp_system/memory_store.py
Ação/Tipo: Melhoria
Descrição: Expõe estatísticas globais do cache determinístico e utilitário para métricas básicas do MemoryStore (SQLite).
Detalhes:
Problema: Não existia forma centralizada de consultar métricas dos caches em memória e do MemoryStore.
Causa: Implementação inicial do cache não expunha funções utilitárias para inspeção.
Solução: Adiciona get_all_cache_stats() e get_memory_store_stats(store) em mcp_system/memory_store.py.
Observações: get_memory_store_stats assume que MemoryStore possui um atributo `conn` (sqlite3.Connection); tratamento de erro seguro retornando dicionário com 'error'.

[2025-09-02] - Assistant
Arquivos: mcp_system/memory_store.py
Ação/Tipo: Melhoria
Descrição: Adiciona cache determinístico em memória com TTL, normalização de chaves e métricas.
Detalhes:
Problema: Ausência de cache local determinístico para otimizar buscas locais e reduzir chamadas repetidas ao indexador/embeddings.
Causa: Implementação de MemoryStore faltante ou incompleta para caching leve.
Solução: Implementa DeterministicCache com TTL, thread-safety (RLock), métricas de hits/misses/evictions e helper get_cache(ns) para reuso por namespace.
Observações: TTLs padrão definidos (TTL_SEARCH_S=120s, TTL_EMB_DAYS=14, TTL_META_DAYS=30); a implementação é puramente em memória e não persiste entre execuções.

[2025-09-03] - Assistant
Arquivos: mcp_system/memory_store.py, mcp_system/mcp_server_enhanced.py, mcp_system/scripts/get_stats.py
Ação/Tipo: Melhoria
Descrição: Adiciona shim mínimo de MemoryStore sqlite e melhora mensagens de log/diagnóstico para ausência de MemoryStore.
Detalhes:
Problema: Servidor esperava uma classe MemoryStore presente em mcp_system.memory_store; em ambientes onde esta classe não existia, logs mostravam ImportError e funcionalidades de persistência faltavam.
Causa: Implementação parcial do módulo de memória; importações rígidas e mensagens pouco descritivas.
Solução: - Implementa MemoryStore shim (sqlite em .mcp_memory/memory.db) com conn/add_session_summary/close para compatibilidade mínima.
- Ajusta a inicialização preguiçosa da memória no servidor e mensagens de log para serem informativas e acionáveis.
- Torna get_stats.py resiliente ao importar o módulo memory_store e usa getattr para obter funções opcionais.
Observações: O shim é minimal e visa compatibilidade; pode ser substituído por uma implementação completa posterior.

[2025-09-02] - Assistant
Arquivos: mcp_system/mcp_server_enhanced.py, scripts/reports/generate_mcp_report.py
Ação/Tipo: Melhoria
Descrição: Corrige instrumentação de métricas agregadas e aprimora relatório com p95 e separação de warmups.
Detalhes:
Problema: tokens_sent_total/tokens_saved_total apareciam zerados; relatório não exibia p95 nem separava warmups.
Causa: Duplicidade de definições de context_pack e resets dos acumuladores; render_text sem campos p95/breakdown.
Solução: Unifica caminho de atualização (_handle_context_pack + __update_metrics_from_pack), evita reset dos contadores, adiciona logging por consulta na MemoryStore e imprime p95 + breakdown warmup.
Observações: Verificar novamente get_stats após novas queries para confirmar incremento e revisar limiares de alerta.

[2025-09-02] - Assistant
Arquivos: scripts/reports/generate_mcp_report.py
Ação/Tipo: Ferramenta/Teste
Descrição: Adiciona utilitário para gerar relatórios agregados do MCP chamando scripts existentes e salvando JSON+TXT.
Detalhes:
Problema: Análise manual de múltiplos scripts para relatório diário consome tempo.
Causa: Ferramentas de métricas dispersas e need for single consolidated report.
Solução: Implementa scripts/reports/generate_mcp_report.py que executa get_stats/summarize_metrics/visual_metrics/memory_dump, agrega resultados e calcula métricas derivadas (economia %). Salva .json e .txt em scripts/reports/output.
Observações: Usa python -m para executar scripts internos e grava saída estruturada para pipelines e visualização humana.

[2025-09-01] - Assistant
Arquivos: mcp_system/scripts/visual_metrics.py
Ação/Tipo: Melhoria
Descrição: Adiciona saída JSON estruturada (--json) e função generate_visual_report_structured para integração com pipelines.
Detalhes:
Problema: Ferramenta gerava apenas saída legível; integração com pipelines exigia formato estruturado.
Causa: Ausência de saída JSON consolidada e função utilitária.
Solução: Implementa generate_visual_report_structured() que retorna summary/daily/rows e adiciona --json para imprimir esse JSON; mantém saída legível padrão.
Observações: Compatível com uso interativo e pipelines; não altera formato CSV de entrada.

[2025-09-01] - Assistant
Arquivos: mcp_system/scripts/summarize_metrics.py
Ação/Tipo: Melhoria
Descrição: Evita reparse de timestamps e garante saída JSON com ensure_ascii=False.
Detalhes:
Problema: parse_dt era chamado várias vezes durante filtros e cálculos, impactando performance.
Causa: filter_rows chamava parse_dt para cada verificação múltipla.
Solução: filter_rows agora pré-parseia timestamps e anota cada linha com _parsed_ts; _compute_stats reutiliza esse valor. Também assegura ensure_ascii=False no JSON.
Observações: Comportamento e resultados idênticos; melhoria de desempenho em grandes CSVs.

[2025-09-01] - Assistant
Arquivos: mcp_system/scripts/memory_dump.py
Ação/Tipo: Melhoria
Descrição: Adiciona flags --pretty e --limit-fields e validação de --memory-dir.
Detalhes:
Problema: JSON muito verboso e possibilidade de memória-dir inválido sendo aceita silenciosamente.
Causa: Falta de opções de truncamento e validação do caminho informado.
Solução: Implementa --pretty para truncar campos longos e --limit-fields para controlar o limite; valida --memory-dir e aborta com erro claro se inexistente.
Observações: Saída padrão permanece JSON completa; opção --pretty facilita inspeção humana.

[2025-09-01] - Assistant
Arquivos: mcp_system/scripts/summarize_metrics.py, mcp_system/scripts/visual_metrics.py, mcp_system/scripts/get_stats.py, mcp_system/scripts/memory_dump.py
Ação/Tipo: Melhoria
Descrição: Robustez nos scripts de métricas e memória (datas ISO-8601, amostragem em gráficos ASCII, fallback de tokens, flags --json/--reverse, index antes de stats).
Detalhes:
Problema: Parsers frágeis para timestamps; gráficos quebravam com séries longas; total_tokens zerado em alguns registros; necessidade de payload bruto e ordenação customizada.
Causa: Formatos variados (UTC +00:00/Z); séries maiores que largura; campos alternativos (total_tokens_sent); coleta de stats após index; ausência de flags utilitárias.
Solução: parse_dt com fromisoformat e suporte a 'Z'; amostragem para largura fixa; fallback para total_tokens_sent; flag --json no get_stats; indexação opcional antes de coletar stats; flag --reverse no memory_dump.
Observações: Compatível com CSVs atuais (metrics_context/index); não altera contratos de saída padrão.

[2025-09-01] - Assistant
Arquivos: mcp_system/README 2.md -> (removido)
Ação/Tipo: Documentação
Descrição: Remove README 2 duplicado para evitar divergência de informações; README.md passa a ser fonte única.
Detalhes:
Problema: Documentação fragmentada em dois READMEs no mcp_system, podendo gerar confusão.
Causa: Evolução incremental com múltiplos arquivos de documentação.
Solução: Remoção do arquivo redundante; README.md consolidado com conteúdo de produção.
Observações: Sem impacto funcional; apenas documentação.

[2025-09-06] - Assistant
Arquivos: tests/test_get_stats.py
Ação/Tipo: Teste
Descrição: Adiciona testes unitários para get_stats.print_agg cobrindo casos vazio e não vazio.
Detalhes:
Problema: get_stats.print_agg não tinha testes automatizados; saída não era validada em CI.
Causa: Arquivo get_stats.py utilizado como script sem cobertura unitária.
Solução: Implementados dois testes que validam behavior para agregados vazios e com múltiplos modelos (ordenação por tokens e totais).
Observações: Testes não dependem de MemoryStore e usam capsys para capturar stdout.

[2025-09-06] - Assistant
Arquivos: mcp_system/mcp_server_enhanced.py, .codellm/rules/00-context.retrieval.mdc
Ação/Tipo: Correção | Documentação
Descrição: Adiciona suporte a model_name/provider em handlers MCP e wrappers de ferramentas; inclui client_info em logs, context packs e métricas; documenta injeção do modelo no contexto.
Detalhes:
Problema: Handlers e capturadores do MCP não recebiam nem logavam metadados de modelo e provedor, o que dificultava telemetria detalhada e roteamento baseado em modelo.
Causa: Ausência dos parâmetros opcionais `model_name` e `provider` nas assinaturas, além de falta de documentação para uso padrão em payloads MCP.
Solução: Atualização dos handlers principais (index_path, search_code, context_pack, get_stats, cache_management, where_we_stopped) para aceitar `model_name` e `provider` com valores fallback (env ou "unknown"); logs revisados para registrar client_info; objetos retornados enriquecidos; adicionada documentação em .codellm/rules/00-context.retrieval.mdc sobre o uso do `mcp.set_client_info` e inclusão no payload.
Observações: Compatível e não disruptivo, parâmetros opcionais; recomenda-se reiniciar servidor MCP para ativar coleta dos metadados; testes devem validar presença dos logs e métricas com client_info.
