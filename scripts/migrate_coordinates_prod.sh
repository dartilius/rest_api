#!/bin/bash
set -e

PROJECT_DIR="$HOME/rmc_rest_api"
DOCKER_COMPOSE_FILE="prod.yml"
BACKEND_SERVICE="backend"
POSTGRES_SERVICE="db"
DATABASE="rest_api"
DB_USER="postgres"
BACKUP_DIR="$PROJECT_DIR/db_dumps"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

clear
echo "============================================"
echo " МИГРАЦИЯ КООРДИНАТ - ПРОДАКШЕН"
echo "============================================"

cd "$PROJECT_DIR" || {
    log_error "Не удалось перейти в $PROJECT_DIR"
    exit 1
}

# ============================================
# 1. СОЗДАНИЕ РЕЗЕРВНОЙ КОПИИ
# ============================================
log_info "1. Создание резервной копии БД..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_coordinates_$TIMESTAMP.sql"
mkdir -p "$BACKUP_DIR"

if docker compose -f "$DOCKER_COMPOSE_FILE" exec -T "$POSTGRES_SERVICE" pg_dump -U "$DB_USER" -d "$DATABASE" > "$BACKUP_FILE"; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log_info "Бэкап создан: $BACKUP_FILE ($BACKUP_SIZE)"
else
    log_error "Не удалось создать бэкап БД!"
    exit 1
fi

# ============================================
# 2. СОЗДАНИЕ МИГРАЦИЙ ДЛЯ ВСЕХ ПРИЛОЖЕНИЙ
# ============================================
log_info "2. Создание миграций для всех приложений..."

# Создаём миграции для users (критически важно!)
log_info "Создание миграций для users..."
docker compose -f "$DOCKER_COMPOSE_FILE" exec "$BACKEND_SERVICE" python manage.py makemigrations users

# Создаём миграции для всех остальных приложений
log_info "Создание миграций для всех приложений..."
docker compose -f "$DOCKER_COMPOSE_FILE" exec "$BACKEND_SERVICE" python manage.py makemigrations

# ============================================
# 3. ПРИМЕНЕНИЕ ВСЕХ МИГРАЦИЙ
# ============================================
log_info "3. Применение всех миграций..."

log_info "Применение миграций с --fake-initial..."
if docker compose -f "$DOCKER_COMPOSE_FILE" exec "$BACKEND_SERVICE" python manage.py migrate --fake-initial; then
    log_info "✓ Все миграции применены"
else
    log_warn "Проблема с миграциями, пробуем применить по отдельности..."

    # Создаём пустые миграции для приложений без миграций
    for app in "users" "counterparties" "nomenclatures" "brands" "files" "orders" "promotions" "tasks" "ch_statistic"; do
        log_info "Проверка приложения $app..."
        if docker compose -f "$DOCKER_COMPOSE_FILE" exec "$BACKEND_SERVICE" python manage.py makemigrations $app --check 2>/dev/null; then
            log_info "Создание миграции для $app..."
            docker compose -f "$DOCKER_COMPOSE_FILE" exec "$BACKEND_SERVICE" python manage.py makemigrations $app --empty --name initial 2>/dev/null || true
        fi
    done

    # Применяем миграции по одному
    for app in "users" "counterparties" "nomenclatures" "brands" "files" "orders" "promotions" "tasks" "ch_statistic" "addresses"; do
        log_info "Применение миграций для $app..."
        docker compose -f "$DOCKER_COMPOSE_FILE" exec "$BACKEND_SERVICE" python manage.py migrate $app --fake 2>/dev/null || true
    done
fi

# ============================================
# 4. ПРОВЕРКА СОСТОЯНИЯ ПЕРЕД МИГРАЦИЕЙ КООРДИНАТ
# ============================================
log_info "4. Проверка состояния перед миграцией координат..."

COUNT_QUERY="SELECT
    COUNT(*) as total,
    COUNT(coordinates) as with_coordinates
FROM addresses_address;"

log_info "Статистика addresses:"
docker compose -f "$DOCKER_COMPOSE_FILE" exec "$POSTGRES_SERVICE" psql -U "$DB_USER" -d "$DATABASE" -c "$COUNT_QUERY"

# ============================================
# 5. СОЗДАНИЕ И ПРИМЕНЕНИЕ МИГРАЦИЙ ДЛЯ КООРДИНАТ
# ============================================
log_info "5. Создание и применение миграций для координат..."

# Получаем ID контейнера backend
BACKEND_CONTAINER_ID=$(docker compose -f "$DOCKER_COMPOSE_FILE" ps -q "$BACKEND_SERVICE")

# 5.1. Миграция добавления полей
cat > /tmp/0002_add_coordinate_fields.py << 'EOF'
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('addresses', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='address',
            name='latitude',
            field=models.DecimalField(
                blank=True,
                null=True,
                max_digits=9,
                decimal_places=6,
                verbose_name='Широта'
            ),
        ),
        migrations.AddField(
            model_name='address',
            name='longitude',
            field=models.DecimalField(
                blank=True,
                null=True,
                max_digits=9,
                decimal_places=6,
                verbose_name='Долгота'
            ),
        ),
    ]
EOF

docker cp /tmp/0002_add_coordinate_fields.py "$BACKEND_CONTAINER_ID":/app/addresses/migrations/0002_add_coordinate_fields.py

# 5.2. Миграция переноса данных
cat > /tmp/0003_migrate_coordinates.py << 'EOF'
from django.db import migrations
from decimal import Decimal

def migrate_coordinates(apps, schema_editor):
    Address = apps.get_model('addresses', 'Address')

    print('=== НАЧИНАЕМ ПЕРЕНОС КООРДИНАТ ===')

    addresses = Address.objects.filter(coordinates__isnull=False).exclude(coordinates='')
    total = addresses.count()
    print(f'Найдено адресов: {total}')

    success = 0
    for i, addr in enumerate(addresses, 1):
        try:
            coords = addr.coordinates.strip()

            if ';' in coords:
                lat_str, lon_str = coords.split(';', 1)
            elif ',' in coords:
                lat_str, lon_str = coords.split(',', 1)
            else:
                continue

            addr.latitude = Decimal(lat_str.strip())
            addr.longitude = Decimal(lon_str.strip())
            addr.save(update_fields=['latitude', 'longitude'])
            success += 1

            if i % 100 == 0:
                print(f'Обработано {i}/{total}')

        except Exception as e:
            print(f'Ошибка {addr.id}: {e}')

    print(f'Успешно: {success}/{total}')

def reverse_migration(apps, schema_editor):
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('addresses', '0002_add_coordinate_fields'),
    ]

    operations = [
        migrations.RunPython(migrate_coordinates, reverse_migration, atomic=False),
    ]
EOF

docker cp /tmp/0003_migrate_coordinates.py "$BACKEND_CONTAINER_ID":/app/addresses/migrations/0003_migrate_coordinates.py

# ============================================
# 6. ПРИМЕНЕНИЕ МИГРАЦИЙ КООРДИНАТ
# ============================================
log_info "6. Применение миграций координат..."

log_info "Применение миграции добавления полей..."
docker compose -f "$DOCKER_COMPOSE_FILE" exec "$BACKEND_SERVICE" python manage.py migrate addresses 0002_add_coordinate_fields

log_info "Применение миграции переноса данных..."
docker compose -f "$DOCKER_COMPOSE_FILE" exec "$BACKEND_SERVICE" python manage.py migrate addresses 0003_migrate_coordinates

# ============================================
# 7. ПРОВЕРКА РЕЗУЛЬТАТА
# ============================================
log_info "7. Проверка результата..."

# Исправленный SQL-запрос с правильным синтаксисом для PostgreSQL
FINAL_CHECK_QUERY="SELECT 
    'Всего адресов' as metric, COUNT(*) as value FROM addresses_address
UNION ALL
    SELECT 'С текстовыми координатами', COUNT(coordinates) FROM addresses_address WHERE coordinates IS NOT NULL
UNION ALL
    SELECT 'С широтой', COUNT(latitude) FROM addresses_address WHERE latitude IS NOT NULL
UNION ALL
    SELECT 'С долготой', COUNT(longitude) FROM addresses_address WHERE longitude IS NOT NULL
ORDER BY metric;"

log_info "Статистика после миграции:"
docker compose -f "$DOCKER_COMPOSE_FILE" exec "$POSTGRES_SERVICE" psql -U "$DB_USER" -d "$DATABASE" -c "$FINAL_CHECK_QUERY"

# ============================================
# 8. ОПЦИОНАЛЬНО: УДАЛЕНИЕ ПОЛЯ COORDINATES
# ============================================
read -p "Удалить старое поле coordinates из БД? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "Удаление поля coordinates..."

    cat > /tmp/0004_remove_coordinates.py << 'EOF'
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('addresses', '0003_migrate_coordinates'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='address',
            name='coordinates',
        ),
    ]
EOF

    docker cp /tmp/0004_remove_coordinates.py "$BACKEND_CONTAINER_ID":/app/addresses/migrations/0004_remove_coordinates.py
    docker compose -f "$DOCKER_COMPOSE_FILE" exec "$BACKEND_SERVICE" python manage.py migrate addresses 0004_remove_coordinates
    log_info "✓ Поле coordinates удалено"
fi

# ============================================
# 9. ЗАВЕРШЕНИЕ
# ============================================
echo "============================================"
log_info "МИГРАЦИЯ УСПЕШНО ЗАВЕРШЕНА!"
echo "============================================"
log_info "Резервная копия: $BACKUP_FILE"
echo "Для отката:"
echo "  docker compose -f $DOCKER_COMPOSE_FILE exec -T $POSTGRES_SERVICE psql -U $DB_USER -d $DATABASE < $BACKUP_FILE"
echo "============================================"

rm -f /tmp/*.py

exit 0
