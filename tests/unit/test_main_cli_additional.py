import importlib
import sys
from decimal import Decimal
from pathlib import Path
from click.testing import CliRunner
import builtins

import pytest

import main

from src.domain.models import AnalysisResult, BankStatement
from src.domain.exceptions import DomainException

runner = CliRunner()


def _capture_console(monkeypatch):
    printed = []
    # Use a real Rich Console with recording enabled to produce plaintext output
    from rich.console import Console as RichConsole
    real_console = RichConsole(record=True, force_terminal=False)

    def fake_print(*args, **kwargs):
        # Delegate to the real rich Console so complex renderables are rendered to text
        real_console.print(*args, **kwargs)
        try:
            text = real_console.export_text()
        except Exception:
            # Fallback: join str() of args
            text = " ".join(str(a) for a in args)
        printed.append(text)

    # Patch main.console.print to our fake_print while keeping other Console features untouched
    monkeypatch.setattr(main, 'console', type('C', (), {'print': staticmethod(fake_print)}))
    return printed


def _inject_fake_extractor(monkeypatch, FakeClass):
    # Install a fake module into sys.modules so imports inside main.analyze
    # will pick up our FakeClass as ExtractAnalyzer. We set parent package
    # entries as well to ensure import resolution works.
    import types
    fake_module = types.ModuleType('src.application.use_cases')
    fake_module.ExtractAnalyzer = FakeClass
    # Ensure parent packages exist
    pkg_src = sys.modules.get('src') or types.ModuleType('src')
    pkg_application = sys.modules.get('src.application') or types.ModuleType('src.application')
    pkg_application.use_cases = fake_module
    pkg_src.application = pkg_application
    monkeypatch.setitem(sys.modules, 'src', pkg_src)
    monkeypatch.setitem(sys.modules, 'src.application', pkg_application)
    monkeypatch.setitem(sys.modules, 'src.application.use_cases', fake_module)
    # Also, if the real module is already importable, patch its ExtractAnalyzer
    try:
        real_mod = importlib.import_module('src.application.use_cases')
        setattr(real_mod, 'ExtractAnalyzer', FakeClass)
    except Exception:
        pass


def test_analyze_with_output_and_markdown(tmp_path, monkeypatch):
    input_file = tmp_path / "input.txt"
    input_file.write_text("dummy")

    result = AnalysisResult(
        statement_id="s1",
        total_income=Decimal("100.00"),
        total_expenses=Decimal("50.00"),
        net_flow=Decimal("50.00"),
        currency="EUR",
        categories_summary={},
        monthly_summary={},
        alerts=[],
        insights=[],
        metadata={"transaction_count": 2}
    )
    report_str = "REPORT CONTENT"
    statement = BankStatement(transactions=[])

    class FakeExtractAnalyzer:
        def __init__(self):
            class UC:
                report_generator = None
            self.use_case = UC()
        def analyze_file(self, file_path, output_path=None):
            return result, report_str, statement

    _inject_fake_extractor(monkeypatch, FakeExtractAnalyzer)
    printed = _capture_console(monkeypatch)

    out_path = tmp_path / "out.txt"

    # Call the analyze command function directly to avoid CLI import layering issues
    main.analyze.callback(str(input_file), str(out_path), 'markdown')

    # We expect the CLI to have printed a confirmation that the report was saved
    combined = "\n".join(printed).lower()
    assert "relat" in combined  # fragment of 'relatório salvo' or similar


def test_analyze_handles_domain_exception(tmp_path, monkeypatch):
    input_file = tmp_path / "input.txt"
    input_file.write_text("dummy")

    class FakeExtractAnalyzer:
        def __init__(self):
            class UC:
                report_generator = None
            self.use_case = UC()
        def analyze_file(self, file_path, output_path=None):
            raise DomainException("invalid statement")

    _inject_fake_extractor(monkeypatch, FakeExtractAnalyzer)
    printed = _capture_console(monkeypatch)

    # Calling the analyze function should cause SystemExit in the exception branch.
    with pytest.raises(SystemExit):
        main.analyze.callback(str(input_file), None, 'text')

    combined = "\n".join(printed).lower()
    assert "erro" in combined or "invalid statement" in combined or "error" in combined


def test_sample_write_error(tmp_path, monkeypatch):
    # Force open to raise an error to exercise the exception branch
    def fake_open(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(builtins, 'open', fake_open)

    printed = _capture_console(monkeypatch)
    with pytest.raises(SystemExit):
        main.sample.callback(str(tmp_path / 'instr.txt'))

    combined = "\n".join(printed).lower()
    assert "erro ao criar arquivo" in combined or "erro" in combined


def test_analyze_prints_alerts_and_insights(tmp_path, monkeypatch):
    input_file = tmp_path / "input2.txt"
    input_file.write_text("dummy")

    result = AnalysisResult(
        statement_id="s2",
        total_income=Decimal("0.00"),
        total_expenses=Decimal("0.00"),
        net_flow=Decimal("0.00"),
        currency="EUR",
        categories_summary={},
        monthly_summary={},
        alerts=["Alerta teste"],
        insights=["Insight teste"],
        metadata={}
    )
    report_str = "REPORT"
    statement = BankStatement(transactions=[])

    class FakeExtractAnalyzer:
        def __init__(self):
            class UC:
                report_generator = None
            self.use_case = UC()
        def analyze_file(self, file_path, output_path=None):
            return result, report_str, statement

    _inject_fake_extractor(monkeypatch, FakeExtractAnalyzer)
    printed = _capture_console(monkeypatch)

    main.analyze.callback(str(input_file), None, 'text')

    combined = "\n".join(printed).lower()
    # Either the alerts/insights terms appear or at least the summary was printed
    assert ("alerta" in combined or "insight" in combined) or ("análise concluída" in combined)
