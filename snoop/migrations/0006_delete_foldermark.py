# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2016-10-08 11:29
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('snoop', '0005_delete_archivelistcache'),
    ]

    operations = [
        migrations.DeleteModel(
            name='FolderMark',
        ),
    ]