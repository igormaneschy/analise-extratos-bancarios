# Relatório de Validação das Regras
==================================================

## Métricas Gerais
- Violações de Clean Architecture: 0
- Violações de SOLID: 3
- Violações de DRY/KISS/YAGNI: 2
- Violações de Testes: 0
- Violações de Histórico: 0

## Cobertura de Testes
- Cobertura atual: 82%
- Linhas totais: 2933
- Linhas não cobertas: 516

## Violações Encontradas
1. SRP violado: src/infrastructure/readers/pdf_reader.py:19 - Classe com 12 métodos
2. SRP violado: src/infrastructure/readers/excel_reader.py:24 - Classe com 16 métodos
3. SRP violado: src/infrastructure/readers/base_reader.py:21 - Classe com 12 métodos
4. Ferramenta duplo não disponível
5. Ferramenta radon não disponível

## Recomendações
- Refatorar classes com muitas responsabilidades
- Reduzir duplicação de código e complexidade