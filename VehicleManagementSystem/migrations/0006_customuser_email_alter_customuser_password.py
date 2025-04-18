# Generated by Django 5.1.5 on 2025-03-11 05:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('VehicleManagementSystem', '0005_remove_customuser_password_reset_required'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='email',
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='password',
            field=models.CharField(max_length=128, verbose_name='password'),
        ),
    ]
