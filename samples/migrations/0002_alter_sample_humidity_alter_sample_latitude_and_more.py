# Generated by Django 4.2.9 on 2024-03-11 19:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sample',
            name='humidity',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='sample',
            name='latitude',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='sample',
            name='longitude',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='sample',
            name='temperature',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='sample',
            name='value_PM2',
            field=models.FloatField(),
        ),
    ]