#!/bin/bash

# Jamie Docker Build Script
# Builds and optionally runs the Docker containers

set -e

echo "🏗️ Building Jamie Docker containers..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️ .env file not found. Copying from .env.docker template...${NC}"
    cp .env.docker .env
    echo -e "${YELLOW}🔧 Please edit .env file with your actual credentials before continuing.${NC}"
    read -p "Press Enter after updating .env file, or Ctrl+C to cancel..."
fi

# Build the Docker image
echo -e "${BLUE}📦 Building Jamie application image...${NC}"
docker build -t jamie-app:latest .

# Check if user wants to run the full stack
echo -e "${BLUE}🚀 Build complete! Options:${NC}"
echo "1. Run full stack (Jamie + PostgreSQL + Redis)"
echo "2. Run only Jamie app (requires external database)"
echo "3. Just build (don't run anything)"

read -p "Choose option (1-3): " option

case $option in
    1)
        echo -e "${GREEN}🌟 Starting full stack with docker-compose...${NC}"
        docker-compose up -d
        echo -e "${GREEN}✅ Full stack started!${NC}"
        echo -e "${BLUE}📱 Jamie app: http://localhost:8000${NC}"
        echo -e "${BLUE}🗄️ PostgreSQL: localhost:5432${NC}"
        echo -e "${BLUE}🔴 Redis: localhost:6379${NC}"
        echo ""
        echo "📋 Useful commands:"
        echo "  - View logs: docker-compose logs -f jamie-app"
        echo "  - Stop stack: docker-compose down"
        echo "  - View all containers: docker-compose ps"
        ;;
    2)
        echo -e "${GREEN}🏃 Running Jamie app only...${NC}"
        docker run -d \
            --name jamie-app-standalone \
            -p 8000:8000 \
            --env-file .env \
            jamie-app:latest
        echo -e "${GREEN}✅ Jamie app started on http://localhost:8000${NC}"
        echo "📋 Useful commands:"
        echo "  - View logs: docker logs -f jamie-app-standalone"
        echo "  - Stop app: docker stop jamie-app-standalone"
        echo "  - Remove container: docker rm jamie-app-standalone"
        ;;
    3)
        echo -e "${GREEN}✅ Build complete! Image 'jamie-app:latest' is ready.${NC}"
        ;;
    *)
        echo -e "${YELLOW}Invalid option. Exiting.${NC}"
        exit 1
        ;;
esac

echo -e "${GREEN}🎉 Docker setup complete!${NC}"
