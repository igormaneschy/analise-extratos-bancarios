import sys
import types
from types import SimpleNamespace
import os
import io
import pytest
from click.testing import CliRunner

import main


class FakeAnalyzer:
    def __init__(self):
        # use_case must be present and allow setting report_generator
        self.use_case = SimpleNamespace(report_generator=None)

    def analyze_file(self, file_path, output):
        result = SimpleNamespace(
            currency='EUR',
            metadata={'transaction_count': 3},
            total_income=1000.0,
            total_expenses=500.0,
            net_flow=500.0,
            alerts=[],
            insights=[],
        )
        report = "Relatório de teste"
        statement = None
        return result, report, statement


@pytest.fixture(autouse=True)
def mock_src_modules(monkeypatch):
    """Provide lightweight fake modules to satisfy main.analyze late imports."""
    # src.application.use_cases
    mod_use_cases = types.ModuleType("src.application.use_cases")
    mod_use_cases.ExtractAnalyzer = FakeAnalyzer
    sys.modules["src.application.use_cases"] = mod_use_cases

    # src.domain.exceptions
    mod_ex = types.ModuleType("src.domain.exceptions")
    class DomainException(Exception):
        pass
    mod_ex.DomainException = DomainException
    sys.modules["src.domain.exceptions"] = mod_ex

    # src.utils.currency_utils
    mod_cur = types.ModuleType("src.utils.currency_utils")
    class CurrencyUtils:
        @staticmethod
        def get_currency_symbol(code):
            return '€' if code == 'EUR' else '?'
    mod_cur.CurrencyUtils = CurrencyUtils
    sys.modules["src.utils.currency_utils"] = mod_cur

    # src.infrastructure.reports.text_report (for markdown option)
    mod_rep = types.ModuleType("src.infrastructure.reports.text_report")
    class MarkdownReportGenerator:
        def __init__(self):
            pass
    mod_rep.MarkdownReportGenerator = MarkdownReportGenerator
    sys.modules["src.infrastructure.reports.text_report"] = mod_rep

    yield


def test_analyze_default_format(tmp_path):
    runner = CliRunner()
    # create a temporary file to act as input
    f = tmp_path / "sample.csv"
    f.write_text("data,descricao,valor\n01/01/2023,Teste,100.00")

    result = runner.invoke(main.cli, ["analyze", str(f)])
    assert result.exit_code == 0
    assert "Análise concluída" in result.output
    assert "Total de transações" in result.output
    assert "€" in result.output


def test_analyze_markdown_option(tmp_path):
    runner = CliRunner()
    f = tmp_path / "sample2.csv"
    f.write_text("data,descricao,valor\n02/01/2023,Teste2,200.00")

    result = runner.invoke(main.cli, ["analyze", str(f), "--format", "markdown"]) 
    assert result.exit_code == 0
    assert "Análise concluída" in result.output
    # ensure that MarkdownReportGenerator path didn't crash


def test_sample_creates_file(tmp_path):
    runner = CliRunner()
    out = tmp_path / "instructions.md"

    result = runner.invoke(main.cli, ["sample", str(out)])
    assert result.exit_code == 0
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "Instruções para uso do Sistema" in content


def test_version_shows_info():
    runner = CliRunner()
    result = runner.invoke(main.cli, ["version"]) 
    assert result.exit_code == 0
    assert "Versão: 1.0.0" in result.output
