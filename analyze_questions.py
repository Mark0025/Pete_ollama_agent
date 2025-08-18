#!/usr/bin/env python3
"""
Question Analysis Script
========================

Analyzes all questions from langchain_indexed_conversations.json to:
1. Extract every unique question that has been asked
2. Count frequency of each question pattern
3. Generate test cases for the most common questions
4. Create comprehensive test suite data

This will help optimize the similarity matching system and create better test coverage.
"""

import json
import sys
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Tuple, Set

# Simple stopwords list (no NLTK needed)
STOPWORDS = {
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has', 'he', 
    'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the', 'to', 'was', 'were', 
    'will', 'with', 'i', 'you', 'we', 'they', 'me', 'my', 'your', 'our', 'their'
}

def clean_question(text: str) -> str:
    """Clean and normalize question text"""
    if not text:
        return ""
    
    # Remove extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove common phone conversation artifacts
    text = re.sub(r'\b(um|uh|ah|er|like|you know)\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text.strip())
    
    return text

def extract_questions(text: str) -> List[str]:
    """Extract questions from conversation text"""
    if not text:
        return []
    
    questions = []
    
    # Split by sentence endings and look for question patterns
    sentences = re.split(r'[.!?]+', text)
    
    for sentence in sentences:
        sentence = clean_question(sentence)
        if not sentence:
            continue
            
        # Check if it's likely a question
        is_question = False
        
        # Direct question marks (after cleaning)
        if '?' in sentence:
            is_question = True
        
        # Question word patterns
        question_patterns = [
            r'\b(what|when|where|who|why|how|which|whose|whom)\b',
            r'\b(is|are|am|was|were|do|does|did|can|could|would|will|should|may|might)\s',
            r'\b(have you|has he|has she|have they|do you|does he|does she|are you|is there|are there)\b'
        ]
        
        for pattern in question_patterns:
            if re.search(pattern, sentence, re.IGNORECASE):
                is_question = True
                break
        
        if is_question and len(sentence.split()) >= 3:  # At least 3 words
            # Clean up the question
            question = sentence.strip()
            if not question.endswith('?'):
                question += '?'
            questions.append(question)
    
    return questions

def normalize_question(question: str) -> str:
    """Normalize question for similarity matching (simple version)"""
    try:
        # Convert to lowercase
        normalized = question.lower()
        
        # Remove punctuation except question marks
        normalized = re.sub(r'[^\w\s?]', '', normalized)
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized.strip())
        
        # Simple word filtering (remove common stopwords)
        words = normalized.split()
        filtered_words = []
        
        for word in words:
            if word not in STOPWORDS and word != '?':
                filtered_words.append(word)
            elif word == '?':
                filtered_words.append(word)
        
        return ' '.join(filtered_words)
            
    except Exception as e:
        print(f"⚠️ Error normalizing question '{question}': {e}")
        return question.lower()

def categorize_question(question: str) -> str:
    """Categorize questions by topic"""
    question_lower = question.lower()
    
    # Property management categories
    if any(word in question_lower for word in ['rent', 'payment', 'pay', 'due', 'late', 'fee']):
        return 'Rent & Payments'
    
    if any(word in question_lower for word in ['maintenance', 'repair', 'fix', 'broken', 'leak', 'heat', 'ac', 'air']):
        return 'Maintenance & Repairs'
    
    if any(word in question_lower for word in ['lease', 'contract', 'agreement', 'term', 'renewal', 'sign']):
        return 'Lease & Legal'
    
    if any(word in question_lower for word in ['pet', 'dog', 'cat', 'animal']):
        return 'Pet Policy'
    
    if any(word in question_lower for word in ['park', 'parking', 'garage', 'spot', 'car']):
        return 'Parking'
    
    if any(word in question_lower for word in ['office', 'hour', 'time', 'open', 'close', 'contact', 'phone']):
        return 'Office & Contact'
    
    if any(word in question_lower for word in ['move', 'moving', 'moveout', 'evict', 'notice', 'leave']):
        return 'Moving & Notices'
    
    if any(word in question_lower for word in ['util', 'electric', 'water', 'gas', 'internet', 'cable']):
        return 'Utilities'
    
    if any(word in question_lower for word in ['neighbor', 'noise', 'complaint', 'issue', 'problem']):
        return 'Tenant Issues'
    
    return 'General'

def analyze_conversations(file_path: str) -> Dict:
    """Analyze conversations and extract question patterns"""
    
    print(f"📊 Analyzing conversations from: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading conversation data: {e}")
        return {}
    
    print(f"📈 Found {len(data.get('threads', {}))} conversation threads")
    
    all_questions = []
    question_contexts = defaultdict(list)
    question_categories = defaultdict(list)
    
    # Extract questions from all conversations
    threads = data.get('threads', {})
    
    for thread_id, thread_data in threads.items():
        conversations = thread_data.get('conversations', [])
        
        for conv in conversations:
            # Look for user/human messages (questions)
            if conv.get('role') in ['user', 'human'] or conv.get('sender') not in ['Jamie', 'assistant']:
                content = conv.get('content', '') or conv.get('message', '')
                
                if content:
                    questions = extract_questions(content)
                    
                    for question in questions:
                        if len(question) > 10:  # Filter out very short questions
                            all_questions.append(question)
                            
                            # Store context (Jamie's response if available)
                            context = {
                                'thread_id': thread_id,
                                'question': question,
                                'original_message': content,
                                'timestamp': conv.get('timestamp', ''),
                                'response': None
                            }
                            
                            # Try to find Jamie's response
                            conv_index = conversations.index(conv)
                            if conv_index + 1 < len(conversations):
                                next_conv = conversations[conv_index + 1]
                                if next_conv.get('sender') == 'Jamie' or next_conv.get('role') == 'assistant':
                                    context['response'] = next_conv.get('content', '') or next_conv.get('message', '')
                            
                            question_contexts[question].append(context)
                            
                            # Categorize question
                            category = categorize_question(question)
                            question_categories[category].append(question)
    
    print(f"🔍 Extracted {len(all_questions)} total questions")
    print(f"📝 Found {len(question_contexts)} unique question patterns")
    
    # Count question frequencies
    question_counter = Counter(all_questions)
    normalized_counter = Counter()
    
    # Group similar questions by normalized form
    question_groups = defaultdict(list)
    
    for question in all_questions:
        normalized = normalize_question(question)
        normalized_counter[normalized] += 1
        question_groups[normalized].append(question)
    
    # Prepare results
    results = {
        'total_questions': len(all_questions),
        'unique_questions': len(question_contexts),
        'question_frequencies': dict(question_counter.most_common()),
        'normalized_frequencies': dict(normalized_counter.most_common()),
        'question_groups': dict(question_groups),
        'question_contexts': dict(question_contexts),
        'categories': {category: len(questions) for category, questions in question_categories.items()},
        'category_breakdown': dict(question_categories),
        'most_common_questions': question_counter.most_common(20),
        'most_common_normalized': normalized_counter.most_common(20)
    }
    
    return results

def generate_test_cases(analysis_results: Dict, min_frequency: int = 2) -> List[Dict]:
    """Generate test cases from analysis results"""
    
    test_cases = []
    
    # Use normalized questions that appear frequently
    for normalized_question, frequency in analysis_results['most_common_normalized']:
        if frequency >= min_frequency:
            # Get original questions for this normalized form
            original_questions = analysis_results['question_groups'][normalized_question]
            
            # Get context for the most common original question
            most_common_original = Counter(original_questions).most_common(1)[0][0]
            contexts = analysis_results['question_contexts'][most_common_original]
            
            # Create test case
            test_case = {
                'normalized_question': normalized_question,
                'frequency': frequency,
                'original_variants': list(set(original_questions)),
                'primary_question': most_common_original,
                'category': categorize_question(most_common_original),
                'sample_responses': []
            }
            
            # Add sample responses
            for context in contexts[:3]:  # Up to 3 sample responses
                if context['response']:
                    test_case['sample_responses'].append(context['response'][:200] + '...' if len(context['response']) > 200 else context['response'])
            
            test_cases.append(test_case)
    
    # Sort by frequency
    test_cases.sort(key=lambda x: x['frequency'], reverse=True)
    
    return test_cases

def main():
    """Main analysis function"""
    
    # Look for conversation data file
    data_file = 'langchain_indexed_conversations.json'
    
    if not Path(data_file).exists():
        print(f"❌ Conversation data file not found: {data_file}")
        print("Please make sure the file exists in the current directory.")
        return
    
    print("🔬 CONVERSATION QUESTION ANALYSIS")
    print("=" * 60)
    
    # Analyze conversations
    results = analyze_conversations(data_file)
    
    if not results:
        print("❌ No analysis results generated")
        return
    
    print("\n📊 ANALYSIS SUMMARY")
    print("-" * 30)
    print(f"Total questions asked: {results['total_questions']:,}")
    print(f"Unique question patterns: {results['unique_questions']:,}")
    
    print("\n📋 QUESTION CATEGORIES")
    print("-" * 30)
    for category, count in sorted(results['categories'].items(), key=lambda x: x[1], reverse=True):
        print(f"{category:20}: {count:4} questions")
    
    print("\n🔥 TOP 20 MOST COMMON QUESTIONS")
    print("-" * 50)
    for i, (question, count) in enumerate(results['most_common_questions'], 1):
        print(f"{i:2}. ({count:2}x) {question[:70]}{'...' if len(question) > 70 else ''}")
    
    print("\n🎯 TOP 20 NORMALIZED QUESTION PATTERNS")
    print("-" * 50)
    for i, (normalized, count) in enumerate(results['most_common_normalized'], 1):
        print(f"{i:2}. ({count:2}x) {normalized[:70]}{'...' if len(normalized) > 70 else ''}")
    
    # Generate test cases
    print("\n🧪 GENERATING TEST CASES")
    print("-" * 30)
    
    test_cases = generate_test_cases(results, min_frequency=2)
    print(f"Generated {len(test_cases)} test cases for questions asked 2+ times")
    
    # Save results
    output_files = {
        'question_analysis.json': results,
        'test_cases.json': test_cases
    }
    
    for filename, data in output_files.items():
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✅ Saved: {filename}")
        except Exception as e:
            print(f"❌ Error saving {filename}: {e}")
    
    print("\n🎉 Analysis complete!")
    print(f"📁 Results saved to: question_analysis.json")
    print(f"🧪 Test cases saved to: test_cases.json")
    
    # Show preview of test cases
    print(f"\n📋 PREVIEW: TOP 10 TEST CASES")
    print("-" * 50)
    for i, test_case in enumerate(test_cases[:10], 1):
        print(f"{i:2}. [{test_case['category']}] ({test_case['frequency']}x)")
        print(f"    Q: {test_case['primary_question'][:60]}{'...' if len(test_case['primary_question']) > 60 else ''}")
        if test_case['sample_responses']:
            print(f"    A: {test_case['sample_responses'][0][:60]}{'...' if len(test_case['sample_responses'][0]) > 60 else ''}")
        print()

if __name__ == "__main__":
    main()
