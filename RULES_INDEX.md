# 📋 Índice das Regras de Desenvolvimento

Este documento serve como índice para todas as regras de desenvolvimento do projeto.

## 🎯 Regras Principais

### **1. 🏗️ Clean Architecture**
- **Arquivo**: `.cursor/rules/clean_architecture.mdc`
- **Versão Genérica**: `rules_generic/clean_architecture.mdc`
- **Objetivo**: Manter separação clara de responsabilidades e dependências
- **Aplicação**: Estrutura de camadas (Domain, Application, Infrastructure, Presentation)

### **2. 🔧 Princípios SOLID**
- **Arquivo**: `.cursor/rules/solid.mdc`
- **Objetivo**: Promover design modular, extensível e de fácil manutenção
- **Aplicação**: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion

### **3. 🎯 DRY/KISS/YAGNI**
- **Arquivo**: `.cursor/rules/dry_kiss.mdc`
- **Objetivo**: Evitar duplicação de lógica e manter código simples
- **Aplicação**: Don't Repeat Yourself, Keep It Simple, You Aren't Gonna Need It

### **4. 🧪 Política de Testes**
- **Arquivo**: `.cursor/rules/testing.policy.mdc`
- **Objetivo**: Garantir cobertura adequada de testes
- **Aplicação**: Testes unitários, integração, regressão, debugging

### **5. 📝 Histórico de Desenvolvimento**
- **Arquivo**: `.cursor/rules/historicodev.mdc`
- **Objetivo**: Rastreabilidade e documentação de mudanças
- **Aplicação**: Templates, automação, validação de formato

## 🛠️ Ferramentas de Validação

### **Scripts de Validação**
- **`scripts/validate_rules.py`**: Validador principal de todas as regras
- **`scripts/metrics.py`**: Calculadora de métricas e dashboard
- **`scripts/validate_history.sh`**: Validador de formato do histórico
- **`scripts/generate_history_entry.sh`**: Gerador automático de entradas

### **Scripts de Utilidade**
- **`scripts/create_generic_rules.py`**: Criador de versões genéricas
- **`scripts/README.md`**: Documentação completa das ferramentas

## 📚 Documentação

### **Guias de Uso**
- **`QUICK_START_RULES.md`**: Guia rápido para usar em outros projetos
- **`scripts/README.md`**: Documentação detalhada das ferramentas
- **`RULES_INDEX.md`**: Este arquivo - índice de todas as regras

### **Versões Disponíveis**
- **Específica**: `.cursor/rules/` (domínio bancário)
- **Genérica**: `rules_generic/` (qualquer projeto)

## 🚀 Uso Rápido

### **Validação Completa**
```bash
# Executar todas as validações
python scripts/validate_rules.py

# Calcular métricas
python scripts/metrics.py

# Validar histórico
./scripts/validate_history.sh
```

### **Geração de Histórico**
```bash
# Gerar entrada para bug fix
./scripts/generate_history_entry.sh bug "Corrige erro de parsing"

# Gerar entrada para nova funcionalidade
./scripts/generate_history_entry.sh feat "Adiciona suporte a PDF"
```

### **Copiar para Outros Projetos**
```bash
# Copiar regras genéricas
cp rules_generic/*.mdc novo_projeto/.cursor/rules/

# Copiar ferramentas
cp scripts/ novo_projeto/scripts/
```

## 📊 Métricas de Conformidade

### **Scores Atuais**
- 🏗️ **Clean Architecture**: 100.0% ✅
- 🔧 **SOLID**: 86.2% ✅
- 🎯 **DRY/KISS/YAGNI**: 70.0% ⚠️
- 🧪 **Testes**: 82.0% ✅
- 📝 **Histórico**: 100.0% ✅
- **📈 GERAL**: **87.6%** ✅

### **Metas de Conformidade**
- **Score Geral**: ≥ 80%
- **Clean Architecture**: ≥ 80%
- **SOLID**: ≥ 80%
- **DRY/KISS/YAGNI**: ≥ 80%
- **Testes**: ≥ 80%
- **Histórico**: ≥ 80%

## 🔧 Adaptação por Linguagem

### **Python** (Atual)
```yaml
globs: ["src/**/*", "app/**/*", "domain/**/*"]
comandos: python -m pytest tests/unit/ -v
```

### **Node.js**
```yaml
globs: ["src/**/*", "lib/**/*", "packages/**/*"]
comandos: npm test
```

### **.NET**
```yaml
globs: ["src/**/*", "app/**/*", "core/**/*"]
comandos: dotnet test
```

### **Java**
```yaml
globs: ["src/**/*", "app/**/*", "domain/**/*"]
comandos: mvn test
```

### **Go**
```yaml
globs: ["src/**/*", "internal/**/*", "pkg/**/*"]
comandos: go test ./...
```

## 🎯 Benefícios das Regras

### **✅ Qualidade**
- Código mais limpo e organizado
- Arquitetura consistente
- Testes adequados
- Documentação atualizada

### **✅ Produtividade**
- Padrões claros para desenvolvimento
- Ferramentas de validação automática
- Onboarding mais rápido
- Manutenção simplificada

### **✅ Escalabilidade**
- Regras aplicáveis a qualquer projeto
- Adaptação fácil para diferentes linguagens
- Padrões universais
- Ferramentas reutilizáveis

## 📞 Suporte

Para dúvidas ou problemas:
1. Consultar documentação específica de cada regra
2. Verificar logs de erro das ferramentas
3. Usar versões genéricas para novos projetos
4. Adaptar gradualmente para necessidades específicas

## 🔄 Atualizações

As regras são atualizadas continuamente com base em:
- Feedback da equipe
- Melhores práticas da indústria
- Novas tecnologias e padrões
- Experiência em projetos reais

**Última atualização**: 2025-09-12
