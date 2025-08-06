# Ollama Modelfile Creation Rules for PeteOllama Property Management Agent

## Overview
This document defines the rules and standards for creating proper Ollama Modelfiles that ingest conversation data from our pete.db database for training custom property management AI models.

## Core Principles

### 1. Modelfile Structure (REQUIRED)
```
FROM <base_model>
SYSTEM <system_prompt>
PARAMETER <key> <value>
TEMPLATE <template_definition>
MESSAGE user <example_user_input>
MESSAGE assistant <example_assistant_response>
```

### 2. Base Model Selection
- **Primary**: `llama3:latest` (available locally)
- **Secondary**: `mistral:7b-instruct-q4_K_M` (if available)
- **Fallback**: Any available model from `ollama list`

### 3. System Prompt Requirements
```
SYSTEM """You are PeteOllama, an expert AI property manager with extensive experience in:
- Tenant communications and relations
- Property maintenance coordination  
- Lease management and renewals
- Financial calculations and rent collection
- Real estate market knowledge
- Legal compliance and documentation

You have been trained on 1,469 real property management phone conversations and understand:
- Common tenant concerns and questions
- Professional communication standards
- Property management best practices
- Emergency vs. routine maintenance prioritization
- Payment issues and late fee management
- Move-in/move-out coordination

Always respond professionally, helpfully, and with practical solutions.
Prioritize urgent issues (AC outages, plumbing emergencies) over routine requests.
Provide clear next steps and contact information when appropriate.
"""
```

### 4. Parameter Configuration
```
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1
PARAMETER num_ctx 8192
```

### 5. Template Definition
```
TEMPLATE """{{ if .System }}{{ .System }}

{{ end }}{{ if .Prompt }}Human: {{ .Prompt }}

{{ end }}Assistant: {{ .Response }}"""
```

### 6. Training Examples Format
Use MESSAGE pairs instead of embedded examples:
```
MESSAGE user "Hi, my air conditioning isn't working and I have a baby in the house. When can someone come fix it?"
MESSAGE assistant "I'm so sorry to hear about your AC issue, especially with a baby at home. This is definitely a priority emergency. I'll dispatch our maintenance team immediately - they should contact you within the next hour to schedule same-day service. In the meantime, if you have any fans or need temporary cooling solutions, please let me know. I'll personally follow up to ensure this gets resolved today. Can you confirm your address and the best number to reach you?"
```

## Database Integration Rules

### 1. Data Source Requirements
- **Database**: `pete.db` (SQLite)
- **Table**: `communication_logs`
- **Required Fields**: `Transcription`, `Incoming`, `CreationDate`, `Data`
- **Minimum Records**: 10+ conversations for basic training
- **Optimal Records**: 100+ conversations for comprehensive training

### 2. Conversation Selection Criteria
```sql
SELECT Transcription, Incoming, Data, CreationDate 
FROM communication_logs 
WHERE Transcription IS NOT NULL 
AND LENGTH(Transcription) > 50
AND Transcription NOT LIKE '%Welcome to OG&E%'  -- Filter out non-property calls
AND Transcription NOT LIKE '%Thank you for calling%'  -- Filter out automated messages
ORDER BY CreationDate DESC
LIMIT 20
```

### 3. Data Processing Rules
- **Clean Transcriptions**: Remove automated message prefixes
- **Extract Key Scenarios**: Maintenance, rent, complaints, emergencies
- **Anonymize**: Replace specific names with "Tenant" or "Property Manager"
- **Preserve Context**: Keep property addresses for authenticity
- **Categorize**: Group by issue type (AC, plumbing, rent, etc.)

### 4. Example Generation Rules
- **Minimum**: 10 MESSAGE pairs
- **Maximum**: 30 MESSAGE pairs (to avoid token limits)
- **Diversity**: Cover all major property management scenarios
- **Quality**: Each example should demonstrate proper response patterns
- **Length**: User messages 50-300 characters, Assistant responses 100-500 characters

## Python Agent Implementation Rules

### 1. ModelFile Generator Class Structure
```python
class PropertyManagementModelfileGenerator:
    def __init__(self, db_path: str, base_model: str = "llama3:latest"):
        self.db_path = db_path
        self.base_model = base_model
        self.conversations = []
        
    def extract_conversations(self) -> List[Dict]:
        """Extract and clean conversations from pete.db"""
        
    def categorize_conversations(self) -> Dict[str, List]:
        """Group conversations by type (maintenance, rent, etc.)"""
        
    def generate_message_pairs(self) -> List[Tuple[str, str]]:
        """Create user/assistant MESSAGE pairs"""
        
    def create_modelfile(self) -> str:
        """Generate complete Modelfile content"""
        
    def save_and_create_model(self, model_name: str) -> bool:
        """Save Modelfile and create Ollama model"""
```

### 2. Conversation Processing Pipeline
1. **Extract**: Pull raw conversations from database
2. **Filter**: Remove automated/irrelevant messages  
3. **Clean**: Standardize format and remove PII
4. **Categorize**: Group by issue type
5. **Select**: Choose diverse representative examples
6. **Format**: Convert to MESSAGE pairs
7. **Generate**: Create complete Modelfile
8. **Create**: Execute `ollama create` command

### 3. Quality Assurance Rules
- **Validate Syntax**: Check Modelfile before creation
- **Test Examples**: Ensure MESSAGE pairs are properly formatted
- **Verify Model**: Test created model with sample queries
- **Performance Check**: Measure response quality vs. base model

### 4. Error Handling Requirements
- **Missing Database**: Graceful fallback to basic Modelfile
- **Insufficient Data**: Minimum viable Modelfile with generic examples
- **Ollama Errors**: Retry with alternative base models
- **Syntax Errors**: Validate and fix before model creation

## Conversation Categories and Patterns

### 1. Emergency Maintenance (High Priority)
- **Keywords**: "AC", "air conditioning", "heating", "plumbing", "leak", "emergency"
- **Response Pattern**: Immediate acknowledgment + same-day service + personal follow-up
- **Example Count**: 4-6 MESSAGE pairs

### 2. Routine Maintenance (Standard Priority)  
- **Keywords**: "repair", "fix", "maintenance", "door", "window", "garbage disposal"
- **Response Pattern**: Professional assessment + timeline + cost estimate
- **Example Count**: 3-4 MESSAGE pairs

### 3. Rent/Payment Issues
- **Keywords**: "rent", "payment", "late", "fee", "due", "paycheck"
- **Response Pattern**: Understanding + flexible solutions + clear expectations
- **Example Count**: 3-4 MESSAGE pairs

### 4. Move-in/Move-out Coordination
- **Keywords**: "move", "lockbox", "keys", "transfer", "new", "lease"
- **Response Pattern**: Clear processes + timelines + contact information
- **Example Count**: 2-3 MESSAGE pairs

### 5. Account/Administrative
- **Keywords**: "account", "verification", "information", "update", "contact"
- **Response Pattern**: Verification + information gathering + follow-up
- **Example Count**: 2-3 MESSAGE pairs

## Implementation Specifications

### 1. File Naming Convention
- **Modelfile**: `models/Modelfile.property-manager`
- **Model Name**: `peteollama:property-manager-v{timestamp}`
- **Backup**: `models/backups/Modelfile.{timestamp}.bak`

### 2. Integration Points
- **Database Manager**: Extend `PeteDBManager` with conversation extraction
- **Model Manager**: Enhance `ModelManager` with Modelfile generation
- **Admin Interface**: Add "Generate Enhanced Model" endpoint
- **CLI Tool**: Create standalone training script

### 3. Success Metrics
- **Data Coverage**: >80% of conversation categories represented
- **Response Quality**: Maintains professional tone and accuracy
- **Context Retention**: Demonstrates property management knowledge
- **Performance**: <3 second response time for typical queries

### 4. Deployment Process
1. Extract conversations from pete.db
2. Generate enhanced Modelfile with MESSAGE pairs
3. Create new model version with timestamp
4. Test model performance with validation set
5. Update system to use new model
6. Archive previous model version

## Example Implementation Flow
```python
# 1. Initialize generator
generator = PropertyManagementModelfileGenerator("pete.db")

# 2. Extract and process conversations
conversations = generator.extract_conversations()
categorized = generator.categorize_conversations()

# 3. Generate MESSAGE pairs
message_pairs = generator.generate_message_pairs()

# 4. Create enhanced Modelfile
modelfile_content = generator.create_modelfile()

# 5. Deploy new model
success = generator.save_and_create_model("peteollama:property-manager-enhanced")
```

This approach leverages your existing 1,469 conversations to create a truly trained property management AI while maintaining compatibility with your current architecture.