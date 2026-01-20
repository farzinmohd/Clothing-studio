@echo off
REM Fix for TensorFlow protobuf compatibility issue
REM This script sets environment variable and starts Django server

echo Setting protobuf environment variable...
set PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

echo Starting Django server...
python manage.py runserver

pause
