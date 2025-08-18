"""
Model Preloader for keeping Ollama models warm in memory.
"""
import asyncio
import subprocess
import time
from typing import Dict, Set, List
from loguru import logger
import threading
from concurrent.futures import ThreadPoolExecutor

class OllamaModelPreloader:
    """Manages preloading and keeping Ollama models warm in memory."""
    
    def __init__(self):
        self.loaded_models: Set[str] = set()
        self.model_load_times: Dict[str, float] = {}
        self.preload_lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=2)
        self._shutdown = False
        
    def is_model_loaded(self, model_name: str) -> bool:
        """Check if a model is currently loaded in memory."""
        try:
            # Check if model process is running
            result = subprocess.run([
                "ollama", "ps"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                # Look for the model in the running processes
                return model_name in result.stdout
            
            return False
        except Exception as e:
            logger.warning(f"Could not check model status: {e}")
            return False
    
    def preload_model(self, model_name: str, unload_others: bool = True) -> bool:
        """
        Preload a model into memory using a lightweight prompt.
        
        Args:
            model_name: The model to preload
            unload_others: Whether to unload other models first (default: True)
        
        Returns:
            True if successful, False otherwise.
        """
        with self.preload_lock:
            # Unload other models first if requested
            if unload_others and self.loaded_models:
                for loaded_model in list(self.loaded_models):
                    if loaded_model != model_name:
                        self.unload_model(loaded_model)
            
            if model_name in self.loaded_models:
                logger.info(f"Model {model_name} already loaded")
                return True
            
            try:
                logger.info(f"🔄 Preloading model {model_name} into memory...")
                start_time = time.time()
                
                # Use a very simple prompt to load the model
                result = subprocess.run([
                    "ollama", "run", model_name, "Hi"
                ], capture_output=True, text=True, timeout=300)  # 5 min timeout for first load
                
                load_time = time.time() - start_time
                
                if result.returncode == 0:
                    self.loaded_models.add(model_name)
                    self.model_load_times[model_name] = load_time
                    logger.info(f"✅ Model {model_name} preloaded in {load_time:.2f}s")
                    return True
                else:
                    logger.error(f"❌ Failed to preload {model_name}: {result.stderr}")
                    return False
                    
            except subprocess.TimeoutExpired:
                logger.error(f"❌ Timeout preloading {model_name}")
                return False
            except Exception as e:
                logger.error(f"❌ Error preloading {model_name}: {e}")
                return False
    
    def unload_model(self, model_name: str) -> bool:
        """
        Unload a model from memory.
        
        Args:
            model_name: The model to unload
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Stop the model process
            result = subprocess.run([
                "ollama", "stop", model_name
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.loaded_models.discard(model_name)
                logger.info(f"🗑️ Model {model_name} unloaded from memory")
                return True
            else:
                logger.warning(f"⚠️ Could not unload {model_name}: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error unloading {model_name}: {e}")
            return False
    
    async def preload_model_async(self, model_name: str) -> bool:
        """Async wrapper for preload_model."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self.preload_model, model_name)
    
    def preload_jamie_models(self) -> Dict[str, bool]:
        """Preload all Jamie model variants."""
        jamie_models = [
            "peteollama:jamie-fixed",
            "peteollama:jamie-simple", 
            "peteollama:jamie-voice-complete",
            "llama3:latest"  # Base model
        ]
        
        results = {}
        logger.info(f"🚀 Starting preload of {len(jamie_models)} models...")
        
        for model in jamie_models:
            try:
                results[model] = self.preload_model(model)
                # Small delay between loads to avoid overwhelming system
                time.sleep(2)
            except Exception as e:
                logger.error(f"Error preloading {model}: {e}")
                results[model] = False
        
        loaded_count = sum(1 for success in results.values() if success)
        logger.info(f"📊 Preload complete: {loaded_count}/{len(jamie_models)} models loaded")
        
        return results
    
    def get_model_info(self, model_name: str) -> Dict:
        """Get information about a model's load status and performance."""
        return {
            "name": model_name,
            "loaded": model_name in self.loaded_models,
            "load_time": self.model_load_times.get(model_name, 0),
            "is_running": self.is_model_loaded(model_name),
            "base_model": self._get_base_model(model_name)
        }
    
    def _get_base_model(self, model_name: str) -> str:
        """Determine the base model for a given model."""
        if "jamie" in model_name.lower():
            return "llama3:latest"  # Most Jamie models are based on llama3
        elif "llama3" in model_name.lower():
            return "llama3:latest"
        else:
            return "unknown"
    
    def get_all_models_status(self) -> List[Dict]:
        """Get status of all known models."""
        known_models = [
            "peteollama:jamie-fixed",
            "peteollama:jamie-simple", 
            "peteollama:jamie-voice-complete",
            "peteollama:jamie-working-working_20250806",
            "llama3:latest"
        ]
        
        return [self.get_model_info(model) for model in known_models]
    
    def keep_warm(self, model_name: str, interval_minutes: int = 30):
        """
        Keep a model warm by sending periodic lightweight requests.
        This should be run in a background thread.
        """
        def warm_model():
            while True:
                try:
                    if model_name in self.loaded_models:
                        # Send a very short prompt to keep model active
                        subprocess.run([
                            "ollama", "run", model_name, "?"
                        ], capture_output=True, text=True, timeout=30)
                        logger.debug(f"🔥 Kept {model_name} warm")
                    
                    time.sleep(interval_minutes * 60)  # Convert to seconds
                    
                except Exception as e:
                    logger.warning(f"Error keeping {model_name} warm: {e}")
                    time.sleep(60)  # Retry in 1 minute on error
        
        # Run in background thread
        thread = threading.Thread(target=warm_model, daemon=True)
        thread.start()
        logger.info(f"🔥 Started keep-warm thread for {model_name}")
    
    def shutdown(self):
        """Shutdown the preloader and clean up resources."""
        logger.info("🧹 Shutting down model preloader...")
        self._shutdown = True
        
        # Shutdown the executor
        try:
            self.executor.shutdown(wait=True, timeout=30)
            logger.info("✅ ThreadPoolExecutor shutdown complete")
        except Exception as e:
            logger.warning(f"⚠️ ThreadPoolExecutor shutdown warning: {e}")
        
        # Unload all models
        if self.loaded_models:
            logger.info(f"🗑️ Unloading {len(self.loaded_models)} models...")
            for model in list(self.loaded_models):
                try:
                    self.unload_model(model)
                except Exception as e:
                    logger.warning(f"⚠️ Error unloading {model}: {e}")
        
        logger.info("✅ Model preloader shutdown complete")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        if not self._shutdown:
            try:
                self.shutdown()
            except Exception:
                pass  # Ignore errors in destructor

# Global preloader instance
model_preloader = OllamaModelPreloader()
