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

from src.application.use_cases import ExtractAnalyzer
from src.domain.exceptions import DomainException
from src.utils.currency_utils import CurrencyUtils


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
    """Analisa um extrato bancário em PDF ou Excel."""
    try:
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
            f"💰 Receitas: {CurrencyUtils.format_currency(result.total_income, result.currency)}\n"
            f"💸 Despesas: {CurrencyUtils.format_currency(result.total_expenses, result.currency)}\n"
            f"📈 Saldo: {CurrencyUtils.format_currency(result.net_flow, result.currency)}",
            title="Resumo da Análise"
        ))

        # Mostra alertas se houver
        if result.alerts:
            console.print("\n[bold yellow]⚠️  Alertas:[/bold yellow]")
            for alert in result.alerts:
                console.print(f"  • {alert}")

        # Mostra insights
        if result.insights:
            console.print("\n[bold cyan]💡 Insights:[/bold cyan]")
            for insight in result.insights:
                console.print(f"  • {insight}")

        # Salva ou mostra relatório completo
        if output:
            console.print(f"\n[green]✓ Relatório salvo em: {output}[/green]")
        else:
            console.print("\n[dim]Use --output para salvar o relatório completo[/dim]")
            if click.confirm("\nDeseja ver o relatório completo?"):
                console.print("\n" + report)

    except FileNotFoundError:
        console.print(f"[bold red]❌ Erro: Arquivo '{file_path}' não encontrado![/bold red]")
        sys.exit(1)
    except DomainException as e:
        console.print(f"[bold red]❌ Erro: {str(e)}[/bold red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]❌ Erro inesperado: {str(e)}[/bold red]")
        console.print("[dim]Use --debug para mais informações[/dim]")
        sys.exit(1)


@cli.command()
def sample():
    """Cria um arquivo de exemplo para teste."""
    sample_dir = Path("data/samples")
    sample_dir.mkdir(parents=True, exist_ok=True)
    
    sample_file = sample_dir / "exemplo_instrucoes.txt"
    
    content = """
INSTRUÇÕES PARA TESTE DO SISTEMA
================================

Para testar o sistema de análise de extratos, você precisa:

1. Obter um extrato bancário em PDF ou Excel
   - Pode ser do seu banco (Santander, BBVA, CaixaBank, BPI, etc.)
   - Certifique-se de que é um PDF com texto (não escaneado) ou Excel válido

2. Colocar o arquivo na pasta 'data/samples/'
   - Exemplo: data/samples/extrato_janeiro.pdf
   - Exemplo: data/samples/extrato_janeiro.xlsx

3. Executar a análise:
   python main.py analyze data/samples/extrato_janeiro.pdf

4. Para salvar o relatório:
   python main.py analyze data/samples/extrato_janeiro.pdf --output relatorio.txt

5. Para gerar relatório em Markdown:
   python main.py analyze data/samples/extrato_janeiro.pdf --output relatorio.md --format markdown

FORMATO ESPERADO DO PDF
-----------------------
O sistema espera encontrar no PDF:
- Data das transações (formato DD/MM/AAAA ou DD/MM)
- Descrição da transação
- Valor (com símbolo de moeda apropriado: €, R$, $, etc.)
- Saldo (opcional)

FORMATO ESPERADO DO EXCEL
-------------------------
O sistema espera encontrar no Excel:
- Coluna com datas das transações
- Coluna com descrições
- Coluna com valores (positivos para crédito, negativos para débito)
- Cabeçalhos identificáveis (ex: "Data Mov.", "Descrição", "Valor")

LIMITAÇÕES ATUAIS
-----------------
- Suporta apenas PDFs com texto extraível
- Não processa imagens ou PDFs escaneados
- Categorização básica por palavras-chave
- Pode precisar ajustes para formatos específicos de bancos

PRÓXIMAS MELHORIAS
------------------
- Integração com IA para melhor categorização
- Suporte para mais formatos de arquivo
- Detecção automática de padrões de bancos
- Interface web
- Análise de tendências temporais

MOEDAS SUPORTADAS
-----------------
O sistema detecta automaticamente as seguintes moedas:
- EUR (€) - Euro
- BRL (R$) - Real Brasileiro
- USD ($) - Dólar Americano
- GBP (£) - Libra Esterlina
- JPY (¥) - Iene Japonês
- CHF - Franco Suíço
- CAD (C$) - Dólar Canadense
- AUD (A$) - Dólar Australiano
"""
    
    sample_file.write_text(content.strip(), encoding='utf-8')
    console.print(f"[green]✓ Arquivo de exemplo criado em: {sample_file}[/green]")


@cli.command()
def version():
    """Mostra a versão do sistema."""
    console.print("[bold blue]Sistema de Análise de Extratos Bancários[/bold blue]")
    console.print("Versão: 1.0.0")
    console.print("Desenvolvido para análise automatizada de extratos bancários")


if __name__ == '__main__':
    cli()