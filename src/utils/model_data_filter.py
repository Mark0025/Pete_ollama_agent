#!/usr/bin/env python3
"""
Model Data Filter Utility

Uses psutil to filter and analyze model data, responses, and performance metrics.
Can be used anywhere in the application for consistent data filtering.
"""

import psutil
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class FilterCriteria:
    """Filter criteria for model data"""
    time_period: str = "all"  # all, today, week, month
    data_type: str = "all"    # all, tests, models, responses
    model_filter: str = "all" # all, ollama, openrouter, runpod
    status_filter: str = "all" # all, pass, fail, error
    min_duration: int = 0
    max_duration: int = 999999
    min_quality: float = 0.0
    max_quality: float = 10.0
    min_tokens: int = 0
    max_tokens: int = 999999
    model_name_pattern: str = ""  # regex pattern for model names

@dataclass
class FileMetadata:
    """File metadata using psutil"""
    size_mb: float
    created: str
    modified: str
    accessed: str
    permissions: str
    owner: str

class ModelDataFilter:
    """Utility for filtering model data and responses using psutil"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.cache = {}
    
    def get_file_metadata(self, file_path: Union[str, Path]) -> Optional[FileMetadata]:
        """Get file metadata using psutil"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return None
            
            # Get file stats using os.stat (psutil doesn't have stat)
            stat = file_path.stat()
            
            # Get file owner info
            try:
                owner = stat.st_uid
                if hasattr(psutil, 'users'):
                    users = psutil.users()
                    owner_name = next((u.name for u in users if u.pid == owner), str(owner))
                else:
                    owner_name = str(owner)
            except:
                owner_name = "unknown"
            
            return FileMetadata(
                size_mb=round(stat.st_size / (1024 * 1024), 2),
                created=datetime.fromtimestamp(stat.st_ctime).isoformat(),
                modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                accessed=datetime.fromtimestamp(stat.st_atime).isoformat(),
                permissions=oct(stat.st_mode)[-3:],
                owner=owner_name
            )
        except Exception as e:
            logger.error(f"Error getting file metadata for {file_path}: {e}")
            return None
    
    def filter_test_results(self, test_data: Dict[str, Any], criteria: FilterCriteria) -> List[Dict[str, Any]]:
        """Filter test results based on criteria"""
        filtered_results = []
        
        if 'test_results' not in test_data:
            return filtered_results
        
        for test in test_data['test_results']:
            # Apply time period filter
            if not self._passes_time_filter(test, criteria.time_period):
                continue
            
            # Apply data type filter
            if not self._passes_data_type_filter(test, criteria.data_type):
                continue
            
            # Apply model filter
            if not self._passes_model_filter(test, criteria.model_filter):
                continue
            
            # Apply status filter
            if not self._passes_status_filter(test, criteria.status_filter):
                continue
            
            # Apply duration filter
            if not self._passes_duration_filter(test, criteria.min_duration, criteria.max_duration):
                continue
            
            # Apply quality filter
            if not self._passes_quality_filter(test, criteria.min_quality, criteria.max_quality):
                continue
            
            # Apply token filter
            if not self._passes_token_filter(test, criteria.min_tokens, criteria.max_tokens):
                continue
            
            # Apply model name pattern filter
            if criteria.model_name_pattern and not self._passes_name_pattern_filter(test, criteria.model_name_pattern):
                continue
            
            filtered_results.append(test)
        
        # Sort by timestamp (newest first)
        filtered_results.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return filtered_results
    
    def _passes_time_filter(self, test: Dict[str, Any], time_period: str) -> bool:
        """Check if test passes time period filter"""
        if time_period == "all":
            return True
        
        try:
            test_time = datetime.fromisoformat(test.get('timestamp', '2025-01-01'))
            now = datetime.now()
            
            if time_period == "today":
                return test_time.date() == now.date()
            elif time_period == "week":
                return test_time >= now - timedelta(days=7)
            elif time_period == "month":
                return test_time >= now - timedelta(days=30)
            
            return True
        except:
            return True
    
    def _passes_data_type_filter(self, test: Dict[str, Any], data_type: str) -> bool:
        """Check if test passes data type filter"""
        if data_type == "all":
            return True
        
        test_name = test.get('test_name', '').lower()
        
        if data_type == "tests":
            return "test" in test_name
        elif data_type == "models":
            return "model" in test_name
        elif data_type == "responses":
            return "response" in test_name or "generate" in test_name
        
        return True
    
    def _passes_model_filter(self, test: Dict[str, Any], model_filter: str) -> bool:
        """Check if test passes model filter"""
        if model_filter == "all":
            return True
        
        test_model = test.get('details', {}).get('result', {}).get('model', '').lower()
        
        if model_filter == "ollama":
            return "ollama" in test_model
        elif model_filter == "openrouter":
            return "openrouter" in test_model or "gpt" in test_model or "claude" in test_model
        elif model_filter == "runpod":
            return "runpod" in test_model
        
        return True
    
    def _passes_status_filter(self, test: Dict[str, Any], status_filter: str) -> bool:
        """Check if test passes status filter"""
        if status_filter == "all":
            return True
        
        test_status = test.get('status', '').lower()
        return status_filter.lower() in test_status
    
    def _passes_duration_filter(self, test: Dict[str, Any], min_duration: int, max_duration: int) -> bool:
        """Check if test passes duration filter"""
        test_duration = test.get('details', {}).get('result', {}).get('duration_ms', 0)
        return min_duration <= test_duration <= max_duration
    
    def _passes_quality_filter(self, test: Dict[str, Any], min_quality: float, max_quality: float) -> bool:
        """Check if test passes quality filter"""
        test_quality = test.get('details', {}).get('result', {}).get('quality_score', 5.0)
        return min_quality <= test_quality <= max_quality
    
    def _passes_token_filter(self, test: Dict[str, Any], min_tokens: int, max_tokens: int) -> bool:
        """Check if test passes token filter"""
        result = test.get('details', {}).get('result', {})
        total_tokens = result.get('response_data', {}).get('usage', {}).get('total_tokens', 0)
        return min_tokens <= total_tokens <= max_tokens
    
    def _passes_name_pattern_filter(self, test: Dict[str, Any], pattern: str) -> bool:
        """Check if test passes model name pattern filter"""
        if not pattern:
            return True
        
        test_model = test.get('details', {}).get('result', {}).get('model', '')
        try:
            import re
            return bool(re.search(pattern, test_model, re.IGNORECASE))
        except:
            return pattern.lower() in test_model.lower()
    
    def analyze_model_files(self, models_dir: str = "models") -> List[Dict[str, Any]]:
        """Analyze model files using psutil for size, dates, etc."""
        models_path = self.project_root / models_dir
        if not models_path.exists():
            return []
        
        model_files = []
        
        for file_path in models_path.rglob("*"):
            if file_path.is_file():
                metadata = self.get_file_metadata(file_path)
                if metadata:
                    model_files.append({
                        "name": file_path.name,
                        "path": str(file_path.relative_to(self.project_root)),
                        "metadata": metadata,
                        "type": self._get_file_type(file_path)
                    })
        
        return sorted(model_files, key=lambda x: x.metadata.modified, reverse=True)
    
    def _get_file_type(self, file_path: Path) -> str:
        """Determine file type based on extension"""
        ext = file_path.suffix.lower()
        if ext in ['.gguf', '.bin', '.safetensors']:
            return "model"
        elif ext in ['.json', '.yaml', '.yml', '.toml']:
            return "config"
        elif ext in ['.md', '.txt']:
            return "documentation"
        elif ext in ['.py', '.js', '.ts']:
            return "code"
        else:
            return "other"
    
    def get_filtered_data_summary(self, test_data: Dict[str, Any], criteria: FilterCriteria) -> Dict[str, Any]:
        """Get summary of filtered data with metadata"""
        filtered_results = self.filter_test_results(test_data, criteria)
        
        # Calculate summary statistics
        total_duration = sum(
            result.get('details', {}).get('result', {}).get('duration_ms', 0) 
            for result in filtered_results
        )
        
        success_count = sum(1 for result in filtered_results if result.get('status', '').lower() == 'pass')
        success_rate = (success_count / len(filtered_results) * 100) if filtered_results else 0
        
        models_used = set()
        for result in filtered_results:
            model = result.get('details', {}).get('result', {}).get('model', '')
            if model:
                models_used.add(model)
        
        return {
            "total_results": len(filtered_results),
            "success_rate": round(success_rate, 1),
            "average_duration": total_duration / len(filtered_results) if filtered_results else 0,
            "models_used": list(models_used),
            "filters_applied": {
                "time_period": criteria.time_period,
                "data_type": criteria.data_type,
                "model_filter": criteria.model_filter,
                "status_filter": criteria.status_filter,
                "min_duration": criteria.min_duration,
                "max_duration": criteria.max_duration,
                "min_quality": criteria.min_quality,
                "max_quality": criteria.max_quality,
                "min_tokens": criteria.min_tokens,
                "max_tokens": criteria.max_tokens
            }
        }

# Convenience functions for easy use anywhere in the app
def create_filter_criteria(**kwargs) -> FilterCriteria:
    """Create filter criteria with keyword arguments"""
    return FilterCriteria(**kwargs)

def filter_model_data(test_data: Dict[str, Any], criteria: FilterCriteria, project_root: str = ".") -> List[Dict[str, Any]]:
    """Filter model data using the utility"""
    filter_util = ModelDataFilter(project_root)
    return filter_util.filter_test_results(test_data, criteria)

def get_model_files_analysis(project_root: str = ".", models_dir: str = "models") -> List[Dict[str, Any]]:
    """Get analysis of model files"""
    filter_util = ModelDataFilter(project_root)
    return filter_util.analyze_model_files(models_dir)
