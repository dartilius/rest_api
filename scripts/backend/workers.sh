#!/usr/bin/env bash

workers=$1
count=1

while [[ $count -le $workers ]]; do
  celery -A rmc_rest_api worker -n worker$count@backend -D -l INFO \
   --logfile=/app/logs/%n.log \
   --pidfile=/app/logs/%n.pid \
   --pool=solo
   ((count += 1))
done

#w_pids=()
#count=1
#
#while [[ $count -le $workers ]]; do
#  w_pids+=(`cat /app/logs/worker$count@backend.pid`)
#  ((count += 1))
#done

