# Análise de Extratos Bancários com IA

Sistema Python para análise automatizada de extratos bancários utilizando inteligência artificial para validação, categorização e geração de insights financeiros.

## 🎯 Objetivo

Ler e processar extratos bancários em diversos formatos (PDF, Excel, CSV) para:
- Extrair transações automaticamente
- Categorizar despesas e receitas
- Identificar padrões de gastos
- Gerar relatórios e alertas personalizados
- Detectar anomalias e transações suspeitas

## 🏗️ Arquitetura

O projeto segue os princípios da Clean Architecture:

```
analise-extratos-bancarios/
├── src/
│   ├── domain/          # Entidades e regras de negócio
│   ├── application/     # Casos de uso e serviços
│   ├── infrastructure/  # Implementações (leitores, parsers)
│   ├── presentation/    # Interface CLI/API
│   └── utils/          # Utilitários gerais
├── tests/              # Testes unitários e integração
├── data/               # Dados de exemplo
└── docs/               # Documentação
```

## 🚀 Instalação

```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente (Windows)
venv\Scripts\activate

# Ativar ambiente (Linux/Mac)
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

## 📋 Funcionalidades

### Fase 1 - MVP (Atual)
- [x] Estrutura básica do projeto
- [x] Leitura de PDFs de extratos
- [x] Extração de transações básicas
- [x] Modelo de dados para transações
- [ ] Análise simples (totais, categorias)
- [ ] Relatório básico em texto

### Fase 2 - Integração IA
- [ ] Integração com OpenAI/Claude para categorização
- [ ] Detecção de padrões de gastos
- [ ] Análise de anomalias
- [ ] Sugestões de economia

### Fase 3 - Expansão
- [ ] Suporte para múltiplos bancos
- [ ] Dashboard web
- [ ] Exportação de relatórios (PDF/Excel)
- [ ] Alertas automáticos

## 🔧 Uso Básico

```python
# Exemplo de uso simples
from src.application.extract_analyzer import ExtractAnalyzer

analyzer = ExtractAnalyzer()
result = analyzer.analyze_file("extrato.pdf")
print(result.summary)
```

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT.