# RMC_REST_API WIP

### Установка и запуск

1. git clone 
2. создайте файл ```.env``` в корневой директории и задайте следующие переменные:
```bash
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
 
 - CLICKHOUSE_NAME
 - CLICKHOUSE_HOST
 - CLICKHOUSE_PORT
 - CLICKHOUSE_USER
 - CLICKHOUSE_PASSWORD
 
 - CELERY_BROKER
 - CELERY_BACKEND
 - RABBITMQ_USER
 - RABBITMQ_PASS
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
7. Настраиваем базу данных clickhouse
```bash
docker compose exec clickhouse bash
apt-get update
apt-get install nano
nano /etc/clickhouse-server/users.xml 
```
(либо открыть файлы в docker desctop) и 
в блоке ```<users><default>``` добавить следующее
```bash 
<access_management>1</access_management>
<named_collection_control>1</named_collection_control>
<show_named_collections>1</show_named_collections>
<show_named_collections_secrets>1</show_named_collections_secrets>
```
- Создаем пользователя базы clickhouse и даем ему права суперпользователя
```bash
clickhouse-client
CREATE USER <CLICKHOUSE_USER> IDENTIFIED BY 'password';
GRANT ALL ON *.* TO <CLICKHOUSE_USER> WITH GRANT OPTION;
CREATE DATABASE statistic;
```
8. Добавляем пользователя RabbitMQ
```bash
rabbitmqctl add_user <USER> <PASSWORD>
rabbitmqctl set_permissions <USER> ".*" ".*" ".*"
```
9. Проводим миграции, собираем статические файлы и создаем суперпользователя
```bash
docker exec backend sh -c "python manage.py makemigrations"
docker exec backend sh -c "python manage.py migrate"
docker compose exec backend sh -c "python manage.py migrate --database clickhouse"
docker exec backend sh -c "python manage.py collectstatic --no-input"
docker exec backend sh -c "python manage.py createsuperuser"
```
