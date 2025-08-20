#!/usr/bin/env python3
"""
FeatureTracker - Individual module interface
Delegates to the main whatsworking_platform collector
"""

from ..whatsworking_platform.collectors.feature_tracker import StatusReporter

class FeatureTracker:
    """Feature tracker wrapper that uses the platform's status reporter"""
    
    def __init__(self, project_root):
        self.status_reporter = StatusReporter(str(project_root))
        self.project_root = project_root
    
    def track_all_features(self):
        """Track all features and their health"""
        status = self.status_reporter.check_serverless_status()
        return {
            "features": {
                "serverless": status,
                "environment": status.get("environment", {}),
                "files": status.get("files", {}),
                "dependencies": status.get("dependencies", {})
            },
            "health_summary": {
                "overall": status.get("overall", "unknown"),
                "ready_for_deployment": status.get("ready_for_deployment", False)
            }
        }
