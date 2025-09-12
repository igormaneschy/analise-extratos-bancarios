import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
from decimal import Decimal
from src.application.use_cases import AnalyzeStatementUseCase, ExtractAnalyzer
from src.domain.models import BankStatement, Transaction, AnalysisResult, TransactionCategory
from src.domain.exceptions import DomainException

# Testes para AnalyzeStatementUseCase

@patch("pathlib.Path.exists", return_value=True)
def test_execute_success(mock_exists):
    from decimal import Decimal

    # Mocks
    reader = Mock()
    categorizer = Mock()
    analyzer = Mock()
    report_generator = Mock()

    # Dados simulados
    transaction = Transaction(date="2023-01-01", description="desc", amount=100, category=None)
    statement = BankStatement(transactions=[transaction])
    analysis_result = AnalysisResult(
        statement_id="id123",
        total_income=Decimal('100.00'),
        total_expenses=Decimal('50.00'),
        net_flow=Decimal('50.00'),
        currency="USD",
        categories_summary={},
        monthly_summary={},
    )
    report = "Relatorio gerado"

    reader.read.return_value = statement
    categorizer.categorize.return_value = transaction
    analyzer.analyze.return_value = analysis_result
    report_generator.generate.return_value = report

    use_case = AnalyzeStatementUseCase(reader, categorizer, analyzer, report_generator)

    result, generated_report = use_case.execute("fake_path")

    # Verificações
    reader.read.assert_called_once()
    categorizer.categorize.assert_called_once_with(transaction)
    analyzer.analyze.assert_called_once_with(statement)
    report_generator.generate.assert_called_once_with(analysis_result, None)

    assert result == analysis_result
    assert generated_report == report


def test_execute_file_not_found():
    reader = Mock()
    categorizer = Mock()
    analyzer = Mock()
    report_generator = Mock()

    use_case = AnalyzeStatementUseCase(reader, categorizer, analyzer, report_generator)

    with pytest.raises(FileNotFoundError):
        use_case.execute("non_existent_file")


def test_extract_analyzer_get_appropriate_reader():
    analyzer = ExtractAnalyzer()

    # Deve retornar um leitor válido para arquivo PDF
    reader = analyzer._get_appropriate_reader("data/samples/20250507_Extrato_Integrado.pdf")
    assert reader.can_read(Path("data/samples/20250507_Extrato_Integrado.pdf"))

    # Deve lançar erro para arquivo sem leitor
    with pytest.raises(ValueError):
        analyzer._get_appropriate_reader("file.unsupported")


def test_extract_analyzer_analyze_file(monkeypatch):
    analyzer = ExtractAnalyzer()

    # Mock do use_case.execute para retornar valores simulados
    monkeypatch.setattr(analyzer.use_case, "execute", lambda file_path, output_path=None: ("result", "report"))

    result, report, statement = analyzer.analyze_file("data/samples/20250507_Extrato_Integrado.pdf")

    assert result == "result"
    assert report == "report"
    assert statement is not None


def test_extract_analyzer_analyze_and_print(monkeypatch, capsys):
    analyzer = ExtractAnalyzer()

    monkeypatch.setattr(analyzer, "analyze_file", lambda file_path: ("result", "report", "statement"))

    result = analyzer.analyze_and_print("data/samples/20250507_Extrato_Integrado.pdf")

    captured = capsys.readouterr()
    assert "report" in captured.out
    assert result == "result"
