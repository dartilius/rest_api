"""
Переиндексация данных в OpenSearch.

Использование:
    docker exec -it backend python scripts/opensearch/reindex.py
    docker exec -it backend python scripts/opensearch/reindex.py --index nomenclature
    docker exec -it backend python scripts/opensearch/reindex.py --index brands
"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rmc_rest_api.settings")
django.setup()

import argparse

parser = argparse.ArgumentParser(description="Переиндексация OpenSearch")
parser.add_argument("--index", choices=["nomenclature", "brands", "all"], default="all")
args = parser.parse_args()

def reindex(document_class, label):
    doc = document_class()
    qs = doc.get_queryset()
    total = qs.count()
    print(f"  Индексируем {label}: {total} объектов...", end=" ", flush=True)
    try:
        result = doc.update(qs, action="index")
        print(f"✅ готово ({result[0]} успешно, {len(result[1])} ошибок)")
    except Exception as e:
        print(f"❌ ошибка: {e}")

print("\n🔄 Переиндексация OpenSearch:\n")

if args.index in ("nomenclature", "all"):
    from nomenclatures.documents import NomenclatureDocument
    reindex(NomenclatureDocument, "nomenclature")

if args.index in ("brands", "all"):
    from brands.documents import BrandDocument
    reindex(BrandDocument, "brands")

print()