# RMC_REST_API WIP

### Установка и запуск

1. Клонируем проект
```bash
git clone git@webgit.krasrm.com:shaleinikove/rmc_rest_api.git
```
2. создайте файл ```.env``` в корневой директории и задайте следующие переменные:
```
SECRET_KEY
ALLOWED_HOSTS
DEBUG

MINIO_STORAGE_ACCESS_KEY
MINIO_STORAGE_SECRET_KEY
MINIO_ENDPOINT
MINIO_ROOT_USER
MINIO_ROOT_PASSWORD

POSTGRES_USER
POSTGRES_PASSWORD
POSTGRES_DB
DB_HOST
DB_PORT

CLICKHOUSE_DB
CLICKHOUSE_HOST
CLICKHOUSE_PORT
CLICKHOUSE_USER
CLICKHOUSE_PASSWORD
CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT = 1

CELERY_BROKER
CELERY_BACKEND
RABBITMQ_USER
RABBITMQ_PASS
```
3. Поднимаем файловое хранилище чтобы получить 
```MINIO_STORAGE_ACCESS_KEY``` 
и ```MINIO_STORAGE_SECRET_KEY```
```bahs
docker compose up --build files
```
4. Открываем в браузере админ панель minio http://127.0.0.1/9001
5. Во вкладке ```Access Keys``` создайте новый ключ 
доступа и внесите данные в ```.env```
6. Собираем проект
```bash
docker compose up --build
```
7. Добавляем пользователя RabbitMQ
```bash
docker exec rabbit sh -c "rabbitmqctl add_user <RABBITMQ_USER> <RABBITMQ_PASSWORD>"
docker exec rabbit sh -c "rabbitmqctl set_permissions <RABBITMQ_USER> '.*' '.*' '.*'"
docker exec rabbit sh -c "rabbitmqctl set_user_tags uid0001 administrator"
```
8. Проводим миграции, собираем статические файлы и создаем суперпользователя
```bash
docker exec backend sh -c "python manage.py makemigrations"
docker exec backend sh -c "python manage.py migrate"
docker exec backend sh -c "python manage.py migrate --database clickhouse"
docker exec backend sh -c "python manage.py collectstatic --no-input"
docker exec backend sh -c "python manage.py createsuperuser"
```

### Цель проекта

### Используемые технологии

### Возможности проекта