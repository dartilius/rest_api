#!/bin/bash

gunicorn --bind 0:8000 --workers 8 rmc_rest_api.wsgi

#celery worker --app=backend --logfile=logs/celery.log -l INFO