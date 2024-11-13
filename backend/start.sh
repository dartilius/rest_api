#!/bin/bash

set -e

if ${DEBUG}; then
  exec gunicorn --bind 0:8000 --workers 4 --timeout 90 rmc_rest_api.wsgi
else
  exec gunicorn --bind 0:8000 --workers 8 --threads 2 --timeout 90 rmc_rest_api.wsgi
fi
