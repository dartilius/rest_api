# RMC_REST_API WIP

### Установка и запуск

1. Клонируем проект

```console
git clone git@webgit.krasrm.com:shaleinikove/rmc_rest_api.git
```

2. Для работы проекта нужно создать файл `.env` в корневой директории
   со следующими переменными:

```
# django
SECRET_KEY
ALLOWED_HOSTS
DEBUG

# healthcheck
BACKEND_HC

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

```

3. Поднимаем файловое хранилище чтобы получить
   `MINIO_STORAGE_ACCESS_KEY`
   и `MINIO_STORAGE_SECRET_KEY`

```console
docker compose up --build files
```

4. Открываем в браузере админ панель minio http://127.0.0.1/9001
   и входим используя `MINIO_ROOT_USER` и `MINIO_ROOT_PASSWORD`
5. Во вкладке `Access Keys` создайте новый ключ
   доступа и внесите данные в `.env`
6. Переменная `MINIO_REGION` нужна для генерации ссылок на медиа файлы.
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

## Локальный запуск в Kubernetes (k3d)

Этот способ запуска предназначен для локальной проверки разделения Django и
NestJS. Он не заменяет существующий `docker compose` выше и не удаляет его.
Стенд поднимает PostgreSQL, Django API, Nest API и административную панель
`k8s-view`. MinIO в локальный Kubernetes-стенд пока не включён: импорт базы
переносит только PostgreSQL-данные, без объектов из MinIO.

### Предварительные требования

- Docker Desktop с работающим Linux Engine;
- `kubectl`, `k3d` и Helm;
- локальный кластер `rmc-local` с ingress-nginx, опубликованным на порту
  `8080`.

Проверка подключения к кластеру:

```powershell
kubectl get nodes
kubectl get pods -A
```

Полный запуск или повторный деплой из корня репозитория:

```powershell
.\scripts\k8s\deploy-local.ps1
```

Скрипт создаёт локальные секреты и RSA-ключи вне Git, собирает образы Django и
Nest, применяет манифесты, выполняет миграции Django, создаёт тестового
пользователя и выдаёт NestJS доступ только на чтение к исходным таблицам.

> При повторном запуске создаётся новая пара JWT RSA-ключей. Выпущенные ранее
> access-токены после этого становятся недействительными — выполните логин
> заново.

### Административная панель Kubernetes

`k8s-view` доступен только через локальный port-forward, а не через публичный
Ingress. Откройте отдельное окно PowerShell и оставьте команду работающей:

```powershell
kubectl port-forward --address 127.0.0.1 -n monitoring svc/k8s-view 8081:80
```

После этого панель открывается на `http://127.0.0.1:8081`. В локальном k3d
она имеет полные права на кластер: просмотр логов, exec, restart, scale и
изменение YAML. Не переносите эти права в production.

### Порты и адреса

| Режим | Адрес / порт | Назначение |
| --- | --- | --- |
| k3d | `http://localhost:8080/site-api/docs` | Swagger / документация NestJS API |
| k3d | `http://localhost:8080/site-api/v1/...` | NestJS API сайта; например `/brands/` |
| k3d | `http://localhost:8080/auth/...` | Django JWT и legacy-refresh авторизация |
| k3d | `http://localhost:8080/api/...` | Django API и обмен с 1С |
| k3d | `http://127.0.0.1:8081` | `k8s-view`; работает, пока запущен port-forward |
| k3d | `5432` внутри кластера | PostgreSQL `postgres.rmc.svc.cluster.local:5432`; на ноутбук не опубликован |
| Docker Compose | `http://localhost:80` | Nginx gateway текущего Compose-запуска |
| Docker Compose | `8000` | Django/gunicorn напрямую |
| Docker Compose | `5432` | PostgreSQL |
| Docker Compose | `9000` / `9001` | MinIO API / административная панель |
| Docker Compose | `8123` / `8888` | ClickHouse HTTP / native client |
| Docker Compose | `9200` | OpenSearch HTTP API |
| Docker Compose | `5672` / `15672` | RabbitMQ AMQP / административная панель |
| Docker Compose | `5555` | Flower, мониторинг Celery |
| Docker Compose | `7777` | TileServer |
| Docker Compose | `15432` | pgAdmin |

`http://localhost:8080/` намеренно возвращает `404`: корневой маршрут в
Ingress не назначен ни одному сервису. Используйте маршруты из таблицы выше.

## Полный чистый Kubernetes-стенд

`deploy-local.ps1` выше оставлен для минимальной JWT-лаборатории. Для полного
локального запуска без Docker Compose используйте новый чистый кластер
`rmc-local` и команду:

```powershell
.\scripts\k8s\deploy-full-local.ps1
```

Если кластера ещё нет или его нужно полностью очистить вместе с локальными
Kubernetes PVC, используйте вместо этого:

```powershell
.\scripts\k8s\reset-full-local.ps1
```

В отличие от минимальной JWT-лаборатории, полный стенд назначает `/` на Django
admin, поэтому прежнее пояснение про `404` на корневом адресе к нему не
относится.

Она запускает PostgreSQL, MinIO, RabbitMQ, Redis, ClickHouse, OpenSearch,
Django, Nest, Celery worker/beat, Nginx gateway, Flower, pgAdmin и `k8s-view`.
База, buckets и очереди создаются пустыми; старые данные Docker Compose не
копируются. Docker Desktop необходим только потому, что k3d создаёт Kubernetes
ноды в контейнерах — `docker compose up` запускать не требуется.

Состояние полного стенда:

```powershell
kubectl get pods -A
kubectl get jobs -n rmc
```

Полезные адреса:

| Сервис | Адрес или команда |
| --- | --- |
| Django admin | `http://localhost:8080/` |
| Nest Swagger | `http://localhost:8080/site-api/docs` |
| Nest API | `http://localhost:8080/site-api/v1/brands/` |
| Django auth | `http://localhost:8080/auth/jwt/create/` |
| Flower | `kubectl port-forward -n monitoring svc/flower-ui 5555:5555` → `http://127.0.0.1:5555` |
| pgAdmin | `kubectl port-forward -n monitoring svc/pgadmin 15432:80` → `http://127.0.0.1:15432` |
| k8s-view | `kubectl port-forward -n monitoring svc/k8s-view 8081:80` → `http://127.0.0.1:8081` |
| MinIO console | `kubectl port-forward -n rmc svc/minio 9001:9001` → `http://127.0.0.1:9001` |

Локальный Django superuser: `admin@local.test` / `LocalAdmin!2026`.
Локальный pgAdmin: `admin@example.com` / `LocalAdmin!2026`.

TileServer по умолчанию отключён, так как файл
`siberian-fed-district.mbtiles` не хранится в репозитории. После получения
файла его нужно смонтировать в `/data` pod'а TileServer и изменить `replicas`
у Deployment `tileserver` с `0` на `1`.

Локально используется закреплённый community-образ MinIO, поскольку прежний
официальный образ из Docker Hub стал недоступен для загрузки. Перед production
нужно заменить его на образ, сохранённый в корпоративном registry.

## Серверный Kubernetes: запуск и Django-команды

Этот блок для одного корпоративного сервера с k3s. Манифесты
`deploy/k8s/local/` — только лаборатория: в них локальные образы,
`imagePullPolicy: Never`, тестовые учётные данные и порты k3d. Не применяйте
их на сервере без отдельной production-настройки. Для production нужны образы
из корпоративного registry, Secrets вне Git, PersistentVolume на выделенных
дисках и проверенная внешняя резервная копия.

### Вход на сервер и в кластер

Подключение по SSH:

```bash
ssh <admin>@<server-ip>
sudo kubectl get nodes
sudo kubectl get pods -A
```

Пока для вашей учётной записи не сделан отдельный Kubernetes RBAC, выполняйте
команды через `sudo kubectl`. Файл `/etc/rancher/k3s/k3s.yaml` даёт полный
доступ к кластеру. Не копируйте его на ноутбук без защиты и без замены адреса
API-сервера на серверный IP.

Проверка нужного контекста и RMC:

```bash
sudo kubectl config current-context
sudo kubectl -n rmc get deploy,statefulset,pod,job
sudo kubectl -n monitoring get pod
```

### Первое развёртывание на сервере

1. Установите k3s с отключённым Traefik и установите ingress-nginx.
2. Соберите Django и Nest образы, отправьте в корпоративный registry с версией:
   `registry.company.local/rmc/django:<git-sha>` и
   `registry.company.local/rmc/nest:<git-sha>`.
3. Создайте namespaces `rmc`, `data`, `monitoring` и Secrets вне Git.
4. Примените server manifests в порядке: data-сервисы, bootstrap Jobs, Django,
   Nest, Celery, gateway/Ingress, monitoring.
5. Дождитесь bootstrap Jobs и готовности API:

```bash
sudo kubectl -n rmc wait --for=condition=complete job/django-bootstrap --timeout=10m
sudo kubectl -n rmc get pods -w
sudo kubectl -n rmc rollout status deployment/django-api --timeout=5m
sudo kubectl -n rmc rollout status deployment/nest-api --timeout=5m
```

`django-bootstrap` должен запускать `migrate --noinput`, миграции ClickHouse,
`collectstatic` и создание первого администратора. `makemigrations` на сервере
не запускают: миграции создаются, проверяются и попадают в Git до деплоя.

### Как выполнять Django-команды в Kubernetes

Сначала смотрите состояние и логи:

```bash
sudo kubectl -n rmc logs deploy/django-api --tail=200
sudo kubectl -n rmc logs deploy/celery-worker --tail=200
sudo kubectl -n rmc exec -it deploy/django-api -- python manage.py check
```

Основные команды:

```bash
# Интерактивная оболочка Django.
sudo kubectl -n rmc exec -it deploy/django-api -- python manage.py shell

# Создать администратора вручную, если bootstrap его не создавал.
sudo kubectl -n rmc exec -it deploy/django-api -- python manage.py createsuperuser

# Миграции — только после бэкапа PostgreSQL и в окно деплоя.
sudo kubectl -n rmc exec -it deploy/django-api -- python manage.py migrate --noinput
sudo kubectl -n rmc exec -it deploy/django-api -- python manage.py migrate --database clickhouse --noinput

# Статика после изменения Django admin или других статических файлов.
sudo kubectl -n rmc exec -it deploy/django-api -- python manage.py collectstatic --noinput
```

После нового образа обновляйте только нужный Deployment и ждите rollout:

```bash
sudo kubectl -n rmc set image deployment/django-api \
  django-api=registry.company.local/rmc/django:<version>
sudo kubectl -n rmc rollout status deployment/django-api --timeout=5m
```

### Панели и диагностика на сервере

Не публикуйте pgAdmin, Flower, MinIO Console и k8s-view через публичный
Ingress. Заходите через SSH-туннель с ноутбука:

```bash
# Выполнить на ноутбуке; затем открыть http://127.0.0.1:8081.
ssh -L 8081:127.0.0.1:8081 <admin>@<server-ip>
```

На сервере в отдельной SSH-сессии поднимите нужный port-forward:

```bash
sudo kubectl -n monitoring port-forward --address 127.0.0.1 svc/k8s-view 8081:80
sudo kubectl -n monitoring port-forward --address 127.0.0.1 svc/flower-ui 5555:5555
sudo kubectl -n rmc port-forward --address 127.0.0.1 svc/minio 9001:9001
```

Перед ручной миграцией убедитесь, что есть свежий бэкап PostgreSQL и понятный
план отката. Тумба-юмба думать: `migrate` меняет данные, её нельзя выполнять
просто для проверки.
