#!/bin/bash
# Script para criar nova entrada no histórico de desenvolvimento
# Este é um alias para generate_history_entry.sh para manter compatibilidade

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📝 Criando nova entrada no histórico de desenvolvimento...${NC}"
echo ""

# Chama o script principal
exec "$(dirname "$0")/generate_history_entry.sh" "$@"
