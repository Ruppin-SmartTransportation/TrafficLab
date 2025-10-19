.PHONY: help down up build clean cd

# Default target
help:
	@echo "Available commands:"
	@echo "  make down     - Stop and remove containers, networks, and orphaned containers"
	@echo "  make up       - Start services with docker-compose up"
	@echo "  make build    - Build and start services with docker-compose up --build"
	@echo "  make clean    - Stop containers, remove orphans, and start with build"
	@echo "  make cd       - Take down, remove orphans, and build with no cache"

# Stop and remove containers, networks, and orphaned containers
down:
	@echo "Stopping and removing containers..."
	docker compose -f docker-compose.prod.yml down --remove-orphans

# Start services
up:
	@echo "Starting services..."
	docker compose -f docker-compose.prod.yml up -d --build

# Build and start services
build:
	@echo "Building and starting services..."
	docker compose -f docker-compose.prod.yml up --build

# Complete workflow: down, then up with build
clean: down
	@echo "Starting fresh with build..."
	docker compose -f docker-compose.prod.yml up --build

# Take down, remove orphans, and build with no cache
cd: down
	@echo "Building with no cache..."
	docker compose -f docker-compose.prod.yml build --no-cache
	@echo "Starting services in detached mode..."
	docker compose -f docker-compose.prod.yml up -d
