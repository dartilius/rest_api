"""
Проверка почему конкретный объект попал в результаты поиска.
Показывает контекст вхождения запроса в поле search_text.

Использование:
    docker exec -it backend python scripts/opensearch/explain.py <uuid> апт
    docker exec -it backend python scripts/opensearch/explain.py <uuid> апт --index brands
"""

import sys
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
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
name = source.get("name", "—")
print(f"\n📄 Документ: {name[:80]}")
print(f"   UUID: {args.uuid}")
print(f"   Индекс: {args.index}\n")

# ищем вхождения в search_text
text = source.get("search_text", "")
query_lower = args.query.lower()
text_lower = text.lower()

print(f"🔍 Поиск '{args.query}' в search_text ({len(text)} символов):\n")

pos = 0
found = 0
while True:
    idx = text_lower.find(query_lower, pos)
    if idx == -1:
        break
    found += 1
    ctx_start = max(0, idx - args.context)
    ctx_end = min(len(text), idx + len(args.query) + args.context)
    context = text[ctx_start:ctx_end].replace("\n", " ")
    print(f"  [{found}] позиция {idx}: ...{context}...")
    pos = idx + 1

if found == 0:
    print(f"  ❌ Вхождений не найдено в search_text.")
    print(f"     Возможно, объект попал через fuzziness или другое поле.\n")

    # проверяем другие поля
    check_fields = ["name", "code1c", "id_rasb", "description"]
    print("  Проверка других полей:")
    for field in check_fields:
        val = str(source.get(field, "") or "").lower()
        if query_lower in val:
            print(f"    ✅ найдено в поле '{field}': {source.get(field, '')[:80]}")
else:
    print(f"\n  Итого вхождений: {found}")

print()