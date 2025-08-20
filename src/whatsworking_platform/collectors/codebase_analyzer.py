#!/usr/bin/env python3
"""
Analyzers Module - Consolidated analysis functionality

This module consolidates all the analysis functionality from the scattered
whatsworking files into a unified system.
"""

import os
import ast
import pendulum
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from collections import defaultdict, Counter

@dataclass
class FileAnalysis:
    """Data structure for file analysis results"""
    file: str
    relative_path: str
    imports: Set[str]
    local_imports: Set[str]
    external_imports: Set[str]
    functions: List[str]
    classes: List[str]
    decorators: List[str]
    lines_of_code: int
    role: str
    is_init: bool
    has_main: bool
    has_tests: bool
    complexity_score: int

class CodebaseAnalyzer:
    """Main analyzer class that parses Python files and extracts metadata"""
    
    def __init__(self, root_dir: str = '.'):
        self.root_dir = Path(root_dir).resolve()
        self.analyses: List[FileAnalysis] = []
        self.project_modules: Set[str] = set()
        
        # Backend/Frontend/Utility classification patterns
        self.role_patterns = {
            'Backend': {
                'imports': {'fastapi', 'flask', 'django', 'pandas', 'sqlalchemy', 
                           'uvicorn', 'pydantic', 'gspread', 'oauth2client'},
                'functions': {'authenticate', 'get_data', 'load_', 'save_', 'client'},
                'classes': {'Client', 'Service', 'API', 'Database'}
            },
            'Frontend': {
                'imports': {'PyQt5', 'tkinter', 'streamlit', 'jinja2', 'flask'},
                'functions': {'init_ui', 'show_', 'handle_', 'on_', 'create_'},
                'classes': {'Widget', 'Component', 'Dialog', 'Window', 'UI'}
            },
            'CLI': {
                'imports': {'click', 'argparse', 'rich', 'typer'},
                'functions': {'main', 'cli', 'command'},
                'decorators': {'command', 'click'}
            },
            'Data': {
                'imports': {'pandas', 'numpy', 'rapidfuzz', 'openpyxl'},
                'functions': {'transform', 'standardize', 'map', 'convert'},
                'classes': {'Standardizer', 'Converter', 'Mapper'}
            },
            'Utility': {
                'imports': {'os', 're', 'json', 'logging', 'datetime', 'pathlib'},
                'functions': {'helper', 'util', 'format', 'parse'},
                'classes': []
            }
        }
        
        # Exclude directories
        self.exclude_dirs = {
            '__pycache__', 'build', 'dist', '.git', '.venv', 'venv', 
            '.mypy_cache', 'node_modules', '.pytest_cache', '.tox'
        }

    def get_all_py_files(self) -> List[Path]:
        """Recursively find all Python files, excluding unwanted directories"""
        py_files = []
        
        for dirpath, dirnames, filenames in os.walk(self.root_dir):
            # Filter out excluded directories
            dirnames[:] = [d for d in dirnames if d not in self.exclude_dirs]
            
            for filename in filenames:
                if filename.endswith('.py'):
                    full_path = Path(dirpath) / filename
                    py_files.append(full_path)
        
        # Also collect project module names for local import detection
        for file in py_files:
            if file.stem != '__init__':
                self.project_modules.add(file.stem)
        
        return sorted(py_files)

    def analyze_file(self, filepath: Path) -> Optional[FileAnalysis]:
        """Analyze a single Python file using AST"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            tree = ast.parse(content, filename=str(filepath))
        except (SyntaxError, UnicodeDecodeError) as e:
            print(f"Warning: Could not parse {filepath}: {e}")
            return None

        # Initialize analysis data
        imports = set()
        local_imports = set()
        external_imports = set()
        functions = []
        classes = []
        decorators = []
        has_main = False
        has_tests = False
        complexity_score = 0

        # Walk the AST
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name.split('.')[0]
                    imports.add(module_name)
                    
                    if module_name in self.project_modules or module_name in {'backend', 'frontend', 'utils'}:
                        local_imports.add(module_name)
                    else:
                        external_imports.add(module_name)
                        
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_name = node.module.split('.')[0]
                    imports.add(module_name)
                    
                    if module_name in self.project_modules or module_name in {'backend', 'frontend', 'utils'}:
                        local_imports.add(module_name)
                    else:
                        external_imports.add(module_name)
                        
            elif isinstance(node, ast.FunctionDef):
                functions.append(node.name)
                complexity_score += len(node.body)
                
                if node.name == 'main':
                    has_main = True
                if 'test' in node.name.lower():
                    has_tests = True
                    
                # Extract decorators
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name):
                        decorators.append(decorator.id)
                    elif isinstance(decorator, ast.Attribute):
                        decorators.append(decorator.attr)
                        
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
                complexity_score += len(node.body)

        # Calculate lines of code (excluding empty lines and comments)
        lines_of_code = len([line for line in content.split('\n') 
                           if line.strip() and not line.strip().startswith('#')])

        # Classify role
        role = self._classify_role(imports, functions, classes, decorators, filepath)
        
        relative_path = str(filepath.relative_to(self.root_dir))
        
        return FileAnalysis(
            file=str(filepath),
            relative_path=relative_path,
            imports=imports,
            local_imports=local_imports,
            external_imports=external_imports,
            functions=functions,
            classes=classes,
            decorators=decorators,
            lines_of_code=lines_of_code,
            role=role,
            is_init=filepath.name == '__init__.py',
            has_main=has_main,
            has_tests=has_tests,
            complexity_score=complexity_score
        )

    def _classify_role(self, imports: Set[str], functions: List[str], 
                      classes: List[str], decorators: List[str], filepath: Path) -> str:
        """Classify the role of a file based on its contents and location"""
        
        # Path-based classification first
        path_parts = filepath.parts
        if 'backend' in path_parts:
            return 'Backend'
        elif 'frontend' in path_parts:
            return 'Frontend'
        elif 'test' in str(filepath).lower():
            return 'Test'
        elif filepath.name in {'cli.py', 'main.py'}:
            return 'CLI'
        
        # Content-based classification
        scores = defaultdict(int)
        
        for role, patterns in self.role_patterns.items():
            # Score based on imports
            for imp in imports:
                if imp in patterns['imports']:
                    scores[role] += 3
                    
            # Score based on function names
            for func in functions:
                for pattern in patterns['functions']:
                    if pattern in func.lower():
                        scores[role] += 2
                        
            # Score based on class names
            for cls in classes:
                for pattern in patterns.get('classes', []):
                    if pattern in cls:
                        scores[role] += 2
                        
            # Score based on decorators
            for dec in decorators:
                if dec in patterns.get('decorators', []):
                    scores[role] += 2
        
        # Return highest scoring role, or 'Utility' as default
        return max(scores, key=scores.get) if scores else 'Utility'

    def analyze_codebase(self) -> None:
        """Analyze the entire codebase"""
        print(f"🧠 Analyzing codebase at {self.root_dir}")
        
        py_files = self.get_all_py_files()
        print(f"Found {len(py_files)} Python files")
        
        for filepath in py_files:
            analysis = self.analyze_file(filepath)
            if analysis:
                self.analyses.append(analysis)
        
        print(f"✅ Successfully analyzed {len(self.analyses)} files")

    def generate_summary_stats(self) -> Dict[str, Any]:
        """Generate summary statistics"""
        roles = Counter(analysis.role for analysis in self.analyses)
        total_loc = sum(analysis.lines_of_code for analysis in self.analyses)
        total_functions = sum(len(analysis.functions) for analysis in self.analyses)
        total_classes = sum(len(analysis.classes) for analysis in self.analyses)
        
        # Most complex files
        complex_files = sorted(self.analyses, key=lambda x: x.complexity_score, reverse=True)[:5]
        
        # Most connected files (most imports)
        connected_files = sorted(self.analyses, key=lambda x: len(x.imports), reverse=True)[:5]
        
        return {
            'total_files': len(self.analyses),
            'total_loc': total_loc,
            'total_functions': total_functions,
            'total_classes': total_classes,
            'roles': dict(roles),
            'avg_loc_per_file': total_loc / len(self.analyses) if self.analyses else 0,
            'most_complex': [(f.relative_path, f.complexity_score) for f in complex_files],
            'most_connected': [(f.relative_path, len(f.imports)) for f in connected_files]
        }

class InfrastructureAnalyzer:
    """Analyze infrastructure and deployment readiness"""
    
    def __init__(self, project_path: str = './'):
        self.project_path = Path(project_path).resolve()
    
    def analyze(self, project_path: Path) -> Dict[str, Any]:
        """Analyze infrastructure setup"""
        # This would analyze deployment files, requirements, etc.
        return {
            "deployment_ready": False,
            "missing_files": [],
            "recommendations": []
        }

class TestResultsAggregator:
    """Aggregate and analyze test results"""
    
    def __init__(self, project_path: str = './'):
        self.project_path = Path(project_path).resolve()
    
    def analyze(self, project_path: Path) -> Dict[str, Any]:
        """Analyze test results and coverage"""
        # This would analyze test results, coverage reports, etc.
        return {
            "test_coverage": 0.0,
            "total_tests": 0,
            "passing_tests": 0,
            "failing_tests": 0
        }

class FeatureUsageTracker:
    """Track feature usage and adoption"""
    
    def __init__(self, project_path: str = './'):
        self.project_path = Path(project_path).resolve()
    
    def analyze(self, project_path: Path) -> Dict[str, Any]:
        """Analyze feature usage patterns"""
        # This would analyze feature usage, adoption metrics, etc.
        return {
            "features_used": [],
            "adoption_rate": 0.0,
            "popular_features": []
        }
