
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