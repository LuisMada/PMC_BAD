# Generated by Django 5.1.5 on 2025-03-28 09:40

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('VehicleManagementSystem', '0012_vehicleinspection_is_submitted'),
    ]

    operations = [
        migrations.CreateModel(
            name='DamageReport',
            fields=[
                ('damage_id', models.AutoField(primary_key=True, serialize=False)),
                ('report_id', models.CharField(max_length=20, unique=True)),
                ('inspection_date', models.DateField()),
                ('battery_damage', models.TextField(blank=True, null=True)),
                ('lights_damage', models.TextField(blank=True, null=True)),
                ('oil_damage', models.TextField(blank=True, null=True)),
                ('water_damage', models.TextField(blank=True, null=True)),
                ('brakes_damage', models.TextField(blank=True, null=True)),
                ('air_damage', models.TextField(blank=True, null=True)),
                ('gas_damage', models.TextField(blank=True, null=True)),
                ('maintenance_diagnosis', models.TextField(blank=True, null=True)),
                ('estimate_repair_time', models.CharField(default='0', max_length=50)),
                ('concerns', models.TextField(blank=True, null=True)),
                ('is_submitted', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('inspector', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='damage_inspections', to=settings.AUTH_USER_MODEL)),
                ('vehicle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='damage_reports', to='VehicleManagementSystem.vehicle')),
            ],
        ),
    ]
