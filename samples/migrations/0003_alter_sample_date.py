# Generated by Django 4.2.9 on 2024-03-11 20:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0002_alter_sample_humidity_alter_sample_latitude_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sample',
            name='date',
            field=models.DateTimeField(),
        ),
    ]
