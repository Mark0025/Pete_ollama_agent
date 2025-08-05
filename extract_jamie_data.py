#!/usr/bin/env python3
"""
Virtual Jamie.V1 Data Extraction for Ollama Agent
================================================

Quick script to extract property management communication data from prod-db
and create a local pete.db for training Virtual Jamie.V1 with Ollama.

Usage:
    cd /Users/markcarpenter/Desktop/pete/ollama_agent
    python extract_jamie_data.py

Output:
    Creates pete.db in the ollama_agent directory with communication logs
"""

import os
import sys
from virtual_jamie_extractor import VirtualJamieDataExtractor

def main():
    print("🤖 Virtual Jamie.V1 - Ollama Property Management Agent")
    print("=" * 60)
    print("📊 Extracting communication logs from prod-db...")
    print("🎯 Target: CompanyId=1, UserId=6, Phone calls >15 seconds")
    print("📁 Output: pete.db in ollama_agent directory")
    print("🏠 Purpose: Train Virtual Jamie for property management")
    print()
    
    try:
        # Create extractor and run extraction
        extractor = VirtualJamieDataExtractor()
        success = extractor.run_full_extraction()
        
        if success:
            print()
            print("🎉 SUCCESS! Virtual Jamie.V1 training database created!")
            print(f"📁 Database location: {extractor.target_db_path}")
            print("📊 Contains communication logs for property management training")
            print("🤖 Ready to train Virtual Jamie.V1 with Ollama!")
            print()
            print("📋 Next steps:")
            print("   1. Use pete.db for Ollama model training")
            print("   2. Train Virtual Jamie.V1 on property management conversations")
            print("   3. Deploy as your AI property management assistant")
            
        else:
            print()
            print("❌ EXTRACTION FAILED!")
            print("📋 Check the logs for error details:")
            print("   📄 ollama_agent/logs/virtual_jamie_extraction.log")
            print("💡 Common issues:")
            print("   - Database connection problems")
            print("   - Missing .env credentials")
            print("   - No data matching criteria")
            
    except (ImportError, ConnectionError, FileNotFoundError) as e:
        print(f"❌ ERROR: {e}")
        print()
        print("🔧 Troubleshooting:")
        print("   - Make sure you're in the ollama_agent directory")
        print("   - Check that prod-db credentials are in ollama_agent/.env")
        print("   - Verify PROD_DB_* environment variables are set correctly")
        print("   - Ensure required Python packages are installed")

if __name__ == "__main__":
    main()