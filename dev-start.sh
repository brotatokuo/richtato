#!/bin/bash

# Start Django backend
echo "Starting Django backend..."
cd richtato
python manage.py runserver 8000 &
DJANGO_PID=$!

# Start React frontend
echo "Starting React frontend..."
cd ../frontend
yarn dev &
REACT_PID=$!

echo "Development servers started!"
echo "Django backend: http://localhost:8000"
echo "React frontend: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for user to stop
wait

# Cleanup
echo "Stopping servers..."
kill $DJANGO_PID 2>/dev/null
kill $REACT_PID 2>/dev/null
echo "Servers stopped."
