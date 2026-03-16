#!/bin/bash

set -e

if ${DEBUG}; then
  exec gunicorn --bind 0:8000 --workers 18 --threads 3 --timeout 90 rmc_rest_api.wsgi
else
  exec gunicorn --bind 0:8000 --workers 18 --threads 3 --timeout 90 rmc_rest_api.wsgi
fi
