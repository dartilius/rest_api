"""
Проверка поиска по OpenSearch.

Использование:
    docker exec -it backend python scripts/opensearch/search.py апт
    docker exec -it backend python scripts/opensearch/search.py "торговый центр" --size 10
    docker exec -it backend python scripts/opensearch/search.py мег --index brands
"""

import sys
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rmc_rest_api.settings")
django.setup()

import argparse
from nomenclatures.documents import NomenclatureDocument
from brands.documents import BrandDocument

parser = argparse.ArgumentParser(description="Поиск по OpenSearch")
parser.add_argument("query", help="Поисковый запрос")
parser.add_argument("--size", type=int, default=10, help="Кол-во результатов (default: 10)")
parser.add_argument("--index", choices=["nomenclatures", "brands"], default="nomenclatures")
args = parser.parse_args()

query = args.query.strip()
size = args.size
index = args.index

print(f"\n🔍 Поиск: '{query}' | индекс: {index} | size: {size}\n")

if index == "nomenclatures":
    s = NomenclatureDocument.search()
    s = s.filter("term", is_active=True)
    s = s.query("match", search_text=query)
else:
    s = BrandDocument.search()
    s = s.filter("term", is_deleted=False)
    s = s.query("match", name=query)

s = s.extra(size=size)
response = s.execute()
total = response.hits.total["value"]

print(f"Найдено: {total}\n")
for i, hit in enumerate(response, 1):
    name = getattr(hit, "name", "—")[:70]
    print(f"  {i:>3}. score={hit.meta.score:.2f} | {name}")

print()