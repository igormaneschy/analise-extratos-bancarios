#!/usr/bin/env python3
"""
CLI principal para análise de extratos bancários.
"""
import sys
from pathlib import Path
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Imports de src removidos do topo e movidos para dentro da função analyze para permitir testes sem src no PYTHONPATH.
# Serão importados tardiamente dentro do comando analyze.


console = Console()


@click.group()
def cli():
    """Sistema de Análise de Extratos Bancários"""
    pass


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--output', '-o', help='Caminho para salvar o relatório')
@click.option('--format', '-f', type=click.Choice(['text', 'markdown']), default='text', help='Formato do relatório')
def analyze(file_path, output, format):
    """Analisa um extrato bancário em PDF, Excel ou CSV."""
    try:
        # Imports tardios para evitar dependência em tempo de import do módulo
        from src.application.use_cases import ExtractAnalyzer
        from src.domain.exceptions import DomainException  # noqa: F401 - usado no except
        from src.utils.currency_utils import CurrencyUtils

        analyzer = ExtractAnalyzer()

        # Se especificou formato markdown, troca o gerador
        if format == 'markdown':
            from src.infrastructure.reports.text_report import MarkdownReportGenerator
            analyzer.use_case.report_generator = MarkdownReportGenerator()

        result, report, statement = analyzer.analyze_file(file_path, output)

        # Formata valores com a moeda correta
        currency_symbol = CurrencyUtils.get_currency_symbol(result.currency)

        # Mostra resumo no console
        console.print(Panel.fit(
            f"[bold green]✓ Análise concluída![/bold green]\n\n"
            f"📊 Total de transações: {result.metadata.get('transaction_count', 0)}\n"
            f"💰 Receitas: {currency_symbol}{result.total_income:,.2f}\n"
            f"💸 Despesas: {currency_symbol}{result.total_expenses:,.2f}\n"
            f"📈 Saldo: {currency_symbol}{result.net_flow:,.2f}"
        ))

        # Mostra alertas, se houver
        if result.alerts:
            alert_table = Table(title="⚠️  Alertas", style="yellow")
            alert_table.add_column("Alerta", style="yellow")
            for alert in result.alerts:
                alert_table.add_row(alert)
            console.print(alert_table)

        # Mostra insights, se houver
        if result.insights:
            insight_table = Table(title="💡 Insights")
            insight_table.add_column("Insight", style="cyan")
            for insight in result.insights:
                insight_table.add_row(insight)
            console.print(insight_table)

        # Salva ou mostra o relatório completo
        if output:
            console.print(f"[green]Relatório salvo em:[/green] {output}")
        else:
            console.print("\n[bold]Relatório completo:[/bold]\n")
            console.print(report)

    except Exception as e:
        # Tenta identificar DomainException para mensagem específica
        try:
            from src.domain.exceptions import DomainException  # type: ignore
            if isinstance(e, DomainException):
                console.print(f"[red]Erro de domínio:[/red] {str(e)}")
                sys.exit(1)
        except Exception:
            pass
        console.print(f"[red]Erro inesperado:[/red] {str(e)}")
        sys.exit(1)


@cli.command()
@click.argument('output_path', type=click.Path())
def sample(output_path):
    """Cria um arquivo de instruções de exemplo."""
    instructions = """# Instruções para uso do Sistema de Análise de Extratos Bancários

## Formatos Suportados

O sistema suporta os seguintes formatos de extrato:
1. PDF - Extratos em formato PDF
2. Excel - Extratos em formato XLSX ou XLS
3. CSV - Extratos em formato CSV

## Estrutura Esperada para CSV

Para que o sistema possa processar corretamente um arquivo CSV, ele deve conter as seguintes colunas:

### Colunas Obrigatórias:
- Data da transação (formatos aceitos: DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD)
- Descrição da transação
- Valor da transação (positivo para receitas, negativo para despesas)

### Colunas Opcionais:
- Saldo após a transação
- Número da conta
- Saldo inicial/final

### Nomes de Colunas Aceitos:

#### Para Data:
- data
- date
- data transacao
- transaction date

#### Para Descrição:
- descricao
- description
- descrição

#### Para Valor:
- valor
- amount
- value
- montante

#### Para Saldo:
- saldo
- balance
- saldo após
- balance after

## Exemplo de Estrutura CSV:

data,descricao,valor,saldo
01/01/2023,Salário Janeiro,2500.00,2500.00
02/01/2023,Supermercado,-150.50,2349.50
03/01/2023,Conta de Luz,-80.00,2269.50
05/01/2023,Restaurante,-65.75,2203.75

## Moedas Suportadas:

O sistema detecta automaticamente a moeda do extrato:
- EUR (Euro) - Padrão
- USD (Dólar Americano)
- BRL (Real Brasileiro)
- GBP (Libra Esterlina)
- JPY (Iene Japonês)
- CHF (Franco Suíço)
- CAD (Dólar Canadense)
- AUD (Dólar Australiano)

## Executando a Análise:

Para analisar um extrato, use o comando:

```bash
python main.py analyze caminho/para/seu/extrato.pdf
python main.py analyze caminho/para/seu/extrato.xlsx
python main.py analyze caminho/para/seu/extrato.csv
```

Para salvar o relatório em um arquivo:

```bash
python main.py analyze caminho/para/seu/extrato.csv --output relatorio.txt
```

Para gerar um relatório em formato Markdown:

```bash
python main.py analyze caminho/para/seu/extrato.csv --format markdown --output relatorio.md
```
"""
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(instructions)
        console.print(f"[green]✓[/green] Arquivo de instruções criado em: {output_path}")
    except Exception as e:
        console.print(f"[red]✗[/red] Erro ao criar arquivo de instruções: {str(e)}")
        sys.exit(1)


@cli.command()
def version():
    """Mostra a versão do sistema."""
    console.print("[bold blue]Sistema de Análise de Extratos Bancários[/bold blue]")
    console.print("Versão: 1.0.0")
    console.print("Formatos suportados: PDF, Excel, CSV")


if __name__ == '__main__':
    cli()