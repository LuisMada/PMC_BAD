# Generated by Django 5.1.5 on 2025-03-05 13:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('VehicleManagementSystem', '0003_alter_customuser_employee_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='password_reset_required',
            field=models.BooleanField(default=True),
        ),
    ]
