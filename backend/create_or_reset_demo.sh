#!/bin/bash

# Create or reset demo user data
# This script should be run from the backend directory

echo "Creating or resetting demo user data..."

# Run the Django management command
python manage.py shell -c "from apps.richtato_user.demo_user_factory import DemoUserFactory; DemoUserFactory().create_or_reset()"

echo "Demo user data created successfully!"
echo "Username: demo"
echo "Password: demopassword123!"
echo "Email: demo@richtato.com"
