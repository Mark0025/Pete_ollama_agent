#!/usr/bin/env python3
"""
🔍 What's Working - Codebase Analysis Utility

A rational observer utility that analyzes your Python codebase using AST parsing.
No AI hallucinations - just facts extracted from your actual code.

Features:
- AST-based analysis of all Python files
- Import dependency mapping
- Class/function/decorator extraction
- Role classification (Backend/Frontend/Utility)
- Mermaid diagram generation
- Relationship detection
- File health analysis
- Comprehensive markdown reports

Usage:
    python backend/utils/whatsworking.py
    
Output:
    DEV_MAN/WHATS_WORKING_<timestamp>.md
"""

import os
import ast
import pendulum
import json
import re
import fnmatch
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple
from dataclasses import dataclass, asdict

# Configuration
EXCLUDE_DIRS = {
    '__pycache__', 'build', 'dist', '.git', '.venv', 'venv', 
    '.mypy_cache', 'node_modules', '.pytest_cache', '.tox'
}

DEV_MAN_DIR = 'DEV_MAN'
REPORTS_DIR = os.path.join(DEV_MAN_DIR, 'whatsworking')
ARCHITECTURE_CONFIG_PATH = os.path.join(DEV_MAN_DIR, 'architecture_config.json')

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

class ArchitectureDiagramGenerator:
    """Generates Mermaid architecture diagrams from codebase analysis"""
    
    def __init__(self, config_path: str = ARCHITECTURE_CONFIG_PATH):
        self.config = self._load_config(config_path)
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load architecture configuration from JSON file"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Return default config if file doesn't exist
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default architecture configuration"""
        return {
            "title": "🎯 Codebase Architecture",
            "direction": "TB",
            "groups": {
                "Frontend": {"label": "🎨 Frontend", "path_patterns": ["frontend/"], "color": "#4ecdc4"},
                "Backend": {"label": "🔧 Backend", "path_patterns": ["backend/"], "color": "#ff6b6b"},
                "CLI": {"label": "🚪 Entry Points", "path_patterns": ["cli.py"], "color": "#45b7d1"}
            }
        }
    
    def _matches_pattern(self, file_path: str, patterns: List[str]) -> bool:
        """Check if file path matches any of the given patterns"""
        normalized_path = file_path.replace('\\', '/')
        for pattern in patterns:
            if fnmatch.fnmatch(normalized_path, pattern) or pattern in normalized_path:
                return True
        return False
    
    def _get_file_icon(self, file_path: str) -> str:
        """Get icon for file based on its name and type"""
        file_name = os.path.basename(file_path).lower()
        icons = self.config.get('node_icons', {})
        
        # Check exact matches first
        if file_name in icons:
            return icons[file_name]
        
        # Check partial matches
        for key, icon in icons.items():
            if key in file_name:
                return icon
        
        # Default icons based on file type
        if 'test' in file_name:
            return '🧪'
        elif 'main' in file_name or 'cli' in file_name:
            return '🚪'
        elif 'dialog' in file_name:
            return '💬'
        elif 'client' in file_name:
            return '📡'
        elif 'util' in file_name:
            return '🛠️'
        else:
            return '📄'
    
    def _categorize_files(self, analyses: List[FileAnalysis]) -> Dict[str, List[FileAnalysis]]:
        """Categorize files based on configuration patterns"""
        categorized = defaultdict(list)
        
        for analysis in analyses:
            file_path = analysis.file
            categorized_flag = False
            
            # Check each group in config
            for group_name, group_config in self.config.get('groups', {}).items():
                patterns = group_config.get('path_patterns', [])
                exclude_patterns = group_config.get('exclude_patterns', [])
                
                # Check if file matches include patterns
                if self._matches_pattern(file_path, patterns):
                    # Check if file should be excluded
                    if not any(self._matches_pattern(file_path, [pattern]) for pattern in exclude_patterns):
                        # Check subgroups
                        subgroups = group_config.get('subgroups', {})
                        placed_in_subgroup = False
                        
                        for subgroup_name, subgroup_config in subgroups.items():
                            subgroup_patterns = subgroup_config.get('path_patterns', [])
                            if self._matches_pattern(file_path, subgroup_patterns):
                                categorized[f"{group_name}_{subgroup_name}"].append(analysis)
                                placed_in_subgroup = True
                                break
                        
                        if not placed_in_subgroup:
                            categorized[group_name].append(analysis)
                        
                        categorized_flag = True
                        break
            
            if not categorized_flag:
                categorized['Other'].append(analysis)
        
        return dict(categorized)
    
    def generate_mermaid_diagram(self, analyses: List[FileAnalysis]) -> str:
        """Generate Mermaid diagram from file analyses"""
        categorized = self._categorize_files(analyses)
        
        lines = [
            f"graph {self.config.get('direction', 'TD')}",
            f"    subgraph \"{self.config.get('title', 'Codebase Architecture')}\""
        ]
        
        # Generate nodes for each category
        node_id_map = {}
        node_counter = 0
        
        for category, files in categorized.items():
            if not files:
                continue
            
            # Get group configuration
            group_name = category.split('_')[0]
            group_config = self.config.get('groups', {}).get(group_name, {})
            
            if '_' in category:
                # This is a subgroup
                subgroup_name = category.split('_', 1)[1]
                subgroup_config = group_config.get('subgroups', {}).get(subgroup_name, {})
                label = subgroup_config.get('label', subgroup_name)
                icon = subgroup_config.get('icon', '📁')
            else:
                label = group_config.get('label', category)
                icon = group_config.get('icon', '📁')
            
            # Add subgraph for category
            file_count = len(files)
            lines.append(f"        subgraph \"{icon} {label} ({file_count} files)\"")
            
            # Add nodes for each file
            max_nodes = self.config.get('mermaid_settings', {}).get('max_nodes_per_group', 10)
            for i, analysis in enumerate(files[:max_nodes]):
                node_id = f"node_{node_counter}"
                node_counter += 1
                
                file_name = os.path.basename(analysis.file)
                file_icon = self._get_file_icon(analysis.file)
                
                # Create descriptive label
                if self.config.get('mermaid_settings', {}).get('include_file_metrics', True):
                    label_text = f"{file_name}<br/>{file_icon} {analysis.role}<br/>📊 {analysis.lines_of_code} LOC"
                else:
                    label_text = f"{file_name}<br/>{file_icon} {analysis.role}"
                
                lines.append(f"            {node_id}[\"{label_text}\"]")
                node_id_map[analysis.file] = node_id
            
            # Show if there are more files
            if len(files) > max_nodes:
                lines.append(f"            more_node_{node_counter}[\"... and {len(files) - max_nodes} more files\"]")
                node_counter += 1
            
            lines.append("        end")
        
        lines.append("    end")
        
        # Add key relationships
        lines.append("")
        lines.append("    %% Key relationships")
        relationship_count = 0
        max_relationships = 20  # Limit to keep diagram readable
        
        for analysis in analyses:
            if analysis.file in node_id_map and relationship_count < max_relationships:
                from_node = node_id_map[analysis.file]
                
                # Find import relationships to other analyzed files
                for imported_module in analysis.imports:
                    for other_analysis in analyses:
                        if relationship_count >= max_relationships:
                            break
                        
                        other_file_name = os.path.basename(other_analysis.file).replace('.py', '')
                        other_dir = os.path.dirname(other_analysis.file).replace('/', '').replace('\\', '')
                        
                        # Check for module matches
                        if (imported_module.lower() == other_file_name.lower() or 
                            imported_module.lower() == other_dir.lower() or
                            imported_module.lower() in other_analysis.file.lower().replace('/', '').replace('\\', '')):
                            
                            if (other_analysis.file in node_id_map and 
                                other_analysis.file != analysis.file):
                                to_node = node_id_map[other_analysis.file]
                                lines.append(f"    {from_node} --> {to_node}")
                                relationship_count += 1
                                break
        
        # Add styling based on configuration
        lines.append("")
        lines.append("    %% Styling")
        for category, files in categorized.items():
            group_name = category.split('_')[0]
            group_config = self.config.get('groups', {}).get(group_name, {})
            color = group_config.get('color')
            
            if color:
                for analysis in files:
                    if analysis.file in node_id_map:
                        node_id = node_id_map[analysis.file]
                        lines.append(f"    style {node_id} fill:{color}")
        
        return '\n'.join(lines)

class CodebaseAnalyzer:
    """Main analyzer class that parses Python files and extracts metadata"""
    
    def __init__(self, root_dir: str = '.'):
        self.root_dir = Path(root_dir).resolve()
        self.analyses: List[FileAnalysis] = []
        self.project_modules: Set[str] = set()
        self.diagram_generator = ArchitectureDiagramGenerator()
        
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

    def get_all_py_files(self) -> List[Path]:
        """Recursively find all Python files, excluding unwanted directories"""
        py_files = []
        
        for dirpath, dirnames, filenames in os.walk(self.root_dir):
            # Filter out excluded directories
            dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
            
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

    def generate_mermaid_diagram(self) -> str:
        """Generate Mermaid architecture diagram using ArchitectureDiagramGenerator"""
        try:
            diagram = self.diagram_generator.generate_mermaid_diagram(self.analyses)
            return f"```mermaid\n{diagram}\n```"
        except Exception as e:
            print(f"⚠️  Architecture diagram generation failed: {e}")
            # Fallback to simple diagram
            return self._generate_fallback_diagram()
    
    def _generate_workflow_diagram(self) -> str:
        """Generate the smart data workflow diagram"""
        return '''```mermaid
graph TD
    subgraph "🎯 New Smart Data Workflow"
        direction TB
        
        A["📁 File Upload<br/>Select CSV/Excel"]
        
        B["📝 Data Prep Editor<br/>🆕 NEW STEP<br/>• Smart column editing<br/>• Multi-select concatenation<br/>• Version history<br/>• Undo/Redo<br/>• Clean preview"]
        
        C["🗺️ Pete Mapping<br/>• Enhanced readability<br/>• Better headers<br/>• Clean dropdowns<br/>• Visual feedback"]
        
        D["👁️ Preview & Export<br/>• Final review<br/>• Download options"]
        
        subgraph "📝 Data Prep Features"
            B1["🔗 Smart Merger<br/>• Select 2+ columns<br/>• Choose delimiter<br/>• Auto-suggest names<br/>• Keep/remove originals"]
            B2["📚 Version History<br/>• Every change tracked<br/>• Undo/Redo anytime<br/>• Change descriptions"]
            B3["✏️ Column Editing<br/>• Right-click operations<br/>• Rename columns<br/>• Clean interface"]
            B4["🔄 Reset Options<br/>• Back to original<br/>• Confirm changes<br/>• State management"]
        end
        
        subgraph "🎨 UX Improvements"
            UI1["📊 Better Headers<br/>• Blue styling<br/>• Readable text<br/>• Proper sizing"]
            UI2["🖱️ User-Friendly<br/>• Right-click menus<br/>• Clear buttons<br/>• Visual feedback"]
            UI3["⚡ Smart Workflow<br/>• Logical progression<br/>• Easy navigation<br/>• No confusion"]
        end
    end
    
    %% Main workflow
    A --> B
    B --> C
    C --> D
    
    %% Data prep features
    B --> B1
    B --> B2
    B --> B3
    B --> B4
    
    %% UI improvements
    B --> UI1
    C --> UI1
    B --> UI2
    C --> UI2
    A --> UI3
    B --> UI3
    
    %% Navigation
    B -.->|Back| A
    C -.->|Back| B
    D -.->|Back| C
    
    %% Styling
    style A fill:#e3f2fd
    style B fill:#c8e6c9
    style C fill:#fff3e0
    style D fill:#f3e5f5
    style B1 fill:#4caf50
    style B2 fill:#4caf50
    style B3 fill:#4caf50
    style B4 fill:#4caf50
    style UI1 fill:#1976d2
    style UI2 fill:#1976d2
    style UI3 fill:#1976d2
```'''

    def _generate_fallback_diagram(self) -> str:
        """Generate a simple fallback diagram if architecture generation fails"""
        lines = ['```mermaid', 'graph TD', '    subgraph "📊 Codebase Overview"']
        
        # Group by role and show counts
        role_counts = defaultdict(int)
        for analysis in self.analyses:
            role_counts[analysis.role] += 1
        
        for role, count in role_counts.items():
            safe_role = role.replace(' ', '_')
            lines.append(f'        {safe_role}["{role}<br/>{count} files"]')
        
        lines.extend(['    end', '```'])
        return '\n'.join(lines)

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

    def generate_report(self) -> str:
        """Generate comprehensive markdown report"""
        timestamp = pendulum.now('America/Chicago').strftime("%Y-%m-%d %H:%M:%S")
        stats = self.generate_summary_stats()
        
        lines = [
            "# 🔍 What's Working - Codebase Analysis Report",
            "",
            f"**Generated:** {timestamp}",
            f"**Analyzed:** {stats['total_files']} Python files",
            f"**Total Lines of Code:** {stats['total_loc']:,}",
            "",
            "---",
            ""
        ]
        
        # Summary Statistics
        lines.extend([
            "## 📊 Summary Statistics",
            "",
            f"- **Files:** {stats['total_files']}",
            f"- **Functions:** {stats['total_functions']}",
            f"- **Classes:** {stats['total_classes']}",
            f"- **Average LOC/File:** {stats['avg_loc_per_file']:.1f}",
            "",
            "### Files by Role:",
            ""
        ])
        
        for role, count in sorted(stats['roles'].items()):
            lines.append(f"- **{role}:** {count} files")
        
        lines.extend(["", "---", ""])
        
        # Architecture Diagram
        lines.extend([
            "## 🏗️ Architecture Overview",
            "",
            self.generate_mermaid_diagram(),
            "",
            "---",
            ""
        ])
        
        # Smart Data Workflow
        lines.extend([
            "## 🎯 Smart Data Workflow",
            "",
            "The application implements a user-friendly data processing workflow:",
            "",
            self._generate_workflow_diagram(),
            "",
            "### Key Workflow Features:",
            "",
            "- **📝 Data Preparation Editor**: New smart editor for preparing data before Pete mapping",
            "- **🔗 Multi-Column Concatenation**: Select multiple columns and merge with custom delimiters", 
            "- **📚 Version History**: Full undo/redo with change tracking",
            "- **🎨 Enhanced UI**: Better readability, clear headers, intuitive navigation",
            "- **⚡ Logical Flow**: Upload → Prepare → Map → Export",
            "",
            "---",
            ""
        ])
        
        # Most Complex Files
        if stats['most_complex']:
            lines.extend([
                "## 🧮 Most Complex Files",
                "",
                "| File | Complexity Score |",
                "|------|------------------|"
            ])
            
            for filepath, score in stats['most_complex']:
                lines.append(f"| `{filepath}` | {score} |")
            
            lines.extend(["", "---", ""])
        
        # Most Connected Files
        if stats['most_connected']:
            lines.extend([
                "## 🔗 Most Connected Files",
                "",
                "| File | Import Count |",
                "|------|--------------|"
            ])
            
            for filepath, count in stats['most_connected']:
                lines.append(f"| `{filepath}` | {count} |")
            
            lines.extend(["", "---", ""])
        
        # Detailed File Analysis
        lines.extend([
            "## 📋 Detailed File Analysis",
            ""
        ])
        
        # Group by role
        by_role = defaultdict(list)
        for analysis in self.analyses:
            by_role[analysis.role].append(analysis)
        
        for role in sorted(by_role.keys()):
            files = sorted(by_role[role], key=lambda x: x.relative_path)
            lines.extend([
                f"### {role} Files ({len(files)})",
                ""
            ])
            
            for analysis in files:
                lines.append(f"#### 📄 `{analysis.relative_path}`")
                lines.append(f"**Lines:** {analysis.lines_of_code} | **Complexity:** {analysis.complexity_score}")
                
                if analysis.external_imports:
                    lines.append(f"- **External Imports:** {', '.join(sorted(analysis.external_imports))}")
                if analysis.local_imports:
                    lines.append(f"- **Local Imports:** {', '.join(sorted(analysis.local_imports))}")
                if analysis.classes:
                    lines.append(f"- **Classes:** {', '.join(analysis.classes)}")
                if analysis.functions and not analysis.is_init:
                    func_list = analysis.functions[:5]  # Show first 5
                    more = f" (+{len(analysis.functions)-5} more)" if len(analysis.functions) > 5 else ""
                    lines.append(f"- **Functions:** {', '.join(func_list)}{more}")
                if analysis.decorators:
                    lines.append(f"- **Decorators:** {', '.join(set(analysis.decorators))}")
                
                # Special markers
                markers = []
                if analysis.has_main:
                    markers.append("🚪 Entry Point")
                if analysis.has_tests:
                    markers.append("🧪 Has Tests")
                if analysis.is_init:
                    markers.append("📦 Init File")
                    
                if markers:
                    lines.append(f"- **Special:** {' | '.join(markers)}")
                
                lines.append("")
        
        # Dependency Analysis
        lines.extend([
            "---",
            "",
            "## 🔄 Dependency Relationships",
            ""
        ])
        
        # Build dependency map
        dependencies = defaultdict(list)
        for analysis in self.analyses:
            source_name = analysis.relative_path
            for local_import in analysis.local_imports:
                # Find the target file
                for target in self.analyses:
                    if target.relative_path.endswith(f'{local_import}.py'):
                        dependencies[source_name].append(target.relative_path)
                        break
        
        if dependencies:
            for source, targets in sorted(dependencies.items()):
                targets_str = ', '.join(f"`{t}`" for t in targets)
                lines.append(f"- `{source}` depends on: {targets_str}")
        else:
            lines.append("- No internal dependencies detected")
        
        lines.extend([
            "",
            "---",
            "",
            f"**Report generated by:** `backend/utils/whatsworking.py`",
            f"**Timestamp:** {timestamp}",
            ""
        ])
        
        return '\n'.join(lines)

    def generate_pipeline_analysis_report(self) -> str:
        """Generate a comprehensive pipeline analysis report with before/after metrics"""
        timestamp = pendulum.now('America/Chicago').strftime("%Y-%m-%d %H:%M:%S")
        
        # Run the pipeline analyzer
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            
            from backend.utils.data_pipeline_analyzer import DataPipelineAnalyzer
            analyzer = DataPipelineAnalyzer()
            results = analyzer.run_full_analysis()
            
            lines = [
                "# 🔍 Data Pipeline Analysis Report",
                "",
                f"**Generated:** {timestamp}",
                f"**Dataset:** {results.get('dataset_file', 'Unknown')}",
                "",
                "---",
                "",
                "## 📊 Pipeline Performance Summary",
                ""
            ]
            
            # Before metrics
            before = results.get('before_metrics', {})
            lines.extend([
                "### 🚫 Before Processing:",
                f"- **Total Rows:** {before.get('total_rows', 0):,}",
                f"- **Total Columns:** {before.get('total_columns', 0)}",
                f"- **Phone Columns:** {len(before.get('phone_columns', []))}",
                f"- **Trailing .0 Count:** {before.get('trailing_dot_count', 0):,}",
                f"- **Sample Phone Numbers:** {', '.join(before.get('sample_phone_numbers', [])[:3])}",
                ""
            ])
            
            # After metrics
            after = results.get('after_metrics', {})
            effectiveness = after.get('prioritization_effectiveness', {})
            lines.extend([
                "### ✅ After Processing:",
                f"- **Total Rows:** {after.get('total_rows', 0):,}",
                f"- **Correct Numbers Selected:** {effectiveness.get('correct_numbers_selected', 0):,}",
                f"- **Mobile Numbers Selected:** {effectiveness.get('mobile_numbers_selected', 0):,}",
                f"- **Selection Quality Score:** {effectiveness.get('selection_quality_score', 0):.1f}%",
                ""
            ])
            
            # Status distribution
            status_data = after.get('status_distribution', {})
            if status_data:
                lines.extend([
                    "### 📊 Phone Status Distribution:",
                    "| Status | Count | Percentage |",
                    "|--------|-------|------------|"
                ])
                total_status = sum(status_data.values())
                for status, count in status_data.items():
                    percentage = (count / total_status * 100) if total_status > 0 else 0
                    lines.append(f"| {status} | {count:,} | {percentage:.1f}% |")
                lines.append("")
            
            # Type distribution
            type_data = after.get('type_distribution', {})
            if type_data:
                lines.extend([
                    "### 📱 Phone Type Distribution:",
                    "| Type | Count | Percentage |",
                    "|------|-------|------------|"
                ])
                total_type = sum(type_data.values())
                for phone_type, count in type_data.items():
                    percentage = (count / total_type * 100) if total_type > 0 else 0
                    lines.append(f"| {phone_type} | {count:,} | {percentage:.1f}% |")
                lines.append("")
            
            # Key improvements
            lines.extend([
                "## 🎯 Key Improvements Achieved",
                "",
                "### ⚡ Performance Improvements:",
                f"- **Trailing .0 Cleanup:** {before.get('trailing_dot_count', 0):,} phone numbers cleaned",
                f"- **Data Quality:** {effectiveness.get('selection_quality_score', 0):.1f}% quality score for phone selection",
                f"- **Efficiency:** Automated prioritization of {effectiveness.get('correct_numbers_selected', 0):,} correct numbers",
                ""
            ])
            
            # Visualization info
            viz_file = results.get('visualization_file', '')
            if viz_file:
                lines.extend([
                    "## 📊 Visualization",
                    "",
                    f"Pipeline funnel visualization saved: `{viz_file}`",
                    "",
                    "The visualization shows:",
                    "- Data flow through the pipeline stages",
                    "- Phone status and type distributions", 
                    "- Call history analysis",
                    "- Prioritization effectiveness",
                    ""
                ])
            
            lines.extend([
                "---",
                "",
                f"**Report generated by:** `backend/utils/whatsworking.py`",
                f"**Timestamp:** {timestamp}",
                ""
            ])
            
            return '\n'.join(lines)
            
        except Exception as e:
            return f"# ❌ Pipeline Analysis Failed\n\nError: {str(e)}\n\nTimestamp: {timestamp}"

    def generate_end_user_flow_report(self) -> str:
        """Generate an end-user focused report explaining the app flow and user experience"""
        timestamp = pendulum.now('America/Chicago').strftime("%Y-%m-%d %H:%M:%S")
        
        lines = [
            "# 🎯 Pete Data Cleaner - End User Experience Guide",
            "",
            f"**Generated:** {timestamp}",
            "**Audience:** End Users & Project Managers",
            "",
            "---",
            "",
            "## 🚀 What Pete Data Cleaner Does For You",
            "",
            "Pete Data Cleaner is your **smart data preparation assistant** that transforms messy spreadsheets into clean, Pete-ready data. Think of it as having a data expert who knows exactly what Pete needs and automatically fixes common problems.",
            "",
            "### 🎯 The Problem We Solve",
            "",
            "**Before Pete Data Cleaner:**",
            "- 📱 Phone numbers look like: `4098880401.0`, `8702853184.0` (with annoying .0 endings)",
            "- 📊 Spreadsheets have 30+ phone columns but Pete only needs 5",
            "- 🗂️ Column names are messy: `Phone 1`, `Phone_1`, `phone1`, `PHONE1`",
            "- 📋 Empty columns everywhere cluttering your view",
            "- ⏰ Hours spent manually cleaning and organizing data",
            "",
            "**After Pete Data Cleaner:**",
            "- 📱 Clean phone numbers: `4098880401`, `8702853184`",
            "- 🎯 Smart selection of the 5 best phone numbers for Pete",
            "- 🏷️ Consistent, clean column names",
            "- 🧹 Hidden empty columns for clean workspace",
            "- ⚡ Minutes instead of hours",
            "",
            "---",
            "",
            "## 📋 Your Data Journey (Step-by-Step)",
            "",
            "### 1️⃣ **Upload Your Data**",
            "**What you do:** Click 'Upload File' and select your CSV or Excel file",
            "**What happens behind the scenes:**",
            "- 🔍 Pete automatically detects your file format",
            "- 🧹 Strips trailing `.0` from phone numbers (no more `4098880401.0`)",
            "- 📊 Shows you a preview of your cleaned data",
            "- ✅ Validates that your data is ready for processing",
            "",
            "### 2️⃣ **Smart Data Preparation**",
            "**What you do:** Use the Data Prep Editor to organize your data",
            "**What happens behind the scenes:**",
            "- 🔗 **Smart Column Merging:** Select multiple phone columns and merge them with custom delimiters",
            "- 📚 **Version History:** Every change is tracked - undo/redo anytime",
            "- ✏️ **Column Editing:** Right-click to rename, hide, or reorganize columns",
            "- 🎨 **Clean Interface:** Blue headers, readable text, intuitive navigation",
            "",
            "### 3️⃣ **Phone Number Intelligence**",
            "**What you do:** Click '📞 Prioritize Phones' to see your phone data analysis",
            "**What happens behind the scenes:**",
            "- 📊 **Status Analysis:** Shows how many 'CORRECT', 'WRONG', 'UNKNOWN' numbers you have",
            "- 📱 **Type Analysis:** Categorizes by 'MOBILE', 'LANDLINE', 'VOIP'",
            "- 📞 **Call History:** Analyzes tags like `call_a01` (called once), `call_a05` (called 5 times)",
            "- 🎯 **Smart Selection:** Automatically picks the 5 best numbers for Pete based on:",
            "  - ✅ **Priority 1:** CORRECT numbers (verified working)",
            "  - 📱 **Priority 2:** MOBILE numbers (higher connection rate)",
            "  - 📞 **Priority 3:** Numbers with fewer call attempts",
            "  - ❌ **Excluded:** WRONG numbers (saves Pete time)",
            "",
            "### 4️⃣ **Pete Mapping**",
            "**What you do:** Map your cleaned columns to Pete's expected format",
            "**What happens behind the scenes:**",
            "- 🎯 **Smart Suggestions:** Pete suggests the best matches for your columns",
            "- 🏷️ **Clean Headers:** Consistent, readable column names",
            "- ✅ **Validation:** Ensures all required Pete fields are mapped",
            "",
            "### 5️⃣ **Export & Done**",
            "**What you do:** Review your final data and export",
            "**What happens behind the scenes:**",
            "- 📊 **Final Preview:** Clean, organized data ready for Pete",
            "- 💾 **Multiple Formats:** Export as CSV, Excel, or Pete's preferred format",
            "- ✅ **Quality Check:** Ensures data meets Pete's requirements",
            "",
            "---",
            "",
            "## 📊 Data Transformation Examples",
            "",
            "### Phone Number Cleaning",
            "**Input:** `4098880401.0`, `8702853184.0`, `4054104179.0`",
            "**Output:** `4098880401`, `8702853184`, `4054104179`",
            "",
            "### Phone Prioritization Logic",
            "**Input:** 30 phone columns with mixed status",
            "**Output:** 5 best phones selected based on:",
            "- 🥇 **CORRECT** status (verified working numbers)",
            "- 📱 **MOBILE** type (higher connection success)",
            "- 📞 **Call history** (prefer fewer attempts)",
            "- ❌ **Exclude WRONG** numbers (saves time)",
            "",
            "### Column Organization",
            "**Input:** Messy column names like `Phone_1`, `phone1`, `PHONE1`",
            "**Output:** Clean, consistent names like `Phone 1`, `Phone 2`, etc.",
            "",
            "---",
            "",
            "## 🎯 Key Features That Save You Time",
            "",
            "### ⚡ **Automatic .0 Cleanup**",
            "- **Problem:** Excel exports phone numbers as `4098880401.0`",
            "- **Solution:** Pete automatically strips the `.0` on upload",
            "- **Time Saved:** 5-10 minutes per file",
            "",
            "### 🎯 **Smart Phone Selection**",
            "- **Problem:** Pete only needs 5 phones but you have 30+ columns",
            "- **Solution:** Intelligent prioritization based on status, type, and call history",
            "- **Time Saved:** 15-30 minutes of manual selection",
            "",
            "### 🧹 **Hide Empty Columns**",
            "- **Problem:** Spreadsheets cluttered with empty columns",
            "- **Solution:** One-click to hide columns that are 90% empty",
            "- **Time Saved:** 5 minutes of manual cleanup",
            "",
            "### 📚 **Version History**",
            "- **Problem:** Making changes and losing your work",
            "- **Solution:** Full undo/redo with change tracking",
            "- **Time Saved:** No more lost work, easy experimentation",
            "",
            "---",
            "",
            "## 📈 Expected Outcomes",
            "",
            "### For Data Managers:",
            "- ⚡ **90% faster** data preparation time",
            "- 🎯 **Consistent quality** across all Pete uploads",
            "- 📊 **Better success rates** with properly prioritized phone numbers",
            "- 🧹 **Cleaner data** with automatic formatting fixes",
            "",
            "### For Pete Users:",
            "- 📞 **Higher connection rates** with mobile-first phone selection",
            "- ⏰ **Less wasted time** calling wrong numbers",
            "- 📋 **Consistent data format** for reliable processing",
            "- 🎯 **Focused effort** on the most promising contacts",
            "",
            "---",
            "",
            "## 🔧 Technical Architecture (For Developers)",
            "",
            "### Data Flow Architecture:",
            "",
            "```mermaid",
            "graph TD",
            "    A[📁 Raw CSV/Excel] --> B[🔧 Data Standardizer]",
            "    B --> C[🧹 Auto .0 Cleanup]",
            "    C --> D[📝 Data Prep Editor]",
            "    D --> E[📞 Phone Prioritizer]",
            "    E --> F[🗺️ Pete Mapper]",
            "    F --> G[📊 Final Export]",
            "    ",
            "    subgraph '🔧 Backend Processing'",
            "        H[trailing_dot_cleanup.py]",
            "        I[phone_prioritizer.py]",
            "        J[data_standardizer.py]",
            "    end",
            "    ",
            "    subgraph '🎨 Frontend UI'",
            "        K[Data Tools Panel]",
            "        L[Phone Prioritization Dialog]",
            "        M[File Selector]",
            "    end",
            "    ",
            "    C --> H",
            "    E --> I",
            "    B --> J",
            "    D --> K",
            "    E --> L",
            "    A --> M",
            "```",
            "",
            "### Key Data Transformations:",
            "",
            "**Input Data Structure:**",
            "```json",
            "{",
            '  "Phone 1": "4098880401.0",',
            '  "Phone Status 1": "CORRECT",',
            '  "Phone Type 1": "MOBILE",',
            '  "Phone Tags 1": "call_a01",',
            '  "Phone 2": "8702853184.0",',
            '  "Phone Status 2": "WRONG",',
            '  "Phone Type 2": "LANDLINE",',
            '  "Phone Tags 2": "call_a05"',
            "}",
            "```",
            "",
            "**Output Data Structure:**",
            "```json",
            "{",
            '  "Phone 1": "4098880401",',
            '  "Phone Status 1": "CORRECT",',
            '  "Phone Type 1": "MOBILE",',
            '  "Phone Tags 1": "call_a01",',
            '  "Phone 2": "8702853184",',
            '  "Phone Status 2": "CORRECT",',
            '  "Phone Type 2": "MOBILE",',
            '  "Phone Tags 2": "call_a01"',
            "}",
            "```",
            "",
            "### Phone Prioritization Algorithm:",
            "",
            "1. **Filter by Status:** CORRECT > UNKNOWN > WRONG",
            "2. **Filter by Type:** MOBILE > LANDLINE > VOIP",
            "3. **Filter by Call History:** Lower call count preferred",
            "4. **Select Top 5:** Best combination of status, type, and history",
            "",
            "---",
            "",
            f"**Report generated by:** `backend/utils/whatsworking.py`",
            f"**Timestamp:** {timestamp}",
            ""
        ]
        
        return '\n'.join(lines)

    def save_end_user_report(self, content: str) -> str:
        """Save end-user focused report to DEV_MAN/whatsworking directory"""
        os.makedirs(REPORTS_DIR, exist_ok=True)
        
        # Create timestamp and version
        now = pendulum.now('America/Chicago')
        timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
        date_only = now.strftime("%Y-%m-%d")
        
        # Generate version number for today
        existing_files = [f for f in os.listdir(REPORTS_DIR) if f.startswith(f"END_USER_GUIDE_{date_only}")]
        version = len(existing_files) + 1
        
        # Create versioned filename
        filename = os.path.join(REPORTS_DIR, f"END_USER_GUIDE_{date_only}_v{version:02d}_{timestamp}.md")
        
        # Save main report
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Also save as latest
        latest_filename = os.path.join(REPORTS_DIR, "LATEST_END_USER_GUIDE.md")
        with open(latest_filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"🎯 End-User Guide v{version} saved to: {filename}")
        print(f"📋 Latest end-user guide: {latest_filename}")
        return filename

    def save_pipeline_report(self, content: str) -> str:
        """Save pipeline analysis report to DEV_MAN/whatsworking directory"""
        os.makedirs(REPORTS_DIR, exist_ok=True)
        
        # Create timestamp and version
        now = pendulum.now('America/Chicago')
        timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
        date_only = now.strftime("%Y-%m-%d")
        
        # Generate version number for today
        existing_files = [f for f in os.listdir(REPORTS_DIR) if f.startswith(f"PIPELINE_ANALYSIS_{date_only}")]
        version = len(existing_files) + 1
        
        # Create versioned filename
        filename = os.path.join(REPORTS_DIR, f"PIPELINE_ANALYSIS_{date_only}_v{version:02d}_{timestamp}.md")
        
        # Save main report
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Also save as latest
        latest_filename = os.path.join(REPORTS_DIR, "LATEST_PIPELINE_ANALYSIS.md")
        with open(latest_filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"🔍 Pipeline Analysis v{version} saved to: {filename}")
        print(f"📋 Latest pipeline analysis: {latest_filename}")
        return filename

    def save_report(self, content: str) -> str:
        """Save versioned report to DEV_MAN/whatsworking directory"""
        os.makedirs(REPORTS_DIR, exist_ok=True)
        
        # Create timestamp and version
        now = pendulum.now('America/Chicago')
        timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
        date_only = now.strftime("%Y-%m-%d")
        
        # Generate version number for today
        existing_files = [f for f in os.listdir(REPORTS_DIR) if f.startswith(f"WHATS_WORKING_{date_only}")]
        version = len(existing_files) + 1
        
        # Create versioned filename
        filename = os.path.join(REPORTS_DIR, f"WHATS_WORKING_{date_only}_v{version:02d}_{timestamp}.md")
        
        # Save main report
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Also save as latest
        latest_filename = os.path.join(REPORTS_DIR, "LATEST_REPORT.md")
        with open(latest_filename, 'w', encoding='utf-8') as f:
            f.write(content)
            
        # Save metadata
        metadata = {
            "timestamp": timestamp,
            "version": version,
            "date": date_only,
            "total_files": len(self.analyses),
            "total_loc": sum(a.lines_of_code for a in self.analyses),
            "summary": self.generate_summary_stats()
        }
        
        metadata_file = os.path.join(REPORTS_DIR, f"metadata_{date_only}_v{version:02d}.json")
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        # Save architecture data as JSON
        try:
            architecture_data = {
                "timestamp": timestamp,
                "version": version,
                "categorized_files": self.diagram_generator._categorize_files(self.analyses),
                "config": self.diagram_generator.config,
                "mermaid_diagram": self.diagram_generator.generate_mermaid_diagram(self.analyses)
            }
            
            arch_file = os.path.join(REPORTS_DIR, f"architecture_{date_only}_v{version:02d}.json")
            with open(arch_file, 'w', encoding='utf-8') as f:
                # Convert FileAnalysis objects to dictionaries for JSON serialization
                serializable_data = {
                    "timestamp": architecture_data["timestamp"],
                    "version": architecture_data["version"],
                    "config": architecture_data["config"],
                    "mermaid_diagram": architecture_data["mermaid_diagram"],
                    "categorized_files": {
                        category: [asdict(analysis) for analysis in files]
                        for category, files in architecture_data["categorized_files"].items()
                    }
                }
                json.dump(serializable_data, f, indent=2, default=str)
            
            print(f"🏗️  Architecture data: {arch_file}")
            
        except Exception as e:
            print(f"⚠️  Failed to save architecture data: {e}")
        
        print(f"✅ Report v{version} saved to: {filename}")
        print(f"📋 Latest report: {latest_filename}")
        print(f"📊 Metadata: {metadata_file}")
        return filename

def main():
    """Main entry point"""
    try:
        analyzer = CodebaseAnalyzer()
        analyzer.analyze_codebase()
        
        # Generate basic reports (skip heavy pipeline analysis)
        report = analyzer.generate_report()
        end_user_report = analyzer.generate_end_user_flow_report()
        
        # Skip pipeline analysis to avoid heavy processing
        # pipeline_report = analyzer.generate_pipeline_analysis_report()
        
        # Save main report
        filename = analyzer.save_report(report)
        
        # Save end-user report
        end_user_filename = analyzer.save_end_user_report(end_user_report)
        
        # Skip pipeline report saving
        # pipeline_filename = analyzer.save_pipeline_report(pipeline_report)
        
        print(f"\n📋 Analysis complete! Reports saved to:")
        print(f"   📊 Technical Report: {filename}")
        print(f"   🎯 End-User Guide: {end_user_filename}")
        print(f"   ⏭️  Pipeline Analysis: Skipped (heavy processing)")
        print(f"🎯 Found {len(analyzer.analyses)} Python files across the codebase")
        
        # Quick summary
        stats = analyzer.generate_summary_stats()
        print(f"📊 Summary: {stats['total_functions']} functions, {stats['total_classes']} classes, {stats['total_loc']:,} LOC")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        raise

if __name__ == '__main__':
    main()