# RMC_REST_API WIP

### Установка и запуск

1. Клонируем проект
```console
git clone git@webgit.krasrm.com:shaleinikove/rmc_rest_api.git
```
2. Для работы проекта нужно создать файл ```.env``` в корневой директории 
со следующими переменными:
```
# django
SECRET_KEY
ALLOWED_HOSTS
DEBUG
FRONTEND_DOMEN

# healthcheck
BACKEND_HC
FRONTEND_HC

# create superuser
DJANGO_SUPERUSER_NAME
DJANGO_SUPERUSER_PASS

# minio
MINIO_STORAGE_ACCESS_KEY
MINIO_STORAGE_SECRET_KEY
MINIO_ENDPOINT
MINIO_EXTERNAL_ENDPOINT
MINIO_ROOT_USER
MINIO_ROOT_PASSWORD
MINIO_HTTPS
MINIO_REGION

# postgres
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASS
POSTGRES_HOST
POSTGRES_PORT

# clickhouse
CLICKHOUSE_DB
CLICKHOUSE_HOST
CLICKHOUSE_PORT
CLICKHOUSE_USER
CLICKHOUSE_PASSWORD
CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT

# celery
CELERY_BROKER
CELERY_SINGLETON_BACKEND
CELERY_WORKERS

# rabbitmq
RABBITMQ_USER
RABBITMQ_PASS

# frontend
NEXT_PUBLIC_API_URL
```
3. Поднимаем файловое хранилище чтобы получить 
```MINIO_STORAGE_ACCESS_KEY``` 
и ```MINIO_STORAGE_SECRET_KEY```
```console
docker compose up --build files
```
4. Открываем в браузере админ панель minio http://127.0.0.1/9001
и входим используя ```MINIO_ROOT_USER``` и ```MINIO_ROOT_PASSWORD```
5. Во вкладке ```Access Keys``` создайте новый ключ 
доступа и внесите данные в ```.env```
6. Переменная ```MINIO_REGION``` нужна для генерации ссылок на медиа файлы.
Написать в неё можно что-угодно
7. Собираем проект
```console
docker compose up --build
```
8. Добавляем пользователя RabbitMQ
```console
docker exec rabbit sh -c "rabbitmqctl add_user <RABBITMQ_USER> <RABBITMQ_PASSWORD>"
docker exec rabbit sh -c "rabbitmqctl set_permissions <RABBITMQ_USER> '.*' '.*' '.*'"
docker exec rabbit sh -c "rabbitmqctl set_user_tags <RABBITMQ_USER> administrator"
```
9. Проводим миграции, собираем статические файлы и создаем суперпользователя
```console
docker exec -it backend sh -c "python manage.py makemigrations"
docker exec -it backend sh -c "python manage.py migrate"
docker exec -it backend sh -c "python manage.py migrate --database clickhouse"
docker exec -it backend sh -c "python manage.py collectstatic --no-input"
docker exec -it backend sh -c "python manage.py createsuperuser"
```

## Принятые соглашения
```
  <тип>[(необязательный контекст)]: <описание>

  [необязательное тело]

  [необязательная(ые) сноска(и)]

  <тип>: обязательно должен быть одним из перечисленных
        feat      ✨ Добавление нового функционала
                     (MINOR в Cемантическом Версионировании)
        fix       🐛 Исправление ошибок
                     (PATCH в Cемантическом Версионировании)
        docs      📚 Только обновление документации
        style     💎 Правки по кодстайлу
                     (табы, отступы, точки, запятые и т.д.)
        refactor  📦 Правки кода без исправления ошибок или
                     добавления новых функций
        perf      🚀 Изменения направленные на улучшение
                     производительности
        test      🚨 Добавление или исправление существующих
                     тестов
        build     🛠️ Сборка проекта или изменения внешних
                     зависимостей
        ci        ⚙️ Настройка CI и работа со скриптами
        chore     ♻️ Другие изменения не модифицирующие
                     исходный код или тесты
        revert    🗑️ Откат на предыдущие коммиты
        wip       🐒 Работа в процессе
                     (промежуточный коммит)

  <описание>: должно формулироваться, как продолжение фразы:
              "В случае применения этого коммита будет...",
              начинаться с маленькой буквы, быть не длиннее 72 символов
              и не заканчиваться точкой '.'

  [необязательное тело]: должно описывать смысл изменения.
                         Не "что было поменяно" (это видно в диффе),
                         не где было поменяно (это тоже было в диффе),
                         а ПОЧЕМУ.

  [(необязательный контекст)]: может содержать номер тикета из Projeqtor
                               или быть кратким (одно, два слова)
                               описанием доменной области, которую
                               затрагивает коммит

  BREAKING CHANGE: коммит, который имеет сноску BREAKING CHANGE или
  коммит, заканчивающийся восклицательным знаком (!) после типа или
  контекста, вводящий изменение(я), нарушающие обратную совместимость
  (соответствует MAJOR в Cемантическом Версионировании).
  BREAKING CHANGE может быть частью коммита любого типа.
  ```
  Подробнее смотреть: https://habr.com/ru/articles/867012/

  пример написания сообщения коммита:

  ```
  fix: убрано логирование включенное для отладки

  ...

  feat(12345): добавлена возможность выбора роли пользователя

  ...

  refactor(auth): добавлен сервис для авторизации пользователей
  ```

### Цель проекта

### Используемые технологии

### Возможности проекта