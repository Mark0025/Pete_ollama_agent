"""
Jamie LangChain Property Manager Trainer

This script uses LangChain-powered conversation processing to train
Jamie on real property management conversations with full context.
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


class JamieTrainer:
    """
    Main LangChain trainer for Jamie the property manager
    """
    
    def __init__(self):
        self.indexer = ConversationIndexer()
        self.generator = SmartModelfileGenerator()
        self.training_complete = False
        self.model_name = None
    
    def run_complete_training(self, max_examples: int = 20) -> bool:
        """
        Run complete Jamie training process using LangChain methodology
        """
        logger.info("🤖 Jamie LangChain Property Manager Training")
        logger.info("=" * 55)
        logger.info("📚 Training Jamie on real property management conversations")
        logger.info("🧠 Using LangChain-powered context understanding")
        logger.info("")
        
        # Step 1: Index conversations with full context
        logger.info("Step 1: 🔍 Indexing conversations with context...")
        if not self.indexer.run_full_indexing():
            logger.error("❌ Conversation indexing failed")
            return False
        
        # Step 2: Analyze conversation patterns and threads
        logger.info("\nStep 2: 📊 Analyzing conversation patterns...")
        patterns = self.indexer.analyze_conversation_patterns()
        
        self._log_analysis_summary(patterns)
        
        # Step 3: Generate training examples with context
        logger.info("\nStep 3: 📚 Creating context-aware training examples...")
        examples = self.indexer.create_training_examples(max_examples)
        
        if not examples:
            logger.error("❌ No training examples generated")
            return False
        
        logger.info(f"✅ Generated {len(examples)} high-quality examples")
        
        # Step 4: Create smart Modelfile
        logger.info("\nStep 4: 🧠 Generating smart Modelfile...")
        self.generator.training_examples = examples
        self.generator.conversation_threads = self.indexer.conversation_threads
        self.generator.patterns = patterns
        
        success, model_name = self.generator.save_and_create_model(
            max_examples=max_examples
        )
        
        if success:
            self.training_complete = True
            self.model_name = model_name
            logger.success(f"\n🎉 SUCCESS! Jamie model trained: {model_name}")
            logger.info(f"📊 Trained on {len(examples)} real conversations")
            logger.info(f"🧵 {len(self.indexer.conversation_threads)} conversation threads")
            logger.info(f"👥 Real client interactions with context")
            logger.info(f"\n🧪 Test your model:")
            logger.info(f"   ollama run {model_name} \"Hi Jamie, my AC stopped working\"")
            return True
        else:
            logger.error("❌ Model creation failed")
            return False
    
    def _log_analysis_summary(self, patterns: dict):
        """Log summary of conversation analysis"""
        client_issues = patterns.get('common_client_issues', {})
        jamie_responses = patterns.get('jamie_response_types', {})
        
        logger.info("   📋 Client Issues Found:")
        for issue, count in sorted(client_issues.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"      {issue}: {count} occurrences")
        
        logger.info("   💬 Jamie Response Types:")
        for response_type, count in sorted(jamie_responses.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"      {response_type}: {count} responses")
        
        logger.info(f"   🧵 Conversation threads: {len(self.indexer.conversation_threads)}")
    
    def get_training_summary(self) -> dict:
        """Get comprehensive training summary"""
        if not self.training_complete:
            return {"status": "not_trained"}
        
        return {
            "status": "trained",
            "model_name": self.model_name,
            "total_conversations": len(self.indexer.conversations),
            "conversation_threads": len(self.indexer.conversation_threads),
            "training_examples": len(self.generator.training_examples),
            "patterns": self.indexer.analyze_conversation_patterns(),
            "training_date": datetime.now().isoformat()
        }


def main():
    """Main entry point for Jamie LangChain training"""
    trainer = JamieTrainer()
    
    # Run complete training
    success = trainer.run_complete_training(max_examples=25)
    
    if success:
        # Show summary
        summary = trainer.get_training_summary()
        logger.info("\n📊 Training Summary:")
        logger.info(f"   Model: {summary['model_name']}")
        logger.info(f"   Conversations: {summary['total_conversations']}")
        logger.info(f"   Threads: {summary['conversation_threads']}")
        logger.info(f"   Examples: {summary['training_examples']}")
        
    else:
        logger.error("❌ Training failed")
        sys.exit(1)


if __name__ == "__main__":
    main()