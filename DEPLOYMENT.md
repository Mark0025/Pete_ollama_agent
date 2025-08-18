# PeteOllama V1 - Deployment Guide

This guide covers deploying PeteOllama using lightweight requirements with RunPod serverless backend.

## 🎯 Deployment Summary

**✅ Ready for deployment!** Your app has been configured for lightweight deployment with:
- **80% smaller** build size (~400MB vs 2GB+)
- **No breaking changes** - all functionality preserved
- **Graceful fallbacks** for ML features
- **RunPod serverless** AI backend

## 📋 Prerequisites

### Required Environment Variables
```bash
# RunPod Configuration (Required)
RUNPOD_SERVERLESS_ENDPOINT=your-runpod-endpoint-id
RUNPOD_API_KEY=your-runpod-api-key

# Database (Required for production)
DATABASE_URL=postgresql://user:pass@host:port/db

# Optional
PORT=8000
REDIS_URL=redis://localhost:6379/0
```

---

## 🐳 Docker Deployment

### Quick Start
```bash
# 1. Copy environment template
cp .env.example .env
# Edit .env with your RunPod credentials

# 2. Build lightweight image
docker build -f Dockerfile.lightweight -t peteollama:latest .

# 3. Run container
docker run -p 8000:8000 --env-file .env peteollama:latest
```

### Using Docker Compose
```bash
# 1. Setup environment
cp .env.example .env
# Edit .env with your credentials

# 2. Start full stack (app + database + redis)
docker-compose -f docker-compose.lightweight.yml up -d

# 3. Check health
curl http://localhost:8000/health
```

### Production Docker Deployment
```bash
# Build production image
docker build -f Dockerfile.lightweight -t peteollama:prod .

# Run with external database
docker run -d \
  --name peteollama-prod \
  -p 8000:8000 \
  -e RUNPOD_SERVERLESS_ENDPOINT=your-endpoint \
  -e RUNPOD_API_KEY=your-api-key \
  -e DATABASE_URL=postgresql://user:pass@your-db:5432/db \
  -e REDIS_URL=redis://your-redis:6379/0 \
  --restart unless-stopped \
  peteollama:prod
```

---

## ⚡ Vercel Deployment

### Quick Deploy
```bash
# 1. Install Vercel CLI
npm i -g vercel

# 2. Deploy
vercel --prod
```

### Environment Setup for Vercel
```bash
# Set environment variables in Vercel dashboard or CLI:
vercel env add RUNPOD_SERVERLESS_ENDPOINT
vercel env add RUNPOD_API_KEY
vercel env add DATABASE_URL  # Use Vercel Postgres or external
```

### Manual Vercel Setup
1. **Connect Repository**: Link your GitHub repo to Vercel
2. **Configure Build**:
   - Framework Preset: Other
   - Build Command: `pip install -r requirements.txt`
   - Output Directory: (leave empty)
3. **Environment Variables**: Add your RunPod credentials
4. **Deploy**: Push to main branch or click Deploy

---

## 🌐 Platform-Specific Instructions

### Vercel with Vercel Postgres
```bash
# 1. Enable Vercel Postgres in dashboard
# 2. Copy connection string to DATABASE_URL
# 3. Deploy
vercel --prod
```

### Railway
```bash
# 1. Connect GitHub repo
# 2. Add environment variables
# 3. Use Dockerfile.lightweight for deployment
```

### Fly.io
```bash
# 1. Install flyctl
# 2. Create fly.toml
fly launch --dockerfile Dockerfile.lightweight
fly secrets set RUNPOD_SERVERLESS_ENDPOINT=your-endpoint
fly secrets set RUNPOD_API_KEY=your-key
fly deploy
```

### Google Cloud Run
```bash
# 1. Build and push image
docker build -f Dockerfile.lightweight -t gcr.io/YOUR-PROJECT/peteollama .
docker push gcr.io/YOUR-PROJECT/peteollama

# 2. Deploy
gcloud run deploy peteollama \
  --image gcr.io/YOUR-PROJECT/peteollama \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars RUNPOD_SERVERLESS_ENDPOINT=your-endpoint \
  --set-env-vars RUNPOD_API_KEY=your-key
```

---

## 🔧 Configuration Options

### Lightweight vs Full Requirements
```bash
# Lightweight (default) - 400MB, no ML dependencies
requirements.txt  # (copied from requirements.lightweight.txt)

# Full version - 2GB+ with all ML features  
requirements.original.txt  # If you need sentence-transformers
```

### Database Options

#### SQLite (Development)
```bash
# No setup required - uses local file
SQLITE_DB_PATH=./data/pete.db
```

#### PostgreSQL (Production)
```bash
DATABASE_URL=postgresql://user:pass@host:port/database
```

#### Vercel Postgres
```bash
# Enable in Vercel dashboard, use provided connection string
DATABASE_URL=postgres://user:pass@region.vercel-storage.com/db
```

---

## 📊 Monitoring & Health Checks

### Health Check Endpoints
```bash
# Basic health
curl https://your-app.vercel.app/health

# Detailed status
curl https://your-app.vercel.app/

# Admin panel (if enabled)
curl https://your-app.vercel.app/admin
```

### Logs
```bash
# Docker logs
docker logs peteollama-container

# Vercel logs
vercel logs

# Local development
tail -f logs/peteollama.log
```

---

## 🚨 Troubleshooting

### Common Issues

#### 1. Import Errors in Docker
```bash
# Solution: Rebuild with no cache
docker build -f Dockerfile.lightweight --no-cache -t peteollama .
```

#### 2. RunPod Connection Errors
```bash
# Check environment variables
docker exec -it container-name env | grep RUNPOD

# Test RunPod endpoint manually
curl -H "Authorization: Bearer $RUNPOD_API_KEY" \
     https://your-endpoint.runpod.net/health
```

#### 3. Memory Issues on Vercel
```bash
# Increase memory in vercel.json
{
  "functions": {
    "api/index.py": {
      "memory": 1024
    }
  }
}
```

#### 4. Database Connection Issues
```bash
# Test database connection
python -c "
import os
from sqlalchemy import create_engine
engine = create_engine(os.getenv('DATABASE_URL'))
print('✅ Database connected')
"
```

### Performance Optimization

#### 1. Container Optimization
```bash
# Use multi-stage builds for smaller images
# Exclude unnecessary files in .dockerignore
# Use specific Python version tags
```

#### 2. Serverless Optimization
```bash
# Keep RunPod endpoint warm
# Use connection pooling for database
# Enable Redis caching if available
```

---

## 🔒 Security Considerations

### Environment Variables
- ✅ Never commit `.env` files
- ✅ Use environment-specific configs
- ✅ Rotate API keys regularly
- ✅ Use strong database passwords

### Container Security
- ✅ Run as non-root user (already configured)
- ✅ Use specific base image tags
- ✅ Scan images for vulnerabilities
- ✅ Keep dependencies updated

---

## 📈 Scaling

### Horizontal Scaling
```bash
# Docker Swarm
docker service create --replicas 3 peteollama:latest

# Kubernetes
kubectl scale deployment peteollama --replicas=3

# Vercel (automatic scaling)
# No configuration needed
```

### Performance Monitoring
```bash
# Docker stats
docker stats peteollama-container

# Application metrics
curl https://your-app.com/admin/api/stats
```

---

## 🎉 Success Checklist

After deployment, verify:

- [ ] Health endpoint responds: `/health`
- [ ] Main UI loads: `/`
- [ ] Admin panel accessible: `/admin` (if enabled)
- [ ] RunPod integration working
- [ ] Database connected (if using external DB)
- [ ] Environment variables set correctly
- [ ] SSL/HTTPS working (production)
- [ ] Logs showing no errors

---

## 💡 Next Steps

1. **Monitor**: Set up monitoring and alerting
2. **Backup**: Configure database backups
3. **CDN**: Add CloudFlare or similar for static assets
4. **Domain**: Configure custom domain
5. **CI/CD**: Set up automated deployments

---

## 🔗 Quick Links

- [Docker Hub](https://hub.docker.com) - Container registry
- [Vercel](https://vercel.com) - Serverless deployment
- [RunPod](https://runpod.io) - GPU serverless platform
- [Vercel Postgres](https://vercel.com/storage/postgres) - Managed database

---

**Need help?** Check the logs first, then review the troubleshooting section above!
