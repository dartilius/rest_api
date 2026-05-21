"""
Просмотр арендаторов номенклатуры из OpenSearch индекса.

Использование:
    docker exec -it backend python scripts_opensearch/tenants.py <uuid>
    docker exec -it backend python scripts_opensearch/tenants.py <uuid> --find апт
    docker exec -it backend python scripts_opensearch/tenants.py <uuid> --idx 19
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

parser = argparse.ArgumentParser(description="Арендаторы номенклатуры из OpenSearch")
parser.add_argument("uuid", help="UUID номенклатуры")
parser.add_argument("--find", help="Найти арендаторов у которых есть это слово", default=None)
parser.add_argument("--idx", type=int, help="Показать конкретного арендатора по индексу", default=None)
args = parser.parse_args()

client = OpenSearch("opensearch:9200")

try:
    doc = client.get(index="nomenclature", id=args.uuid)
except Exception as e:
    print(f"❌ Документ не найден: {e}")
    sys.exit(1)

source = doc["_source"]
tenants = source.get("tenants_data", [])

print(f"\n📄 {source.get('name', '—')[:80]}")
print(f"   UUID: {args.uuid}")
print(f"   Арендаторов в индексе: {len(tenants)}\n")


def print_tenant(i, t):
    tenant = t.get("tenant") or {}
    brand = t.get("brand") or {}
    print(f"  [{i}] floor={t.get('floor') or '—'} | atm={t.get('atm')}")
    print(f"       tenant.first_name  : {tenant.get('first_name', '')}")
    print(f"       tenant.last_name   : {tenant.get('last_name', '')}")
    print(f"       tenant.description : {tenant.get('description', '')}")
    print(f"       tenant.keyword     : {tenant.get('keyword', '')}")
    print(f"       tenant.additional  : {tenant.get('additional_name', '')}")
    print(f"       brand.name         : {brand.get('name', '—')}")
    print(f"       brand.code1c       : {brand.get('code1c', '—')}")
    print()


if args.idx is not None:
    if args.idx >= len(tenants):
        print(f"❌ Индекс {args.idx} выходит за пределы (всего {len(tenants)})")
        sys.exit(1)
    print_tenant(args.idx, tenants[args.idx])

elif args.find:
    query = args.find.lower()
    found = 0
    for i, t in enumerate(tenants):
        # собираем все строковые значения арендатора
        all_text = " ".join([
            str(v) for v in (t.get("tenant") or {}).values()
            if isinstance(v, str)
        ] + [
            str(v) for v in (t.get("brand") or {}).values()
            if isinstance(v, str)
        ] + [t.get("floor") or ""]).lower()

        if query in all_text:
            found += 1
            print_tenant(i, t)

    if found == 0:
        print(f"❌ Арендаторов с '{args.find}' не найдено.")

else:
    # выводим всех
    for i, t in enumerate(tenants):
        print_tenant(i, t)