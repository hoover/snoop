# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-06-21 09:40
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maldini', '0027_document_filename'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='md5',
            field=models.CharField(blank=True, db_index=True, default='', max_length=40),
            preserve_default=False,
        ),
    ]
