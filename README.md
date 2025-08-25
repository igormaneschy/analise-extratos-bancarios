# Sistema de Análise de Extratos Bancários

Sistema Python para análise automatizada de extratos bancários com extração de dados, categorização de transações e geração de relatórios financeiros.

## 🎯 Objetivo

Automatizar a análise de extratos bancários em PDF, Excel e CSV, extraindo informações relevantes como:
- **Transações**: Data, valor, descrição, tipo
- **Saldos**: Inicial, final, médio do período
- **Categorização**: Classificação automática por tipo de gasto
- **Relatórios**: Resumos e análises financeiras

## ✨ Funcionalidades

### 📄 **Processamento de PDFs, Excel e CSV**
- Extração de texto de extratos bancários em PDF
- Leitura de extratos em formato Excel (XLSX)
- Leitura de extratos em formato CSV
- Suporte a múltiplos formatos de bancos europeus
- Detecção automática de layout

### 🏷️ **Categorização Inteligente**
- Classificação automática de transações
- Categorias personalizáveis
- Detecção de padrões de gasto

### 📊 **Análise Financeira**
- Resumo de receitas e despesas
- Análise de fluxo de caixa
- Identificação de tendências de gastos
- Alertas financeiros personalizados

### 📈 **Visualização e Relatórios**
- Relatórios em formato texto
- Relatórios em formato Markdown
- Visualizações no terminal com Rich
- Exportação de dados

## 🚀 Começando

### 📋 Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes do Python)

### 🔧 Instalação

1. Clone o repositório:
```bash
git clone <url-do-repositorio>
cd sistema-analise-extratos
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

### 📖 Uso

#### Análise de Extratos

```bash
# Analisar um extrato PDF
python main.py analyze extrato.pdf

# Analisar um extrato Excel
python main.py analyze extrato.xlsx

# Analisar um extrato CSV
python main.py analyze extrato.csv

# Salvar relatório em arquivo
python main.py analyze extrato.pdf --output relatorio.txt

# Gerar relatório em Markdown
python main.py analyze extrato.xlsx --format markdown --output relatorio.md
```

#### Criar Instruções de Uso

```bash
# Gera um arquivo com instruções de uso
python main.py sample instrucoes.txt
```

## 📁 Estrutura de Arquivos CSV

Para que o sistema possa processar corretamente um arquivo CSV, ele deve conter as seguintes colunas:

### Colunas Obrigatórias:
- **Data da transação** (formatos aceitos: DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD)
- **Descrição da transação**
- **Valor da transação** (positivo para receitas, negativo para despesas)

### Colunas Opcionais:
- **Saldo após a transação**
- **Número da conta**
- **Saldo inicial/final**

### Exemplo de Estrutura:

```csv
data,descricao,valor,saldo
01/01/2023,Salário Janeiro,2500.00,2500.00
02/01/2023,Supermercado,-150.50,2349.50
03/01/2023,Conta de Luz,-80.00,2269.50
```

## 💰 Moedas Suportadas

O sistema detecta automaticamente a moeda do extrato:
- EUR (Euro) - Padrão
- USD (Dólar Americano)
- BRL (Real Brasileiro)
- GBP (Libra Esterlina)
- JPY (Iene Japonês)
- CHF (Franco Suíço)
- CAD (Dólar Canadense)
- AUD (Dólar Australiano)

## 🧪 Testes

Execute os testes para verificar a integridade do sistema:

```bash
# Executar todos os testes
python -m pytest tests/

# Executar testes com cobertura
python -m pytest --cov=src tests/
```

## 🛠️ Tecnologias Utilizadas

- **Python 3.8+**
- **pdfplumber** - Extração de texto de PDFs
- **pandas** - Processamento de dados Excel e CSV
- **rich** - Interface de terminal avançada
- **click** - Interface de linha de comando
- **reportlab** - Geração de relatórios PDF (futuro)
- **matplotlib** - Visualizações gráficas (futuro)

## 📦 Estrutura do Projeto

```
sistema-analise-extratos/
├── src/
│   ├── domain/          # Modelos e interfaces de domínio
│   ├── application/     # Casos de uso
│   ├── infrastructure/  # Implementações concretas
│   └── presentation/    # Interface com o usuário
├── tests/               # Testes automatizados
├── data/                # Dados de exemplo
├── main.py              # Ponto de entrada CLI
└── requirements.txt     # Dependências
```

## 📈 Roadmap

- [x] Processamento de PDFs
- [x] Processamento de Excel
- [x] Processamento de CSV
- [x] Categorização automática
- [x] Geração de relatórios
- [ ] Interface web
- [ ] API REST
- [ ] Machine Learning para categorização
- [ ] Suporte a mais bancos
- [ ] Visualizações gráficas
- [ ] Exportação para diferentes formatos

## 🤝 Contribuindo

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 📧 Contato

Seu Nome - [@seu_perfil](https://twitter.com/seu_perfil) - email@example.com

Link do Projeto: [https://github.com/seu_usuario/sistema-analise-extratos](https://github.com/seu_usuario/sistema-analise-extratos)