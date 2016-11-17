# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2016-10-26 14:39
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


DEFAULT_COLLECTION_DESCRIPTION = "This collection was automatically " \
                                 "created by the snoop setup."


def create_default_collection_if_documents_exist(apps, schema_editor):
    db_alias = schema_editor.connection.alias

    Document = apps.get_model('snoop', 'Document')
    document_count = Document.objects.using(db_alias).count()
    if document_count > 0:
        Collection = apps.get_model('snoop', 'Collection')
        try:
            es_index = settings.SNOOP_ELASTICSEARCH_INDEX
            path = settings.SNOOP_ROOT
        except AttributeError:
            print("The settings are not set up properly!")
            raise

        Collection.objects.using(db_alias).bulk_create([
            Collection(
                id=1,
                slug='doc',
                title='Default Collection',
                es_index=es_index,
                description=DEFAULT_COLLECTION_DESCRIPTION,
                path=path,
            )
        ])

class Migration(migrations.Migration):

    dependencies = [
        ('snoop', '0006_delete_foldermark'),
    ]

    operations = [
        migrations.CreateModel(
            name='Collection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('path', models.CharField(max_length=4000)),
                ('slug', models.CharField(db_index=True, max_length=100, unique=True)),
                ('title', models.CharField(max_length=200)),
                ('es_index', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
            ],
        ),
        migrations.RunPython(
            create_default_collection_if_documents_exist,
        ),
        migrations.AddField(
            model_name='document',
            name='collection',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='document_set', to='snoop.Collection'),
            preserve_default=False,
        ),
    ]
