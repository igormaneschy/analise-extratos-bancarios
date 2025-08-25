# Sistema de Análise de Extratos Bancários

Sistema Python para análise automatizada de extratos bancários com extração de dados, categorização de transações e geração de relatórios financeiros.

## 🎯 Objetivo

Automatizar a análise de extratos bancários em PDF e Excel, extraindo informações relevantes como:
- **Transações**: Data, valor, descrição, tipo
- **Saldos**: Inicial, final, médio do período
- **Categorização**: Classificação automática por tipo de gasto
- **Relatórios**: Resumos e análises financeiras

## ✨ Funcionalidades

### 📄 **Processamento de PDFs e Excel**
- Extração de texto de extratos bancários em PDF
- Leitura de extratos em formato Excel (XLSX)
- Suporte a múltiplos formatos de bancos europeus
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
- Exportação em múltiplos formatos (texto, Markdown)
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
- **openpyxl**: Leitura de arquivos Excel
- **pandas**: Manipulação de dados
- **matplotlib**: Geração de gráficos
- **reportlab**: Criação de relatórios PDF

## 📖 Uso

### Análise de Extrato
```bash
# Analisar um extrato em PDF
python main.py analyze data/samples/extrato.pdf

# Analisar um extrato em Excel
python main.py analyze data/samples/extrato.xlsx

# Salvar relatório em arquivo
python main.py analyze data/samples/extrato.pdf --output relatorio.txt

# Gerar relatório em Markdown
python main.py analyze data/samples/extrato.pdf --output relatorio.md --format markdown
```

### Informações do Sistema
```bash
# Ver informações sobre o sistema
python main.py info

# Criar arquivo de instruções de teste
python main.py sample
```

## 🏦 Bancos Suportados

O sistema suporta extratos de diversos bancos europeus, incluindo:

**Portugal:**
- Banco BPI
- Caixa Geral de Depósitos
- Banco Comercial Português
- Millennium BCP
- Novo Banco
- Banco Santander Totta

**Espanha:**
- Santander
- BBVA
- CaixaBank
- Banco Sabadell

**França:**
- BNP Paribas
- Crédit Agricole
- ING Bank

**Alemanha:**
- Deutsche Bank
- Commerzbank
- Sparkasse
- Volksbank

**Itália:**
- UniCredit
- Intesa Sanpaolo

**Países Baixos:**
- ING Bank
- ABN AMRO
- Rabobank

**Bélgica:**
- KBC Bank
- Belfius
- BNP Paribas Fortis

**Áustria:**
- Erste Bank
- Raiffeisen

**Suíça:**
- UBS
- Credit Suisse

**Reino Unido:**
- HSBC
- Barclays
- Lloyds
- NatWest

**Bancos Digitais:**
- Revolut
- Wise (TransferWise)
- N26
- Monzo
- Starling Bank

## 🛠️ Desenvolvimento

### Estrutura do Projeto
```
src/
├── domain/          # Modelos e interfaces do domínio
├── application/     # Casos de uso e lógica de aplicação
├── infrastructure/  # Implementações concretas
│   ├── readers/     # Leitores de diferentes formatos
│   ├── categorizers/ # Categorizadores de transações
│   ├── analyzers/   # Analisadores de extratos
│   └── reports/     # Geradores de relatórios
└── presentation/    # Interface com o usuário (CLI)
```

### Nota sobre Histórico de Desenvolvimento
- O registro de histórico (dev_history.md) é gerenciado exclusivamente pelas rules do CodeLLM em `.codellm/rules/01-historico_desenvolvimento.mdc`.
- O servidor MCP e os componentes em `mcp_system/` não escrevem nem leem o dev_history.md.
- A pasta `mcp_system/` é intencionalmente excluída do histórico pela regra.

### Adicionando Suporte a Novos Bancos

1. Atualize o arquivo `src/infrastructure/readers/pdf_reader_config.json` com padrões específicos do banco
2. Adicione padrões de nome do banco na lista `bank_name_patterns`
3. Teste com extratos reais do banco

### Criando Novos Leitores

Implemente a interface `StatementReader` no módulo `src.domain.interfaces`:

```python
class StatementReader(ABC):
    @abstractmethod
    def can_read(self, file_path: Path) -> bool:
        """Verifica se pode ler o arquivo."""
        pass
    
    @abstractmethod
    def read(self, file_path: Path) -> BankStatement:
        """Lê o arquivo e retorna um extrato."""
        pass
```

## 📋 Próximos Passos (Roadmap)

- [x] Suporte a múltiplos formatos de arquivo (PDF, Excel)
- [x] Expansão para bancos europeus
- [ ] Suporte a mais formatos (CSV, OFX)
- [ ] Integração com IA para categorização aprimorada
- [ ] Detecção automática de padrões de bancos
- [ ] Persistência das análises para histórico e modelo de aprendizagem
- [ ] Interface web com Flask/Django
- [ ] API REST para integração
- [ ] Internacionalização (português, inglês, espanhol)

## 🧪 Testes

```bash
# Executar testes
pytest

# Executar testes com cobertura
pytest --cov=src
```

## 📄 Licença

MIT License - veja o arquivo [LICENSE](LICENSE) para mais detalhes.