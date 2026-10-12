"""Public documentation resolves to the actual generated API contract."""

import json

import pytest
from django.contrib import admin
from django.test import RequestFactory
from drf_spectacular.generators import SchemaGenerator


@pytest.fixture(scope="module")
def api_schema():
    return SchemaGenerator().get_schema(request=None, public=True)


def test_schema_describes_playlist_editing_with_structured_examples(api_schema):
    methods = api_schema["paths"]["/api/playlists/{id}/"]
    patch = methods["patch"]
    assert "**`items`**" in patch["description"]
    assert "revision" in patch["description"]
    assert patch["requestBody"]["content"]["application/json"]["examples"]
    create = api_schema["paths"]["/api/playlists/"]["post"]
    assert len(create["requestBody"]["content"]["application/json"]["examples"]) >= 5
    assert "PATCH по-прежнему меняет только" not in json.dumps(api_schema, ensure_ascii=False)
    response_schema = methods["get"]["responses"]["200"]["content"]["application/json"]["schema"]
    component = api_schema["components"]["schemas"][response_schema["$ref"].rsplit("/", 1)[-1]]
    assert {"owner", "files", "items"} <= component["properties"].keys()


@pytest.mark.django_db
def test_legacy_docs_route_serves_dynamic_schema_and_local_redoc_assets(client):
    page = client.get("/docs/")
    assert page.status_code == 200
    assert b"/api/schema/" in page.content
    assert b"redoc@next" not in page.content
    schema = client.get("/docs/openapi-schema.yml")
    assert schema.status_code == 200
    assert b"/api/broadcast-orders/" in schema.content
    assert b"/api/playlists/{id}/" in schema.content
    guide = client.get("/api/integration-guide.md")
    assert guide.status_code == 200
    assert "**`items`**" in guide.content.decode("utf-8")


@pytest.mark.django_db
def test_original_admin_keeps_model_links_and_permission_filtering(client, super_user, user):
    client.force_login(super_user)
    response = client.get("/admin/")
    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "admin_navigation_players" not in content
    assert "admin_navigation_points" not in content
    assert '/admin/nomenclatures/stationcommandv2/' in content
    assert '<a href=""' not in content
    request = RequestFactory().get("/admin/")
    request.user = user
    assert admin.site.get_app_list(request) == []
