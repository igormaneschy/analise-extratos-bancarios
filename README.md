# Sistema de Análise de Extratos Bancários

Uma aplicação Python robusta e modular para análise automatizada de extratos bancários, desenvolvida com arquitetura limpa (Clean Architecture) e suporte a múltiplos formatos de arquivo.

## 🚀 Funcionalidades

### 📊 Análise Completa de Extratos
- **Extração automática** de transações de PDF, Excel e CSV
- **Categorização inteligente** de transações baseada em palavras-chave
- **Cálculo de saldos** e fluxos financeiros
- **Análise mensal** e por categoria
- **Detecção automática de moeda** (EUR, USD, BRL, GBP, JPY, CHF, CAD, AUD)

### 📈 Relatórios e Insights
- **Relatórios detalhados** em texto ou Markdown
- **Alertas inteligentes** sobre padrões financeiros
- **Insights automatizados** sobre gastos e economia
- **Resumos mensais** e por categoria
- **Interface CLI rica** com Rich para melhor experiência

### 🔧 Arquitetura Modular
- **Arquitetura Limpa** (Clean Architecture) com separação clara de responsabilidades
- **Interfaces bem definidas** para extensibilidade
- **Injeção de dependências** para testabilidade
- **Suporte a múltiplos leitores** (PDF, Excel, CSV)
- **Categorizadores plugáveis** para diferentes regras

## 🏗️ Arquitetura

O projeto segue os princípios da Clean Architecture:

```
src/
├── domain/           # Regras de negócio e modelos
│   ├── models.py     # Entidades (Transaction, BankStatement, etc.)
│   ├── interfaces.py # Contratos abstratos
│   └── exceptions.py # Exceções de domínio
├── application/      # Casos de uso
│   └── use_cases.py  # Lógica de aplicação
├── infrastructure/   # Implementações concretas
│   ├── readers/      # Leitores de arquivos (PDF, Excel, CSV)
│   ├── analyzers/    # Analisadores de extratos
│   ├── categorizers/ # Categorizadores de transações
│   └── reports/      # Geradores de relatórios
└── utils/            # Utilitários
    └── currency_utils.py # Manipulação de moedas
```

## 📋 Pré-requisitos

- Python 3.8+
- pip para gerenciamento de dependências

## 🛠️ Instalação

1. **Clone o repositório:**
   ```bash
   git clone <url-do-repositorio>
   cd analise-extratos-bancarios
   ```

2. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Instalação opcional para PDFs complexos:**
   ```bash
   pip install PyPDF2 pdfplumber
   ```

## 📖 Uso

### Comando Básico

```bash
python main.py analyze caminho/para/extrato.pdf
```

### Opções Disponíveis

```bash
python main.py analyze --help
```

- `--output, -o`: Caminho para salvar o relatório
- `--format, -f`: Formato do relatório (text/markdown)
- `--help`: Mostra ajuda

### Exemplos de Uso

#### Analisar PDF
```bash
python main.py analyze data/samples/20250507_Extrato_Integrado.pdf
```

#### Analisar Excel
```bash
python main.py analyze data/samples/extmovs_bpi2108102947.xlsx
```

#### Analisar CSV
```bash
python main.py analyze data/samples/extrato_exemplo.csv
```

#### Salvar relatório em arquivo
```bash
python main.py analyze extrato.pdf --output relatorio.txt
```

#### Gerar relatório em Markdown
```bash
python main.py analyze extrato.pdf --format markdown --output relatorio.md
```

### Criar Arquivo de Instruções

```bash
python main.py sample instrucoes.md
```

## 📄 Formatos Suportados

### CSV
Estrutura esperada:
```csv
data,descricao,valor,saldo
01/01/2023,Salário Janeiro,2500.00,2500.00
02/01/2023,Supermercado,-150.50,2349.50
```

**Colunas obrigatórias:**
- `data` (DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD)
- `descricao` (descrição da transação)
- `valor` (positivo para receitas, negativo para despesas)

**Colunas opcionais:**
- `saldo` (saldo após transação)
- `conta` (número da conta)

### Excel
- Suporte a múltiplas planilhas
- Detecção automática de cabeçalhos
- Compatível com .xlsx e .xls

### PDF
- Extração de texto estruturado
- Suporte a PDFs de bancos europeus
- Detecção de tabelas e dados tabulares

## 💰 Moedas Suportadas

- **EUR** (€) - Euro
- **USD** ($) - Dólar Americano
- **BRL** (R$) - Real Brasileiro
- **GBP** (£) - Libra Esterlina
- **JPY** (¥) - Iene Japonês
- **CHF** (CHF) - Franco Suíço
- **CAD** (C$) - Dólar Canadense
- **AUD** (A$) - Dólar Australiano

## 📊 Categorias de Transação

- **ALIMENTACAO**: Alimentação e restaurantes
- **TRANSPORTE**: Transporte público, combustível
- **MORADIA**: Aluguel, condomínio, manutenção
- **SAUDE**: Médicos, medicamentos, seguros
- **EDUCACAO**: Cursos, livros, mensalidades
- **LAZER**: Entretenimento, hobbies
- **COMPRAS**: Compras gerais
- **SERVICOS**: Serviços diversos
- **TRANSFERENCIA**: Transferências entre contas
- **INVESTIMENTO**: Investimentos e aplicações
- **SALARIO**: Receitas salariais
- **OUTROS**: Outras categorias

## 🧪 Testes

Execute os testes com:

```bash
# Todos os testes
pytest

# Com cobertura
pytest --cov=src --cov-report=html

# Testes específicos
pytest tests/unit/test_models.py
```

## 📁 Estrutura do Projeto

```
├── main.py                 # Ponto de entrada CLI
├── requirements.txt        # Dependências Python
├── pytest.ini            # Configuração de testes
├── data/
│   └── samples/          # Arquivos de exemplo
├── src/
│   ├── domain/           # Camada de domínio
│   ├── application/      # Casos de uso
│   ├── infrastructure/   # Implementações
│   └── utils/            # Utilitários
├── tests/                # Testes automatizados
└── scripts/              # Scripts auxiliares
```

## 🔧 Desenvolvimento

### Adicionar Novo Leitor

1. Implemente a interface `StatementReader` em `src/domain/interfaces.py`
2. Crie classe concreta em `src/infrastructure/readers/`
3. Registre no `ExtractAnalyzer` em `use_cases.py`

### Adicionar Nova Categoria

1. Adicione ao enum `TransactionCategory` em `models.py`
2. Atualize o categorizador em `categorizers/`

### Adicionar Suporte a Nova Moeda

1. Adicione símbolo em `CURRENCY_SYMBOLS` em `currency_utils.py`
2. Adicione padrão de detecção em `CURRENCY_PATTERNS`

## 📈 Exemplos de Saída

### Resumo no Terminal
```
✓ Análise concluída!

📊 Total de transações: 45
💰 Receitas: € 3.250,00
💸 Despesas: € 2.180,50
📈 Saldo: € 1.069,50
```

### Alertas
```
⚠️  Alertas
   Atenção: Despesas superaram receitas em € 150,00
   ⚠️ 5 transações não foram categorizadas automaticamente
   ⚠️ Gastos com ALIMENTACAO representam 35.2% do total
```

### Insights
```
💡 Insights
   Maior categoria de gastos: ALIMENTACAO (€ 768,50 - 35.2%)
   💡 Média diária de gastos: € 72,68
   💡 68% das suas despesas são menores que € 45,00
```

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

## 🆘 Suporte

Para suporte ou dúvidas:
- Abra uma issue no GitHub
- Consulte a documentação em `python main.py sample instrucoes.md`

---

**Desenvolvido com ❤️ para facilitar a análise financeira pessoal**