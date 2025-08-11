#!/usr/bin/env python3
"""
PeteOllama Smart Model Versioner
================================

Intelligent model versioning system that only creates new models when there are
meaningful improvements, with proper semantic versioning and diff analysis.
"""

import sys
import os
import json
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import sqlite3

# Add src to Python path
src_path = str(Path(__file__).parent / "src")
sys.path.insert(0, src_path)

from database.pete_db_manager import PeteDBManager

class SmartModelVersioner:
    """Intelligent model versioning with improvement tracking"""
    
    def __init__(self, db_path: str = None):
        """Initialize the versioner"""
        self.db_manager = PeteDBManager(db_path) if db_path else PeteDBManager()
        self.version_file = Path("model_versions.json")
        self.models_dir = Path("models")
        self.models_dir.mkdir(exist_ok=True)
        
        # Load existing version history
        self.version_history = self._load_version_history()
        
    def _load_version_history(self) -> Dict:
        """Load existing model version history"""
        if self.version_file.exists():
            try:
                with open(self.version_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  Error loading version history: {e}")
        
        return {
            "current_version": "0.0.0",
            "models": {},
            "improvements": [],
            "last_training_data_hash": None
        }
    
    def _save_version_history(self):
        """Save version history to file"""
        try:
            with open(self.version_file, 'w') as f:
                json.dump(self.version_history, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving version history: {e}")
    
    def _calculate_training_data_hash(self) -> str:
        """Calculate hash of current training data to detect changes"""
        try:
            # Get conversation count and recent data
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Get basic stats
            cursor.execute("SELECT COUNT(*) FROM communication_logs")
            total_conversations = cursor.fetchone()[0]
            
            # Get recent conversations for hash
            cursor.execute("""
                SELECT Transcription, CreationDate 
                FROM communication_logs 
                WHERE Transcription IS NOT NULL 
                ORDER BY CreationDate DESC 
                LIMIT 50
            """)
            recent_data = cursor.fetchall()
            
            # Create hash from data
            data_string = f"{total_conversations}_{len(recent_data)}"
            for transcription, date in recent_data:
                data_string += f"{transcription[:100]}_{date}"
            
            return hashlib.md5(data_string.encode()).hexdigest()
            
        except Exception as e:
            print(f"⚠️  Error calculating data hash: {e}")
            return "unknown"
    
    def _check_for_improvements(self) -> Tuple[bool, str]:
        """Check if we should create a new model version"""
        current_hash = self._calculate_training_data_hash()
        last_hash = self.version_history.get("last_training_data_hash")
        
        # Check if training data has changed
        if current_hash != last_hash:
            return True, f"Training data changed (hash: {current_hash[:8]} vs {last_hash[:8] if last_hash else 'none'})"
        
        # Check if we have performance improvements to incorporate
        if self._has_performance_improvements():
            return True, "Performance improvements detected"
        
        # Check if it's been too long since last model (30 days)
        last_model_date = self._get_last_model_date()
        if last_model_date:
            days_since = (datetime.now() - last_model_date).days
            if days_since > 30:
                return True, f"Regular update (last model: {days_since} days ago)"
        
        return False, "No significant changes detected"
    
    def _has_performance_improvements(self) -> bool:
        """Check if there are performance improvements to incorporate"""
        try:
            # Check benchmark logs for recent improvements
            benchmark_files = list(Path("logs").glob("benchmark_*.jsonl"))
            if not benchmark_files:
                return False
            
            # Get most recent benchmark data
            latest_file = max(benchmark_files, key=lambda x: x.stat().st_mtime)
            
            # Analyze recent performance
            recent_scores = []
            with open(latest_file, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        if 'quality_metrics' in data:
                            score = data['quality_metrics'].get('estimated_quality_score', 0)
                            recent_scores.append(score)
                    except:
                        continue
            
            if recent_scores:
                avg_score = sum(recent_scores) / len(recent_scores)
                # If average quality is improving, consider creating new model
                return avg_score > 7.0  # Threshold for "good" performance
            
        except Exception as e:
            print(f"⚠️  Error checking performance improvements: {e}")
        
        return False
    
    def _get_last_model_date(self) -> Optional[datetime]:
        """Get the date of the last model creation"""
        if not self.version_history.get("models"):
            return None
        
        try:
            last_model = max(self.version_history["models"].values(), 
                           key=lambda x: x.get("created_at", ""))
            return datetime.fromisoformat(last_model["created_at"])
        except:
            return None
    
    def _increment_version(self, improvement_type: str) -> str:
        """Increment version number based on improvement type"""
        current = self.version_history.get("current_version", "0.0.0")
        major, minor, patch = map(int, current.split("."))
        
        if "major" in improvement_type.lower():
            major += 1
            minor = 0
            patch = 0
        elif "performance" in improvement_type.lower():
            minor += 1
            patch = 0
        else:
            patch += 1
        
        return f"{major}.{minor}.{patch}"
    
    def _create_model_diff(self, old_model: str, new_model: str) -> str:
        """Create a diff analysis of what changed between models"""
        try:
            # Get old and new Modelfiles
            old_modelfile = self.models_dir / f"{old_model.replace(':', '_')}_modelfile"
            new_modelfile = self.models_dir / f"{new_model.replace(':', '_')}_modelfile"
            
            if not old_modelfile.exists() or not new_modelfile.exists():
                return "No previous model to compare"
            
            # Simple diff analysis
            with open(old_modelfile, 'r') as f:
                old_content = f.read()
            with open(new_modelfile, 'r') as f:
                new_content = f.read()
            
            # Count MESSAGE pairs
            old_messages = old_content.count("MESSAGE")
            new_messages = new_content.count("MESSAGE")
            
            # Count conversation examples
            old_examples = old_content.count("Example:")
            new_examples = new_content.count("Example:")
            
            diff_summary = f"""
Model Improvement Analysis:
- Training data hash: {self._calculate_training_data_hash()[:8]}
- MESSAGE pairs: {old_messages} → {new_messages} ({new_messages - old_messages:+d})
- Conversation examples: {old_examples} → {new_examples} ({new_examples - old_examples:+d})
- Base model: llama3:latest
- Training data: Real property management conversations
"""
            
            return diff_summary
            
        except Exception as e:
            return f"Error creating diff: {e}"
    
    def should_create_new_model(self) -> Tuple[bool, str, str]:
        """Determine if we should create a new model version"""
        should_create, reason = self._check_for_improvements()
        
        if should_create:
            # Determine improvement type for versioning
            if "performance" in reason.lower():
                improvement_type = "performance"
            elif "regular" in reason.lower():
                improvement_type = "patch"
            else:
                improvement_type = "minor"
            
            new_version = self._increment_version(improvement_type)
            return True, reason, new_version
        
        return False, reason, self.version_history.get("current_version", "0.0.0")
    
    def create_new_model_version(self, reason: str, version: str) -> bool:
        """Create a new model version with proper tracking"""
        try:
            print(f"🎯 Creating new model version {version}")
            print(f"📝 Reason: {reason}")
            
            # Generate model name - use jamie naming convention to match UI expectations
            model_name = f"peteollama:jamie-v{version}"
            
            # Create the model using enhanced trainer
            from enhanced_model_trainer import PropertyManagementModelfileGenerator
            
            generator = PropertyManagementModelfileGenerator()
            
            # Extract conversations and create model
            conversations = generator.extract_conversations()
            if not conversations:
                print("❌ No conversations found for training")
                return False
            
            # Create the model
            success = generator.save_and_create_model(model_name)
            
            if success:
                # Update version history
                self.version_history["current_version"] = version
                self.version_history["models"][version] = {
                    "name": model_name,
                    "created_at": datetime.now().isoformat(),
                    "reason": reason,
                    "conversations_used": len(conversations),
                    "training_data_hash": self._calculate_training_data_hash()
                }
                
                # Add improvement record
                self.version_history["improvements"].append({
                    "version": version,
                    "date": datetime.now().isoformat(),
                    "reason": reason,
                    "model_name": model_name
                })
                
                # Update last training data hash
                self.version_history["last_training_data_hash"] = self._calculate_training_data_hash()
                
                # Save version history
                self._save_version_history()
                
                # Create diff analysis
                if self.version_history["models"]:
                    previous_version = max(
                        [v for v in self.version_history["models"].keys() if v != version],
                        default=None
                    )
                    if previous_version:
                        diff_analysis = self._create_model_diff(
                            self.version_history["models"][previous_version]["name"],
                            model_name
                        )
                        print(f"📊 Diff Analysis:\n{diff_analysis}")
                
                print(f"✅ Successfully created model version {version}: {model_name}")
                return True
            else:
                print("❌ Failed to create new model version")
                return False
                
        except Exception as e:
            print(f"❌ Error creating new model version: {e}")
            return False
    
    def get_current_model_info(self) -> Dict:
        """Get information about the current model"""
        current_version = self.version_history.get("current_version", "0.0.0")
        current_model = self.version_history.get("models", {}).get(current_version, {})
        
        return {
            "version": current_version,
            "model_name": current_model.get("name", "No model created yet"),
            "created_at": current_model.get("created_at", "Unknown"),
            "reason": current_model.get("reason", "Initial creation"),
            "conversations_used": current_model.get("conversations_used", 0),
            "total_models": len(self.version_history.get("models", {})),
            "improvements": len(self.version_history.get("improvements", []))
        }
    
    def list_all_models(self) -> List[Dict]:
        """List all created models with their information"""
        models = []
        for version, info in self.version_history.get("models", {}).items():
            models.append({
                "version": version,
                "model_name": info["name"],
                "created_at": info["created_at"],
                "reason": info["reason"],
                "conversations_used": info["conversations_used"]
            })
        
        return sorted(models, key=lambda x: x["version"], reverse=True)

def main():
    """Main execution function"""
    print("🎯 PeteOllama Smart Model Versioner")
    print("=" * 50)
    
    try:
        versioner = SmartModelVersioner()
        
        # Check if we should create a new model
        should_create, reason, version = versioner.should_create_new_model()
        
        print(f"📊 Current version: {versioner.get_current_model_info()['version']}")
        print(f"🔍 Should create new model: {should_create}")
        print(f"📝 Reason: {reason}")
        
        if should_create:
            print("\n🚀 Creating new model version...")
            success = versioner.create_new_model_version(reason, version)
            
            if success:
                print("\n✅ New model version created successfully!")
                print(f"📊 Model info: {versioner.get_current_model_info()}")
            else:
                print("\n❌ Failed to create new model version")
                return False
        else:
            print("\n✅ No new model needed - current version is up to date")
            print(f"📊 Current model: {versioner.get_current_model_info()}")
        
        # Show model history
        print("\n📋 Model History:")
        for model in versioner.list_all_models():
            print(f"  v{model['version']}: {model['model_name']} ({model['created_at']})")
            print(f"    Reason: {model['reason']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1) 