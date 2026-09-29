from django.contrib.postgres.indexes import BTreeIndex
from django.core.validators import RegexValidator
from django.db import migrations, models
import django.db.models.deletion


SCHEMA_SQL = """
SET lock_timeout = '2s';

ALTER TABLE addresses_country
    ADD COLUMN IF NOT EXISTS iso_code varchar(2) NULL,
    ADD COLUMN IF NOT EXISTS iso3_code varchar(3) NULL;
ALTER TABLE addresses_region
    ADD COLUMN IF NOT EXISTS country_id uuid NULL;

UPDATE addresses_region AS region
SET country_id = district.country_id
FROM addresses_federal_district AS district
WHERE region.country_id IS NULL AND region.federal_district_id = district.id;

DO $$
DECLARE only_country uuid;
BEGIN
    SELECT id INTO only_country FROM addresses_country LIMIT 1;
    IF (SELECT count(*) FROM addresses_country) = 1 THEN
        UPDATE addresses_region SET country_id = only_country WHERE country_id IS NULL;
    END IF;
    IF EXISTS (SELECT 1 FROM addresses_region WHERE country_id IS NULL) THEN
        RAISE EXCEPTION 'addresses_region contains rows without a determinable country';
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'addresses_region_country_id_fk'
    ) THEN
        ALTER TABLE addresses_region
            ADD CONSTRAINT addresses_region_country_id_fk
            FOREIGN KEY (country_id) REFERENCES addresses_country(id) NOT VALID;
    END IF;
END $$;
ALTER TABLE addresses_region VALIDATE CONSTRAINT addresses_region_country_id_fk;
ALTER TABLE addresses_region ALTER COLUMN country_id SET NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS addresses_country_iso_code_uniq
    ON addresses_country (iso_code) WHERE iso_code IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS addresses_country_iso3_code_uniq
    ON addresses_country (iso3_code) WHERE iso3_code IS NOT NULL;
CREATE INDEX IF NOT EXISTS region_country_name_idx
    ON addresses_region (country_id, name);

RESET lock_timeout;
"""


class Migration(migrations.Migration):
    atomic = False

    dependencies = [("addresses", "0004_city_slug_not_null")]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterModelOptions(
                    name="region",
                    options={
                        "ordering": ["country__name", "name"],
                        "verbose_name": "Регион",
                        "verbose_name_plural": "Регионы",
                    },
                ),
                migrations.RemoveIndex(model_name="region", name="region_fd_name_idx"),
                migrations.AlterUniqueTogether(name="region", unique_together=set()),
                migrations.AddField(
                    model_name="country",
                    name="iso_code",
                    field=models.CharField(
                        max_length=2, unique=True, null=True, blank=True, db_index=True,
                        validators=[RegexValidator(r"^[A-Z]{2}$")],
                    ),
                ),
                migrations.AddField(
                    model_name="country",
                    name="iso3_code",
                    field=models.CharField(
                        max_length=3, unique=True, null=True, blank=True,
                        validators=[RegexValidator(r"^[A-Z]{3}$")],
                    ),
                ),
                migrations.AddField(
                    model_name="region",
                    name="country",
                    field=models.ForeignKey(
                        "addresses.country", on_delete=django.db.models.deletion.PROTECT,
                        related_name="regions",
                    ),
                ),
                migrations.AlterField(
                    model_name="region", name="federal_district",
                    field=models.ForeignKey(
                        "addresses.federaldistrict", on_delete=django.db.models.deletion.PROTECT,
                        related_name="regions", null=True, blank=True,
                    ),
                ),
                migrations.AlterField(
                    model_name="region", name="type_region",
                    field=models.ForeignKey(
                        "addresses.typeregion", on_delete=django.db.models.deletion.PROTECT,
                        related_name="regions", null=True, blank=True,
                    ),
                ),
                migrations.AddIndex(
                    model_name="region",
                    index=BTreeIndex(fields=["country", "name"], name="region_country_name_idx"),
                ),
            ],
            database_operations=[migrations.RunSQL(SCHEMA_SQL, migrations.RunSQL.noop)],
        )
    ]
