#!/bin/bash
# Script to squash migrations for all Django apps
# Usage: ./squash_all_migrations.sh [app_name]
# If app_name is provided, only squash that app. Otherwise, squash all apps.

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Apps with migrations (based on project structure)
APPS=(
    "budget"
    "categorization"
    "financial_account"
    "richtato_user"
    "sync"
    "transaction"
)

# Function to get migration numbers for an app
get_migrations() {
    local app=$1
    local migrations_dir="apps/${app}/migrations"

    if [ ! -d "$migrations_dir" ]; then
        return 1
    fi

    # Get all migration files except __init__.py, __pycache__, and squashed migrations
    ls -1 "$migrations_dir"/*.py 2>/dev/null | \
        grep -v __init__ | \
        grep -v squashed | \
        grep -E '[0-9]+_' | \
        sed 's/.*\/\([0-9]*\)_.*/\1/' | \
        sort -n | \
        uniq
}

# Function to squash migrations for an app
squash_app() {
    local app=$1
    local migrations_dir="apps/${app}/migrations"

    if [ ! -d "$migrations_dir" ]; then
        echo "⚠️  Skipping $app: no migrations directory"
        return 0
    fi

    # Get all migration numbers into an array
    local migrations_str=$(get_migrations "$app" 2>/dev/null)
    if [ -z "$migrations_str" ]; then
        echo "⚠️  Skipping $app: no migration files found"
        return 0
    fi

    # Convert to array
    local migrations=()
    while IFS= read -r line; do
        migrations+=("$line")
    done <<< "$migrations_str"

    local migration_count=${#migrations[@]}

    if [ $migration_count -le 1 ]; then
        echo "⚠️  Skipping $app: only $migration_count migration(s), nothing to squash"
        return 0
    fi

    # Get first and last migration numbers (using compatible indexing)
    local first_migration=${migrations[0]}
    local last_index=$((migration_count - 1))
    local last_migration=${migrations[$last_index]}

    # Squash from first to second-to-last (keep the last one separate)
    local second_to_last_index=$((migration_count - 2))
    local second_to_last=${migrations[$second_to_last_index]}

    # Skip if first == second_to_last (nothing to squash)
    if [ "$first_migration" = "$second_to_last" ]; then
        echo "⚠️  Skipping $app: first migration ($first_migration) == second-to-last ($second_to_last), nothing to squash"
        return 0
    fi

    echo "📦 Squashing migrations for $app:"
    echo "   Migrations found: ${migrations[*]}"
    echo "   From: ${first_migration} to: ${second_to_last}"
    echo "   (Keeping ${last_migration} separate)"

    python manage.py squashmigrations "$app" "$first_migration" "$second_to_last" --noinput || {
        echo "❌ Failed to squash migrations for $app"
        return 1
    }

    echo "✅ Successfully squashed migrations for $app"
    echo ""
}

# Main execution
if [ $# -eq 1 ]; then
    # Squash specific app
    APP=$1
    if [[ ! " ${APPS[@]} " =~ " ${APP} " ]]; then
        echo "❌ Error: '$APP' is not a valid app name"
        echo "Available apps: ${APPS[*]}"
        exit 1
    fi
    squash_app "$APP"
else
    # Squash all apps
    echo "🔄 Squashing migrations for all apps..."
    echo ""

    for app in "${APPS[@]}"; do
        squash_app "$app"
    done

    echo "✨ Done! All migrations have been squashed."
    echo ""
    echo "⚠️  IMPORTANT NEXT STEPS:"
    echo "1. Review the squashed migration files"
    echo "2. Test that migrations work: python manage.py migrate --plan"
    echo "3. If everything looks good, you can delete the old migration files"
    echo "4. Commit the changes"
fi
