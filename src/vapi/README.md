# VAPI Modular Server

This directory contains the modularized version of the VAPI webhook server, extracted from the original monolithic `webhook_server.py`.

## 🏗️ Structure

```
vapi/
├── README.md                    # This file
├── modular_server.py           # Main modular server (replaces webhook_server.py)
├── api/                        # API routers
│   ├── __init__.py
│   ├── vapi_router.py         # VAPI webhook endpoints
│   ├── admin_router.py        # Admin dashboard endpoints
│   └── ui_router.py           # UI endpoints (serves existing frontend)
├── models/                     # Pydantic models
│   ├── __init__.py
│   └── webhook_models.py      # VAPI request/response models
└── services/                   # Business logic services
    ├── __init__.py
    └── provider_service.py    # AI provider management
```

## 🚀 Quick Start

### Run the Modular Server

```bash
# From the src/ directory
cd vapi
python modular_server.py

# Or with options
python modular_server.py --host 0.0.0.0 --port 8000 --debug
```

### Available Endpoints

- **🏠 Root**: http://localhost:8000/ (redirects to UI)
- **💬 Main UI**: http://localhost:8000/ui (serves existing `frontend/html/main-ui.html`)
- **🔧 Admin Dashboard**: http://localhost:8000/admin (serves existing `frontend/html/admin-ui.html`)
- **🤖 VAPI Webhooks**: http://localhost:8000/vapi/*
- **❤️ Health Check**: http://localhost:8000/health

## 📁 Frontend Integration

The modular server **uses the existing frontend files** from `frontend/`:
- **Main UI**: `frontend/html/main-ui.html` → `/ui`
- **Admin UI**: `frontend/html/admin-ui.html` → `/admin`
- **CSS/JS**: Automatically served from `frontend/css/` and `frontend/js/`
- **Assets**: `public/` directory mounted as `/public/`

No new HTML templates were created - the server serves your existing, feature-rich frontend.

## 🔧 Key Features

### Separation of Concerns
- **Models**: Pydantic models for request/response validation
- **Services**: Business logic (provider management, model handling)
- **Routers**: HTTP endpoint handling with clean separation
- **Main Server**: Coordinates everything together

### Router Modules
1. **VAPI Router** (`vapi_router.py`):
   - `/vapi/personas` - Model listing
   - `/vapi/chat/completions` - OpenAI-compatible chat
   - `/vapi/webhook` - VAPI webhook handling
   - `/vapi/test/*` - Testing endpoints

2. **Admin Router** (`admin_router.py`):
   - `/admin/` - Dashboard (existing admin-ui.html)
   - `/admin/status` - System status
   - `/admin/models` - Model management
   - `/admin/config` - Configuration
   - `/admin/logs` - Log viewing

3. **UI Router** (`ui_router.py`):
   - `/ui` - Main chat interface (existing main-ui.html)
   - `/personas` - UI model listing
   - `/chat` - UI chat endpoint
   - `/switch-provider` - Provider switching

### Services
- **Provider Service**: Handles Ollama, OpenRouter, and RunPod integration
- **Model Management**: Abstracted through ModelManager dependency

## 🔄 Migration from Monolithic Server

### What Changed
1. **Extracted** HTML content → Uses existing `frontend/` files
2. **Separated** routes → Individual router modules
3. **Extracted** models → `models/webhook_models.py`
4. **Created** services → `services/provider_service.py`
5. **Simplified** main server → Clean coordination

### What Stayed the Same
- **All existing functionality** preserved
- **Same endpoints** and behavior
- **Existing frontend** files used as-is
- **Same database/logging** integration points

### Benefits
- ✅ **Cleaner code** - Easier to maintain and understand
- ✅ **Better testability** - Each module can be tested independently
- ✅ **Easier development** - Multiple developers can work on different modules
- ✅ **Reusable components** - Services and models can be imported elsewhere
- ✅ **Frontend preservation** - Your existing, sophisticated UI remains intact

## 🔗 Dependencies

The modular server maintains the same dependencies as the original:
- FastAPI
- Pydantic
- All existing model and AI integrations
- Existing `utils/`, `ai/`, `config/` modules

## 🧪 Testing

```bash
# Test the modular server
python modular_server.py --debug

# Test individual components
python -c "from vapi.services.provider_service import ProviderService; print('✅ Services work')"
python -c "from vapi.models.webhook_models import VAPIChatRequest; print('✅ Models work')"
```

## 🎯 Next Steps

1. **Replace** the original `webhook_server.py` usage with `modular_server.py`
2. **Add tests** for individual router modules
3. **Extend services** with additional business logic
4. **Create shared components** for common UI elements
5. **Add middleware** for logging, authentication, etc.

This modular structure preserves all your existing functionality while making the codebase much more maintainable and extensible! 🎉
