#!/bin/bash

set -e

gunicorn --bind 0:8000 --workers 4 rmc_rest_api.wsgi

exec "$@"
