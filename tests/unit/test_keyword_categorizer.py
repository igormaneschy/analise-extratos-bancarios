import pytest
from decimal import Decimal
from datetime import datetime
from src.infrastructure.categorizers.keyword_categorizer import KeywordCategorizer
from src.domain.models import Transaction, TransactionCategory, TransactionType

class TestKeywordCategorizer:
    """Testes para o KeywordCategorizer."""
    
    def test_categorize_alimentacao(self):
        """Testa a categorização de transações de alimentação."""
        categorizer = KeywordCategorizer()
        
        transaction = Transaction(
            date=datetime.now(),
            description="Compra no mercado",
            amount=Decimal("150.00"),
            type=TransactionType.DEBIT
        )
        
        categorized = categorizer.categorize(transaction)
        assert categorized.category == TransactionCategory.ALIMENTACAO
    
    def test_categorize_transporte(self):
        """Testa a categorização de transações de transporte."""
        categorizer = KeywordCategorizer()
        
        transaction = Transaction(
            date=datetime.now(),
            description="Uber para trabalho",
            amount=Decimal("25.50"),
            type=TransactionType.DEBIT
        )
        
        categorized = categorizer.categorize(transaction)
        assert categorized.category == TransactionCategory.TRANSPORTE
    
    def test_categorize_moradia(self):
        """Testa a categorização de transações de moradia."""
        categorizer = KeywordCategorizer()
        
        transaction = Transaction(
            date=datetime.now(),
            description="Pagamento de energia elétrica",
            amount=Decimal("120.00"),
            type=TransactionType.DEBIT
        )
        
        categorized = categorizer.categorize(transaction)
        assert categorized.category == TransactionCategory.MORADIA
    
    def test_categorize_saude(self):
        """Testa a categorização de transações de saúde."""
        categorizer = KeywordCategorizer()
        
        transaction = Transaction(
            date=datetime.now(),
            description="Consulta médica",
            amount=Decimal("200.00"),
            type=TransactionType.DEBIT
        )
        
        categorized = categorizer.categorize(transaction)
        assert categorized.category == TransactionCategory.SAUDE
    
    def test_categorize_educacao(self):
        """Testa a categorização de transações de educação."""
        categorizer = KeywordCategorizer()
        
        transaction = Transaction(
            date=datetime.now(),
            description="Mensalidade da faculdade",
            amount=Decimal("800.00"),
            type=TransactionType.DEBIT
        )
        
        categorized = categorizer.categorize(transaction)
        assert categorized.category == TransactionCategory.EDUCACAO
    
    def test_categorize_lazer(self):
        """Testa a categorização de transações de lazer."""
        categorizer = KeywordCategorizer()
        
        transaction = Transaction(
            date=datetime.now(),
            description="Ingresso para cinema",
            amount=Decimal("45.00"),
            type=TransactionType.DEBIT
        )
        
        categorized = categorizer.categorize(transaction)
        assert categorized.category == TransactionCategory.LAZER
    
    def test_categorize_compras(self):
        """Testa a categorização de transações de compras."""
        categorizer = KeywordCategorizer()
        
        transaction = Transaction(
            date=datetime.now(),
            description="Compra de roupa",
            amount=Decimal("180.00"),
            type=TransactionType.DEBIT
        )
        
        categorized = categorizer.categorize(transaction)
        assert categorized.category == TransactionCategory.COMPRAS
    
    def test_categorize_servicos(self):
        """Testa a categorização de transações de serviços."""
        categorizer = KeywordCategorizer()
        
        transaction = Transaction(
            date=datetime.now(),
            description="Corte de cabelo em salao",
            amount=Decimal("60.00"),
            type=TransactionType.DEBIT
        )
        
        categorized = categorizer.categorize(transaction)
        assert categorized.category == TransactionCategory.SERVICOS
    
    def test_categorize_transferencia(self):
        """Testa a categorização de transações de transferência."""
        categorizer = KeywordCategorizer()
        
        transaction = Transaction(
            date=datetime.now(),
            description="Transferência PIX recebida",
            amount=Decimal("500.00"),
            type=TransactionType.CREDIT
        )
        
        categorized = categorizer.categorize(transaction)
        assert categorized.category == TransactionCategory.TRANSFERENCIA
    
    def test_categorize_investimento(self):
        """Testa a categorização de transações de investimento."""
        categorizer = KeywordCategorizer()
        
        transaction = Transaction(
            date=datetime.now(),
            description="Aplicação em CDB",
            amount=Decimal("1000.00"),
            type=TransactionType.DEBIT
        )
        
        categorized = categorizer.categorize(transaction)
        assert categorized.category == TransactionCategory.INVESTIMENTO
    
    def test_categorize_salario(self):
        """Testa a categorização de transações de salário."""
        categorizer = KeywordCategorizer()
        
        transaction = Transaction(
            date=datetime.now(),
            description="Salário mensal holerite",
            amount=Decimal("3500.00"),
            type=TransactionType.CREDIT
        )
        
        categorized = categorizer.categorize(transaction)
        assert categorized.category == TransactionCategory.SALARIO
    
    def test_categorize_nao_categorizado(self):
        """Testa a categorização de transações que não se encaixam em nenhuma categoria."""
        categorizer = KeywordCategorizer()
        
        transaction = Transaction(
            date=datetime.now(),
            description="Descrição qualquer sem categoria definida",
            amount=Decimal("100.00"),
            type=TransactionType.DEBIT
        )
        
        categorized = categorizer.categorize(transaction)
        assert categorized.category == TransactionCategory.NAO_CATEGORIZADO
    
    def test_normalize_text_with_accents(self):
        """Testa a normalização de texto com acentos."""
        categorizer = KeywordCategorizer()
        
        # Testa remoção de acentos
        assert categorizer._normalize_text("café") == "cafe"
        assert categorizer._normalize_text("álcool") == "alcool"
        assert categorizer._normalize_text("restauração") == "restauracao"
    
    def test_normalize_text_with_special_chars(self):
        """Testa a normalização de texto com caracteres especiais."""
        categorizer = KeywordCategorizer()
        
        # Testa remoção de caracteres especiais
        assert categorizer._normalize_text("restaurante!") == "restaurante"
        assert categorizer._normalize_text("supermercado@") == "supermercado"
        assert categorizer._normalize_text("compra#de#material") == "compra de material"
    
    def test_load_keywords(self):
        """Testa o carregamento de palavras-chave."""
        categorizer = KeywordCategorizer()
        
        # Verifica que todas as categorias estão presentes
        assert TransactionCategory.ALIMENTACAO in categorizer.keywords
        assert TransactionCategory.TRANSPORTE in categorizer.keywords
        assert TransactionCategory.MORADIA in categorizer.keywords
        assert TransactionCategory.SAUDE in categorizer.keywords
        assert TransactionCategory.EDUCACAO in categorizer.keywords
        assert TransactionCategory.LAZER in categorizer.keywords
        assert TransactionCategory.COMPRAS in categorizer.keywords
        assert TransactionCategory.SERVICOS in categorizer.keywords
        assert TransactionCategory.TRANSFERENCIA in categorizer.keywords
        assert TransactionCategory.INVESTIMENTO in categorizer.keywords
        assert TransactionCategory.SALARIO in categorizer.keywords