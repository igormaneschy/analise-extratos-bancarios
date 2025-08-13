"""
Caso de uso principal para análise de extratos.
"""
from pathlib import Path
from typing import Optional

from src.domain.models import BankStatement, AnalysisResult
from src.domain.interfaces import (
    StatementReader, 
    TransactionCategorizer,
    StatementAnalyzer,
    ReportGenerator
)
from src.domain.exceptions import FileNotSupportedError


class AnalyzeStatementUseCase:
    """Caso de uso para analisar extratos bancários."""
    
    def __init__(
        self,
        reader: StatementReader,
        categorizer: TransactionCategorizer,
        analyzer: StatementAnalyzer,
        report_generator: ReportGenerator
    ):
        self.reader = reader
        self.categorizer = categorizer
        self.analyzer = analyzer
        self.report_generator = report_generator
    
    def execute(
        self, 
        file_path: str, 
        output_path: Optional[str] = None
    ) -> tuple[AnalysisResult, str]:
        """
        Executa a análise completa de um extrato.
        
        Args:
            file_path: Caminho do arquivo de extrato
            output_path: Caminho opcional para salvar o relatório
            
        Returns:
            Tupla com (resultado da análise, relatório em texto)
        """
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
        from src.infrastructure.categorizers.keyword_categorizer import KeywordCategorizer
        from src.infrastructure.analyzers.basic_analyzer import BasicStatementAnalyzer
        from src.infrastructure.reports.text_report import TextReportGenerator
        
        # Inicializa componentes
        self.pdf_reader = PDFStatementReader()
        self.categorizer = KeywordCategorizer()
        self.analyzer = BasicStatementAnalyzer()
        self.text_report = TextReportGenerator()
        
        # Cria caso de uso
        self.use_case = AnalyzeStatementUseCase(
            reader=self.pdf_reader,
            categorizer=self.categorizer,
            analyzer=self.analyzer,
            report_generator=self.text_report
        )
    
    def analyze_file(
        self, 
        file_path: str, 
        output_path: Optional[str] = None
    ) -> tuple[AnalysisResult, str]:
        """
        Analisa um arquivo de extrato.
        
        Args:
            file_path: Caminho do arquivo
            output_path: Caminho opcional para salvar relatório
            
        Returns:
            Tupla com (resultado da análise, relatório)
        """
        return self.use_case.execute(file_path, output_path)
    
    def analyze_and_print(self, file_path: str) -> AnalysisResult:
        """
        Analisa um arquivo e imprime o relatório no console.
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            Resultado da análise
        """
        result, report = self.analyze_file(file_path)
        print(report)
        return result