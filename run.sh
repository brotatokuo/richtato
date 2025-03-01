#!/bin/bash
echo "Starting Django Server"
python richtato/manage.py makemigrations
echo "Migrations made"
python richtato/manage.py migrate
echo "Migrations applied"
echo "starting server"
ls
python richtato/manage.py runserver 0.0.0.0:$PORT
