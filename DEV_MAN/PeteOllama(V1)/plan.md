# PeteOllama V1 - STREAMLINED Property Manager Plan

## 🎯 **FOCUSED OBJECTIVE**

Train Qwen 2.5 7B on **real property management phone calls** from your existing database, then connect to VAPI for intelligent voice responses. **Simple and focused.**

### **Core Strategy**

1. Use **existing phone call data** from prod-db (extract_jamie_data.py)
2. Train model on **real conversations** - not synthetic data
3. Deploy via **VAPI** for voice interactions
4. **Minimal complexity** - build only what's needed

---

## 📋 **SIMPLE ARCHITECTURE**

```
   Real Phone Calls     Train Model        Voice Interface
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   pete.db       │───▶│ Qwen 2.5 7B  │───▶│   VAPI Voice    │
│ (conversation   │    │ Custom Model │    │   Calls         │
│  transcripts)   │    │ (trained)    │    │                 │
└─────────────────┘    └──────────────┘    └─────────────────┘
         ▲                       │                       │
         │                       ▼                       │
┌─────────────────┐    ┌──────────────────┐             │
│   prod-db       │    │  Docker Ollama   │◀────────────┘
│ (phone calls)   │    │   Container      │
└─────────────────┘    └──────────────────┘
```

---

## 🛠️ Technology Stack

### **AI & Language Models**

- **Base Model**: Qwen 2.5 7B (128K context window)
- **Platform**: Ollama (Docker containerized)
- **Custom Model**: Property management fine-tuned version
- **Context Window**: 128,000 tokens (~400 pages of text)

### **Voice Integration**

- **Voice API**: VAPI for real-time voice interactions
- **Communication**: RESTful API integration
- **Real-time**: Voice-to-text and text-to-voice processing

### **Database & Storage**

- **Primary DB**: PostgreSQL 17 (Docker container)
- **Data Persistence**: Named Docker volumes
- **Connection**: Database accessible at `localhost:5432`

### **Infrastructure**

- **Containerization**: Docker Compose
- **Network**: Custom bridge network (`ollama_postgres_network`)
- **Environment**: macOS Darwin 24.5.0
- **Package Management**: UV CLI

### **Development Environment**

- **Shell**: ZSH
- **Python Runtime**: UV managed Python environment
- **Environment Variables**: `.env` file with python-dotenv

---

## 🗂️ **SIMPLE PROJECT STRUCTURE**

```
ollama_agent/
├── extract_jamie_data.py          # Extract training data (EXISTS)
├── pete.db                        # Training database (CREATED BY SCRIPT)
├── docker-compose.yml             # Ollama container (EXISTS)
├── .env                          # Basic config (EXISTS)
├── train_model.py                # Train on pete.db (TO BUILD)
├── vapi_webhook.py               # VAPI integration (TO BUILD)
├── Modelfile                     # Custom model definition (TO BUILD)
└── DEV_MAN/PeteOllama(V1)/plan.md # This plan (REFACTORED)
```

**That's it!** No complex folder structures or overengineered classes.

---

## 🏢 Property Management Capabilities

### **Core Functions**

- **Tenant Communication**: Handle inquiries, complaints, and requests
- **Financial Analysis**: Rent calculations, expense tracking, ROI analysis
- **Maintenance Coordination**: Schedule repairs, track work orders
- **Lease Management**: Review terms, renewal processing, compliance
- **Property Analytics**: Market analysis, performance reporting
- **Documentation**: Generate reports, maintain records

### **Knowledge Areas**

- Real estate regulations and compliance
- Financial calculations and reporting
- Property maintenance procedures
- Tenant relations and communication
- Market analysis and trends
- Legal compliance and documentation

---

## 🐳 Docker Configuration

### **Services Running**

- **Ollama Container**: AI model serving on port `11435`
- **PostgreSQL Container**: Database on port `5432`
- **Named Volumes**: `ollama_data`, `postgres_data`
- **Custom Network**: `ollama_postgres_network`

### **Database Configuration**

```env
DB_USER=pete
DB_PASSWORD=jonihbuyers
DB_NAME=peteollama
```

### **Resource Allocation**

- **Ollama**: 4GB memory limit, 2GB reserved
- **PostgreSQL**: 2GB memory limit, 1GB reserved

---

## 📊 Database Schema Design

### **Core Tables**

```sql
-- Conversations: Store all voice interactions
conversations (
    id, timestamp, vapi_call_id, duration,
    transcript, ai_response, sentiment_score
)

-- Properties: Property information and details
properties (
    id, address, type, owner_id,
    lease_details, financial_data, maintenance_history
)

-- Tenants: Tenant information and history
tenants (
    id, name, contact_info, property_id,
    lease_start, lease_end, payment_history
)

-- Interactions: Track all property-related interactions
interactions (
    id, conversation_id, property_id, tenant_id,
    interaction_type, outcome, follow_up_required
)

-- Model_Performance: Track AI accuracy and improvements
model_performance (
    id, conversation_id, accuracy_score,
    feedback, improvement_suggestions
)
```

---

## 🔄 Development Phases

### **Phase 1: Extract Training Data** (Ready!)

- [x] Docker Ollama setup (port 11435)
- [x] Base model selected (Qwen 2.5 7B)
- [x] Data extraction script exists (`extract_jamie_data.py`)
- [ ] Run extraction → create `pete.db`

### **Phase 2: Train Custom Model**

- [ ] Download Qwen 2.5 7B base model
- [ ] Create simple training script
- [ ] Build Modelfile for property management
- [ ] Train on phone conversation data
- [ ] Test model responses

### **Phase 3: VAPI Integration**

- [ ] VAPI account setup
- [ ] Simple webhook endpoint
- [ ] Connect trained model to voice
- [ ] Test end-to-end voice calls

### **Phase 4: Simple Database Context** (Future)

- [ ] Basic pete.db queries for context
- [ ] Conversation history lookup
- [ ] Property information retrieval

**NO COMPLEX FEATURES YET** - Keep it simple!

---

## 🎯 Success Metrics

### **Performance Targets**

- **Response Time**: < 2 seconds for voice interactions
- **Context Retention**: Handle 100+ page documents in conversation
- **Accuracy**: > 90% correct responses for property queries
- **Availability**: 99.9% uptime for voice system

### **Business Metrics**

- **Tenant Satisfaction**: Measured through interaction feedback
- **Efficiency Gains**: Reduced manual property management tasks
- **Cost Savings**: Automated routine inquiries and processes
- **Scalability**: Support for multiple properties and tenants

---

## 🔧 Configuration Files

### **Environment Variables** (`.env`)

```env
# Database Configuration
DB_USER=pete
DB_PASSWORD=jonihbuyers
DB_NAME=peteollama

# VAPI Configuration (to be added)
VAPI_API_KEY=your_vapi_key_here
VAPI_PHONE_NUMBER=your_phone_number

# Ollama Configuration
OLLAMA_HOST=localhost:11435
OLLAMA_MODEL=peteollama:property-manager
```

### **Docker Compose** (`docker-compose.yml`)

- Ollama service on custom port `11435`
- PostgreSQL with health checks
- Named volumes for data persistence
- Custom network for service communication

---

## 🚀 Quick Start Commands

### **Start the Environment**

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### **Model Management**

```bash
# Download base model
docker exec -it ollama ollama pull qwen2.5:7b

# Create custom model (future)
docker exec -it ollama ollama create peteollama:property-manager -f ./Modelfile

# Test model
docker exec -it ollama ollama run qwen2.5:7b
```

### **Database Access**

```bash
# Connect to PostgreSQL
docker exec -it postgres psql -U pete -d peteollama

# Run SQL scripts
docker exec -i postgres psql -U pete -d peteollama < schema.sql
```

---

## 📝 Next Immediate Actions

1. **Complete Model Download**: Finish downloading Qwen 2.5 7B
2. **Database Schema**: Create PostgreSQL tables for properties and conversations
3. **Basic Testing**: Verify model responses for property management queries
4. **VAPI Setup**: Configure voice API integration
5. **Custom Model Creation**: Begin property management fine-tuning

---

## 📚 Additional Resources

- **Ollama Documentation**: https://ollama.com/docs
- **VAPI Documentation**: https://vapi.ai/docs
- **Qwen 2.5 Model Details**: https://ollama.com/library/qwen2.5
- **PostgreSQL 17 Docs**: https://www.postgresql.org/docs/17/

---

**Version**: 1.0  
**Last Updated**: January 2025  
**Project Lead**: Pete  
**Status**: In Development - Phase 1 Complete
