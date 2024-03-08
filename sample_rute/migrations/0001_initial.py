# Generated by Django 4.2.9 on 2024-03-08 20:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('samples', '0001_initial'),
        ('rutes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Sample_rute',
            fields=[
                ('id_sample_rute', models.AutoField(primary_key=True, serialize=False)),
                ('rute', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='rutes.rute')),
                ('sample', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='samples.sample')),
            ],
        ),
    ]
