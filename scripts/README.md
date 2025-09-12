# 🛠️ Ferramentas de Validação das Regras

Este diretório contém ferramentas para validar e monitorar a conformidade com as regras do projeto.

## 📋 Ferramentas Disponíveis

### 1. **validate_rules.py** - Validador Principal
Valida conformidade com todas as regras do projeto.

```bash
python scripts/validate_rules.py
```

**Funcionalidades:**
- ✅ Validação de Clean Architecture
- ✅ Validação de princípios SOLID
- ✅ Validação de DRY/KISS/YAGNI
- ✅ Validação de política de testes
- ✅ Validação de histórico de desenvolvimento
- 📊 Gera relatório detalhado

### 2. **metrics.py** - Calculadora de Métricas
Calcula scores de conformidade e gera dashboard.

```bash
python scripts/metrics.py
```

**Funcionalidades:**
- 📊 Calcula scores individuais por regra
- 📈 Gera dashboard visual
- 💾 Salva métricas em JSON
- 🎯 Score geral de conformidade

### 3. **generate_history_entry.sh** - Gerador de Histórico
Gera entradas automáticas no dev_history.md.

```bash
./scripts/generate_history_entry.sh <tipo> <descrição> [autor]
```

**Tipos disponíveis:**
- `bug` - Correção de bug
- `feat` - Nova funcionalidade
- `refactor` - Refatoração
- `test` - Adição de testes
- `docs` - Documentação
- `config` - Configuração

**Exemplos:**
```bash
./scripts/generate_history_entry.sh bug "Corrige parsing de valores negativos"
./scripts/generate_history_entry.sh feat "Adiciona suporte a Excel" "João Silva"
./scripts/generate_history_entry.sh refactor "Melhora arquitetura de readers"
```

### 4. **validate_history.sh** - Validador de Histórico
Valida formato e completude do dev_history.md.

```bash
./scripts/validate_history.sh
```

**Funcionalidades:**
- ✅ Verifica formato das entradas
- 📅 Valida datas
- 🔍 Verifica seções obrigatórias
- 📊 Estatísticas de completude

## 🚀 Uso Rápido

### Validação Completa
```bash
# Executar todas as validações
python scripts/validate_rules.py

# Calcular métricas
python scripts/metrics.py

# Validar histórico
./scripts/validate_history.sh
```

### Geração de Histórico
```bash
# Gerar entrada para bug fix
./scripts/generate_history_entry.sh bug "Corrige erro de parsing"

# Gerar entrada para nova funcionalidade
./scripts/generate_history_entry.sh feat "Adiciona suporte a PDF"
```

## 📊 Interpretação dos Scores

### **Clean Architecture (0-100%)**
- **90-100%**: Excelente separação de camadas
- **80-89%**: Boa separação, pequenas melhorias
- **60-79%**: Separação adequada, refatoração necessária
- **0-59%**: Violações graves, refatoração urgente

### **SOLID (0-100%)**
- **90-100%**: Princípios bem aplicados
- **80-89%**: Boa aplicação, pequenos ajustes
- **60-79%**: Aplicação parcial, melhorias necessárias
- **0-59%**: Violações graves, refatoração urgente

### **DRY/KISS/YAGNI (0-100%)**
- **90-100%**: Código limpo e eficiente
- **80-89%**: Boa qualidade, pequenas melhorias
- **60-79%**: Qualidade adequada, refatoração necessária
- **0-59%**: Código complexo, refatoração urgente

### **Testes (0-100%)**
- **90-100%**: Excelente cobertura
- **80-89%**: Boa cobertura, pequenos ajustes
- **60-79%**: Cobertura adequada, mais testes necessários
- **0-59%**: Cobertura insuficiente, testes urgentes

### **Histórico (0-100%)**
- **90-100%**: Histórico completo e atualizado
- **80-89%**: Histórico bom, pequenas atualizações
- **60-79%**: Histórico adequado, mais entradas necessárias
- **0-59%**: Histórico incompleto, atualização urgente

## 🔧 Dependências

### Python
```bash
pip install ast
```

### Ferramentas Externas (Opcionais)
```bash
# Para análise de duplicação
pip install duplo

# Para análise de complexidade
pip install radon

# Para cobertura de testes
pip install pytest-cov
```

## 📁 Arquivos Gerados

- **validation_report.md**: Relatório detalhado de validação
- **metrics.json**: Métricas em formato JSON
- **duplo-report.html**: Relatório de duplicação (se disponível)

## 🎯 Metas de Conformidade

- **Score Geral**: ≥ 80%
- **Clean Architecture**: ≥ 80%
- **SOLID**: ≥ 80%
- **DRY/KISS/YAGNI**: ≥ 80%
- **Testes**: ≥ 80%
- **Histórico**: ≥ 80%

## 🚨 Troubleshooting

### Erro: "Ferramenta não encontrada"
```bash
# Instalar ferramentas opcionais
pip install duplo radon pytest-cov
```

### Erro: "Permissão negada"
```bash
# Tornar scripts executáveis
chmod +x scripts/*.sh
```

### Erro: "Timeout na execução"
```bash
# Aumentar timeout ou executar individualmente
python scripts/validate_rules.py --timeout 120
```

## 🌍 Genericidade das Regras

### **Nível de Genericidade: 95%**

As regras criadas são **genéricas o suficiente** para serem utilizadas em qualquer projeto, com apenas pequenos ajustes necessários.

#### **✅ Regras Completamente Genéricas (100%):**
- 🏗️ **Clean Architecture**: Agnóstica de tecnologia e domínio
- 🔧 **Princípios SOLID**: Aplicável a qualquer linguagem OOP
- 🎯 **DRY/KISS/YAGNI**: Filosofia universal de desenvolvimento
- 🧪 **Política de Testes**: Conceitos aplicáveis a qualquer framework
- 📝 **Histórico de Desenvolvimento**: Formato universal em Markdown

#### **⚠️ Adaptações Necessárias (5%):**
- **Exemplos de código**: Adaptar para o domínio específico
- **Comandos de teste**: Ajustar para a linguagem/framework
- **Estrutura de diretórios**: Adaptar para organização do projeto

### **📁 Versões Disponíveis:**

| Versão | Localização | Uso |
|--------|-------------|-----|
| **Específica** | `.cursor/rules/` | Projeto atual (domínio bancário) |
| **Genérica** | `rules_generic/` | Qualquer projeto |

## 🚀 Como Copiar Regras para Outros Projetos

### **Método 1: Copiar Regras Genéricas (Recomendado)**

```bash
# 1. Copiar regras genéricas
cp rules_generic/*.mdc .cursor/rules/

# 2. Adaptar para o projeto específico
# - Editar exemplos de código para o domínio
# - Ajustar comandos de teste para a linguagem
# - Modificar estrutura de diretórios se necessário
```

### **Método 2: Copiar Regras Específicas e Adaptar**

```bash
# 1. Copiar regras atuais
cp .cursor/rules/*.mdc novo_projeto/.cursor/rules/

# 2. Adaptar exemplos
# - Substituir BankStatement por entidades do domínio
# - Ajustar comandos pytest para a linguagem
# - Modificar estrutura de diretórios
```

### **Método 3: Usar Script de Criação**

```bash
# 1. Executar script de criação
python scripts/create_generic_rules.py

# 2. Copiar regras geradas
cp rules_generic/*.mdc novo_projeto/.cursor/rules/

# 3. Personalizar para o projeto
```

## 📋 Checklist de Adaptação

### **✅ Adaptações Obrigatórias:**

#### **1. Exemplos de Código**
```python
# Substituir exemplos específicos
# ANTES (domínio bancário):
class BankStatement:
    bank_name: str
    transactions: List[Transaction]

# DEPOIS (domínio específico):
class User:
    id: str
    email: str
    profile: UserProfile
```

#### **2. Comandos de Teste**
```bash
# Python (atual)
python -m pytest tests/unit/ -v

# Node.js
npm test

# .NET
dotnet test

# Java
mvn test

# Go
go test ./...
```

#### **3. Estrutura de Diretórios**
```yaml
# Atual
globs: ["src/**/*", "app/**/*", "domain/**/*"]

# Adaptar para:
globs: ["src/**/*", "lib/**/*", "packages/**/*"]  # Node.js
globs: ["src/**/*", "app/**/*", "core/**/*"]      # .NET
globs: ["src/**/*", "internal/**/*", "pkg/**/*"]  # Go
```

### **✅ Adaptações Opcionais:**

#### **1. Nomes de Arquivos**
```bash
# Atual
dev_history.md

# Adaptar para:
CHANGELOG.md
HISTORY.md
DEVELOPMENT_LOG.md
```

#### **2. Templates de Histórico**
```markdown
# Adaptar templates para o contexto do projeto
# - Adicionar campos específicos
# - Modificar formato de data
# - Incluir metadados específicos
```

## 🛠️ Ferramentas de Adaptação

### **Script de Criação de Regras Genéricas**
```bash
# Criar versões genéricas das regras
python scripts/create_generic_rules.py

# Resultado: rules_generic/ com regras adaptáveis
```

### **Script de Validação Universal**
```bash
# Validar regras em qualquer projeto
python scripts/validate_rules.py

# Funciona com qualquer estrutura de projeto
```

### **Script de Métricas Universal**
```bash
# Calcular métricas de conformidade
python scripts/metrics.py

# Adapta-se automaticamente ao projeto
```

## 📚 Exemplos de Adaptação por Linguagem

### **Python**
```yaml
# .cursor/rules/clean_architecture.mdc
globs: ["src/**/*", "app/**/*", "domain/**/*"]
```

### **Node.js**
```yaml
# .cursor/rules/clean_architecture.mdc
globs: ["src/**/*", "lib/**/*", "packages/**/*"]
```

### **.NET**
```yaml
# .cursor/rules/clean_architecture.mdc
globs: ["src/**/*", "app/**/*", "core/**/*"]
```

### **Java**
```yaml
# .cursor/rules/clean_architecture.mdc
globs: ["src/**/*", "app/**/*", "domain/**/*"]
```

### **Go**
```yaml
# .cursor/rules/clean_architecture.mdc
globs: ["src/**/*", "internal/**/*", "pkg/**/*"]
```

## 🎯 Benefícios da Genericidade

### **✅ Vantagens:**
- **Reutilização**: Mesmas regras em múltiplos projetos
- **Consistência**: Padrões uniformes na organização
- **Manutenção**: Atualizações centralizadas
- **Onboarding**: Novos desenvolvedores já conhecem as regras
- **Qualidade**: Padrões testados e validados

### **⚠️ Considerações:**
- **Adaptação**: Pequenos ajustes necessários por projeto
- **Contexto**: Exemplos devem ser relevantes ao domínio
- **Ferramentas**: Comandos específicos por linguagem
- **Estrutura**: Organização de diretórios pode variar

## 📞 Suporte

Para dúvidas ou problemas com as ferramentas:
1. Verificar logs de erro
2. Executar validações individuais
3. Verificar dependências
4. Consultar documentação das regras
5. Usar versões genéricas para novos projetos
