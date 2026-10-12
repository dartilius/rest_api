from django.apps import apps
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.questioner import MigrationQuestioner
from django.db.migrations.state import ProjectState


def test_address_state_does_not_recreate_region_uniqueness():
    """Deploying unrelated features must preserve legacy regions and their links."""
    loader = MigrationLoader(None)
    migrated = loader.project_state()
    current = ProjectState.from_apps(apps)

    assert not migrated.models["addresses", "region"].options.get("unique_together")
    assert not current.models["addresses", "region"].options.get("unique_together")

    changes = MigrationAutodetector(
        migrated, current, MigrationQuestioner()
    ).changes(graph=loader.graph, trim_to_apps={"addresses"})

    assert "addresses" not in changes
