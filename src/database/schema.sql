-- PeteOllama Database Schema
-- SQLite3 database for AI Property Manager conversations and training

-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- Conversations table - stores all voice interactions
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT UNIQUE NOT NULL,
    user_id TEXT,
    agent_name TEXT DEFAULT 'Jamie',
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    status TEXT DEFAULT 'active',
    model_used TEXT,
    total_tokens INTEGER DEFAULT 0,
    response_time_ms INTEGER,
    quality_score REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Messages table - individual messages within conversations
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL,
    message_type TEXT NOT NULL, -- 'user', 'agent', 'system'
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    token_count INTEGER DEFAULT 0,
    thinking_process TEXT, -- AI reasoning/analysis
    confidence_score REAL DEFAULT 0.0,
    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id)
);

-- Training data table - high-quality conversations for model training
CREATE TABLE IF NOT EXISTS training_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL,
    quality_score REAL NOT NULL,
    training_status TEXT DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
    approved_by TEXT,
    approved_at TIMESTAMP,
    training_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id)
);

-- Models table - tracks available and trained models
CREATE TABLE IF NOT EXISTS models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    display_name TEXT,
    base_model TEXT,
    model_type TEXT DEFAULT 'base', -- 'base', 'jamie', 'custom'
    file_path TEXT,
    size_mb REAL,
    parameters JSON, -- model parameters as JSON
    is_active BOOLEAN DEFAULT 1,
    show_in_ui BOOLEAN DEFAULT 1,
    auto_preload BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Model performance metrics
CREATE TABLE IF NOT EXISTS model_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL,
    conversation_id TEXT NOT NULL,
    response_time_ms INTEGER,
    token_count INTEGER,
    quality_score REAL,
    user_feedback TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (model_name) REFERENCES models(name),
    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id)
);

-- System settings and configuration
CREATE TABLE IF NOT EXISTS system_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key TEXT UNIQUE NOT NULL,
    setting_value TEXT,
    setting_type TEXT DEFAULT 'string', -- 'string', 'number', 'boolean', 'json'
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Analytics and reporting data
CREATE TABLE IF NOT EXISTS analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    metric_value REAL,
    metric_unit TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    context JSON -- additional context as JSON
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_start_time ON conversations(start_time);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_training_data_quality ON training_data(quality_score);
CREATE INDEX IF NOT EXISTS idx_models_active ON models(is_active);
CREATE INDEX IF NOT EXISTS idx_model_metrics_model ON model_metrics(model_name);

-- Insert default system settings
INSERT OR IGNORE INTO system_settings (setting_key, setting_value, setting_type, description) VALUES
('default_model', 'jamie:latest', 'string', 'Default model to use for conversations'),
('max_response_time', '30000', 'number', 'Maximum response time in milliseconds'),
('quality_threshold', '0.7', 'number', 'Minimum quality score for training data'),
('training_conversation_limit', '100', 'number', 'Maximum conversations to use for training'),
('auto_preload_models', 'true', 'boolean', 'Automatically preload models on startup'),
('enable_analytics', 'true', 'boolean', 'Enable analytics collection'),
('database_version', '1.0.0', 'string', 'Current database schema version');

-- Insert default models
INSERT OR IGNORE INTO models (name, display_name, base_model, model_type, is_active, show_in_ui) VALUES
('llama3:8b', 'Llama 3 (8B)', 'llama3:8b', 'base', 1, 1),
('llama3:70b', 'Llama 3 (70B)', 'llama3:70b', 'base', 1, 1),
('jamie:latest', 'Jamie AI (Latest)', 'llama3:8b', 'jamie', 1, 1),
('jamie:property', 'Jamie Property Expert', 'llama3:8b', 'jamie', 1, 1);
