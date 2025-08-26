import pytest
from decimal import Decimal
from datetime import datetime
from src.domain.models import Transaction, BankStatement, AnalysisResult, TransactionType, TransactionCategory

class TestTransaction:
    """Testes para o modelo Transaction."""
    
    def test_transaction_creation(self):
        """Testa a criação de uma transação."""
        transaction = Transaction(
            date=datetime(2024, 1, 1),
            description="Test transaction",
            amount=Decimal("100.50"),
            type=TransactionType.CREDIT
        )
        
        assert transaction.description == "Test transaction"
        assert transaction.amount == Decimal("100.50")
        assert transaction.type == TransactionType.CREDIT
        assert transaction.category == TransactionCategory.NAO_CATEGORIZADO
    
    def test_transaction_post_init_conversion(self):
        """Testa a conversão automática de tipos no __post_init__."""
        transaction = Transaction(
            date=datetime(2024, 1, 1),
            description="Test transaction",
            amount=100.50,  # float
            type=TransactionType.CREDIT,
            balance_after=200.75  # float
        )
        
        assert isinstance(transaction.amount, Decimal)
        assert isinstance(transaction.balance_after, Decimal)
        assert transaction.amount == Decimal("100.50")
        assert transaction.balance_after == Decimal("200.75")
    
    def test_transaction_is_income(self):
        """Testa a propriedade is_income."""
        credit_transaction = Transaction(
            date=datetime(2024, 1, 1),
            description="Salary",
            amount=Decimal("2500.00"),
            type=TransactionType.CREDIT
        )
        
        debit_transaction = Transaction(
            date=datetime(2024, 1, 1),
            description="Supermarket",
            amount=Decimal("150.00"),
            type=TransactionType.DEBIT
        )
        
        assert credit_transaction.is_income == True
        assert debit_transaction.is_income == False
    
    def test_transaction_is_expense(self):
        """Testa a propriedade is_expense."""
        credit_transaction = Transaction(
            date=datetime(2024, 1, 1),
            description="Salary",
            amount=Decimal("2500.00"),
            type=TransactionType.CREDIT
        )
        
        debit_transaction = Transaction(
            date=datetime(2024, 1, 1),
            description="Supermarket",
            amount=Decimal("150.00"),
            type=TransactionType.DEBIT
        )
        
        assert credit_transaction.is_expense == False
        assert debit_transaction.is_expense == True


class TestBankStatement:
    """Testes para o modelo BankStatement."""
    
    def test_bank_statement_creation(self):
        """Testa a criação de um extrato bancário."""
        statement = BankStatement(
            bank_name="Test Bank",
            account_number="12345-6",
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 1, 31),
            initial_balance=Decimal("1000.00"),
            final_balance=Decimal("1500.00"),
            currency="EUR"
        )
        
        assert statement.bank_name == "Test Bank"
        assert statement.account_number == "12345-6"
        assert statement.currency == "EUR"
        assert len(statement.transactions) == 0
    
    def test_bank_statement_post_init_conversion(self):
        """Testa a conversão automática de tipos no __post_init__."""
        statement = BankStatement(
            bank_name="Test Bank",
            account_number="12345-6",
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 1, 31),
            initial_balance=1000.00,  # float
            final_balance=1500.75,    # float
            currency="EUR"
        )
        
        assert isinstance(statement.initial_balance, Decimal)
        assert isinstance(statement.final_balance, Decimal)
        assert statement.initial_balance == Decimal("1000.00")
        assert statement.final_balance == Decimal("1500.75")
    
    def test_bank_statement_total_income(self):
        """Testa o cálculo do total de receitas."""
        transactions = [
            Transaction(
                date=datetime(2024, 1, 1),
                description="Salary",
                amount=Decimal("2500.00"),
                type=TransactionType.CREDIT
            ),
            Transaction(
                date=datetime(2024, 1, 2),
                description="Gift",
                amount=Decimal("100.00"),
                type=TransactionType.CREDIT
            ),
            Transaction(
                date=datetime(2024, 1, 3),
                description="Supermarket",
                amount=Decimal("150.00"),
                type=TransactionType.DEBIT
            )
        ]
        
        statement = BankStatement(
            bank_name="Test Bank",
            account_number="12345-6",
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 1, 31),
            initial_balance=Decimal("1000.00"),
            final_balance=Decimal("1500.00"),
            currency="EUR",
            transactions=transactions
        )
        
        assert statement.total_income == Decimal("2600.00")
    
    def test_bank_statement_total_expenses(self):
        """Testa o cálculo do total de despesas."""
        transactions = [
            Transaction(
                date=datetime(2024, 1, 1),
                description="Salary",
                amount=Decimal("2500.00"),
                type=TransactionType.CREDIT
            ),
            Transaction(
                date=datetime(2024, 1, 2),
                description="Supermarket",
                amount=Decimal("150.00"),
                type=TransactionType.DEBIT
            ),
            Transaction(
                date=datetime(2024, 1, 3),
                description="Gas",
                amount=Decimal("80.00"),
                type=TransactionType.DEBIT
            )
        ]
        
        statement = BankStatement(
            bank_name="Test Bank",
            account_number="12345-6",
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 1, 31),
            initial_balance=Decimal("1000.00"),
            final_balance=Decimal("1500.00"),
            currency="EUR",
            transactions=transactions
        )
        
        assert statement.total_expenses == Decimal("230.00")
    
    def test_bank_statement_net_flow(self):
        """Testa o cálculo do fluxo líquido."""
        transactions = [
            Transaction(
                date=datetime(2024, 1, 1),
                description="Salary",
                amount=Decimal("2500.00"),
                type=TransactionType.CREDIT
            ),
            Transaction(
                date=datetime(2024, 1, 2),
                description="Supermarket",
                amount=Decimal("150.00"),
                type=TransactionType.DEBIT
            )
        ]
        
        statement = BankStatement(
            bank_name="Test Bank",
            account_number="12345-6",
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 1, 31),
            initial_balance=Decimal("1000.00"),
            final_balance=Decimal("1500.00"),
            currency="EUR",
            transactions=transactions
        )
        
        assert statement.net_flow == Decimal("2350.00")  # 2500 - 150
    
    def test_bank_statement_transaction_count(self):
        """Testa a contagem de transações."""
        transactions = [
            Transaction(
                date=datetime(2024, 1, 1),
                description="Salary",
                amount=Decimal("2500.00"),
                type=TransactionType.CREDIT
            ),
            Transaction(
                date=datetime(2024, 1, 2),
                description="Supermarket",
                amount=Decimal("150.00"),
                type=TransactionType.DEBIT
            )
        ]
        
        statement = BankStatement(
            bank_name="Test Bank",
            account_number="12345-6",
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 1, 31),
            initial_balance=Decimal("1000.00"),
            final_balance=Decimal("1500.00"),
            currency="EUR",
            transactions=transactions
        )
        
        assert statement.transaction_count == 2
    
    def test_bank_statement_add_transaction(self):
        """Testa a adição de uma transação."""
        statement = BankStatement(
            bank_name="Test Bank",
            account_number="12345-6",
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 1, 31),
            initial_balance=Decimal("1000.00"),
            final_balance=Decimal("1500.00"),
            currency="EUR"
        )
        
        transaction = Transaction(
            date=datetime(2024, 1, 1),
            description="Test transaction",
            amount=Decimal("100.00"),
            type=TransactionType.CREDIT
        )
        
        assert len(statement.transactions) == 0
        statement.add_transaction(transaction)
        assert len(statement.transactions) == 1
        assert statement.transactions[0] == transaction
    
    def test_bank_statement_get_transactions_by_category(self):
        """Testa a obtenção de transações por categoria."""
        alimentacao_transaction = Transaction(
            date=datetime(2024, 1, 1),
            description="Supermarket",
            amount=Decimal("150.00"),
            type=TransactionType.DEBIT,
            category=TransactionCategory.ALIMENTACAO
        )
        
        transporte_transaction = Transaction(
            date=datetime(2024, 1, 2),
            description="Uber",
            amount=Decimal("25.00"),
            type=TransactionType.DEBIT,
            category=TransactionCategory.TRANSPORTE
        )
        
        statement = BankStatement(
            bank_name="Test Bank",
            account_number="12345-6",
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 1, 31),
            initial_balance=Decimal("1000.00"),
            final_balance=Decimal("1500.00"),
            currency="EUR",
            transactions=[alimentacao_transaction, transporte_transaction]
        )
        
        alimentacao_transactions = statement.get_transactions_by_category(TransactionCategory.ALIMENTACAO)
        transporte_transactions = statement.get_transactions_by_category(TransactionCategory.TRANSPORTE)
        
        assert len(alimentacao_transactions) == 1
        assert alimentacao_transactions[0] == alimentacao_transaction
        assert len(transporte_transactions) == 1
        assert transporte_transactions[0] == transporte_transaction
    
    def test_bank_statement_get_transactions_by_date_range(self):
        """Testa a obtenção de transações por período."""
        transaction1 = Transaction(
            date=datetime(2024, 1, 1),
            description="Transaction 1",
            amount=Decimal("100.00"),
            type=TransactionType.CREDIT
        )
        
        transaction2 = Transaction(
            date=datetime(2024, 1, 15),
            description="Transaction 2",
            amount=Decimal("200.00"),
            type=TransactionType.DEBIT
        )
        
        transaction3 = Transaction(
            date=datetime(2024, 2, 1),
            description="Transaction 3",
            amount=Decimal("300.00"),
            type=TransactionType.CREDIT
        )
        
        statement = BankStatement(
            bank_name="Test Bank",
            account_number="12345-6",
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 2, 28),
            initial_balance=Decimal("1000.00"),
            final_balance=Decimal("1500.00"),
            currency="EUR",
            transactions=[transaction1, transaction2, transaction3]
        )
        
        # Busca transações em janeiro de 2024
        jan_transactions = statement.get_transactions_by_date_range(
            datetime(2024, 1, 1),
            datetime(2024, 1, 31)
        )
        
        assert len(jan_transactions) == 2
        assert transaction1 in jan_transactions
        assert transaction2 in jan_transactions
        assert transaction3 not in jan_transactions


class TestAnalysisResult:
    """Testes para o modelo AnalysisResult."""
    
    def test_analysis_result_creation(self):
        """Testa a criação de um resultado de análise."""
        categories_summary = {
            TransactionCategory.ALIMENTACAO: Decimal("500.00"),
            TransactionCategory.TRANSPORTE: Decimal("200.00")
        }
        
        monthly_summary = {
            "2024-01": {
                "income": Decimal("2500.00"),
                "expenses": Decimal("700.00"),
                "balance": Decimal("1800.00")
            }
        }
        
        analysis_result = AnalysisResult(
            statement_id="stmt123",
            total_income=Decimal("2500.00"),
            total_expenses=Decimal("700.00"),
            net_flow=Decimal("1800.00"),
            currency="EUR",
            categories_summary=categories_summary,
            monthly_summary=monthly_summary,
            alerts=["High expenses this month"],
            insights=["Consider reducing transportation costs"],
            metadata={"transaction_count": 10}
        )
        
        assert analysis_result.statement_id == "stmt123"
        assert analysis_result.total_income == Decimal("2500.00")
        assert analysis_result.total_expenses == Decimal("700.00")
        assert analysis_result.net_flow == Decimal("1800.00")
        assert analysis_result.currency == "EUR"
        assert len(analysis_result.alerts) == 1
        assert len(analysis_result.insights) == 1
        assert analysis_result.metadata["transaction_count"] == 10