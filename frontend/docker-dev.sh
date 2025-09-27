#!/bin/bash

# Docker development helper script for Neuron v2 Frontend

set -e

case "$1" in
    "build")
        echo "🔨 Building frontend Docker image..."
        cd "$(dirname "$0")/.."
        docker compose build frontend
        echo "✅ Frontend Docker image built successfully!"
        ;;
    "start")
        echo "🚀 Starting frontend container..."
        cd "$(dirname "$0")/.."
        docker compose up frontend -d
        echo "✅ Frontend container started!"
        echo "📱 Access the app at: http://localhost:5927"
        ;;
    "stop")
        echo "🛑 Stopping frontend container..."
        cd "$(dirname "$0")/.."
        docker compose down
        echo "✅ Frontend container stopped!"
        ;;
    "logs")
        echo "📋 Showing frontend container logs..."
        cd "$(dirname "$0")/.."
        docker compose logs -f frontend
        ;;
    "shell")
        echo "🐚 Opening shell in frontend container..."
        cd "$(dirname "$0")/.."
        docker compose exec frontend sh
        ;;
    "restart")
        echo "🔄 Restarting frontend container..."
        cd "$(dirname "$0")/.."
        docker compose restart frontend
        echo "✅ Frontend container restarted!"
        ;;
    *)
        echo "Neuron v2 Frontend Docker Helper"
        echo ""
        echo "Usage: $0 {build|start|stop|logs|shell|restart}"
        echo ""
        echo "Commands:"
        echo "  build   - Build the Docker image"
        echo "  start   - Start the container in detached mode"
        echo "  stop    - Stop and remove the container"
        echo "  logs    - Show container logs (follow mode)"
        echo "  shell   - Open a shell inside the container"
        echo "  restart - Restart the container"
        echo ""
        exit 1
        ;;
esac
