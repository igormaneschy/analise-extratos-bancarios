import sys
import os
import pytest
from click.testing import CliRunner

# Ajustar sys.path para importar main.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import cli

runner = CliRunner()

# Teste básico para o comando analyze com arquivo inexistente

def test_analyze_file_not_found():
    result = runner.invoke(cli, ['analyze', 'arquivo_inexistente.pdf'])
    assert result.exit_code != 0
    assert "does not exist" in result.output or "não encontrado" in result.output

# Teste básico para o comando sample para criar arquivo de instruções

def test_sample_creates_file(tmp_path):
    output_file = tmp_path / "instrucoes.txt"
    result = runner.invoke(cli, ['sample', str(output_file)])
    assert result.exit_code == 0
    assert output_file.exists()
    content = output_file.read_text()
    assert "Instruções" in content

# Teste básico para o comando version

def test_version():
    result = runner.invoke(cli, ['version'])
    assert result.exit_code == 0
    assert "versão" in result.output.lower() or "version" in result.output.lower()


import os


# Teste analyze com arquivo PDF de exemplo - modificado para mostrar saída em caso de erro

def test_analyze_pdf_sample():
    sample_path = os.path.join('data', 'samples', '20250507_Extrato_Integrado.pdf')
    result = runner.invoke(cli, ['analyze', sample_path])
    if result.exit_code != 0:
        print("Erro na análise PDF:", result.output)
    assert result.exit_code == 0
    assert "análise concluída" in result.output.lower() or "total de transações" in result.output.lower() or "fim do relatório" in result.output.lower()

# Teste analyze com arquivo Excel de exemplo

def test_analyze_excel_sample():
    sample_path = os.path.join('data', 'samples', 'extmovs_bpi2108102947.xlsx')
    result = runner.invoke(cli, ['analyze', sample_path])
    if result.exit_code != 0:
        print("Erro na análise Excel:", result.output)
    assert result.exit_code == 0
    assert "análise concluída" in result.output.lower() or "total de transações" in result.output.lower() or "fim do relatório" in result.output.lower()

# Teste analyze com arquivo CSV de exemplo

def test_analyze_csv_sample():
    sample_path = os.path.join('data', 'samples', 'extrato_exemplo.csv')
    result = runner.invoke(cli, ['analyze', sample_path])
    assert result.exit_code == 0
    assert "análise concluída" in result.output.lower() or "total de transações" in result.output.lower() or "fim do relatório" in result.output.lower()
