# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-12 01:02
from __future__ import unicode_literals

from django.conf import settings
import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0008_alter_user_username_max_length'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='LeaseBlock',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prot_number', models.CharField(blank=True, max_length=7, null=True)),
                ('prot_aprv', models.CharField(blank=True, max_length=11, null=True)),
                ('block_number', models.CharField(blank=True, max_length=6, null=True)),
                ('prot_numb', models.CharField(blank=True, max_length=15, null=True)),
                ('min_depth', models.FloatField()),
                ('max_depth', models.FloatField()),
                ('avg_depth', models.FloatField()),
                ('min_wind_speed', models.FloatField()),
                ('max_wind_speed', models.FloatField()),
                ('majority_sediment', models.CharField(blank=True, max_length=35, null=True)),
                ('variety_sediment', models.IntegerField()),
                ('majority_seabed', models.CharField(blank=True, max_length=35, null=True)),
                ('variety_seabed', models.IntegerField(blank=True, null=True)),
                ('min_distance', models.FloatField(blank=True, null=True)),
                ('max_distance', models.FloatField(blank=True, null=True)),
                ('avg_distance', models.FloatField(blank=True, null=True)),
                ('awc_min_distance', models.FloatField(blank=True, null=True)),
                ('awc_max_distance', models.FloatField(blank=True, null=True)),
                ('awc_avg_distance', models.FloatField(blank=True, null=True)),
                ('wea_number', models.IntegerField(blank=True, null=True)),
                ('wea_name', models.CharField(blank=True, max_length=10, null=True)),
                ('ais_all_vessels_maj', models.IntegerField(blank=True, null=True)),
                ('ais_all_vessels_low', models.FloatField(blank=True, null=True)),
                ('ais_all_vessels_medium', models.FloatField(blank=True, null=True)),
                ('ais_all_vessels_high', models.FloatField(blank=True, null=True)),
                ('ais_cargo_vessels_maj', models.IntegerField(blank=True, null=True)),
                ('ais_cargo_vessels_low', models.FloatField(blank=True, null=True)),
                ('ais_cargo_vessels_medium', models.FloatField(blank=True, null=True)),
                ('ais_cargo_vessels_high', models.FloatField(blank=True, null=True)),
                ('ais_passenger_vessels_maj', models.IntegerField(blank=True, null=True)),
                ('ais_passenger_vessels_low', models.FloatField(blank=True, null=True)),
                ('ais_passenger_vessels_medium', models.FloatField(blank=True, null=True)),
                ('ais_passenger_vessels_high', models.FloatField(blank=True, null=True)),
                ('ais_tanker_vessels_maj', models.IntegerField(blank=True, null=True)),
                ('ais_tanker_vessels_low', models.FloatField(blank=True, null=True)),
                ('ais_tanker_vessels_medium', models.FloatField(blank=True, null=True)),
                ('ais_tanker_vessels_high', models.FloatField(blank=True, null=True)),
                ('ais_tugtow_vessels_maj', models.IntegerField(blank=True, null=True)),
                ('ais_tugtow_vessels_low', models.FloatField(blank=True, null=True)),
                ('ais_tugtow_vessels_medium', models.FloatField(blank=True, null=True)),
                ('ais_tugtow_vessels_high', models.FloatField(blank=True, null=True)),
                ('min_wind_speed_rev', models.FloatField(blank=True, null=True)),
                ('max_wind_speed_rev', models.FloatField(blank=True, null=True)),
                ('tsz_min_distance', models.FloatField(blank=True, null=True)),
                ('tsz_max_distance', models.FloatField(blank=True, null=True)),
                ('tsz_mean_distance', models.FloatField(blank=True, null=True)),
                ('lace_coral_count', models.IntegerField(blank=True, null=True)),
                ('lace_coral_name', models.CharField(blank=True, max_length=50, null=True)),
                ('black_coral_count', models.IntegerField(blank=True, null=True)),
                ('black_coral_name', models.CharField(blank=True, max_length=50, null=True)),
                ('soft_coral_count', models.IntegerField(blank=True, null=True)),
                ('soft_coral_name', models.CharField(blank=True, max_length=50, null=True)),
                ('gorgo_coral_count', models.IntegerField(blank=True, null=True)),
                ('gorgo_coral_name', models.CharField(blank=True, max_length=50, null=True)),
                ('sea_pen_count', models.IntegerField(blank=True, null=True)),
                ('sea_pen_name', models.CharField(blank=True, max_length=50, null=True)),
                ('hard_coral_count', models.IntegerField(blank=True, null=True)),
                ('hard_coral_name', models.CharField(blank=True, max_length=50, null=True)),
                ('seabed_depression', models.FloatField(blank=True, null=True)),
                ('seabed_low_slope', models.FloatField(blank=True, null=True)),
                ('seabed_steep', models.FloatField(blank=True, null=True)),
                ('seabed_mid_flat', models.FloatField(blank=True, null=True)),
                ('seabed_side_slow', models.FloatField(blank=True, null=True)),
                ('seabed_high_flat', models.FloatField(blank=True, null=True)),
                ('seabed_high_slope', models.FloatField(blank=True, null=True)),
                ('seabed_total', models.FloatField(blank=True, null=True)),
                ('discharge_min_distance', models.FloatField(blank=True, null=True)),
                ('discharge_max_distance', models.FloatField(blank=True, null=True)),
                ('discharge_mean_distance', models.FloatField(blank=True, null=True)),
                ('discharge_flow_min_distance', models.FloatField(blank=True, null=True)),
                ('discharge_flow_max_distance', models.FloatField(blank=True, null=True)),
                ('discharge_flow_mean_distance', models.FloatField(blank=True, null=True)),
                ('dredge_site', models.IntegerField(blank=True, null=True)),
                ('wpa', models.IntegerField(blank=True, null=True)),
                ('wpa_name', models.CharField(blank=True, max_length=75, null=True)),
                ('shipwreck_density', models.IntegerField(blank=True, null=True)),
                ('uxo', models.IntegerField(blank=True, null=True)),
                ('substation_min_distance', models.FloatField(blank=True, null=True)),
                ('substation_max_distance', models.FloatField(blank=True, null=True)),
                ('substation_mean_distance', models.FloatField(blank=True, null=True)),
                ('marco_region', models.IntegerField(blank=True, null=True)),
                ('geometry', django.contrib.gis.db.models.fields.MultiPolygonField(blank=True, null=True, srid=3857, verbose_name='Lease Block Geometry')),
            ],
        ),
        migrations.CreateModel(
            name='LeaseBlockSelection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date Created')),
                ('date_modified', models.DateTimeField(auto_now=True, verbose_name='Date Modified')),
                ('object_id', models.PositiveIntegerField(blank=True, null=True)),
                ('leaseblock_ids', models.TextField()),
                ('description', models.TextField(blank=True, null=True)),
                ('geometry_actual', django.contrib.gis.db.models.fields.MultiPolygonField(blank=True, null=True, srid=3857, verbose_name='Lease Block Selection Geometry')),
                ('content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='scenarios_leaseblockselection_related', to='contenttypes.ContentType')),
                ('sharing_groups', models.ManyToManyField(blank=True, editable=False, related_name='scenarios_leaseblockselection_related', to='auth.Group', verbose_name='Share with the following groups')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='scenarios_leaseblockselection_related', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Objective',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=35)),
                ('color', models.CharField(default='778B1A55', max_length=8)),
            ],
        ),
        migrations.CreateModel(
            name='Parameter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ordering_id', models.IntegerField(blank=True, null=True)),
                ('name', models.CharField(blank=True, max_length=35, null=True)),
                ('shortname', models.CharField(blank=True, max_length=35, null=True)),
                ('objectives', models.ManyToManyField(blank=True, null=True, to='scenarios.Objective')),
            ],
        ),
        migrations.CreateModel(
            name='Scenario',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date Created')),
                ('date_modified', models.DateTimeField(auto_now=True, verbose_name='Date Modified')),
                ('object_id', models.PositiveIntegerField(blank=True, null=True)),
                ('input_parameter_depth', models.BooleanField(default=False, verbose_name='Depth Parameter')),
                ('input_min_depth', models.FloatField(blank=True, null=True, verbose_name='Minimum Depth')),
                ('input_max_depth', models.FloatField(blank=True, null=True, verbose_name='Maximum Depth')),
                ('input_parameter_distance_to_shore', models.BooleanField(default=False, verbose_name='Distance to Shore')),
                ('input_min_distance_to_shore', models.FloatField(blank=True, null=True, verbose_name='Minimum Distance to Shore')),
                ('input_max_distance_to_shore', models.FloatField(blank=True, null=True, verbose_name='Maximum Distance to Shore')),
                ('input_parameter_substrate', models.BooleanField(default=False, verbose_name='Substrate Parameter')),
                ('input_parameter_sediment', models.BooleanField(default=False, verbose_name='Sediment Parameter')),
                ('input_parameter_wind_speed', models.BooleanField(default=False, verbose_name='Wind Speed Parameter')),
                ('input_avg_wind_speed', models.FloatField(blank=True, null=True, verbose_name='Average Wind Speed')),
                ('input_parameter_distance_to_awc', models.BooleanField(default=False, verbose_name='Distance to AWC Station')),
                ('input_distance_to_awc', models.FloatField(blank=True, null=True, verbose_name='Maximum Distance to AWC Station')),
                ('input_parameter_distance_to_substation', models.BooleanField(default=False, verbose_name='Distance to Coastal Substation')),
                ('input_distance_to_substation', models.FloatField(blank=True, null=True, verbose_name='Maximum Distance to Coastal Substation')),
                ('input_parameter_wea', models.BooleanField(default=False, verbose_name='WEA Parameter')),
                ('input_filter_ais_density', models.BooleanField(default=False, verbose_name='Excluding Areas with AIS Density >= 1')),
                ('input_filter_distance_to_shipping', models.BooleanField(default=False, verbose_name='Distance to Ship Routing Measures')),
                ('input_distance_to_shipping', models.FloatField(blank=True, null=True, verbose_name='Minimum Distance to Ship Routing Measures')),
                ('input_filter_uxo', models.BooleanField(default=False, verbose_name='Excluding Areas with UXO')),
                ('description', models.TextField(blank=True, null=True)),
                ('satisfied', models.BooleanField(default=True)),
                ('active', models.BooleanField(default=True)),
                ('lease_blocks', models.TextField(blank=True, null=True, verbose_name='Lease Block IDs')),
                ('geometry_final_area', models.FloatField(blank=True, null=True, verbose_name='Total Area')),
                ('geometry_dissolved', django.contrib.gis.db.models.fields.MultiPolygonField(blank=True, null=True, srid=3857, verbose_name='Scenario result dissolved')),
                ('content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='scenarios_scenario_related', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Sediment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sediment_id', models.IntegerField()),
                ('sediment_name', models.CharField(max_length=35)),
                ('sediment_output', models.CharField(max_length=55)),
                ('sediment_shortname', models.CharField(max_length=35)),
            ],
        ),
        migrations.CreateModel(
            name='Substrate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('substrate_id', models.IntegerField()),
                ('substrate_name', models.CharField(max_length=35)),
                ('substrate_shortname', models.CharField(max_length=35)),
            ],
        ),
        migrations.CreateModel(
            name='WEA',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('wea_id', models.IntegerField()),
                ('wea_name', models.CharField(max_length=35)),
                ('wea_shortname', models.CharField(max_length=35)),
            ],
        ),
        migrations.AddField(
            model_name='scenario',
            name='input_sediment',
            field=models.ManyToManyField(blank=True, null=True, to='scenarios.Sediment'),
        ),
        migrations.AddField(
            model_name='scenario',
            name='input_substrate',
            field=models.ManyToManyField(blank=True, null=True, to='scenarios.Substrate'),
        ),
        migrations.AddField(
            model_name='scenario',
            name='input_wea',
            field=models.ManyToManyField(blank=True, null=True, to='scenarios.WEA'),
        ),
        migrations.AddField(
            model_name='scenario',
            name='sharing_groups',
            field=models.ManyToManyField(blank=True, editable=False, related_name='scenarios_scenario_related', to='auth.Group', verbose_name='Share with the following groups'),
        ),
        migrations.AddField(
            model_name='scenario',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='scenarios_scenario_related', to=settings.AUTH_USER_MODEL),
        ),
    ]
