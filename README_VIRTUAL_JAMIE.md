# Virtual Jamie.V1 - Ollama Property Management Agent

## 🏠 Overview

Virtual Jamie.V1 is an AI-powered property management assistant built using Ollama. This system extracts real communication logs from your production database to train an intelligent agent that understands property management conversations.

## 🎯 Purpose

Train an AI agent to handle property management tasks by learning from actual phone conversations, tenant interactions, and property-related communications.

## 📁 Files in this Directory

### Core Extraction System

- **`virtual_jamie_extractor.py`** - Main data extraction module
- **`extract_jamie_data.py`** - Simple runner script
- **`pete.db`** - SQLite training database (created after extraction)

### Existing Ollama Setup

- **`setup_database.py`** - Original Ollama database setup
- **`src/database/connection.py`** - Database connection utilities
- **`requirements.txt`** - Python dependencies
- **`docker-compose.yml`** - Ollama containerization

## 🚀 Quick Start

### 1. Extract Training Data

```bash
cd /Users/markcarpenter/Desktop/pete/ollama_agent
python extract_jamie_data.py
```

### 2. What Gets Extracted

The system pulls communication logs with these criteria:

- **Company ID**: 1
- **User ID**: 6 (property manager)
- **Communication Type**: 3 (phone calls)
- **Duration**: >15 seconds
- **Excludes**: Internal number +14052752322
- **Requires**: Transcription data available

### 3. Database Structure

After extraction, `pete.db` contains:

**📋 Tables:**

- `communication_logs` - Raw conversation data
- `extraction_metadata` - Extraction details and source info
- `training_summary` - Statistics about the training data

**📊 Data Fields:**

- `Incoming` - Call direction (incoming/outgoing)
- `Data` - Call metadata and context
- `CreationDate` - When the conversation occurred
- `Transcription` - Full conversation transcript
- `TranscriptionJson` - Structured conversation data

## 🤖 Training Virtual Jamie.V1

### What Jamie Learns From:

- **Real Property Management Calls** - Actual conversations with tenants
- **Problem Resolution Patterns** - How issues are typically handled
- **Communication Tone** - Professional property management language
- **Common Scenarios** - Rent questions, maintenance requests, lease issues

### Training Data Quality:

- ✅ Real conversations (not synthetic)
- ✅ Properly transcribed phone calls
- ✅ Property management context preserved
- ✅ Quality filtered (>15 second duration)

## 📊 Database Integration

### Connection to Production

- Uses existing `pete_db/PeteDbWorkspace/.env` credentials
- Read-only access to `prod-db`
- Connects to Azure SQL Server instance
- No modifications to production data

### Local Training Database

- SQLite format for easy integration with Ollama
- Self-contained training dataset
- Metadata tracking for model versioning
- Ready for machine learning workflows

## 🛠️ Development Workflow

### 1. Data Extraction

```bash
python extract_jamie_data.py
```

### 2. Ollama Model Training

```bash
# Use pete.db with your Ollama training pipeline
# Train on property management conversations
# Focus on tenant communication patterns
```

### 3. Agent Deployment

```bash
# Deploy trained Virtual Jamie.V1
# Integrate with property management systems
# Handle tenant communications automatically
```

## 📋 Logging and Monitoring

### Extraction Logs

- **Location**: `logs/virtual_jamie_extraction.log`
- **Rotation**: 5MB files, 10 days retention
- **Content**: Extraction progress, data statistics, errors

### Log Contents:

- 📊 Number of records extracted
- 📅 Date range of conversations
- 📞 Call statistics (incoming/outgoing)
- 🎤 Transcription availability
- ✅ Success/failure status

## 🔧 Configuration

### Environment Setup

The `ollama_agent/.env` file contains all necessary configuration:

```env
# Production Database Configuration (for Virtual Jamie.V1 data extraction)
PROD_DB_HOST=prod-ihbsql.database.windows.net
PROD_DB_USERNAME=peteRO
PROD_DB_PASSWORD=1cFwi90Cz&51
PROD_DB_DATABASE=prod-db
PROD_DB_DRIVER=ODBC Driver 18 for SQL Server

# Local PostgreSQL (for Ollama conversations)
DB_USER=pete
DB_PASSWORD=jonihbuyers
DB_NAME=peteollama

# Ollama Configuration
OLLAMA_HOST=localhost:11435
OLLAMA_MODEL=qwen2.5:7b
JAMIE_CUSTOM_MODEL=peteollama:property-manager
```

### Database Connection

The system automatically loads credentials from the local `.env` file in the ollama_agent directory. This setup provides:

- **Production Data Access**: Read-only connection to extract training data
- **Local Database**: PostgreSQL for storing conversations and agent interactions
- **Self-Contained**: No dependencies on external configuration files

### Output Location

- **Default**: `ollama_agent/pete.db`
- **Format**: SQLite3 database
- **Purpose**: Training data for Virtual Jamie.V1

## 🎯 Use Cases for Virtual Jamie.V1

### Tenant Communications

- Answer common rent and lease questions
- Schedule maintenance appointments
- Provide property information
- Handle routine inquiries professionally

### Property Management Tasks

- Process maintenance requests
- Explain lease terms and policies
- Coordinate with vendors and contractors
- Manage tenant relations efficiently

### 24/7 Availability

- Handle after-hours tenant calls
- Provide consistent responses
- Escalate complex issues appropriately
- Maintain professional communication standards

## 📈 Next Steps

1. **Extract Data** - Run the extraction script
2. **Review Training Data** - Check pete.db contents
3. **Train with Ollama** - Use conversation data for model training
4. **Test Virtual Jamie** - Validate responses on sample scenarios
5. **Deploy Agent** - Integrate with property management workflow

---

**Virtual Jamie.V1** - Your AI Property Management Assistant 🏠🤖

_Trained on real conversations, ready to handle tenant communications with professional expertise._
