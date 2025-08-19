#!/usr/bin/env python3
"""
Debug Webhook Server
Debug route registration issues
"""

import os
import sys
from pathlib import Path
import traceback

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def debug_route_registration():
    """Debug the route registration process"""
    
    print("🔍 Debugging route registration...")
    
    try:
        # Import the webhook server
        print("📦 Importing VAPIWebhookServer...")
        from vapi.webhook_server import VAPIWebhookServer
        
        print("✅ Import successful")
        
        # Create instance
        print("🏗️ Creating VAPIWebhookServer instance...")
        server = VAPIWebhookServer(port=8002)
        
        print("✅ Instance created")
        
        # Check if routes were registered
        print("🔍 Checking registered routes...")
        routes = []
        for route in server.app.routes:
            if hasattr(route, 'path'):
                if hasattr(route, 'methods'):
                    routes.append(f"{list(route.methods)} {route.path}")
                else:
                    # Handle Mount objects and other route types
                    routes.append(f"MOUNT {route.path}")
        
        print(f"📋 Found {len(routes)} routes:")
        for route in routes:
            print(f"   {route}")
        
        # Check if UI route exists
        ui_routes = [r for r in routes if "/ui" in r]
        if ui_routes:
            print(f"✅ UI route found: {ui_routes}")
        else:
            print("❌ UI route NOT found!")
        
        # Check if admin route exists
        admin_routes = [r for r in routes if "/admin" in r]
        if admin_routes:
            print(f"✅ Admin routes found: {admin_routes}")
        else:
            print("❌ Admin routes NOT found!")
        
        return server
        
    except Exception as e:
        print(f"❌ Error during import/creation: {e}")
        print("📋 Full traceback:")
        traceback.print_exc()
        return None

def main():
    """Main function"""
    print("🧪 Debug Webhook Server")
    print("=" * 50)
    
    server = debug_route_registration()
    
    if server:
        print("\n🎉 Debug successful! Server ready for testing.")
        print("🔗 Test URL: http://localhost:8002/ui")
        
        # Start server
        import uvicorn
        print("\n🚀 Starting debug server on port 8002...")
        uvicorn.run(server.app, host="0.0.0.0", port=8002, log_level="debug")
    else:
        print("\n❌ Debug failed. Check the errors above.")

if __name__ == "__main__":
    main()
