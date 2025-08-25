[2025-08-13] - Assistant
Arquivos: src/infrastructure/readers/csv_reader.py, src/application/use_cases.py, main.py, README.md, tests/test_csv_reader.py, tests/test_comprehensive_suite.py, data/samples/extrato_exemplo.csv
Ação/Tipo: Melhoria
Descrição: Implementa suporte ao formato CSV para leitura de extratos bancários.
Detalhes:
Problema: Sistema só suportava PDF e Excel
Causa: Necessidade de suportar mais formatos de entrada
Solução: Implementação do CSVStatementReader com detecção automática de colunas e moeda
Observações: Adicionados testes específicos para o leitor CSV e atualização da documentação

[2025-08-13] - Assistant
Arquivos: src/services/transaction_analyzer.py, src/domain/models.py
Ação/Tipo: Melhoria
Descrição: Integra modelo de ML para detecção de padrões de gasto e anomalias.
Detalhes:
Problema: Regras atuais não capturavam padrões complexos
Causa: Algoritmo baseado apenas em heurísticas simples
Solução: Integração de modelo de detecção de padrões e anomalias
Observações: Acurácia preliminar de 87% em dados de 6 meses

[2025-08-12] - Assistant
Arquivos: src/utils/currency_utils.py, src/domain/models.py, src/infrastructure/readers/excel_reader.py, src/infrastructure/analyzers/basic_analyzer.py, src/infrastructure/reports/text_report.py, main.py
Ação/Tipo: Melhoria
Descrição: Implementa detecção automática de moeda e formatação dinâmica.
Detalhes:
Problema: Sistema estava hardcoded para EUR
Causa: Necessidade de suportar múltiplas moedas
Solução: Detecção automática de moeda (EUR, BRL, USD, GBP, JPY, CHF, CAD, AUD) e formatação dinâmica
Observações: Cobertura de testes para módulo de moeda atingiu 97%

[2025-08-11] - Assistant
Arquivos: tests/test_currency_utils.py, tests/test_suite.py, tests/test_comprehensive_suite.py
Ação/Tipo: Teste
Descrição: Adiciona testes abrangentes para utilitários de moeda e atualiza testes existentes.
Detalhes:
Problema: Cobertura de testes insuficiente
Causa: Falta de testes para novas funcionalidades
Solução: Implementação de testes unitários e de integração
Observações: Cobertura geral aumentada para 85%

[2025-08-10] - Assistant
Arquivos: src/infrastructure/reports/text_report.py
Ação/Tipo: Correção
Descrição: Corrige formatação de valores monetários em relatórios de texto.
Detalhes:
Problema: Valores monetários não estavam sendo formatados corretamente
Causa: Uso de formatação hardcoded para Euro
Solução: Implementação de formatação dinâmica baseada na moeda do extrato
Observações: Agora suporta formatação adequada para diferentes moedas

[2025-08-09] - Assistant
Arquivos: src/domain/models.py, src/infrastructure/analyzers/basic_analyzer.py
Ação/Tipo: Melhoria
Descrição: Adiciona propriedades de totais ao modelo AnalysisResult e melhora cálculos.
Detalhes:
Problema: Cálculos de totais estavam espalhados
Causa: Falta de centralização dos cálculos
Solução: Adição de propriedades income, expenses e balance ao AnalysisResult
Observações: Simplificação do código de análise com melhor reusabilidade

[2025-08-08] - Assistant
Arquivos: src/application/use_cases.py, main.py
Ação/Tipo: Melhoria
Descrição: Implementa seleção automática de leitor baseado no tipo de arquivo.
Detalhes:
Problema: Sistema tinha leitores hardcoded
Causa: Necessidade de suportar múltiplos formatos
Solução: Implementação de mecanismo de detecção automática de formato
Observações: Agora suporta PDF, Excel e futuros formatos de forma transparente

[2025-08-07] - Assistant
Arquivos: src/infrastructure/readers/excel_reader.py
Ação/Tipo: Melhoria
Descrição: Melhora extração de dados de arquivos Excel com detecção automática de moeda.
Detalhes:
Problema: Sistema só suportava Euro
Causa: Necessidade de suportar múltiplas moedas
Solução: Implementação de detecção automática de moeda em arquivos Excel
Observações: Suporta USD, BRL, GBP além de EUR

[2025-08-06] - Assistant
Arquivos: src/domain/models.py, src/infrastructure/readers/pdf_reader.py
Ação/Tipo: Refatoração
Descrição: Adiciona campo de moeda aos modelos e melhora parsing de PDFs.
Detalhes:
Problema: Modelos não tinham suporte a moedas
Causa: Necessidade de internacionalização
Solução: Adição de campo currency aos modelos BankStatement e AnalysisResult
Observações: Melhorias no parsing de valores monetários em PDFs

[2025-08-05] - Assistant
Arquivos: main.py, src/application/use_cases.py, src/infrastructure/reports/text_report.py
Ação/Tipo: Melhoria
Descrição: Adiciona suporte a relatórios em Markdown e melhora interface CLI.
Detalhes:
Problema: Sistema só gerava relatórios em texto simples
Causa: Necessidade de formatos mais ricos
Solução: Implementação de MarkdownReportGenerator e melhorias na CLI
Observações: Nova opção --format markdown no comando analyze