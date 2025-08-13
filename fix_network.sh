#!/bin/bash
# Network Fix Script for RunPod
# Fixes DNS and network connectivity issues

echo "🔧 Fixing Network Connectivity Issues..."
echo "======================================"

# Function to test connectivity
test_connectivity() {
    echo "🧪 Testing network connectivity..."
    
    # Test DNS resolution
    if nslookup google.com >/dev/null 2>&1; then
        echo "✅ DNS resolution working"
        return 0
    else
        echo "❌ DNS resolution failed"
        return 1
    fi
}

# Function to fix DNS
fix_dns() {
    echo "🔧 Attempting DNS fixes..."
    
    # Backup original resolv.conf
    cp /etc/resolv.conf /etc/resolv.conf.backup 2>/dev/null || true
    
    # Try multiple DNS servers
    local dns_servers=(
        "8.8.8.8 8.8.4.4"
        "1.1.1.1 1.0.0.1"
        "208.67.222.222 208.67.220.220"
        "9.9.9.9 149.112.112.112"
    )
    
    for dns_pair in "${dns_servers[@]}"; do
        echo "🔄 Trying DNS servers: $dns_pair"
        
        # Create new resolv.conf
        cat > /etc/resolv.conf << EOF
# Fixed DNS configuration
nameserver $(echo $dns_pair | cut -d' ' -f1)
nameserver $(echo $dns_pair | cut -d' ' -f2)
search .
options timeout:2 attempts:3
EOF
        
        # Test if it works
        if test_connectivity; then
            echo "✅ DNS fixed with servers: $dns_pair"
            return 0
        fi
        
        echo "❌ DNS servers $dns_pair failed, trying next..."
    done
    
    # Restore original if all failed
    echo "⚠️ All DNS fixes failed, restoring original config"
    cp /etc/resolv.conf.backup /etc/resolv.conf 2>/dev/null || true
    return 1
}

# Function to fix network interfaces
fix_network_interfaces() {
    echo "🔧 Checking network interfaces..."
    
    # Check if we're in Docker
    if [ -f /.dockerenv ]; then
        echo "🐳 Running in Docker container"
        
        # Try to restart networking (if possible)
        if command -v systemctl >/dev/null 2>&1; then
            echo "🔄 Attempting to restart networking..."
            systemctl restart networking 2>/dev/null || echo "⚠️ Could not restart networking"
        fi
        
        # Check Docker DNS
        if [ -f /etc/resolv.conf ] && grep -q "127.0.0.11" /etc/resolv.conf; then
            echo "🐳 Using Docker internal DNS"
            # Docker DNS should work, but let's verify
            if ! test_connectivity; then
                echo "⚠️ Docker DNS not working, trying external DNS"
                fix_dns
            fi
        fi
    else
        echo "🖥️ Running on host system"
        fix_dns
    fi
}

# Function to test GitHub access
test_github() {
    echo "🐙 Testing GitHub access..."
    
    # Try multiple methods
    local github_urls=(
        "https://github.com"
        "https://api.github.com"
        "https://raw.githubusercontent.com"
    )
    
    for url in "${github_urls[@]}"; do
        if curl -s --connect-timeout 10 "$url" >/dev/null 2>&1; then
            echo "✅ GitHub access working via: $url"
            return 0
        fi
    done
    
    echo "❌ GitHub access failed"
    return 1
}

# Main execution
echo "🔍 Starting network diagnostics..."

# Test current connectivity
if test_connectivity; then
    echo "✅ Network is working correctly!"
    
    # Test GitHub specifically
    if test_github; then
        echo "✅ All network tests passed!"
        exit 0
    else
        echo "⚠️ Basic connectivity works but GitHub access failed"
        echo "🔧 This might be a firewall or proxy issue"
    fi
else
    echo "❌ Network connectivity issues detected"
    echo "🔧 Attempting to fix..."
    
    # Try to fix network
    fix_network_interfaces
    
    # Test again
    if test_connectivity; then
        echo "✅ Network fixed!"
        
        if test_github; then
            echo "✅ All network issues resolved!"
            exit 0
        else
            echo "⚠️ Basic connectivity restored but GitHub still blocked"
        fi
    else
        echo "❌ Could not fix network issues"
        echo "💡 Try restarting the pod or contact RunPod support"
        exit 1
    fi
fi

# Final recommendations
echo ""
echo "📋 Network Status Summary:"
echo "=========================="
echo "• Basic connectivity: $(test_connectivity && echo "✅ Working" || echo "❌ Failed")"
echo "• GitHub access: $(test_github && echo "✅ Working" || echo "❌ Failed")"
echo ""
echo "💡 If issues persist:"
echo "   1. Restart the RunPod pod"
echo "   2. Check RunPod network settings"
echo "   3. Contact RunPod support"
echo "   4. Use existing local scripts as fallback"
