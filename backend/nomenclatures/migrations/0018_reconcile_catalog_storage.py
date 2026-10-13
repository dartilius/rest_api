"""Complete storage omitted by the production-only state migration 0011.

Existing catalog values and video records are preserved. Reversal deliberately
keeps this storage: it predates this reconciliation on production databases.
"""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("nomenclatures", "0017_station_command_superseded_state")]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    """
                    SET LOCAL lock_timeout = '2s';
                    ALTER TABLE "nomenclature" ADD COLUMN IF NOT EXISTS
                        "old_catalog_slug" varchar(512) DEFAULT '' NOT NULL;
                    ALTER TABLE "nomenclature" ALTER COLUMN "old_catalog_slug" SET DEFAULT '';
                    DO $$
                    BEGIN
                        IF to_regclass('nomenclature_videos') IS NULL THEN
                            CREATE TABLE "nomenclature_videos" (
                                "id" uuid NOT NULL PRIMARY KEY,
                                "source" varchar(100) NOT NULL,
                                "type" varchar(31) NOT NULL,
                                "created" timestamp with time zone NOT NULL,
                                "hash" varchar(64) NOT NULL,
                                "nomenclature_id" uuid NOT NULL,
                                CONSTRAINT "nomenclature_videos_station_fk"
                                    FOREIGN KEY ("nomenclature_id") REFERENCES "nomenclature" ("id")
                                    DEFERRABLE INITIALLY DEFERRED
                            );
                            -- The table is new and empty; no concurrent build needed.
                            CREATE INDEX "nomenclature_videos_hash_idx" ON "nomenclature_videos" ("hash");
                            CREATE INDEX "nomenclature_videos_hash_like_idx" ON "nomenclature_videos" ("hash" varchar_pattern_ops);
                            CREATE INDEX "nomenclature_videos_station_idx" ON "nomenclature_videos" ("nomenclature_id");
                        END IF;
                    END $$;
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.AlterField(
                    model_name="nomenclature", name="old_catalog_slug",
                    field=models.SlugField(
                        max_length=512, blank=True, default="", db_default="", db_index=True,
                        verbose_name="Старый URL slug (каталог)",
                        help_text="Slug из старой версии каталога для редиректов",
                    ),
                ),
            ],
        ),
    ]
