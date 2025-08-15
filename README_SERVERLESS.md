# PeteOllama V1 - RunPod Serverless Deployment

## 🚀 **Overview**

This is the serverless version of PeteOllama, optimized for RunPod Serverless deployment. It eliminates all the pod-level network and connectivity issues by using RunPod's managed infrastructure.

## 🏗️ **Architecture**

### **Components:**
- **`rp_handler.py`** - Main RunPod Serverless handler
- **`Dockerfile.serverless`** - Optimized Docker image
- **`requirements.serverless.txt`** - Minimal dependencies
- **`build_serverless.sh`** - Build and deploy script

### **Request Types:**
1. **`webhook`** - VAPI webhook requests
2. **`chat`** - Direct chat completion
3. **`admin`** - Admin UI operations

## 🐳 **Building the Image**

### **1. Build Locally:**
```bash
chmod +x build_serverless.sh
./build_serverless.sh
```

### **2. Manual Build:**
```bash
docker build -f Dockerfile.serverless -t peteollama-serverless:v1.0.0 .
```

## 🚀 **Deploying to RunPod Serverless**

### **1. Push to Registry:**
```bash
# Tag for your registry
docker tag peteollama-serverless:v1.0.0 your-registry/peteollama-serverless:v1.0.0

# Push to registry
docker push your-registry/peteollama-serverless:v1.0.0
```

### **2. Create RunPod Endpoint:**
1. Go to [RunPod Serverless Console](https://runpod.io/console/serverless)
2. Click **New Endpoint**
3. Choose **Import from Docker Registry**
4. Enter your image: `your-registry/peteollama-serverless:v1.0.0`
5. Configure endpoint settings
6. Deploy!

## 🧪 **Testing the Endpoint**

### **Test Chat Request:**
```bash
curl -X POST "https://your-endpoint.runpod.net/run" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "type": "chat",
      "model": "peteollama:property-manager-v0.0.1",
      "messages": [{"role": "user", "content": "Hi Jamie!"}],
      "temperature": 0.7
    }
  }'
```

### **Test Admin Status:**
```bash
curl -X POST "https://your-endpoint.runpod.net/run" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "type": "admin",
      "action": "status"
    }
  }'
```

## 🔧 **Configuration**

### **Environment Variables:**
- **`OLLAMA_HOST`** - Ollama service URL
- **`DB_HOST`** - Database host
- **`DB_USER`** - Database username
- **`DB_PASSWORD`** - Database password
- **`DB_NAME`** - Database name

### **Model Requirements:**
Ensure your Ollama service has these models:
- `peteollama:property-manager-v0.0.1`
- `llama3:8b` (base model)

## 📊 **Benefits of Serverless**

✅ **No network issues** - RunPod handles infrastructure  
✅ **Auto-scaling** - Handles VAPI load automatically  
✅ **Cost-effective** - Pay per request, not idle time  
✅ **Reliable** - Managed environment with health checks  
✅ **Easy updates** - Deploy new image versions  

## 🚨 **Important Notes**

- **Cold starts** - First request may take longer
- **Memory limits** - Configure appropriate memory allocation
- **Timeout settings** - Set reasonable request timeouts
- **External services** - Ensure Ollama and database are accessible

## 🔍 **Troubleshooting**

### **Common Issues:**
1. **Image build fails** - Check Dockerfile syntax
2. **Dependencies missing** - Verify requirements.serverless.txt
3. **Runtime errors** - Check logs in RunPod console
4. **Connection issues** - Verify external service URLs

### **Debug Mode:**
Enable debug logging by setting environment variable:
```bash
LOG_LEVEL=DEBUG
```

## 📞 **Support**

For issues with:
- **RunPod Serverless** - Contact RunPod support
- **PeteOllama code** - Check logs and error messages
- **Deployment** - Verify image and configuration

---

**🎯 Ready to deploy? Run the build script and create your RunPod Serverless endpoint!**
