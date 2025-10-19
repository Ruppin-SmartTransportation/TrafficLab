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
	docker-compose down --remove-orphans

# Start services
up:
	@echo "Starting services..."
	docker-compose up

# Build and start services
build:
	@echo "Building and starting services..."
	docker-compose up --build

# Complete workflow: down, then up with build
clean: down
	@echo "Starting fresh with build..."
	docker-compose up --build

# Take down, remove orphans, and build with no cache
cd: down
	@echo "Building with no cache..."
	docker-compose build --no-cache
	@echo "Starting services..."
	docker-compose up
