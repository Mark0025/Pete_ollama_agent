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
from database.pete_db_manager import PeteDBManager
from utils.logger import logger

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
            """Return list of personas (model + icon)."""
            models = self.model_manager.list_models()
            persona_list = []
            for m in models:
                name = m.get("name")
                if name == self.model_manager.custom_model_name:
                    icon = "/public/pm.png"
                else:
                    icon = "/public/pete.png"
                persona_list.append({"name": name, "icon": icon})
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
            try:
                body = await request.json()
                message = body.get('message', '')
                model_name = body.get('model')
                if not message:
                    raise HTTPException(status_code=400, detail="Message required")

                def token_iter():
                    for token in self.model_manager.generate_stream(message, model_name=model_name):
                        yield token
                return StreamingResponse(token_iter(), media_type='text/plain')
            except Exception as e:
                logger.error(f"Stream message error: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        # ---------- Simple HTML UI ----------
        @self.app.get("/ui", response_class=HTMLResponse)
        async def user_interface():
            """Basic browser UI for manual testing"""
            return '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>PeteOllama Chat</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; text-align:center; }
        #personas { position: fixed; left: 10px; top: 120px; display: flex; flex-direction: column; gap: 10px; }
        .persona-icon { width: 48px; height: 48px; border: 2px solid transparent; border-radius: 6px; cursor: pointer; }
        .persona-icon.active { border-color: #007bff; }
        #log { width: 100%; height: 400px; border: 1px solid #ccc; padding: 10px; overflow-y: auto; }
        #msg { width: 80%; padding: 10px; }
        #send { padding: 10px; }
    </style>
</head>
<body>
    <div id="personas"></div>
    <img src="/public/pete.png" alt="PeteOllama Logo" style="height:80px;"/>
    <h1>PeteOllama Chat</h1>
    <div id="log"></div><br/>
    <label>Model:
        <select id="model"></select>
    </label><br/><br/>
    <input id="msg" placeholder="Type a message"/>
    <button id="send">Send</button>
    <script>
    const log = document.getElementById('log');
    const modelSelect = document.getElementById('model');

    // Populate model list
    fetch('/models').then(r => r.json()).then(list => {
        list.forEach(name => {
            const opt = document.createElement('option');
            opt.value = name;
            opt.textContent = name;
            modelSelect.appendChild(opt);
        });
    });

    // Populate persona icons
    fetch('/personas').then(r=>r.json()).then(list=>{
        const bar=document.getElementById('personas');
        list.forEach(p=>{
            const img=document.createElement('img');
            img.src=p.icon; img.title=p.name; img.className='persona-icon';
            img.onclick=()=>{
                Array.from(document.getElementsByClassName('persona-icon')).forEach(el=>el.classList.remove('active'));
                img.classList.add('active');
                modelSelect.value=p.name;
            };
            bar.appendChild(img);
            // set first as active default
            if(p.name===modelSelect.value||!modelSelect.value){img.classList.add('active');}
        });
    });

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
            """Minimal admin dashboard for training and testing"""
            return '''<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Admin – JamieAI 1.0</title>
<style>
body{font-family:Arial,Helvetica,sans-serif;margin:40px}
#samples{width:100%;height:250px;border:1px solid #ccc;overflow:auto;white-space:pre;font-size:12px;padding:6px}
#log{height:120px;border:1px solid #ccc;overflow:auto;white-space:pre;font-size:12px;padding:6px;margin-top:10px}
button{padding:8px 16px;margin-top:10px}
</style></head><body>
<h1>JamieAI 1.0 – Training Dashboard</h1>
<p>Preview training samples pulled from pete.db</p>
<button id="refresh">Load Samples</button>
<button id="train">Train Property-Manager Model</button>
<div id="samples"></div>
<h3>Training Log</h3>
<div id="log"></div>
<script>
const samplesDiv=document.getElementById('samples');
const logDiv=document.getElementById('log');
function appendLog(txt){logDiv.innerText+=txt+'\n';logDiv.scrollTop=logDiv.scrollHeight;}

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
                        # move DB to /app so ModelManager can load it
                        import shutil, os, pathlib
                        src_db = pathlib.Path(extractor.target_db_path)
                        dst_db = pathlib.Path("/app/pete.db")
                        try:
                            shutil.copy2(src_db, dst_db)
                            yield "Copied pete.db to /app\n"
                            os.environ["PETE_DB_PATH"] = str(dst_db)
                        except Exception as e:
                            yield f"Copy error: {e}\n"
                    yield ("Extraction success\n" if ok else "Extraction failed\n")
                except Exception as e:
                    yield f"Extraction error: {e}\n"
                    return
                yield "Training model...\n"
                ok = self.model_manager.train_property_manager()
                yield ("Training started\n" if ok else "Training failed\n")
            return StreamingResponse(iter_logs(), media_type='text/plain')

    
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