# 🚀 Quick Start - Como Usar as Regras em Outros Projetos

Este guia mostra como copiar e adaptar as regras de desenvolvimento para qualquer projeto.

## 📋 Pré-requisitos

- Projeto com estrutura de diretórios organizada
- Editor que suporte regras Cursor (ou similar)
- Conhecimento básico da linguagem do projeto

## 🎯 Método Rápido (Recomendado)

### **Passo 1: Copiar Regras Genéricas**
```bash
# Copiar regras genéricas para o novo projeto
cp rules_generic/*.mdc novo_projeto/.cursor/rules/
```

### **Passo 2: Adaptar para o Projeto**
```bash
# Editar exemplos de código para o domínio específico
# Ajustar comandos de teste para a linguagem
# Modificar estrutura de diretórios se necessário
```

### **Passo 3: Validar**
```bash
# Copiar ferramentas de validação
cp scripts/ novo_projeto/scripts/

# Executar validação
cd novo_projeto
python scripts/validate_rules.py
```

## 🔧 Adaptações por Linguagem

### **Python**
```yaml
# .cursor/rules/clean_architecture.mdc
globs: ["src/**/*", "app/**/*", "domain/**/*"]

# Comandos de teste
python -m pytest tests/unit/ -v
```

### **Node.js**
```yaml
# .cursor/rules/clean_architecture.mdc
globs: ["src/**/*", "lib/**/*", "packages/**/*"]

# Comandos de teste
npm test
```

### **.NET**
```yaml
# .cursor/rules/clean_architecture.mdc
globs: ["src/**/*", "app/**/*", "core/**/*"]

# Comandos de teste
dotnet test
```

### **Java**
```yaml
# .cursor/rules/clean_architecture.mdc
globs: ["src/**/*", "app/**/*", "domain/**/*"]

# Comandos de teste
mvn test
```

### **Go**
```yaml
# .cursor/rules/clean_architecture.mdc
globs: ["src/**/*", "internal/**/*", "pkg/**/*"]

# Comandos de teste
go test ./...
```

## 📝 Exemplos de Adaptação

### **1. Exemplos de Código**

#### **Antes (Domínio Bancário):**
```python
class BankStatement:
    bank_name: str
    transactions: List[Transaction]
```

#### **Depois (E-commerce):**
```python
class Order:
    id: str
    customer_id: str
    items: List[OrderItem]
```

#### **Depois (Sistema de Saúde):**
```python
class Patient:
    id: str
    name: str
    medical_records: List[MedicalRecord]
```

### **2. Comandos de Teste**

#### **Python:**
```bash
python -m pytest tests/unit/ -v
python -m pytest tests/unit/ --cov=src --cov-report=term-missing
```

#### **Node.js:**
```bash
npm test
npm run test:coverage
```

#### **.NET:**
```bash
dotnet test
dotnet test --collect:"XPlat Code Coverage"
```

#### **Java:**
```bash
mvn test
mvn test jacoco:report
```

#### **Go:**
```bash
go test ./...
go test -cover ./...
```

### **3. Estrutura de Diretórios**

#### **Python (Atual):**
```
src/
├── domain/
├── application/
├── infrastructure/
└── presentation/
```

#### **Node.js:**
```
src/
├── domain/
├── application/
├── infrastructure/
└── presentation/
```

#### **.NET:**
```
src/
├── Core/
├── Application/
├── Infrastructure/
└── Presentation/
```

#### **Java:**
```
src/main/java/
├── domain/
├── application/
├── infrastructure/
└── presentation/
```

#### **Go:**
```
internal/
├── domain/
├── application/
├── infrastructure/
└── presentation/
```

## 🛠️ Ferramentas de Validação

### **Copiar Ferramentas**
```bash
# Copiar scripts de validação
cp scripts/validate_rules.py novo_projeto/scripts/
cp scripts/metrics.py novo_projeto/scripts/
cp scripts/validate_history.sh novo_projeto/scripts/
cp scripts/generate_history_entry.sh novo_projeto/scripts/
```

### **Adaptar Scripts**
```python
# validate_rules.py - Ajustar caminhos se necessário
PROJECT_ROOT = Path(".")  # Ajustar para estrutura do projeto
```

### **Executar Validação**
```bash
# Validar conformidade
python scripts/validate_rules.py

# Calcular métricas
python scripts/metrics.py

# Validar histórico
./scripts/validate_history.sh
```

## 📚 Templates de Histórico

### **Adaptar Nome do Arquivo**
```bash
# Atual
dev_history.md

# Adaptar para:
CHANGELOG.md
HISTORY.md
DEVELOPMENT_LOG.md
```

### **Adaptar Templates**
```markdown
# Template genérico
[{{DATA_ATUAL}}] - {{NOME_AUTOR}}
Arquivos: {{LISTA_ARQUIVOS}}
Ação/Tipo: [Correção | Melhoria | Refatoração | Bug | Documentação | Configuração | Teste]
Descrição: {{BREVE_DESCRICAO}}

# Adaptar para o contexto do projeto
# - Adicionar campos específicos
# - Modificar formato de data
# - Incluir metadados específicos
```

## 🎯 Checklist de Adaptação

### **✅ Obrigatório:**
- [ ] Copiar regras genéricas
- [ ] Adaptar exemplos de código para o domínio
- [ ] Ajustar comandos de teste para a linguagem
- [ ] Modificar estrutura de diretórios
- [ ] Testar ferramentas de validação

### **✅ Opcional:**
- [ ] Adaptar nomes de arquivos
- [ ] Personalizar templates de histórico
- [ ] Adicionar campos específicos do projeto
- [ ] Configurar CI/CD para validação automática

## 🚨 Problemas Comuns

### **1. Comandos de Teste Não Funcionam**
```bash
# Verificar se a linguagem/framework está instalado
python --version
node --version
dotnet --version
java -version
go version
```

### **2. Estrutura de Diretórios Diferente**
```bash
# Ajustar globs nas regras
# .cursor/rules/clean_architecture.mdc
globs: ["src/**/*", "app/**/*", "domain/**/*"]
```

### **3. Ferramentas de Validação Não Funcionam**
```bash
# Instalar dependências Python
pip install ast

# Verificar permissões dos scripts
chmod +x scripts/*.sh
```

## 📞 Suporte

Para dúvidas ou problemas:
1. Verificar logs de erro
2. Consultar documentação das regras
3. Usar versões genéricas como base
4. Adaptar gradualmente para o projeto específico

## 🎉 Resultado Esperado

Após a adaptação, você terá:
- ✅ Regras de desenvolvimento padronizadas
- ✅ Ferramentas de validação funcionando
- ✅ Métricas de conformidade
- ✅ Histórico de desenvolvimento estruturado
- ✅ Qualidade de código consistente

**Tempo estimado de adaptação: 15-30 minutos** ⏱️
