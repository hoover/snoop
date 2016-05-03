# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-05-03 10:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('path', models.CharField(db_index=True, max_length=4000, unique=True)),
                ('disk_size', models.BigIntegerField()),
            ],
        ),
    ]
