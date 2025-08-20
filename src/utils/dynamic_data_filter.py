#!/usr/bin/env python3
"""
Dynamic Data Filter Utility

A generic, intelligent filtering system that can work with ANY JSON data structure.
Automatically discovers filterable fields and creates dynamic filtering options.
Uses Pydantic for type safety and validation.
"""

import json
import psutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Set
from dataclasses import dataclass, field
import logging
from collections import defaultdict
from pydantic import BaseModel, Field, validator
import pandas as pd

logger = logging.getLogger(__name__)

# ===== PYDANTIC MODELS FOR TYPE SAFETY =====

class FieldMetadata(BaseModel):
    """Metadata about a field in the data"""
    name: str = Field(..., description="Field name")
    path: str = Field(..., description="JSON path to the field")
    data_type: str = Field(..., description="Data type (string, number, boolean, date, array, object)")
    filter_type: str = Field(..., description="Recommended filter type")
    unique_count: int = Field(0, description="Number of unique values")
    sample_values: List[str] = Field(default_factory=list, description="Sample values for the field")
    min_value: Optional[Union[int, float, str]] = Field(None, description="Minimum value (for numeric fields)")
    max_value: Optional[Union[int, float, str]] = Field(None, description="Maximum value (for numeric fields)")
    is_filterable: bool = Field(True, description="Whether this field can be filtered")
    is_displayable: bool = Field(True, description="Whether this field should be shown in tables")

class FilterCriteria(BaseModel):
    """Dynamic filter criteria that adapts to the data structure"""
    field_filters: Dict[str, Any] = Field(default_factory=dict, description="Field-specific filters")
    text_search: str = Field("", description="Global text search across string fields")
    sort_by: str = Field("", description="Field to sort by")
    sort_order: str = Field("desc", description="Sort order (asc/desc)")
    limit: int = Field(100, description="Maximum number of results")
    offset: int = Field(0, description="Number of results to skip")
    selected_columns: List[str] = Field(default_factory=list, description="Columns to display in table")

class DataAnalysisResult(BaseModel):
    """Result of analyzing a data structure"""
    total_items: int = Field(..., description="Total number of items in the dataset")
    fields_discovered: int = Field(..., description="Number of fields discovered")
    filterable_fields: int = Field(..., description="Number of fields that can be filtered")
    field_types: Dict[str, int] = Field(default_factory=dict, description="Count of each field type")
    field_metadata: Dict[str, FieldMetadata] = Field(..., description="Metadata for each field")
    data_summary: Dict[str, Any] = Field(default_factory=dict, description="Summary statistics")

class FilteredDataResult(BaseModel):
    """Result of filtering data"""
    success: bool = Field(..., description="Whether filtering was successful")
    total_results: int = Field(..., description="Total number of results after filtering")
    results: List[Dict[str, Any]] = Field(..., description="Filtered results")
    applied_filters: Dict[str, Any] = Field(..., description="Filters that were applied")
    columns_available: List[str] = Field(..., description="Available columns for display")
    pagination: Dict[str, Any] = Field(default_factory=dict, description="Pagination information")

# ===== MAIN DYNAMIC DATA FILTER CLASS =====

class DynamicDataFilter:
    """
    Generic data filtering utility that automatically discovers structure
    and creates intelligent filtering options
    """
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.cache = {}
        self.analysis_cache = {}
    
    def analyze_data_structure(self, data: Union[Dict, List], max_depth: int = 5) -> DataAnalysisResult:
        """
        Automatically analyze any JSON data structure to discover filterable fields
        Returns a Pydantic model with complete analysis
        """
        cache_key = str(hash(str(data)[:1000]))  # Simple cache key
        if cache_key in self.analysis_cache:
            return self.analysis_cache[cache_key]
        
        fields = {}
        
        if isinstance(data, list):
            # Analyze first few items to understand structure
            for item in data[:20]:  # Sample first 20 items
                self._analyze_object(item, "", fields, max_depth)
        elif isinstance(data, dict):
            self._analyze_object(data, "", fields, max_depth)
        
        # Post-process fields to determine filter types and metadata
        for field_name, field_info in fields.items():
            self._determine_filter_type(field_info)
        
        # Create field metadata objects
        field_metadata = {}
        for field_name, field_info in fields.items():
            field_metadata[field_name] = FieldMetadata(
                name=field_name,
                path=field_info.path,
                data_type=field_info.data_type,
                filter_type=field_info.filter_type,
                unique_count=field_info.unique_count,
                sample_values=list(field_info.sample_values)[:10],  # Limit to 10 samples
                min_value=field_info.min_value,
                max_value=field_info.max_value,
                is_filterable=field_info.is_filterable,
                is_displayable=field_info.is_displayable
            )
        
        # Generate summary statistics
        data_summary = self._generate_data_summary(data, fields)
        
        result = DataAnalysisResult(
            total_items=len(data) if isinstance(data, list) else 1,
            fields_discovered=len(fields),
            filterable_fields=len([f for f in fields.values() if f.is_filterable]),
            field_types=defaultdict(int, {f.data_type: sum(1 for field in fields.values() if field.data_type == f.data_type) for f in fields.values()}),
            field_metadata=field_metadata,
            data_summary=data_summary
        )
        
        # Cache the result
        self.analysis_cache[cache_key] = result
        return result
    
    def _analyze_object(self, obj: Any, path: str, fields: Dict[str, Any], depth: int):
        """Recursively analyze object structure"""
        if depth <= 0 or not isinstance(obj, (dict, list)):
            return
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                self._analyze_value(key, current_path, value, fields, depth - 1)
        elif isinstance(obj, list):
            for i, item in enumerate(obj[:10]):  # Sample first 10 items
                current_path = f"{path}[{i}]"
                self._analyze_value(f"item_{i}", current_path, item, fields, depth - 1)
    
    def _analyze_value(self, key: str, path: str, value: Any, fields: Dict[str, Any], depth: int):
        """Analyze a single value and update field info"""
        if key not in fields:
            fields[key] = type('FieldInfo', (), {
                'name': key,
                'path': path,
                'data_type': self._get_data_type(value),
                'sample_values': set(),
                'unique_count': 0,
                'min_value': None,
                'max_value': None,
                'is_filterable': True,
                'is_displayable': True
            })()
        
        field_info = fields[key]
        field_info.sample_values.add(str(value)[:100])  # Limit sample value length
        
        # Update min/max for numeric values
        if isinstance(value, (int, float)):
            if field_info.min_value is None or value < field_info.min_value:
                field_info.min_value = value
            if field_info.max_value is None or value > field_info.max_value:
                field_info.max_value = value
        
        # Recursively analyze nested objects
        if isinstance(value, (dict, list)) and depth > 0:
            self._analyze_object(value, path, fields, depth)
    
    def _get_data_type(self, value: Any) -> str:
        """Determine the data type of a value"""
        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, str):
            # Try to detect if it's a date
            try:
                datetime.fromisoformat(value.replace('Z', '+00:00'))
                return "date"
            except:
                return "string"
        elif isinstance(value, list):
            return "array"
        elif isinstance(value, dict):
            return "object"
        else:
            return "unknown"
    
    def _determine_filter_type(self, field_info: Any):
        """Determine the best filter type for a field"""
        sample_values = list(field_info.sample_values)
        
        if field_info.data_type in ["integer", "float"]:
            field_info.filter_type = "range"
        elif field_info.data_type == "boolean":
            field_info.filter_type = "dropdown"
            field_info.options = [True, False]
        elif field_info.data_type == "date":
            field_info.filter_type = "date_range"
        elif field_info.data_type == "string":
            if len(sample_values) <= 20:  # Small number of unique values
                field_info.filter_type = "dropdown"
                field_info.options = sorted(sample_values)
            else:
                field_info.filter_type = "text_search"
        else:
            field_info.filter_type = "text_search"
        
        field_info.unique_count = len(field_info.sample_values)
    
    def _generate_data_summary(self, data: Union[Dict, List], fields: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive data summary"""
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict) and 'test_results' in data:
            items = data['test_results']
        else:
            items = [data]
        
        summary = {
            "total_items": len(items),
            "fields_discovered": len(fields),
            "filterable_fields": len([f for f in fields.values() if f.is_filterable]),
            "field_types": defaultdict(int),
            "field_summaries": {}
        }
        
        # Count field types
        for field_info in fields.values():
            summary["field_types"][field_info.data_type] += 1
        
        # Generate field summaries
        for field_name, field_info in fields.items():
            summary["field_summaries"][field_name] = {
                "type": field_info.data_type,
                "filter_type": field_info.filter_type,
                "unique_values": field_info.unique_count,
                "sample_values": list(field_info.sample_values)[:5],  # First 5 samples
                "range": {
                    "min": field_info.min_value,
                    "max": field_info.max_value
                } if field_info.data_type in ["integer", "float"] else None
            }
        
        return summary
    
    def filter_data(self, data: Union[Dict, List], criteria: FilterCriteria, fields: Dict[str, FieldMetadata]) -> FilteredDataResult:
        """
        Filter data based on dynamic criteria
        Returns a Pydantic model with filtered results
        """
        try:
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict) and 'test_results' in data:
                items = data['test_results']
            else:
                items = [data]
            
            filtered_items = []
            
            for item in items:
                if self._item_passes_filters(item, criteria, fields):
                    filtered_items.append(item)
            
            # Apply sorting
            if criteria.sort_by:
                filtered_items.sort(
                    key=lambda x: self._get_nested_value(x, criteria.sort_by),
                    reverse=(criteria.sort_order == "desc")
                )
            
            # Apply pagination
            start = criteria.offset
            end = start + criteria.limit
            paginated_results = filtered_items[start:end]
            
            # Determine available columns
            columns_available = list(fields.keys()) if fields else []
            
            # Apply column selection if specified
            if criteria.selected_columns:
                paginated_results = self._apply_column_selection(paginated_results, criteria.selected_columns)
            
            return FilteredDataResult(
                success=True,
                total_results=len(filtered_items),
                results=paginated_results,
                applied_filters=criteria.dict(),
                columns_available=columns_available,
                pagination={
                    "page": (criteria.offset // criteria.limit) + 1,
                    "total_pages": (len(filtered_items) + criteria.limit - 1) // criteria.limit,
                    "items_per_page": criteria.limit,
                    "has_next": end < len(filtered_items),
                    "has_previous": criteria.offset > 0
                }
            )
            
        except Exception as e:
            logger.error(f"Error filtering data: {str(e)}")
            return FilteredDataResult(
                success=False,
                total_results=0,
                results=[],
                applied_filters=criteria.dict(),
                columns_available=[],
                pagination={}
            )
    
    def _item_passes_filters(self, item: Dict, criteria: FilterCriteria, fields: Dict[str, FieldMetadata]) -> bool:
        """Check if an item passes all applied filters"""
        
        # Apply field-specific filters
        for field_path, filter_value in criteria.field_filters.items():
            if not self._apply_field_filter(item, field_path, filter_value, fields):
                return False
        
        # Apply text search across all string fields
        if criteria.text_search:
            if not self._apply_text_search(item, criteria.text_search, fields):
                return False
        
        return True
    
    def _apply_field_filter(self, item: Dict, field_path: str, filter_value: Any, fields: Dict[str, FieldMetadata]) -> bool:
        """Apply a specific field filter"""
        field_value = self._get_nested_value(item, field_path)
        
        if field_value is None:
            return False
        
        # Handle different filter types
        field_info = next((f for f in fields.values() if f.path == field_path), None)
        if not field_info:
            return True  # Unknown field, don't filter
        
        if field_info.filter_type == "dropdown":
            return field_value in filter_value
        elif field_info.filter_type == "range":
            if isinstance(filter_value, dict):
                min_val = filter_value.get('min')
                max_val = filter_value.get('max')
                if min_val is not None and field_value < min_val:
                    return False
                if max_val is not None and field_value > max_val:
                    return False
        elif field_info.filter_type == "text_search":
            if isinstance(filter_value, str) and filter_value.lower() not in str(field_value).lower():
                return False
        
        return True
    
    def _apply_text_search(self, item: Dict, search_text: str, fields: Dict[str, FieldMetadata]) -> bool:
        """Apply text search across string fields"""
        search_text = search_text.lower()
        
        for field_info in fields.values():
            if field_info.data_type == "string":
                field_value = self._get_nested_value(item, field_info.path)
                if field_value and search_text in str(field_value).lower():
                    return True
        
        return False
    
    def _get_nested_value(self, obj: Any, path: str) -> Any:
        """Get a nested value from an object using dot notation path"""
        try:
            for key in path.split('.'):
                if '[' in key and ']' in key:
                    # Handle array access like "items[0].name"
                    array_key, index = key.split('[')
                    index = int(index.rstrip(']'))
                    obj = obj[array_key][index]
                else:
                    obj = obj[key]
        except (KeyError, IndexError, TypeError):
            return None
        return obj
    
    def _apply_column_selection(self, results: List[Dict], selected_columns: List[str]) -> List[Dict]:
        """Apply column selection to results"""
        if not selected_columns:
            return results
        
        filtered_results = []
        for item in results:
            filtered_item = {}
            for col in selected_columns:
                if col in item:
                    filtered_item[col] = item[col]
            filtered_results.append(filtered_item)
        
        return filtered_results
    
    def export_to_csv(self, data: List[Dict], filename: str = "exported_data.csv") -> str:
        """Export filtered data to CSV"""
        try:
            if not data:
                return "No data to export"
            
            df = pd.DataFrame(data)
            csv_path = Path(self.project_root) / filename
            df.to_csv(csv_path, index=False)
            return str(csv_path)
        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            return f"Export failed: {str(e)}"
    
    def get_benchmark_metrics(self, data: Union[Dict, List]) -> Dict[str, Any]:
        """Extract benchmark metrics from data"""
        try:
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict) and 'test_results' in data:
                items = data['test_results']
            else:
                items = [data]
            
            metrics = {
                "total_items": len(items),
                "success_rate": 0,
                "avg_duration": 0,
                "field_analysis": {},
                "performance_summary": {}
            }
            
            if not items:
                return metrics
            
            # Analyze success rate
            success_count = 0
            total_duration = 0
            duration_count = 0
            
            for item in items:
                if isinstance(item, dict):
                    # Check for success indicators
                    status = item.get('status', '').lower()
                    if 'pass' in status or 'success' in status:
                        success_count += 1
                    
                    # Check for duration
                    duration = item.get('duration_ms') or item.get('duration')
                    if duration and isinstance(duration, (int, float)):
                        total_duration += duration
                        duration_count += 1
            
            if len(items) > 0:
                metrics["success_rate"] = (success_count / len(items)) * 100
            
            if duration_count > 0:
                metrics["avg_duration"] = total_duration / duration_count
            
            # Analyze field patterns
            field_counts = defaultdict(int)
            for item in items:
                if isinstance(item, dict):
                    for key in item.keys():
                        field_counts[key] += 1
            
            metrics["field_analysis"] = dict(field_counts)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting benchmark metrics: {str(e)}")
            return {"error": str(e)}

# ===== CONVENIENCE FUNCTIONS =====

def create_dynamic_filter(project_root: str = ".") -> DynamicDataFilter:
    """Create a dynamic data filter instance"""
    return DynamicDataFilter(project_root)

def analyze_any_data(data: Union[Dict, List], project_root: str = ".") -> DataAnalysisResult:
    """Analyze any data structure and return field information"""
    filter_util = DynamicDataFilter(project_root)
    return filter_util.analyze_data_structure(data)

def filter_any_data(data: Union[Dict, List], criteria: FilterCriteria, fields: Dict[str, FieldMetadata], project_root: str = ".") -> FilteredDataResult:
    """Filter any data using the dynamic filter"""
    filter_util = DynamicDataFilter(project_root)
    return filter_util.filter_data(data, criteria, fields)

def get_benchmark_metrics(data: Union[Dict, List], project_root: str = ".") -> Dict[str, Any]:
    """Get benchmark metrics from any data structure"""
    filter_util = DynamicDataFilter(project_root)
    return filter_util.get_benchmark_metrics(data)
