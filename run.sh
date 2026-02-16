#!/bin/bash
# Simple run script for Smart Classroom System

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the Flask application
python3 app/app.py
