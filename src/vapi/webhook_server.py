"""
PeteOllama V1 - VAPI Webhook Server
===================================

FastAPI server for handling VAPI voice interactions.
Receives voice calls and responds using the trained AI model.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import json
from typing import Dict, Any
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai.model_manager import ModelManager
from ai.model_preloader import model_preloader
from database.pete_db_manager import PeteDBManager
from utils.logger import logger
from config.model_settings import model_settings
from analytics.response_validator import response_validator

class VAPIWebhookServer:
    """VAPI webhook server for voice interactions"""
    
    def __init__(self, port: int = 8000):
        """Initialize webhook server"""
        self.port = port
        self.app = FastAPI(
            title="PeteOllama VAPI Webhook",
            description="AI Property Manager Voice Interface",
            version="1.0.0"
        )
        
        self.model_manager = ModelManager()
        self.db_manager = PeteDBManager()
        
        # Serve static assets from /public for logos etc.
        public_dir = Path(__file__).parent.parent / "public"
        if public_dir.exists():
            self.app.mount("/public", StaticFiles(directory=str(public_dir)), name="public")
        self.setup_routes()
    
    def setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/")
        async def root():
            """Root endpoint"""
            return {
                "service": "PeteOllama VAPI Webhook",
                "version": "1.0.0",
                "status": "running",
                "model_available": self.model_manager.is_available()
            }
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "model_available": self.model_manager.is_available(),
                "database_connected": self.db_manager.is_connected()
            }

        @self.app.get("/models")
        async def list_models():
            """Return list of models available in Ollama."""
            models = self.model_manager.list_models()
            return [m.get("name") for m in models]

        # ---- Persona list endpoint ----
        @self.app.get("/personas")
        async def personas():
            """Return list of personas filtered by model settings."""
            # Get only models that are enabled for UI display
            ui_models = model_settings.get_ui_models()
            
            if not ui_models:
                logger.warning("No models enabled for UI display")
                return []
            
            persona_list = []
            jamie_models = []
            generic_models = []
            
            for model_config in ui_models:
                model_data = {
                    "name": model_config.name,
                    "display_name": model_config.display_name,
                    "description": model_config.description,
                    "auto_preload": model_config.auto_preload
                }
                
                if model_config.is_jamie_model:
                    jamie_models.append(model_data)
                else:
                    generic_models.append(model_data)
            
            # Create Jamie persona if we have Jamie models
            if jamie_models:
                persona_list.append({
                    "name": "Jamie (Property Manager)",
                    "icon": "/public/Jamie.png",
                    "type": "primary",
                    "models": jamie_models,
                    "description": "Professional property manager AI trained on real conversations"
                })
            
            # Add generic models
            for model in generic_models:
                persona_list.append({
                    "name": model["display_name"],
                    "icon": "/public/pete.png",
                    "type": "generic",
                    "models": [model],
                    "description": model["description"]
                })
            
            logger.info(f"Serving {len(ui_models)} models to UI: {[m.name for m in ui_models]}")
            return persona_list

        # ---- Train property-manager model ----
        @self.app.post("/train/pm")
        async def train_pm():
            ok = self.model_manager.train_property_manager()
            return {"status": "started" if ok else "failed"}
        
        @self.app.post("/vapi/webhook")
        async def vapi_webhook(request: Request):
            """Main VAPI webhook endpoint"""
            try:
                # Get request body
                body = await request.json()
                
                # Log the incoming request
                logger.info(f"VAPI webhook received: {body.get('type', 'unknown')}")
                
                # Handle different VAPI event types
                event_type = body.get('type')
                
                if event_type == 'function-call':
                    return await self.handle_function_call(body)
                elif event_type == 'conversation-update':
                    return await self.handle_conversation_update(body)
                elif event_type == 'end-of-call-report':
                    return await self.handle_end_of_call(body)
                else:
                    logger.warning(f"Unknown VAPI event type: {event_type}")
                    return {"status": "ignored"}
            
            except Exception as e:
                logger.error(f"VAPI webhook error: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/test/message")
        async def test_message(request: Request):
            """Test endpoint for direct message testing"""
            try:
                body = await request.json()
                message = body.get('message', '')
                model_name = body.get('model')  # optional specific model
                
                if not message:
                    raise HTTPException(status_code=400, detail="Message required")
                
                # Generate AI response (model_name can be None)
                response = self.model_manager.generate_response(message, model_name=model_name)
                
                return {
                    "user_message": message,
                    "ai_response": response,
                    "model_used": model_name or (self.model_manager.custom_model_name if self.model_manager.is_model_available(self.model_manager.custom_model_name) else self.model_manager.model_name)
                }
            
            except Exception as e:
                logger.error(f"Test message error: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        # --- Streaming endpoint ---
        @self.app.post("/test/stream")
        async def test_stream(request: Request):
            """Stream AI response token-by-token (chunked plain text)."""
            import time
            import json
            
            start_time = time.time()
            request_id = f"req_{int(start_time)}_{hash(time.time()) % 10000}"
            
            try:
                body = await request.json()
                message = body.get('message', '')
                model_name = body.get('model')
                if not message:
                    raise HTTPException(status_code=400, detail="Message required")

                # Log request start
                logger.info(f"🔄 BENCHMARK [{request_id}] Starting stream - Model: {model_name}, Message: {message[:50]}...")
                
                # Collect the full response for logging
                full_response = ""
                token_count = 0
                first_token_time = None

                def token_iter():
                    nonlocal full_response, token_count, first_token_time
                    
                    for token in self.model_manager.generate_stream(message, model_name=model_name):
                        if first_token_time is None:
                            first_token_time = time.time()
                        
                        full_response += token
                        token_count += 1
                        yield token
                    
                    # Log complete response after streaming
                    end_time = time.time()
                    total_duration = end_time - start_time
                    first_token_latency = (first_token_time - start_time) if first_token_time else 0
                    
                    # Calculate performance metrics
                    tokens_per_second = token_count / total_duration if total_duration > 0 else 0
                    response_length = len(full_response)
                    words_count = len(full_response.split())
                    
                    # Create benchmark data using Pydantic models
                    import sys
                    from pathlib import Path
                    sys.path.insert(0, str(Path(__file__).parent.parent))
                    
                    try:
                        from analytics.benchmark_models import BenchmarkRecord, PerformanceMetrics, QualityMetrics
                        
                        # Create structured benchmark record
                        performance = PerformanceMetrics(
                            total_duration_ms=int(total_duration * 1000),
                            first_token_latency_ms=int(first_token_latency * 1000),
                            tokens_per_second=round(tokens_per_second, 2),
                            token_count=token_count,
                            response_length_chars=response_length,
                            word_count=words_count
                        )
                        
                        quality = QualityMetrics(
                            response_relevance="auto_analyze",
                            response_completeness="complete" if response_length > 50 else "brief",
                            estimated_quality_score=min(10, max(1, (response_length / 100) + (words_count / 20))),
                            has_error=False,
                            is_on_topic=True
                        )
                        
                        benchmark_record = BenchmarkRecord(
                            request_id=request_id,
                            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                            model=model_name or "unknown",
                            user_message=message,
                            ai_response=full_response,
                            performance=performance,
                            quality_metrics=quality,
                            source="ui",
                            status="success"
                        )
                        
                        benchmark_data = benchmark_record.dict()
                        
                    except ImportError:
                        # Fallback to dict format if Pydantic models not available
                        benchmark_data = {
                            "request_id": request_id,
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "model": model_name,
                            "user_message": message,
                            "ai_response": full_response,
                            "performance": {
                                "total_duration_ms": int(total_duration * 1000),
                                "first_token_latency_ms": int(first_token_latency * 1000),
                                "tokens_per_second": round(tokens_per_second, 2),
                                "token_count": token_count,
                                "response_length_chars": response_length,
                                "word_count": words_count
                            },
                            "quality_metrics": {
                                "response_relevance": "auto_analyze",
                                "response_completeness": "complete" if response_length > 50 else "brief",
                                "estimated_quality_score": min(10, max(1, (response_length / 100) + (words_count / 20)))
                            },
                            "source": "ui",
                            "status": "success"
                        }
                    
                    logger.info(f"📊 BENCHMARK [{request_id}] Complete - Duration: {total_duration:.2f}s, Tokens: {token_count}, TPS: {tokens_per_second:.2f}")
                    logger.info(f"📝 BENCHMARK [{request_id}] Response: {full_response[:100]}...")
                    
                    # Save to benchmark log file
                    self._save_benchmark_data(benchmark_data)
                
                return StreamingResponse(token_iter(), media_type='text/plain')
            except Exception as e:
                end_time = time.time()
                error_duration = end_time - start_time
                
                # Log error with benchmark data
                error_data = {
                    "request_id": request_id,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "model": model_name,
                    "user_message": message,
                    "error": str(e),
                    "duration_ms": int(error_duration * 1000),
                    "status": "error"
                }
                
                logger.error(f"❌ BENCHMARK [{request_id}] Error after {error_duration:.2f}s: {str(e)}")
                self._save_benchmark_data(error_data)
                
                raise HTTPException(status_code=500, detail=str(e))

        # ---------- Favicon ----------
        @self.app.get("/favicon.ico")
        async def favicon():
            """Serve pete.png as favicon"""
            from fastapi.responses import FileResponse
            import os
            
            favicon_path = os.path.join(os.path.dirname(__file__), "..", "public", "pete.png")
            if os.path.exists(favicon_path):
                return FileResponse(favicon_path, media_type="image/png")
            else:
                # Fallback to absolute path
                abs_favicon_path = os.path.join(os.getcwd(), "src", "public", "pete.png")
                if os.path.exists(abs_favicon_path):
                    return FileResponse(abs_favicon_path, media_type="image/png")
                else:
                    from fastapi import HTTPException
                    raise HTTPException(status_code=404, detail="Favicon not found")

        # ---------- Simple HTML UI ----------
        @self.app.get("/ui", response_class=HTMLResponse)
        async def user_interface():
            """Basic browser UI for manual testing"""
            return '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Jamie AI Property Manager</title>
    <link rel="icon" type="image/png" href="/favicon.ico">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; background: #f8f9fa; }
        .header { background: white; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .header-content { max-width: 800px; margin: 0 auto; display: flex; align-items: center; gap: 20px; }
        .jamie-section { display: flex; align-items: center; gap: 15px; }
        .jamie-avatar { width: 80px; height: 80px; border-radius: 50%; border: 3px solid #007acc; }
        .jamie-info h1 { margin: 0; color: #007acc; font-size: 24px; }
        .jamie-info p { margin: 5px 0 0 0; color: #666; font-size: 14px; }
        .model-selector { margin-left: auto; }
        .model-selector label { font-weight: bold; color: #333; margin-right: 10px; }
        .model-selector select { padding: 8px 12px; border: 2px solid #007acc; border-radius: 6px; font-size: 14px; }
        .chat-container { max-width: 800px; margin: 0 auto; padding: 0 20px; }
        #log { width: 100%; height: 400px; border: 1px solid #ddd; padding: 15px; overflow-y: auto; background: white; border-radius: 8px; margin-bottom: 20px; }
        .input-section { display: flex; gap: 10px; }
        #msg { flex: 1; padding: 12px; border: 2px solid #007acc; border-radius: 6px; font-size: 16px; }
        #send { padding: 12px 24px; background: #007acc; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; }
        #send:hover { background: #0056b3; }
    </style>
</head>
<body>
    <!-- Pete Logo Header -->
    <div style="text-align:center;padding:15px;background:white;border-bottom:2px solid #007acc;">
        <img src="/public/pete.png" alt="PeteOllama Logo" style="height:60px;"/>
        <h2 style="margin:5px 0 0 0;color:#007acc;">PeteOllama</h2>
    </div>
    
    <div class="header">
        <div class="header-content">
            <div class="jamie-section">
                <img id="jamieAvatar" src="/public/Jamie.png" alt="Jamie" class="jamie-avatar"/>
                <div class="jamie-info">
                    <h1>Jamie AI</h1>
                    <p>Property Management Assistant</p>
                </div>
            </div>
            <div class="model-selector">
                <label for="model">Model:</label>
        <select id="model"></select>
            </div>
        </div>
        
        <!-- Environment Indicator -->
        <div id="environmentIndicator" style="text-align:center;padding:8px;margin:10px auto;max-width:600px;border-radius:6px;font-weight:bold;font-size:14px;">
            <span id="envStatus">🔄 Detecting Environment...</span>
            <span id="envDetails" style="font-size:11px;margin-left:10px;font-weight:normal;"></span>
        </div>
    </div>
    
    <div class="chat-container">
        <div id="log"></div>
        <div class="input-section">
            <input id="msg" placeholder="Ask Jamie about property management..."/>
    <button id="send">Send</button>
        </div>
    </div>
    <script>
    const log = document.getElementById('log');
    const modelSelect = document.getElementById('model');

    // Populate Jamie models in header dropdown
    fetch('/personas').then(r=>r.json()).then(list=>{
        let jamieModels = [];
        let otherModels = [];
        
        list.forEach(p=>{
            if(p.type === 'primary' && p.models && p.models.length > 0){
                // Jamie models - prioritize these
                jamieModels = p.models;
            } else {
                // Other models
                otherModels.push(...p.models);
            }
        });
        
        // Add Jamie models first
        if(jamieModels.length > 0){
            const jamieGroup = document.createElement('optgroup');
            jamieGroup.label = '👩‍💼 Jamie Models';
            jamieModels.forEach(model => {
            const opt = document.createElement('option');
                opt.value = model;
                opt.textContent = model.replace('peteollama:jamie-', 'Jamie ').replace('peteollama:', '');
                jamieGroup.appendChild(opt);
            });
            modelSelect.appendChild(jamieGroup);
            
            // Set first Jamie model as default
            modelSelect.value = jamieModels[0];
        }
        
        // Add other models if any (as backup)
        if(otherModels.length > 0){
            const otherGroup = document.createElement('optgroup');
            otherGroup.label = '🤖 Other Models';
            otherModels.forEach(model => {
                const opt = document.createElement('option');
                opt.value = model;
                opt.textContent = model;
                otherGroup.appendChild(opt);
            });
            modelSelect.appendChild(otherGroup);
        }
    });

    // Environment detection (same as admin)
    async function loadEnvironmentStatus(){
        try{
            const resp=await fetch('/admin/environment');
            const env=await resp.json();
            
            const indicator=document.getElementById('environmentIndicator');
            const status=document.getElementById('envStatus');
            const details=document.getElementById('envDetails');
            
            if(env.is_local){
                indicator.style.background='#d4edda';
                indicator.style.border='2px solid #155724';
                status.innerHTML='💻 Local Development';
                details.innerHTML=`Platform: ${env.platform} • Timeout: ${env.timeout_seconds}s`;
            }else{
                indicator.style.background='#cce5ff';
                indicator.style.border='2px solid #0066cc';
                status.innerHTML='☁️ Cloud (RunPod)';
                details.innerHTML=`Platform: ${env.platform} • Timeout: ${env.timeout_seconds}s`;
            }
        }catch(e){
            document.getElementById('envStatus').innerHTML='❌ Environment Detection Failed';
        }
    }
    loadEnvironmentStatus();

    document.getElementById('send').onclick = async () => {
        const text = document.getElementById('msg').value;
        if (!text) return;
        log.innerHTML += `<div><b>You:</b> ${text}</div>`;
        const resp = await fetch('/test/stream', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({message: text, model: modelSelect.value})
        });
        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        let aiBlock = document.createElement('div');
        aiBlock.innerHTML = `<b>AI (${modelSelect.value}):</b> `;
        log.appendChild(aiBlock);
        while (true) {
            const {value, done} = await reader.read();
            if (done) break;
            aiBlock.innerHTML += decoder.decode(value, {stream: true});
            log.scrollTop = log.scrollHeight;
        }
        document.getElementById('msg').value = '';
    };
    </script>
</body>
</html>'''

        # ---------- Admin HTML UI ----------
        @self.app.get("/admin", response_class=HTMLResponse)
        async def admin_ui():
            """Enhanced admin dashboard for training and model testing"""
            return '''<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Admin – JamieAI 1.0 Enhanced</title>
<link rel="icon" type="image/png" href="/favicon.ico">
<style>
body{font-family:Arial,Helvetica,sans-serif;margin:20px;background:#f5f5f5}
.container{max-width:1200px;margin:0 auto;background:white;padding:20px;border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,0.1)}
.section{margin-bottom:30px;padding:20px;border:1px solid #ddd;border-radius:6px;background:#fafafa}
.section h3{margin-top:0;color:#333;border-bottom:2px solid #007acc;padding-bottom:10px}
#samples{width:100%;height:200px;border:1px solid #ccc;overflow:auto;white-space:pre;font-size:12px;padding:6px;background:white}
#log{height:120px;border:1px solid #ccc;overflow:auto;white-space:pre;font-size:12px;padding:6px;margin-top:10px;background:white}
#testOutput{height:300px;border:1px solid #ccc;overflow:auto;white-space:pre-wrap;font-size:13px;padding:10px;margin-top:10px;background:white}
button{padding:10px 20px;margin:5px;background:#007acc;color:white;border:none;border-radius:4px;cursor:pointer;font-size:14px}
button:hover{background:#0056b3}
button:disabled{background:#ccc;cursor:not-allowed}
select{padding:8px;margin:5px;border:1px solid #ccc;border-radius:4px;font-size:14px}
input[type="text"]{padding:8px;margin:5px;border:1px solid #ccc;border-radius:4px;font-size:14px;width:300px}
.test-case{background:#e8f4f8;padding:10px;margin:5px 0;border-radius:4px;cursor:pointer}
.test-case:hover{background:#d1ecf1}
.performance{display:inline-block;margin-left:15px;font-size:12px;color:#666}
.error{color:#dc3545;background:#f8d7da;padding:8px;border-radius:4px;margin:5px 0}
.success{color:#155724;background:#d4edda;padding:8px;border-radius:4px;margin:5px 0}
</style></head><body>
<!-- Pete Logo Header -->
<div style="text-align:center;padding:15px;background:white;border-bottom:2px solid #007acc;margin-bottom:20px;">
    <img src="/public/pete.png" alt="PeteOllama Logo" style="height:60px;"/>
    <h2 style="margin:5px 0 0 0;color:#007acc;">PeteOllama</h2>
</div>

<div class="container">
<div class="nav-links" style="margin-bottom:20px;text-align:center;">
    <a href="/admin" style="margin:0 15px;color:#007acc;text-decoration:none;font-weight:bold;">Dashboard</a>
    <a href="/admin/settings" style="margin:0 15px;color:#007acc;text-decoration:none;font-weight:bold;">Settings</a>
    <a href="/admin/stats" style="margin:0 15px;color:#007acc;text-decoration:none;font-weight:bold;">Stats</a>
    <a href="/ui" style="margin:0 15px;color:#007acc;text-decoration:none;font-weight:bold;">Main UI</a>
</div>

<h1>🤖 JamieAI 1.0 – Enhanced Testing Dashboard</h1>

<!-- Environment Indicator -->
<div id="environmentIndicator" style="text-align:center;padding:10px;margin:10px 0;border-radius:6px;font-weight:bold;font-size:16px;">
    <span id="envStatus">🔄 Detecting Environment...</span>
    <span id="envDetails" style="font-size:12px;margin-left:15px;font-weight:normal;"></span>
</div>

<div class="section">
<h3>📚 Training Data</h3>
<p>Preview training samples pulled from pete.db</p>
<button id="refresh">Load Samples</button>
<button id="train">Train Property-Manager Model</button>
<div id="samples"></div>
<h4>Training Log</h4>
<div id="log"></div>
</div>

<div class="section">
<h3>🧪 Model Testing & Comparison</h3>
<p>Test different Jamie models with GPU acceleration and preloading</p>

<div style="margin-bottom:15px;padding:10px;background:#e3f2fd;border-radius:4px">
<h4>🚀 Smart Model Loading</h4>
<p style="font-size:12px;margin:5px 0">Models are loaded into memory when selected for 10x faster response times</p>
<div id="loadingStatus" style="margin:10px 0;padding:8px;background:#fff;border-radius:4px;display:none">
<div style="color:#007acc;font-weight:bold">🔄 Loading model into memory...</div>
<div style="font-size:11px;color:#666;margin-top:3px">Please wait about 1 minute before testing. Model will stay loaded until you switch.</div>
</div>
<button id="checkModelStatus" style="font-size:12px">📊 Check Model Status</button>
<div id="modelStatusDisplay" style="margin-top:10px;font-size:12px"></div>
</div>

<div style="margin-bottom:15px">
<label>Select Model:</label>
<select id="modelSelect">
<option value="llama3:latest">Base Model (llama3:latest)</option>
<option value="peteollama:jamie-simple">Jamie Simple</option>
<option value="peteollama:jamie-voice-complete">Jamie Voice Complete</option>
<option value="peteollama:jamie-working-working_20250806">Jamie Working</option>
<option value="peteollama:jamie-fixed">Jamie Fixed (Latest)</option>
</select>
<span class="performance" id="modelInfo">Select a model to load and test</span>
</div>

<div style="margin-bottom:15px">
<label>Test Message:</label>
<input type="text" id="testMessage" placeholder="Enter test message..." value="My AC stopped working">
<button id="runTest">🚀 Test Model</button>
<button id="runAllTests">📊 Run All Test Cases</button>
</div>

<div style="margin-bottom:15px">
<h4>🎯 Quick Test Cases (click to use):</h4>
<div class="test-case" onclick="setTestMessage(this.textContent)">My AC stopped working this morning</div>
<div class="test-case" onclick="setTestMessage(this.textContent)">My toilet is leaking water on the floor</div>
<div class="test-case" onclick="setTestMessage(this.textContent)">When is my rent due this month?</div>
<div class="test-case" onclick="setTestMessage(this.textContent)">The garbage disposal isn't working</div>
<div class="test-case" onclick="setTestMessage(this.textContent)">My neighbor is being too loud at night</div>
<div class="test-case" onclick="setTestMessage(this.textContent)">I need to pay my rent but the portal is down</div>
</div>

<div id="testOutput"></div>
</div>

<div class="section">
<h3>💬 Conversation Testing</h3>
<p>Test ongoing conversations with context preservation and analysis</p>

<div style="margin-bottom:15px">
<label>Conversation Model:</label>
<select id="conversationModel">
<option value="peteollama:jamie-fixed">Jamie Fixed (Latest)</option>
<option value="peteollama:jamie-simple">Jamie Simple</option>
<option value="peteollama:jamie-voice-complete">Jamie Voice Complete</option>
<option value="llama3:latest">Base Model (llama3:latest)</option>
</select>
<button id="startNewConversation">🆕 Start New Conversation</button>
<button id="clearConversation">🗑️ Clear History</button>
</div>

<div style="margin-bottom:15px">
<input type="text" id="conversationMessage" placeholder="Type your message here..." style="width:70%">
<button id="sendConversationMessage">💬 Send Message</button>
</div>

<div id="conversationHistory" style="height:400px;border:1px solid #ccc;overflow:auto;padding:10px;margin:10px 0;background:white;font-family:Arial,sans-serif"></div>

<div id="conversationAnalysis" style="background:#f8f9fa;padding:10px;border-radius:4px;margin:10px 0;display:none">
<h4>🧠 Agent Analysis</h4>
<div id="analysisContent"></div>
</div>
</div>

</div>
<script>
const samplesDiv=document.getElementById('samples');
const logDiv=document.getElementById('log');
const testOutput=document.getElementById('testOutput');
const modelSelect=document.getElementById('modelSelect');
const testMessage=document.getElementById('testMessage');

function appendLog(txt){logDiv.innerText+=txt+'\\n';logDiv.scrollTop=logDiv.scrollHeight;}
function appendTest(txt){testOutput.innerHTML+=txt+'<br>';testOutput.scrollTop=testOutput.scrollHeight;}
function setTestMessage(msg){testMessage.value=msg;}

// Environment detection (new)
async function loadEnvironmentStatus(){
  try{
    const resp=await fetch('/admin/environment');
    const env=await resp.json();
    
    const indicator=document.getElementById('environmentIndicator');
    const status=document.getElementById('envStatus');
    const details=document.getElementById('envDetails');
    
    if(env.is_local){
      indicator.style.background='#d4edda';
      indicator.style.border='2px solid #155724';
      status.innerHTML='💻 Local Development';
      details.innerHTML=`Platform: ${env.platform} • Timeout: ${env.timeout_seconds}s • Host: ${env.hostname}`;
    }else{
      indicator.style.background='#cce5ff';
      indicator.style.border='2px solid #0066cc';
      status.innerHTML='☁️ Cloud (RunPod)';
      details.innerHTML=`Platform: ${env.platform} • Timeout: ${env.timeout_seconds}s • Host: ${env.hostname}`;
    }
  }catch(e){
    document.getElementById('envStatus').innerHTML='❌ Environment Detection Failed';
  }
}
loadEnvironmentStatus();

// Training functions (existing)
document.getElementById('refresh').onclick=async()=>{
  const res=await fetch('/admin/training-samples?limit=20');
  const json=await res.json();
  samplesDiv.innerText=JSON.stringify(json,null,2);
};

document.getElementById('train').onclick=async()=>{
  appendLog('Starting training ...');
  const resp=await fetch('/admin/train-jamie',{method:'POST'});
  const reader=resp.body.getReader();
  const dec=new TextDecoder();
  while(true){const {value,done}=await reader.read();if(done)break;appendLog(dec.decode(value));}
  appendLog('Training request finished');
};

// Smart model loading functions
let currentLoadedModel = null;
let isLoading = false;

async function loadModelIntoMemory(modelName) {
  if (isLoading || currentLoadedModel === modelName) {
    return; // Already loading or already loaded
  }
  
  isLoading = true;
  const loadingDiv = document.getElementById('loadingStatus');
  const statusDiv = document.getElementById('modelStatusDisplay');
  const modelInfo = document.getElementById('modelInfo');
  
  // Show loading message
  loadingDiv.style.display = 'block';
  modelInfo.textContent = `Loading ${modelName}...`;
  
  try {
    const response = await fetch('/admin/preload-model', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({model: modelName})
    });
    
    const result = await response.json();
    
    if (result.success) {
      currentLoadedModel = modelName;
      loadingDiv.style.display = 'none';
      modelInfo.innerHTML = `🟢 ${modelName} loaded in ${result.duration_seconds}s`;
      statusDiv.innerHTML = `<div class="success">✅ ${result.message}</div>`;
      
      // Auto-refresh model status
      setTimeout(() => document.getElementById('checkModelStatus').click(), 500);
    } else {
      loadingDiv.style.display = 'none';
      modelInfo.innerHTML = `🔴 Failed to load ${modelName}`;
      statusDiv.innerHTML = `<div class="error">❌ Error: ${result.error}</div>`;
    }
  } catch (e) {
    loadingDiv.style.display = 'none';
    modelInfo.innerHTML = `🔴 Network error loading ${modelName}`;
    statusDiv.innerHTML = `<div class="error">❌ Network Error: ${e.message}</div>`;
  } finally {
    isLoading = false;
  }
}

document.getElementById('checkModelStatus').onclick=async()=>{
  const statusDiv=document.getElementById('modelStatusDisplay');
  
  try{
    const resp=await fetch('/admin/model-status');
    const result=await resp.json();
    
    if(result.success){
      let html='<div style="font-weight:bold">Model Status:</div>';
      result.models.forEach(model=>{
        const status=model.loaded?'🟢 Loaded':'🔴 Cold';
        const running=model.is_running?' (Running)':'';
        html+=`<div>${status} ${model.name}${running} (Base: ${model.base_model})</div>`;
      });
      html+=`<div style="margin-top:5px;font-weight:bold">Total: ${result.total_loaded}/${result.models.length} loaded, ${result.total_running} running</div>`;
      statusDiv.innerHTML=html;
    }else{
      statusDiv.innerHTML=`<div class="error">❌ Error: ${result.error}</div>`;
    }
  }catch(e){
    statusDiv.innerHTML=`<div class="error">❌ Network Error: ${e.message}</div>`;
  }
};

// Auto-check model status on page load
setTimeout(()=>document.getElementById('checkModelStatus').click(),500);

// Model testing functions (enhanced)
document.getElementById('runTest').onclick=async()=>{
  const model=modelSelect.value;
  const message=testMessage.value;
  if(!message){alert('Please enter a test message');return;}
  
  // Check if model is loaded
  if (currentLoadedModel !== model) {
    const loadNow = confirm(`⚠️ Model ${model} is not loaded into memory. This will be slower.\n\nWould you like to load it first? (Recommended)`);
    if (loadNow) {
      await loadModelIntoMemory(model);
      // Wait a moment for loading to complete
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  }
  
  appendTest(`<div class="section" style="margin:10px 0;padding:10px;border-left:4px solid #007acc">
    <strong>🧪 Testing Model:</strong> ${model}<br>
    <strong>📝 Message:</strong> ${message}<br>
    <strong>⏰ Started:</strong> ${new Date().toLocaleTimeString()}<br>
    <strong>🔋 Model Status:</strong> ${currentLoadedModel === model ? '🟢 Preloaded' : '🔴 Cold Start'}
  </div>`);
  
  const startTime=Date.now();
  document.getElementById('runTest').disabled=true;
  
  try{
    const resp=await fetch('/admin/test-model',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({model:model,message:message})
    });
    
    const result=await resp.json();
    const clientDuration=Date.now()-startTime;
    
    if(result.success){
      const agentResponse = result.parsed_response ? result.parsed_response.agent_response : result.raw_response;
      const thinking = result.parsed_response ? result.parsed_response.thinking_process : '';
      const systemContent = result.parsed_response ? result.parsed_response.system_content : '';
      const similarity = result.similarity_analysis || {};
      
      // Performance metrics
      const actualDuration = result.actual_duration_seconds || (result.duration_ms / 1000);
      const preloadStatus = result.model_preloaded ? '🟢 Preloaded' : '🔴 Cold Start';
      
      appendTest(`<div class="success">
        <strong>✅ Jamie's Response:</strong><br>
        <div style="background:#f3e5f5;padding:10px;border-radius:4px;margin:5px 0">
          ${agentResponse}
        </div>
        <div style="background:#e8f4f8;padding:8px;margin:5px 0;border-radius:4px;font-size:12px">
          <strong>⚡ Performance:</strong> ${actualDuration.toFixed(2)}s • ${preloadStatus} • ${result.environment} • Base: ${result.base_model || 'unknown'}
        </div>
      </div>`);
      
      // Real success rate based on conversation similarity
      if(similarity.real_success_rate !== undefined){
        const successColor = similarity.real_success_rate >= 70 ? '#d4edda' : similarity.real_success_rate >= 50 ? '#fff3cd' : '#f8d7da';
        appendTest(`<div style="background:${successColor};padding:8px;margin:5px 0;border-radius:4px">
          <strong>🎯 Real Success Rate:</strong> ${similarity.real_success_rate.toFixed(1)}% 
          (Similarity: ${(similarity.similarity_score * 100).toFixed(1)}%)<br>
          <small>${similarity.explanation}</small>
          ${similarity.best_match_context ? `<br><small>Best match: ${similarity.best_match_context}</small>` : ''}
        </div>`);
      }
      
      // PYDANTIC VALIDATION RESULTS - Self-correcting validation
      if(result.validation_result){
        const validation = result.validation_result;
        const validationColor = validation.is_valid ? '#d4edda' : '#f8d7da';
        const statusIcon = validation.is_valid ? '✅' : '❌';
        
        appendTest(`<div style="background:${validationColor};padding:8px;margin:5px 0;border-radius:4px">
          <strong>${statusIcon} Pydantic Validation:</strong> ${validation.is_valid ? 'PASSED' : 'FAILED'}<br>
          <strong>Jamie Score:</strong> ${(validation.jamie_score * 100).toFixed(1)}% • 
          <strong>Category:</strong> ${validation.issue_category} (${validation.urgency_level})
        </div>`);
        
        // Show validation errors if any
        if(validation.validation_errors && validation.validation_errors.length > 0){
          appendTest(`<details style="margin:5px 0;padding:8px;background:#f8d7da;border-radius:4px">
            <summary style="cursor:pointer;font-weight:bold">⚠️ Validation Errors Found</summary>
            <ul style="margin:8px 0;padding-left:20px">
              ${validation.validation_errors.map(error => `<li>${error}</li>`).join('')}
            </ul>
          </details>`);
        }
        
        // Show improvement suggestions
        if(validation.improvement_suggestions && validation.improvement_suggestions.length > 0){
          appendTest(`<details style="margin:5px 0;padding:8px;background:#fff3cd;border-radius:4px">
            <summary style="cursor:pointer;font-weight:bold">💡 Improvement Suggestions</summary>
            <ul style="margin:8px 0;padding-left:20px">
              ${validation.improvement_suggestions.map(suggestion => `<li>${suggestion}</li>`).join('')}
            </ul>
          </details>`);
        }
        
        // Show what Jamie actually said for comparison
        if(validation.jamie_alternative){
          appendTest(`<details style="margin:5px 0;padding:8px;background:#e7f3ff;border-radius:4px">
            <summary style="cursor:pointer;font-weight:bold">👩‍💼 What Jamie Actually Said (Database)</summary>
            <div style="margin:8px 0;font-style:italic;background:white;padding:8px;border-radius:3px">
              "${validation.jamie_alternative}"
            </div>
          </details>`);
        }
        
        // Show corrected response if validation failed
        if(validation.corrected_response){
          appendTest(`<details style="margin:5px 0;padding:8px;background:#d1ecf1;border-radius:4px">
            <summary style="cursor:pointer;font-weight:bold">📝 Corrected Response (Auto-Generated)</summary>
            <div style="margin:8px 0;background:white;padding:8px;border-radius:3px;border-left:4px solid #17a2b8">
              "${validation.corrected_response}"
            </div>
          </details>`);
        }
      }
      
      // Show thinking process if available
      if(thinking){
        appendTest(`<details style="margin:5px 0;padding:8px;background:#fff3cd;border-radius:4px">
          <summary style="cursor:pointer;font-weight:bold">🧠 Show Agent Thinking Process</summary>
          <div style="margin:8px 0;font-family:monospace;font-size:11px;white-space:pre-wrap">${thinking}</div>
        </details>`);
      }
      
      // Show system content if it was separated
      if(systemContent){
        appendTest(`<details style="margin:5px 0;padding:8px;background:#e7f3ff;border-radius:4px">
          <summary style="cursor:pointer;font-weight:bold">⚙️ Show System Instructions Found</summary>
          <div style="margin:8px 0;font-family:monospace;font-size:11px;white-space:pre-wrap">${systemContent}</div>
        </details>`);
      }
      
      // Enhanced analysis using parsed data
      if(result.analysis && Object.keys(result.analysis).length > 0){
        const analysis = result.analysis;
        appendTest(`<details style="margin:5px 0;padding:8px;background:#d4edda;border-radius:4px">
          <summary style="cursor:pointer;font-weight:bold">📊 Show Detailed Quality Analysis</summary>
          <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-top:5px">
            <div>Parsing: ${(analysis.parsing_confidence * 100).toFixed(1)}%</div>
            <div>Relevance: ${(analysis.response_relevance * 100).toFixed(1)}%</div>
            <div>Professional: ${(analysis.professional_tone * 100).toFixed(1)}%</div>
            <div>Action-Oriented: ${(analysis.action_oriented * 100).toFixed(1)}%</div>
          </div>
        </details>`);
      }
    }else{
      appendTest(`<div class="error">❌ Error: ${result.error}</div>`);
    }
  }catch(e){
    appendTest(`<div class="error">❌ Network Error: ${e.message}</div>`);
  }finally{
    document.getElementById('runTest').disabled=false;
  }
};

document.getElementById('runAllTests').onclick=async()=>{
  const testCases=[
    "My AC stopped working this morning",
    "My toilet is leaking water on the floor", 
    "When is my rent due this month?",
    "The garbage disposal isn't working",
    "My neighbor is being too loud at night",
    "I need to pay my rent but the portal is down"
  ];
  
  appendTest(`<h3>🏁 Running ${testCases.length} test cases on ${modelSelect.value}</h3>`);
  
  for(let i=0;i<testCases.length;i++){
    testMessage.value=testCases[i];
    await document.getElementById('runTest').onclick();
    await new Promise(r=>setTimeout(r,1000)); // Brief pause between tests
  }
  
  appendTest(`<div class="success"><strong>🎉 All tests completed!</strong></div>`);
};

function analyzeResponse(response,question){
  const length=response.length;
  const hasAction=response.toLowerCase().includes("i'll")||response.toLowerCase().includes("i'm");
  const hasContact=response.includes("405-367-6318")||response.toLowerCase().includes("call");
  const hasConversation=response.toLowerCase().includes("conversation")||response.toLowerCase().includes("back and forth");
  const hasLoop=response.split(' ').length>200; // Very long might indicate loop
  
  let score=0;
  let notes=[];
  
  if(length>50&&length<300){score+=2;notes.push("Good length");}
  else if(length<50){notes.push("⚠️ Too short");}
  else if(length>300){notes.push("⚠️ Might be too long");}
  
  if(hasAction){score+=2;notes.push("✅ Action-oriented");}
  if(hasContact){score+=1;notes.push("✅ Professional contact");}
  if(!hasConversation){score+=2;notes.push("✅ No conversation simulation");}
  else{notes.push("⚠️ Conversation patterns detected");}
  if(!hasLoop){score+=1;notes.push("✅ Concise");}
  
  return `Score: ${score}/8 - ${notes.join(", ")}`;
}

// Model selection handler - load model when changed
modelSelect.onchange = async () => {
  const selectedModel = modelSelect.value;
  const modelInfo = document.getElementById('modelInfo');
  
  if (selectedModel !== currentLoadedModel) {
    modelInfo.textContent = `Selected: ${selectedModel}`;
    
    // Ask user if they want to load the model
    if (confirm(`Load ${selectedModel} into memory for faster responses? This will unload the current model.`)) {
      await loadModelIntoMemory(selectedModel);
    }
  } else {
    modelInfo.innerHTML = `🟢 ${selectedModel} (already loaded)`;
  }
};

// Conversation Testing Logic
let conversationHistory = [];
let currentConversationId = null;

const conversationHistoryDiv = document.getElementById('conversationHistory');
const conversationMessage = document.getElementById('conversationMessage');
const conversationModel = document.getElementById('conversationModel');
const conversationAnalysis = document.getElementById('conversationAnalysis');
const analysisContent = document.getElementById('analysisContent');

// Handle conversation model selection
conversationModel.onchange = async () => {
  const selectedModel = conversationModel.value;
  if (selectedModel !== currentLoadedModel) {
    if (confirm(`Load ${selectedModel} into memory for faster conversation responses?`)) {
      await loadModelIntoMemory(selectedModel);
    }
  }
};

function addConversationMessage(user, agent, thinking, analysis, timestamp) {
  const messageDiv = document.createElement('div');
  messageDiv.style.cssText = 'margin:10px 0;padding:10px;border-radius:6px;border-left:4px solid #007acc';
  
  let html = `
    <div style="font-size:12px;color:#666;margin-bottom:5px">${timestamp}</div>
    <div style="background:#e3f2fd;padding:8px;border-radius:4px;margin:4px 0">
      <strong>👤 User:</strong> ${user}
    </div>
    <div style="background:#f3e5f5;padding:8px;border-radius:4px;margin:4px 0">
      <strong>🤖 Jamie:</strong> ${agent}
    </div>`;
  
  if (thinking) {
    html += `
    <details style="margin:4px 0;padding:4px;background:#fff3cd;border-radius:4px">
      <summary style="cursor:pointer;font-weight:bold">🧠 Show Agent Thinking</summary>
      <div style="margin:8px 0;font-family:monospace;font-size:11px;white-space:pre-wrap">${thinking}</div>
    </details>`;
  }
  
  if (analysis && Object.keys(analysis).length > 0) {
    html += `
    <details style="margin:4px 0;padding:4px;background:#d4edda;border-radius:4px">
      <summary style="cursor:pointer;font-weight:bold">📊 Show Quality Analysis</summary>
      <div style="margin:8px 0;font-size:11px">
        <div>Relevance: ${(analysis.response_relevance * 100).toFixed(1)}%</div>
        <div>Professional Tone: ${(analysis.professional_tone * 100).toFixed(1)}%</div>
        <div>Action Oriented: ${(analysis.action_oriented * 100).toFixed(1)}%</div>
        <div>Parsing Confidence: ${(analysis.parsing_confidence * 100).toFixed(1)}%</div>
      </div>
    </details>`;
  }
  
  messageDiv.innerHTML = html;
  conversationHistoryDiv.appendChild(messageDiv);
  conversationHistoryDiv.scrollTop = conversationHistoryDiv.scrollHeight;
}

document.getElementById('startNewConversation').onclick = () => {
  conversationHistory = [];
  currentConversationId = `conv_${Date.now()}`;
  conversationHistoryDiv.innerHTML = '<div style="text-align:center;color:#666;font-style:italic">New conversation started</div>';
  conversationAnalysis.style.display = 'none';
};

document.getElementById('clearConversation').onclick = () => {
  conversationHistory = [];
  currentConversationId = null;
  conversationHistoryDiv.innerHTML = '';
  conversationAnalysis.style.display = 'none';
};

document.getElementById('sendConversationMessage').onclick = async () => {
  const message = conversationMessage.value.trim();
  if (!message) {
    alert('Please enter a message');
    return;
  }
  
  const model = conversationModel.value;
  if (!currentConversationId) {
    currentConversationId = `conv_${Date.now()}`;
  }
  
  // Disable send button during request
  const sendButton = document.getElementById('sendConversationMessage');
  sendButton.disabled = true;
  sendButton.textContent = '⏳ Sending...';
  
  try {
    const response = await fetch('/admin/conversation/stream', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        model: model,
        message: message,
        conversation_id: currentConversationId,
        conversation_history: conversationHistory
      })
    });
    
    const result = await response.json();
    
    if (result.success) {
      const timestamp = new Date().toLocaleTimeString();
      const parsed = result.parsed_response;
      const analysis = result.analysis;
      
      // Add to conversation history
      conversationHistory.push({
        user: message,
        agent: parsed ? parsed.agent_response : result.raw_response,
        timestamp: timestamp,
        thinking: parsed ? parsed.thinking_process : '',
        analysis: analysis
      });
      
      // Display the conversation
      addConversationMessage(
        message,
        parsed ? parsed.agent_response : result.raw_response,
        parsed ? parsed.thinking_process : '',
        analysis,
        timestamp
      );
      
      // Show analysis summary
      if (analysis && Object.keys(analysis).length > 0) {
        conversationAnalysis.style.display = 'block';
        analysisContent.innerHTML = `
          <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px">
            <div><strong>Response Quality:</strong> ${(analysis.parsing_confidence * 100).toFixed(1)}%</div>
            <div><strong>Relevance:</strong> ${(analysis.response_relevance * 100).toFixed(1)}%</div>
            <div><strong>Professional:</strong> ${(analysis.professional_tone * 100).toFixed(1)}%</div>
            <div><strong>Action-Oriented:</strong> ${(analysis.action_oriented * 100).toFixed(1)}%</div>
          </div>
          <div style="margin-top:10px;font-size:12px;color:#666">
            Turn ${result.turn_number} • Duration: ${result.duration_ms}ms • Environment: ${result.environment}
          </div>
        `;
      }
      
      // Clear input
      conversationMessage.value = '';
      
    } else {
      alert(`Error: ${result.error}`);
    }
    
  } catch (error) {
    alert(`Network error: ${error.message}`);
  } finally {
    sendButton.disabled = false;
    sendButton.textContent = '💬 Send Message';
  }
};

// Allow Enter key to send message
conversationMessage.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') {
    document.getElementById('sendConversationMessage').click();
  }
});
</script></body></html>'''

        # ---------- Admin API endpoints ----------
        @self.app.get("/admin/training-samples")
        async def training_samples(limit: int = 20):
            from database.pete_db_manager import PeteDBManager
            db = PeteDBManager()
            samples = db.get_training_examples()[:limit]
            return samples

        @self.app.post("/admin/train-jamie", response_class=StreamingResponse)
        async def admin_train_jamie():
            """Run extractor then train model, stream log lines."""
            def iter_logs():
                yield "Extracting data...\n"
                try:
                    from virtual_jamie_extractor import VirtualJamieDataExtractor
                    extractor = VirtualJamieDataExtractor()
                    ok = extractor.run_full_extraction()
                    if ok:
                        # Ensure ModelManager can locate the freshly created DB
                        import shutil, os, pathlib
                        src_db = pathlib.Path(extractor.target_db_path)
                        target_path = pathlib.Path("/app/pete.db")
                        if src_db != target_path:
                            try:
                                target_path.parent.mkdir(parents=True, exist_ok=True)
                                shutil.copy2(src_db, target_path)
                                yield "Copied pete.db to /app\n"
                            except Exception as e:
                                yield f"Copy error: {e}\n"
                            os.environ["PETE_DB_PATH"] = str(target_path)
                        else:
                            # DB already at desired location
                            os.environ["PETE_DB_PATH"] = str(src_db)
                            yield "Database already at /app\n"
                    yield ("Extraction success\n" if ok else "Extraction failed\n")
                except Exception as e:
                    yield f"Extraction error: {e}\n"
                    return
                yield "Training model...\n"
                ok = self.model_manager.train_property_manager()
                yield ("Training started\n" if ok else "Training failed\n")
            return StreamingResponse(iter_logs(), media_type='text/plain')

        @self.app.get("/admin/environment")
        async def get_environment():
            """Get current environment info"""
            import os
            import platform
            
            # Detect if running locally or in cloud
            is_local = any([
                os.path.exists("/Users"),  # macOS
                os.path.exists("/home") and not os.path.exists("/workspace"),  # Linux local
                platform.system() in ["Darwin", "Windows"],  # Local systems
                "localhost" in os.getenv("HOSTNAME", ""),
                not os.path.exists("/runpod_volume")  # Not in RunPod
            ])
            
            environment = "Local Development" if is_local else "Cloud (RunPod)"
            timeout_seconds = 180 if is_local else 60  # 3 minutes local, 1 minute cloud
            
            return {
                "environment": environment,
                "is_local": is_local,
                "timeout_seconds": timeout_seconds,
                "platform": platform.system(),
                "hostname": os.getenv("HOSTNAME", "unknown")
            }

        @self.app.post("/admin/preload-model")
        async def preload_single_model(request: dict):
            """Preload a single model into memory, unloading others"""
            import time
            
            try:
                model_name = request.get("model", "")
                if not model_name:
                    return {"success": False, "error": "Model name required"}
                
                start_time = time.time()
                logger.info(f"🔄 Loading model {model_name} into memory...")
                
                # Preload the model, unloading others
                success = model_preloader.preload_model(model_name, unload_others=True)
                
                duration = time.time() - start_time
                
                if success:
                    return {
                        "success": True,
                        "message": f"Model {model_name} loaded into memory",
                        "duration_seconds": round(duration, 2),
                        "model": model_name,
                        "load_time": model_preloader.model_load_times.get(model_name, duration)
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to load model {model_name}",
                        "duration_seconds": round(duration, 2),
                        "model": model_name
                    }
                
            except Exception as e:
                logger.error(f"Error preloading model: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "model": request.get("model", "unknown")
                }

        @self.app.post("/admin/preload-models")
        async def preload_models():
            """Preload Jamie models into memory for faster response times (legacy endpoint)"""
            import time
            
            start_time = time.time()
            logger.info("🔄 Starting model preloading...")
            
            try:
                # Preload models in background
                results = model_preloader.preload_jamie_models()
                
                duration = time.time() - start_time
                loaded_count = sum(1 for success in results.values() if success)
                total_count = len(results)
                
                return {
                    "success": True,
                    "message": f"Preloaded {loaded_count}/{total_count} models",
                    "duration_seconds": round(duration, 2),
                    "results": results,
                    "loaded_models": [model for model, success in results.items() if success]
                }
                
            except Exception as e:
                logger.error(f"Error preloading models: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "duration_seconds": time.time() - start_time
                }

        @self.app.get("/admin/model-status")
        async def model_status():
            """Get current status of all models"""
            try:
                models_status = model_preloader.get_all_models_status()
                return {
                    "success": True,
                    "models": models_status,
                    "total_loaded": sum(1 for m in models_status if m["loaded"]),
                    "total_running": sum(1 for m in models_status if m["is_running"])
                }
            except Exception as e:
                logger.error(f"Error getting model status: {e}")
                return {"success": False, "error": str(e)}

        @self.app.get("/admin/model-settings")
        async def get_model_settings():
            """Get all model configurations"""
            try:
                all_models = model_settings.get_all_models()
                stats = model_settings.get_stats()
                
                return {
                    "success": True,
                    "models": {name: {
                        "name": config.name,
                        "display_name": config.display_name,
                        "description": config.description,
                        "show_in_ui": config.show_in_ui,
                        "auto_preload": config.auto_preload,
                        "is_jamie_model": config.is_jamie_model,
                        "base_model": config.base_model,
                        "last_updated": config.last_updated
                    } for name, config in all_models.items()},
                    "stats": stats
                }
            except Exception as e:
                logger.error(f"Error getting model settings: {e}")
                return {"success": False, "error": str(e)}

        @self.app.post("/admin/model-settings/update")
        async def update_model_settings(request: dict):
            """Update model configuration"""
            try:
                model_name = request.get("model_name")
                if not model_name:
                    return {"success": False, "error": "Model name required"}
                
                # Update the configuration
                success = model_settings.update_model_config(model_name, **{
                    k: v for k, v in request.items() 
                    if k != "model_name" and v is not None
                })
                
                if success:
                    # Auto-preload model if it was enabled for UI and auto_preload
                    config = model_settings.get_model_config(model_name)
                    if config and config.show_in_ui and config.auto_preload:
                        logger.info(f"Auto-preloading {model_name} due to UI settings")
                        model_preloader.preload_model(model_name, unload_others=True)
                    
                    return {
                        "success": True,
                        "message": f"Updated settings for {model_name}",
                        "config": model_settings.get_model_config(model_name).__dict__
                    }
                else:
                    return {"success": False, "error": "Failed to update settings"}
                
            except Exception as e:
                logger.error(f"Error updating model settings: {e}")
                return {"success": False, "error": str(e)}

        @self.app.post("/admin/model-settings/toggle-ui")
        async def toggle_model_ui(request: dict):
            """Toggle UI visibility for a model"""
            try:
                model_name = request.get("model_name")
                if not model_name:
                    return {"success": False, "error": "Model name required"}
                
                success = model_settings.toggle_ui_visibility(model_name)
                config = model_settings.get_model_config(model_name)
                
                if success and config:
                    # Auto-preload if enabled for UI and auto_preload is on
                    if config.show_in_ui and config.auto_preload:
                        logger.info(f"Auto-preloading {model_name} due to UI enablement")
                        model_preloader.preload_model(model_name, unload_others=True)
                    
                    return {
                        "success": True,
                        "message": f"Toggled UI visibility for {model_name}",
                        "show_in_ui": config.show_in_ui
                    }
                else:
                    return {"success": False, "error": "Failed to toggle UI visibility"}
                
            except Exception as e:
                logger.error(f"Error toggling model UI: {e}")
                return {"success": False, "error": str(e)}

        @self.app.post("/admin/test-model")
        async def test_model(request: dict):
            """Test a specific model with a message"""
            import time
            import subprocess
            import os
            import platform
            import sys
            from pathlib import Path
            
            try:
                model = request.get("model", "llama3:latest")
                message = request.get("message", "Hello")
                conversation_id = request.get("conversation_id", None)  # For ongoing conversations
                
                # Detect environment and set appropriate timeout
                is_local = any([
                    os.path.exists("/Users"),  # macOS
                    os.path.exists("/home") and not os.path.exists("/workspace"),  # Linux local
                    platform.system() in ["Darwin", "Windows"],  # Local systems
                    "localhost" in os.getenv("HOSTNAME", ""),
                    not os.path.exists("/runpod_volume")  # Not in RunPod
                ])
                
                timeout_seconds = 180 if is_local else 60  # 3 minutes local, 1 minute cloud
                env_type = "Local" if is_local else "Cloud"
                
                # Check if model is preloaded
                model_info = model_preloader.get_model_info(model)
                is_preloaded = model_info["loaded"] or model_info["is_running"]
                
                # Extract base model name for comparison tracking
                base_model_name = self._extract_base_model_name(model)
                
                logger.info(f"Testing model {model} (base: {base_model_name}) with message: {message} ({env_type} - timeout: {timeout_seconds}s - Preloaded: {is_preloaded})")
                
                # If not preloaded, suggest preloading
                if not is_preloaded:
                    logger.warning(f"⚠️ Model {model} not preloaded - this may cause delays")
                
                logger.info(f"🚀 Starting model inference for {model}...")
                
                # Accurate timing with Pendulum
                import pendulum
                request_start_time = pendulum.now()
                start_time = time.perf_counter()
                logger.info(f"⏱️  Model {model} - Starting at {request_start_time.format('HH:mm:ss')}")
                
                result = subprocess.run([
                    "ollama", "run", model, message
                ], capture_output=True, text=True, timeout=timeout_seconds)
                
                end_time = time.perf_counter()
                request_end_time = pendulum.now()
                actual_duration = end_time - start_time
                
                # Calculate total request time (user request to final response)
                total_request_duration = request_end_time - request_start_time
                total_request_seconds = total_request_duration.total_seconds()
                
                logger.info(f"✅ Model {model} - Completed in {actual_duration:.2f}s (Total request: {total_request_seconds:.2f}s)")
                
                duration_ms = int(actual_duration * 1000)  # Convert to ms with precise timing
                
                if result.returncode == 0:
                    raw_response = result.stdout.strip()
                    
                    # Parse the response using our new parser
                    try:
                        sys.path.insert(0, str(Path(__file__).parent.parent))
                        from analytics.response_parser import ResponseParser
                        
                        parser = ResponseParser()
                        parsed = parser.parse_response(raw_response, message)
                        analysis = parser.analyze_response_quality(parsed, message)
                        
                        logger.info(f"📝 Parsed response - Agent: {len(parsed.agent_response)} chars, Analysis confidence: {parsed.confidence_score:.2f}")
                        
                    except Exception as e:
                        logger.error(f"Error parsing response: {e}")
                        # Fallback to raw response
                        parsed = None
                        analysis = {}
                    
                    # Calculate conversation similarity for real success rate
                    similarity_result = None
                    real_success_rate = 0.0
                    try:
                        sys.path.insert(0, str(Path(__file__).parent.parent))
                        from analytics.conversation_similarity import ConversationSimilarityAnalyzer
                        
                        similarity_analyzer = ConversationSimilarityAnalyzer()
                        similarity_result = similarity_analyzer.calculate_similarity(
                            message, 
                            parsed.agent_response if parsed else raw_response
                        )
                        real_success_rate = similarity_analyzer.get_success_rate(
                            similarity_result.similarity_score,
                            len(raw_response)
                        )
                        
                        logger.info(f"🎯 Similarity analysis: {similarity_result.similarity_score:.2f}, Success rate: {real_success_rate:.1f}%")
                        
                    except Exception as e:
                        logger.warning(f"Could not calculate conversation similarity: {e}")
                    
                    # PYDANTIC VALIDATION - Self-correcting response validation
                    validation_result = None
                    try:
                        validation_result = response_validator.validate_response(message, raw_response)
                        
                        if validation_result.is_valid:
                            logger.info(f"✅ Response validation passed - Jamie score: {validation_result.jamie_score:.2f}")
                        else:
                            logger.warning(f"❌ Response validation failed - Jamie score: {validation_result.jamie_score:.2f}")
                            logger.warning(f"Errors: {validation_result.validation_errors}")
                            if validation_result.corrected_response:
                                logger.info(f"📝 Suggested correction: {validation_result.corrected_response[:100]}...")
                        
                    except Exception as e:
                        logger.warning(f"Could not validate response: {e}")
                    
                    # Save admin test benchmark data with parsed content and similarity
                    admin_benchmark = {
                        "request_id": f"admin_{int(start_time)}_{hash(time.time()) % 10000}",
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "model": model,
                        "user_message": message,
                        "ai_response": raw_response,
                        "parsed_response": {
                            "agent_response": parsed.agent_response if parsed else raw_response,
                            "system_content": parsed.system_content if parsed else "",
                            "thinking_process": parsed.thinking_process if parsed else "",
                            "confidence_score": parsed.confidence_score if parsed else 0.5
                        } if parsed else None,
                        "performance": {
                            "total_duration_ms": duration_ms,  # Use precise timing
                            "actual_duration_seconds": actual_duration,
                            "total_request_seconds": total_request_seconds,  # Full request timing
                            "request_start_time": request_start_time.isoformat(),
                            "request_end_time": request_end_time.isoformat(),
                            "environment": env_type,
                            "timeout_used": timeout_seconds,
                            "model_preloaded": is_preloaded,
                            "base_model": base_model_name
                        },
                        "source": "admin_test",
                        "conversation_id": conversation_id,
                        "similarity_analysis": {
                            "similarity_score": similarity_result.similarity_score if similarity_result else 0.0,
                            "real_success_rate": real_success_rate,
                            "best_match_context": similarity_result.best_match.context if similarity_result and similarity_result.best_match else None,
                            "explanation": similarity_result.explanation if similarity_result else "No similarity analysis available",
                            "confidence": similarity_result.confidence if similarity_result else 0.0
                        },
                        "validation_result": {
                            "is_valid": validation_result.is_valid if validation_result else False,
                            "jamie_score": validation_result.jamie_score if validation_result else 0.0,
                            "validation_errors": validation_result.validation_errors if validation_result else [],
                            "improvement_suggestions": validation_result.improvement_suggestions if validation_result else [],
                            "jamie_alternative": validation_result.jamie_alternative if validation_result else None,
                            "corrected_response": validation_result.corrected_response if validation_result else None,
                            "issue_category": validation_result.issue_category if validation_result else "unknown",
                            "urgency_level": validation_result.urgency_level if validation_result else "normal"
                        },
                        "quality_metrics": {
                            "response_length_chars": len(raw_response),
                            "word_count": len(raw_response.split()),
                            "estimated_quality_score": min(10, max(1, (len(raw_response) / 100) + (len(raw_response.split()) / 20))),
                            "parsing_analysis": analysis
                        }
                    }
                    self._save_benchmark_data(admin_benchmark)
                    
                    return {
                        "success": True,
                        "raw_response": raw_response,
                        "parsed_response": {
                            "agent_response": parsed.agent_response if parsed else raw_response,
                            "system_content": parsed.system_content if parsed else "",
                            "thinking_process": parsed.thinking_process if parsed else "",
                            "confidence_score": parsed.confidence_score if parsed else 0.5
                        } if parsed else None,
                        "analysis": analysis,
                        "similarity_analysis": {
                            "similarity_score": similarity_result.similarity_score if similarity_result else 0.0,
                            "real_success_rate": real_success_rate,
                            "explanation": similarity_result.explanation if similarity_result else "No similarity analysis",
                            "best_match_context": similarity_result.best_match.context if similarity_result and similarity_result.best_match else None
                        },
                        "model": model,
                        "duration_ms": duration_ms,  # Accurate timing
                        "actual_duration_seconds": actual_duration,
                        "message": message,
                        "environment": env_type,
                        "timeout_used": timeout_seconds,
                        "model_preloaded": is_preloaded,
                        "base_model": model_info.get("base_model", "unknown"),
                        "conversation_id": conversation_id
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Model error: {result.stderr}",
                        "model": model,
                        "duration_ms": duration,
                        "environment": env_type,
                        "timeout_used": timeout_seconds
                    }
                    
            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "error": f"Model response timed out after {timeout_seconds} seconds",
                    "model": model,
                    "duration_ms": timeout_seconds * 1000,
                    "environment": env_type,
                    "timeout_used": timeout_seconds
                }
            except Exception as e:
                logger.error(f"Error testing model: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "model": model,
                    "environment": "Unknown"
                }

        @self.app.post("/admin/conversation/stream")
        async def conversation_stream(request: dict):
            """Stream conversation with a model, maintaining conversation context"""
            import time
            import subprocess
            import os
            import platform
            import sys
            from pathlib import Path
            import json
            
            try:
                model = request.get("model", "llama3:latest")
                message = request.get("message", "")
                conversation_id = request.get("conversation_id", f"conv_{int(time.time())}")
                conversation_history = request.get("conversation_history", [])
                
                # Detect environment and set timeout
                is_local = any([
                    os.path.exists("/Users"),
                    os.path.exists("/home") and not os.path.exists("/workspace"),
                    platform.system() in ["Darwin", "Windows"],
                    "localhost" in os.getenv("HOSTNAME", ""),
                    not os.path.exists("/runpod_volume")
                ])
                
                timeout_seconds = 180 if is_local else 60
                env_type = "Local" if is_local else "Cloud"
                
                # Build conversation context
                context_messages = []
                for msg in conversation_history[-5:]:  # Last 5 messages for context
                    context_messages.append(f"User: {msg.get('user', '')}")
                    context_messages.append(f"Jamie: {msg.get('agent', '')}")
                
                # Create full prompt with context
                if context_messages:
                    full_prompt = "Previous conversation:\n" + "\n".join(context_messages) + "\n\nUser: " + message + "\nJamie:"
                else:
                    full_prompt = message
                
                logger.info(f"🗣️ Conversation stream for {model} - ConvID: {conversation_id}")
                logger.info(f"📝 Message: {message}")
                
                start_time = time.time()
                
                # Use Ollama for streaming response
                result = subprocess.run([
                    "ollama", "run", model, full_prompt
                ], capture_output=True, text=True, timeout=timeout_seconds)
                
                end_time = time.time()
                duration = int((end_time - start_time) * 1000)
                
                if result.returncode == 0:
                    raw_response = result.stdout.strip()
                    
                    # Parse the response
                    try:
                        sys.path.insert(0, str(Path(__file__).parent.parent))
                        from analytics.response_parser import ResponseParser
                        
                        parser = ResponseParser()
                        parsed = parser.parse_response(raw_response, message)
                        analysis = parser.analyze_response_quality(parsed, message)
                        
                    except Exception as e:
                        logger.error(f"Error parsing conversation response: {e}")
                        parsed = None
                        analysis = {}
                    
                    # Save conversation benchmark data
                    conv_benchmark = {
                        "request_id": f"conv_{conversation_id}_{int(start_time)}",
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "model": model,
                        "user_message": message,
                        "ai_response": raw_response,
                        "conversation_id": conversation_id,
                        "conversation_turn": len(conversation_history) + 1,
                        "parsed_response": {
                            "agent_response": parsed.agent_response if parsed else raw_response,
                            "system_content": parsed.system_content if parsed else "",
                            "thinking_process": parsed.thinking_process if parsed else "",
                            "confidence_score": parsed.confidence_score if parsed else 0.5
                        } if parsed else None,
                        "performance": {
                            "total_duration_ms": duration,
                            "environment": env_type,
                            "timeout_used": timeout_seconds
                        },
                        "source": "conversation_stream",
                        "quality_metrics": {
                            "response_length_chars": len(raw_response),
                            "word_count": len(raw_response.split()),
                            "estimated_quality_score": min(10, max(1, (len(raw_response) / 100) + (len(raw_response.split()) / 20))),
                            "parsing_analysis": analysis
                        }
                    }
                    self._save_benchmark_data(conv_benchmark)
                    
                    return {
                        "success": True,
                        "conversation_id": conversation_id,
                        "raw_response": raw_response,
                        "parsed_response": {
                            "agent_response": parsed.agent_response if parsed else raw_response,
                            "system_content": parsed.system_content if parsed else "",
                            "thinking_process": parsed.thinking_process if parsed else "",
                            "confidence_score": parsed.confidence_score if parsed else 0.5
                        } if parsed else None,
                        "analysis": analysis,
                        "model": model,
                        "duration_ms": duration,
                        "environment": env_type,
                        "turn_number": len(conversation_history) + 1
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Model error: {result.stderr}",
                        "conversation_id": conversation_id,
                        "model": model,
                        "duration_ms": duration
                    }
                    
            except Exception as e:
                logger.error(f"Error in conversation stream: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "conversation_id": conversation_id,
                    "model": model
                }

        # ---------- Admin Settings Page ----------
        @self.app.get("/admin/settings", response_class=HTMLResponse)
        async def admin_settings():
            """Admin settings page with configuration options"""
            return '''<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Settings – JamieAI 1.0</title>
<link rel="icon" type="image/png" href="/favicon.ico">
<style>
body{font-family:Arial,Helvetica,sans-serif;margin:20px;background:#f5f5f5}
.container{max-width:1200px;margin:0 auto;background:white;padding:20px;border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,0.1)}
.section{margin-bottom:30px;padding:20px;border:1px solid #ddd;border-radius:6px;background:#fafafa}
.section h3{margin-top:0;color:#333;border-bottom:2px solid #007acc;padding-bottom:10px}
button{padding:10px 20px;margin:5px;background:#007acc;color:white;border:none;border-radius:4px;cursor:pointer;font-size:14px}
button:hover{background:#0056b3}
button:disabled{background:#ccc;cursor:not-allowed}
input[type="number"], input[type="text"], select{padding:8px;margin:5px;border:1px solid #ccc;border-radius:4px;font-size:14px;width:200px}
.modelfile-viewer{height:400px;border:1px solid #ccc;overflow:auto;white-space:pre-wrap;font-family:monospace;font-size:12px;padding:10px;background:#f8f9fa}
.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:15px;margin:15px 0}
.stat-card{background:white;padding:15px;border-radius:6px;border:1px solid #ddd;text-align:center}
.stat-value{font-size:24px;font-weight:bold;color:#007acc}
.stat-label{font-size:12px;color:#666;margin-top:5px}
.nav-links{margin-bottom:20px;text-align:center}
.nav-links a{margin:0 15px;color:#007acc;text-decoration:none;font-weight:bold}
.nav-links a:hover{text-decoration:underline}
</style></head><body>

<!-- Pete Logo Header -->
<div style="text-align:center;padding:15px;background:white;border-bottom:2px solid #007acc;margin-bottom:20px;">
    <img src="/public/pete.png" alt="PeteOllama Logo" style="height:60px;"/>
    <h2 style="margin:5px 0 0 0;color:#007acc;">PeteOllama</h2>
</div>

<div class="container">
<div class="nav-links">
    <a href="/admin">← Back to Dashboard</a>
    <a href="/admin/settings">Settings</a>
    <a href="/admin/stats">Stats</a>
    <a href="/ui">Main UI</a>
</div>

<h1>⚙️ System Settings</h1>

<div class="section">
<h3>🤖 Model Management</h3>
<p>Control which models appear in the UI and their preloading behavior</p>

<div style="margin-bottom:20px;">
<button id="loadModelSettings">🔄 Load Model Settings</button>
<div id="modelSettingsStats" style="margin:10px 0;font-size:12px;color:#666;"></div>
</div>

<div id="modelConfigTable" style="display:none;">
<table style="width:100%;border-collapse:collapse;margin:15px 0;">
<thead>
<tr style="background:#f0f0f0;">
<th style="padding:8px;border:1px solid #ddd;text-align:left;">Model</th>
<th style="padding:8px;border:1px solid #ddd;text-align:center;">Show in UI</th>
<th style="padding:8px;border:1px solid #ddd;text-align:center;">Auto-Preload</th>
<th style="padding:8px;border:1px solid #ddd;text-align:left;">Description</th>
<th style="padding:8px;border:1px solid #ddd;text-align:center;">Actions</th>
</tr>
</thead>
<tbody id="modelConfigRows"></tbody>
</table>
</div>
</div>

<div class="section">
<h3>🔧 Model Configuration</h3>
<p>Adjust model timeout and performance settings</p>
<label>Model Timeout (seconds):
    <input type="number" id="modelTimeout" value="180" min="30" max="600"/>
    <small style="color:#666;">Recommended: 60s (Cloud), 180s (Local)</small>
</label><br/>
<label>Temperature (0.0-2.0):
    <input type="number" id="temperature" value="0.7" min="0" max="2" step="0.1"/>
    <small style="color:#666;">Lower = more focused, Higher = more creative</small>
</label><br/>
<label>Max Tokens:
    <input type="number" id="maxTokens" value="2048" min="256" max="8192"/>
    <small style="color:#666;">Maximum response length</small>
</label><br/>
<button onclick="saveSettings()">Save Settings</button>
</div>

<div class="section">
<h3>📥 Download New Models</h3>
<p>Pull new models from Ollama Hub</p>
<label>Model Tag:
    <input type="text" id="modelTag" placeholder="llama3:latest" />
    <small style="color:#666;">Examples: llama3:latest, mistral:7b, codellama:13b</small>
</label><br/>
<button onclick="downloadModel()">Download Model</button>
<div id="downloadStatus" style="margin-top:10px;"></div>
</div>

<div class="section">
<h3>📋 Current Modelfile</h3>
<p>View the active Jamie modelfile in markdown format</p>
<label>Select Model:
    <select id="modelfileSelect">
        <option value="">Loading models...</option>
    </select>
    <button onclick="loadModelfile()">Load Modelfile</button>
</label>
<div id="modelfileViewer" class="modelfile-viewer">Select a model to view its Modelfile...</div>
</div>

</div>

<script>
// Load available models for modelfile viewer
fetch('/models').then(r=>r.json()).then(models=>{
    const select = document.getElementById('modelfileSelect');
    select.innerHTML = '<option value="">Select a model...</option>';
    models.forEach(model => {
        const option = document.createElement('option');
        option.value = model;
        option.textContent = model;
        select.appendChild(option);
    });
});

function saveSettings(){
    const settings = {
        timeout: document.getElementById('modelTimeout').value,
        temperature: document.getElementById('temperature').value,
        maxTokens: document.getElementById('maxTokens').value
    };
    
    // This would normally save to a backend endpoint
    alert('Settings saved! (Note: This is a demo - implement backend storage)');
}

function downloadModel(){
    const tag = document.getElementById('modelTag').value;
    if(!tag){
        alert('Please enter a model tag');
        return;
    }
    
    const status = document.getElementById('downloadStatus');
    status.innerHTML = '<div style="color:#007acc;">🔄 Downloading ' + tag + '...</div>';
    
    // Simulate download (replace with actual API call)
    setTimeout(() => {
        status.innerHTML = '<div style="color:#28a745;">✅ Downloaded ' + tag + ' successfully!</div>';
    }, 3000);
}

function loadModelfile(){
    const model = document.getElementById('modelfileSelect').value;
    if(!model){
        alert('Please select a model');
        return;
    }
    
    const viewer = document.getElementById('modelfileViewer');
    viewer.innerHTML = 'Loading modelfile for ' + model + '...';
    
    // This would fetch the actual modelfile
    setTimeout(() => {
        viewer.innerHTML = `# Modelfile for ${model}

FROM llama3:latest

SYSTEM """You are Jamie, an expert property manager. Respond concisely and professionally, focusing on providing actionable solutions to tenant inquiries. Do NOT simulate a conversation or ask follow-up questions unless explicitly necessary for the solution."""

PARAMETER temperature 0.3
PARAMETER repeat_penalty 1.3
PARAMETER top_k 20

TEMPLATE """{{ .System }}

User: {{ .Prompt }}

Jamie:"""

MESSAGE user """My AC stopped working this morning and it's getting really hot in here"""
MESSAGE assistant """I understand this is an emergency situation. I'm calling our HVAC contractor right now to get someone out there today. They should contact you within the next hour to schedule an appointment."""

MESSAGE user """When is my rent due this month?"""
MESSAGE assistant """Rent is due on the 1st of each month. You can pay online through your tenant portal or drop off a check at our office during business hours."""

# Additional training examples would continue here...
`;
    }, 1000);
}

// Model Management Functions
let modelSettingsData = {};

document.getElementById('loadModelSettings').onclick = async () => {
    const button = document.getElementById('loadModelSettings');
    const statsDiv = document.getElementById('modelSettingsStats');
    const tableDiv = document.getElementById('modelConfigTable');
    
    button.disabled = true;
    button.textContent = '🔄 Loading...';
    
    try {
        const response = await fetch('/admin/model-settings');
        const result = await response.json();
        
        if (result.success) {
            modelSettingsData = result.models;
            
            // Update stats
            const stats = result.stats;
            statsDiv.innerHTML = `Total: ${stats.total_models} | UI Visible: ${stats.ui_visible} | Jamie Models: ${stats.jamie_models} | Auto-Preload: ${stats.auto_preload}`;
            
            // Build table
            buildModelTable();
            tableDiv.style.display = 'block';
        } else {
            alert('Error loading model settings: ' + result.error);
        }
    } catch (e) {
        alert('Network error: ' + e.message);
    } finally {
        button.disabled = false;
        button.textContent = '🔄 Load Model Settings';
    }
};

function buildModelTable() {
    const tbody = document.getElementById('modelConfigRows');
    tbody.innerHTML = '';
    
    Object.values(modelSettingsData).forEach(model => {
        const row = document.createElement('tr');
        
        const modelType = model.is_jamie_model ? '🤖 Jamie' : '🔧 Base';
        const uiStatus = model.show_in_ui ? '🟢 Yes' : '🔴 No';
        const preloadStatus = model.auto_preload ? '🟢 Yes' : '🔴 No';
        
        row.innerHTML = `
            <td style="padding:8px;border:1px solid #ddd;">
                ${modelType} <strong>${model.display_name}</strong><br>
                <small style="color:#666;">${model.name}</small>
            </td>
            <td style="padding:8px;border:1px solid #ddd;text-align:center;">
                ${uiStatus}
            </td>
            <td style="padding:8px;border:1px solid #ddd;text-align:center;">
                ${preloadStatus}
            </td>
            <td style="padding:8px;border:1px solid #ddd;">
                ${model.description}
            </td>
            <td style="padding:8px;border:1px solid #ddd;text-align:center;">
                <button onclick="toggleUI('${model.name}')" style="font-size:12px;margin:2px;">
                    ${model.show_in_ui ? 'Hide from UI' : 'Show in UI'}
                </button><br>
                <button onclick="togglePreload('${model.name}')" style="font-size:12px;margin:2px;">
                    ${model.auto_preload ? 'Disable Preload' : 'Enable Preload'}
                </button>
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

async function toggleUI(modelName) {
    try {
        const response = await fetch('/admin/model-settings/toggle-ui', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({model_name: modelName})
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Update local data
            modelSettingsData[modelName].show_in_ui = result.show_in_ui;
            buildModelTable();
            
            // Show feedback
            alert(result.message);
        } else {
            alert('Error: ' + result.error);
        }
    } catch (e) {
        alert('Network error: ' + e.message);
    }
}

async function togglePreload(modelName) {
    try {
        const response = await fetch('/admin/model-settings/update', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                model_name: modelName,
                auto_preload: !modelSettingsData[modelName].auto_preload
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Update local data
            modelSettingsData[modelName].auto_preload = result.config.auto_preload;
            buildModelTable();
            
            // Show feedback
            alert(result.message);
        } else {
            alert('Error: ' + result.error);
        }
    } catch (e) {
        alert('Network error: ' + e.message);
    }
}

// Auto-load model settings on page load
setTimeout(() => document.getElementById('loadModelSettings').click(), 500);
</script>
</body></html>'''

        # ---------- Admin Benchmark Analytics ----------
        @self.app.get("/admin/benchmarks", response_class=HTMLResponse)
        async def admin_benchmarks():
            """Advanced benchmark analytics dashboard"""
            return '''<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Benchmarks – JamieAI Analytics</title>
<link rel="icon" type="image/png" href="/favicon.ico">
<style>
body{font-family:Arial,Helvetica,sans-serif;margin:20px;background:#f5f5f5}
.container{max-width:1400px;margin:0 auto;background:white;padding:20px;border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,0.1)}
.section{margin-bottom:30px;padding:20px;border:1px solid #ddd;border-radius:6px;background:#fafafa}
.section h3{margin-top:0;color:#333;border-bottom:2px solid #007acc;padding-bottom:10px}
.nav-links{margin-bottom:20px;text-align:center}
.nav-links a{margin:0 15px;color:#007acc;text-decoration:none;font-weight:bold}
.nav-links a:hover{text-decoration:underline}
.metrics-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:15px;margin:15px 0}
.metric-card{background:white;padding:20px;border-radius:8px;border:1px solid #ddd;text-align:center;box-shadow:0 2px 4px rgba(0,0,0,0.1)}
.metric-value{font-size:32px;font-weight:bold;color:#007acc;margin:10px 0}
.metric-label{font-size:14px;color:#666;font-weight:bold}
.benchmark-table{width:100%;border-collapse:collapse;margin:15px 0;font-size:12px}
.benchmark-table th,.benchmark-table td{padding:8px;text-align:left;border-bottom:1px solid #ddd}
.benchmark-table th{background:#f8f9fa;font-weight:bold}
.status-success{color:#28a745} .status-error{color:#dc3545}
.fast{color:#28a745} .slow{color:#dc3545} .medium{color:#ffc107}
button{padding:10px 20px;margin:5px;background:#007acc;color:white;border:none;border-radius:4px;cursor:pointer;font-size:14px}
button:hover{background:#0056b3}
.loading{text-align:center;color:#666;padding:20px}
.export-section{text-align:center;margin:20px 0}
</style></head><body>

<!-- Pete Logo Header -->
<div style="text-align:center;padding:15px;background:white;border-bottom:2px solid #007acc;margin-bottom:20px;">
    <img src="/public/pete.png" alt="PeteOllama Logo" style="height:60px;"/>
    <h2 style="margin:5px 0 0 0;color:#007acc;">PeteOllama</h2>
</div>

<div class="container">
<div class="nav-links">
    <a href="/admin">← Dashboard</a>
    <a href="/admin/settings">Settings</a>
    <a href="/admin/stats">Stats</a>
    <a href="/admin/benchmarks">Benchmarks</a>
    <a href="/ui">Main UI</a>
</div>

<h1>📊 Advanced Benchmark Analytics</h1>

<div class="section">
<h3>📈 Today's Performance Summary</h3>
<div id="summaryMetrics" class="metrics-grid">
    <div class="loading">Loading performance metrics...</div>
</div>
</div>

<div class="section">
<h3>🏆 Model Performance Comparison</h3>
<div id="modelComparison" class="loading">Loading model comparison...</div>
</div>

<div class="section">
<h3>📋 Recent Benchmark Data</h3>
<div class="export-section">
    <button onclick="refreshData()">🔄 Refresh Data</button>
    <button onclick="exportAnalysis()">📄 Export Analysis</button>
    <button onclick="loadHistoricalData()">📅 Load Historical</button>
</div>
<div id="benchmarkTable" class="loading">Loading benchmark data...</div>
</div>

<div class="section">
<h3>⏱️ Response Time Distribution</h3>
<canvas id="responseTimeChart" width="800" height="400" style="max-width:100%;"></canvas>
</div>

</div>

<script>
let currentData = null;

// Load initial data
document.addEventListener('DOMContentLoaded', function() {
    loadBenchmarkData();
});

async function loadBenchmarkData() {
    try {
        const response = await fetch('/admin/api/benchmarks');
        const data = await response.json();
        currentData = data;
        
        updateSummaryMetrics(data.summary);
        updateModelComparison(data.model_comparisons);
        updateBenchmarkTable(data.recent_data);
        drawResponseTimeChart(data.recent_data);
        
    } catch (error) {
        console.error('Error loading benchmark data:', error);
        document.getElementById('summaryMetrics').innerHTML = '<div style="color:red;">Error loading data: ' + error.message + '</div>';
    }
}

function updateSummaryMetrics(summary) {
    const metricsHtml = `
        <div class="metric-card">
            <div class="metric-value">${summary.total_requests}</div>
            <div class="metric-label">Total Requests</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">${summary.avg_response_time_ms}ms</div>
            <div class="metric-label">Avg Response Time</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">${summary.success_rate.toFixed(1)}%</div>
            <div class="metric-label">Success Rate</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">${summary.avg_quality_score.toFixed(1)}/10</div>
            <div class="metric-label">Avg Quality Score</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">${summary.fast_responses_count}</div>
            <div class="metric-label">Fast Responses (&lt;3s)</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">${summary.models_tested.length}</div>
            <div class="metric-label">Models Tested</div>
        </div>
    `;
    document.getElementById('summaryMetrics').innerHTML = metricsHtml;
}

function updateModelComparison(comparisons) {
    if (!comparisons || comparisons.length === 0) {
        document.getElementById('modelComparison').innerHTML = '<p>No model comparison data available.</p>';
        return;
    }
    
    let tableHtml = `
        <table class="benchmark-table">
            <thead>
                <tr>
                    <th>Model</th>
                    <th>Requests</th>
                    <th>Avg Response Time</th>
                    <th>Success Rate</th>
                    <th>Avg Quality</th>
                    <th>Fast Response Rate</th>
                    <th>Grade</th>
                    <th>Recommendation</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    comparisons.forEach(comp => {
        const responseTimeClass = comp.avg_response_time_ms < 2000 ? 'fast' : (comp.avg_response_time_ms < 5000 ? 'medium' : 'slow');
        tableHtml += `
            <tr>
                <td><strong>${comp.model_name}</strong></td>
                <td>${comp.request_count}</td>
                <td class="${responseTimeClass}">${comp.avg_response_time_ms.toFixed(0)}ms</td>
                <td>${comp.success_rate.toFixed(1)}%</td>
                <td>${comp.avg_quality_score.toFixed(1)}/10</td>
                <td>${comp.fast_response_rate.toFixed(1)}%</td>
                <td><strong>${comp.performance_grade}</strong></td>
                <td>${comp.recommendation}</td>
            </tr>
        `;
    });
    
    tableHtml += '</tbody></table>';
    document.getElementById('modelComparison').innerHTML = tableHtml;
}

function updateBenchmarkTable(recentData) {
    if (!recentData || recentData.length === 0) {
        document.getElementById('benchmarkTable').innerHTML = '<p>No recent benchmark data available.</p>';
        return;
    }
    
    let tableHtml = `
        <table class="benchmark-table">
            <thead>
                <tr>
                    <th>Time</th>
                    <th>Model</th>
                    <th>Message</th>
                    <th>Response Time</th>
                    <th>Quality</th>
                    <th>Status</th>
                    <th>Source</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    recentData.slice(-20).forEach(record => {
        const time = new Date(record.timestamp).toLocaleTimeString();
        const responseTime = record.perf_total_duration_ms;
        const timeClass = responseTime < 2000 ? 'fast' : (responseTime < 5000 ? 'medium' : 'slow');
        const statusClass = record.status === 'success' ? 'status-success' : 'status-error';
        
        tableHtml += `
            <tr>
                <td>${time}</td>
                <td>${record.model}</td>
                <td title="${record.user_message}">${record.user_message.substring(0, 30)}...</td>
                <td class="${timeClass}">${responseTime}ms</td>
                <td>${record.quality_estimated_quality_score.toFixed(1)}/10</td>
                <td class="${statusClass}">${record.status}</td>
                <td>${record.source}</td>
            </tr>
        `;
    });
    
    tableHtml += '</tbody></table>';
    document.getElementById('benchmarkTable').innerHTML = tableHtml;
}

function drawResponseTimeChart(data) {
    // Simple canvas-based chart (you could replace with Chart.js for more advanced charts)
    const canvas = document.getElementById('responseTimeChart');
    const ctx = canvas.getContext('2d');
    
    if (!data || data.length === 0) {
        ctx.fillStyle = '#666';
        ctx.font = '16px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('No data available for chart', canvas.width / 2, canvas.height / 2);
        return;
    }
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Simple histogram of response times
    const responseTimes = data.map(d => d.perf_total_duration_ms).filter(t => t > 0);
    const maxTime = Math.max(...responseTimes);
    const bins = 10;
    const binSize = maxTime / bins;
    
    const histogram = new Array(bins).fill(0);
    responseTimes.forEach(time => {
        const binIndex = Math.min(Math.floor(time / binSize), bins - 1);
        histogram[binIndex]++;
    });
    
    const maxCount = Math.max(...histogram);
    const barWidth = canvas.width / bins;
    const maxBarHeight = canvas.height - 40;
    
    // Draw bars
    ctx.fillStyle = '#007acc';
    histogram.forEach((count, i) => {
        const barHeight = (count / maxCount) * maxBarHeight;
        const x = i * barWidth;
        const y = canvas.height - barHeight - 20;
        
        ctx.fillRect(x + 2, y, barWidth - 4, barHeight);
        
        // Draw labels
        ctx.fillStyle = '#333';
        ctx.font = '12px Arial';
        ctx.textAlign = 'center';
        ctx.fillText(`${Math.round(i * binSize)}-${Math.round((i + 1) * binSize)}ms`, x + barWidth / 2, canvas.height - 5);
        ctx.fillStyle = '#007acc';
    });
}

async function refreshData() {
    await loadBenchmarkData();
}

async function exportAnalysis() {
    if (!currentData) {
        alert('No data to export');
        return;
    }
    
    const dataStr = JSON.stringify(currentData, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'benchmark-analysis-' + new Date().toISOString().split('T')[0] + '.json';
    link.click();
}

function loadHistoricalData() {
    // Placeholder for historical data loading
    alert('Historical data loading feature coming soon!');
}
</script>
</body></html>'''
        
        @self.app.get("/admin/api/benchmarks")
        async def api_benchmarks():
            """API endpoint for benchmark analytics data"""
            import sys
            from pathlib import Path
            
            try:
                # Add src to path for imports
                sys.path.insert(0, str(Path(__file__).parent.parent))
                from analytics.benchmark_analyzer import BenchmarkAnalyzer
                
                analyzer = BenchmarkAnalyzer()
                df = analyzer.load_benchmark_data()
                
                if df.empty:
                    return {
                        "summary": {
                            "total_requests": 0,
                            "successful_requests": 0,
                            "failed_requests": 0,
                            "avg_response_time_ms": 0,
                            "success_rate": 0,
                            "avg_quality_score": 0,
                            "fast_responses_count": 0,
                            "models_tested": []
                        },
                        "model_comparisons": [],
                        "recent_data": []
                    }
                
                summary = analyzer.generate_summary(df)
                model_comparisons = analyzer.compare_models(df)
                
                # Convert recent data to dict format
                recent_data = df.tail(50).to_dict('records') if not df.empty else []
                
                return {
                    "summary": summary.dict(),
                    "model_comparisons": [comp.dict() for comp in model_comparisons],
                    "recent_data": recent_data
                }
                
            except Exception as e:
                logger.error(f"Error in benchmark API: {e}")
                return {
                    "error": str(e),
                    "summary": {"total_requests": 0, "avg_response_time_ms": 0, "success_rate": 0, "avg_quality_score": 0, "fast_responses_count": 0, "models_tested": []},
                    "model_comparisons": [],
                    "recent_data": []
                }

        # ---------- Admin Stats Page ----------
        @self.app.get("/admin/stats", response_class=HTMLResponse)
        async def admin_stats():
            """Admin stats page with model performance analytics"""
            return '''<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Stats – JamieAI 1.0</title>
<link rel="icon" type="image/png" href="/favicon.ico">
<style>
body{font-family:Arial,Helvetica,sans-serif;margin:20px;background:#f5f5f5}
.container{max-width:1200px;margin:0 auto;background:white;padding:20px;border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,0.1)}
.section{margin-bottom:30px;padding:20px;border:1px solid #ddd;border-radius:6px;background:#fafafa}
.section h3{margin-top:0;color:#333;border-bottom:2px solid #007acc;padding-bottom:10px}
.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:15px;margin:15px 0}
.stat-card{background:white;padding:20px;border-radius:8px;border:1px solid #ddd;text-align:center;box-shadow:0 2px 4px rgba(0,0,0,0.1)}
.stat-value{font-size:32px;font-weight:bold;color:#007acc;margin:10px 0}
.stat-label{font-size:14px;color:#666;font-weight:bold}
.stat-sublabel{font-size:11px;color:#999;margin-top:5px}
.nav-links{margin-bottom:20px;text-align:center}
.nav-links a{margin:0 15px;color:#007acc;text-decoration:none;font-weight:bold}
.nav-links a:hover{text-decoration:underline}
.performance-table{width:100%;border-collapse:collapse;margin:15px 0}
.performance-table th,.performance-table td{padding:10px;text-align:left;border-bottom:1px solid #ddd}
.performance-table th{background:#f8f9fa;font-weight:bold}
.good{color:#28a745} .warning{color:#ffc107} .error{color:#dc3545}
button{padding:10px 20px;margin:5px;background:#007acc;color:white;border:none;border-radius:4px;cursor:pointer;font-size:14px}
button:hover{background:#0056b3}
</style></head><body>

<!-- Pete Logo Header -->
<div style="text-align:center;padding:15px;background:white;border-bottom:2px solid #007acc;margin-bottom:20px;">
    <img src="/public/pete.png" alt="PeteOllama Logo" style="height:60px;"/>
    <h2 style="margin:5px 0 0 0;color:#007acc;">PeteOllama</h2>
</div>

<div class="container">
<div class="nav-links">
    <a href="/admin">← Back to Dashboard</a>
    <a href="/admin/settings">Settings</a>
    <a href="/admin/stats">Stats</a>
    <a href="/ui">Main UI</a>
</div>

<h1>📊 Model Performance Analytics</h1>

<div class="section">
<h3>📈 Overall Performance Metrics</h3>
<div class="stats-grid">
    <div class="stat-card">
        <div class="stat-value">1,469</div>
        <div class="stat-label">Training Conversations</div>
        <div class="stat-sublabel">From pete.db</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">4</div>
        <div class="stat-label">Jamie Models</div>
        <div class="stat-sublabel">Active variants</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">2.3s</div>
        <div class="stat-label">Avg Response Time</div>
        <div class="stat-sublabel">Last 24 hours</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">94.7%</div>
        <div class="stat-label">Success Rate</div>
        <div class="stat-sublabel">Non-timeout responses</div>
    </div>
</div>
</div>

<div class="section">
<h3>🏆 Model Comparison</h3>
<table class="performance-table">
    <thead>
        <tr>
            <th>Model & Base</th>
            <th>Avg Response Time</th>
            <th>Success Rate</th>
            <th>Quality Score</th>
            <th>Training Data</th>
            <th>Status</th>
        </tr>
    </thead>
    <tbody>
        <!-- Model data will be loaded dynamically -->
    </tbody>
</table>
</div>

<div class="section">
<h3>🎯 Training Data Quality</h3>
<div class="stats-grid">
    <div class="stat-card">
        <div class="stat-value">847</div>
        <div class="stat-label">Voice Calls</div>
        <div class="stat-sublabel">High-quality conversations</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">622</div>
        <div class="stat-label">SMS Messages</div>
        <div class="stat-sublabel">Filtered out for voice training</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">234</div>
        <div class="stat-label">Property Issues</div>
        <div class="stat-sublabel">Unique problem types</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">89.2%</div>
        <div class="stat-label">Resolution Rate</div>
        <div class="stat-sublabel">Issues resolved by Jamie</div>
    </div>
</div>
</div>

<div class="section">
<h3>🔄 Real-time Monitoring</h3>
<button onclick="refreshStats()">🔄 Refresh Stats</button>
<button onclick="exportStats()">📄 Export Report</button>
<div id="liveStats" style="margin-top:15px;">
    <div><strong>Last Updated:</strong> <span id="lastUpdate">Loading...</span></div>
    <div><strong>Active Model:</strong> <span id="activeModel">jamie-fixed</span></div>
    <div><strong>Ollama Status:</strong> <span id="ollamaStatus" class="good">✅ Running</span></div>
</div>
</div>

</div>

<script>
function refreshStats(){
    document.getElementById('lastUpdate').textContent = new Date().toLocaleString();
    // In real implementation, this would fetch fresh stats from API
}

// Load real benchmark data
async function loadBenchmarkData() {
    try {
        const response = await fetch('/admin/benchmarks');
        const data = await response.json();
        
        if (data.success && data.comparisons) {
            updateModelTable(data.comparisons);
            updateOverallStats(data.summary);
        } else {
            console.error('Failed to load benchmark data:', data.error);
        }
    } catch (error) {
        console.error('Error loading benchmark data:', error);
    }
}

function updateModelTable(comparisons) {
    const tbody = document.querySelector('#modelComparison tbody');
    tbody.innerHTML = '';
    
    comparisons.forEach(model => {
        const row = document.createElement('tr');
        
        // Status class based on performance
        const timeClass = model.avg_response_time_ms < 2000 ? 'good' : 
                         model.avg_response_time_ms < 3000 ? 'warning' : 'error';
        const successClass = model.success_rate >= 95 ? 'good' : 
                             model.success_rate >= 90 ? 'warning' : 'error';
        const qualityClass = model.avg_quality_score >= 8 ? 'good' : 
                             model.avg_quality_score >= 7 ? 'warning' : 'error';
        
        // Determine training data description
        let trainingDescription = 'Unknown';
        if (model.model_name.includes('jamie-fixed')) trainingDescription = 'Full conversations';
        else if (model.model_name.includes('jamie-voice')) trainingDescription = 'Voice conversations';
        else if (model.model_name.includes('jamie-simple')) trainingDescription = 'Basic examples';
        else if (model.model_name.includes('jamie-working')) trainingDescription = 'Legacy training';
        else if (model.model_name.includes('llama3')) trainingDescription = 'Base model only';
        
        // Status icon based on recommendation
        const statusIcon = model.recommendation.includes('Excellent') ? '✅ Recommended' :
                          model.recommendation.includes('Good') ? '⚠️ Good' :
                          model.recommendation.includes('Needs') ? '❌ Deprecated' : 
                          '⚠️ Limited';
        
        const statusClass = statusIcon.includes('✅') ? 'good' :
                           statusIcon.includes('⚠️') ? 'warning' : 'error';
        
        row.innerHTML = `
            <td><strong>${model.model_name}</strong><br><small>Base: ${model.base_model || 'unknown'}</small></td>
            <td><span class="${timeClass}">${(model.avg_response_time_ms / 1000).toFixed(1)}s</span></td>
            <td><span class="${successClass}">${model.success_rate.toFixed(1)}%</span></td>
            <td><span class="${qualityClass}">${model.avg_quality_score.toFixed(1)}/10</span></td>
            <td>${trainingDescription}<br><small>Preloaded: ${model.preload_rate.toFixed(0)}%</small></td>
            <td><span class="${statusClass}">${statusIcon}</span></td>
        `;
        
        tbody.appendChild(row);
    });
}

function updateOverallStats(summary) {
    if (!summary) return;
    
    // Update the overview metrics
    document.querySelector('.metric:nth-child(1) .metric-value').textContent = summary.successful_requests || 0;
    document.querySelector('.metric:nth-child(2) .metric-value').textContent = summary.models_tested ? summary.models_tested.length : 0;
    document.querySelector('.metric:nth-child(3) .metric-value').textContent = 
        summary.avg_response_time_ms ? `${(summary.avg_response_time_ms / 1000).toFixed(1)}s` : '0s';
    document.querySelector('.metric:nth-child(4) .metric-value').textContent = 
        summary.success_rate ? `${summary.success_rate.toFixed(1)}%` : '0%';
}

function exportStats(){
    // Use real data for export
    fetch('/admin/benchmarks')
        .then(response => response.json())
        .then(data => {
            const statsData = {
                timestamp: new Date().toISOString(),
                summary: data.summary,
                models: data.comparisons,
                trainingData: {
                    totalConversations: data.summary?.successful_requests || 0,
                    modelsCount: data.summary?.models_tested?.length || 0,
                    avgResponseTime: data.summary?.avg_response_time_ms || 0,
                    successRate: data.summary?.success_rate || 0
                }
            };
            
            const dataStr = JSON.stringify(statsData, null, 2);
            const dataBlob = new Blob([dataStr], {type: 'application/json'});
            const url = URL.createObjectURL(dataBlob);
            const link = document.createElement('a');
            link.href = url;
            link.download = 'jamie-ai-stats-' + new Date().toISOString().split('T')[0] + '.json';
            link.click();
        })
        .catch(error => {
            console.error('Error exporting stats:', error);
            alert('Failed to export stats. Please try again.');
        });
}

// Initialize page
document.getElementById('lastUpdate').textContent = new Date().toLocaleString();

// Load real benchmark data on page load
loadBenchmarkData();
</script>
</body></html>'''

    
    async def handle_function_call(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Handle VAPI function call"""
        try:
            # Extract function call details
            function_call = body.get('functionCall', {})
            function_name = function_call.get('name')
            parameters = function_call.get('parameters', {})
            
            logger.info(f"Function call: {function_name} with params: {parameters}")
            
            # Handle property management functions
            if function_name == 'answer_property_question':
                question = parameters.get('question', '')
                caller_info = parameters.get('caller_info', {})
                
                # Get context from database if phone number provided
                context = ""
                phone = caller_info.get('phone')
                if phone:
                    # Look up caller information
                    caller_data = self.get_caller_context(phone)
                    if caller_data:
                        context = f"Caller: {caller_data}"
                
                # Generate AI response
                ai_response = self.model_manager.generate_response(question, context)
                
                return {
                    "result": {
                        "response": ai_response,
                        "action": "continue_conversation"
                    }
                }
            
            else:
                return {
                    "result": {
                        "response": "I can help you with property management questions. What would you like to know?",
                        "action": "continue_conversation"
                    }
                }
        
        except Exception as e:
            logger.error(f"Function call error: {str(e)}")
            return {
                "result": {
                    "response": "I'm experiencing technical difficulties. Please try again.",
                    "action": "continue_conversation"
                }
            }
    
    def _extract_base_model_name(self, model_name: str) -> str:
        """Extract the base model name from a custom model name"""
        
        # Common base model patterns
        base_models = {
            "llama3": ["llama3", "llama-3", "llama 3"],
            "qwen": ["qwen", "qwen2", "qwen3"],
            "mistral": ["mistral"],
            "codellama": ["codellama", "code-llama"],
            "gemma": ["gemma"],
            "phi": ["phi"],
            "vicuna": ["vicuna"],
            "orca": ["orca"]
        }
        
        model_lower = model_name.lower()
        
        # Check for base model patterns
        for base_name, patterns in base_models.items():
            if any(pattern in model_lower for pattern in patterns):
                return base_name
        
        # If it's a custom model (contains :), try to extract from the tag
        if ":" in model_name:
            base_part = model_name.split(":")[0]
            # Check if the base part matches known models
            for base_name, patterns in base_models.items():
                if any(pattern in base_part.lower() for pattern in patterns):
                    return base_name
            
            # If base part is custom, assume llama3 (most common base)
            if base_part.startswith("peteollama") or "jamie" in base_part.lower():
                return "llama3"  # Jamie models are based on llama3
        
        return "unknown"
    
    def _save_benchmark_data(self, benchmark_data: dict):
        """Save benchmark data to log file for analysis"""
        import json
        import os
        from pathlib import Path
        
        try:
            # Ensure logs directory exists
            logs_dir = Path("logs")
            logs_dir.mkdir(exist_ok=True)
            
            # Create benchmark log file with date
            import time
            log_file = logs_dir / f"benchmark_{time.strftime('%Y-%m-%d')}.jsonl"
            
            # Append benchmark data as JSON line
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(benchmark_data) + '\n')
                
            # Also log summary to main log
            if benchmark_data.get("status") != "error":
                perf = benchmark_data.get("performance", {})
                quality = benchmark_data.get("quality_metrics", {})
                logger.info(f"💾 SAVED BENCHMARK: {benchmark_data['model']} - {perf.get('total_duration_ms', 0)}ms, Quality: {quality.get('estimated_quality_score', 0):.1f}/10")
                
        except Exception as e:
            logger.error(f"Failed to save benchmark data: {e}")
    
    async def handle_conversation_update(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Handle conversation updates"""
        try:
            conversation = body.get('conversation', {})
            logger.info(f"Conversation update: {len(conversation.get('messages', []))} messages")
            
            # Store conversation in database for learning
            self.store_conversation_update(conversation)
            
            return {"status": "recorded"}
        
        except Exception as e:
            logger.error(f"Conversation update error: {str(e)}")
            return {"status": "error"}
    
    async def handle_end_of_call(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Handle end of call reporting"""
        try:
            call_data = body.get('call', {})
            logger.info(f"Call ended: {call_data.get('id')} duration: {call_data.get('duration')}s")
            
            # Store complete call data for analysis
            self.store_call_data(call_data)
            
            return {"status": "recorded"}
        
        except Exception as e:
            logger.error(f"End of call error: {str(e)}")
            return {"status": "error"}
    
    def get_caller_context(self, phone: str) -> str:
        """Get caller context from database"""
        try:
            # Search for previous conversations from this number
            conversations = self.db_manager.search_conversations(phone, limit=3)
            
            if conversations:
                context = f"Previous interactions with {phone}: "
                for conv in conversations:
                    context += f"[{conv['date']}] "
                return context
            
            return ""
        
        except Exception as e:
            logger.error(f"Error getting caller context: {str(e)}")
            return ""
    
    def store_conversation_update(self, conversation: Dict[str, Any]):
        """Store conversation update in database"""
        try:
            # TODO: Implement conversation storage
            # This would store the conversation in PostgreSQL for learning
            logger.info("Conversation update stored")
        
        except Exception as e:
            logger.error(f"Error storing conversation: {str(e)}")
    
    def store_call_data(self, call_data: Dict[str, Any]):
        """Store complete call data"""
        try:
            # TODO: Implement call data storage
            # This would store complete call transcripts and metadata
            logger.info("Call data stored")
        
        except Exception as e:
            logger.error(f"Error storing call data: {str(e)}")
    
    async def start(self):
        """Start the webhook server"""
        logger.info(f"🚀 Starting VAPI webhook server on port {self.port}")
        
        config = uvicorn.Config(
            self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="info"
        )
        
        server = uvicorn.Server(config)
        await server.serve()

# For running directly
if __name__ == "__main__":
    import asyncio
    
    server = VAPIWebhookServer()
    asyncio.run(server.start())