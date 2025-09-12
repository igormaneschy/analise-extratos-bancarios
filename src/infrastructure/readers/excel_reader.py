"""
Implementação de leitor de extratos em Excel.
"""
import re
import json
import os
import logging
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import List, Optional
import pandas as pd

from src.domain.models import BankStatement, Transaction, TransactionType
from src.domain.interfaces import StatementReader
from src.domain.exceptions import ParsingError
from src.utils.currency_utils import CurrencyUtils
from src.infrastructure.readers.base_reader import BaseStatementReader


logger = logging.getLogger(__name__)


class ExcelStatementReader(BaseStatementReader):
    """Leitor de extratos bancários em formato Excel."""

    def __init__(self):
        super().__init__()
        # Debug e mapeamentos externos
        self._external_mappings = None
        self._debug_enabled = os.getenv("EXCEL_READER_DEBUG", "").lower() in {"1", "true", "yes", "on"}
        self._logger = logging.getLogger(__name__)
        # Métricas simples de execução
        self._metrics = {
            "attempts": [],  # lista de dicts {strategy: str, ok: bool, error: Optional[str]}
            "chosen_strategy": None,
            "header_detect_row": None,
        }

    def _debug(self, msg: str, *args):
        if self._debug_enabled:
            try:
                self._logger.debug(msg, *args)
            except Exception:
                pass

    def _load_external_mappings(self):
        if self._external_mappings is not None:
            return self._external_mappings
        cfg_path = Path("config") / "excel_mappings.json"
        if cfg_path.exists():
            try:
                with cfg_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self._external_mappings = data
                        self._debug("Mapeamentos externos carregados: %s", list(data.keys()))
                        return data
            except Exception as e:
                self._debug("Falha ao ler excel_mappings.json: %s", e)
        self._external_mappings = None
        return None

    def can_read(self, file_path: Path) -> bool:
        """Verifica se pode ler o arquivo Excel."""
        return file_path.suffix.lower() in [".xlsx", ".xls"]

    def read(self, file_path: Path) -> BankStatement:
        try:
            # Lê o arquivo Excel
            excel_file = pd.ExcelFile(file_path)

            df = None
            # Para o banco BPI, tentar a aba 'Movimentos' (alguns arquivos possuem cabeçalho extenso)
            if "bpi" in file_path.name.lower():
                # Estratégia 1: header=None e normalização
                try:
                    raw = pd.read_excel(file_path, sheet_name="Movimentos", header=None)
                    df = self._normalize_dataframe(raw)
                    self._metrics["attempts"].append({"strategy": "movimentos_header_none_normalize", "ok": True})
                    self._metrics["chosen_strategy"] = "movimentos_header_none_normalize"
                    self._debug("Leitura BPI com header=None ok. Colunas: %s", list(df.columns))
                except Exception as e:
                    self._metrics["attempts"].append({"strategy": "movimentos_header_none_normalize", "ok": False, "error": str(e)})
                    df = None
                # Fallbacks
                if df is None or df.empty:
                    for attempt in (
                        dict(sheet_name="Movimentos", skiprows=11, header=0),
                        dict(sheet_name="Movimentos"),
                        dict(sheet_name=excel_file.sheet_names[0]),
                    ):
                        try:
                            tmp = pd.read_excel(file_path, **attempt)
                            tmp = self._normalize_dataframe(tmp)
                            df = tmp
                            self._metrics["attempts"].append({"strategy": f"fallback_{attempt}", "ok": True})
                            self._metrics["chosen_strategy"] = f"fallback_{attempt}"
                            self._debug("Fallback BPI aplicado: %s. Colunas: %s", attempt, list(df.columns))
                            break
                        except Exception as ex:
                            self._metrics["attempts"].append({"strategy": f"fallback_{attempt}", "ok": False, "error": str(ex)})
                            continue
                    if df is None:
                        try:
                            raw = pd.read_excel(file_path, sheet_name=excel_file.sheet_names[0], header=None)
                            df = self._normalize_dataframe(raw)
                            self._metrics["attempts"].append({"strategy": "first_sheet_header_none_normalize", "ok": True})
                            self._metrics["chosen_strategy"] = "first_sheet_header_none_normalize"
                            self._debug("Último fallback header=None normalizado. Colunas: %s", list(df.columns))
                        except Exception as e:
                            self._metrics["attempts"].append({"strategy": "first_sheet_header_none_normalize", "ok": False, "error": str(e)})
            else:
                # Assume que os dados estão na primeira aba
                try:
                    raw = pd.read_excel(file_path, sheet_name=excel_file.sheet_names[0], header=None)
                    df = self._normalize_dataframe(raw)
                    self._metrics["attempts"].append({"strategy": "first_sheet_header_none_normalize", "ok": True})
                    self._metrics["chosen_strategy"] = "first_sheet_header_none_normalize"
                except Exception as e:
                    self._metrics["attempts"].append({"strategy": "first_sheet_header_none_normalize", "ok": False, "error": str(e)})
                    df = pd.read_excel(file_path, sheet_name=excel_file.sheet_names[0])

            if df is None:
                raise ParsingError("Falha ao carregar planilha Excel")

            # Detecta a moeda automaticamente
            detected_currency = CurrencyUtils.extract_currency_from_dataframe(df)
            self.currency = detected_currency or "EUR"

            # Extrai as transações do DataFrame
            try:
                transactions = self._extract_transactions(df)
            except ParsingError:
                # Reaplica normalização leve e tenta novamente
                df2 = self._normalize_dataframe(df)
                transactions = self._extract_transactions(df2)

            # Cria o extrato bancário
            statement = BankStatement(
                bank_name=self._extract_bank_name(df),
                account_number=self._extract_account_number(df),
                period_start=self._extract_start_date(transactions),
                period_end=self._extract_end_date(transactions),
                initial_balance=self._extract_initial_balance(df),
                final_balance=self._extract_final_balance(df),
                currency=self.currency,  # Usa a moeda detectada
                transactions=transactions,
            )

            return statement

        except Exception as e:
            raise ParsingError(f"Erro ao ler o arquivo Excel: {str(e)}")

    # ----------------------------------------------------
    # Utilidades e mapeamentos
    # ----------------------------------------------------
    def _identify_bank(self, df) -> str:
        """Identifica o banco com base no conteúdo do DataFrame."""
        text = " ".join(df.columns.astype(str).str.lower()) + " " + " ".join(df.astype(str).values.flatten()).lower()
        if "bpi" in text:
            return "BPI"
        if "caixa" in text:
            return "Caixa"
        if "santander" in text:
            return "Santander"
        return "Desconhecido"

    def _get_column_mappings(self, bank_name: str):
        # Tenta mapeamentos externos
        ext = self._load_external_mappings()
        if isinstance(ext, dict):
            if bank_name in ext:
                return ext[bank_name]
            if "default" in ext:
                return ext["default"]
        if bank_name == "BPI":
            return {
                "date": [
                    "data mov.", "data mov", "data movimento", "data", "date", "data transacao", "transaction date", "data lancamento", "data valor", "data lançamento"
                ],
                "description": [
                    "descricao", "descrição", "description", "detalhes", "descricao movimento", "descrição movimento", "descricao movimentos", "descrição movimentos", "narrativa", "movimento", "descritivo", "descr."
                ],
                "amount": ["valor", "amount", "value", "montante", "quantia", "valor (eur)", "montante (eur)"],
                "credit": ["credito", "crédito", "credit", "credito (eur)", "crédito (eur)"],
                "debit": ["debito", "débito", "debit", "debito (eur)", "débito (eur)"],
            }
        elif bank_name == "Caixa":
            return {
                "date": ["data", "date", "data transacao"],
                "description": ["descricao", "description", "descrição", "movimento", "descritivo"],
                "amount": ["valor", "amount", "value", "valor (eur)"],
                "credit": ["credito", "crédito", "credit", "crédito (eur)"],
                "debit": ["debito", "débito", "debit", "débito (eur)"],
            }
        elif bank_name == "Santander":
            return {
                "date": ["data", "date", "data transacao", "data valor"],
                "description": ["descricao", "description", "descrição", "movimento", "descritivo"],
                "amount": ["valor", "amount", "value", "valor (eur)"],
                "credit": ["credito", "crédito", "credit", "crédito (eur)"],
                "debit": ["debito", "débito", "debit", "débito (eur)"],
            }
        else:
            return {
                "date": ["data mov.", "data mov", "data", "date", "data transacao", "transaction date", "data valor"],
                "description": ["descricao", "description", "descrição", "movimento", "descritivo"],
                "amount": ["valor", "amount", "value", "montante", "valor (eur)"],
                "credit": ["credito", "crédito", "credit", "crédito (eur)"],
                "debit": ["debito", "débito", "debit", "débito (eur)"],
            }

    def _normalize_text(self, text: str) -> str:
        """Normaliza texto removendo acentos e caixa."""
        import unicodedata

        text = unicodedata.normalize("NFD", str(text))
        text = "".join(c for c in text if unicodedata.category(c) != "Mn")
        return text.lower().strip()

    def _find_column(self, df: pd.DataFrame, possible_names: List[str]) -> Optional[str]:
        columns_lower = [self._normalize_text(col) for col in df.columns]
        # 1) Igualdade exata
        for name in possible_names:
            norm = self._normalize_text(name)
            if norm in columns_lower:
                return df.columns[columns_lower.index(norm)]
        # 2) Substring: candidato dentro do nome da coluna (mas não vice-versa)
        for name in possible_names:
            norm = self._normalize_text(name)
            for i, col_norm in enumerate(columns_lower):
                # Evita correspondências parciais que podem causar confusão
                # Especialmente evita "valor" em "data valor"
                if (norm and len(norm) > 3 and norm in col_norm and 
                    col_norm != norm and not (norm == "valor" and "data" in col_norm)):
                    return df.columns[i]
        # 3) Substring invertido: nome da coluna dentro do candidato (mas não vice-versa)
        for name in possible_names:
            norm = self._normalize_text(name)
            for i, col_norm in enumerate(columns_lower):
                if (col_norm and len(col_norm) > 3 and col_norm in norm and 
                    col_norm != norm and not (col_norm == "valor" and "data" in norm)):
                    return df.columns[i]
        return None


    def _parse_balance(self, balance_str: str) -> Optional[Decimal]:
        if balance_str is None:
            return None
        s = str(balance_str).strip()
        if s == "" or s.lower() in ["nan", "none", "null"]:
            return None
        cleaned = re.sub(r"[^\d,.-]", "", s.replace(" ", ""))
        if "," in cleaned and "." in cleaned:
            cleaned = cleaned.replace(".", "").replace(",", ".")
        elif "," in cleaned:
            cleaned = cleaned.replace(",", ".")
        try:
            return Decimal(cleaned)
        except Exception:
            return None

    def _normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Detecta e aplica a linha de cabeçalho real quando o arquivo traz preâmbulo.
        Heurística: encontra linha contendo ao menos duas dentre: data, descrição e (valor|crédito|débito).
        Aceita DataFrames com ou sem cabeçalho inicial (header=None ou header=0).
        """
        # Se já há colunas típicas, mantém
        try:
            cols_norm = [self._normalize_text(c) for c in df.columns]
            typical_any = any(any(k in c for k in ["data", "descricao", "descri", "valor", "credito", "debito"]) for c in cols_norm)
            if typical_any and not isinstance(df.columns[0], (int, float)):
                return df
        except Exception:
            pass

        date_candidates = {self._normalize_text(x) for x in [
            "data mov.", "data mov", "data movimento", "data", "date", "data transacao", "transaction date", "data lancamento", "data valor", "data lançamento"
        ]}
        desc_candidates = {self._normalize_text(x) for x in [
            "descricao", "descrição", "description", "detalhes", "descricao movimento", "descrição movimento", "movimento", "descritivo", "descr."
        ]}
        amt_candidates = {self._normalize_text(x) for x in [
            "valor", "amount", "value", "montante", "credito", "crédito", "debit", "debito", "débito", "saldo"
        ]}
        max_scan = min(len(df), 100)
        try:
            for i in range(max_scan):
                row_vals = [self._normalize_text(v) for v in df.iloc[i].tolist()]
                has_date = any(v in date_candidates or v.startswith("data") for v in row_vals)
                has_desc = any(v in desc_candidates or v.startswith("descr") or v.startswith("mov") for v in row_vals)
                has_amountish = any(v in amt_candidates for v in row_vals)
                if (has_date and has_desc) or (has_date and has_amountish) or (has_desc and has_amountish):
                    header_vals = df.iloc[i].tolist()
                    df2 = df.iloc[i + 1 :].copy()
                    df2.columns = header_vals
                    self._metrics["header_detect_row"] = i
                    return df2.reset_index(drop=True)
        except Exception as e:
            self._debug("Falha na normalização de cabeçalho: %s", e)
            return df
        return df

    # ----------------------------------------------------
    # Extrações
    # ----------------------------------------------------
    def _extract_transactions(self, df) -> List[Transaction]:
        transactions: List[Transaction] = []
        self.bank_name = self._identify_bank(df)
        column_map = self._get_column_mappings(self.bank_name)

        date_col = self._find_column(df, column_map["date"])
        description_col = self._find_column(df, column_map["description"])
        amount_col = self._find_column(df, column_map["amount"]) if "amount" in column_map else None
        credit_col = self._find_column(df, column_map.get("credit", []))
        debit_col = self._find_column(df, column_map.get("debit", []))

        if not date_col or not description_col or (not amount_col and not (credit_col or debit_col)):
            raise ParsingError(
                f"Não foi possível identificar as colunas necessárias no Excel para o banco {self.bank_name}"
            )

        self._debug("Colunas detectadas -> data: %s, desc: %s, amount: %s, credit: %s, debit: %s",
                    date_col, description_col, amount_col, credit_col, debit_col)

        for _, row in df.iterrows():
            try:
                amount_raw = None
                if amount_col:
                    amount_raw = str(row[amount_col]).strip()
                else:
                    credit_raw = str(row[credit_col]).strip() if credit_col else ""
                    debit_raw = str(row[debit_col]).strip() if debit_col else ""
                    if credit_raw and credit_raw.lower() not in ["nan", "none", "null", ""]:
                        amount_raw = credit_raw
                    elif debit_raw and debit_raw.lower() not in ["nan", "none", "null", ""]:
                        amount_raw = f"-{debit_raw}" if not str(debit_raw).startswith("-") else debit_raw
                    else:
                        amount_raw = ""

                # Ignora linhas vazias/metadados
                if amount_raw == "" or amount_raw.lower() in ["nan", "none", "null"]:
                    continue

                amount = self._parse_amount(amount_raw)
                ttype = self._determine_transaction_type(amount, str(row[description_col]).strip())
                date_val = self._parse_date(str(row[date_col]).strip())
                description = str(row[description_col]).strip()

                # Armazena o valor absoluto na transação
                amount = abs(amount)

                transaction = Transaction(
                    date=date_val,
                    description=description,
                    amount=amount,
                    type=ttype,
                )
                transactions.append(transaction)
            except Exception:
                # Ignora linhas inválidas
                continue

        return transactions

    # Métodos auxiliares para extrair outras informações do DataFrame
    def _extract_bank_name(self, df) -> str:
        # Para o BPI, extrai o nome do banco da aba 'Movimentos'
        if self.bank_name == "BPI":
            return "Banco BPI"
        return self.bank_name or "Desconhecido"

    def _extract_account_number(self, df) -> str:
        # Para o BPI, tenta extrair o número da conta da aba 'Movimentos'
        if self.bank_name == "BPI":
            for col in df.columns:
                for val in df[col].astype(str):
                    if re.match(r"\d{1,2}-\d{7,}\.??\d*", val):
                        return val
        return ""

    def _extract_initial_balance(self, df) -> Decimal:
        """Extrai saldo inicial procurando por 'Saldo Disponível' e lendo o valor logo abaixo na mesma coluna (como em testes)."""
        meta_col = self._find_column(df, ["meta", "detalhes", "observacoes", "observações"])
        search_cols = [meta_col] if meta_col else list(df.columns)
        for col in search_cols:
            for i in range(len(df)):
                cell = df.iloc[i][col]
                if self._normalize_text(cell) == "saldo disponivel":
                    if i + 1 < len(df):
                        value_cell = df.iloc[i + 1][col]
                        bal = self._parse_balance(value_cell)
                        if bal is not None:
                            return bal
        return Decimal("0.00")

    def _extract_final_balance(self, df) -> Decimal:
        """Extrai saldo final procurando por padrões como 'Saldo 1.234,56' de baixo para cima."""
        meta_col = self._find_column(df, ["meta", "detalhes", "observacoes", "observações"])
        search_cols = [meta_col] if meta_col else list(df.columns)
        pattern = re.compile(r"saldo\s*([\d\.,]+)", re.IGNORECASE)
        for i in range(len(df) - 1, -1, -1):
            for col in search_cols:
                cell = str(df.iloc[i][col])
                m = pattern.search(cell)
                if m:
                    bal = self._parse_balance(m.group(1))
                    if bal is not None:
                        return bal
        return Decimal("0.00")