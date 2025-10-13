#!/bin/bash

# Database Initialization Script for TrafficLab
# This script ensures the database is properly initialized before starting the application

set -e

echo "🗄️ Initializing TrafficLab Database..."

# Function to wait for database to be ready
wait_for_db() {
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Waiting for database to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if docker exec trafficlab-db-1 pg_isready -U user -d trafficlab > /dev/null 2>&1; then
            echo "✅ Database is ready"
            return 0
        fi
        
        echo "⏳ Database not ready yet... (attempt $attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
    
    echo "❌ Database failed to become ready after $max_attempts attempts"
    return 1
}

# Function to initialize database tables
init_database() {
    echo "🔧 Creating database tables..."
    
    if docker exec trafficlab-backend-1 python -c "
from models.database import create_tables
try:
    create_tables()
    print('✅ Database tables created successfully')
except Exception as e:
    print(f'❌ Error creating tables: {e}')
    exit(1)
"; then
        echo "✅ Database initialization completed"
    else
        echo "❌ Database initialization failed"
        return 1
    fi
}

# Function to verify database setup
verify_database() {
    echo "🔍 Verifying database setup..."
    
    if docker exec trafficlab-db-1 psql -U user -d trafficlab -c "\dt" | grep -q "journeys"; then
        echo "✅ Journeys table exists"
    else
        echo "❌ Journeys table not found"
        return 1
    fi
    
    if docker exec trafficlab-db-1 psql -U user -d trafficlab -c "SELECT COUNT(*) FROM journeys;" > /dev/null 2>&1; then
        echo "✅ Database is accessible"
    else
        echo "❌ Database is not accessible"
        return 1
    fi
}

# Main execution
main() {
    echo "🚀 Starting database initialization process..."
    
    # Check if containers are running
    if ! docker ps | grep -q "trafficlab-db-1"; then
        echo "❌ Database container is not running. Please start the services first."
        exit 1
    fi
    
    if ! docker ps | grep -q "trafficlab-backend-1"; then
        echo "❌ Backend container is not running. Please start the services first."
        exit 1
    fi
    
    # Wait for database to be ready
    wait_for_db
    
    # Initialize database
    init_database
    
    # Verify setup
    verify_database
    
    echo "🎉 Database initialization completed successfully!"
    echo "📊 You can now start the application with: docker compose -f docker-compose.prod.yml up -d"
}

# Run main function
main "$@"

