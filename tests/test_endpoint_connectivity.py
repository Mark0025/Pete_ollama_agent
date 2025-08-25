#!/usr/bin/env python3
"""
Simple RunPod Endpoint Connectivity Test
Tests basic network connectivity to the endpoint
"""

import socket
import requests
import subprocess
import sys
import os
from urllib.parse import urlparse

def test_dns_resolution(hostname):
    """Test DNS resolution"""
    try:
        ip = socket.gethostbyname(hostname)
        print(f"✅ DNS Resolution: {hostname} → {ip}")
        return ip
    except socket.gaierror as e:
        print(f"❌ DNS Resolution failed: {e}")
        return None

def test_port_connectivity(hostname, port):
    """Test if a specific port is open"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((hostname, port))
        sock.close()
        
        if result == 0:
            print(f"✅ Port {port} is OPEN")
            return True
        else:
            print(f"❌ Port {port} is CLOSED (error code: {result})")
            return False
    except Exception as e:
        print(f"❌ Port {port} test failed: {e}")
        return False

def test_http_connectivity(url, timeout=10):
    """Test HTTP connectivity"""
    try:
        response = requests.get(url, timeout=timeout)
        print(f"✅ HTTP {response.status_code}: {url}")
        return True
    except requests.exceptions.Timeout:
        print(f"⏰ HTTP Timeout: {url}")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"🔌 HTTP Connection Error: {url} - {e}")
        return False
    except Exception as e:
        print(f"❌ HTTP Error: {url} - {e}")
        return False

def test_curl_connectivity(url, timeout=10):
    """Test using curl command"""
    try:
        result = subprocess.run(
            ['curl', '-m', str(timeout), '-s', '-o', '/dev/null', '-w', '%{http_code}', url],
            capture_output=True,
            text=True,
            timeout=timeout + 5
        )
        
        if result.returncode == 0:
            status_code = result.stdout.strip()
            if status_code.isdigit():
                print(f"✅ cURL {status_code}: {url}")
                return True
            else:
                print(f"❌ cURL failed: {result.stdout}")
                return False
        else:
            print(f"❌ cURL error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ cURL timeout: {url}")
        return False
    except FileNotFoundError:
        print("⚠️ cURL not available, skipping curl test")
        return False
    except Exception as e:
        print(f"❌ cURL test failed: {e}")
        return False

def main():
    """Main connectivity test"""
    print("🔍 RunPod Endpoint Connectivity Test")
    print("=" * 50)
    
    # Get endpoint from environment
    endpoint_id = os.getenv('RUNPOD_SERVERLESS_ENDPOINT')
    if not endpoint_id:
        print("❌ RUNPOD_SERVERLESS_ENDPOINT not set")
        sys.exit(1)
    
    hostname = f"{endpoint_id}.runpod.net"
    base_url = f"https://{hostname}"
    
    print(f"🌐 Testing endpoint: {hostname}")
    print(f"🔗 Base URL: {base_url}")
    print()
    
    # Test DNS
    ip = test_dns_resolution(hostname)
    print()
    
    if not ip:
        print("❌ Cannot proceed without DNS resolution")
        sys.exit(1)
    
    # Test common ports
    print("🔌 Testing port connectivity:")
    test_port_connectivity(hostname, 80)   # HTTP
    test_port_connectivity(hostname, 443)  # HTTPS
    test_port_connectivity(hostname, 8080) # Alternative HTTP
    print()
    
    # Test HTTP endpoints
    print("🌐 Testing HTTP connectivity:")
    test_http_connectivity(f"{base_url}/health", timeout=15)
    test_http_connectivity(f"{base_url}/", timeout=15)
    print()
    
    # Test with curl
    print("📡 Testing with cURL:")
    test_curl_connectivity(f"{base_url}/health", timeout=15)
    test_curl_connectivity(f"{base_url}/", timeout=15)
    print()
    
    # Summary
    print("📊 Summary:")
    print("   - If port 443 is closed, your endpoint is likely down or misconfigured")
    print("   - Check your RunPod dashboard for endpoint status")
    print("   - Try restarting the endpoint if it's in a failed state")
    print("   - Verify network configuration and security groups")

if __name__ == "__main__":
    main()
