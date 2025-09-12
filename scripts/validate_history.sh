#!/bin/bash
# Script para validar dev_history.md

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Verificar se dev_history.md existe
if [ ! -f "dev_history.md" ]; then
    echo -e "${RED}❌ dev_history.md não encontrado${NC}"
    exit 1
fi

echo -e "${BLUE}🔍 Validando dev_history.md...${NC}"
echo ""

# Contar entradas
TOTAL_ENTRIES=$(grep -c '^\[[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}\]' dev_history.md)
TODAY=$(date +"%Y-%m-%d")
TODAY_ENTRIES=$(grep -c "\[$TODAY\]" dev_history.md)

echo -e "${BLUE}📊 Estatísticas:${NC}"
echo -e "  Total de entradas: $TOTAL_ENTRIES"
echo -e "  Entradas de hoje: $TODAY_ENTRIES"
echo ""

# Verificar se há entradas
if [ $TOTAL_ENTRIES -eq 0 ]; then
    echo -e "${RED}❌ Nenhuma entrada encontrada${NC}"
    exit 1
fi

# Verificar se há entradas de hoje
if [ $TODAY_ENTRIES -gt 0 ]; then
    echo -e "${GREEN}✅ Entradas de hoje encontradas: $TODAY_ENTRIES${NC}"
else
    echo -e "${YELLOW}⚠️  Nenhuma entrada de hoje encontrada${NC}"
fi

# Verificar formato das entradas
echo ""
echo -e "${BLUE}🔍 Verificando formato das entradas...${NC}"

# Verificar se todas as entradas têm seções obrigatórias
MISSING_SECTIONS=0
grep -n '^\[[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}\]' dev_history.md | while IFS=: read -r line_num line_content; do
    # Verificar se há "Ação/Tipo:" nas próximas 5 linhas
    if ! sed -n "${line_num},$((line_num + 5))p" dev_history.md | grep -q "Ação/Tipo:"; then
        echo -e "${YELLOW}⚠️  Entrada sem 'Ação/Tipo:' na linha $line_num${NC}"
        MISSING_SECTIONS=$((MISSING_SECTIONS + 1))
    fi
    
    # Verificar se há "Descrição:" nas próximas 5 linhas
    if ! sed -n "${line_num},$((line_num + 5))p" dev_history.md | grep -q "Descrição:"; then
        echo -e "${YELLOW}⚠️  Entrada sem 'Descrição:' na linha $line_num${NC}"
        MISSING_SECTIONS=$((MISSING_SECTIONS + 1))
    fi
done

# Resultado final
echo ""
if [ $TODAY_ENTRIES -gt 0 ]; then
    echo -e "${GREEN}✅ dev_history.md está em conformidade!${NC}"
    echo -e "${GREEN}✅ $TOTAL_ENTRIES entradas encontradas${NC}"
    echo -e "${GREEN}✅ $TODAY_ENTRIES entradas de hoje${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  dev_history.md precisa de melhorias:${NC}"
    echo -e "  - Nenhuma entrada de hoje encontrada"
    echo -e "  - Considere adicionar uma entrada para mudanças recentes"
    exit 1
fi