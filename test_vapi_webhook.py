#!/usr/bin/env python3
"""
Test VAPI Webhook Exactly As VAPI Sends It
==========================================

Test the webhook endpoint with the exact payload structure VAPI sends
"""

import sys
import os
import json
import requests
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_vapi_webhook_payload():
    """Test with exact VAPI payload structure"""
    print("🎯 Testing VAPI Webhook with Exact Payload...")
    
    # This is exactly what VAPI sends
    vapi_payload = {
        "id": "36d491e9-3bc5-447e-be84-170f1fc8122d",
        "createdAt": "2025-07-29T20:00:39.426Z",
        "updatedAt": "2025-08-22T21:12:23.263Z",
        "type": "apiRequest",
        "function": {
            "name": "api_request_tool",
            "description": "Look up available rental properties from a specified website using OpenRouter AI."
        },
        "messages": [
            {
                "type": "request-start",
                "content": "Yeah give me just a second here, Please bare with me while i check on that.",
                "blocking": False
            }
        ],
        "orgId": "3a6d6585-c027-4bb4-af35-2203df3fe91f",
        "name": "Rental_lookUP_FAPI",
        "url": "https://3987f7e86124.ngrok-free.app/tools/webhook",
        "method": "POST",
        "headers": {
            "type": "object",
            "properties": {
                "Content-Type": {
                    "type": "string",
                    "value": "application/json"
                }
            }
        },
        "body": {
            "type": "object",
            "required": ["website"],
            "properties": {
                "website": {
                    "description": "",
                    "type": "string",
                    "value": "http://nolenrentals.com/"
                }
            }
        }
    }
    
    print("📋 VAPI Payload Structure:")
    print(f"  Tool Name: {vapi_payload['name']}")
    print(f"  Function: {vapi_payload['function']['name']}")
    print(f"  Website: {vapi_payload['body']['properties']['website']['value']}")
    print(f"  Message: {vapi_payload['messages'][0]['content']}")
    
    return vapi_payload

def simulate_webhook_handler(vapi_payload):
    """Simulate how your webhook handler should process this"""
    print("\n🔧 Processing VAPI Webhook...")
    
    try:
        # Extract the website from VAPI payload
        website_url = vapi_payload['body']['properties']['website']['value']
        tool_name = vapi_payload['function']['name']
        
        print(f"🌐 Target Website: {website_url}")
        print(f"🛠️ Tool: {tool_name}")
        
        # This is where you'd call your DuckDuckGo search
        # Try multiple search strategies for better results
        search_queries = [
            f"site:{website_url} rental properties available",
            f"site:{website_url} apartments rent",
            f"{website_url} rental listings",
            f"properties for rent {website_url.split('//')[1]}"
        ]
        
        print(f"🔍 Trying {len(search_queries)} search strategies...")
        
        # Test the DuckDuckGo search with multiple queries
        return test_website_search_multiple(search_queries, website_url)
        
    except Exception as e:
        print(f"❌ Webhook processing failed: {e}")
        return False

def test_website_search_multiple(search_queries, website_url):
    """Test multiple search strategies to find results"""
    print(f"\n🔎 Searching website: {website_url}")
    
    all_results = []
    
    try:
        from duckduckgo_search import DDGS
        
        for i, query in enumerate(search_queries, 1):
            print(f"\n🔍 Strategy {i}: {query}")
            
            with DDGS() as ddgs:
                try:
                    results = list(ddgs.text(query, max_results=3))
                    print(f"   → Found {len(results)} results")
                    
                    if results:
                        # Add unique results only
                        for result in results:
                            if result not in all_results:
                                all_results.append(result)
                                
                except Exception as e:
                    print(f"   → Search failed: {e}")
                    continue
        
        print(f"\n✅ Total unique results: {len(all_results)}")
        
        if all_results:
            print("\n📋 Combined Search Results:")
            print("=" * 50)
            
            for i, result in enumerate(all_results[:5], 1):  # Show top 5
                title = result.get('title', 'No title')
                url = result.get('href', 'No URL')
                snippet = result.get('body', 'No snippet')
                
                print(f"{i}. {title}")
                print(f"   🔗 {url}")
                print(f"   📝 {snippet[:150]}...")
                print()
                
            # Format response for VAPI
            response_text = format_vapi_response(all_results, website_url)
            print("🎤 VAPI Response:")
            print("=" * 50)
            print(response_text)
            
            return True
        else:
            # If no specific results, try a general search
            print("\n🔄 No results found, trying general search...")
            return test_general_search(website_url)
            
    except Exception as e:
        print(f"❌ Website search failed: {e}")
        return False

def test_general_search(website_url):
    """Test general rental property search as fallback"""
    try:
        from duckduckgo_search import DDGS
        
        # Extract domain for general search
        domain = website_url.replace('https://', '').replace('http://', '').split('/')[0]
        general_query = f"rental properties apartments {domain}"
        
        print(f"🔍 General search: {general_query}")
        
        with DDGS() as ddgs:
            results = list(ddgs.text(general_query, max_results=5))
            
        if results:
            print(f"✅ Found {len(results)} general results")
            
            print("\n📋 General Search Results:")
            print("=" * 50)
            
            for i, result in enumerate(results[:3], 1):
                title = result.get('title', 'No title')
                url = result.get('href', 'No URL')
                snippet = result.get('body', 'No snippet')
                
                print(f"{i}. {title}")
                print(f"   🔗 {url}")
                print(f"   📝 {snippet[:100]}...")
                print()
            
            # Format response for VAPI
            response_text = f"I found {len(results)} rental property listings related to {domain}. "
            response_text += "Here are some options that might help you find what you're looking for. "
            response_text += "Would you like me to search for more specific criteria?"
            
            print("🎤 VAPI Response:")
            print("=" * 50)
            print(response_text)
            
            return True
        else:
            print("⚠️ No general results found either")
            return False
            
    except Exception as e:
        print(f"❌ General search failed: {e}")
        return False

def test_website_search(search_query, website_url):
    """Test searching a specific website using DuckDuckGo"""
    print(f"\n🔎 Searching website: {website_url}")
    
    try:
        # Method 1: Direct DuckDuckGo search
        from duckduckgo_search import DDGS
        
        with DDGS() as ddgs:
            # Search for rental properties on the specific site
            results = list(ddgs.text(search_query, max_results=5))
            
        print(f"✅ Found {len(results)} results from {website_url}")
        
        if results:
            print("\n📋 Search Results:")
            print("=" * 50)
            
            for i, result in enumerate(results, 1):
                title = result.get('title', 'No title')
                url = result.get('href', 'No URL')
                snippet = result.get('body', 'No snippet')
                
                print(f"{i}. {title}")
                print(f"   🔗 {url}")
                print(f"   📝 {snippet[:150]}...")
                print()
                
            # Format response for VAPI
            response_text = format_vapi_response(results, website_url)
            print("🎤 VAPI Response:")
            print("=" * 50)
            print(response_text)
            
            return True
        else:
            print("⚠️ No results found")
            return False
            
    except Exception as e:
        print(f"❌ Website search failed: {e}")
        return False

def format_vapi_response(results, website_url):
    """Format search results for VAPI voice response"""
    if not results:
        return f"I couldn't find any rental properties on {website_url}. The website might be down or not have publicly searchable content."
    
    # Create a concise response for voice
    response = f"I found {len(results)} rental listings on {website_url}. "
    
    # Add top 3 results
    for i, result in enumerate(results[:3], 1):
        title = result.get('title', 'Property listing')
        snippet = result.get('body', '')
        
        # Extract key info from snippet (rent, bedrooms, etc.)
        key_info = extract_property_info(snippet)
        
        response += f"{i}. {title}. "
        if key_info:
            response += f"{key_info}. "
    
    response += f"Would you like me to get more details about any of these properties?"
    
    return response

def extract_property_info(text):
    """Extract key property info from text snippet"""
    import re
    
    # Look for rent amounts
    rent_match = re.search(r'\$[\d,]+', text)
    
    # Look for bedrooms/bathrooms
    bed_match = re.search(r'(\d+)\s*(?:bed|br|bedroom)', text.lower())
    bath_match = re.search(r'(\d+)\s*(?:bath|ba|bathroom)', text.lower())
    
    info_parts = []
    
    if rent_match:
        info_parts.append(f"Rent: {rent_match.group()}")
    
    if bed_match:
        beds = bed_match.group(1)
        baths = bath_match.group(1) if bath_match else "?"
        info_parts.append(f"{beds} bed, {baths} bath")
    
    return " - ".join(info_parts) if info_parts else None

def test_local_webhook_server():
    """Test if there's a local webhook server running"""
    print("\n🌐 Testing Local Webhook Server...")
    
    try:
        # Check if there's a server running on common ports
        test_urls = [
            "http://localhost:8000/tools/webhook",
            "http://localhost:3000/tools/webhook", 
            "http://localhost:5000/tools/webhook",
            "http://127.0.0.1:8000/health",
            "http://127.0.0.1:8000/"
        ]
        
        for url in test_urls:
            try:
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    print(f"✅ Found server at: {url}")
                    return url
            except:
                continue
                
        print("⚠️ No local webhook server found")
        print("💡 You can start your server with: uv run python api_server.py")
        return None
        
    except Exception as e:
        print(f"❌ Server check failed: {e}")
        return None

def main():
    """Run the complete VAPI webhook test"""
    print("🚀 VAPI Webhook Test - Exact Payload Simulation")
    print("=" * 60)
    
    # Step 1: Get the VAPI payload
    vapi_payload = test_vapi_webhook_payload()
    
    # Step 2: Process it like your webhook would
    search_success = simulate_webhook_handler(vapi_payload)
    
    # Step 3: Check for local server
    local_server = test_local_webhook_server()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)
    print(f"VAPI Payload Parsing: {'✅ PASS' if vapi_payload else '❌ FAIL'}")
    print(f"Website Search: {'✅ PASS' if search_success else '❌ FAIL'}")
    print(f"Local Server: {'✅ RUNNING' if local_server else '⚠️ NOT FOUND'}")
    
    if search_success:
        print("\n🎉 Your DuckDuckGo website search is working!")
        print("🔗 Next steps:")
        print("  1. Start your webhook server: uv run python api_server.py")
        print("  2. Set up ngrok: ngrok http 8000")
        print("  3. Update VAPI tool URL to your ngrok endpoint")
        print("  4. Test with actual VAPI voice call")
    else:
        print("\n⚠️ Search functionality needs debugging")
        print("💡 Check your internet connection and duckduckgo-search installation")

if __name__ == "__main__":
    main()
