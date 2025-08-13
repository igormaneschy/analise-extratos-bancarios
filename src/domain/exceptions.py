"""
Exceções customizadas do domínio.
"""


class DomainException(Exception):
    """Exceção base do domínio."""
    pass


class InvalidTransactionError(DomainException):
    """Erro quando uma transação é inválida."""
    pass


class InvalidStatementError(DomainException):
    """Erro quando um extrato é inválido."""
    pass


class ParsingError(DomainException):
    """Erro ao fazer parsing de dados."""
    pass


class FileNotSupportedError(DomainException):
    """Erro quando o formato do arquivo não é suportado."""
    pass


class AnalysisError(DomainException):
    """Erro durante análise de dados."""
    pass