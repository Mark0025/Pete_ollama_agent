#!/usr/bin/env python3
"""
TestResultsUpdater - Individual module interface
Provides test results aggregation functionality
"""

import json
from pathlib import Path
from datetime import datetime

class TestResultsUpdater:
    """Test results updater and aggregator"""
    
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.test_results_dir = self.project_root / "DEV_MAN"
    
    def update_all_results(self):
        """Update and aggregate all test results"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "test_files": [],
            "latest_results": None,
            "summary": {
                "total_test_files": 0,
                "latest_test_count": 0,
                "latest_passed": 0,
                "latest_failed": 0
            }
        }
        
        # Find test result files
        test_files = list(self.test_results_dir.glob("**/test_results_*.json"))
        
        for test_file in test_files:
            try:
                with open(test_file, 'r') as f:
                    test_data = json.load(f)
                results["test_files"].append({
                    "file": str(test_file),
                    "size": test_file.stat().st_size,
                    "modified": test_file.stat().st_mtime
                })
                
                # Use the most recent as latest
                if results["latest_results"] is None:
                    results["latest_results"] = test_data
                    results["summary"]["latest_test_count"] = test_data.get("total_tests", 0)
                    results["summary"]["latest_passed"] = test_data.get("passed_tests", 0)
                    results["summary"]["latest_failed"] = test_data.get("failed_tests", 0)
                    
            except Exception as e:
                print(f"Error reading test file {test_file}: {e}")
        
        results["summary"]["total_test_files"] = len(test_files)
        return results
