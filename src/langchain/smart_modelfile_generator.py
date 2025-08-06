"""
Smart Modelfile Generator for LangChain Integration

This module creates intelligent Modelfiles using:
- Processed conversation context from ConversationIndexer
- Real conversation flow understanding
- Jamie-focused training examples
- Proper conversation threading and context
"""

import os
import json
import sys
from typing import Dict, List, Tuple
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import logger
from .conversation_indexer import ConversationIndexer


class SmartModelfileGenerator:
    """
    Generates intelligent Modelfiles using LangChain-processed conversation data
    
    Key Features:
    - Uses real conversation context and threading
    - Focuses on Jamie's property management expertise
    - Creates contextually-aware training examples
    - Builds proper conversation flow understanding
    """
    
    def __init__(self, indexed_data_path: str = None):
        self.indexed_data = None
        self.training_examples = []
        self.conversation_threads = {}
        self.patterns = {}
        
        if indexed_data_path and os.path.exists(indexed_data_path):
            self.load_indexed_data(indexed_data_path)
    
    def load_indexed_data(self, data_path: str) -> bool:
        """Load indexed conversation data from JSON"""
        try:
            with open(data_path, 'r') as f:
                self.indexed_data = json.load(f)
            
            self.training_examples = self.indexed_data.get('training_examples', [])
            self.conversation_threads = self.indexed_data.get('conversation_threads', {})
            self.patterns = self.indexed_data.get('patterns', {})
            
            logger.info(f"✅ Loaded indexed data with {len(self.training_examples)} examples")
            return True
            
        except Exception as e:
            logger.error(f"Error loading indexed data: {e}")
            return False
    
    def generate_from_live_data(self) -> bool:
        """Generate indexed data from live database"""
        logger.info("🔄 Generating fresh indexed data from database...")
        
        indexer = ConversationIndexer()
        if indexer.run_full_indexing():
            self.training_examples = indexer.create_training_examples()
            self.conversation_threads = indexer.conversation_threads
            self.patterns = indexer.analyze_conversation_patterns()
            return True
        return False
    
    def select_best_examples(self, max_examples: int = 15) -> List[Dict]:
        """
        Select the best training examples based on:
        - Conversation quality and completeness
        - Diversity of issues/responses
        - Jamie's expertise demonstration
        - Context richness
        """
        if not self.training_examples:
            logger.warning("No training examples available")
            return []
        
        # Score examples based on quality metrics
        scored_examples = []
        
        for example in self.training_examples:
            score = 0
            user_msg = example.get('user', '')
            assistant_msg = example.get('assistant', '')
            context = example.get('context', '{}')
            
            # Length quality (substantial but not too long)
            user_len = len(user_msg)
            assistant_len = len(assistant_msg)
            if 50 <= user_len <= 300 and 30 <= assistant_len <= 400:
                score += 10
            
            # Response quality indicators
            quality_indicators = [
                "i'll", "let me", "i can", "i will", "schedule", 
                "call", "check", "send", "maintenance", "repair"
            ]
            score += sum(2 for indicator in quality_indicators 
                        if indicator in assistant_msg.lower())
            
            # Issue diversity
            issue_types = [
                ("maintenance", ["repair", "fix", "broken", "ac", "leak"]),
                ("payment", ["rent", "payment", "late", "check"]),
                ("move", ["move", "transfer", "address", "lease"]),
                ("emergency", ["emergency", "urgent", "asap"])
            ]
            
            for issue_type, keywords in issue_types:
                if any(keyword in user_msg.lower() for keyword in keywords):
                    score += 5
                    break
            
            # Context richness
            try:
                context_data = json.loads(context)
                if context_data.get('previous_interactions', 0) > 0:
                    score += 3
                if context_data.get('client_name', 'Unknown') != 'Unknown':
                    score += 2
            except:
                pass
            
            scored_examples.append((score, example))
        
        # Sort by score and take top examples
        scored_examples.sort(key=lambda x: x[0], reverse=True)
        best_examples = [example for score, example in scored_examples[:max_examples]]
        
        logger.info(f"✅ Selected {len(best_examples)} best training examples")
        return best_examples
    
    def create_system_prompt(self) -> str:
        """Create comprehensive system prompt based on conversation patterns"""
        
        # Analyze Jamie's common response patterns
        common_issues = self.patterns.get('common_client_issues', {})
        response_types = self.patterns.get('jamie_response_types', {})
        
        # Count total conversations and clients
        total_threads = len(self.conversation_threads)
        total_conversations = sum(len(thread['conversations']) 
                                for thread in self.conversation_threads.values())
        
        system_prompt = f"""You are Jamie, an expert property manager with extensive experience managing residential properties. You have been trained on {total_conversations} real property management conversations with {total_threads} different clients.

Your expertise includes:

🏠 PROPERTY MANAGEMENT CORE SKILLS:
- Tenant communications and relationship management
- Maintenance coordination and emergency response
- Lease management, renewals, and move-in/move-out processes
- Rent collection and payment issue resolution
- Property inspection and compliance
- Vendor management and contractor coordination

📞 COMMUNICATION STYLE (learned from real conversations):
- Professional yet personable and approachable
- Proactive in scheduling and follow-up
- Clear about next steps and timelines
- Empathetic to tenant concerns, especially emergencies
- Efficient in problem-solving and decision-making

🔧 COMMON TENANT ISSUES YOU HANDLE:
- Maintenance requests (AC, plumbing, electrical, appliances)
- Emergency repairs requiring immediate attention
- Routine maintenance and property upkeep
- Payment questions and late rent situations
- Move coordination and address changes
- Property access and lockbox arrangements

💡 YOUR RESPONSE APPROACH:
- Always acknowledge the tenant's concern immediately
- Provide specific next steps and timelines
- Offer contact information when appropriate (405-367-6318)
- Schedule maintenance or follow-up as needed
- Keep tenants informed throughout the process
- Prioritize emergencies (AC outages, leaks, safety issues)

📋 CONVERSATION CONTEXT AWARENESS:
You understand that tenants may have called before about similar issues. You maintain context about ongoing situations and can reference previous conversations when relevant.

Always respond as Jamie would - professionally, helpfully, and with practical solutions that demonstrate your property management expertise."""
        
        return system_prompt
    
    def format_message_pairs(self, examples: List[Dict]) -> str:
        """Format training examples as MESSAGE pairs for Modelfile with FULL context"""
        message_pairs = []
        
        for i, example in enumerate(examples, 1):
            user_msg = example.get('user', '').strip()
            assistant_msg = example.get('assistant', '').strip()
            
            # Clean up messages for Modelfile format
            user_msg = self._clean_for_modelfile(user_msg)
            assistant_msg = self._clean_for_modelfile(assistant_msg)
            
            if user_msg and assistant_msg:
                # Add rich context comment with client info
                try:
                    context = json.loads(example.get('context', '{}'))
                    client_name = context.get('client_name', 'Client')
                    client_phone = context.get('client_phone', 'Unknown')
                    conversation_num = context.get('conversation_number', 1)
                    total_calls = context.get('total_calls_with_client', 1)
                    previous_issues = context.get('previous_issues', [])
                    
                    # Create rich context comment
                    context_comment = f"# Example {i}: {client_name} ({client_phone})"
                    if total_calls > 1:
                        context_comment += f" - Call {conversation_num}/{total_calls}"
                    if previous_issues:
                        context_comment += f" - Previous: {', '.join(previous_issues[-2:])}"
                    
                    # Add conversation flow info if available
                    conversation_flow = example.get('conversation_flow', {})
                    if conversation_flow:
                        main_issue = conversation_flow.get('main_issue', 'General')
                        resolution = conversation_flow.get('resolution', 'Handled')
                        context_comment += f" - Issue: {main_issue} - {resolution}"
                    
                    message_pairs.append(context_comment)
                    
                    # Add full conversation context as comment (truncated)
                    full_conv = example.get('full_conversation', '')
                    if full_conv:
                        conv_preview = full_conv[:150] + "..." if len(full_conv) > 150 else full_conv
                        message_pairs.append(f"# Full context: {conv_preview}")
                    
                except Exception as e:
                    message_pairs.append(f"# Example {i}: Property Management Conversation")
                
                message_pairs.append(f'MESSAGE user """{user_msg}"""')
                message_pairs.append(f'MESSAGE assistant """{assistant_msg}"""')
                message_pairs.append("")  # Empty line for readability
        
        return "\n".join(message_pairs)
    
    def _clean_for_modelfile(self, text: str) -> str:
        """Clean text for Modelfile format"""
        # Remove excessive whitespace
        text = " ".join(text.split())
        
        # Escape quotes for Modelfile
        text = text.replace('"""', '\\"\\"\\"')
        text = text.replace('"', '\\"')
        
        # Limit length to avoid Modelfile issues
        if len(text) > 500:
            text = text[:497] + "..."
        
        return text
    
    def generate_smart_modelfile(self, 
                                base_model: str = "llama3:latest",
                                model_name: str = None,
                                max_examples: int = 15) -> str:
        """Generate complete smart Modelfile with context-aware training"""
        
        if model_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            model_name = f"peteollama:jamie-smart-{timestamp}"
        
        # Get best training examples
        best_examples = self.select_best_examples(max_examples)
        
        if not best_examples:
            logger.warning("No training examples available - generating basic Modelfile")
            best_examples = []
        
        # Generate system prompt
        system_prompt = self.create_system_prompt()
        
        # Format MESSAGE pairs
        message_pairs = self.format_message_pairs(best_examples)
        
        # Create complete Modelfile
        modelfile = f"""FROM {base_model}

# Jamie - Smart Property Manager AI
# Trained on {len(self.training_examples)} real property management conversations
# Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

SYSTEM \"\"\"{system_prompt}\"\"\"

# Model Parameters for Property Management Conversations
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1
PARAMETER num_ctx 8192
PARAMETER stop "Human:"
PARAMETER stop "Assistant:"

# Conversation Template
TEMPLATE \"\"\"{{{{ if .System }}}}{{{{ .System }}}}

{{{{ end }}}}{{{{ if .Prompt }}}}Human: {{{{ .Prompt }}}}

{{{{ end }}}}Assistant: {{{{ .Response }}}}\"\"\"

# Training Examples from Real Property Management Conversations
{message_pairs}"""
        
        logger.info(f"✅ Generated smart Modelfile for {model_name}")
        logger.info(f"   📊 System prompt: {len(system_prompt)} characters")
        logger.info(f"   📚 Training examples: {len(best_examples)}")
        logger.info(f"   🎯 Model name: {model_name}")
        
        return modelfile, model_name
    
    def save_and_create_model(self, 
                             base_model: str = "llama3:latest",
                             model_name: str = None,
                             max_examples: int = 15) -> Tuple[bool, str]:
        """Generate, save, and create the smart model"""
        
        # Generate Modelfile
        modelfile_content, final_model_name = self.generate_smart_modelfile(
            base_model, model_name, max_examples
        )
        
        # Save Modelfile
        models_dir = Path(os.getcwd()) / "models"
        models_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        modelfile_path = models_dir / f"Modelfile.smart.{timestamp}"
        
        with open(modelfile_path, 'w') as f:
            f.write(modelfile_content)
        
        logger.info(f"💾 Saved Modelfile to {modelfile_path}")
        
        # Create model using Ollama
        try:
            import requests
            import json
            
            response = requests.post(
                "http://localhost:11434/api/create",
                json={
                    "name": final_model_name,
                    "modelfile": modelfile_content
                },
                stream=True
            )
            
            success = False
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    status = data.get('status', '')
                    if status:
                        logger.info(f"Model creation: {status}")
                    if 'success' in data and data['success']:
                        success = True
            
            if response.status_code == 200:
                success = True
                logger.success(f"🎉 Smart model created: {final_model_name}")
            else:
                logger.error(f"Model creation failed: {response.status_code}")
            
            return success, final_model_name
            
        except Exception as e:
            logger.error(f"Error creating model: {e}")
            return False, final_model_name


def main():
    """Main function for testing the smart Modelfile generator"""
    logger.info("🧠 Smart Modelfile Generator for Jamie Property Manager")
    logger.info("=" * 60)
    
    generator = SmartModelfileGenerator()
    
    # Generate from live data
    if generator.generate_from_live_data():
        # Create smart model
        success, model_name = generator.save_and_create_model(max_examples=20)
        
        if success:
            logger.success("🎉 Smart Jamie model ready for testing!")
            logger.info(f"Test with: ollama run {model_name} \"Hi Jamie, my AC isn't working\"")
        else:
            logger.error("❌ Model creation failed")
    else:
        logger.error("❌ Failed to generate indexed data")


if __name__ == "__main__":
    main()