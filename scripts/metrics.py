#!/usr/bin/env python3
"""
Script para calcular métricas de conformidade das regras do projeto.
"""
import os
import sys
import ast
import re
from pathlib import Path
from typing import Dict, List, Tuple
import subprocess
import json
from datetime import datetime

class ConformityMetrics:
    """Calculadora de métricas de conformidade."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.metrics = {}
    
    def calculate_clean_architecture_score(self) -> float:
        """Calcula score de conformidade com Clean Architecture."""
        domain_files = list(self.project_root.glob("src/domain/**/*.py"))
        total_files = len(domain_files)
        violations = 0
        
        for file_path in domain_files:
            if file_path.name == "__init__.py":
                continue
                
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verificar imports de outras camadas
            if re.search(r'from src\.(application|infrastructure|presentation)', content):
                violations += 1
            if re.search(r'import src\.(application|infrastructure|presentation)', content):
                violations += 1
        
        if total_files == 0:
            return 100.0
        
        score = max(0, 100 - (violations / total_files) * 100)
        self.metrics['clean_architecture_score'] = score
        return score
    
    def calculate_solid_score(self) -> float:
        """Calcula score de conformidade com princípios SOLID."""
        total_classes = 0
        violations = 0
        
        for file_path in self.project_root.glob("src/**/*.py"):
            if file_path.name == "__init__.py":
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        total_classes += 1
                        methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                        
                        # SRP: Classes com muitos métodos
                        if len(methods) > 10:
                            violations += 1
                        
                        # ISP: Classes com muitos métodos públicos
                        public_methods = [m for m in methods if not m.name.startswith('_')]
                        if len(public_methods) > 5:
                            violations += 1
                
            except Exception:
                continue
        
        if total_classes == 0:
            return 100.0
        
        score = max(0, 100 - (violations / total_classes) * 100)
        self.metrics['solid_score'] = score
        return score
    
    def calculate_dry_kiss_score(self) -> float:
        """Calcula score de conformidade com DRY/KISS/YAGNI."""
        score = 100.0
        
        # Verificar complexidade ciclomática
        try:
            result = subprocess.run(['radon', 'cc', 'src/', '--min', 'B'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                complex_functions = len([line for line in result.stdout.split('\n') if 'B' in line or 'C' in line or 'D' in line])
                if complex_functions > 0:
                    score -= min(50, complex_functions * 5)  # Penalizar funções complexas
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Verificar duplicação (simulação)
        duplicate_penalty = 0
        for file_path in self.project_root.glob("src/**/*.py"):
            if file_path.name == "__init__.py":
                continue
                
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Detectar padrões de duplicação simples
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if len(line.strip()) > 20:  # Linhas significativas
                    for j, other_line in enumerate(lines[i+1:], i+1):
                        if line.strip() == other_line.strip() and len(line.strip()) > 10:
                            duplicate_penalty += 1
                            break
        
        score -= min(30, duplicate_penalty * 2)
        
        self.metrics['dry_kiss_score'] = max(0, score)
        return max(0, score)
    
    def calculate_testing_score(self) -> float:
        """Calcula score de conformidade com política de testes."""
        try:
            result = subprocess.run(['python', '-m', 'pytest', 'tests/unit/', '--cov=src', '--cov-report=term-missing'], 
                                  capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                coverage_match = re.search(r'TOTAL\s+(\d+)\s+(\d+)\s+(\d+)%', result.stdout)
                if coverage_match:
                    coverage_percent = int(coverage_match.group(3))
                    self.metrics['test_coverage'] = coverage_percent
                    return coverage_percent
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return 0.0
    
    def calculate_dev_history_score(self) -> float:
        """Calcula score de conformidade com histórico de desenvolvimento."""
        history_file = self.project_root / "dev_history.md"
        if not history_file.exists():
            return 0.0
        
        with open(history_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar se há entradas recentes (últimos 30 dias)
        entries = re.findall(r'\[(\d{4}-\d{2}-\d{2})\]', content)
        if not entries:
            return 0.0
        
        # Verificar formato das entradas
        valid_entries = 0
        for entry in entries:
            try:
                entry_date = datetime.strptime(entry, '%Y-%m-%d')
                if (datetime.now() - entry_date).days <= 30:
                    valid_entries += 1
            except ValueError:
                continue
        
        score = min(100, (valid_entries / max(1, len(entries))) * 100)
        self.metrics['dev_history_score'] = score
        return score
    
    def calculate_overall_score(self) -> float:
        """Calcula score geral de conformidade."""
        scores = [
            self.calculate_clean_architecture_score(),
            self.calculate_solid_score(),
            self.calculate_dry_kiss_score(),
            self.calculate_testing_score(),
            self.calculate_dev_history_score()
        ]
        
        overall_score = sum(scores) / len(scores)
        self.metrics['overall_score'] = overall_score
        return overall_score
    
    def generate_dashboard(self) -> str:
        """Gera dashboard de métricas."""
        dashboard = []
        dashboard.append("# 📊 Dashboard de Conformidade das Regras")
        dashboard.append("=" * 60)
        dashboard.append("")
        
        # Scores individuais
        dashboard.append("## 🎯 Scores de Conformidade")
        dashboard.append("")
        
        ca_score = self.calculate_clean_architecture_score()
        solid_score = self.calculate_solid_score()
        dry_kiss_score = self.calculate_dry_kiss_score()
        testing_score = self.calculate_testing_score()
        history_score = self.calculate_dev_history_score()
        overall_score = self.calculate_overall_score()
        
        dashboard.append(f"| Regra | Score | Status |")
        dashboard.append(f"|-------|-------|--------|")
        dashboard.append(f"| 🏗️ Clean Architecture | {ca_score:.1f}% | {'✅' if ca_score >= 80 else '⚠️' if ca_score >= 60 else '❌'} |")
        dashboard.append(f"| 🔧 SOLID | {solid_score:.1f}% | {'✅' if solid_score >= 80 else '⚠️' if solid_score >= 60 else '❌'} |")
        dashboard.append(f"| 🎯 DRY/KISS/YAGNI | {dry_kiss_score:.1f}% | {'✅' if dry_kiss_score >= 80 else '⚠️' if dry_kiss_score >= 60 else '❌'} |")
        dashboard.append(f"| 🧪 Testes | {testing_score:.1f}% | {'✅' if testing_score >= 80 else '⚠️' if testing_score >= 60 else '❌'} |")
        dashboard.append(f"| 📝 Histórico | {history_score:.1f}% | {'✅' if history_score >= 80 else '⚠️' if history_score >= 60 else '❌'} |")
        dashboard.append(f"| **📈 GERAL** | **{overall_score:.1f}%** | **{'✅' if overall_score >= 80 else '⚠️' if overall_score >= 60 else '❌'}** |")
        dashboard.append("")
        
        # Métricas detalhadas
        dashboard.append("## 📈 Métricas Detalhadas")
        dashboard.append("")
        
        if 'test_coverage' in self.metrics:
            dashboard.append(f"- **Cobertura de Testes**: {self.metrics['test_coverage']}%")
        
        dashboard.append(f"- **Score Clean Architecture**: {ca_score:.1f}%")
        dashboard.append(f"- **Score SOLID**: {solid_score:.1f}%")
        dashboard.append(f"- **Score DRY/KISS/YAGNI**: {dry_kiss_score:.1f}%")
        dashboard.append(f"- **Score Histórico**: {history_score:.1f}%")
        dashboard.append("")
        
        # Recomendações
        dashboard.append("## 💡 Recomendações")
        dashboard.append("")
        
        if ca_score < 80:
            dashboard.append("- 🔧 Melhorar separação de camadas na Clean Architecture")
        if solid_score < 80:
            dashboard.append("- 🔧 Aplicar princípios SOLID nas classes")
        if dry_kiss_score < 80:
            dashboard.append("- 🔧 Reduzir duplicação e complexidade do código")
        if testing_score < 80:
            dashboard.append("- 🧪 Aumentar cobertura de testes")
        if history_score < 80:
            dashboard.append("- 📝 Atualizar histórico de desenvolvimento")
        
        if overall_score >= 80:
            dashboard.append("- 🎉 **Excelente conformidade!** Continue mantendo a qualidade.")
        elif overall_score >= 60:
            dashboard.append("- ⚠️ **Boa conformidade**, mas há espaço para melhorias.")
        else:
            dashboard.append("- ❌ **Conformidade baixa**, priorize as melhorias sugeridas.")
        
        dashboard.append("")
        dashboard.append(f"*Relatório gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        
        return "\n".join(dashboard)
    
    def save_metrics_json(self, filename: str = "metrics.json"):
        """Salva métricas em formato JSON."""
        metrics_data = {
            'timestamp': datetime.now().isoformat(),
            'clean_architecture_score': self.calculate_clean_architecture_score(),
            'solid_score': self.calculate_solid_score(),
            'dry_kiss_score': self.calculate_dry_kiss_score(),
            'testing_score': self.calculate_testing_score(),
            'dev_history_score': self.calculate_dev_history_score(),
            'overall_score': self.calculate_overall_score(),
            'metrics': self.metrics
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(metrics_data, f, indent=2, ensure_ascii=False)

def main():
    """Função principal."""
    metrics = ConformityMetrics()
    
    print("📊 Calculando métricas de conformidade...")
    print("")
    
    # Calcular scores
    overall_score = metrics.calculate_overall_score()
    
    # Gerar dashboard
    dashboard = metrics.generate_dashboard()
    print(dashboard)
    
    # Salvar métricas
    metrics.save_metrics_json()
    
    print("")
    print(f"📄 Métricas salvas em: metrics.json")
    print(f"📊 Score geral: {overall_score:.1f}%")
    
    if overall_score >= 80:
        print("🎉 Excelente conformidade!")
        sys.exit(0)
    elif overall_score >= 60:
        print("⚠️ Boa conformidade, mas há espaço para melhorias.")
        sys.exit(0)
    else:
        print("❌ Conformidade baixa, priorize as melhorias.")
        sys.exit(1)

if __name__ == "__main__":
    main()
