#!/bin/bash
echo "Starting Django Server"

cd richtato
echo "Installing npm dependencies..."
npm install
echo "npm dependencies installed"

python manage.py makemigrations
echo "Migrations made"

python manage.py migrate
echo "Migrations applied"

echo "starting server"
python manage.py runserver 0.0.0.0:$PORT
