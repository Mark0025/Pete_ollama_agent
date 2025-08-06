#!/usr/bin/env python3
"""
PeteOllama Enhanced Model Trainer
================================

Implements proper Ollama Modelfile creation using real conversation data
from pete.db following .cursor/rulesOllamaModelfile.md specifications.
"""

import sys
import os
import sqlite3
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import subprocess

# Add src to Python path
src_path = str(Path(__file__).parent / "src")
sys.path.insert(0, src_path)

from database.pete_db_manager import PeteDBManager

class PropertyManagementModelfileGenerator:
    """Generates enhanced Ollama Modelfiles from real conversation data"""
    
    def __init__(self, db_path: str = None, base_model: str = "llama3:latest"):
        """Initialize the generator"""
        self.db_manager = PeteDBManager(db_path) if db_path else PeteDBManager()
        self.base_model = base_model
        self.conversations = []
        self.categorized_conversations = {}
        self.message_pairs = []
        
        # Conversation categories and their keywords
        self.categories = {
            "emergency_maintenance": ["AC", "air conditioning", "heating", "plumbing", "leak", "emergency", "urgent", "baby", "hot", "cold"],
            "routine_maintenance": ["repair", "fix", "maintenance", "door", "window", "garbage disposal", "ceiling fan", "drywall"],
            "rent_payment": ["rent", "payment", "late", "fee", "due", "paycheck", "billing", "money"],
            "move_coordination": ["move", "lockbox", "keys", "transfer", "new", "lease", "address"],
            "account_admin": ["account", "verification", "information", "update", "contact", "email", "phone"]
        }
    
    def extract_conversations(self) -> List[Dict]:
        """Extract and clean conversations from pete.db"""
        print("📊 Extracting conversations from database...")
        
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Enhanced query to get quality conversations
            query = """
            SELECT Transcription, Incoming, Data, CreationDate 
            FROM communication_logs 
            WHERE Transcription IS NOT NULL 
            AND LENGTH(Transcription) > 50
            AND Transcription NOT LIKE '%Welcome to OG&E%'
            AND Transcription NOT LIKE '%Thank you for calling%'
            AND Transcription NOT LIKE '%Your call is being transferred%'
            AND Transcription NOT LIKE '%Please hold%'
            ORDER BY RANDOM()
            LIMIT 100
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            conversations = []
            for row in results:
                conversation = {
                    'transcription': self._clean_transcription(row[0]),
                    'incoming': bool(row[1]),
                    'data': row[2] or '',
                    'date': row[3],
                    'category': self._categorize_conversation(row[0])
                }
                conversations.append(conversation)
            
            self.conversations = conversations
            print(f"✅ Extracted {len(conversations)} quality conversations")
            return conversations
            
        except Exception as e:
            print(f"❌ Error extracting conversations: {e}")
            return []
    
    def _clean_transcription(self, transcription: str) -> str:
        """Clean and standardize transcription text"""
        if not transcription:
            return ""
        
        # Remove automated message prefixes
        patterns_to_remove = [
            r"Welcome to .+?customer service\.",
            r"Thank you for calling .+?\.",
            r"Please hold while .+?\.",
            r"Your call will be answered .+?\.",
            r"Para espanol.+?\.",
            r"Press \d+ for .+?\.",
        ]
        
        cleaned = transcription
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Anonymize while preserving context
        cleaned = re.sub(r'\b\d{3}-\d{3}-\d{4}\b', '[PHONE]', cleaned)
        cleaned = re.sub(r'\b\d{5}\b', '[ZIP]', cleaned)
        
        return cleaned
    
    def _categorize_conversation(self, transcription: str) -> str:
        """Categorize conversation by content"""
        if not transcription:
            return "general"
        
        text_lower = transcription.lower()
        category_scores = {}
        
        for category, keywords in self.categories.items():
            score = sum(1 for keyword in keywords if keyword.lower() in text_lower)
            if score > 0:
                category_scores[category] = score
        
        if not category_scores:
            return "general"
        
        # Return category with highest score
        return max(category_scores, key=category_scores.get)
    
    def categorize_conversations(self) -> Dict[str, List]:
        """Group conversations by type"""
        print("📋 Categorizing conversations...")
        
        categorized = {}
        for conversation in self.conversations:
            category = conversation['category']
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(conversation)
        
        self.categorized_conversations = categorized
        
        # Print category distribution
        for category, convs in categorized.items():
            print(f"  📁 {category}: {len(convs)} conversations")
        
        return categorized
    
    def generate_message_pairs(self) -> List[Tuple[str, str]]:
        """Create user/assistant MESSAGE pairs from conversations"""
        print("🔄 Generating MESSAGE pairs...")
        
        message_pairs = []
        
        # Target distribution for balanced training
        target_per_category = {
            "emergency_maintenance": 6,
            "routine_maintenance": 4, 
            "rent_payment": 4,
            "move_coordination": 3,
            "account_admin": 3
        }
        
        for category, target_count in target_per_category.items():
            if category in self.categorized_conversations:
                conversations = self.categorized_conversations[category][:target_count]
                
                for conv in conversations:
                    user_msg, assistant_msg = self._create_message_pair(conv, category)
                    if user_msg and assistant_msg:
                        message_pairs.append((user_msg, assistant_msg))
        
        self.message_pairs = message_pairs
        print(f"✅ Generated {len(message_pairs)} MESSAGE pairs")
        return message_pairs
    
    def _create_message_pair(self, conversation: Dict, category: str) -> Tuple[str, str]:
        """Create a user/assistant pair from a conversation"""
        transcription = conversation['transcription']
        
        # Extract REAL user and assistant parts from the actual conversation
        user_msg, assistant_msg = self._extract_real_conversation_pair(transcription)
        
        if not user_msg or not assistant_msg:
            return None, None
        
        return user_msg, assistant_msg
    
    def _extract_real_conversation_pair(self, transcription: str) -> Tuple[str, str]:
        """Extract actual user/assistant pair from real conversation transcript"""
        if not transcription:
            return None, None
        
        # Look for patterns that indicate speaker changes in the conversation
        # Common patterns: "This is Jamie", "Hey Jamie", names, direct questions
        
        # Split on common conversation markers
        markers = ["This is Jamie", "Hey Jamie", "Hi Jamie", "Jamie,", "Okay,", "Yeah,", "Alright,"]
        
        # Try to find where Jamie (property manager) responds
        sentences = transcription.split('.')
        
        user_part = ""
        assistant_part = ""
        
        # Look for the tenant's issue/question (usually early in conversation)
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue
                
            # Indicators of tenant issues/questions
            if any(word in sentence.lower() for word in [
                "my", "the", "we have", "I have", "there's", "can you", "when", "how", "what",
                "need", "want", "problem", "issue", "not working", "broken", "calling about"
            ]):
                user_part = sentence
                # Look for Jamie's response in the next few sentences
                for j in range(i+1, min(i+4, len(sentences))):
                    response = sentences[j].strip()
                    if len(response) > 20 and any(word in response for word in [
                        "I'll", "Let me", "I can", "I will", "Okay", "Alright", "Sure", "Yes", "No problem"
                    ]):
                        assistant_part = response
                        break
                break
        
        # If we couldn't find a clear pair, try to split the conversation
        if not user_part or not assistant_part:
            # Fallback: take first substantial part as user, second as assistant
            substantial_parts = [s.strip() for s in sentences if len(s.strip()) > 30]
            if len(substantial_parts) >= 2:
                user_part = substantial_parts[0]
                assistant_part = substantial_parts[1]
        
        # Clean up and validate
        if user_part and assistant_part:
            user_part = user_part[:300]  # Limit length
            assistant_part = assistant_part[:400]  # Limit length
            
            # Make sure assistant part sounds like a property manager response
            if any(word in assistant_part.lower() for word in [
                "I'll", "let me", "I can", "we'll", "maintenance", "schedule", "call", "check"
            ]):
                return user_part, assistant_part
        
        return None, None
    
    def _extract_user_inquiry(self, transcription: str) -> str:
        """Extract the main user inquiry from transcription"""
        # Look for patterns that indicate the main issue
        sentences = transcription.split('.')
        
        # Find sentences with question indicators or problem statements
        inquiry_indicators = [
            "my", "the", "we have", "I have", "there's", "can you", "when", "how", "what",
            "need", "want", "problem", "issue", "not working", "broken"
        ]
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and any(indicator in sentence.lower() for indicator in inquiry_indicators):
                # Clean up and return first good inquiry
                if len(sentence) > 200:
                    sentence = sentence[:200] + "..."
                return sentence
        
        # Fallback: return first substantial sentence
        for sentence in sentences:
            if len(sentence.strip()) > 20:
                return sentence.strip()[:200]
        
        return transcription[:200] if transcription else ""
    
    def _generate_assistant_response(self, user_msg: str, category: str, conversation: Dict) -> str:
        """Generate appropriate assistant response based on category"""
        
        # Use different response for each category and context
        user_lower = user_msg.lower()
        
        if category == "emergency_maintenance" or any(word in user_lower for word in ["ac", "air conditioning", "emergency", "urgent", "baby"]):
            if "baby" in user_lower or "kid" in user_lower:
                return "I'm so sorry about your AC issue, especially with a baby at home. This is definitely a priority emergency. I'll dispatch our maintenance team immediately and they should contact you within the next hour for same-day service. If you need immediate assistance, please call me at 405-367-6318."
            else:
                return "I understand this is an urgent AC issue. I'm scheduling emergency maintenance right away - you should hear from our technician within 2 hours for same-day service. I'll personally follow up to ensure this gets resolved quickly."
        
        elif category == "routine_maintenance" or any(word in user_lower for word in ["repair", "fix", "door", "shower", "disposal"]):
            if "cost" in user_lower or "$" in user_msg:
                return "I'll create a work order for this repair and get you a cost estimate. Our maintenance team will assess it and I'll follow up with pricing and timeline. You can put any approved materials on the company account."
            else:
                return "Thanks for reporting this maintenance issue. I'll coordinate with our contractor to schedule the repair. I'll keep you updated on the timeline and let you know if I need any additional information."
        
        elif category == "rent_payment" or any(word in user_lower for word in ["rent", "payment", "late", "paycheck"]):
            if "paycheck" in user_lower:
                return "I understand the paycheck situation is affecting your rent payment. Thanks for communicating with us. Just keep me updated on when you expect it to be resolved, and we'll work with you to avoid unnecessary late fees."
            else:
                return "I appreciate you reaching out about the payment situation. Let's work together on a solution. Please keep me in the loop and we'll make sure everything gets handled properly."
        
        elif category == "move_coordination" or any(word in user_lower for word in ["move", "lockbox", "transfer", "address"]):
            return "I'll help coordinate that for you. Let me get the process started and I'll send you confirmation details once everything is set up. I'll make sure all the logistics are handled properly."
        
        elif category == "account_admin" or any(word in user_lower for word in ["account", "verification", "email", "information"]):
            return "I'll look into that account information for you right away. Let me verify the details and I'll get back to you with an update by end of day. I'll send confirmation to your email once everything is current."
        
        else:
            # General response
            return "Thanks for reaching out. I'll look into this for you and get back to you with more information. If you need immediate assistance, please call me at 405-367-6318."
    
    def _extract_context(self, user_msg: str, conversation: Dict) -> str:
        """Extract relevant context from user message"""
        if "baby" in user_msg.lower() or "kid" in user_msg.lower():
            return "with a baby/child at home"
        elif "urgent" in user_msg.lower() or "emergency" in user_msg.lower():
            return "given the urgent nature"
        elif "paycheck" in user_msg.lower():
            return "with the paycheck issue"
        return "with this situation"
    
    def _extract_details(self, user_msg: str, conversation: Dict) -> str:
        """Extract relevant details for response"""
        if "cost" in user_msg.lower() or "$" in user_msg:
            return "I'll get you a cost estimate for the materials and labor."
        elif "time" in user_msg.lower() or "when" in user_msg.lower():
            return "I'll provide you with a timeline for completion."
        elif "schedule" in user_msg.lower():
            return "I'll coordinate the scheduling and timing."
        return "I'll handle all the details and coordination."
    
    def create_modelfile(self) -> str:
        """Generate complete Modelfile content"""
        print("📝 Creating enhanced Modelfile...")
        
        # Check if base model is available
        available_models = self._get_available_models()
        if self.base_model not in available_models:
            print(f"⚠️  Base model {self.base_model} not available. Using llama3:latest")
            self.base_model = "llama3:latest"
        
        modelfile_content = f"""FROM {self.base_model}

SYSTEM \"\"\"You are PeteOllama, an expert AI property manager with extensive experience in:
- Tenant communications and relations
- Property maintenance coordination  
- Lease management and renewals
- Financial calculations and rent collection
- Real estate market knowledge
- Legal compliance and documentation

You have been trained on {len(self.conversations)} real property management phone conversations and understand:
- Common tenant concerns and questions
- Professional communication standards
- Property management best practices
- Emergency vs. routine maintenance prioritization
- Payment issues and late fee management
- Move-in/move-out coordination

Always respond professionally, helpfully, and with practical solutions.
Prioritize urgent issues (AC outages, plumbing emergencies) over routine requests.
Provide clear next steps and contact information when appropriate.
\"\"\"

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1
PARAMETER num_ctx 8192

TEMPLATE \"\"\"{{{{ if .System }}}}{{{{ .System }}}}

{{{{ end }}}}{{{{ if .Prompt }}}}Human: {{{{ .Prompt }}}}

{{{{ end }}}}Assistant: {{{{ .Response }}}}\"\"\"

"""
        
        # Add MESSAGE pairs
        for i, (user_msg, assistant_msg) in enumerate(self.message_pairs, 1):
            modelfile_content += f'\n# Example {i}: {self._get_example_title(user_msg)}\n'
            modelfile_content += f'MESSAGE user "{self._escape_quotes(user_msg)}"\n'
            modelfile_content += f'MESSAGE assistant "{self._escape_quotes(assistant_msg)}"\n'
        
        return modelfile_content
    
    def _get_available_models(self) -> List[str]:
        """Get list of available Ollama models"""
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                models = [line.split()[0] for line in lines if line.strip()]
                return models
        except Exception:
            pass
        return []
    
    def _get_example_title(self, user_msg: str) -> str:
        """Generate descriptive title for example"""
        if "AC" in user_msg or "air conditioning" in user_msg:
            return "AC Emergency"
        elif "rent" in user_msg.lower() or "payment" in user_msg.lower():
            return "Payment Issue"
        elif "repair" in user_msg.lower() or "fix" in user_msg.lower():
            return "Maintenance Request"
        elif "move" in user_msg.lower() or "lockbox" in user_msg.lower():
            return "Move Coordination"
        else:
            return "General Inquiry"
    
    def _escape_quotes(self, text: str) -> str:
        """Escape quotes for Modelfile format"""
        return text.replace('"', '\\"').replace('\n', ' ').strip()
    
    def save_and_create_model(self, model_name: str = None) -> bool:
        """Save Modelfile and create Ollama model"""
        if not model_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            model_name = f"peteollama:property-manager-{timestamp}"
        
        print(f"💾 Creating model: {model_name}")
        
        # Create models directory
        models_dir = Path("models")
        models_dir.mkdir(exist_ok=True)
        
        # Generate and save Modelfile
        modelfile_content = self.create_modelfile()
        modelfile_path = models_dir / "Modelfile.enhanced"
        
        try:
            with open(modelfile_path, 'w', encoding='utf-8') as f:
                f.write(modelfile_content)
            print(f"✅ Saved Modelfile to {modelfile_path}")
            
            # Create model with ollama
            cmd = ['ollama', 'create', model_name, '-f', str(modelfile_path)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"🎉 Successfully created model: {model_name}")
                return True
            else:
                print(f"❌ Failed to create model: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error saving/creating model: {e}")
            return False

def main():
    """Main execution function"""
    print("🏠 PeteOllama Enhanced Model Trainer")
    print("=" * 50)
    print("📊 Training on real property management conversations")
    print()
    
    try:
        # Initialize generator
        generator = PropertyManagementModelfileGenerator()
        
        # Check database connection
        if not generator.db_manager.is_connected():
            print("❌ Cannot connect to database!")
            return False
        
        stats = generator.db_manager.get_training_stats()
        print(f"📞 Total conversations available: {stats['total']}")
        print(f"📅 Date range: {stats['date_range']}")
        print()
        
        # Extract and process conversations
        conversations = generator.extract_conversations()
        if not conversations:
            print("❌ No conversations found!")
            return False
        
        # Categorize conversations
        categorized = generator.categorize_conversations()
        print()
        
        # Generate MESSAGE pairs
        message_pairs = generator.generate_message_pairs()
        if not message_pairs:
            print("❌ No MESSAGE pairs generated!")
            return False
        
        print()
        
        # Create enhanced model
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_name = f"peteollama:property-manager-enhanced-{timestamp}"
        
        success = generator.save_and_create_model(model_name)
        
        if success:
            print()
            print("🎉 SUCCESS! Enhanced property management model created!")
            print(f"✅ Model: {model_name}")
            print(f"📊 Trained on {len(conversations)} real conversations")
            print(f"🔄 {len(message_pairs)} MESSAGE pairs included")
            print()
            print("🧪 Test your model:")
            print(f"   ollama run {model_name} \"My AC isn't working, can you help?\"")
            return True
        else:
            print("❌ Model creation failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)