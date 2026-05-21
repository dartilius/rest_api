"""
Проверка почему конкретный объект попал в результаты поиска.
Показывает в каких конкретно полях найдено вхождение запроса.

Использование:
    docker exec -it backend python scripts_opensearch/explain.py <uuid> апт
    docker exec -it backend python scripts_opensearch/explain.py <uuid> апт --index brands
"""

import sys
import os

sys.path.insert(0, '/app')

import django
from dotenv import load_dotenv

load_dotenv('/app/.env')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rmc_rest_api.settings")
django.setup()

import argparse
from opensearchpy import OpenSearch

parser = argparse.ArgumentParser(description="Почему объект попал в результаты")
parser.add_argument("uuid", help="UUID документа")
parser.add_argument("query", help="Поисковый запрос")
parser.add_argument("--index", choices=["nomenclature", "brands"], default="nomenclature")
parser.add_argument("--context", type=int, default=40, help="Символов контекста вокруг вхождения")
args = parser.parse_args()

client = OpenSearch("opensearch:9200")

try:
    doc = client.get(index=args.index, id=args.uuid)
except Exception as e:
    print(f"❌ Документ не найден: {e}")
    sys.exit(1)

source = doc["_source"]
query_lower = args.query.lower()
ctx = args.context


def find_in_text(text, label, results):
    """Ищет вхождения query в тексте, добавляет в results."""
    if not text:
        return
    text_str = str(text)
    text_lower = text_str.lower()
    pos = 0
    while True:
        idx = text_lower.find(query_lower, pos)
        if idx == -1:
            break
        ctx_start = max(0, idx - ctx)
        ctx_end = min(len(text_str), idx + len(args.query) + ctx)
        snippet = text_str[ctx_start:ctx_end].replace("\n", " ").strip()
        results.append((label, snippet))
        pos = idx + 1


def scan_object(obj, prefix, results):
    """Рекурсивно сканирует объект (dict/list/str) и ищет вхождения."""
    if isinstance(obj, str):
        find_in_text(obj, prefix, results)
    elif isinstance(obj, dict):
        for key, val in obj.items():
            scan_object(val, f"{prefix}.{key}", results)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            scan_object(item, f"{prefix}[{i}]", results)


# Поля для проверки (кроме search_text — оно агрегированное)
SKIP_FIELDS = {"search_text"}

name = source.get("name", "—")
print(f"\n📄 {name[:80]}")
print(f"   UUID : {args.uuid}")
print(f"   Индекс: {args.index}")
print(f"   Поиск : '{args.query}'\n")

all_results = []

for field, value in source.items():
    if field in SKIP_FIELDS:
        continue
    scan_object(value, field, all_results)

# отдельно проверяем search_text целиком
search_text = source.get("search_text", "")
st_results = []
find_in_text(search_text, "search_text", st_results)

if all_results:
    print(f"✅ Найдено в полях ({len(all_results)} вхождений):\n")
    for label, snippet in all_results:
        print(f"  [{label}]")
        print(f"    ...{snippet}...")
        print()
else:
    print("❌ В конкретных полях не найдено.\n")

if st_results:
    print(f"📦 search_text ({len(st_results)} вхождений):\n")
    for label, snippet in st_results:
        print(f"    ...{snippet}...")
    print()
elif not all_results:
    print("   Возможно, объект попал через fuzziness (похожие токены).")

print()