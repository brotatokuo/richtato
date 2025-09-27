# Richtato - Docker Setup

This document explains how to run the Richtato application using Docker Compose.

## Prerequisites

- Docker Desktop or Docker Engine
- Docker Compose

## Quick Start

### Development Environment

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd richtato
   ```

2. **Start all services**:
   ```bash
   docker-compose up --build
   ```

3. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - Django Admin: http://localhost:8000/admin

### Production Environment

1. **Create environment file**:
   ```bash
   cp .env.example .env
   # Edit .env with your production values
   ```

2. **Start production services**:
   ```bash
   docker-compose -f docker-compose.prod.yml up --build -d
   ```

## Services

### Database (PostgreSQL)
- **Port**: 5432
- **Database**: richtato
- **Username**: richtato
- **Password**: richtato_password (dev) / ${POSTGRES_PASSWORD} (prod)

### Backend (Django)
- **Port**: 8000
- **Framework**: Django 5.1 + DRF
- **Database**: PostgreSQL
- **Features**: API endpoints, admin panel, CORS enabled

### Frontend (React)
- **Port**: 3000 (dev) / 80 (prod)
- **Framework**: React 19 + TypeScript + Vite
- **Features**: Hot reload (dev), optimized build (prod)

## Development Commands

### Start services
```bash
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# Start with rebuild
docker-compose up --build
```

### Stop services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### View logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs backend
docker-compose logs frontend
docker-compose logs db
```

### Execute commands
```bash
# Django shell
docker-compose exec backend python manage.py shell

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Run migrations
docker-compose exec backend python manage.py migrate

# Collect static files
docker-compose exec backend python manage.py collectstatic
```

### Database operations
```bash
# Access PostgreSQL shell
docker-compose exec db psql -U richtato -d richtato

# Backup database
docker-compose exec db pg_dump -U richtato richtato > backup.sql

# Restore database
docker-compose exec -T db psql -U richtato richtato < backup.sql
```

## Environment Variables

### Development (.env.example)
```env
SECRET_KEY=your-super-secret-key-change-this-in-production
DEBUG=True
DEPLOY_STAGE=DEV
DEV_DATABASE_URL=postgresql://richtato:richtato_password@db:5432/richtato
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://frontend:3000
```

### Production
```env
SECRET_KEY=your-production-secret-key
DEBUG=False
DEPLOY_STAGE=PROD
PROD_DATABASE_URL=postgresql://richtato:your-password@db:5432/richtato
POSTGRES_PASSWORD=your-secure-password
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

## Troubleshooting

### Common Issues

1. **Port already in use**:
   ```bash
   # Check what's using the port
   lsof -i :3000
   lsof -i :8000
   lsof -i :5432

   # Kill the process or change ports in docker-compose.yml
   ```

2. **Database connection issues**:
   ```bash
   # Check if database is running
   docker-compose ps

   # Check database logs
   docker-compose logs db

   # Restart database
   docker-compose restart db
   ```

3. **Frontend not loading**:
   ```bash
   # Check frontend logs
   docker-compose logs frontend

   # Rebuild frontend
   docker-compose up --build frontend
   ```

4. **CORS errors**:
   - Ensure `CORS_ALLOWED_ORIGINS` includes your frontend URL
   - Check that the frontend is making requests to the correct backend URL

### Reset Everything
```bash
# Stop and remove all containers, networks, and volumes
docker-compose down -v --remove-orphans

# Remove all images
docker system prune -a

# Start fresh
docker-compose up --build
```

## File Structure

```
richtato/
├── docker-compose.yml          # Development compose file
├── docker-compose.prod.yml     # Production compose file
├── docker-compose.override.yml # Local development overrides
├── Dockerfile.backend          # Django backend Dockerfile
├── requirements.txt            # Python dependencies
├── backend/                    # Django project
│   ├── manage.py
│   ├── richtato/
│   └── apps/
├── frontend/                   # React project
│   ├── Dockerfile             # Development Dockerfile
│   ├── Dockerfile.prod        # Production Dockerfile
│   ├── nginx.conf             # Nginx configuration
│   ├── package.json
│   └── src/
└── README-DOCKER.md           # This file
```

## Next Steps

1. **Set up CI/CD**: Configure GitHub Actions or similar for automated builds
2. **Add monitoring**: Integrate logging and monitoring solutions
3. **SSL/TLS**: Set up HTTPS for production
4. **Load balancing**: Add nginx or similar for production scaling
5. **Backup strategy**: Implement automated database backups
