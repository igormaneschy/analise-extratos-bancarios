"""
Factories para criação de componentes do sistema.
"""
from typing import List
from src.domain.interfaces import (
    StatementReader,
    TransactionCategorizer,
    StatementAnalyzer,
    ReportGenerator,
)


class ComponentFactory:
    """Factory para criação de componentes do sistema."""
    
    @staticmethod
    def create_readers() -> List[StatementReader]:
        """Cria todos os leitores disponíveis."""
        from src.infrastructure.readers.pdf_reader import PDFStatementReader
        from src.infrastructure.readers.excel_reader import ExcelStatementReader
        from src.infrastructure.readers.csv_reader import CSVStatementReader
        
        return [
            PDFStatementReader(),
            ExcelStatementReader(),
            CSVStatementReader()
        ]
    
    @staticmethod
    def create_categorizer() -> TransactionCategorizer:
        """Cria o categorizador de transações."""
        from src.infrastructure.categorizers.keyword_categorizer import KeywordCategorizer
        return KeywordCategorizer()
    
    @staticmethod
    def create_analyzer() -> StatementAnalyzer:
        """Cria o analisador de extratos."""
        from src.infrastructure.analyzers.basic_analyzer import BasicStatementAnalyzer
        return BasicStatementAnalyzer()
    
    @staticmethod
    def create_report_generator() -> ReportGenerator:
        """Cria o gerador de relatórios."""
        from src.infrastructure.reports.text_report import TextReportGenerator
        return TextReportGenerator()
    
    @staticmethod
    def get_appropriate_reader(file_path: str, readers: List[StatementReader]) -> StatementReader:
        """Retorna o leitor apropriado para o tipo de arquivo."""
        from pathlib import Path
        
        file_path_obj = Path(file_path)
        for reader in readers:
            if reader.can_read(file_path_obj):
                return reader
        raise ValueError(f"Nenhum leitor disponível para o arquivo: {file_path}")
