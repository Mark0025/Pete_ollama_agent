#!/usr/bin/env python3
"""
Code Finder Module - Extracted from main.py

This module handles finding and searching for code files across the system.
"""

import os
import shutil
from pathlib import Path
from typing import List, Tuple
from rich.console import Console

console = Console()

class CodeFinder:
    """Find code files matching patterns across the system"""
    
    def __init__(self, target_dir: Path):
        self.target_dir = Path(target_dir).resolve()
        self.found_items = []
        
        # Only look for actual code files, not documentation
        self.code_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.rs', '.java', 
            '.c', '.cpp', '.h', '.hpp', '.cs', '.php', '.rb', '.swift',
            '.kt', '.scala', '.clj', '.hs', '.ml', '.r', '.m', '.pl',
            '.sh', '.bash', '.zsh', '.ps1', '.sql', '.json', '.yaml', '.yml',
            '.toml', '.ini', '.cfg', '.conf', '.env', '.dockerfile'
        }
        
        self.search_patterns = [
            "whatsworking",
            "whatsworing",  # typo version
            "whats_working",
            "what_is_working",
            "update_whats_working"
        ]
    
    def _directory_has_code_files(self, directory: Path) -> bool:
        """Check if a directory contains any code files"""
        try:
            # Check up to 3 levels deep for code files
            for file_path in directory.rglob("*"):
                if file_path.is_file() and file_path.suffix.lower() in self.code_extensions:
                    return True
        except (PermissionError, OSError):
            pass
        return False
    
    def search(self, pattern: str = "whatsworking", max_depth: int = 5) -> List[str]:
        """Search for files matching a pattern"""
        found = []
        
        try:
            # Skip certain directories that are typically not relevant
            skip_dirs = {
                '.git', '.svn', '.hg', 'node_modules', '__pycache__', 
                '.venv', 'venv', '.env', 'env', 'build', 'dist',
                'Library', 'Applications', 'System', 'private/var',
                '.Trash', '.cache', '.npm', '.yarn'
            }
            
            def _search_recursive(current_path: Path, current_depth: int = 0):
                if current_depth > max_depth:
                    return
                    
                try:
                    if not current_path.exists() or not os.access(current_path, os.R_OK):
                        return
                        
                    for item in current_path.iterdir():
                        try:
                            # Skip if we don't have read permissions
                            if not os.access(item, os.R_OK):
                                continue
                                
                            item_name_lower = item.name.lower()
                            
                            # Check if this item matches our pattern
                            if pattern.lower() in item_name_lower:
                                # Don't include our own target directory
                                if item.resolve() != self.target_dir.resolve():
                                    if item.is_dir():
                                        # For directories, check if they contain code files
                                        has_code_files = self._directory_has_code_files(item)
                                        if has_code_files:
                                            found.append(str(item))
                                    elif item.is_file():
                                        # For files, only include if they have code extensions
                                        if item.suffix.lower() in self.code_extensions:
                                            found.append(str(item))
                                        
                        except (PermissionError, OSError):
                            continue
                            
                        # Recursively search subdirectories
                        if item.is_dir() and item.name not in skip_dirs:
                            _search_recursive(item, current_depth + 1)
                            
                except (PermissionError, OSError):
                    pass
            
            # Start search from common locations
            search_paths = [
                Path.home(),
                Path.home() / "Desktop",
                Path.home() / "Documents",
                Path.home() / "Projects",
                Path.home() / "Development"
            ]
            
            for search_path in search_paths:
                if search_path.exists():
                    _search_recursive(search_path, 0)
            
        except Exception as e:
            console.print(f"[red]Search error: {e}[/red]")
        
        return found
    
    def copy_items(self, items: List[str], dry_run: bool = False) -> bool:
        """Copy found items to target directory"""
        if not items:
            return True
        
        success_count = 0
        error_count = 0
        
        for item_path in items:
            try:
                source_path = Path(item_path)
                if not source_path.exists():
                    continue
                
                if source_path.is_file():
                    # Copy file
                    dest_path = self.target_dir / source_path.name
                    if not dry_run:
                        shutil.copy2(source_path, dest_path)
                    console.print(f"📄 {'[DRY RUN] ' if dry_run else ''}Copied: {source_path.name}")
                    success_count += 1
                    
                elif source_path.is_dir():
                    # Copy directory
                    dest_path = self.target_dir / source_path.name
                    if not dry_run:
                        if dest_path.exists():
                            shutil.rmtree(dest_path)
                        shutil.copytree(source_path, dest_path)
                    console.print(f"📁 {'[DRY RUN] ' if dry_run else ''}Copied: {source_path.name}/")
                    success_count += 1
                    
            except Exception as e:
                console.print(f"[red]❌ Failed to copy {item_path}: {e}[/red]")
                error_count += 1
        
        if dry_run:
            console.print(f"[yellow]DRY RUN: Would copy {success_count} items[/yellow]")
        else:
            console.print(f"[green]✅ Successfully copied {success_count} items[/green]")
            if error_count > 0:
                console.print(f"[red]❌ Failed to copy {error_count} items[/red]")
        
        return error_count == 0
