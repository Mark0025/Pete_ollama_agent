#!/usr/bin/env python3
"""
Manual Jamie Model Testing with Longer Timeouts
"""

import subprocess
import sys

def test_jamie_model(model_name: str = "peteollama:jamie-working-working_20250806"):
    """Test Jamie model with longer timeout for local testing"""
    
    test_cases = [
        "My AC stopped working",
        "When is rent due?", 
        "My toilet is leaking",
        "The garbage disposal is broken",
        "My neighbor is too loud"
    ]
    
    print(f"🧪 Testing Jamie Model: {model_name}")
    print("=" * 60)
    print("⏰ Using 2-minute timeout for local testing")
    print()
    
    for i, test in enumerate(test_cases, 1):
        print(f"🔍 TEST {i}: {test}")
        print("-" * 40)
        
        try:
            # Increase timeout to 2 minutes for local testing
            result = subprocess.run([
                "ollama", "run", model_name, test
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                response = result.stdout.strip()
                print(f"Jamie: {response}")
                
                # Analyze response quality
                print(f"\n📊 Analysis:")
                print(f"   Length: {len(response)} characters")
                
                # Check for good patterns
                good_patterns = ["I'll", "I'm", "contact", "call", "schedule", "send"]
                bad_patterns = ["conversation", "back and forth", "what would you like", "how can I help"]
                
                good_found = [p for p in good_patterns if p.lower() in response.lower()]
                bad_found = [p for p in bad_patterns if p.lower() in response.lower()]
                
                if good_found:
                    print(f"   ✅ Good patterns: {good_found}")
                if bad_found:
                    print(f"   ⚠️  Concerning patterns: {bad_found}")
                
                if len(response) > 50 and good_found and not bad_found:
                    print("   🎯 EXCELLENT RESPONSE!")
                elif len(response) > 30:
                    print("   👍 Good response")
                else:
                    print("   ⚠️  Response might be too short")
                    
            else:
                print(f"❌ Error: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print("⏰ Response timed out after 2 minutes")
        except Exception as e:
            print(f"❌ Test failed: {e}")
        
        print("\n" + "="*60 + "\n")

def quick_test(question: str = "My AC is broken"):
    """Quick single test"""
    model_name = "peteollama:jamie-working-working_20250806"
    print(f"🚀 Quick test: {question}")
    print(f"Model: {model_name}")
    print("-" * 40)
    
    try:
        result = subprocess.run([
            "ollama", "run", model_name, question
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            response = result.stdout.strip()
            print(f"Jamie: {response}")
            return response
        else:
            print(f"❌ Error: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Quick test with custom question
        question = " ".join(sys.argv[1:])
        quick_test(question)
    else:
        # Full test suite
        test_jamie_model()