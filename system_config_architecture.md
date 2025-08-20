# System Configuration Architecture

## Configuration Hierarchy & Flow

```mermaid
graph TB
    %% Top Level Configuration
    subgraph "🔧 System Configuration Manager"
        SC[SystemConfig]
        SC --> GC[Global Caching]
        SC --> PS[Provider Settings]
        SC --> MS[Model Settings]
        SC --> SS[System Settings]
    end
    
    %% Global Caching Configuration
    subgraph "🌐 Global Caching (Highest Priority)"
        GC --> GC_EN[enabled: true]
        GC --> GC_TH[threshold: 0.75]
        GC --> GC_AGE[max_age: 24h]
        GC --> GC_SIM[similarity_analyzer: true]
        GC --> GC_FB[fallback_cache: true]
    end
    
    %% Provider Level Configuration
    subgraph "🚀 Provider Level (Medium Priority)"
        PS --> OR[OpenRouter]
        PS --> RP[RunPod]
        PS --> OL[Ollama]
        
        OR --> OR_C[OR Caching Config]
        RP --> RP_C[RP Caching Config]
        OL --> OL_C[OL Caching Config]
        
        OR_C --> OR_EN[enabled: true]
        OR_C --> OR_TH[threshold: 0.80]
        OR_C --> OR_AGE[max_age: 24h]
        
        RP_C --> RP_EN[enabled: false]
        RP_C --> RP_TH[threshold: 0.70]
        RP_C --> RP_AGE[max_age: 12h]
        
        OL_C --> OL_EN[enabled: true]
        OL_C --> OL_TH[threshold: 0.75]
        OL_C --> OL_AGE[max_age: 48h]
    end
    
    %% Model Level Configuration
    subgraph "🤖 Model Level (Lowest Priority)"
        MS --> GPT35[openai/gpt-3.5-turbo]
        MS --> CLAUDE[anthropic/claude-3-haiku]
        MS --> LLAMA[llama3:latest]
        
        GPT35 --> GPT35_C[GPT-3.5 Caching]
        CLAUDE --> CLAUDE_C[Claude Caching]
        LLAMA --> LLAMA_C[Llama Caching]
        
        GPT35_C --> GPT35_TH[threshold: 0.90]
        GPT35_C --> GPT35_TOK[max_tokens: 2048]
        
        CLAUDE_C --> CLAUDE_TH[threshold: 0.85]
        CLAUDE_C --> CLAUDE_TOK[max_tokens: 4000]
        
        LLAMA_C --> LLAMA_EN[enabled: false]
        LLAMA_C --> LLAMA_TOK[max_tokens: 4096]
    end
    
    %% Configuration Flow
    subgraph "🔄 Configuration Resolution Flow"
        REQ[User Request]
        REQ --> CHECK_CACHE{Check Cache?}
        
        CHECK_CACHE -->|Yes| GET_CONFIG[Get Caching Config]
        GET_CONFIG --> MERGE[Merge Configs]
        
        MERGE --> GLOBAL[Start with Global]
        GLOBAL --> PROVIDER[Override with Provider]
        PROVIDER --> MODEL[Override with Model]
        
        MODEL --> FINAL[Final Caching Config]
        FINAL --> EXECUTE[Execute Caching Logic]
        
        CHECK_CACHE -->|No| DIRECT[Direct to Provider]
    end
    
    %% Admin API Interface
    subgraph "🛠️ Admin API Interface"
        ADMIN[Admin Dashboard]
        ADMIN --> GET[GET /admin/system-config]
        ADMIN --> UPDATE_GC[PUT /admin/system-config/global-caching]
        ADMIN --> UPDATE_PROV[PUT /admin/system-config/providers/{name}]
        ADMIN --> UPDATE_MODEL[PUT /admin/system-config/models/{name}]
        ADMIN --> UPDATE_SYS[PUT /admin/system-config/system]
        ADMIN --> RESET[POST /admin/system-config/reset]
        ADMIN --> EXPORT[GET /admin/system-config/export]
    end
    
    %% Integration Points
    subgraph "🔗 System Integration"
        INT[ModelManager]
        INT --> USE_CONFIG[Use System Config]
        USE_CONFIG --> CACHE_DECISION[Cache Decision]
        
        CACHE_DECISION --> SIMILARITY[Similarity Analyzer]
        CACHE_DECISION --> FALLBACK[Fallback Cache]
        CACHE_DECISION --> PROVIDER[Provider Call]
    end
    
    %% Styling
    classDef configBox fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef priorityBox fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef flowBox fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef apiBox fill:#fff3e0,stroke:#e65100,stroke-width:2px
    
    class SC,GC,PS,MS configBox
    class GC_EN,GC_TH,GC_AGE,GC_SIM,GC_FB priorityBox
    class REQ,CHECK_CACHE,GET_CONFIG,MERGE,GLOBAL,PROVIDER,MODEL,FINAL,EXECUTE flowBox
    class ADMIN,GET,UPDATE_GC,UPDATE_PROV,UPDATE_MODEL,UPDATE_SYS,RESET,EXPORT apiBox
```

## Configuration Priority Rules

### 1. **Global Level** (Highest Priority)
- Controls system-wide caching behavior
- Sets default values for all providers and models
- Can be overridden by provider or model settings

### 2. **Provider Level** (Medium Priority)
- Overrides global settings for specific providers
- Allows provider-specific caching policies
- Examples:
  - **OpenRouter**: High threshold (0.80), long cache age (24h)
  - **RunPod**: No caching (enabled: false)
  - **Ollama**: Medium threshold (0.75), long cache age (48h)

### 3. **Model Level** (Lowest Priority)
- Overrides provider settings for specific models
- Allows fine-grained control per model
- Examples:
  - **GPT-3.5**: Very high threshold (0.90), standard cache age
  - **Claude**: High threshold (0.85), short cache age (12h)
  - **Llama**: No caching (enabled: false)

## Configuration Flow Example

```
User Request → Check Cache? → Get Caching Config → Merge Configs → Execute

1. Start with Global: enabled=true, threshold=0.75
2. Override with Provider: threshold=0.80 (OpenRouter)
3. Override with Model: threshold=0.90 (GPT-3.5)
4. Final Config: enabled=true, threshold=0.90
```

## Key Benefits

✅ **Centralized Control**: All settings in one place  
✅ **Hierarchical Overrides**: Top-down control with bottom-up customization  
✅ **Provider Flexibility**: Different caching policies per provider  
✅ **Model Granularity**: Fine-tuned control per model  
✅ **Admin Interface**: Full control through API endpoints  
✅ **Real-time Updates**: Changes take effect immediately  
✅ **Export/Import**: Backup and restore configurations  

## Usage Examples

### Disable Caching for RunPod
```json
{
  "caching": {
    "enabled": false
  }
}
```

### Set High Threshold for Premium Models
```json
{
  "caching": {
    "threshold": 0.90,
    "max_cache_age_hours": 12
  }
}
```

### Global Caching Policy
```json
{
  "global_caching": {
    "enabled": true,
    "threshold": 0.75,
    "max_cache_age_hours": 24
  }
}
```
