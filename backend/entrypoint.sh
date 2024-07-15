#!/bin/bash

set -e

while getopts ':abc' option; do
  case $option in
    a)
      if [ "${LOGNAME:-$USER}" = "uid0001" ] ; then
        echo "rerunning $0 as user root"
        sleep 1
        exec su - root -c "/app/entrypoint.sh $@"
      fi
      echo "hello I am $LOGNAME"

      python manage.py collectstatic --no-input
      python manage.py makemigrations
      python manage.py migrate
      gunicorn --bind 0:8000 --workers 8 rmc_rest_api.wsgi
      ;;

    b)
      gunicorn --bind 0:8000 --workers 8 rmc_rest_api.wsgi
      ;;

    ?)
      echo invalid args "$OPTARG"
      ;;

  esac
done

exec "$@"