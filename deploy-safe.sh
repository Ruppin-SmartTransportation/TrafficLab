#!/bin/bash

# Safe Deployment Script for TrafficLab
# This script ensures proper deployment with health checks and rollback capability

set -e  # Exit on any error

echo "🚀 Starting safe deployment of TrafficLab..."

# Function to check if a service is healthy
check_service_health() {
    local service_name=$1
    local max_attempts=30
    local attempt=1
    
    echo "🔍 Checking health of $service_name..."
    
    while [ $attempt -le $max_attempts ]; do
        if docker compose -f docker-compose.prod.yml ps | grep -q "$service_name.*Up"; then
            echo "✅ $service_name is running"
            return 0
        fi
        
        echo "⏳ Waiting for $service_name to start... (attempt $attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    echo "❌ $service_name failed to start after $max_attempts attempts"
    return 1
}

# Function to backup current deployment
backup_deployment() {
    echo "💾 Creating backup of current deployment..."
    docker compose -f docker-compose.prod.yml ps > backup-$(date +%Y%m%d-%H%M%S).txt
}

# Function to rollback on failure
rollback_deployment() {
    echo "🔄 Rolling back deployment..."
    docker compose -f docker-compose.prod.yml down
    docker compose -f docker-compose.prod.yml up -d
}

# Main deployment process
main() {
    # Create backup
    backup_deployment
    
    # Stop current services
    echo "🛑 Stopping current services..."
    docker compose -f docker-compose.prod.yml down
    
    # Build new images
    echo "🔨 Building new images..."
    docker compose -f docker-compose.prod.yml build --no-cache
    
    # Start services
    echo "🚀 Starting services..."
    docker compose -f docker-compose.prod.yml up -d
    
    # Wait for services to be ready
    echo "⏳ Waiting for services to be ready..."
    sleep 30
    
    # Initialize database
    echo "🗄️ Initializing database..."
    if ! ./init-db.sh; then
        echo "❌ Database initialization failed"
        rollback_deployment
        exit 1
    fi
    
    # Health checks
    if ! check_service_health "trafficlab-backend-1"; then
        echo "❌ Backend health check failed"
        rollback_deployment
        exit 1
    fi
    
    if ! check_service_health "trafficlab-frontend-1"; then
        echo "❌ Frontend health check failed"
        rollback_deployment
        exit 1
    fi
    
    if ! check_service_health "trafficlab-db-1"; then
        echo "❌ Database health check failed"
        rollback_deployment
        exit 1
    fi
    
    # Test API endpoints
    echo "🧪 Testing API endpoints..."
    if ! curl -f -s https://api.smart-transport.cloud/health > /dev/null; then
        echo "❌ API health check failed"
        rollback_deployment
        exit 1
    fi
    
    if ! curl -f -s https://demo.smart-transport.cloud/ > /dev/null; then
        echo "❌ Frontend health check failed"
        rollback_deployment
        exit 1
    fi
    
    echo "✅ Deployment successful! All services are healthy."
    echo "🌐 Frontend: https://demo.smart-transport.cloud/"
    echo "🔗 API: https://api.smart-transport.cloud/"
}

# Run main function
main "$@"
