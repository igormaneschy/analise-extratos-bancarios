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
from rich import print as rprint

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.application.use_cases import ExtractAnalyzer
from src.domain.exceptions import DomainException


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
    """Analisa um extrato bancário em PDF."""
    try:
        with console.status("[bold green]Analisando extrato...") as status:
            analyzer = ExtractAnalyzer()
            
            # Se especificou formato markdown, troca o gerador
            if format == 'markdown':
                from src.infrastructure.reports.text_report import MarkdownReportGenerator
                analyzer.use_case.report_generator = MarkdownReportGenerator()
            
            result, report = analyzer.analyze_file(file_path, output)
        
        # Mostra resumo no console
        console.print(Panel.fit(
            f"[bold green]✓ Análise concluída![/bold green]\n\n"
            f"📊 Total de transações: {result.metadata.get('transaction_count', 0)}\n"
            f"💰 Receitas: € {result.total_income:,.2f}\n"
            f"💸 Despesas: € {result.total_expenses:,.2f}\n"
            f"📈 Saldo: € {result.net_flow:,.2f}",
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

1. Obter um extrato bancário em PDF
   - Pode ser do seu banco (Itaú, Bradesco, Santander, etc.)
   - Certifique-se de que é um PDF com texto (não escaneado)

2. Colocar o arquivo PDF na pasta 'data/samples/'
   - Exemplo: data/samples/extrato_janeiro.pdf

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
- Valor (com R$ ou indicação de C/D para crédito/débito)
- Saldo (opcional)

LIMITAÇÕES ATUAIS
-----------------
- Suporta apenas PDFs com texto extraível
- Não processa imagens ou PDFs escaneados
- Categorização básica por palavras-chave
- Pode precisar ajustes para formatos específicos de bancos

PRÓXIMAS MELHORIAS
------------------
- Integração com IA para melhor categorização
- Suporte para Excel e CSV
- Detecção automática de padrões de bancos
- Interface web
"""
    
    with open(sample_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    console.print(Panel.fit(
        f"[bold green]✓ Arquivo de instruções criado![/bold green]\n\n"
        f"📄 Local: {sample_file}\n\n"
        f"[yellow]⚠️  Importante:[/yellow]\n"
        f"Você precisa adicionar um PDF de extrato real para testar.\n"
        f"Leia as instruções no arquivo criado.",
        title="Instruções de Teste"
    ))


@cli.command()
def info():
    """Mostra informações sobre o sistema."""
    table = Table(title="Sistema de Análise de Extratos Bancários")
    
    table.add_column("Componente", style="cyan", no_wrap=True)
    table.add_column("Status", style="green")
    table.add_column("Descrição", style="white")
    
    table.add_row("Leitor PDF", "✓ Implementado", "Extrai dados de PDFs bancários")
    table.add_row("Categorizador", "✓ Implementado", "Categoriza por palavras-chave")
    table.add_row("Analisador", "✓ Implementado", "Gera insights e alertas")
    table.add_row("Relatórios", "✓ Implementado", "Texto e Markdown")
    table.add_row("IA", "⏳ Planejado", "Integração com GPT/Claude")
    table.add_row("Excel/CSV", "⏳ Planejado", "Suporte adicional")
    
    console.print(table)
    
    console.print("\n[bold]Categorias suportadas:[/bold]")
    categories = [
        "Alimentação", "Transporte", "Moradia", "Saúde", 
        "Educação", "Lazer", "Compras", "Serviços",
        "Transferência", "Investimento", "Salário"
    ]
    for cat in categories:
        console.print(f"  • {cat}")


if __name__ == '__main__':
    cli()