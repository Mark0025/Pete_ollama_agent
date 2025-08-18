#!/usr/bin/env python3
"""
Test Suite Generator
===================

Uses the existing conversation similarity system to:
1. Extract all questions and their frequencies from the loaded conversation data
2. Create comprehensive test cases based on working similarity system
3. Generate performance benchmarks for the ModelManager

This builds on the existing working codebase rather than duplicating functionality.
"""

import sys
import json
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Tuple

# Add src to path for imports
sys.path.insert(0, 'src')

try:
    from analytics.conversation_similarity import ConversationSimilarityAnalyzer
except ImportError:
    print("❌ Could not import ConversationSimilarityAnalyzer")
    sys.exit(1)

def extract_questions_from_similarity_system() -> Dict:
    """Extract questions and frequencies from the existing similarity system"""
    
    print("🧠 Loading existing conversation similarity system...")
    
    try:
        analyzer = ConversationSimilarityAnalyzer()
        print(f"✅ Loaded {len(analyzer.conversation_samples)} conversation samples")
    except Exception as e:
        print(f"❌ Error loading similarity analyzer: {e}")
        return {}
    
    # Extract all user messages (questions) from conversation samples
    all_questions = []
    question_responses = defaultdict(list)
    question_contexts = defaultdict(list)
    
    print("🔍 Analyzing conversation samples...")
    
    for sample in analyzer.conversation_samples:
        user_message = sample.user_message.strip()
        agent_response = sample.agent_response.strip()
        
        # Store the question and its response
        if len(user_message) > 10:  # Filter very short messages
            all_questions.append(user_message)
            question_responses[user_message].append(agent_response)
            
            # Store additional context
            context = {
                'user_message': user_message,
                'agent_response': agent_response,
                'metadata': getattr(sample, 'metadata', {})
            }
            question_contexts[user_message].append(context)
    
    # Count frequencies
    question_counter = Counter(all_questions)
    
    print(f"📊 Found {len(all_questions)} total questions")
    print(f"📝 Found {len(question_counter)} unique questions")
    
    # Categorize questions
    categories = categorize_questions(question_counter.keys())
    
    results = {
        'total_questions': len(all_questions),
        'unique_questions': len(question_counter),
        'question_frequencies': dict(question_counter.most_common()),
        'question_responses': dict(question_responses),
        'question_contexts': dict(question_contexts),
        'categories': categories,
        'top_20_questions': question_counter.most_common(20),
        'analyzer_stats': {
            'total_samples': len(analyzer.conversation_samples),
            'vector_store_docs': getattr(analyzer.vector_store, '_collection', {}).get('count', 'Unknown') if hasattr(analyzer, 'vector_store') else 'Unknown'
        }
    }
    
    return results

def categorize_questions(questions: List[str]) -> Dict[str, List[str]]:
    """Categorize questions by topic using property management categories"""
    
    categories = defaultdict(list)
    
    for question in questions:
        question_lower = question.lower()
        
        # Property management categories
        if any(word in question_lower for word in ['rent', 'payment', 'pay', 'due', 'late', 'fee']):
            categories['Rent & Payments'].append(question)
        elif any(word in question_lower for word in ['maintenance', 'repair', 'fix', 'broken', 'leak', 'heat', 'ac', 'air']):
            categories['Maintenance & Repairs'].append(question)
        elif any(word in question_lower for word in ['lease', 'contract', 'agreement', 'term', 'renewal', 'sign']):
            categories['Lease & Legal'].append(question)
        elif any(word in question_lower for word in ['pet', 'dog', 'cat', 'animal']):
            categories['Pet Policy'].append(question)
        elif any(word in question_lower for word in ['park', 'parking', 'garage', 'spot', 'car']):
            categories['Parking'].append(question)
        elif any(word in question_lower for word in ['office', 'hour', 'time', 'open', 'close', 'contact', 'phone']):
            categories['Office & Contact'].append(question)
        elif any(word in question_lower for word in ['move', 'moving', 'moveout', 'evict', 'notice', 'leave']):
            categories['Moving & Notices'].append(question)
        elif any(word in question_lower for word in ['util', 'electric', 'water', 'gas', 'internet', 'cable']):
            categories['Utilities'].append(question)
        elif any(word in question_lower for word in ['neighbor', 'noise', 'complaint', 'issue', 'problem']):
            categories['Tenant Issues'].append(question)
        else:
            categories['General'].append(question)
    
    return dict(categories)

def create_test_cases(question_data: Dict, min_frequency: int = 2) -> List[Dict]:
    """Create test cases from question analysis"""
    
    test_cases = []
    
    # Create test cases for frequent questions
    for question, frequency in question_data['question_frequencies'].items():
        if frequency >= min_frequency:
            
            # Get category
            category = 'General'
            for cat, questions in question_data['categories'].items():
                if question in questions:
                    category = cat
                    break
            
            # Get sample responses
            responses = question_data['question_responses'].get(question, [])
            sample_responses = []
            
            for response in responses[:3]:  # Up to 3 sample responses
                if response:
                    # Truncate long responses
                    if len(response) > 150:
                        sample_responses.append(response[:150] + '...')
                    else:
                        sample_responses.append(response)
            
            test_case = {
                'question': question,
                'frequency': frequency,
                'category': category,
                'sample_responses': sample_responses,
                'expected_similarity_threshold': 0.75 if frequency >= 5 else 0.70,  # Higher threshold for common questions
                'test_variations': generate_question_variations(question)
            }
            
            test_cases.append(test_case)
    
    # Sort by frequency (most common first)
    test_cases.sort(key=lambda x: x['frequency'], reverse=True)
    
    return test_cases

def generate_question_variations(question: str) -> List[str]:
    """Generate variations of a question for testing"""
    
    variations = []
    original = question.lower().rstrip('?')
    
    # Add different phrasings
    if 'when is' in original:
        variations.extend([
            original.replace('when is', 'when will') + '?',
            original.replace('when is', 'what day is') + '?'
        ])
    
    if 'what are' in original:
        variations.extend([
            original.replace('what are', 'what is') + '?',
            original.replace('what are', 'can you tell me') + '?'
        ])
    
    if 'how do i' in original:
        variations.extend([
            original.replace('how do i', 'how can i') + '?',
            original.replace('how do i', 'what is the process to') + '?'
        ])
    
    if 'can i' in original:
        variations.extend([
            original.replace('can i', 'am i able to') + '?',
            original.replace('can i', 'is it possible to') + '?'
        ])
    
    # Remove duplicates and return
    return list(set(variations))

def create_performance_test_suite(test_cases: List[Dict]) -> Dict:
    """Create performance test suite for the ModelManager"""
    
    # Select different categories of tests
    performance_tests = {
        'instant_response_tests': [],  # Should hit similarity cache
        'fallback_tests': [],         # Should go to RunPod
        'edge_case_tests': []         # Unusual questions
    }
    
    # High frequency questions should get instant responses
    high_freq_tests = [tc for tc in test_cases if tc['frequency'] >= 5][:10]
    performance_tests['instant_response_tests'] = high_freq_tests
    
    # Medium frequency questions might go to fallback
    med_freq_tests = [tc for tc in test_cases if 2 <= tc['frequency'] < 5][:10]
    performance_tests['fallback_tests'] = med_freq_tests
    
    # Single occurrence questions for edge cases
    edge_tests = [tc for tc in test_cases if tc['frequency'] == 1][:5]
    performance_tests['edge_case_tests'] = edge_tests
    
    return performance_tests

def main():
    """Main function to create test suite"""
    
    print("🧪 CREATING TEST SUITE FROM EXISTING SIMILARITY SYSTEM")
    print("=" * 60)
    
    # Extract questions from existing system
    question_data = extract_questions_from_similarity_system()
    
    if not question_data:
        print("❌ No question data extracted")
        return
    
    # Display summary
    print("\n📊 QUESTION ANALYSIS SUMMARY")
    print("-" * 40)
    print(f"Total questions: {question_data['total_questions']:,}")
    print(f"Unique questions: {question_data['unique_questions']:,}")
    
    print("\n📋 TOP CATEGORIES")
    print("-" * 30)
    category_counts = {cat: len(questions) for cat, questions in question_data['categories'].items()}
    for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"{category:20}: {count:4} questions")
    
    print(f"\n🔥 TOP 20 MOST FREQUENT QUESTIONS")
    print("-" * 50)
    for i, (question, count) in enumerate(question_data['top_20_questions'], 1):
        print(f"{i:2}. ({count:2}x) {question[:60]}{'...' if len(question) > 60 else ''}")
    
    # Create test cases
    print(f"\n🧪 GENERATING TEST CASES")
    print("-" * 30)
    
    test_cases = create_test_cases(question_data, min_frequency=2)
    print(f"Created {len(test_cases)} test cases for questions with 2+ occurrences")
    
    # Create performance test suite
    performance_suite = create_performance_test_suite(test_cases)
    
    print(f"Performance test breakdown:")
    for test_type, tests in performance_suite.items():
        print(f"  {test_type}: {len(tests)} tests")
    
    # Save results
    output_files = {
        'question_analysis_v1.json': question_data,
        'test_cases_v1.json': test_cases,
        'performance_test_suite_v1.json': performance_suite
    }
    
    for filename, data in output_files.items():
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✅ Saved: {filename}")
        except Exception as e:
            print(f"❌ Error saving {filename}: {e}")
    
    # Show sample test cases
    print(f"\n📋 SAMPLE TEST CASES (Top 5)")
    print("-" * 50)
    for i, test_case in enumerate(test_cases[:5], 1):
        print(f"{i}. [{test_case['category']}] ({test_case['frequency']}x)")
        print(f"   Q: {test_case['question']}")
        if test_case['sample_responses']:
            print(f"   A: {test_case['sample_responses'][0][:50]}...")
        if test_case['test_variations']:
            print(f"   Variations: {len(test_case['test_variations'])} generated")
        print()
    
    print("🎉 Test suite generation complete!")
    print(f"📁 Files created:")
    for filename in output_files.keys():
        print(f"   - {filename}")

if __name__ == "__main__":
    main()
