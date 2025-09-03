import sys
from pathlib import Path

from click.testing import CliRunner
import builtins

# Garante import do CLI sem depender de src.* em import-time
sys.path.insert(0, str(Path(__file__).parent.parent))
from main import cli  # noqa: E402


def test_cli_version_outputs_expected_lines():
    runner = CliRunner()
    result = runner.invoke(cli, ["version"])
    assert result.exit_code == 0
    assert "Sistema de Análise de Extratos Bancários" in result.output
    assert "Versão: 1.0.0" in result.output
    assert "Formatos suportados: PDF, Excel, CSV" in result.output


def test_cli_sample_creates_file_and_writes_instructions(tmp_path):
    runner = CliRunner()
    out_file = tmp_path / "instrucoes.txt"

    result = runner.invoke(cli, ["sample", str(out_file)])

    assert result.exit_code == 0
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    # Verifica alguns marcadores do texto gerado
    assert "Instruções para uso do Sistema de Análise de Extratos Bancários" in content
    assert "Formatos Suportados" in content
    assert "CSV" in content


def test_cli_analyze_handles_missing_src_dependencies(monkeypatch, tmp_path):
    # Cria um arquivo vazio para simular entrada de caminho válido
    fake_input = tmp_path / "extrato.csv"
    fake_input.write_text("data,descricao,valor\n", encoding="utf-8")

    runner = CliRunner()

    # Monkeypatch para simular ImportError apenas para imports de 'src' e submódulos
    orig_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "src" or name.startswith("src."):
            raise ImportError("src package not available")
        return orig_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    result = runner.invoke(cli, ["analyze", str(fake_input)])

    # Espera-se erro inesperado com exit_code 1 (pois não há src no ambiente de teste)
    assert result.exit_code == 1
    assert "Erro inesperado:" in result.output
