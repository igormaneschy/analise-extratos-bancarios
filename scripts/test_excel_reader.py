#!/usr/bin/env python3
"""
Script de teste para o leitor de Excel.
"""
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.readers.excel_reader import ExcelStatementReader
from src.domain.models import TransactionType

def test_excel_reader():
    """Testa o leitor de Excel com o arquivo de exemplo."""
    reader = ExcelStatementReader()
    
    # Caminho para o arquivo de exemplo
    excel_path = Path("data/samples/extmovs_bpi2108102947.xlsx")
    
    if not excel_path.exists():
        print(f"Arquivo não encontrado: {excel_path}")
        return
    
    print(f"Testando leitor de Excel com: {excel_path}")
    
    # Verifica se pode ler o arquivo
    if not reader.can_read(excel_path):
        print("O leitor não reconhece este arquivo como Excel")
        return
    
    try:
        # Lê o extrato
        statement = reader.read(excel_path)
        
        print(f"\nExtrato lido com sucesso!")
        print(f"Banco: {statement.bank_name}")
        print(f"Conta: {statement.account_number}")
        print(f"Período: {statement.period_start} a {statement.period_end}")
        print(f"Saldo inicial: € {statement.initial_balance}")
        print(f"Saldo final: € {statement.final_balance}")
        print(f"Total de transações: {len(statement.transactions)}")
        
        print(f"\nPrimeiras 5 transações:")
        for i, transaction in enumerate(statement.transactions[:5]):
            print(f"  {i+1}. {transaction.date.strftime('%d/%m/%Y')} - "
                  f"{transaction.description} - "
                  f"{'+' if transaction.type == TransactionType.CREDIT else '-'}€ {transaction.amount}")
        
        print(f"\nÚltimas 5 transações:")
        for i, transaction in enumerate(statement.transactions[-5:], len(statement.transactions)-4):
            print(f"  {i}. {transaction.date.strftime('%d/%m/%Y')} - "
                  f"{transaction.description} - "
                  f"{'+' if transaction.type == TransactionType.CREDIT else '-'}€ {transaction.amount}")
                  
    except Exception as e:
        print(f"Erro ao ler o extrato: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_excel_reader()