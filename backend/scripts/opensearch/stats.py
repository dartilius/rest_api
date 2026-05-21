"""
Статистика индексов OpenSearch.

Использование:
    docker exec -it backend python scripts/opensearch/stats.py
"""

import os

sys.path.insert(0, "/app")

import django
from dotenv import load_dotenv

load_dotenv("/app/.env")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rmc_rest_api.settings")
django.setup()

from opensearchpy import OpenSearch

client = OpenSearch("opensearch:9200")

indices = ["nomenclature", "brands"]

print("\n📊 Статистика индексов OpenSearch:\n")
for index in indices:
    try:
        count = client.count(index=index)["count"]
        info = client.indices.stats(index=index)
        size = info["indices"][index]["total"]["store"]["size_in_bytes"]
        size_mb = size / (1024 * 1024)
        print(f"  {index:<20} документов: {count:<8} размер: {size_mb:.1f} MB")
    except Exception as e:
        print(f"  {index:<20} ❌ ошибка: {e}")

print()