# Скрипты для работы с OpenSearch

Набор утилит для отладки и обслуживания OpenSearch индексов проекта RMC.

Все скрипты запускаются внутри контейнера `backend`:

```bash
docker exec -it backend python scripts_opensearch/<script>.py [аргументы]
```

---

## stats.py — статистика индексов

Показывает количество документов и размер каждого индекса.

```bash
docker exec -it backend python scripts_opensearch/stats.py
```

**Пример вывода:**
```
📊 Статистика индексов OpenSearch:

  nomenclature         документов: 4238     размер: 12.3 MB
  brands               документов: 145      размер: 0.4 MB
```

---

## reindex.py — переиндексация

Загружает данные из БД и записывает их в OpenSearch. Нужно запускать после изменений в `documents.py` или при расхождении данных.

```bash
# переиндексировать всё
docker exec -it backend python scripts_opensearch/reindex.py

# только номенклатуры
docker exec -it backend python scripts_opensearch/reindex.py --index nomenclature

# только бренды
docker exec -it backend python scripts_opensearch/reindex.py --index brands
```

**Аргументы:**

| Аргумент | Значения | По умолчанию |
|---|---|---|
| `--index` | `nomenclature`, `brands`, `all` | `all` |

---

## search.py — тестовый поиск

Выполняет поиск по индексу и выводит результаты со score.

```bash
docker exec -it backend python scripts_opensearch/search.py <запрос>
docker exec -it backend python scripts_opensearch/search.py <запрос> --size 20
docker exec -it backend python scripts_opensearch/search.py <запрос> --index brands
```

**Аргументы:**

| Аргумент | Значения | По умолчанию |
|---|---|---|
| `query` | строка поиска | обязательный |
| `--size` | число | `10` |
| `--index` | `nomenclatures`, `brands` | `nomenclatures` |

**Примеры:**
```bash
# поиск номенклатур
docker exec -it backend python scripts_opensearch/search.py апт
docker exec -it backend python scripts_opensearch/search.py "торговый центр" --size 20

# поиск брендов
docker exec -it backend python scripts_opensearch/search.py мег --index brands
```

**Пример вывода:**
```
🔍 Поиск: 'апт' | индекс: nomenclatures | size: 10

Найдено: 37

    1. score=7.19 | Дешевая аптека Абакан, ООО, р. Хакасия, г. Абакан...
    2. score=7.16 | Гармония здоровья Норильск, ООО, Красноярский кр....
    3. score=7.15 | Гармония здоровья Норильск, ООО, Красноярский кр....
```

---

## explain.py — почему объект попал в результаты

Показывает в каких конкретно полях индекса найдено вхождение запроса.

```bash
docker exec -it backend python scripts_opensearch/explain.py <uuid> <запрос>
docker exec -it backend python scripts_opensearch/explain.py <uuid> <запрос> --index brands
docker exec -it backend python scripts_opensearch/explain.py <uuid> <запрос> --context 80
```

**Аргументы:**

| Аргумент | Значения | По умолчанию |
|---|---|---|
| `uuid` | UUID документа | обязательный |
| `query` | строка поиска | обязательный |
| `--index` | `nomenclature`, `brands` | `nomenclature` |
| `--context` | символов вокруг вхождения | `40` |

**Пример:**
```bash
docker exec -it backend python scripts_opensearch/explain.py \
  5fde8f0f-b30f-463f-8f4a-d39fc9484c4f апт
```

**Пример вывода:**
```
📄 ДМ трейдинг, ООО, Красноярский кр., г. Красноярск, ул. Тельмана, 30г
   UUID : 5fde8f0f-b30f-463f-8f4a-d39fc9484c4f
   Индекс: nomenclature
   Поиск : 'апт'

✅ Найдено в полях (1 вхождений):

  [tenants_data[19].tenant.description]
    ...Вет аптека, Мост, Квант...

📦 search_text (1 вхождений):

    ...Вет аптека, Мост, Квант Транс Логик Фарммед...
```

Если вхождение найдено только в `search_text` но не в конкретных полях — объект скорее всего попал через fuzziness (нечёткое совпадение токенов).

---

## tenants.py — арендаторы номенклатуры

Показывает арендаторов из OpenSearch индекса для конкретной номенклатуры. Удобно использовать вместе с `explain.py` чтобы понять через какого арендатора объект попал в выдачу.

```bash
# все арендаторы
docker exec -it backend python scripts_opensearch/tenants.py <uuid>

# конкретный арендатор по индексу
docker exec -it backend python scripts_opensearch/tenants.py <uuid> --idx 19

# найти арендаторов у которых есть слово
docker exec -it backend python scripts_opensearch/tenants.py <uuid> --find апт
```

**Аргументы:**

| Аргумент | Значения | По умолчанию |
|---|---|---|
| `uuid` | UUID номенклатуры | обязательный |
| `--idx` | индекс арендатора (0-based) | — |
| `--find` | строка для поиска среди арендаторов | — |

**Пример:**
```bash
docker exec -it backend python scripts_opensearch/tenants.py \
  5fde8f0f-b30f-463f-8f4a-d39fc9484c4f --find апт
```

**Пример вывода:**
```
📄 ДМ трейдинг, ООО, г. Красноярск, ул. Тельмана, 30г
   UUID: 5fde8f0f-b30f-463f-8f4a-d39fc9484c4f
   Арендаторов в индексе: 24

  [19] floor=1 | atm=False
       tenant.first_name  :
       tenant.last_name   :
       tenant.description : Вет аптека, Мост, Квант Транс Логик Фарммед
       tenant.keyword     : Т2 Мобайл
       tenant.additional  :
       brand.name         : Т2
       brand.code1c       : 000001535
```

---

## Типичный workflow отладки

**Шаг 1.** Смотришь что нашёл поиск:
```bash
docker exec -it backend python scripts_opensearch/search.py апт --size 20
```

**Шаг 2.** Берёшь подозрительный UUID и смотришь в каком поле найдено:
```bash
docker exec -it backend python scripts_opensearch/explain.py <uuid> апт
```

**Шаг 3.** Если вхождение в `tenants_data[N]` — смотришь кто этот арендатор:
```bash
docker exec -it backend python scripts_opensearch/tenants.py <uuid> --idx N
# или сразу
docker exec -it backend python scripts_opensearch/tenants.py <uuid> --find апт
```

**Шаг 4.** После изменений в `documents.py` — переиндексируешь:
```bash
docker exec -it backend python scripts_opensearch/reindex.py --index nomenclature
```