# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2016-08-10 18:01
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ArchiveListCache',
            fields=[
                ('sha1', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('value', models.TextField()),
                ('time', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Digest',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('data', models.TextField()),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('path', models.CharField(max_length=4000)),
                ('content_type', models.CharField(blank=True, max_length=100)),
                ('filename', models.CharField(max_length=1000)),
                ('disk_size', models.BigIntegerField()),
                ('md5', models.CharField(blank=True, db_index=True, max_length=40)),
                ('sha1', models.CharField(blank=True, db_index=True, max_length=50)),
                ('broken', models.CharField(blank=True, max_length=100)),
                ('rev', models.IntegerField(null=True)),
                ('flags', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict)),
                ('container', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='snoop.Document')),
            ],
        ),
        migrations.CreateModel(
            name='EmailCache',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('value', models.TextField()),
                ('time', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='FolderMark',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('path', models.CharField(db_index=True, max_length=4000, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='HtmlTextCache',
            fields=[
                ('sha1', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('value', models.TextField()),
                ('time', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('queue', models.CharField(max_length=100)),
                ('data', django.contrib.postgres.fields.jsonb.JSONField(null=True)),
                ('started', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Ocr',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tag', models.CharField(max_length=100)),
                ('md5', models.CharField(db_index=True, max_length=40)),
                ('path', models.CharField(max_length=4000)),
                ('text', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='TikaCache',
            fields=[
                ('sha1', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('value', models.TextField()),
                ('time', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='TikaLangCache',
            fields=[
                ('sha1', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('value', models.CharField(max_length=20)),
                ('time', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='ocr',
            unique_together=set([('tag', 'md5')]),
        ),
        migrations.AlterUniqueTogether(
            name='job',
            unique_together=set([('queue', 'data')]),
        ),
        migrations.AlterIndexTogether(
            name='job',
            index_together=set([('queue', 'started')]),
        ),
        migrations.AlterUniqueTogether(
            name='document',
            unique_together=set([('container', 'path')]),
        ),
    ]