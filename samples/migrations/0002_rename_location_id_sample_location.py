# Generated by Django 5.0 on 2024-01-02 02:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='sample',
            old_name='location_id',
            new_name='location',
        ),
    ]
