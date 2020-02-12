from analysistools.models import Analysis
from features.registry import register
import json
from nursery.geojson.geojson import get_properties_json, get_feature_json
from nursery.kml.kml import asKml
from nursery.unit_conversions.unit_conversions import mph_to_mps, mps_to_mph
import os
import time

from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.gis.geos import MultiPolygon
from django.contrib.gis.db.models.aggregates import Union, Collect
from django.utils.html import escape
# import mapnik
from picklefield import PickledObjectField
from django.db.models import Manager as GeoManager

# @register
class Scenario(Analysis):

    description = models.TextField(null=True, blank=True)
    satisfied = models.BooleanField(default=True)
    active = models.BooleanField(default=True)

    #I'm finding myself wishing lease_blocks was spelled without the underscore...
    planning_units = models.TextField(verbose_name='Planning Unit IDs', null=True, blank=True, default=None)
    geometry_final_area = models.FloatField(verbose_name='Total Area', null=True, blank=True, default=None)
    geometry_dissolved = models.MultiPolygonField(srid=settings.GEOMETRY_DB_SRID, null=True, blank=True, verbose_name="Scenario result dissolved")

    ###
    # to be overridden by child model
    ###
    def serialize_attributes(self):
        attributes = []

        if self.planning_units:
            attributes.append({'title': 'Number of Planning Units', 'data': self.planning_units.count(',')+1})
        return { 'event': 'click', 'attributes': attributes }


    def geojson(self, srid):
        props = get_properties_json(self)
        props['absolute_url'] = self.get_absolute_url()
        json_geom = self.geometry_dissolved.transform(srid, clone=True).json
        return get_feature_json(json_geom, json.dumps(props))

    ###
    # to be overridden by child model
    ###
    def run_filters(self, result):
        return result

    def run(self, result=None):
        if not result:
            result = PlanningUnit.objects.all()

        # PU Filtration occurs here
        result = self.run_filters(result)

        try:
            dissolved_geom = result.aggregate(Union('geometry'))
            if dissolved_geom:
                dissolved_geom = dissolved_geom['geometry__union']
            else:
                raise Exception("No planning units available with the current filters.")
        except:
            raise Exception("No planning units available with the current filters.")

        if type(dissolved_geom) == MultiPolygon:
            self.geometry_dissolved = dissolved_geom
        else:
            try:
                self.geometry_dissolved = MultiPolygon(dissolved_geom, srid=dissolved_geom.srid)
            except:
                raise Exception("Unable to dissolve the returned planning units into a single geometry")

        self.active = True

        geom_clone = self.geometry_dissolved.clone()
        geom_clone.transform(2163)
        self.geometry_final_area = geom_clone.area
        self.planning_units = ','.join(str(i)
                                     for i in result.values_list('id',
                                                                 flat=True))

        if self.planning_units:
            self.satisfied = True
        else:
            self.satisfied = False

        return True

    def save(self, rerun=None, *args, **kwargs):
        super(Scenario, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'%s' % self.name

    def support_filename(self):
        return os.path.basename(self.support_file.name)

    @classmethod
    def mapnik_geomfield(self):
        return "output_geom"

    @classmethod
    def input_parameter_fields(klass):
        return [f for f in klass._meta.fields if f.attname.startswith('input_parameter_')]

    @classmethod
    def input_filter_fields(klass):
        return [f for f in klass._meta.fields if f.attname.startswith('input_filter_')]

    @property
    def planning_units_set(self):
        if len(self.planning_units) == 0:  #empty result
            planninunit_ids = []
        else:
            planningunit_ids = [int(id) for id in self.planning_units.split(',')]
        planningunits = PlanningUnit.objects.filter(pk__in=planningunit_ids)
        return planningunits

    @property
    def num_planning_units(self):
        if self.planning_units == '':
            return 0
        return len(self.planning_units.split(','))

    @property
    def geometry_is_empty(self):
        return len(self.planning_units) == 0

    @property
    def color(self):
        # try:
        #     return Objective.objects.get(pk=self.input_objectives.values_list()[0][0]).color
        # except:
        return '778B1A55'

    @property
    def kml_working(self):
        return """
        <Placemark id="%s">
            <visibility>0</visibility>
            <name>%s (WORKING)</name>
        </Placemark>
        """ % (self.uid, escape(self.name))

    @property
    def kml(self):
        #the following list appendation strategy was a good 10% faster than string concatenation
        #(biggest improvement however came by adding/populating a geometry_client column in leaseblock table)
        combined_kml_list = []
        if len(self.planning_units) == 0:  #empty result
            planningunit_ids = []
            combined_kml_list.append('<Folder id="%s"><name>%s -- 0 Planning Units</name><visibility>0</visibility><open>0</open>' %(self.uid, self.name))
        else:
            planningunit_ids = [int(id) for id in self.planning_units.split(',')]
            combined_kml_list.append('<Folder id="%s"><name>%s</name><visibility>0</visibility><open>0</open>' %(self.uid, self.name))
        combined_kml_list.append('<LookAt><longitude>-73.5</longitude><latitude>39</latitude><heading>0</heading><range>600000</range></LookAt>')
        combined_kml_list.append('<styleUrl>#%s-default</styleUrl>' % (self.model_uid()))
        combined_kml_list.append('%s' % self.planningunit_style())
        print('Generating KML for %s Planning Units' % len(planningunit_ids))
        start_time = time.time()
        planningunits = PlanningUnit.objects.filter(pk__in=planningunit_ids)
        for planningunit in planningunits:
            try:
                kml =   """
                    <Placemark>
                        <visibility>1</visibility>
                        <styleUrl>#%s-planningunit</styleUrl>
                        <ExtendedData>
                            <Data name="header"><value>%s</value></Data>
                            <!--
                            <Data name="prot_number"><value>s</value></Data>
                            <Data name="depth_range_output"><value>s</value></Data>
                            <Data name="substrate"><value>s</value></Data>
                            <Data name="sediment"><value>s</value></Data>
                            <Data name="wea_label"><value>s</value></Data>
                            <Data name="wea_state_name"><value>s</value></Data>
                            <Data name="distance_to_shore"><value>.0f</value></Data>
                            <Data name="distance_to_awc"><value>.0f</value></Data>
                            <Data name="wind_speed_output"><value>s</value></Data>
                            <Data name="ais_density"><value>s</value></Data>
                            -->
                            <Data name="user"><value>%s</value></Data>
                            <Data name="modified"><value>%s</value></Data>
                        </ExtendedData>
                        %s
                    </Placemark>
                    """ % ( self.model_uid(), self.name,
                            # planningunit.prot_numb,
                            # planningunit.depth_range_output,
                            # planningunit.majority_seabed, #LeaseBlock Update: might change back to leaseblock.substrate
                            # planningunit.majority_sediment, #TODO: might change sediment to a more user friendly output
                            # planningunit.wea_label,
                            # planningunit.wea_state_name,
                            # planningunit.avg_distance,
                            # planningunit.awc_min_distance,
                            # #LeaseBlock Update: added the following two entries (min and max) to replace avg wind speed for now
                            # planningunit.wind_speed_output,
                            # planningunit.ais_density,
                            self.user, self.date_modified.replace(microsecond=0),
                            #asKml(leaseblock.geometry.transform( settings.GEOMETRY_CLIENT_SRID, clone=True ))
                            asKml(planningunit.geometry_client)
                          )
            except:
                #this is in place to handle (at least one - "NJ18-05_6420") instance in which null value was used in float field max_distance
                # print("The following planning unit threw an error while generating KML:  %s" %planningunit.prot_numb)
                continue
            combined_kml_list.append(kml )
        combined_kml_list.append("</Folder>")
        combined_kml = ''.join(combined_kml_list)
        elapsed_time = time.time() - start_time
        print('Finished generating KML (with a list) for %s Planning Units in %s seconds' % (len(planningunit_ids), elapsed_time))

        return combined_kml

    def planningunit_style(self):
        #LeaseBlock Update:  changed the following from <p>Avg Wind Speed: $[wind_speed]
        return  """
                <Style id="%s-planningunit">
                    <BalloonStyle>
                        <bgColor>ffeeeeee</bgColor>
                        <text> <![CDATA[
                            <font color="#1A3752">
                                Spatial Design for Report: <strong>$[header]</strong>
                                <p>
                                <table width="250">
                                    <tr><td>
                                    Planning Unit Number:
                                    <!--
                                    <b>[prot_number]</b>
                                    -->
                                    </td></tr>
                                </table>
                                <table width="250">
                                    <!--
                                    <tr><td> $[wea_label] <b>$[wea_state_name]</b> </td></tr>
                                    <tr><td> Avg Wind Speed: <b>$[wind_speed_output]</b> </td></tr>
                                    <tr><td> Distance to AWC Station: <b>$[distance_to_awc] miles</b> </td></tr>
                                    -->
                                </table>
                                <table width="250">
                                    <!--
                                    <tr><td> Distance to Shore: <b>$[distance_to_shore] miles</b> </td></tr>
                                    <tr><td> Depth: <b>$[depth_range_output]</b> </td></tr>
                                    <tr><td> Majority Seabed Form: <b>$[substrate]</b> </td></tr>
                                    <tr><td> Majority Sediment: <b>$[sediment]</b> </td></tr>
                                    -->
                                </table>
                                <table width="250">
                                    <!--
                                    <tr><td> Shipping Density: <b>$[ais_density]</b> </td></tr>
                                    -->
                                </table>
                            </font>
                            <font size=1>created by $[user] on $[modified]</font>
                        ]]> </text>
                    </BalloonStyle>
                    <LineStyle>
                        <color>ff8B1A55</color>
                    </LineStyle>
                    <PolyStyle>
                        <color>778B1A55</color>
                    </PolyStyle>
                </Style>
            """ % (self.model_uid())

    @property
    def kml_style(self):
        return """
        <Style id="%s-default">
            <ListStyle>
                <listItemType>checkHideChildren</listItemType>
            </ListStyle>
        </Style>
        """ % (self.model_uid())

    @property
    def get_id(self):
        return self.id

    class Meta:
        abstract = True

    class Options:
        verbose_name = 'Report Name'
        icon_url = 'marco/img/multi.png'
        form = 'scenarios.forms.ScenarioForm'
        form_template = 'scenarios/form.html'
        show_template = 'scenarios/show.html'

@register
class DemoScenario(Scenario):
    # DEMO Params
    id = models.IntegerField(primary_key=True)
    input_parameter_area = models.BooleanField(verbose_name='Planning Unit Area in sq. meters', default=False)
    input_min_area = models.IntegerField(verbose_name='Minimum Planning Unit Area in sq. meters', null=True, blank=True, default=None)
    input_max_area = models.IntegerField(verbose_name='Maximum Planning Unit Area in sq. meters', null=True, blank=True, default=None)

    def serialize_attributes(self):
        attributes = []
        if self.input_parameter_area:
            # Demo dual slider
            area = '%d - %d meters<sup>2</sup>' % (self.input_min_area, self.input_max_area)
            attributes.append({'title': 'Area', 'data': area})

        if self.planning_units:
            attributes.append({'title': 'Number of Planning Units', 'data': self.planning_units.count(',')+1})
        return { 'event': 'click', 'attributes': attributes }

    def run_filters(self, result):
        if self.input_parameter_area:
            result = result.filter(geometry__area__gte=input_min_area, geometry__area__lte=input_max_area)


        return result

    class Options:
        verbose_name = 'Demo Scenario'
        # icon_url = 'marco/img/multi.png'
        form = 'scenarios.forms.DemoScenarioForm'
        form_template = 'scenarios/form.html'
        show_template = 'scenarios/show.html'

class PlanningUnit(models.Model):

    geometry = models.MultiPolygonField(srid=settings.GEOMETRY_DB_SRID, null=True, blank=True, verbose_name="Planning Unit Geometry")
    #geometry_client = models.MultiPolygonField(srid=settings.GEOMETRY_CLIENT_SRID, null=True, blank=True, verbose_name="Planning Unit Client Geometry")
    objects = GeoManager()

    @property
    def kml_done(self):
        return """
        <Placemark id="%s">
            <visibility>1</visibility>
            <styleUrl>#%s-default</styleUrl>
            %s
        </Placemark>
        """ % ( self.uid, self.model_uid(),
                asKml(self.geometry.transform( settings.GEOMETRY_CLIENT_SRID, clone=True ))
              )

    class Meta:
        abstract = True

@register
class PlanningUnitSelection(Analysis):
    palnningunit_ids = models.TextField()
    description = models.TextField(null=True, blank=True)
    geometry_actual = models.MultiPolygonField(srid=settings.GEOMETRY_DB_SRID,
        null=True, blank=True, verbose_name="Planning Unit Selection Geometry")

    def serialize_attributes(self):
        blocks = PlanningUnit.objects.filter(prot_numb__in=self.planningunit_ids.split(','))

        def mean(data):
            return sum(data) / float(len(data))

        if not blocks.exists():
            return {'event': 'click',
                    'attributes': {'title': 'Number of blocks', 'data': 0},
                    'report_values': {}}

        report_values = {
            # 'wind-speed': {
            #     'min': self.reduce(min,
            #            [b.min_wind_speed_rev for b in blocks], digits=3, offset=-0.125),
            #     'max': self.reduce(max,
            #            [b.max_wind_speed_rev for b in blocks], digits=3, offset=0.125),
            #     'avg': self.reduce(mean,
            #            [b.avg_wind_speed for b in blocks], digits=3),
            #     'selection_id': self.uid },
            #
            # 'distance-to-substation': {
            #     'min': self.reduce(min,
            #            [b.substation_min_distance for b in blocks], digits=0),
            #     'max': self.reduce(max,
            #            [b.substation_max_distance for b in blocks], digits=0),
            #     'avg': self.reduce(mean,
            #            [b.substation_mean_distance for b in blocks], digits=1),
            #     'selection_id': self.uid },
            #
            # 'distance-to-awc': {
            #     'min': self.reduce(min,
            #            [b.awc_min_distance for b in blocks], digits=0),
            #     'max': self.reduce(max,
            #            [b.awc_max_distance for b in blocks], digits=0),
            #     'avg': self.reduce(mean,
            #            [b.awc_avg_distance for b in blocks], digits=1),
            #     'selection_id': self.uid },
            #
            # 'distance-to-shipping': {
            #     'min': self.reduce(min,
            #            [b.tsz_min_distance for b in blocks], digits=0),
            #     'max': self.reduce(max,
            #            [b.tsz_max_distance for b in blocks], digits=0),
            #     'avg': self.reduce(mean,
            #            [b.tsz_mean_distance for b in blocks], digits=1),
            #     'selection_id': self.uid },
            #
            # 'distance-to-shore': {
            #     'min': self.reduce(min,
            #            [b.min_distance for b in blocks], digits=0),
            #     'max': self.reduce(max,
            #            [b.max_distance for b in blocks], digits=0),
            #     'avg': self.reduce(mean,
            #            [b.avg_distance for b in blocks], digits=1),
            #     'selection_id': self.uid },
            #
            # 'depth': {
            #     # note: accounting for the issue in which max_depth
            #     # is actually a lesser depth than min_depth
            #     'min': -1 * self.reduce(max,
            #            [b.max_distance for b in blocks], digits=0, handle_none=0),
            #     'max': -1 * self.reduce(min,
            #            [b.min_distance for b in blocks], digits=0, handle_none=0),
            #     'avg': -1 * self.reduce(mean,
            #            [b.avg_distance for b in blocks], digits=0, handle_none=0),
            #     'selection_id': self.uid }
        }

        attrs = (
            # ('Average Wind Speed Range',
            #     '%(min)s to %(max)s m/s' % report_values['wind-speed']),
            # ('Average Wind Speed',
            #     '%(avg)s m/s' % report_values['wind-speed']),
            # ('Distance to Coastal Substation',
            #     '%(min)s to %(max)s miles' % report_values['distance-to-substation']),
            # ('Average Distance to Coastal Substation',
            #      '%(avg)s miles' % report_values['distance-to-substation']),
            # ('Distance to Proposed AWC Hub',
            #     '%(min)s to %(max)s miles' % report_values['distance-to-awc']),
            # ('Average Distance to Proposed AWC Hub',
            #     '%(avg)s miles' % report_values['distance-to-awc']),
            # ('Distance to Ship Routing Measures',
            #     '%(min)s to %(max)s miles' % report_values['distance-to-shipping']),
            # ('Average Distance to Ship Routing Measures',
            #     '%(avg)s miles' % report_values['distance-to-shipping']),
            # ('Distance to Shore',
            #     '%(min)s to %(max)s miles' % report_values['distance-to-shore']),
            # ('Average Distance to Shore',
            #     '%(avg)s miles' % report_values['distance-to-shore']),
            # ('Depth',
            #     '%(min)s to %(max)s meters' % report_values['depth']),
            # ('Average Depth',
            #     '%(avg)s meters' % report_values['depth']),
            # ('Number of blocks',
            #     self.leaseblock_ids.count(',') + 1)
        )

        attributes = []
        for t, d in attrs:
            attributes.append({'title': t, 'data': d})

        return {'event': 'click',
                'attributes': attributes,
                'report_values': report_values}

    @staticmethod
    def reduce(func, data, digits=None, filter_null=True, handle_none='Unknown', offset=None):
        """
        self.reduce: PlanningUnit's custom reduce
        why not the built-in reduce()?
            handles rounding, null values, practical defaults.

        Input:
            func : function that aggregates data to a single value
            data : list of values
        Returns: a single value or a sensible default
                 with some presentation logic intermingled

        In the case of `None` in your list,
        you can either filter them out with `filter_null` (default) or
        you can bail and use `handle_none`
            which either raises an exception or returns a default "null" value

        Rounding and offsetting by constant values are also handled
        for backwards compatibility.
        """
        if filter_null:
            # Filter the incoming data to remove "nulls"
            # remove anything that is not a number
            data = [x for x in data if isinstance(x, (int, long, float, complex))]

        # Deal with any remaining None values
        if not data or None in data:
            if isinstance(handle_none, Exception):
                # We raise the exception to be handled upstream
                raise handle_none
            else:
                # bail and return the `handle_none` object
                # used for presentation or upstream logic ("Unknown", 0 or None)
                return handle_none

        # Rounding and offsetting
        agg = func(data)
        if offset:
            agg = agg + offset
        if isinstance(digits, int):
            agg = round(agg, digits)

        return agg

    def run(self):
        planningunits = PlanningUnit.objects.filter(prot_numb__in=self.planningunit_ids.split(','))

        if not planningunits.exists():
            # We can't return False, because we'll get a collection without
            # any planning units, which doesn't work on the client side.
            # Throw an exception instead.
            # TODO: Make the client handle the "selection didn't work" case.
            # This is most likely because there are no planning units in the db.
            raise Exception("No planning units available with the current selection.")

        dissolved_geom = planningunits.aggregate(Union('geometry'))
        if dissolved_geom:
            dissolved_geom = dissolved_geom['geometry__union']
        else:
            raise Exception("No planning units available with the current filters.")

        if type(dissolved_geom) == MultiPolygon:
            self.geometry_actual = dissolved_geom
        else:
            self.geometry_actual = MultiPolygon(dissolved_geom, srid=dissolved_geom.srid)
        return True

    def geojson(self, srid):
        props = get_properties_json(self)
        props['absolute_url'] = self.get_absolute_url()
        json_geom = self.geometry_actual.transform(srid, clone=True).json
        return get_feature_json(json_geom, json.dumps(props))

    class Options:
        verbose_name = 'Planning Unit Selection'
        form = 'scenarios.forms.PlanningUnitSelectionForm'
        form_template = 'selection/form.html'
        #show_template = 'scenario/show.html'
