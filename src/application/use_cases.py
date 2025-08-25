"""
Casos de uso para análise de extratos.
"""
from pathlib import Path
from typing import Optional, List

from src.domain.interfaces import (
    StatementReader,
    TransactionCategorizer,
    StatementAnalyzer,
    ReportGenerator,
)
from src.domain.models import BankStatement, AnalysisResult


class AnalyzeStatementUseCase:
    """Caso de uso para analisar extratos bancários."""

    def __init__(
        self,
        reader: StatementReader,
        categorizer: TransactionCategorizer,
        analyzer: StatementAnalyzer,
        report_generator: ReportGenerator,
    ):
        self.reader = reader
        self.categorizer = categorizer
        self.analyzer = analyzer
        self.report_generator = report_generator

    def execute(
        self,
        file_path: str,
        output_path: Optional[str] = None,
    ) -> tuple:
        # Converte para Path
        file_path = Path(file_path)
        output_path = Path(output_path) if output_path else None

        # Valida se o arquivo existe
        if not file_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

        # Lê o extrato
        statement = self.reader.read(file_path)

        # Categoriza as transações
        for i, transaction in enumerate(statement.transactions):
            statement.transactions[i] = self.categorizer.categorize(transaction)

        # Analisa o extrato
        analysis_result = self.analyzer.analyze(statement)

        # Gera o relatório
        report = self.report_generator.generate(analysis_result, output_path)

        return analysis_result, report


class ExtractAnalyzer:
    """Classe de fachada para simplificar o uso do sistema."""

    def __init__(self):
        # Importa implementações concretas
        from src.infrastructure.readers.pdf_reader import PDFStatementReader
        from src.infrastructure.readers.excel_reader import ExcelStatementReader
        from src.infrastructure.readers.csv_reader import CSVStatementReader
        from src.infrastructure.categorizers.keyword_categorizer import KeywordCategorizer
        from src.infrastructure.analyzers.basic_analyzer import BasicStatementAnalyzer
        from src.infrastructure.reports.text_report import TextReportGenerator

        # Inicializa componentes
        self.pdf_reader = PDFStatementReader()
        self.excel_reader = ExcelStatementReader()
        self.csv_reader = CSVStatementReader()
        self.categorizer = KeywordCategorizer()
        self.analyzer = BasicStatementAnalyzer()
        self.text_report = TextReportGenerator()

        # Lista de leitores disponíveis
        self.readers: List[StatementReader] = [
            self.pdf_reader,
            self.excel_reader,
            self.csv_reader
        ]

        # Cria caso de uso com o primeiro leitor (será substituído dinamicamente)
        self.use_case = AnalyzeStatementUseCase(
            reader=self.pdf_reader,
            categorizer=self.categorizer,
            analyzer=self.analyzer,
            report_generator=self.text_report,
        )

    def _get_appropriate_reader(self, file_path: str) -> StatementReader:
        """Retorna o leitor apropriado para o tipo de arquivo."""
        file_path_obj = Path(file_path)
        for reader in self.readers:
            if reader.can_read(file_path_obj):
                return reader
        raise ValueError(f"Nenhum leitor disponível para o arquivo: {file_path}")

    def analyze_file(
        self,
        file_path: str,
        output_path: Optional[str] = None,
    ) -> tuple:
        # Seleciona o leitor apropriado
        reader = self._get_appropriate_reader(file_path)
        
        # Atualiza o caso de uso com o leitor correto
        self.use_case.reader = reader
        
        result, report = self.use_case.execute(file_path, output_path)
        return result, report, reader.read(Path(file_path))

    def analyze_and_print(self, file_path: str):
        result, report = self.analyze_file(file_path)
        print(report)
        return result