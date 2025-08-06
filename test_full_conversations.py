"""
Test Full Conversation Extraction

This script demonstrates the difference between fragmented and full conversation extraction
"""

import os
import sys
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.langchain.conversation_indexer import ConversationIndexer
from src.utils.logger import logger


def show_sample_conversations():
    """
    Show sample conversations from the database to see what we're working with
    """
    logger.info("📞 SAMPLE CONVERSATIONS FROM DATABASE")
    logger.info("=" * 50)
    
    indexer = ConversationIndexer()
    indexer.load_conversations()
    
    # Show a few sample conversations
    for i, conv in enumerate(indexer.conversations[:5], 1):
        transcription = conv.get('Transcription', '')
        logger.info(f"\n🎤 CONVERSATION {i}:")
        logger.info(f"   Date: {conv.get('CreationDate', 'Unknown')}")
        logger.info(f"   Length: {len(transcription)} characters")
        logger.info(f"   Content: {transcription[:200]}...")
        
        # Parse this conversation
        flow = indexer._parse_full_conversation_flow(transcription)
        if flow and flow.get('exchanges'):
            exchange = flow['exchanges'][0]
            logger.info(f"\n   📋 EXTRACTED EXCHANGE:")
            logger.info(f"   Client: {exchange.get('client_message', 'None')[:150]}...")
            logger.info(f"   Jamie: {exchange.get('jamie_response', 'None')[:150]}...")
        else:
            logger.info(f"   ❌ No clear exchange extracted")


def demonstrate_full_vs_fragment():
    """
    Demonstrate the difference between full and fragmented conversation extraction
    """
    logger.info("\n🔍 FULL vs FRAGMENTED CONVERSATION EXTRACTION")
    logger.info("=" * 60)
    
    indexer = ConversationIndexer()
    indexer.load_conversations()
    indexer.build_conversation_threads()
    
    # Find a good conversation to demonstrate
    good_conversations = []
    for conv in indexer.conversations:
        transcription = conv.get('Transcription', '')
        if (len(transcription) > 200 and 
            'jamie' in transcription.lower() and 
            any(word in transcription.lower() for word in ['help', 'problem', 'issue', 'ac', 'maintenance'])):
            good_conversations.append(conv)
            if len(good_conversations) >= 3:
                break
    
    if not good_conversations:
        logger.error("No suitable conversations found for demonstration")
        return
    
    for i, conv in enumerate(good_conversations, 1):
        transcription = conv.get('Transcription', '')
        logger.info(f"\n📖 EXAMPLE {i} - FULL CONVERSATION:")
        logger.info(f"   Length: {len(transcription)} characters")
        logger.info(f"   Full transcript: {transcription}")
        
        # Parse with our enhanced method
        flow = indexer._parse_full_conversation_flow(transcription)
        
        if flow and flow.get('exchanges'):
            exchange = flow['exchanges'][0]
            logger.info(f"\n   ✅ ENHANCED EXTRACTION:")
            logger.info(f"   Issue Type: {flow.get('main_issue', 'Unknown')}")
            logger.info(f"   Resolution: {flow.get('resolution', 'Unknown')}")
            logger.info(f"   Client Message: {exchange.get('client_message', 'None')}")
            logger.info(f"   Jamie Response: {exchange.get('jamie_response', 'None')}")
        else:
            logger.info(f"   ❌ Could not extract clear exchange")


def test_complete_conversation_training():
    """
    Test creating training examples with complete conversation context
    """
    logger.info("\n🧠 COMPLETE CONVERSATION TRAINING EXAMPLES")
    logger.info("=" * 55)
    
    indexer = ConversationIndexer()
    indexer.load_conversations()
    indexer.build_conversation_threads()
    
    # Create full conversation examples
    examples = indexer.create_full_conversation_examples(max_examples=5)
    
    logger.info(f"📚 Created {len(examples)} complete conversation examples")
    
    for i, example in enumerate(examples, 1):
        logger.info(f"\n📖 TRAINING EXAMPLE {i}:")
        
        # Show context
        try:
            import json
            context = json.loads(example.get('context', '{}'))
            logger.info(f"   Client: {context.get('client_name', 'Unknown')} ({context.get('client_phone', 'Unknown')})")
            logger.info(f"   Call: {context.get('conversation_number', 1)}/{context.get('total_calls_with_client', 1)}")
            logger.info(f"   Previous Issues: {context.get('previous_issues', [])}")
        except:
            pass
        
        # Show the actual training content
        user_msg = example.get('user', '')
        assistant_msg = example.get('assistant', '')
        
        logger.info(f"   📤 USER MESSAGE ({len(user_msg)} chars):")
        logger.info(f"      {user_msg}")
        logger.info(f"   📥 ASSISTANT MESSAGE ({len(assistant_msg)} chars):")
        logger.info(f"      {assistant_msg}")
        
        # Show full conversation context
        full_conv = example.get('full_conversation', '')
        if full_conv:
            logger.info(f"   📄 FULL CONVERSATION CONTEXT ({len(full_conv)} chars):")
            logger.info(f"      {full_conv[:300]}...")


def main():
    """
    Main test function
    """
    logger.info("🧪 TESTING FULL CONVERSATION EXTRACTION")
    logger.info("=" * 50)
    
    # Step 1: Show sample conversations from database
    show_sample_conversations()
    
    # Step 2: Demonstrate full vs fragmented extraction
    demonstrate_full_vs_fragment()
    
    # Step 3: Test complete conversation training examples
    test_complete_conversation_training()
    
    logger.success("\n🎉 FULL CONVERSATION TESTING COMPLETE!")


if __name__ == "__main__":
    main()