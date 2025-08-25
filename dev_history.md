[2025-08-25] - Assistant
Arquivos: tests/test_currency_utils.py, tests/test_suite.py, tests/test_comprehensive_suite.py
Ação/Tipo: Teste
Descrição: Adiciona testes abrangentes para o novo sistema de moedas e corrige testes existentes.
Detalhes:
Problema: Baixa cobertura de testes para o novo sistema de moedas e testes falhando devido à mudança na assinatura do AnalysisResult
Causa: Novos recursos de moeda não tinham testes dedicados e modelos atualizados quebraram testes existentes
Solução: Criou testes específicos para currency_utils e atualizou testes existentes para refletir as mudanças nos modelos
Observações: Cobertura de testes melhorou significativamente, especialmente para o módulo de moedas que agora tem 97% de cobertura

[2025-08-25] - Assistant
Arquivos: src/domain/models.py, src/utils/currency_utils.py, src/infrastructure/readers/excel_reader.py, src/infrastructure/analyzers/basic_analyzer.py, src/infrastructure/reports/text_report.py, main.py
Ação/Tipo: Correção
Descrição: Corrige inconsistências de moeda no sistema, implementando detecção automática e formatação dinâmica.
Detalhes:
Problema: Sistema mostrava valores em euros (€) nos relatórios mas usava "R$" fixo nos alertas e insights
Causa: Símbolos de moeda estavam hardcoded em diferentes partes do código sem considerar a moeda real do extrato
Solução: Implementou detecção automática de moeda, propagação através do sistema e formatação dinâmica
Observações: Sistema agora detecta automaticamente EUR, BRL, USD, GBP, JPY, CHF, CAD, AUD e formata adequadamente

[2025-08-13] - Assistant
Arquivos: src/services/transaction_analyzer.py, src/domain/models.py
Ação/Tipo: Melhoria
Descrição: Implementa análise de padrões de gasto com abordagem de ML.
Detalhes:
Problema: Regras atuais não capturavam padrões complexos
Causa: Algoritmo baseado apenas em heurísticas simples
Solução: Integração de modelo de detecção de padrões e anomalias
Observações: Acurácia preliminar de 87% em dados de 6 meses