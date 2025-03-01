#!/bin/bash
python richtato/manage.py makemigrations
python richtato/manage.py migrate
python richtato/manage.py runserver 0.0.0.0:$PORT
