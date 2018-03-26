# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-03-26 15:12
from __future__ import unicode_literals

import re

from django.conf import settings
import django.contrib.gis.db.models.fields
import django.contrib.postgres.fields.hstore
from django.db import migrations, models
import django.db.models.deletion
import json


# Functions from the following migrations need manual copying.
# Move them and any dependencies into this file, then update the
# RunPython operations to refer to the local versions:

# geokey.contributions.migrations.0004_auto_20150121_1455
def populate_display_field(apps, schema_editor):
    observation_model = apps.get_model("contributions", "Observation")
    for observation in observation_model.objects.all():
        first_field = observation.category.fields.get(order=0)
        value = observation.attributes.get(first_field.key)
        observation.display_field = '%s:%s' % (first_field.key, value)
        observation.save()


# geokey.contributions.migrations.0005_auto_20150202_1135
def update_search_matches(apps, schema_editor):
    observation_model = apps.get_model("contributions", "Observation")
    for observation in observation_model.objects.all():
        observation.update_search_matches()
        observation.save()


# geokey.contributions.migrations.0007_auto_20150312_1249
def convert_value(val):
    if val is not None and isinstance(val, str):
        try:  # it's an int
            return int(val)
        except ValueError:
            pass

        try:  # it's a float
            return float(val)
        except ValueError:
            pass
    # cannot convert to number, returns string or None
    return val


def copy_attributes(apps, schema_editor):
    observation_model = apps.get_model("contributions", "Observation")
    for observation in observation_model.objects.all():
        properties = {}
        for field in observation.category.fields.all():
            value = observation.attributes.get(field.key)
            if value is not None:
                properties[field.key] = convert_value(value)

        observation.properties = properties
        observation.save()


# geokey.contributions.migrations.0010_auto_20150511_1132
def clean_list(val):
    if val is not None and (isinstance(val, str) or isinstance(val, unicode)):
        return json.loads(val)
    return val


def clean_int(val):
    if val is not None and (isinstance(val, str) or isinstance(val, unicode)):
        return int(val)
    return val


def clean_number(val):
    if val is not None and (isinstance(val, str) or isinstance(val, unicode)):
        try:  # it's an int
            return int(val)
        except ValueError:
            pass

        try:  # it's a float
            return float(val)
        except ValueError:
            pass
    # cannot convert to number, returns string or None
    return val


def clean_values(apps, schema_editor):
    observation_model = apps.get_model("contributions", "Observation")
    numeric_field_model = apps.get_model("categories", "NumericField")
    lookup_field_model = apps.get_model("categories", "LookupField")
    multiple_lookup_field_model = apps.get_model("categories", "MultipleLookupField")

    for field in numeric_field_model.objects.all():
        for observation in observation_model.objects.filter(category=field.category):
            if observation.properties:
                value = observation.properties.get(field.key)
                if value:
                    observation.properties[field.key] = clean_number(value)
                    observation.save()

    for field in lookup_field_model.objects.all():
        for observation in observation_model.objects.filter(category=field.category):
            if observation.properties:
                value = observation.properties.get(field.key)
                if value:
                    observation.properties[field.key] = clean_int(value)
                    observation.save()

    for field in multiple_lookup_field_model.objects.all():
        for observation in observation_model.objects.filter(category=field.category):
            if observation.properties:
                value = observation.properties.get(field.key)
                if value:
                    observation.properties[field.key] = clean_list(value)
                    observation.save()


# geokey.contributions.migrations.0011_auto_20150527_1255
def clean_youtube_links(apps, schema_editor):
    video_file_model = apps.get_model("contributions", "VideoFile")

    for file in video_file_model.objects.all():
        new_link = file.youtube_link.replace('http://', 'https://')
        file.youtube_link = new_link
        file.save()


# geokey.contributions.migrations.0012_auto_20150807_0854
def update_count(apps, schema_editor):
    observation = apps.get_model('contributions', 'Observation')

    for o in observation.objects.all():
        o.num_media = o.files_attached.exclude(status='deleted').count()
        o.num_comments = o.comments.exclude(status='deleted').count()
        o.save()


# geokey.contributions.migrations.0014_auto_20150907_1345
def create_search_index(apps, schema_editor):
    observation = apps.get_model('contributions', 'Observation')

    for o in observation.objects.all():
        search_index = []

        fields = o.search_matches.split('#####')
        for field in fields:
            if field:
                value = field.split(':')[1]

                cleaned = re.sub(r'[\W_]+', ' ', value)
                terms = cleaned.lower().split()

                search_index = search_index + list(
                    set(terms) - set(search_index)
                )

        o.search_index = ','.join(search_index)
        o.save()


class Migration(migrations.Migration):
    replaces = [(b'contributions', '0001_initial'), (b'contributions', '0002_auto_20150106_1338'),
                (b'contributions', '0003_auto_20150121_1544'), (b'contributions', '0004_auto_20150121_1455'),
                (b'contributions', '0005_auto_20150202_1135'), (b'contributions', '0006_auto_20150312_1247'),
                (b'contributions', '0007_auto_20150312_1249'), (b'contributions', '0008_auto_20150312_1508'),
                (b'contributions', '0009_auto_20150420_1549'), (b'contributions', '0010_auto_20150511_1132'),
                (b'contributions', '0011_auto_20150527_1255'), (b'contributions', '0012_auto_20150807_0854'),
                (b'contributions', '0013_auto_20150907_1345'), (b'contributions', '0014_auto_20150907_1345'),
                (b'contributions', '0015_auto_20150907_1345'), (b'contributions', '0016_audiofile'),
                (b'contributions', '0017_auto_20160531_1434'), (b'contributions', '0018_historicalcomment')]

    initial = True

    dependencies = [
        ('projects', '0005_auto_20150202_1041'),
        ('categories', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('categories', '0013_auto_20150130_1440'),
        ('projects', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('status',
                 models.CharField(choices=[(b'active', b'active'), (b'deleted', b'deleted')], default=b'active',
                                  max_length=20)),
                ('review_status',
                 models.CharField(blank=True, choices=[(b'open', b'open'), (b'resolved', b'resolved')], max_length=10,
                                  null=True)),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='HistoricalObservation',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('location_id', models.IntegerField(blank=True, db_index=True, null=True)),
                ('project_id', models.IntegerField(blank=True, db_index=True, null=True)),
                ('category_id', models.IntegerField(blank=True, db_index=True, null=True)),
                ('status', models.CharField(
                    choices=[(b'active', b'active'), (b'draft', b'draft'), (b'review', b'review'),
                             (b'pending', b'pending'), (b'deleted', b'deleted')], default=b'active', max_length=20)),
                ('attributes', django.contrib.postgres.fields.hstore.HStoreField(db_index=True)),
                ('created_at', models.DateTimeField(blank=True, editable=False)),
                ('creator_id', models.IntegerField(blank=True, db_index=True, null=True)),
                ('updated_at', models.DateTimeField(blank=True, editable=False, null=True)),
                ('updator_id', models.IntegerField(blank=True, db_index=True, null=True)),
                ('version', models.IntegerField(default=1)),
                ('search_matches', models.TextField()),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_type',
                 models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE,
                                                   to=settings.AUTH_USER_MODEL)),
                ('display_field', models.TextField(blank=True, null=True)),
            ],
            options={
                'ordering': ('-history_date', '-history_id'),
                'verbose_name': 'historical observation',
            },
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=100, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('geometry', django.contrib.gis.db.models.GeometryField(geography=True, srid=4326)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('version', models.IntegerField(default=1)),
                ('private', models.BooleanField(default=False)),
                ('status', models.CharField(choices=[(b'active', b'active'), (b'review', b'review')], default=b'active',
                                            max_length=20)),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                              to=settings.AUTH_USER_MODEL)),
                ('private_for_project',
                 models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='projects.Project')),
            ],
        ),
        migrations.CreateModel(
            name='MediaFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('status',
                 models.CharField(choices=[(b'active', b'active'), (b'deleted', b'deleted')], default=b'active',
                                  max_length=20)),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='ImageFile',
            fields=[
                ('mediafile_ptr',
                 models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True,
                                      primary_key=True, serialize=False, to='contributions.MediaFile')),
                ('image', models.ImageField(upload_to=b'user-uploads/images')),
            ],
            options={
                'ordering': ['id'],
            },
            bases=('contributions.mediafile',),
        ),
        migrations.CreateModel(
            name='Observation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(
                    choices=[(b'active', b'active'), (b'draft', b'draft'), (b'review', b'review'),
                             (b'pending', b'pending'), (b'deleted', b'deleted')], default=b'active', max_length=20)),
                ('attributes', django.contrib.postgres.fields.hstore.HStoreField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('version', models.IntegerField(default=1)),
                ('search_matches', models.TextField()),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='categories.Category')),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='creator',
                                              to=settings.AUTH_USER_MODEL)),
                ('location', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='locations',
                                               to='contributions.Location')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='observations',
                                              to='projects.Project')),
                ('updator',
                 models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='updator',
                                   to=settings.AUTH_USER_MODEL)),
                ('display_field', models.TextField(blank=True, null=True)),
            ],
            options={
                'ordering': ['-updated_at', 'id'],
            },
        ),
        migrations.CreateModel(
            name='VideoFile',
            fields=[
                ('mediafile_ptr',
                 models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True,
                                      primary_key=True, serialize=False, to='contributions.MediaFile')),
                ('video', models.ImageField(upload_to=b'user-uploads/videos')),
                ('youtube_id', models.CharField(max_length=100)),
                ('thumbnail', models.ImageField(null=True, upload_to=b'user-uploads/videos')),
                ('youtube_link', models.URLField(blank=True, max_length=255, null=True)),
                ('swf_link', models.URLField(blank=True, max_length=255, null=True)),
            ],
            options={
                'ordering': ['id'],
            },
            bases=('contributions.mediafile',),
        ),
        migrations.AddField(
            model_name='mediafile',
            name='contribution',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='files_attached',
                                    to='contributions.Observation'),
        ),
        migrations.AddField(
            model_name='mediafile',
            name='creator',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='comment',
            name='commentto',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments',
                                    to='contributions.Observation'),
        ),
        migrations.AddField(
            model_name='comment',
            name='creator',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='comment',
            name='respondsto',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                    related_name='responses', to='contributions.Comment'),
        ),
        migrations.RunPython(code=populate_display_field,),
        migrations.RunPython(code=update_search_matches,),
        migrations.AddField(
            model_name='historicalobservation',
            name='properties',
            field=django.contrib.postgres.fields.jsonb.JSONField(default={}),
        ),
        migrations.AddField(
            model_name='observation',
            name='properties',
            field=django.contrib.postgres.fields.jsonb.JSONField(default={}),
        ),
        migrations.RunPython(code=copy_attributes,),
        migrations.RemoveField(
            model_name='historicalobservation',
            name='attributes',
        ),
        migrations.RemoveField(
            model_name='observation',
            name='attributes',
        ),
        migrations.AlterModelOptions(
            name='historicalobservation',
            options={'get_latest_by': 'history_date', 'ordering': ('-history_date', '-history_id'),
                     'verbose_name': 'historical observation'},
        ),
        migrations.AlterField(
            model_name='historicalobservation',
            name='history_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    to=settings.AUTH_USER_MODEL),
        ),
        migrations.RunPython(code=clean_values,),
        migrations.RunPython(code=clean_youtube_links,),
        migrations.AddField(
            model_name='historicalobservation',
            name='num_comments',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='historicalobservation',
            name='num_media',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='observation',
            name='num_comments',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='observation',
            name='num_media',
            field=models.IntegerField(default=0),
        ),
        migrations.RunPython(code=update_count,),
        migrations.RemoveField(
            model_name='historicalobservation',
            name='category_id',
        ),
        migrations.RemoveField(
            model_name='historicalobservation',
            name='creator_id',
        ),
        migrations.RemoveField(
            model_name='historicalobservation',
            name='location_id',
        ),
        migrations.RemoveField(
            model_name='historicalobservation',
            name='project_id',
        ),
        migrations.RemoveField(
            model_name='historicalobservation',
            name='updator_id',
        ),
        migrations.AddField(
            model_name='historicalobservation',
            name='category',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True,
                                    on_delete=django.db.models.deletion.DO_NOTHING, related_name='+',
                                    to='categories.Category'),
        ),
        migrations.AddField(
            model_name='historicalobservation',
            name='creator',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True,
                                    on_delete=django.db.models.deletion.DO_NOTHING, related_name='+',
                                    to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='historicalobservation',
            name='location',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True,
                                    on_delete=django.db.models.deletion.DO_NOTHING, related_name='+',
                                    to='contributions.Location'),
        ),
        migrations.AddField(
            model_name='historicalobservation',
            name='project',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True,
                                    on_delete=django.db.models.deletion.DO_NOTHING, related_name='+',
                                    to='projects.Project'),
        ),
        migrations.AddField(
            model_name='historicalobservation',
            name='search_index',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='historicalobservation',
            name='updator',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True,
                                    on_delete=django.db.models.deletion.DO_NOTHING, related_name='+',
                                    to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='observation',
            name='search_index',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='historicalobservation',
            name='history_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+',
                                    to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='historicalobservation',
            name='search_matches',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='observation',
            name='search_matches',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.RunPython(code=create_search_index,),
        migrations.RemoveField(
            model_name='historicalobservation',
            name='search_matches',
        ),
        migrations.RemoveField(
            model_name='observation',
            name='search_matches',
        ),
        migrations.CreateModel(
            name='AudioFile',
            fields=[
                ('mediafile_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE,
                                                       parent_link=True, primary_key=True, serialize=False,
                                                       to='contributions.MediaFile')),
                ('audio', models.FileField(upload_to=b'user-uploads/audio')),
            ],
            options={
                'ordering': ['id'],
            },
            bases=('contributions.mediafile',),
        ),
        migrations.AddField(
            model_name='historicalobservation',
            name='expiry_field',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='observation',
            name='expiry_field',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='HistoricalComment',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('text', models.TextField()),
                ('created_at', models.DateTimeField(blank=True, editable=False)),
                ('status',
                 models.CharField(choices=[(b'active', b'active'), (b'deleted', b'deleted')], default=b'active',
                                  max_length=20)),
                ('review_status',
                 models.CharField(blank=True, choices=[(b'open', b'open'), (b'resolved', b'resolved')], max_length=10,
                                  null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_type',
                 models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('commentto', models.ForeignKey(blank=True, db_constraint=False, null=True,
                                                on_delete=django.db.models.deletion.DO_NOTHING, related_name='+',
                                                to='contributions.Observation')),
                ('creator', models.ForeignKey(blank=True, db_constraint=False, null=True,
                                              on_delete=django.db.models.deletion.DO_NOTHING, related_name='+',
                                              to=settings.AUTH_USER_MODEL)),
                ('history_user',
                 models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+',
                                   to=settings.AUTH_USER_MODEL)),
                ('respondsto', models.ForeignKey(blank=True, db_constraint=False, null=True,
                                                 on_delete=django.db.models.deletion.DO_NOTHING, related_name='+',
                                                 to='contributions.Comment')),
            ],
            options={
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
                'verbose_name': 'historical comment',
            },
        ),
    ]
