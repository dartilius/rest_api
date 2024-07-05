# RMC_REST_API

### Установка и запуск
```
docker compose build
docker compose up -d
docker exec -it db  sh -c "psql -U postgres -d rest_api -c 'CREATE EXTENSION hstore;'"
docker exec -it backend sh -c "python3 manage.py migrate"
docker exec -it backend sh -c "python3 manage.py initialize_buckets"
```