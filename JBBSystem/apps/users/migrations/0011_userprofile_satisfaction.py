# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2019-05-31 11:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0010_userprofile_estimate'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='satisfaction',
            field=models.CharField(choices=[('best', '优'), ('good', '良'), ('normal', '中'), ('bad', '差')], default='', max_length=10),
        ),
    ]
