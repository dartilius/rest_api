from django_opensearch_dsl import Document, fields
from django_opensearch_dsl.registries import registry

from brands.models import Brand


@registry.register_document
class BrandDocument(Document):
    name = fields.TextField(
        attr="name",
        fields={
            "autocomplete": fields.TextField(analyzer="edge_ngram_analyzer"),
            "keyword": fields.KeywordField(),
        },
    )
    description = fields.TextField(
        attr="description",
        fields={
            "autocomplete": fields.TextField(analyzer="edge_ngram_analyzer"),
        },
    )
    code1c = fields.KeywordField(attr="code1c")
    slug = fields.KeywordField(attr="slug")
    is_deleted = fields.BooleanField(attr="is_deleted")

    class Index:
        name = "brands"
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": {
                "filter": {
                    "edge_ngram_filter": {
                        "type": "edge_ngram",
                        "min_gram": 2,
                        "max_gram": 20,
                    }
                },
                "analyzer": {
                    "edge_ngram_analyzer": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": ["lowercase", "edge_ngram_filter"],
                    }
                },
            },
        }

    class Django:
        model = Brand
        queryset_pagination = 500
