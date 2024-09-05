# RMC_REST_API WIP

### Установка и запуск
```
1. git clone
2. создайте файл .env в корневой директории и задайте следующие переменные:
 - SECRET_KEY
 - ALLOWED_HOSTS
 - DEBUG

 - MINIO_STORAGE_ACCESS_KEY
 - MINIO_STORAGE_SECRET_KEY
 - MINIO_ENDPOINT
 - MINIO_ROOT_USER
 - MINIO_ROOT_PASSWORD
 
 - POSTGRES_USER
 - POSTGRES_PASSWORD
 - POSTGRES_DB
 - DB_HOST
 - DB_PORT
 
 - CELERY_BROKER
 - CELERY_BACKEND
 - RABBITMQ_USER
 - RABBITMQ_PASS
3. docker compose up --build
4. docker exec backend sh -c "python manage.py makemigrations"
5. docker exec backend sh -c "python manage.py migrate"
5.1 если ругается на этапе Applying admin.0001.initial...
    то нужно отдельно выполнить 
    docker exec backend sh -c "python manage.py makemigrations users"
    а затем снова провести миграции
6. docker exec backend sh -c "python manage.py collectstatic --no-input"
7. docker exec backend sh -c "python manage.py createsuperuser"
8. войдите в Minio по адресу http://localhost:9001
9. во вкладке Access Keys создайте новый ключ доступа и внесите данные в .env
10. перезапустите кластер

```