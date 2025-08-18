-- Jamie Database Initialization Script
-- Creates necessary tables for conversation logging and analytics

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Conversations table for logging all interactions
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255),
    user_message TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    model_used VARCHAR(100),
    response_time_ms INTEGER,
    tokens_used INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for better query performance
CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at);
CREATE INDEX IF NOT EXISTS idx_conversations_model_used ON conversations(model_used);

-- VAPI call logs table
CREATE TABLE IF NOT EXISTS vapi_calls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    call_id VARCHAR(255) UNIQUE,
    phone_number VARCHAR(50),
    call_type VARCHAR(50), -- 'inbound', 'outbound'
    call_status VARCHAR(50), -- 'started', 'ended', 'failed'
    duration_seconds INTEGER,
    conversation_id UUID REFERENCES conversations(id),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vapi_calls_call_id ON vapi_calls(call_id);
CREATE INDEX IF NOT EXISTS idx_vapi_calls_phone_number ON vapi_calls(phone_number);

-- User sessions table for tracking user interactions
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    conversation_count INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_user_sessions_session_id ON user_sessions(session_id);

-- Analytics summary table (for dashboard)
CREATE TABLE IF NOT EXISTS analytics_summary (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    date_bucket DATE NOT NULL,
    total_conversations INTEGER DEFAULT 0,
    total_tokens_used INTEGER DEFAULT 0,
    avg_response_time_ms NUMERIC(10,2),
    unique_sessions INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_analytics_summary_date ON analytics_summary(date_bucket);

-- Function to update analytics summary daily
CREATE OR REPLACE FUNCTION update_analytics_summary()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO analytics_summary (date_bucket, total_conversations, total_tokens_used, avg_response_time_ms, unique_sessions)
    SELECT 
        CURRENT_DATE,
        COUNT(*),
        SUM(COALESCE(tokens_used, 0)),
        AVG(COALESCE(response_time_ms, 0)),
        COUNT(DISTINCT session_id)
    FROM conversations 
    WHERE DATE(created_at) = CURRENT_DATE
    ON CONFLICT (date_bucket) DO UPDATE SET
        total_conversations = EXCLUDED.total_conversations,
        total_tokens_used = EXCLUDED.total_tokens_used,
        avg_response_time_ms = EXCLUDED.avg_response_time_ms,
        unique_sessions = EXCLUDED.unique_sessions;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update analytics on new conversations
CREATE TRIGGER update_analytics_trigger
    AFTER INSERT ON conversations
    FOR EACH STATEMENT EXECUTE FUNCTION update_analytics_summary();

-- Insert some sample data for testing (optional)
INSERT INTO conversations (session_id, user_message, ai_response, model_used, response_time_ms, tokens_used)
VALUES 
    ('test-session-1', 'Hello Jamie, how are you?', 'Hello! I''m doing well, thank you for asking. How can I help you with your property management needs today?', 'jamie-v2', 1200, 45),
    ('test-session-1', 'Tell me about rent collection', 'I can help you with rent collection! Here are some best practices...', 'jamie-v2', 2100, 89)
ON CONFLICT DO NOTHING;
