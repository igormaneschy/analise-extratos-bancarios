[2025-08-17] - Assistant
Arquivos: src/infrastructure/analyzers/basic_analyzer.py
Ação/Tipo: Correção
Descrição: Correção do tratamento de valores None em operações matemáticas e comparações com period_start e period_end.
Detalhes:
Problema: Ocorria erro "'>' not supported between instances of 'NoneType' and 'NoneType'" e "unsupported operand type(s) for -: 'NoneType' and 'NoneType'" quando o leitor de PDF não conseguia extrair as datas do período do extrato, resultando em period_start e period_end como None.
Causa: O código estava tentando realizar operações matemáticas e comparações com valores None sem verificar se eram válidos antes.
Solução: Adicionadas verificações para garantir que period_start e period_end não sejam None antes de realizar operações matemáticas e comparações, retornando 0 quando os valores são None.
Observações: As correções foram feitas em três pontos específicos do arquivo basic_analyzer.py: 1) No cálculo de period_days no metadata da AnalysisResult, 2) Na verificação de comparação de datas para cálculo de média diária de gastos, 3) Na verificação de comparação de datas para cálculo de frequência de transações.