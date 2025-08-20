#!/usr/bin/env python3
"""
Ollama Agent System Analysis
============================

Uses the whatsWorking framework to analyze our system configuration
and identify exactly what's working and what's not.
"""

import sys
import os
from pathlib import Path

# Import whatsWorking analysis framework
sys.path.insert(0, '/Users/markcarpenter/Desktop/whatsWorking')
from whatsWorking import ServerlessStatus

class OllamaAgentAnalyzer(ServerlessStatus):
    """Analyze the Ollama Agent system configuration"""
    
    def __init__(self):
        super().__init__()
        self.project_path = Path(__file__).parent.parent
        self.status["project"] = "Ollama Agent System Configuration"
        self.status["version"] = "1.0.0"
    
    def check_system_config(self) -> dict:
        """Check our new system configuration system"""
        print("🔍 Checking System Configuration...")
        
        config_status = {
            "system_config_exists": False,
            "system_config_ui_accessible": False,
            "api_endpoints_working": False,
            "config_persistence": False,
            "integration_with_modelmanager": False
        }
        
        try:
            # Check if system config file exists
            config_file = self.project_path / "config" / "system_config.json"
            config_status["system_config_exists"] = config_file.exists()
            
            if config_status["system_config_exists"]:
                print(f"   ✅ System config file: {config_file}")
                
                # Check if UI is accessible
                import requests
                try:
                    response = requests.get("http://localhost:8000/admin/system-config", timeout=5)
                    config_status["system_config_ui_accessible"] = response.status_code == 200
                    print(f"   ✅ System config UI: {'Accessible' if config_status['system_config_ui_accessible'] else 'Not accessible'}")
                except:
                    print("   ❌ System config UI: Not accessible (server not running)")
                
                # Check API endpoints
                try:
                    response = requests.get("http://localhost:8000/admin/system-config/", timeout=5)
                    config_status["api_endpoints_working"] = response.status_code == 200
                    print(f"   ✅ API endpoints: {'Working' if config_status['api_endpoints_working'] else 'Not working'}")
                except:
                    print("   ❌ API endpoints: Not accessible (server not running)")
                
                # Check config persistence
                try:
                    from config.system_config import system_config
                    original_threshold = system_config.config.global_caching.threshold
                    system_config.config.global_caching.threshold = 0.99
                    system_config.save_config()
                    
                    # Reload to test persistence
                    new_system_config = system_config.__class__(system_config.config_file)
                    new_threshold = new_system_config.config.global_caching.threshold
                    
                    config_status["config_persistence"] = abs(new_threshold - 0.99) < 0.01
                    print(f"   ✅ Config persistence: {'Working' if config_status['config_persistence'] else 'Not working'}")
                    
                    # Restore original
                    system_config.config.global_caching.threshold = original_threshold
                    system_config.save_config()
                    
                except Exception as e:
                    print(f"   ❌ Config persistence test failed: {e}")
                
                # Check integration with ModelManager
                try:
                    from ai.model_manager import ModelManager
                    from config.system_config import system_config
                    
                    mm = ModelManager()
                    config_threshold = system_config.get_caching_config().threshold
                    mm_threshold = mm.similarity_threshold
                    
                    config_status["integration_with_modelmanager"] = abs(config_threshold - mm_threshold) < 0.01
                    print(f"   ✅ Integration with ModelManager: {'Working' if config_status['integration_with_modelmanager'] else 'NOT WORKING'}")
                    print(f"      Config threshold: {config_threshold}")
                    print(f"      ModelManager threshold: {mm_threshold}")
                    
                except Exception as e:
                    print(f"   ❌ ModelManager integration test failed: {e}")
            
            else:
                print(f"   ❌ System config file not found: {config_file}")
                
        except Exception as e:
            print(f"   ❌ System config check failed: {e}")
        
        return {
            "status": "✅ Working" if all(config_status.values()) else "❌ Broken",
            "details": config_status
        }
    
    def check_provider_routing(self) -> dict:
        """Check if provider routing actually works"""
        print("🔍 Checking Provider Routing...")
        
        routing_status = {
            "openrouter_available": False,
            "runpod_available": False,
            "ollama_available": False,
            "provider_switching_works": False
        }
        
        try:
            from ai.model_manager import ModelManager
            mm = ModelManager()
            
            # Check provider availability
            try:
                openrouter_handler = mm._get_openrouter_handler()
                routing_status["openrouter_available"] = openrouter_handler and openrouter_handler.available
                print(f"   ✅ OpenRouter: {'Available' if routing_status['openrouter_available'] else 'Not available'}")
            except:
                print("   ❌ OpenRouter: Not available")
            
            try:
                if hasattr(mm, 'pete_handler') and mm.pete_handler:
                    routing_status["runpod_available"] = True
                    print("   ✅ RunPod: Available")
                else:
                    print("   ❌ RunPod: Not available")
            except:
                print("   ❌ RunPod: Not available")
            
            try:
                routing_status["ollama_available"] = mm.is_available()
                print(f"   ✅ Ollama: {'Available' if routing_status['ollama_available'] else 'Not available'}")
            except:
                print("   ❌ Ollama: Not available")
            
            # Test provider switching
            try:
                from config.system_config import system_config
                
                # Switch to RunPod
                original_provider = system_config.config.default_provider
                system_config.update_provider_config("runpod", enabled=True, priority=1)
                
                # Check if ModelManager picks up the change
                current_provider = mm._get_current_provider()
                routing_status["provider_switching_works"] = current_provider == "runpod"
                
                print(f"   ✅ Provider switching: {'Working' if routing_status['provider_switching_works'] else 'NOT WORKING'}")
                print(f"      Config default: runpod")
                print(f"      ModelManager current: {current_provider}")
                
                # Restore original
                system_config.update_provider_config("runpod", enabled=True, priority=2)
                
            except Exception as e:
                print(f"   ❌ Provider switching test failed: {e}")
                
        except Exception as e:
            print(f"   ❌ Provider routing check failed: {e}")
        
        return {
            "status": "✅ Working" if all(routing_status.values()) else "❌ Broken",
            "details": routing_status
        }
    
    def check_caching_behavior(self) -> dict:
        """Check if caching configuration actually affects behavior"""
        print("🔍 Checking Caching Behavior...")
        
        caching_status = {
            "similarity_analyzer_available": False,
            "response_cache_available": False,
            "caching_respects_config": False,
            "threshold_changes_work": False
        }
        
        try:
            from ai.model_manager import ModelManager
            from config.system_config import system_config
            
            mm = ModelManager()
            
            # Check if similarity analyzer is available
            try:
                analyzer = mm._get_similarity_analyzer()
                caching_status["similarity_analyzer_available"] = analyzer is not None
                print(f"   ✅ Similarity analyzer: {'Available' if caching_status['similarity_analyzer_available'] else 'Not available'}")
            except:
                print("   ❌ Similarity analyzer: Not available")
            
            # Check if response cache is available
            try:
                from ai.response_cache import ResponseCache
                cache = ResponseCache()
                caching_status["response_cache_available"] = True
                print("   ✅ Response cache: Available")
            except:
                print("   ❌ Response cache: Not available")
            
            # Check if caching respects configuration
            try:
                # Get current config
                config_threshold = system_config.get_caching_config().threshold
                mm_threshold = mm.similarity_threshold
                
                caching_status["caching_respects_config"] = abs(config_threshold - mm_threshold) < 0.01
                print(f"   ✅ Caching respects config: {'Yes' if caching_status['caching_respects_config'] else 'NO'}")
                print(f"      Config threshold: {config_threshold}")
                print(f"      ModelManager threshold: {mm_threshold}")
                
            except Exception as e:
                print(f"   ❌ Caching config check failed: {e}")
            
            # Test if threshold changes actually work
            try:
                original_threshold = mm.similarity_threshold
                
                # Change config
                system_config.config.global_caching.threshold = 0.99
                system_config.save_config()
                
                # Check if ModelManager picked it up
                new_threshold = system_config.get_caching_config().threshold
                caching_status["threshold_changes_work"] = abs(new_threshold - 0.99) < 0.01
                
                print(f"   ✅ Threshold changes work: {'Yes' if caching_status['threshold_changes_work'] else 'NO'}")
                print(f"      Changed to: 0.99")
                print(f"      Actual: {new_threshold}")
                
                # Restore original
                system_config.config.global_caching.threshold = original_threshold
                system_config.save_config()
                
            except Exception as e:
                print(f"   ❌ Threshold change test failed: {e}")
                
        except Exception as e:
            print(f"   ❌ Caching behavior check failed: {e}")
        
        return {
            "status": "✅ Working" if all(caching_status.values()) else "❌ Broken",
            "details": caching_status
        }
    
    def run_full_analysis(self):
        """Run the complete analysis"""
        print("🚀 Ollama Agent System Configuration Analysis")
        print("=" * 60)
        
        # Run all checks
        checks = [
            ("System Configuration", self.check_system_config),
            ("Provider Routing", self.check_provider_routing),
            ("Caching Behavior", self.check_caching_behavior),
            ("Environment", self.check_environment),
            ("Files", self.check_files),
            ("API Structure", self.check_api_structure)
        ]
        
        results = {}
        for check_name, check_func in checks:
            try:
                results[check_name] = check_func()
            except Exception as e:
                results[check_name] = {
                    "status": f"❌ Error: {e}",
                    "details": {}
                }
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 ANALYSIS SUMMARY")
        print("=" * 60)
        
        working_checks = 0
        total_checks = len(results)
        
        for check_name, result in results.items():
            status = result["status"]
            if "✅" in status:
                working_checks += 1
            print(f"{status} {check_name}")
        
        print(f"\n🎯 Overall: {working_checks}/{total_checks} systems working ({working_checks/total_checks*100:.1f}%)")
        
        if working_checks == total_checks:
            print("🎉 All systems are working perfectly!")
        else:
            print("⚠️ Some systems need attention.")
        
        return results

if __name__ == "__main__":
    analyzer = OllamaAgentAnalyzer()
    results = analyzer.run_full_analysis()
