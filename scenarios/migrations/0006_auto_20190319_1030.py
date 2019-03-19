# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-03-19 17:30
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scenarios', '0005_auto_20180131_1432'),
    ]

    operations = [
        migrations.AlterField(
            model_name='demoscenario',
            name='geometry_final_area',
            field=models.FloatField(blank=True, default=None, null=True, verbose_name='Total Area'),
        ),
        migrations.AlterField(
            model_name='demoscenario',
            name='planning_units',
            field=models.TextField(blank=True, default=None, null=True, verbose_name='Planning Unit IDs'),
        ),
    ]