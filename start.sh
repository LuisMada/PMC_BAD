#!/usr/bin/env bash

# Start Gunicorn processes
echo Starting Gunicorn.
exec gunicorn BAD_PMC.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2