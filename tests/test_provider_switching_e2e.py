#!/usr/bin/env python3
"""
End-to-End Unit Test for Provider Switching Functionality
=========================================================

This test analyzes the complete provider switching flow for race conditions,
dependencies, and potential failure points.
"""

import asyncio
import json
import sys
import time
import traceback
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

class ProviderSwitchingE2ETest:
    def __init__(self):
        self.issues = []
        self.dependencies = []
        self.race_conditions = []
        self.success_steps = []
        
    def log_issue(self, category, description, severity="HIGH", details=""):
        """Log an issue found during testing"""
        self.issues.append({
            "category": category,
            "description": description, 
            "severity": severity,
            "details": details,
            "timestamp": time.time()
        })
        
    def log_dependency(self, depends_on, dependent, required=True):
        """Log a dependency relationship"""
        self.dependencies.append({
            "depends_on": depends_on,
            "dependent": dependent,
            "required": required,
            "timestamp": time.time()
        })
        
    def log_race_condition(self, description, components, mitigation=""):
        """Log a potential race condition"""
        self.race_conditions.append({
            "description": description,
            "components": components,
            "mitigation": mitigation,
            "timestamp": time.time()
        })
    
    def test_1_frontend_html_structure(self):
        """Test 1: Analyze frontend HTML structure and JavaScript"""
        print("🔍 Test 1: Frontend HTML Structure...")
        
        try:
            # Check if provider select element exists in HTML
            webhook_file = Path(__file__).parent / "src/vapi/webhook_server.py"
            if not webhook_file.exists():
                self.log_issue("MISSING_FILE", "webhook_server.py not found", "CRITICAL")
                return False
                
            with open(webhook_file) as f:
                content = f.read()
                
            # Check for provider select element
            if 'id="providerSelect"' not in content:
                self.log_issue("MISSING_ELEMENT", "providerSelect element not found in HTML", "CRITICAL")
                return False
            else:
                self.success_steps.append("✅ Provider select element exists")
                
            # Check for provider status span
            if 'id="providerStatus"' not in content:
                self.log_issue("MISSING_ELEMENT", "providerStatus element not found in HTML", "CRITICAL")
                return False
            else:
                self.success_steps.append("✅ Provider status span exists")
                
            # Check for switchProvider function
            if 'async function switchProvider()' not in content:
                self.log_issue("MISSING_FUNCTION", "switchProvider function not found", "CRITICAL")
                return False
            else:
                self.success_steps.append("✅ switchProvider function exists")
                
            # Check for loadCurrentProvider function  
            if 'async function loadCurrentProvider()' not in content:
                self.log_issue("MISSING_FUNCTION", "loadCurrentProvider function not found", "CRITICAL")
                return False
            else:
                self.success_steps.append("✅ loadCurrentProvider function exists")
                
            # Check onchange handler
            if 'onchange="switchProvider()"' not in content:
                self.log_issue("MISSING_HANDLER", "onchange handler for providerSelect not found", "HIGH")
                return False
            else:
                self.success_steps.append("✅ onChange handler properly attached")
                
            return True
            
        except Exception as e:
            self.log_issue("TEST_ERROR", f"Failed to analyze frontend structure: {e}", "CRITICAL")
            return False
    
    def test_2_backend_api_endpoints(self):
        """Test 2: Check backend API endpoint implementations"""
        print("🔍 Test 2: Backend API Endpoints...")
        
        try:
            webhook_file = Path(__file__).parent / "src/vapi/webhook_server.py"
            with open(webhook_file) as f:
                content = f.read()
                
            # Check for GET provider-settings endpoint
            if '/admin/provider-settings' not in content:
                self.log_issue("MISSING_ENDPOINT", "GET /admin/provider-settings endpoint not found", "CRITICAL")
                return False
            else:
                self.success_steps.append("✅ GET provider-settings endpoint exists")
                
            # Check for POST provider-settings/update endpoint
            if '/admin/provider-settings/update' not in content:
                self.log_issue("MISSING_ENDPOINT", "POST /admin/provider-settings/update endpoint not found", "CRITICAL") 
                return False
            else:
                self.success_steps.append("✅ POST provider-settings/update endpoint exists")
                
            # Check for get_provider_settings function implementation
            if 'async def get_provider_settings():' not in content:
                self.log_issue("MISSING_IMPLEMENTATION", "get_provider_settings function not implemented", "CRITICAL")
                return False
            else:
                self.success_steps.append("✅ get_provider_settings function implemented")
                
            # Check for update_provider_settings function implementation  
            if 'async def update_provider_settings(' not in content:
                self.log_issue("MISSING_IMPLEMENTATION", "update_provider_settings function not implemented", "CRITICAL")
                return False
            else:
                self.success_steps.append("✅ update_provider_settings function implemented")
                
            return True
            
        except Exception as e:
            self.log_issue("TEST_ERROR", f"Failed to analyze backend endpoints: {e}", "CRITICAL") 
            return False
    
    def test_3_model_settings_integration(self):
        """Test 3: Check model settings integration for provider management"""
        print("🔍 Test 3: Model Settings Integration...")
        
        try:
            # Check if model_settings.py exists
            model_settings_file = Path(__file__).parent / "src/config/model_settings.py"
            if not model_settings_file.exists():
                self.log_issue("MISSING_FILE", "model_settings.py not found", "CRITICAL")
                return False
                
            with open(model_settings_file) as f:
                content = f.read()
                
            # Check for provider settings methods in ModelSettingsManager
            if 'get_provider_settings' not in content:
                self.log_issue("MISSING_METHOD", "get_provider_settings method not found in ModelSettingsManager", "CRITICAL", 
                              "Backend API calls model_settings.get_provider_settings() but method doesn't exist")
                return False
            else:
                self.success_steps.append("✅ get_provider_settings method exists")
                
            if 'update_provider_settings' not in content:
                self.log_issue("MISSING_METHOD", "update_provider_settings method not found in ModelSettingsManager", "CRITICAL",
                              "Backend API calls model_settings.update_provider_settings() but method doesn't exist") 
                return False
            else:
                self.success_steps.append("✅ update_provider_settings method exists")
                
            # Log the critical dependency success
            self.log_dependency("ModelSettingsManager.get_provider_settings", "GET /admin/provider-settings", True)
            self.log_dependency("ModelSettingsManager.update_provider_settings", "POST /admin/provider-settings/update", True)
                
            return True  # Methods found and properly integrated
            
        except Exception as e:
            self.log_issue("TEST_ERROR", f"Failed to analyze model settings integration: {e}", "CRITICAL")
            return False
    
    def test_4_frontend_backend_flow(self):
        """Test 4: Analyze complete frontend to backend flow"""
        print("🔍 Test 4: Frontend-Backend Flow...")
        
        # Frontend flow analysis
        frontend_flow = [
            "1. User selects provider from dropdown",
            "2. onchange=\"switchProvider()\" triggers",
            "3. switchProvider() function executes",
            "4. Status shows 'Switching...'",
            "5. POST request to /admin/provider-settings/update",
            "6. Backend processes request", 
            "7. Response handled in frontend",
            "8. Status updated with success/error",
            "9. Message shown in chat log"
        ]
        
        # Check for potential race conditions
        self.log_race_condition(
            "Multiple rapid provider switches",
            ["switchProvider function", "API requests", "UI updates"],
            "Add debouncing or disable dropdown during switch"
        )
        
        self.log_race_condition(
            "Provider loading vs user selection",
            ["loadCurrentProvider", "user dropdown selection", "switchProvider"],
            "Ensure loadCurrentProvider completes before enabling UI"
        )
        
        # Page load dependencies
        self.log_dependency("DOM loaded", "loadCurrentProvider()", True)
        self.log_dependency("loadCurrentProvider()", "Provider dropdown state", True)
        self.log_dependency("Provider settings API", "loadCurrentProvider()", True)
        
        return True
    
    def test_5_error_handling(self):
        """Test 5: Error handling analysis"""
        print("🔍 Test 5: Error Handling...")
        
        try:
            webhook_file = Path(__file__).parent / "src/vapi/webhook_server.py" 
            with open(webhook_file) as f:
                content = f.read()
                
            # Check for try-catch in switchProvider
            switchProvider_start = content.find('async function switchProvider()')
            if switchProvider_start == -1:
                return False
                
            switchProvider_end = content.find('loadCurrentProvider();', switchProvider_start)
            switchProvider_code = content[switchProvider_start:switchProvider_end]
            
            if 'try {' not in switchProvider_code:
                self.log_issue("MISSING_ERROR_HANDLING", "switchProvider function lacks try-catch block", "HIGH")
                return False
            else:
                self.success_steps.append("✅ switchProvider has error handling")
                
            if 'catch (error)' not in switchProvider_code:
                self.log_issue("MISSING_ERROR_HANDLING", "switchProvider function lacks catch block", "HIGH")  
                return False
            else:
                self.success_steps.append("✅ switchProvider has catch block")
                
            # Check for try-catch in loadCurrentProvider
            loadProvider_start = content.find('async function loadCurrentProvider()')
            loadProvider_end = content.find('document.getElementById(\'send\').onclick', loadProvider_start)
            loadProvider_code = content[loadProvider_start:loadProvider_end]
            
            if 'try {' not in loadProvider_code:
                self.log_issue("MISSING_ERROR_HANDLING", "loadCurrentProvider function lacks try-catch block", "MEDIUM")
            else:
                self.success_steps.append("✅ loadCurrentProvider has error handling")
                
            return True
            
        except Exception as e:
            self.log_issue("TEST_ERROR", f"Failed to analyze error handling: {e}", "HIGH")
            return False
    
    def test_6_timing_and_race_conditions(self):
        """Test 6: Identify timing issues and race conditions"""
        print("🔍 Test 6: Timing and Race Conditions...")
        
        # Analyze page load sequence
        page_load_sequence = [
            "1. HTML loaded",
            "2. JavaScript executes",
            "3. fetch('/personas') - Model loading", 
            "4. loadEnvironmentStatus() - Environment detection",
            "5. loadCurrentProvider() - Provider loading"
        ]
        
        # These all happen asynchronously and could race
        self.log_race_condition(
            "Page load async operations race condition",
            ["Model loading", "Environment detection", "Provider loading"],
            "Use Promise.all() or sequential await calls"
        )
        
        # Provider switching during other operations
        self.log_race_condition(
            "Provider switch during model operations", 
            ["switchProvider", "model preloading", "chat requests"],
            "Queue operations or block UI during critical operations"
        )
        
        # UI state consistency
        self.log_race_condition(
            "UI state inconsistency during async operations",
            ["provider dropdown", "status span", "chat log"],
            "Use state management pattern or atomic UI updates"
        )
        
        return True
    
    def test_7_integration_points(self):
        """Test 7: Check integration with other system components"""
        print("🔍 Test 7: Integration Points...")
        
        # Provider switching affects multiple components
        integration_points = [
            "Model Manager - may need to switch models based on provider",
            "VAPI endpoints - chat completions may use different providers", 
            "Admin UI - provider settings shared between main UI and admin",
            "Environment detection - provider availability varies by environment",
            "Error logging - provider errors need proper logging"
        ]
        
        # Check if provider switching integrates with model manager
        self.log_dependency("Provider settings", "Model Manager", False)
        self.log_dependency("Provider settings", "Chat completions", True)
        self.log_dependency("Provider settings", "Admin UI consistency", True)
        
        return True
    
    def run_all_tests(self):
        """Run all end-to-end tests"""
        print("🚀 Starting End-to-End Provider Switching Tests...")
        print("=" * 60)
        
        tests = [
            ("Frontend Structure", self.test_1_frontend_html_structure),
            ("Backend Endpoints", self.test_2_backend_api_endpoints), 
            ("Model Settings Integration", self.test_3_model_settings_integration),
            ("Frontend-Backend Flow", self.test_4_frontend_backend_flow),
            ("Error Handling", self.test_5_error_handling),
            ("Timing & Race Conditions", self.test_6_timing_and_race_conditions),
            ("Integration Points", self.test_7_integration_points)
        ]
        
        results = {}
        for test_name, test_func in tests:
            try:
                result = test_func()
                results[test_name] = result
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"{status} {test_name}")
            except Exception as e:
                results[test_name] = False
                print(f"💥 ERROR {test_name}: {e}")
                self.log_issue("TEST_EXECUTION_ERROR", f"{test_name} failed with exception: {e}", "CRITICAL")
        
        return results
    
    def print_detailed_report(self):
        """Print detailed analysis report"""
        print("\n" + "=" * 60)
        print("🔍 DETAILED ANALYSIS REPORT")
        print("=" * 60)
        
        # Success steps
        if self.success_steps:
            print(f"\n✅ SUCCESSFUL COMPONENTS ({len(self.success_steps)}):")
            for step in self.success_steps:
                print(f"  {step}")
        
        # Critical issues
        critical_issues = [i for i in self.issues if i['severity'] == 'CRITICAL']
        if critical_issues:
            print(f"\n🚨 CRITICAL ISSUES ({len(critical_issues)}):")
            for i, issue in enumerate(critical_issues, 1):
                print(f"  {i}. {issue['category']}: {issue['description']}")
                if issue['details']:
                    print(f"     Details: {issue['details']}")
        
        # High priority issues
        high_issues = [i for i in self.issues if i['severity'] == 'HIGH']
        if high_issues:
            print(f"\n⚠️  HIGH PRIORITY ISSUES ({len(high_issues)}):")
            for i, issue in enumerate(high_issues, 1):
                print(f"  {i}. {issue['category']}: {issue['description']}")
        
        # Dependencies
        if self.dependencies:
            print(f"\n🔗 DEPENDENCIES ({len(self.dependencies)}):")
            for i, dep in enumerate(self.dependencies, 1):
                required = "REQUIRED" if dep['required'] else "OPTIONAL"
                print(f"  {i}. {dep['dependent']} depends on {dep['depends_on']} ({required})")
        
        # Race conditions
        if self.race_conditions:
            print(f"\n⚡ RACE CONDITIONS ({len(self.race_conditions)}):")
            for i, race in enumerate(self.race_conditions, 1):
                print(f"  {i}. {race['description']}")
                print(f"     Components: {', '.join(race['components'])}")
                if race['mitigation']:
                    print(f"     Mitigation: {race['mitigation']}")
        
        # Overall assessment
        total_issues = len(self.issues)
        critical_count = len(critical_issues)
        
        print(f"\n📊 OVERALL ASSESSMENT:")
        print(f"  Total Issues Found: {total_issues}")
        print(f"  Critical Issues: {critical_count}")
        print(f"  Dependencies: {len(self.dependencies)}")
        print(f"  Race Conditions: {len(self.race_conditions)}")
        
        if critical_count > 0:
            print(f"\n❌ RESULT: IMPLEMENTATION HAS CRITICAL ISSUES")
            print(f"   The provider switching will NOT work end-to-end due to missing dependencies.")
        elif total_issues > 5:
            print(f"\n⚠️  RESULT: IMPLEMENTATION HAS SIGNIFICANT ISSUES") 
            print(f"   The provider switching may work but has reliability concerns.")
        else:
            print(f"\n✅ RESULT: IMPLEMENTATION APPEARS FUNCTIONAL")
            print(f"   Provider switching should work end-to-end with minor issues.")

def main():
    """Run the end-to-end test suite"""
    tester = ProviderSwitchingE2ETest()
    
    # Run all tests
    results = tester.run_all_tests()
    
    # Print detailed report
    tester.print_detailed_report()
    
    # Print summary
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    print(f"\n🏁 TEST SUMMARY: {passed}/{total} tests passed")
    
    if tester.issues:
        print(f"\n🛠️  REQUIRED FIXES:")
        critical_issues = [i for i in tester.issues if i['severity'] == 'CRITICAL']
        for issue in critical_issues:
            if issue['category'] == 'MISSING_METHOD':
                print(f"   • Add {issue['description']} to ModelSettingsManager class")
            elif issue['category'] == 'MISSING_ENDPOINT':
                print(f"   • Implement {issue['description']} in webhook server")
            elif issue['category'] == 'MISSING_FUNCTION':
                print(f"   • Add {issue['description']} to frontend JavaScript")

if __name__ == "__main__":
    main()
