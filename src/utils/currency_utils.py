"""
Utilitários para formatação e detecção de moedas.
"""
import re
from typing import Tuple, Optional


class CurrencyUtils:
    """Utilitários para trabalhar com moedas."""
    
    # Mapeamento de símbolos de moeda
    CURRENCY_SYMBOLS = {
        'EUR': '€',
        'USD': '$',
        'BRL': 'R$',
        'GBP': '£',
        'JPY': '¥',
        'CHF': 'CHF',
        'CAD': 'C$',
        'AUD': 'A$'
    }
    
    # Padrões para detectar moedas em texto
    CURRENCY_PATTERNS = [
        (r'€\s*[\d.,]+|[\d.,]+\s*€', 'EUR'),
        (r'R\$\s*[\d.,]+|[\d.,]+\s*R\$', 'BRL'),
        (r'\$\s*[\d.,]+|[\d.,]+\s*\$', 'USD'),
        (r'£\s*[\d.,]+|[\d.,]+\s*£', 'GBP'),
        (r'¥\s*[\d.,]+|[\d.,]+\s*¥', 'JPY'),
        (r'CHF\s*[\d.,]+|[\d.,]+\s*CHF', 'CHF'),
    ]
    
    @classmethod
    def detect_currency_from_text(cls, text: str) -> str:
        """
        Detecta a moeda a partir de um texto.

        Args:
            text: Texto para análise

        Returns:
            Código da moeda (ex: 'EUR', 'BRL', 'USD') ou 'EUR' como padrão
        """
        if not text:
            return 'EUR'

        text = str(text).upper()

        # Procura por padrões de moeda
        for pattern, currency in cls.CURRENCY_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return currency

        # Procura por códigos de moeda explícitos (mas apenas como palavras completas)
        for currency_code in cls.CURRENCY_SYMBOLS.keys():
            # Usar \b para delimitar palavras completas
            if re.search(r'\b' + re.escape(currency_code) + r'\b', text):
                return currency_code

        # Padrão para Europa (assume EUR se não encontrar nada)
        return 'EUR'
    
    @classmethod
    def get_currency_symbol(cls, currency_code: str) -> str:
        """
        Retorna o símbolo da moeda.
        
        Args:
            currency_code: Código da moeda (ex: 'EUR', 'BRL')
            
        Returns:
            Símbolo da moeda (ex: '€', 'R$')
        """
        return cls.CURRENCY_SYMBOLS.get(currency_code.upper(), currency_code)
    
    @classmethod
    def format_currency(cls, amount: float, currency_code: str) -> str:
        """
        Formata um valor monetário com a moeda apropriada.
        
        Args:
            amount: Valor a ser formatado
            currency_code: Código da moeda
            
        Returns:
            Valor formatado com símbolo da moeda
        """
        symbol = cls.get_currency_symbol(currency_code)
        
        # Formatação específica por moeda
        if currency_code == 'EUR':
            # Formato europeu: € 1.234,56
            return f"{symbol} {amount:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        elif currency_code == 'BRL':
            # Formato brasileiro: R$ 1.234,56
            return f"{symbol} {amount:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        else:
            # Formato padrão: $ 1,234.56
            return f"{symbol} {amount:,.2f}"
    
    @classmethod
    def extract_currency_from_dataframe(cls, df) -> str:
        """
        Extrai a moeda de um DataFrame do pandas.

        Args:
            df: DataFrame para análise

        Returns:
            Código da moeda detectada ou None se não detectada
        """
        import pandas as pd

        # Converte todo o DataFrame para string e procura por padrões
        text_content = ""

        # Analisa as primeiras 20 linhas para detectar moeda
        for idx in range(min(20, len(df))):
            row = df.iloc[idx]
            for col in row:
                if pd.notna(col):
                    text_content += str(col) + " "

        currency = cls.detect_currency_from_text(text_content)

        # Lista de moedas padrão para aceitar mesmo que não estejam explicitamente no texto
        default_currencies = ['EUR', 'BRL', 'USD', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD']

        # Retorna None se a moeda detectada não estiver explicitamente no texto,
        # exceto para moedas padrão
        if currency and (currency not in text_content) and (currency not in default_currencies):
            return None
        return currency