"""Join the published branch to the production migration without duplicate DDL.

Production already created these models under the longer 0002 name. Both
identities remain in the graph; this successor only records the reconciliation.
"""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("corporate_broadcast", "0002_typesofplacebroadcast_broadcastlanding_typeofformats_and_more"),
        ("nomenclatures", "0017_station_command_superseded_state"),
    ]

    operations = []
