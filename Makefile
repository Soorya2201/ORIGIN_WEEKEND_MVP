# Clarity Health - Full Stack Makefile

.PHONY: help start stop dev build test clean install backend frontend

# Default target
help:
	@echo "Clarity Health - Full Stack Platform"
	@echo ""
	@echo "Available Commands:"
	@echo ""
	@echo "  make start     - Start both backend and frontend"
	@echo "  make stop      - Stop all services"
	@echo "  make dev       - Start development servers"
	@echo "  make build     - Build both backend and frontend"
	@echo "  make test      - Run all tests"
	@echo "  make clean     - Clean all build artifacts"
	@echo "  make install   - Install all dependencies"
	@echo ""
	@echo "Individual Services:"
	@echo "  make backend   - Start only backend"
	@echo "  make frontend  - Start only frontend"
	@echo ""
	@echo "Quick Start:"
	@echo "  ./start -local  - Complete setup and start (recommended)"

# Start both services
start:
	@echo "🚀 Starting Clarity Health - Full Stack Platform..."
	./start -local

# Stop all services
stop:
	@echo "🛑 Stopping all Clarity Health services..."
	@echo "Backend services..."
	@cd backend && make stop || true
	@echo "Frontend services..."
	@pkill -f "react-scripts start" || true
	@pkill -f "uvicorn" || true
	@echo "✅ All services stopped"

# Development servers
dev: start

# Build both backend and frontend
build:
	@echo "🏗️  Building Clarity Health..."
	@echo "Building backend..."
	@cd backend && make build
	@echo "Building frontend..."
	@cd frontend && make build
	@echo "✅ Full stack build complete"

# Run all tests
test:
	@echo "🧪 Running all tests..."
	@echo "Backend tests..."
	@cd backend && make test
	@echo "Frontend tests..."
	@cd frontend && make test
	@echo "✅ All tests complete"

# Clean all build artifacts
clean:
	@echo "🧹 Cleaning all build artifacts..."
	@cd backend && make clean
	@cd frontend && make clean
	@echo "✅ Clean complete"

# Install all dependencies
install:
	@echo "📦 Installing all dependencies..."
	@echo "Backend dependencies..."
	@cd backend && make install
	@echo "Frontend dependencies..."
	@cd frontend && make install
	@echo "✅ All dependencies installed"

# Start only backend
backend:
	@echo "🔧 Starting Backend only..."
	@cd backend && ./start -local

# Start only frontend
frontend:
	@echo "🎨 Starting Frontend only..."
	@cd frontend && ./start -local

# Health check
health:
	@echo "🔍 Checking service health..."
	@echo "Backend health..."
	@cd backend && make livecheck
	@echo "Frontend health..."
	@cd frontend && make livecheck
	@echo "✅ All services healthy"
