# 🐳 Jamie Docker Deployment Guide

This guide covers containerizing your Jamie Property Management Agent with Docker, including database setup and deployment options.

## 📋 Quick Start

### 1. Prerequisites
- Docker installed and running
- Docker Compose (usually included with Docker Desktop)
- Your RunPod API credentials

### 2. Clone and Build
```bash
# Make the build script executable (if not already)
chmod +x docker-build.sh

# Run the interactive build script
./docker-build.sh
```

### 3. Manual Build (Alternative)
```bash
# Build the image
docker build -t jamie-app:latest .

# Run full stack
docker-compose up -d
```

## 🏗️ Architecture Overview

### Local Development Stack
```
┌─────────────────────────────────┐
│        Jamie App Container      │
│     (FastAPI + RunPod Client)   │  ←─ Port 8000
└─────────────────────────────────┘
                 │
┌─────────────────────────────────┐
│      PostgreSQL Database       │  ←─ Port 5432
│    (Conversation Logs & Data)   │
└─────────────────────────────────┘
                 │
┌─────────────────────────────────┐
│         Redis Cache             │  ←─ Port 6379
│      (Session & Caching)        │
└─────────────────────────────────┘
```

### Production Architecture (Vercel)
```
┌─────────────────────────────────┐
│         Vercel Functions        │
│        (Jamie App Code)         │
└─────────────────────────────────┘
                 │
┌─────────────────────────────────┐
│       External Database         │
│   (Vercel Postgres/Supabase)    │
└─────────────────────────────────┘
                 │
┌─────────────────────────────────┐
│        RunPod Serverless        │
│         (AI Inference)          │
└─────────────────────────────────┘
```

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Copy template and configure
cp .env.docker .env
```

**Required Variables:**
- `RUNPOD_API_KEY`: Your RunPod API key
- `RUNPOD_SERVERLESS_ENDPOINT`: Your RunPod endpoint ID

**Database Options:**
1. **Local Development:** Use Docker Postgres (default)
2. **Production:** Use external database service

## 📊 Database Setup

### Option 1: Docker PostgreSQL (Local Development)
The `docker-compose.yml` includes PostgreSQL with:
- ✅ Conversation logging
- ✅ VAPI call tracking  
- ✅ User session management
- ✅ Analytics dashboard data
- ✅ Automatic schema setup via `init-db.sql`

### Option 2: External Database (Production)
For Vercel deployment, choose one:

#### Vercel Postgres (Recommended)
```bash
# Install Vercel CLI
npm i -g vercel

# Add Vercel Postgres to your project
vercel postgres create jamie-db
```

#### Supabase (Alternative)
```bash
# Sign up at supabase.com and create a project
# Get your DATABASE_URL from the dashboard
```

#### Neon (Alternative)
```bash
# Sign up at neon.tech and create a database
# Get your connection string
```

## 🚀 Deployment Options

### 1. Local Development with Docker
```bash
# Full stack with database
docker-compose up -d

# View logs
docker-compose logs -f jamie-app

# Access services
# Jamie App: http://localhost:8000
# PostgreSQL: localhost:5432 (jamie/jamie_dev_password)
# Redis: localhost:6379
```

### 2. Production Docker (Standalone)
```bash
# Build production image
docker build -t jamie-app:latest .

# Run with external database
docker run -d \
  --name jamie-prod \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql://user:pass@host:5432/db" \
  -e RUNPOD_API_KEY="your_key" \
  -e RUNPOD_SERVERLESS_ENDPOINT="your_endpoint" \
  jamie-app:latest
```

### 3. Vercel Serverless (Recommended for Production)
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Add environment variables in Vercel dashboard:
# - RUNPOD_API_KEY
# - RUNPOD_SERVERLESS_ENDPOINT  
# - DATABASE_URL (from your database provider)
```

## 🗄️ Database Schema

The included `init-db.sql` creates these tables:
- `conversations` - All chat interactions
- `vapi_calls` - Voice call logs
- `user_sessions` - Session tracking
- `analytics_summary` - Dashboard metrics

## 📊 Monitoring & Logs

### Docker Logs
```bash
# View application logs
docker-compose logs -f jamie-app

# View database logs
docker-compose logs -f postgres

# View all services
docker-compose logs -f
```

### Health Checks
- **App Health:** `http://localhost:8000/health`
- **Database:** Built-in PostgreSQL health checks
- **Container Status:** `docker-compose ps`

## 🔧 Troubleshooting

### Common Issues

#### Build Errors
```bash
# Clean Docker cache
docker system prune -a

# Rebuild without cache
docker build --no-cache -t jamie-app:latest .
```

#### Database Connection Issues
```bash
# Check database container
docker-compose exec postgres pg_isready -U jamie

# Connect to database
docker-compose exec postgres psql -U jamie -d jamie_db
```

#### Permission Issues
```bash
# Fix volume permissions
sudo chown -R $(id -u):$(id -g) ./data ./logs
```

### Performance Tuning

#### For High Traffic
```yaml
# In docker-compose.yml, add:
services:
  jamie-app:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 1G
```

## 🔒 Security Considerations

### Production Checklist
- ✅ Use non-root user in container (already implemented)
- ✅ Environment secrets via external secrets manager
- ✅ Database connection over SSL
- ✅ Regular security updates
- ✅ Container vulnerability scanning

### Secrets Management
```bash
# Use Docker secrets in production
echo "your_api_key" | docker secret create runpod_api_key -

# Reference in compose file
secrets:
  - runpod_api_key
```

## 📈 Scaling

### Horizontal Scaling
```bash
# Scale app containers
docker-compose up --scale jamie-app=3 -d

# Add load balancer (nginx)
# See nginx.conf example in /docs
```

### Database Scaling
- **Read Replicas:** For high-read workloads
- **Connection Pooling:** PgBouncer recommended
- **Sharding:** For very large datasets

## 🎯 Next Steps

1. **Set up monitoring:** Prometheus + Grafana
2. **Add CI/CD:** GitHub Actions for auto-deployment  
3. **Implement caching:** Redis for conversation history
4. **Add rate limiting:** For API endpoints
5. **Set up backups:** Automated database backups

## 💡 Tips

- **Development:** Use `docker-compose` for full stack
- **Production:** Use Vercel + external database for best performance
- **Testing:** Run tests in containers with `docker-compose -f docker-compose.test.yml up`
- **Debugging:** Use `docker-compose exec jamie-app bash` to access container shell

---

🎉 **Your Jamie Property Management Agent is now ready for containerized deployment!**
