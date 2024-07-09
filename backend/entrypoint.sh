#!/bin/bash

set -e

case "$1" in

  "b")
    gunicorn --bind 0:8000 --workers 8 rmc_rest_api.wsgi
    ;;

  "c")
    celery worker --logfile=logs/celery.log -l INFO
    ;;

esac

exec "$@"