# Generated by Django 5.1.3 on 2024-11-30 17:27

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("vehicle", "0018_alter_vehicle_year_built_componentpermission"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="vehiclecomponent",
            options={
                "ordering": ["vehicle", "component_type__name"],
                "permissions": [
                    ("view_status", "Can view component status"),
                    ("change_status", "Can change component status"),
                ],
                "verbose_name": "Vehicle Component",
                "verbose_name_plural": "Vehicle Components",
            },
        ),
    ]
