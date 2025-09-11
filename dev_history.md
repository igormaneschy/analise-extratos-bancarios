[2025-09-10] - Assistant
Arquivos: scripts/create_sample_pdf.py
Ação/Tipo: Correção
Descrição: Ajusta uso de cores para compatibilidade com mocks de reportlab nos testes.
Detalhes:
Problema: Testes unitários falharam porque o mock simplificado de reportlab.lib.colors usado nos testes não expõe constantes como `grey`, `whitesmoke`, etc.
Causa: O script `scripts/create_sample_pdf.py` referenciava atributos de cor diretos (e.g., `colors.grey`) que não existem no mock.
Solução: Adicionei um helper `_safe_color` que tenta obter o atributo de `colors` e, se ausente, usa `colors.HexColor()` com um valor hex de fallback. Atualizei os estilos de tabela para usar `_safe_color` em todas as cores, mantendo compatibilidade com a implementação real do reportlab.
Observações: Esta alteração é segura para execução com a biblioteca reportlab real e corrige falhas nos testes unitários que usam um mock minimalista.


[2025-09-10] - Assistant
Arquivos: tests/unit/test_main_cli.py, tests/unit/test_create_sample_pdf.py
Ação/Tipo: Teste
Descrição: Adiciona testes unitários prioritários para o CLI principal (main.py) e para o gerador de PDF de exemplo (scripts/create_sample_pdf.py).
Detalhes:
Problema: Cobertura insuficiente em arquivos críticos (main.py e scripts/*) e ausência de testes para utilitários de criação de PDF de amostra.
Causa: Falta de testes específicos para comandos CLI e scripts auxiliares, deixando linhas importantes não exercitadas durante a suíte de testes.
Solução: Criação de testes em tests/unit/test_main_cli.py (mock dos imports tardios de src.* para isolar o CLI) e tests/unit/test_create_sample_pdf.py (verifica criação do PDF em diretório temporário). Execução dos testes unitários mostrou que todos os testes passam.
Observações: Após inclusão dos testes, executei pytest em tests/unit; 124 testes passaram e a cobertura total subiu para 89% (relatório disponível no console). Próximos passos recomendados: adicionar testes para scripts com cobertura 0% e aumentar cobertura de src/infrastructure/readers/excel_reader.py para >90%.


// ... existing code ...

[2025-09-10] - Assistant
Arquivos: dev_history.md, dev_history_old.md
Ação/Tipo: Manutenção
Descrição: Limpeza e arquivamento do histórico de desenvolvimento. As entradas legadas que referenciavam caminhos não existentes foram movidas para dev_history_old.md (append ao final).
Detalhes:
Problema: dev_history.md acumulou entradas com referências a arquivos/diretórios que não existem mais no repositório, tornando o histórico ruidoso e difícil de manter.
Causa: Evolução do projeto e realocação/remoção de componentes sem limpeza do histórico.
Solução: Arquivei o conteúdo anterior de dev_history.md em dev_history_old.md e reinicializei dev_history.md com este registro resumido de manutenção. Mantive uma cópia íntegra em dev_history_old.md para auditoria.
Observações: Para restaurar entradas antigas, consulte dev_history_old.md. Esta ação segue as convenções de histórico do repositório.
