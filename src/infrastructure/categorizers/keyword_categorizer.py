"""
Implementação de categorizador simples de transações baseado em palavras-chave.
"""
import re
from typing import Dict, List

from src.domain.models import Transaction, TransactionCategory
from src.domain.interfaces import TransactionCategorizer


class KeywordCategorizer(TransactionCategorizer):
    """Categorizador de transações baseado em palavras-chave."""
    
    def __init__(self):
        self.keywords = self._load_keywords()
    
    def _load_keywords(self) -> Dict[TransactionCategory, List[str]]:
        """Define palavras-chave para cada categoria."""
        return {
            TransactionCategory.ALIMENTACAO: [
                'restaurante', 'lanchonete', 'padaria', 'mercado', 'supermercado',
                'açougue', 'feira', 'ifood', 'uber eats', 'rappi', 'delivery',
                'pizza', 'hamburguer', 'sushi', 'churrasco', 'bar', 'café',
                'cantina', 'refeitorio', 'almoço', 'jantar', 'lanche'
            ],
            
            TransactionCategory.TRANSPORTE: [
                'uber', '99', 'cabify', 'taxi', 'combustivel', 'gasolina',
                'etanol', 'alcool', 'posto', 'estacionamento', 'pedagio',
                'onibus', 'metro', 'trem', 'passagem', 'viagem', 'rodoviaria',
                'aeroporto', 'aviao', 'voo', 'locadora', 'aluguel carro'
            ],
            
            TransactionCategory.MORADIA: [
                'aluguel', 'condominio', 'iptu', 'luz', 'energia', 'agua',
                'gas', 'internet', 'telefone', 'celular', 'vivo', 'claro',
                'tim', 'oi', 'net', 'sky', 'manutencao', 'reforma', 'obra',
                'material construcao', 'pintura', 'eletricista', 'encanador'
            ],
            
            TransactionCategory.SAUDE: [
                'farmacia', 'drogaria', 'medicamento', 'remedio', 'hospital',
                'clinica', 'medico', 'consulta', 'exame', 'laboratorio',
                'plano saude', 'unimed', 'amil', 'sulamerica', 'bradesco saude',
                'dentista', 'ortodontia', 'fisioterapia', 'psicologia'
            ],
            
            TransactionCategory.EDUCACAO: [
                'escola', 'faculdade', 'universidade', 'curso', 'livro',
                'livraria', 'apostila', 'material escolar', 'papelaria',
                'mensalidade', 'matricula', 'udemy', 'coursera', 'alura',
                'ingles', 'idioma', 'pos graduacao', 'mba', 'mestrado'
            ],
            
            TransactionCategory.LAZER: [
                'cinema', 'teatro', 'show', 'festa', 'evento', 'ingresso',
                'netflix', 'spotify', 'amazon prime', 'disney', 'hbo',
                'game', 'jogo', 'steam', 'playstation', 'xbox', 'nintendo',
                'viagem', 'hotel', 'pousada', 'airbnb', 'turismo'
            ],
            
            TransactionCategory.COMPRAS: [
                'shopping', 'loja', 'roupa', 'calcado', 'tenis', 'sapato',
                'acessorio', 'relogio', 'oculos', 'bolsa', 'mochila',
                'eletronico', 'celular', 'notebook', 'computador', 'tv',
                'amazon', 'mercado livre', 'americanas', 'magazine', 'casas bahia'
            ],
            
            TransactionCategory.SERVICOS: [
                'cartorio', 'correios', 'sedex', 'pac', 'seguro', 'advogado',
                'contador', 'mecanico', 'oficina', 'lavanderia', 'costura',
                'salao', 'cabeleireiro', 'barbearia', 'manicure', 'estetica',
                'academia', 'personal', 'crossfit', 'pilates', 'yoga'
            ],
            
            TransactionCategory.TRANSFERENCIA: [
                'transferencia', 'ted', 'doc', 'pix', 'deposito', 'saque',
                'envio', 'recebido', 'transf', 'dep', 'saq'
            ],
            
            TransactionCategory.INVESTIMENTO: [
                'investimento', 'aplicacao', 'resgate', 'rendimento', 'cdb',
                'lci', 'lca', 'tesouro', 'poupanca', 'fundo', 'acao',
                'bolsa', 'b3', 'corretora', 'xp', 'rico', 'clear', 'nuinvest'
            ],
            
            TransactionCategory.SALARIO: [
                'salario', 'pagamento', 'vencimento', 'remuneracao', 'holerite',
                'adiantamento', '13o', 'decimo terceiro', 'ferias', 'rescisao',
                'inss', 'fgts', 'vale', 'beneficio', 'auxilio'
            ]
        }
    
    def categorize(self, transaction: Transaction) -> Transaction:
        """Categoriza uma transação baseado em sua descrição."""
        description_lower = transaction.description.lower()
        
        # Remove acentos para melhor matching
        description_normalized = self._normalize_text(description_lower)
        
        # Tenta encontrar categoria por palavras-chave
        for category, keywords in self.keywords.items():
            for keyword in keywords:
                keyword_normalized = self._normalize_text(keyword.lower())
                if keyword_normalized in description_normalized:
                    transaction.category = category
                    return transaction
        
        # Se não encontrou categoria, mantém como não categorizado
        transaction.category = TransactionCategory.NAO_CATEGORIZADO
        return transaction
    
    def _normalize_text(self, text: str) -> str:
        """Normaliza texto removendo acentos e caracteres especiais."""
        # Remove acentos comuns
        replacements = {
            'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a', 'ä': 'a',
            'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
            'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
            'ó': 'o', 'ò': 'o', 'õ': 'o', 'ô': 'o', 'ö': 'o',
            'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
            'ç': 'c', 'ñ': 'n'
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Remove caracteres especiais mantendo espaços e números
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        
        # Remove espaços múltiplos
        text = ' '.join(text.split())
        
        return text