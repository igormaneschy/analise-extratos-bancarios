# Sistema de Análise de Extratos Bancários

Sistema Python para análise automatizada de extratos bancários com extração de dados, categorização de transações e geração de relatórios financeiros.

## 🎯 Objetivo

Automatizar a análise de extratos bancários em PDF, extraindo informações relevantes como:
- **Transações**: Data, valor, descrição, tipo
- **Saldos**: Inicial, final, médio do período
- **Categorização**: Classificação automática por tipo de gasto
- **Relatórios**: Resumos e análises financeiras

## ✨ Funcionalidades

### 📄 **Processamento de PDFs**
- Extração de texto de extratos bancários
- Suporte a múltiplos formatos de bancos
- Detecção automática de layout

### 🏷️ **Categorização Inteligente**
- Classificação automática de transações
- Categorias personalizáveis
- Detecção de padrões de gasto

### 📊 **Análise Financeira**
- Resumo de receitas e despesas
- Análise de fluxo de caixa
- Identificação de gastos recorrentes
- Relatórios por categoria

### 📈 **Relatórios**
- Exportação em múltiplos formatos
- Gráficos e visualizações
- Comparativos mensais

## 🚀 Instalação

### Pré-requisitos
- Python 3.8+
- pip

### Instalação das Dependências
```bash
pip install -r requirements.txt
```

### Dependências Principais
- **PyPDF2**: Extração de texto de PDFs
- **pandas**: Manipulação de dados
- **matplotlib**: Geração de gráficos
- **reportlab**: Criação de relatórios PDF

## 💻 Uso Básico

### Análise de um Extrato
```python
from src.application.extract_analyzer import ExtractAnalyzer

analyzer = ExtractAnalyzer()
result = analyzer.analyze_file("extrato.pdf")
print(result.summary)
```

### Via Linha de Comando
```bash
python main.py --file extrato.pdf --output relatorio.pdf
```

## 📁 Estrutura do Projeto

```
├── README.md                    # Este arquivo
├── requirements.txt             # Dependências
├── main.py                      # Ponto de entrada
├── src/                        # Código fonte
│   ├── domain/                 # Entidades e regras de negócio
│   ├── application/            # Casos de uso e serviços
│   ├── infrastructure/         # Implementações (leitores, parsers)
│   ├── presentation/           # Interface CLI/API
│   └── utils/                  # Utilitários
├── tests/                      # Testes
├── data/                       # Dados de exemplo
│   └── samples/               # Extratos de exemplo
├── scripts/                    # Scripts utilitários
└── dev_history.md             # Histórico de desenvolvimento
```

## 🧪 Testes

```bash
# Executar todos os testes
python -m pytest tests/

# Testes com cobertura
python -m pytest tests/ --cov=src
```

## 📊 Exemplo de Uso

### 1. Criar Extrato de Exemplo
```bash
python scripts/create_sample_pdf.py
```

### 2. Analisar Extrato
```python
from src.application.extract_analyzer import ExtractAnalyzer

# Inicializar analisador
analyzer = ExtractAnalyzer()

# Analisar arquivo
result = analyzer.analyze_file("data/samples/extrato_exemplo.pdf")

# Visualizar resultados
print(f"Total de transações: {len(result.transactions)}")
print(f"Saldo inicial: R$ {result.initial_balance:.2f}")
print(f"Saldo final: R$ {result.final_balance:.2f}")

# Categorias mais frequentes
for category, count in result.category_summary.items():
    print(f"{category}: {count} transações")
```

### 3. Gerar Relatório
```python
# Gerar relatório PDF
report = analyzer.generate_report(result)
report.save("relatorio_financeiro.pdf")

# Exportar dados para Excel
result.to_excel("transacoes.xlsx")
```

## 🔧 Configuração

### Personalizar Categorias
Edite o arquivo `src/domain/categories.py` para adicionar suas próprias categorias:

```python
CATEGORIES = {
    "alimentacao": ["supermercado", "restaurante", "lanchonete"],
    "transporte": ["uber", "taxi", "combustivel", "estacionamento"],
    "saude": ["farmacia", "hospital", "clinica"],
    # Adicione suas categorias aqui
}
```

### Configurar Bancos Suportados
Adicione novos parsers em `src/infrastructure/parsers/` para suportar diferentes bancos.

## 📈 Roadmap

- [ ] **Interface Web**: Dashboard interativo
- [ ] **API REST**: Endpoints para integração
- [ ] **Machine Learning**: Categorização mais inteligente
- [ ] **Múltiplos Bancos**: Suporte expandido
- [ ] **Exportação**: Mais formatos de saída
- [ ] **Alertas**: Notificações de gastos incomuns

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 🆘 Suporte

- **Issues**: Reporte bugs ou solicite funcionalidades
- **Documentação**: Consulte a pasta `src/` para detalhes técnicos
- **Exemplos**: Veja `data/samples/` para arquivos de exemplo

---

**Desenvolvido para simplificar a análise de extratos bancários e fornecer insights financeiros valiosos.**