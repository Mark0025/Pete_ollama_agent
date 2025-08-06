"""
Enhanced Jamie Trainer with Full Conversation Context

This trainer creates complete conversation flows with:
- Phone number tracking for client identification
- Full conversation context from beginning to end
- Client history across multiple calls
- Complete conversation understanding (not snippets)
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.langchain.conversation_indexer import ConversationIndexer
from src.langchain.smart_modelfile_generator import SmartModelfileGenerator
from src.utils.logger import logger


def demonstrate_full_conversation_processing():
    """
    Demonstrate how the enhanced system processes full conversations
    with phone number tracking and complete context
    """
    logger.info("🔍 ENHANCED CONVERSATION PROCESSING DEMONSTRATION")
    logger.info("=" * 60)
    
    indexer = ConversationIndexer()
    
    # Load and process conversations
    if not indexer.load_conversations():
        logger.error("Failed to load conversations")
        return False
    
    # Build conversation threads (phone number based)
    threads = indexer.build_conversation_threads()
    logger.info(f"📞 Built {len(threads)} client threads based on phone numbers")
    
    # Show some example threads
    sorted_threads = sorted(
        threads.items(), 
        key=lambda x: len(x[1]['conversations']), 
        reverse=True
    )
    
    logger.info("\n📋 TOP CLIENT THREADS (by conversation count):")
    for i, (thread_key, thread) in enumerate(sorted_threads[:5], 1):
        client_info = thread['client_info']
        conversations = thread['conversations']
        
        logger.info(f"\n{i}. Client: {client_info['name']} ({client_info['phone']})")
        logger.info(f"   Total calls: {len(conversations)}")
        logger.info(f"   Date range: {thread['date_range']['first']} to {thread['date_range']['last']}")
        
        # Show first conversation preview
        if conversations:
            first_conv = conversations[0]
            preview = first_conv['full_transcription'][:200] + "..."
            logger.info(f"   First call preview: {preview}")
    
    # Create full conversation examples
    logger.info(f"\n🧠 Creating FULL conversation examples with complete context...")
    full_examples = indexer.create_full_conversation_examples(max_examples=10)
    
    logger.info(f"\n📚 FULL CONVERSATION EXAMPLES CREATED: {len(full_examples)}")
    
    # Show detailed example
    if full_examples:
        example = full_examples[0]
        logger.info(f"\n📖 EXAMPLE FULL CONVERSATION:")
        logger.info(f"   Client: {example.get('user', '')[:100]}...")
        logger.info(f"   Jamie: {example.get('assistant', '')[:100]}...")
        
        # Show context
        try:
            import json
            context = json.loads(example.get('context', '{}'))
            logger.info(f"   Context:")
            logger.info(f"     - Client: {context.get('client_name', 'Unknown')} ({context.get('client_phone', 'Unknown')})")
            logger.info(f"     - Call {context.get('conversation_number', 1)}/{context.get('total_calls_with_client', 1)}")
            logger.info(f"     - Previous issues: {context.get('previous_issues', [])}")
        except:
            pass
        
        # Show conversation flow
        conv_flow = example.get('conversation_flow', {})
        if conv_flow:
            logger.info(f"   Conversation Flow:")
            logger.info(f"     - Main issue: {conv_flow.get('main_issue', 'Unknown')}")
            logger.info(f"     - Resolution: {conv_flow.get('resolution', 'Unknown')}")
            logger.info(f"     - Exchanges: {len(conv_flow.get('exchanges', []))}")
    
    return True


def create_enhanced_jamie_model():
    """
    Create Jamie model using full conversation processing
    """
    logger.info("\n🤖 CREATING ENHANCED JAMIE MODEL")
    logger.info("=" * 50)
    
    # Use the enhanced conversation indexer
    indexer = ConversationIndexer()
    
    # Run full indexing
    if not indexer.run_full_indexing():
        logger.error("Failed to run conversation indexing")
        return False
    
    # Create generator with enhanced examples
    generator = SmartModelfileGenerator()
    generator.training_examples = indexer.create_full_conversation_examples(max_examples=15)
    generator.conversation_threads = indexer.conversation_threads
    generator.patterns = indexer.analyze_conversation_patterns()
    
    logger.info(f"📚 Using {len(generator.training_examples)} FULL conversation examples")
    
    # Generate enhanced model
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_name = f"peteollama:jamie-enhanced-{timestamp}"
    
    success, final_model_name = generator.save_and_create_model(
        model_name=model_name,
        max_examples=15
    )
    
    if success:
        logger.success(f"🎉 Enhanced Jamie model created: {final_model_name}")
        logger.info(f"📞 Trained with full phone number tracking")
        logger.info(f"🧵 Complete conversation context understanding")
        logger.info(f"📚 {len(generator.training_examples)} full conversation examples")
        
        logger.info(f"\n🧪 Test your enhanced model:")
        logger.info(f"   ollama run {final_model_name} \"Hi Jamie, this is John calling back about the AC issue\"")
        
        return final_model_name
    else:
        logger.error("❌ Enhanced model creation failed")
        return None


def test_conversation_context_understanding():
    """
    Test the conversation context understanding capabilities
    """
    logger.info("\n🧪 TESTING CONVERSATION CONTEXT UNDERSTANDING")
    logger.info("=" * 55)
    
    indexer = ConversationIndexer()
    indexer.load_conversations()
    threads = indexer.build_conversation_threads()
    
    # Find clients with multiple calls
    multi_call_clients = {k: v for k, v in threads.items() if len(v['conversations']) > 1}
    
    logger.info(f"👥 Clients with multiple calls: {len(multi_call_clients)}")
    
    # Show example of conversation threading
    if multi_call_clients:
        thread_key, thread = list(multi_call_clients.items())[0]
        client_info = thread['client_info']
        conversations = thread['conversations']
        
        logger.info(f"\n📞 EXAMPLE: {client_info['name']} ({client_info['phone']})")
        logger.info(f"   Total calls: {len(conversations)}")
        
        for i, conv in enumerate(conversations[:3], 1):  # Show first 3 calls
            logger.info(f"\n   Call {i} ({conv.get('date', 'Unknown date')}):")
            
            # Parse this conversation
            flow = indexer._parse_full_conversation_flow(conv['full_transcription'])
            if flow:
                logger.info(f"     Issue: {flow.get('main_issue', 'Unknown')}")
                logger.info(f"     Resolution: {flow.get('resolution', 'Unknown')}")
                logger.info(f"     Exchanges: {len(flow.get('exchanges', []))}")
            
            # Show preview
            preview = conv['full_transcription'][:150] + "..."
            logger.info(f"     Preview: {preview}")
    
    return True


def main():
    """
    Main function to demonstrate and create enhanced Jamie model
    """
    logger.info("🚀 ENHANCED JAMIE TRAINING WITH FULL CONVERSATION CONTEXT")
    logger.info("=" * 65)
    logger.info("📋 This trainer demonstrates:")
    logger.info("   • Phone number-based client identification")
    logger.info("   • Full conversation flow analysis")
    logger.info("   • Complete conversation context (not snippets)")
    logger.info("   • Client history across multiple calls")
    logger.info("   • Proper conversation threading")
    logger.info("")
    
    # Step 1: Demonstrate full conversation processing
    if not demonstrate_full_conversation_processing():
        logger.error("❌ Demonstration failed")
        return
    
    # Step 2: Test conversation context understanding
    test_conversation_context_understanding()
    
    # Step 3: Create enhanced model
    model_name = create_enhanced_jamie_model()
    
    if model_name:
        logger.success(f"\n🎉 SUCCESS! Enhanced Jamie model ready: {model_name}")
        logger.info(f"✅ Features:")
        logger.info(f"   • Full conversation understanding")
        logger.info(f"   • Phone number-based client tracking")
        logger.info(f"   • Complete conversation context")
        logger.info(f"   • Multi-call client history")
    else:
        logger.error("❌ Enhanced training failed")


if __name__ == "__main__":
    main()