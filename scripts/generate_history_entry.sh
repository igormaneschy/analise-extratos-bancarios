#!/bin/bash
# Script para gerar entrada automática no dev_history.md

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para mostrar ajuda
show_help() {
    echo "Uso: $0 <tipo> <descrição> [autor]"
    echo ""
    echo "Tipos disponíveis:"
    echo "  bug      - Correção de bug"
    echo "  feat     - Nova funcionalidade"
    echo "  refactor - Refatoração"
    echo "  test     - Adição de testes"
    echo "  docs     - Documentação"
    echo "  config   - Configuração"
    echo ""
    echo "Exemplos:"
    echo "  $0 bug \"Corrige parsing de valores negativos\""
    echo "  $0 feat \"Adiciona suporte a Excel\" \"João Silva\""
    echo "  $0 refactor \"Melhora arquitetura de readers\""
}

# Verificar argumentos
if [ $# -lt 2 ]; then
    echo -e "${RED}❌ Erro: Argumentos insuficientes${NC}"
    echo ""
    show_help
    exit 1
fi

TYPE=$1
DESCRIPTION=$2
AUTHOR=${3:-"Assistant"}
DATE=$(date +"%Y-%m-%d")

# Validar tipo
case $TYPE in
    "bug"|"feat"|"refactor"|"test"|"docs"|"config")
        ;;
    *)
        echo -e "${RED}❌ Erro: Tipo inválido '$TYPE'${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac

# Verificar se dev_history.md existe
if [ ! -f "dev_history.md" ]; then
    echo -e "${YELLOW}⚠️  dev_history.md não encontrado. Criando...${NC}"
    touch dev_history.md
fi

# Gerar entrada baseada no tipo
case $TYPE in
    "bug")
        ENTRY_TYPE="Bug"
        ENTRY_DESC="Corrige $DESCRIPTION"
        ;;
    "feat")
        ENTRY_TYPE="Melhoria"
        ENTRY_DESC="Implementa $DESCRIPTION"
        ;;
    "refactor")
        ENTRY_TYPE="Refatoração"
        ENTRY_DESC="Refatora $DESCRIPTION"
        ;;
    "test")
        ENTRY_TYPE="Teste"
        ENTRY_DESC="Adiciona testes para $DESCRIPTION"
        ;;
    "docs")
        ENTRY_TYPE="Documentação"
        ENTRY_DESC="Atualiza documentação: $DESCRIPTION"
        ;;
    "config")
        ENTRY_TYPE="Configuração"
        ENTRY_DESC="Atualiza configuração: $DESCRIPTION"
        ;;
esac

# Obter arquivos modificados
MODIFIED_FILES=$(git diff --name-only HEAD~1 HEAD 2>/dev/null | tr '\n' ', ' | sed 's/,$//')
if [ -z "$MODIFIED_FILES" ]; then
    MODIFIED_FILES="Arquivos não detectados automaticamente"
fi

# Gerar detalhes baseados no tipo
case $TYPE in
    "bug")
        PROBLEMA="Erro identificado: $DESCRIPTION"
        CAUSA="Análise da causa raiz necessária"
        SOLUCAO="Implementação da correção necessária"
        OBSERVACOES="Testes de regressão necessários"
        ;;
    "feat")
        PROBLEMA="Necessidade de implementar: $DESCRIPTION"
        CAUSA="Requisito de negócio ou melhoria identificada"
        SOLUCAO="Implementação da nova funcionalidade"
        OBSERVACOES="Testes unitários e de integração necessários"
        ;;
    "refactor")
        PROBLEMA="Código necessita refatoração: $DESCRIPTION"
        CAUSA="Melhoria de qualidade, performance ou manutenibilidade"
        SOLUCAO="Refatoração do código existente"
        OBSERVACOES="Validação de funcionalidade e testes necessários"
        ;;
    "test")
        PROBLEMA="Falta de cobertura de testes: $DESCRIPTION"
        CAUSA="Necessidade de validação e confiabilidade"
        SOLUCAO="Implementação de testes unitários/integração"
        OBSERVACOES="Cobertura de código e cenários de teste"
        ;;
    "docs")
        PROBLEMA="Documentação desatualizada: $DESCRIPTION"
        CAUSA="Necessidade de manter documentação sincronizada"
        SOLUCAO="Atualização da documentação"
        OBSERVACOES="Revisão e validação da documentação"
        ;;
    "config")
        PROBLEMA="Configuração necessita atualização: $DESCRIPTION"
        CAUSA="Mudança de requisitos ou ambiente"
        SOLUCAO="Atualização de configurações"
        OBSERVACOES="Validação em ambiente de desenvolvimento"
        ;;
esac

# Criar entrada temporária
TEMP_FILE=$(mktemp)
cat > "$TEMP_FILE" << EOF
[$DATE] - $AUTHOR
Arquivos: $MODIFIED_FILES
Ação/Tipo: $ENTRY_TYPE
Descrição: $ENTRY_DESC
Detalhes:
Problema: $PROBLEMA
Causa: $CAUSA
Solução: $SOLUCAO
Observações: $OBSERVACOES

EOF

# Adicionar ao início do arquivo
{
    cat "$TEMP_FILE"
    cat dev_history.md
} > dev_history.md.tmp

mv dev_history.md.tmp dev_history.md
rm "$TEMP_FILE"

echo -e "${GREEN}✅ Entrada adicionada ao dev_history.md${NC}"
echo -e "${BLUE}📝 Tipo: $ENTRY_TYPE${NC}"
echo -e "${BLUE}📝 Descrição: $ENTRY_DESC${NC}"
echo -e "${BLUE}📝 Autor: $AUTHOR${NC}"
echo -e "${BLUE}📝 Data: $DATE${NC}"
echo ""
echo -e "${YELLOW}💡 Lembre-se de preencher os detalhes da entrada!${NC}"
