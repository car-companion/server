# Generated by Django 5.1.2 on 2024-11-03 12:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vehicle', '0005_componenttype_vehiclecomponent'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='vehiclecomponent',
            unique_together={('vehicle', 'name')},
        ),
    ]