#!/bin/bash

set -e

exec gunicorn --bind 0:8000 --workers 18 --worker-class rmc_rest_api.asgi_worker.RuntimeWorker --timeout 90 rmc_rest_api.asgi:application
