#!/usr/bin/env python3
"""
Script para validar conformidade com as regras do projeto.
"""
import os
import sys
import ast
import re
from pathlib import Path
from typing import List, Dict, Tuple
import subprocess

class RulesValidator:
    """Validador de regras do projeto."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.violations = []
        self.metrics = {}
    
    def validate_clean_architecture(self) -> Dict[str, int]:
        """Valida conformidade com Clean Architecture."""
        violations = 0
        domain_files = list(self.project_root.glob("src/domain/**/*.py"))
        
        for file_path in domain_files:
            if file_path.name == "__init__.py":
                continue
                
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verificar imports de outras camadas
            if re.search(r'from src\.(application|infrastructure|presentation)', content):
                self.violations.append(f"Domain importa outras camadas: {file_path}")
                violations += 1
            
            if re.search(r'import src\.(application|infrastructure|presentation)', content):
                self.violations.append(f"Domain importa outras camadas: {file_path}")
                violations += 1
        
        self.metrics['clean_architecture_violations'] = violations
        return {'violations': violations, 'files_checked': len(domain_files)}
    
    def validate_solid_principles(self) -> Dict[str, int]:
        """Valida conformidade com princípios SOLID."""
        violations = 0
        files_checked = 0
        
        for file_path in self.project_root.glob("src/**/*.py"):
            if file_path.name == "__init__.py":
                continue
                
            files_checked += 1
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                # Verificar SRP - classes com muitos métodos
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                        if len(methods) > 10:
                            self.violations.append(f"SRP violado: {file_path}:{node.lineno} - Classe com {len(methods)} métodos")
                            violations += 1
                
            except Exception as e:
                self.violations.append(f"Erro ao analisar {file_path}: {e}")
                violations += 1
        
        self.metrics['solid_violations'] = violations
        return {'violations': violations, 'files_checked': files_checked}
    
    def validate_dry_kiss(self) -> Dict[str, int]:
        """Valida conformidade com DRY/KISS/YAGNI."""
        violations = 0
        
        # Verificar duplicação de código
        try:
            result = subprocess.run(['duplo', 'src/', '--html', 'duplo-report.html'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                self.violations.append("Ferramenta duplo não encontrada ou erro na execução")
                violations += 1
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.violations.append("Ferramenta duplo não disponível")
            violations += 1
        
        # Verificar complexidade ciclomática
        try:
            result = subprocess.run(['radon', 'cc', 'src/', '--min', 'B'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                complex_functions = len([line for line in result.stdout.split('\n') if 'B' in line or 'C' in line or 'D' in line])
                if complex_functions > 0:
                    self.violations.append(f"KISS violado: {complex_functions} funções com alta complexidade")
                    violations += complex_functions
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.violations.append("Ferramenta radon não disponível")
            violations += 1
        
        self.metrics['dry_kiss_violations'] = violations
        return {'violations': violations}
    
    def validate_testing_policy(self) -> Dict[str, int]:
        """Valida conformidade com política de testes."""
        violations = 0
        
        # Verificar cobertura de testes
        try:
            result = subprocess.run(['python', '-m', 'pytest', 'tests/unit/', '--cov=src', '--cov-report=term-missing'], 
                                  capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                # Extrair cobertura da saída
                coverage_match = re.search(r'TOTAL\s+(\d+)\s+(\d+)\s+(\d+)%', result.stdout)
                if coverage_match:
                    total_lines = int(coverage_match.group(1))
                    missed_lines = int(coverage_match.group(2))
                    coverage_percent = int(coverage_match.group(3))
                    
                    if coverage_percent < 80:
                        self.violations.append(f"Cobertura de testes insuficiente: {coverage_percent}% (mínimo: 80%)")
                        violations += 1
                    
                    self.metrics['test_coverage'] = coverage_percent
                    self.metrics['total_lines'] = total_lines
                    self.metrics['missed_lines'] = missed_lines
            else:
                self.violations.append("Falha na execução dos testes")
                violations += 1
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.violations.append("Ferramenta pytest não disponível")
            violations += 1
        
        self.metrics['testing_violations'] = violations
        return {'violations': violations}
    
    def validate_dev_history(self) -> Dict[str, int]:
        """Valida conformidade com histórico de desenvolvimento."""
        violations = 0
        
        history_file = self.project_root / "dev_history.md"
        if not history_file.exists():
            self.violations.append("dev_history.md não encontrado")
            violations += 1
        else:
            with open(history_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verificar se há entradas recentes
            if not re.search(r'\[2025-\d{2}-\d{2}\]', content):
                self.violations.append("Nenhuma entrada recente encontrada em dev_history.md")
                violations += 1
            
            # Verificar formato das entradas
            entries = re.findall(r'\[(\d{4}-\d{2}-\d{2})\]\s*-\s*(\w+)', content)
            if len(entries) == 0:
                self.violations.append("Nenhuma entrada válida encontrada em dev_history.md")
                violations += 1
        
        self.metrics['dev_history_violations'] = violations
        return {'violations': violations}
    
    def generate_report(self) -> str:
        """Gera relatório de validação."""
        report = []
        report.append("# Relatório de Validação das Regras")
        report.append("=" * 50)
        report.append("")
        
        # Resumo das métricas
        report.append("## Métricas Gerais")
        report.append(f"- Violações de Clean Architecture: {self.metrics.get('clean_architecture_violations', 0)}")
        report.append(f"- Violações de SOLID: {self.metrics.get('solid_violations', 0)}")
        report.append(f"- Violações de DRY/KISS/YAGNI: {self.metrics.get('dry_kiss_violations', 0)}")
        report.append(f"- Violações de Testes: {self.metrics.get('testing_violations', 0)}")
        report.append(f"- Violações de Histórico: {self.metrics.get('dev_history_violations', 0)}")
        report.append("")
        
        # Cobertura de testes
        if 'test_coverage' in self.metrics:
            report.append("## Cobertura de Testes")
            report.append(f"- Cobertura atual: {self.metrics['test_coverage']}%")
            report.append(f"- Linhas totais: {self.metrics['total_lines']}")
            report.append(f"- Linhas não cobertas: {self.metrics['missed_lines']}")
            report.append("")
        
        # Violações detalhadas
        if self.violations:
            report.append("## Violações Encontradas")
            for i, violation in enumerate(self.violations, 1):
                report.append(f"{i}. {violation}")
            report.append("")
        else:
            report.append("## ✅ Nenhuma violação encontrada!")
            report.append("")
        
        # Recomendações
        report.append("## Recomendações")
        if self.metrics.get('clean_architecture_violations', 0) > 0:
            report.append("- Revisar imports no Domain para garantir independência")
        if self.metrics.get('solid_violations', 0) > 0:
            report.append("- Refatorar classes com muitas responsabilidades")
        if self.metrics.get('dry_kiss_violations', 0) > 0:
            report.append("- Reduzir duplicação de código e complexidade")
        if self.metrics.get('testing_violations', 0) > 0:
            report.append("- Aumentar cobertura de testes")
        if self.metrics.get('dev_history_violations', 0) > 0:
            report.append("- Atualizar dev_history.md com mudanças recentes")
        
        return "\n".join(report)
    
    def run_all_validations(self) -> Dict[str, any]:
        """Executa todas as validações."""
        print("🔍 Validando Clean Architecture...")
        ca_result = self.validate_clean_architecture()
        
        print("🔍 Validando princípios SOLID...")
        solid_result = self.validate_solid_principles()
        
        print("🔍 Validando DRY/KISS/YAGNI...")
        dry_kiss_result = self.validate_dry_kiss()
        
        print("🔍 Validando política de testes...")
        testing_result = self.validate_testing_policy()
        
        print("🔍 Validando histórico de desenvolvimento...")
        history_result = self.validate_dev_history()
        
        total_violations = sum([
            ca_result['violations'],
            solid_result['violations'],
            dry_kiss_result['violations'],
            testing_result['violations'],
            history_result['violations']
        ])
        
        return {
            'clean_architecture': ca_result,
            'solid': solid_result,
            'dry_kiss': dry_kiss_result,
            'testing': testing_result,
            'dev_history': history_result,
            'total_violations': total_violations,
            'violations': self.violations,
            'metrics': self.metrics
        }

def main():
    """Função principal."""
    validator = RulesValidator()
    
    print("🚀 Iniciando validação das regras do projeto...")
    print("")
    
    results = validator.run_all_validations()
    
    print("")
    print("📊 Relatório de Validação:")
    print("=" * 50)
    print(validator.generate_report())
    
    # Salvar relatório
    with open("validation_report.md", "w", encoding="utf-8") as f:
        f.write(validator.generate_report())
    
    print("")
    print(f"📄 Relatório salvo em: validation_report.md")
    
    if results['total_violations'] > 0:
        print(f"❌ Total de violações: {results['total_violations']}")
        sys.exit(1)
    else:
        print("✅ Todas as validações passaram!")
        sys.exit(0)

if __name__ == "__main__":
    main()
