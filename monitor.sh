#!/bin/bash

# TrafficLab Container Monitoring Script
# This script monitors the health of all containers and restarts them if needed

echo "🔍 Starting TrafficLab monitoring..."

# Function to check container health
check_container_health() {
    local container_name=$1
    local health_endpoint=$2
    
    if [ -z "$health_endpoint" ]; then
        # Basic container status check
        if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "$container_name.*Up"; then
            echo "✅ $container_name is running"
            return 0
        else
            echo "❌ $container_name is not running"
            return 1
        fi
    else
        # Health endpoint check
        local response=$(docker exec "$container_name" curl -s -o /dev/null -w "%{http_code}" "$health_endpoint" 2>/dev/null)
        if [ "$response" = "200" ]; then
            echo "✅ $container_name health check passed"
            return 0
        else
            echo "❌ $container_name health check failed (HTTP $response)"
            return 1
        fi
    fi
}

# Function to restart container
restart_container() {
    local container_name=$1
    echo "🔄 Restarting $container_name..."
    docker restart "$container_name"
    sleep 10
}

# Main monitoring loop
while true; do
    echo "📊 Checking container health at $(date)"
    
    # Check backend health
    if ! check_container_health "trafficlab-backend-1" "http://localhost:8000/health"; then
        restart_container "trafficlab-backend-1"
    fi
    
    # Check frontend health
    if ! check_container_health "trafficlab-frontend-1"; then
        restart_container "trafficlab-frontend-1"
    fi
    
    # Check database health
    if ! check_container_health "trafficlab-db-1"; then
        restart_container "trafficlab-db-1"
    fi
    
    echo "✅ Health check complete. Sleeping for 60 seconds..."
    sleep 60
done

