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

## 🚀 Início Rápido

### 1. Instalação de Dependências

```bash
pip install -r requirements.txt
```

### 2. Configuração do Ambiente

```bash
# Criar ambiente virtual (opcional mas recomendado)
python -m venv venv

# Ativar ambiente virtual
# No Windows:
venv\Scripts\activate
# No macOS/Linux:
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 3. Executar Testes

```bash
# Executar todos os testes
pytest tests/ -v

# Executar testes específicos
python test_cache.py
python test_model_loading.py
```

## 🤖 Uso do Agente

### Configuração Inicial

```bash
# Configurar contexto do agente
python scripts/setup_agent_context.py
```

### Ferramentas Disponíveis

1. **Servidor MCP** - Para integração com ferramentas externas:
   ```bash
   python mcp_server.py
   ```

2. **Sistema de Cache** - Para otimizar buscas:
   ```bash
   python test_cache.py
   ```

3. **Indexador de Código** - Para busca semântica:
   ```bash
   python reindexProject.py
   ```

4. **Regras do Projeto** - Diretrizes para o comportamento do agente:
   - Histórico de desenvolvimento automático
   - Priorização de arquivos recentes
   - Padrões de codificação

### Comandos CLI

```bash
# Mostrar ajuda
python main.py --help

# Analisar um extrato bancário
python main.py analyze data/samples/extrato_exemplo.pdf

# Criar arquivo de exemplo
python main.py sample

# Mostrar informações do sistema
python main.py info
```

## 🧪 Testes

O projeto inclui uma suíte completa de testes:

```bash
# Executar todos os testes
pytest tests/ -v

# Testes específicos
python test_cache.py          # Testa o sistema de cache
python test_model_loading.py  # Testa carregamento do modelo
python test_embeddings.py     # Testa o sistema de embeddings
```

## 📁 Estrutura de Diretórios

```
analise-extratos-bancarios/
├── src/
│   ├── domain/              # Modelos e interfaces
│   ├── application/         # Casos de uso
│   ├── infrastructure/      # Implementações concretas
│   │   ├── readers/         # Leitores de diferentes formatos
│   │   ├── categorizers/    # Categorizadores de transações
│   │   ├── analyzers/       # Analisadores de extratos
│   │   └── reports/         # Geradores de relatórios
│   ├── presentation/        # Interface CLI
│   └── utils/               # Utilitários (cache, embeddings, etc.)
├── tests/                   # Testes unitários e de integração
├── data/                    # Dados de exemplo e testes
│   └── samples/             # Exemplos de extratos
├── docs/                    # Documentação
├── scripts/                 # Scripts auxiliares
└── .codellm/                # Configurações do agente
    └── rules/               # Regras para o comportamento do agente
```

## 🛠️ Desenvolvimento

### Regras do Agente

O projeto utiliza um sistema de regras para guiar o comportamento do agente:

- **Histórico de desenvolvimento automático** (.codellm/rules/01-historico_desenvolvimento.mdc)
- **Priorização de arquivos recentes** (.codellm/rules/02-priorizacao_recentes.mdc)
- **Padrões de codificação** (.codellm/rules/03-padroes_codificacao.mdc)

### Contribuindo

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.