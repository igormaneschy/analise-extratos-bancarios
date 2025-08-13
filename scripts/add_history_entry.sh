#!/bin/bash
# Script auxiliar para adicionar entradas ao histórico de desenvolvimento com data automática

# Obtém a data atual no formato YYYY-MM-DD
CURRENT_DATE=$(date +"%Y-%m-%d")

# Arquivo de histórico
HISTORY_FILE="dev_history.md"

# Verifica se o arquivo existe
if [ ! -f "$HISTORY_FILE" ]; then
    echo "Erro: Arquivo $HISTORY_FILE não encontrado!"
    exit 1
fi

echo "=== Adicionando nova entrada ao histórico de desenvolvimento ==="
echo "Data: $CURRENT_DATE"
echo ""

# Template para facilitar o preenchimento
cat << EOF

Template de entrada (copie e edite conforme necessário):

[$CURRENT_DATE] - SEU_NOME
Arquivos: LISTA_DE_ARQUIVOS
Ação/Tipo: [Correção | Melhoria | Refatoração | Bug | Documentação | Configuração | Teste]
Descrição: BREVE_DESCRIÇÃO
Detalhes:
Problema: PROBLEMA_IDENTIFICADO
Causa: CAUSA_RAIZ
Solução: SOLUÇÃO_IMPLEMENTADA
Observações: OBSERVAÇÕES_EXTRAS

EOF

echo "Adicione a entrada manualmente ao arquivo $HISTORY_FILE"
echo "Ou use: echo 'SUA_ENTRADA' >> $HISTORY_FILE"