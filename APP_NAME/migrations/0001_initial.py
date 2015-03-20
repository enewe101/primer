# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PasswordReset',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creation_date', models.DateTimeField(verbose_name='creation date', editable=False)),
                ('last_modified', models.DateTimeField(verbose_name='last modified', editable=False)),
                ('email', models.EmailField(max_length=255, verbose_name='email')),
                ('username', models.CharField(max_length=32, verbose_name='username')),
            ],
            options={
                'verbose_name': 'Password reset request',
                'verbose_name_plural': 'Password reset requests',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Proof',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creation_date', models.DateTimeField(verbose_name='creation date', editable=False)),
                ('last_modified', models.DateTimeField(verbose_name='last modified', editable=False)),
                ('text', models.TextField()),
                ('user', models.ForeignKey(verbose_name='user', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProofRequest',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creation_date', models.DateTimeField(verbose_name='creation date', editable=False)),
                ('last_modified', models.DateTimeField(verbose_name='last modified', editable=False)),
                ('text', models.TextField()),
                ('status', models.CharField(max_length=16, choices=[(b'posted', b'posted'), (b'improved', b'improved'), (b'retrieved', b'retrieved'), (b'deleted', b'deleted')])),
                ('user', models.ForeignKey(verbose_name='user', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creation_date', models.DateTimeField(verbose_name='creation date', editable=False)),
                ('last_modified', models.DateTimeField(verbose_name='last modified', editable=False)),
                ('email_validated', models.BooleanField(default=False, verbose_name='email validated')),
                ('avatar_img', models.ImageField(upload_to=b'avatars', verbose_name='avatar image')),
                ('rep', models.IntegerField(default=0, verbose_name='reputation')),
                ('do_email_news', models.BooleanField(default=True, verbose_name='do email news')),
                ('do_email_responses', models.BooleanField(default=True, verbose_name='do email responses')),
                ('do_email_petitions', models.BooleanField(default=True, verbose_name='do email petitions')),
                ('do_email_watched', models.BooleanField(default=True, verbose_name='do email watched')),
                ('user', models.OneToOneField(related_name='profile', verbose_name='user', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'user profile',
                'verbose_name_plural': 'user profiles',
            },
            bases=(models.Model,),
        ),
    ]
