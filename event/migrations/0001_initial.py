# Generated by Django 4.2.9 on 2024-03-11 18:09

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id_event', models.AutoField(primary_key=True, serialize=False)),
                ('dia_sin_carro', models.BooleanField(default=False)),
                ('festividad', models.BooleanField(default=False)),
                ('protesta', models.BooleanField(default=False)),
                ('volumen_trafico', models.DecimalField(decimal_places=2, max_digits=6)),
            ],
        ),
    ]
