#!/usr/bin/env python3
"""
Provider Comparison Test Script
Compare response quality and truncation between RunPod and OpenRouter
Test identical messages with multiple models to isolate issues
"""

import json
import time
from typing import Dict, List, Any
from model_router import model_router


def test_truncation_scenarios() -> Dict[str, Any]:
    """Test various message lengths to identify truncation thresholds"""
    
    test_scenarios = [
        {
            "name": "Short Message",
            "message": "Hi, my tenant says the heating isn't working. What should I do?",
            "expected_length": "short"
        },
        {
            "name": "Medium Message", 
            "message": "Hello, I'm Mark, a property manager. I have a situation where my tenant at 123 Main Street has contacted me about several issues: the heating system isn't working properly, there's a leak in the bathroom ceiling, and the kitchen garbage disposal is making strange noises. They're asking for urgent repairs and want to know what their rights are if these issues aren't fixed quickly. Can you help me understand the proper steps to take and provide guidance on how to respond professionally while ensuring we meet all legal requirements?",
            "expected_length": "medium"
        },
        {
            "name": "Long Message",
            "message": "Hello, I'm Mark, a property manager dealing with a complex situation. I manage multiple rental properties in the downtown area, and I'm facing several challenging issues that require detailed guidance. Here's the full situation: At property #1 (123 Main Street), the tenant has reported multiple maintenance issues including a non-functioning heating system that hasn't worked for three days during winter, a significant water leak in the bathroom ceiling that's causing damage to the unit below, and a malfunctioning garbage disposal that's creating terrible odors throughout the kitchen area. The tenant is understandably frustrated and has mentioned they might withhold rent if these issues aren't resolved immediately. At property #2 (456 Oak Avenue), I have a different tenant who has consistently paid rent late for the past four months, and they're now two months behind. They claim financial hardship due to job loss but haven't provided any documentation. I need to understand the legal eviction process while being compassionate to their situation. At property #3 (789 Pine Road), there's a dispute between upstairs and downstairs tenants about noise complaints, with both sides threatening to break their leases early. The upstairs tenant works night shifts and needs to sleep during the day, while the downstairs tenant has young children who play during normal hours. I need comprehensive advice on how to handle all these situations professionally, legally, and efficiently while maintaining good tenant relationships and protecting my clients' investments. What are the step-by-step processes I should follow for each scenario, and what documentation should I maintain throughout these processes?",
            "expected_length": "long"
        }
    ]
    
    results = {}
    
    print("🧪 Testing Truncation Scenarios")
    print("=" * 60)
    
    for scenario in test_scenarios:
        scenario_name = scenario["name"]
        message = scenario["message"]
        message_length = len(message)
        
        print(f"\n📝 Testing {scenario_name} ({message_length} chars)")
        print(f"💬 Message preview: {message[:100]}...")
        
        scenario_results = {}
        
        # Test with different models and providers
        test_configs = [
            {"provider": "openrouter", "model": "meta-llama/llama-3.1-8b-instruct:free", "max_tokens": 500},
            {"provider": "openrouter", "model": "openai/gpt-3.5-turbo", "max_tokens": 500},
            {"provider": "runpod", "model": "peteollama:jamie-fixed", "max_tokens": 500},
            {"provider": "ollama", "model": "peteollama:jamie-fixed", "max_tokens": 500}
        ]
        
        for config in test_configs:
            provider = config["provider"]
            model = config["model"]
            max_tokens = config["max_tokens"]
            
            # Skip if provider not available
            if not model_router.provider_status.get(provider, False):
                print(f"  ⚠️ Skipping {provider} - not available")
                continue
            
            print(f"\n  🔬 Testing {provider} ({model})")
            
            try:
                start_time = time.time()
                
                result = model_router.route_chat_completion(
                    message=message,
                    model=model,
                    provider=provider,
                    max_tokens=max_tokens,
                    temperature=0.7
                )
                
                end_time = time.time()
                duration = end_time - start_time
                
                if result.get('status') == 'success':
                    response = result['response']
                    response_length = len(response)
                    was_truncated = result.get('was_truncated', False)
                    finish_reason = result.get('finish_reason', 'unknown')
                    
                    print(f"    ✅ Success - {response_length} chars in {duration:.2f}s")
                    print(f"    🏁 Finish reason: {finish_reason}")
                    if was_truncated:
                        print(f"    ⚠️ Response was truncated!")
                    
                    # Analyze response quality
                    quality_score = analyze_response_quality(response, scenario_name)
                    print(f"    📊 Quality score: {quality_score}/10")
                    
                    scenario_results[f"{provider}_{model}"] = {
                        "status": "success",
                        "response_length": response_length,
                        "duration": duration,
                        "was_truncated": was_truncated,
                        "finish_reason": finish_reason,
                        "quality_score": quality_score,
                        "response_preview": response[:200] + "..." if len(response) > 200 else response
                    }
                    
                else:
                    error = result.get('error', 'Unknown error')
                    print(f"    ❌ Failed: {error}")
                    
                    scenario_results[f"{provider}_{model}"] = {
                        "status": "error",
                        "error": error,
                        "duration": duration
                    }
                
                # Small delay between requests
                time.sleep(1)
                
            except Exception as e:
                print(f"    ❌ Exception: {e}")
                scenario_results[f"{provider}_{model}"] = {
                    "status": "exception",
                    "error": str(e)
                }
        
        results[scenario_name] = {
            "message_length": message_length,
            "message": message,
            "results": scenario_results
        }
    
    return results


def analyze_response_quality(response: str, scenario_type: str) -> int:
    """Analyze response quality on a scale of 1-10"""
    
    score = 5  # Base score
    
    # Length analysis
    if len(response) < 50:
        score -= 3  # Too short
    elif len(response) > 100:
        score += 1  # Good length
    
    # Content analysis (basic keyword matching)
    property_keywords = ["tenant", "property", "maintenance", "repair", "lease", "rent"]
    helpful_keywords = ["should", "recommend", "steps", "process", "contact", "document"]
    professional_keywords = ["professional", "legal", "rights", "obligations", "code"]
    
    keyword_score = 0
    for keyword in property_keywords:
        if keyword.lower() in response.lower():
            keyword_score += 1
    
    for keyword in helpful_keywords:
        if keyword.lower() in response.lower():
            keyword_score += 1
    
    for keyword in professional_keywords:
        if keyword.lower() in response.lower():
            keyword_score += 1
    
    score += min(keyword_score // 2, 3)  # Max 3 points for keywords
    
    # Completeness analysis
    if response.endswith(('.', '!', '?')):
        score += 1  # Complete sentences
    
    if len(response.split('. ')) >= 3:
        score += 1  # Multiple sentences
    
    return min(max(score, 1), 10)  # Clamp between 1-10


def test_vapi_webhook_comparison() -> Dict[str, Any]:
    """Test VAPI webhook responses across providers"""
    
    print("\n📞 Testing VAPI Webhook Comparison")
    print("=" * 50)
    
    vapi_test_messages = [
        "My toilet is leaking water everywhere! This is an emergency!",
        "The heat isn't working in my apartment and it's really cold.",
        "Hi Jamie, I wanted to let you know that my rent payment might be a few days late this month due to a bank issue.",
        "I'm interested in renting one of your properties. Can you tell me about availability and pricing?"
    ]
    
    results = {}
    
    for i, message in enumerate(vapi_test_messages):
        test_name = f"VAPI_Test_{i+1}"
        print(f"\n📞 {test_name}: {message}")
        
        webhook_data = {
            "message": message,
            "call_id": f"test-{i+1}-{int(time.time())}"
        }
        
        test_results = {}
        
        # Test each available provider
        for provider in ['openrouter', 'runpod', 'ollama']:
            if not model_router.provider_status.get(provider, False):
                print(f"  ⚠️ Skipping {provider} - not available")
                continue
            
            print(f"  🔬 Testing {provider}")
            
            try:
                start_time = time.time()
                
                # Force provider by adding model hint to webhook data
                if provider == 'openrouter':
                    webhook_data['model'] = 'meta-llama/llama-3.1-8b-instruct:free'
                else:
                    webhook_data['model'] = 'peteollama:jamie-fixed'
                
                result = model_router.route_vapi_webhook(webhook_data)
                
                end_time = time.time()
                duration = end_time - start_time
                
                if result.get('status') == 'success':
                    response = result['response']
                    response_length = len(response)
                    
                    print(f"    ✅ Success - {response_length} chars in {duration:.2f}s")
                    print(f"    📄 Response: {response[:100]}{'...' if len(response) > 100 else ''}")
                    
                    test_results[provider] = {
                        "status": "success",
                        "response_length": response_length,
                        "duration": duration,
                        "response": response
                    }
                    
                else:
                    error = result.get('error', 'Unknown error')
                    print(f"    ❌ Failed: {error}")
                    
                    test_results[provider] = {
                        "status": "error",
                        "error": error,
                        "duration": duration
                    }
                
                time.sleep(0.5)  # Brief delay
                
            except Exception as e:
                print(f"    ❌ Exception: {e}")
                test_results[provider] = {
                    "status": "exception",
                    "error": str(e)
                }
        
        results[test_name] = {
            "message": message,
            "results": test_results
        }
    
    return results


def generate_comparison_report(truncation_results: Dict[str, Any], vapi_results: Dict[str, Any]):
    """Generate a comprehensive comparison report"""
    
    print("\n📊 PROVIDER COMPARISON REPORT")
    print("=" * 60)
    
    # Summary stats
    total_tests = 0
    successful_tests = {"openrouter": 0, "runpod": 0, "ollama": 0}
    truncation_issues = {"openrouter": 0, "runpod": 0, "ollama": 0}
    avg_response_length = {"openrouter": [], "runpod": [], "ollama": []}
    avg_duration = {"openrouter": [], "runpod": [], "ollama": []}
    
    # Analyze truncation test results
    print("\\n🔍 Truncation Analysis:")
    
    for scenario_name, scenario_data in truncation_results.items():
        print(f"\\n  📝 {scenario_name} ({scenario_data['message_length']} chars):")
        
        for test_key, test_result in scenario_data['results'].items():
            provider = test_key.split('_')[0]
            total_tests += 1
            
            if test_result.get('status') == 'success':
                successful_tests[provider] += 1
                
                response_length = test_result.get('response_length', 0)
                duration = test_result.get('duration', 0)
                was_truncated = test_result.get('was_truncated', False)
                
                avg_response_length[provider].append(response_length)
                avg_duration[provider].append(duration)
                
                if was_truncated:
                    truncation_issues[provider] += 1
                    print(f"    ⚠️ {provider}: TRUNCATED ({response_length} chars)")
                else:
                    print(f"    ✅ {provider}: Complete ({response_length} chars)")
            else:
                print(f"    ❌ {provider}: Failed - {test_result.get('error', 'Unknown error')}")
    
    # Calculate averages
    print("\\n📈 Performance Metrics:")
    
    for provider in successful_tests.keys():
        if successful_tests[provider] > 0:
            avg_length = sum(avg_response_length[provider]) / len(avg_response_length[provider])
            avg_time = sum(avg_duration[provider]) / len(avg_duration[provider])
            success_rate = (successful_tests[provider] / total_tests) * 100 if total_tests > 0 else 0
            truncation_rate = (truncation_issues[provider] / successful_tests[provider]) * 100 if successful_tests[provider] > 0 else 0
            
            print(f"\\n  🏠 {provider.upper()}:")
            print(f"    ✅ Success rate: {success_rate:.1f}%")
            print(f"    📏 Avg response length: {avg_length:.0f} chars")
            print(f"    ⏱️ Avg response time: {avg_time:.2f}s")
            print(f"    ⚠️ Truncation rate: {truncation_rate:.1f}%")
    
    # VAPI Analysis
    print("\\n📞 VAPI Webhook Analysis:")
    
    for test_name, test_data in vapi_results.items():
        print(f"\\n  📞 {test_name}:")
        print(f"    💬 Message: {test_data['message'][:60]}...")
        
        for provider, result in test_data['results'].items():
            if result.get('status') == 'success':
                length = result.get('response_length', 0)
                duration = result.get('duration', 0)
                print(f"    ✅ {provider}: {length} chars in {duration:.2f}s")
            else:
                print(f"    ❌ {provider}: {result.get('error', 'Failed')}")
    
    # Recommendations
    print("\\n🎯 RECOMMENDATIONS:")
    
    # Find best performing provider for each metric
    best_success_rate = max(successful_tests.items(), key=lambda x: x[1])
    print(f"\\n  🏆 Best Success Rate: {best_success_rate[0]} ({((best_success_rate[1] / total_tests) * 100):.1f}%)")
    
    # Find provider with least truncation
    least_truncation = min(truncation_issues.items(), key=lambda x: x[1])
    print(f"  🎯 Least Truncation: {least_truncation[0]} ({least_truncation[1]} truncated responses)")
    
    # Check for RunPod specific issues
    runpod_truncation_rate = (truncation_issues.get('runpod', 0) / max(successful_tests.get('runpod', 1), 1)) * 100
    openrouter_truncation_rate = (truncation_issues.get('openrouter', 0) / max(successful_tests.get('openrouter', 1), 1)) * 100
    
    if runpod_truncation_rate > openrouter_truncation_rate:
        print(f"\\n  🚨 ISSUE DETECTED: RunPod shows {runpod_truncation_rate:.1f}% truncation rate vs OpenRouter's {openrouter_truncation_rate:.1f}%")
        print(f"     💡 Consider using OpenRouter as primary provider for longer responses")
    
    print(f"\\n  🔧 Configuration Suggestions:")
    print(f"     • Set fallback_provider to the most reliable provider")
    print(f"     • Use OpenRouter for testing and comparison")
    print(f"     • Monitor response lengths in production")
    print(f"     • Implement response length alerts")


def main():
    """Run the complete provider comparison test"""
    
    print("🚀 Starting Provider Comparison Test")
    print("Testing RunPod vs OpenRouter for truncation issues")
    print("=" * 60)
    
    # Check available providers
    print(f"\\n📊 Available Providers:")
    for provider, status in model_router.provider_status.items():
        status_emoji = "✅" if status else "❌"
        print(f"  {status_emoji} {provider}")
    
    # Run truncation tests
    print(f"\\n🧪 Running truncation scenario tests...")
    truncation_results = test_truncation_scenarios()
    
    # Run VAPI webhook tests
    print(f"\\n📞 Running VAPI webhook tests...")
    vapi_results = test_vapi_webhook_comparison()
    
    # Generate comprehensive report
    generate_comparison_report(truncation_results, vapi_results)
    
    # Save results to file
    timestamp = int(time.time())
    report_file = f"provider_comparison_report_{timestamp}.json"
    
    full_results = {
        "timestamp": timestamp,
        "provider_status": model_router.provider_status,
        "truncation_tests": truncation_results,
        "vapi_tests": vapi_results
    }
    
    try:
        with open(report_file, 'w') as f:
            json.dump(full_results, f, indent=2)
        print(f"\\n💾 Results saved to: {report_file}")
    except Exception as e:
        print(f"\\n⚠️ Could not save results file: {e}")
    
    print(f"\\n✅ Provider comparison test complete!")


if __name__ == "__main__":
    main()
