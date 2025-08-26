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