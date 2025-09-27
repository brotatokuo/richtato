#!/bin/bash

# Docker development helper script for Richtato

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker Desktop and try again."
        exit 1
    fi
}

# Function to show help
show_help() {
    echo "Richtato Docker Development Helper"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start       Start all services (default)"
    echo "  stop        Stop all services"
    echo "  restart     Restart all services"
    echo "  build       Build and start all services"
    echo "  logs        Show logs for all services"
    echo "  logs-backend Show backend logs"
    echo "  logs-frontend Show frontend logs"
    echo "  logs-db     Show database logs"
    echo "  shell       Open Django shell"
    echo "  migrate     Run Django migrations"
    echo "  superuser   Create Django superuser"
    echo "  demo        Create or reset demo user data"
    echo "  clean       Clean up containers and volumes"
    echo "  status      Show status of all services"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 logs-backend"
    echo "  $0 shell"
}

# Function to start services
start_services() {
    print_status "Starting Richtato services..."
    docker-compose up -d
    print_success "Services started successfully!"
    print_status "Frontend: http://localhost:3000"
    print_status "Backend: http://localhost:8000"
    print_status "Database: localhost:5432"
}

# Function to stop services
stop_services() {
    print_status "Stopping Richtato services..."
    docker-compose down
    print_success "Services stopped successfully!"
}

# Function to restart services
restart_services() {
    print_status "Restarting Richtato services..."
    docker-compose restart
    print_success "Services restarted successfully!"
}

# Function to build and start services
build_services() {
    print_status "Building and starting Richtato services..."
    docker-compose up --build -d
    print_success "Services built and started successfully!"
}

# Function to show logs
show_logs() {
    docker-compose logs -f
}

# Function to show backend logs
show_backend_logs() {
    docker-compose logs -f backend
}

# Function to show frontend logs
show_frontend_logs() {
    docker-compose logs -f frontend
}

# Function to show database logs
show_db_logs() {
    docker-compose logs -f db
}

# Function to open Django shell
open_shell() {
    print_status "Opening Django shell..."
    docker-compose exec backend python manage.py shell
}

# Function to run migrations
run_migrations() {
    print_status "Running Django migrations..."
    docker-compose exec backend python manage.py migrate
    print_success "Migrations completed successfully!"
}

# Function to create superuser
create_superuser() {
    print_status "Creating Django superuser..."
    docker-compose exec backend python manage.py createsuperuser
}

# Function to create demo user
create_demo_user() {
    print_status "Creating or resetting demo user data..."
    docker-compose exec backend bash -c "cd /app && ./create_or_reset_demo.sh"
    print_success "Demo user created successfully!"
    print_status "Username: demo"
    print_status "Password: demopassword123!"
    print_status "Email: demo@richtato.com"
}

# Function to clean up
clean_up() {
    print_warning "This will remove all containers, networks, and volumes. Are you sure? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_status "Cleaning up Docker resources..."
        docker-compose down -v --remove-orphans
        docker system prune -f
        print_success "Cleanup completed successfully!"
    else
        print_status "Cleanup cancelled."
    fi
}

# Function to show status
show_status() {
    print_status "Service Status:"
    docker-compose ps
}

# Main script logic
main() {
    check_docker

    case "${1:-start}" in
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        build)
            build_services
            ;;
        logs)
            show_logs
            ;;
        logs-backend)
            show_backend_logs
            ;;
        logs-frontend)
            show_frontend_logs
            ;;
        logs-db)
            show_db_logs
            ;;
        shell)
            open_shell
            ;;
        migrate)
            run_migrations
            ;;
        superuser)
            create_superuser
            ;;
        demo)
            create_demo_user
            ;;
        clean)
            clean_up
            ;;
        status)
            show_status
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
