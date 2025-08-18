#!/usr/bin/env python3
"""
PeteOllama V1 - Local Testing Version
Simplified version for testing locally without serverless dependencies
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get RunPod configuration from environment
RUNPOD_API_KEY = os.getenv('RUNPOD_API_KEY')
RUNPOD_SERVERLESS_ENDPOINT = os.getenv('RUNPOD_SERVERLESS_ENDPOINT')

if not RUNPOD_API_KEY:
    print("⚠️ Warning: RUNPOD_API_KEY not found in environment variables")
if not RUNPOD_SERVERLESS_ENDPOINT:
    print("⚠️ Warning: RUNPOD_SERVERLESS_ENDPOINT not found in environment variables")

def test_endpoint():
    """Test the RunPod serverless endpoint"""
    
    endpoint_url = f"https://{RUNPOD_SERVERLESS_ENDPOINT}.runpod.net"
    print(f"🎯 Testing RunPod endpoint: {endpoint_url}")
    
    # Test health endpoint
    print(f"\n📡 Testing health endpoint...")
    health_url = f"{endpoint_url}/health"
    print(f"URL: {health_url}")
    
    # Test main page
    print(f"\n📡 Testing main page...")
    main_url = f"{endpoint_url}/"
    print(f"URL: {main_url}")
    
    # Test admin dashboard
    print(f"\n📡 Testing admin dashboard...")
    admin_url = f"{endpoint_url}/admin"
    print(f"URL: {admin_url}")
    
    # Test chat API
    print(f"\n📡 Testing chat API...")
    chat_url = f"{endpoint_url}/api/chat"
    print(f"URL: {chat_url}")
    
    print(f"\n🚀 Ready to test! Use these URLs in your browser or curl commands:")
    print(f"Health Check: {health_url}")
    print(f"Main Page: {main_url}")
    print(f"Admin Dashboard: {admin_url}")
    print(f"Chat API: {chat_url}")

def get_endpoint_url():
    """Get the full RunPod serverless endpoint URL"""
    if RUNPOD_SERVERLESS_ENDPOINT:
        return f"https://{RUNPOD_SERVERLESS_ENDPOINT}.runpod.net"
    return None

if __name__ == '__main__':
    print("🏠 PeteOllama V1 - Local Testing")
    print("=" * 50)
    
    if RUNPOD_SERVERLESS_ENDPOINT:
        test_endpoint()
    else:
        print("❌ RUNPOD_SERVERLESS_ENDPOINT not found in .env file")
        print("Please add: RUNPOD_SERVERLESS_ENDPOINT=vk7efas3wu5vd7")
