#!/bin/bash
# Script to reset all migrations and create fresh ones
# WARNING: This will delete all existing migrations and require a database reset

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Apps with migrations
APPS=(
    "budget"
    "categorization"
    "financial_account"
    "richtato_user"
    "sync"
    "transaction"
)

echo "⚠️  WARNING: This will delete all existing migrations!"
echo "   Make sure you've backed up your database if needed."
echo ""
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo "🗑️  Removing existing migrations..."

for app in "${APPS[@]}"; do
    migrations_dir="apps/${app}/migrations"

    if [ ! -d "$migrations_dir" ]; then
        echo "⚠️  Skipping $app: no migrations directory"
        continue
    fi

    # Remove all migration files except __init__.py
    find "$migrations_dir" -name "*.py" ! -name "__init__.py" -type f -delete
    echo "✅ Removed migrations from $app"
done

echo ""
echo "📦 Creating fresh migrations..."

for app in "${APPS[@]}"; do
    echo "Creating migrations for $app..."
    python manage.py makemigrations "$app" || {
        echo "❌ Failed to create migrations for $app"
    }
done

echo ""
echo "✨ Done! Fresh migrations created."
echo ""
echo "⚠️  NEXT STEPS:"
echo "1. Reset your database (if needed):"
echo "   docker compose exec db psql -U richtato -d richtato_db -c 'DROP SCHEMA public CASCADE; CREATE SCHEMA public;'"
echo "   OR: docker compose down -v && docker compose up -d"
echo ""
echo "2. Apply migrations:"
echo "   docker compose exec backend python manage.py migrate"
echo ""
echo "3. Create superuser (if needed):"
echo "   docker compose exec backend python manage.py createsuperuser"
