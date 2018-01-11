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
from django.contrib.gis.db.models.aggregates import Union
from django.utils.html import escape
# import mapnik
from picklefield import PickledObjectField

@register
class Scenario(Analysis):

    description = models.TextField(null=True, blank=True)
    satisfied = models.BooleanField(default=True)
    active = models.BooleanField(default=True)

    #I'm finding myself wishing lease_blocks was spelled without the underscore...
    planning_units = models.TextField(verbose_name='Planning Unit IDs', null=True, blank=True)
    geometry_final_area = models.FloatField(verbose_name='Total Area', null=True, blank=True)
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

    def run(self):
        result = PlanningUnit.objects.all()

        # PU Filtration occurs here
        result = self.run_filters(result)

        dissolved_geom = result.aggregate(Union('geometry'))

        if dissolved_geom:
            dissolved_geom = dissolved_geom['geometry__union']
        else:
            raise Exception("No planning units available with the current filters.")

        if type(dissolved_geom) == MultiPolygon:
            self.geometry_dissolved = dissolved_geom
        else:
            self.geometry_dissolved = MultiPolygon(dissolved_geom,
                                                   srid=dissolved_geom.srid)

        self.active = True

        self.geometry_final_area = self.geometry_dissolved.area
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
        # if rerun is None and self.pk is None:
        #     rerun = True
        # if rerun is None and self.pk is not None: #if editing a scenario and no value for rerun is given
        #     rerun = False
        #     if not rerun:
        #         # try:
        #         #     self.save()
        #         #     orig = Scenario.objects.get(pk=self.pk)
        #         # except:
        #         #     import ipdb
        #         #     ipdb.set_trace()
        #
        #         rerun = True
        #
        #         # if not rerun:
        #         #     for f in Scenario.input_fields():
        #         #         # Is original value different from form value?
        #         #         if getattr(orig, f.name) != getattr(self, f.name):
        #         #             #print('input_field, %s, has changed' %f.name)
        #         #             rerun = True
        #         #             break
        #         # if not rerun:
        #         #     '''
        #         #         the substrates need to be grabbed, then saved, then grabbed again because
        #         #         both getattr calls (orig and self) return the same original list until the model has been saved
        #         #         (perhaps because form.save_m2m has to be called), after which calls to getattr will
        #         #         return the same list (regardless of whether we use orig or self)
        #         #     '''
        #         #     orig_weas = set(getattr(self, 'input_wea').all())
        #         #     orig_substrates = set(getattr(self, 'input_substrate').all())
        #         #     orig_sediments = set(getattr(self, 'input_sediment').all())
        #         #     super(Scenario, self).save(rerun=False, *args, **kwargs)
        #         #     new_weas = set(getattr(self, 'input_wea').all())
        #         #     new_substrates = set(getattr(self, 'input_substrate').all())
        #         #     new_sediments = set(getattr(self, 'input_sediment').all())
        #         #     if orig_substrates != new_substrates or orig_sediments != new_sediments or orig_weas != new_weas:
        #         #         rerun = True
        #     super(Scenario, self).save(rerun=rerun, *args, **kwargs)
        # else: #editing a scenario and rerun is provided
        #     super(Scenario, self).save(rerun=rerun, *args, **kwargs)

    def __unicode__(self):
        return u'%s' % self.name

    def support_filename(self):
        return os.path.basename(self.support_file.name)

    @classmethod
    def mapnik_geomfield(self):
        return "output_geom"

    # @classmethod
    # def mapnik_style(self):
    #     polygon_style = mapnik.Style()
    #
    #     ps = mapnik.PolygonSymbolizer(mapnik.Color('#ffffff'))
    #     ps.fill_opacity = 0.5
    #
    #     ls = mapnik.LineSymbolizer(mapnik.Color('#555555'),0.75)
    #     ls.stroke_opacity = 0.5
    #
    #     r = mapnik.Rule()
    #     r.symbols.append(ps)
    #     r.symbols.append(ls)
    #     polygon_style.rules.append(r)
    #     return polygon_style

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

    # @property
    # def input_wea_names(self):
    #     return [wea.wea_name for wea in self.input_wea.all()]
    #
    # @property
    # def input_substrate_names(self):
    #     return [substrate.substrate_name for substrate in self.input_substrate.all()]
    #
    # @property
    # def input_sediment_names(self):
    #     return [sediment.sediment_name for sediment in self.input_sediment.all()]

    #TODO: is this being used...?  Yes, see show.html
    # @property
    # def has_wind_energy_criteria(self):
    #     wind_parameters = Scenario.input_parameter_fields()
    #     for wp in wind_parameters:
    #         if getattr(self, wp.name):
    #             return True
    #     return False
    #
    # @property
    # def has_shipping_filters(self):
    #     shipping_filters = Scenario.input_filter_fields()
    #     for sf in shipping_filters:
    #         if getattr(self, sf.name):
    #             return True
    #     return False
    #
    # @property
    # def has_military_filters(self):
    #     return False

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

    class Options:
        verbose_name = 'Report Name'
        icon_url = 'marco/img/multi.png'
        form = 'scenarios.forms.ScenarioForm'
        form_template = 'scenarios/form.html'
        show_template = 'scenarios/show.html'

    #no longer needed? Used in 'color'
    # class Objective(models.Model):
    #     name = models.CharField(max_length=35)
    #     color = models.CharField(max_length=8, default='778B1A55')
    #
    #     def __unicode__(self):
    #         return u'%s' % self.name

    #no longer needed?
    # class Parameter(models.Model):
    #     ordering_id = models.IntegerField(null=True, blank=True)
    #     name = models.CharField(max_length=35, null=True, blank=True)
    #     shortname = models.CharField(max_length=35, null=True, blank=True)
    #     objectives = models.ManyToManyField("Objective", null=True, blank=True)
    #
    #     def __unicode__(self):
    #         return u'%s' % self.name

@register
class DemoScenario(Scenario):
    # DEMO Params
    input_parameter_area = models.BooleanField(verbose_name='Planning Unit Area in sq. meters', default=False)
    input_min_area = models.IntegerField(verbose_name='Minimum Planning Unit Area in sq. meters', null=True, blank=True, default=None)
    input_max_area = models.IntegerField(verbose_name='Maximum Planning Unit Area in sq. meters', null=True, blank=True, default=None)

    #Input Parameters
    #input_objectives = models.ManyToManyField("Objective")
    #input_parameters = models.ManyToManyField("Parameter")
    #input_dist_port = models.FloatField(verbose_name='Distance to Port')
    #GeoPhysical
    # input_parameter_depth = models.BooleanField(verbose_name='Depth Parameter', default=False)
    # input_min_depth = models.FloatField(verbose_name='Minimum Depth', null=True, blank=True)
    # input_max_depth = models.FloatField(verbose_name='Maximum Depth', null=True, blank=True)
    #
    # input_parameter_distance_to_shore = models.BooleanField(verbose_name='Distance to Shore', default=False)
    # input_min_distance_to_shore = models.FloatField(verbose_name='Minimum Distance to Shore', null=True, blank=True)
    # input_max_distance_to_shore = models.FloatField(verbose_name='Maximum Distance to Shore', null=True, blank=True)
    #
    # input_parameter_substrate = models.BooleanField(verbose_name='Substrate Parameter', default=False)
    # input_substrate = models.ManyToManyField('Substrate', null=True, blank=True)
    #
    # input_parameter_sediment = models.BooleanField(verbose_name='Sediment Parameter', default=False)
    # input_sediment = models.ManyToManyField('Sediment', null=True, blank=True)
    #
    # #Wind Energy
    #
    # input_parameter_wind_speed = models.BooleanField(verbose_name='Wind Speed Parameter', default=False)
    # input_avg_wind_speed = models.FloatField(verbose_name='Average Wind Speed', null=True, blank=True)
    #
    # input_parameter_distance_to_awc = models.BooleanField(verbose_name='Distance to AWC Station', default=False)
    # input_distance_to_awc = models.FloatField(verbose_name='Maximum Distance to AWC Station', null=True, blank=True)
    #
    # input_parameter_distance_to_substation = models.BooleanField(verbose_name='Distance to Coastal Substation', default=False)
    # input_distance_to_substation = models.FloatField(verbose_name='Maximum Distance to Coastal Substation', null=True, blank=True)
    #
    # input_parameter_wea = models.BooleanField(verbose_name='WEA Parameter', default=False)
    # input_wea = models.ManyToManyField('WEA', null=True, blank=True)
    #
    # #Shipping
    #
    # input_filter_ais_density = models.BooleanField(verbose_name='Excluding Areas with AIS Density >= 1', default=False)
    # #input_ais_density = models.FloatField(verbose_name='Mean AIS Density', null=True, blank=True)
    #
    # input_filter_distance_to_shipping = models.BooleanField(verbose_name='Distance to Ship Routing Measures', default=False)
    # input_distance_to_shipping = models.FloatField(verbose_name='Minimum Distance to Ship Routing Measures', null=True, blank=True)
    #
    # #Security
    #
    # input_filter_uxo = models.BooleanField(verbose_name='Excluding Areas with UXO', default=False)
    #
    #Descriptors (name field is inherited from Analysis)

    def serialize_attributes(self):
        attributes = []
        if self.input_parameter_area:
            # Demo dual slider
            area = '%d - %d meters<sup>2</sup>' % (self.input_min_area, self.input_max_area)
            attributes.append({'title': 'Area', 'data': area})

        # if self.input_parameter_wind_speed:
        #     wind_speed = '%.1f m/s' % (self.input_avg_wind_speed)
        #     attributes.append({'title': 'Minimum Average Wind Speed', 'data': wind_speed})
        # if self.input_parameter_distance_to_shore:
        #     distance_to_shore = '%.0f - %.0f miles' % (self.input_min_distance_to_shore,
        #                                                self.input_max_distance_to_shore)
        #     attributes.append({'title': 'Distance to Shore', 'data': distance_to_shore})
        # if self.input_parameter_depth:
        #     depth_range = '%.0f - %.0f meters' %(self.input_min_depth, self.input_max_depth)
        #     attributes.append({'title': 'Depth Range', 'data': depth_range})
        # if self.input_parameter_distance_to_awc:
        #     distance_to_awc = '%.0f miles' % (self.input_distance_to_awc)
        #     attributes.append({'title': 'Max Distance to Proposed AWC Hub', 'data': distance_to_awc})
        # if self.input_parameter_distance_to_substation:
        #     distance_to_substation = '%.0f miles' % (self.input_distance_to_substation)
        #     attributes.append({'title': 'Max Distance to Coastal Substation', 'data': distance_to_substation})
        # if self.input_filter_distance_to_shipping:
        #     miles_to_shipping = round(self.input_distance_to_shipping, 0)
        #     if miles_to_shipping == 1:
        #         distance_to_shipping = '%s mile' %miles_to_shipping
        #     else:
        #         distance_to_shipping = '%s miles' %miles_to_shipping
        #     attributes.append({'title': 'Minimum Distance to Ship Routing Measures', 'data': distance_to_shipping})
        # if self.input_filter_ais_density:
        #     attributes.append({'title': 'Excluding Areas with Moderate or High Ship Traffic', 'data': ''})
        # if self.input_filter_uxo:
        #     attributes.append({'title': 'Excluding Areas with Unexploded Ordnances', 'data': ''})

        if self.planning_units:
            attributes.append({'title': 'Number of Planning Units', 'data': self.planning_units.count(',')+1})
        return { 'event': 'click', 'attributes': attributes }

    def run_filters(self, result):
        if self.input_parameter_area:
            result = result.filter(geometry__area__gte=input_min_area, geometry__area__lte=input_max_area)

        # if self.input_parameter_distance_to_shore:
        #     #why isn't this max_distance >= input.min_distance && min_distance <= input.max_distance ???
        #     result = result.filter(avg_distance__gte=self.input_min_distance_to_shore, avg_distance__lte=self.input_max_distance_to_shore)
        # if self.input_parameter_depth:
        #     #note:  converting input to negative values and converted to meters (to match db)
        #     input_min_depth = -self.input_min_depth
        #     input_max_depth = -self.input_max_depth
        #     #result = result.filter(min_depth__lte=input_min_depth, max_depth__gte=input_max_depth)
        #     result = result.filter(avg_depth__lte=input_min_depth, avg_depth__gte=input_max_depth)
        #     result = result.filter(avg_depth__lt=0) #not sure this is doing anything, but do want to ensure 'no data' values are not included
        # '''
        # if self.input_parameter_substrate:
        #     input_substrate = [s.substrate_name for s in self.input_substrate.all()]
        #     result = result.filter(majority_seabed__in=input_substrate)
        # if self.input_parameter_sediment:
        #     input_sediment = [s.sediment_name for s in self.input_sediment.all()]
        #     result = result.filter(majority_sediment__in=input_sediment)
        # '''
        # #Wind Energy
        # if self.input_parameter_wind_speed:
        #     #input_wind_speed = mph_to_mps(self.input_avg_wind_speed)
        #     result = result.filter(min_wind_speed_rev__gte=self.input_avg_wind_speed)
        # if self.input_parameter_wea:
        #     input_wea = [wea.wea_id for wea in self.input_wea.all()]
        #     result = result.filter(wea_number__in=input_wea)
        # if self.input_parameter_distance_to_awc:
        #     result = result.filter(awc_min_distance__lte=self.input_distance_to_awc)
        # if self.input_parameter_distance_to_substation:
        #     result = result.filter(substation_min_distance__lte=self.input_distance_to_substation)
        # #Shipping
        # if self.input_filter_ais_density:
        #     result = result.filter(ais_all_vessels_maj__lte=1)
        # if self.input_filter_distance_to_shipping:
        #     result = result.filter(tsz_min_distance__gte=self.input_distance_to_shipping)
        # #Security
        # if self.input_filter_uxo:
        #     result = result.filter(uxo=0)

        return result

    class Options:
        verbose_name = 'Demo Scenario'
        # icon_url = 'marco/img/multi.png'
        form = 'scenarios.forms.DemoScenarioForm'
        form_template = 'scenarios/form.html'
        show_template = 'scenarios/show.html'

class PlanningUnit(models.Model):
    # prot_number = models.CharField(max_length=7, null=True, blank=True)
    # prot_aprv = models.CharField(max_length=11, null=True, blank=True)
    # block_number = models.CharField(max_length=6, null=True, blank=True)
    # prot_numb = models.CharField(max_length=15, null=True, blank=True)
    #
    # min_depth = models.FloatField()
    # max_depth = models.FloatField()
    # avg_depth = models.FloatField()
    #
    # min_wind_speed = models.FloatField()
    # max_wind_speed = models.FloatField()
    #
    # majority_sediment = models.CharField(max_length=35, null=True, blank=True)  #LeaseBlock Update: might change back to IntegerField
    # variety_sediment = models.IntegerField()
    #
    # majority_seabed = models.CharField(max_length=35, null=True, blank=True) #LeaseBlock Update: might change back to IntegerField
    # variety_seabed = models.IntegerField(null=True, blank=True)
    #
    # min_distance = models.FloatField(null=True, blank=True)
    # max_distance = models.FloatField(null=True, blank=True)
    # avg_distance = models.FloatField(null=True, blank=True)
    #
    # awc_min_distance = models.FloatField(null=True, blank=True)
    # awc_max_distance = models.FloatField(null=True, blank=True)
    # awc_avg_distance = models.FloatField(null=True, blank=True)
    #
    # wea_number = models.IntegerField(null=True, blank=True)
    # wea_name = models.CharField(max_length=10, null=True, blank=True)
    #
    # ais_all_vessels_maj = models.IntegerField(null=True, blank=True)
    # ais_all_vessels_low = models.FloatField(null=True, blank=True)
    # ais_all_vessels_medium = models.FloatField(null=True, blank=True)
    # ais_all_vessels_high = models.FloatField(null=True, blank=True)
    # ais_cargo_vessels_maj = models.IntegerField(null=True, blank=True)
    # ais_cargo_vessels_low = models.FloatField(null=True, blank=True)
    # ais_cargo_vessels_medium = models.FloatField(null=True, blank=True)
    # ais_cargo_vessels_high = models.FloatField(null=True, blank=True)
    # ais_passenger_vessels_maj = models.IntegerField(null=True, blank=True)
    # ais_passenger_vessels_low = models.FloatField(null=True, blank=True)
    # ais_passenger_vessels_medium = models.FloatField(null=True, blank=True)
    # ais_passenger_vessels_high = models.FloatField(null=True, blank=True)
    # ais_tanker_vessels_maj = models.IntegerField(null=True, blank=True)
    # ais_tanker_vessels_low = models.FloatField(null=True, blank=True)
    # ais_tanker_vessels_medium = models.FloatField(null=True, blank=True)
    # ais_tanker_vessels_high = models.FloatField(null=True, blank=True)
    # ais_tugtow_vessels_maj = models.IntegerField(null=True, blank=True)
    # ais_tugtow_vessels_low = models.FloatField(null=True, blank=True)
    # ais_tugtow_vessels_medium = models.FloatField(null=True, blank=True)
    # ais_tugtow_vessels_high = models.FloatField(null=True, blank=True)
    #
    # min_wind_speed_rev = models.FloatField(null=True, blank=True)
    # max_wind_speed_rev = models.FloatField(null=True, blank=True)
    #
    # tsz_min_distance = models.FloatField(null=True, blank=True)
    # tsz_max_distance = models.FloatField(null=True, blank=True)
    # tsz_mean_distance = models.FloatField(null=True, blank=True)
    #
    # lace_coral_count = models.IntegerField(null=True, blank=True)
    # lace_coral_name = models.CharField(max_length=50, null=True, blank=True)
    # black_coral_count = models.IntegerField(null=True, blank=True)
    # black_coral_name = models.CharField(max_length=50, null=True, blank=True)
    # soft_coral_count = models.IntegerField(null=True, blank=True)
    # soft_coral_name = models.CharField(max_length=50, null=True, blank=True)
    # gorgo_coral_count = models.IntegerField(null=True, blank=True)
    # gorgo_coral_name = models.CharField(max_length=50, null=True, blank=True)
    # sea_pen_count = models.IntegerField(null=True, blank=True)
    # sea_pen_name = models.CharField(max_length=50, null=True, blank=True)
    # hard_coral_count = models.IntegerField(null=True, blank=True)
    # hard_coral_name = models.CharField(max_length=50, null=True, blank=True)
    #
    # seabed_depression = models.FloatField(null=True, blank=True)
    # seabed_low_slope = models.FloatField(null=True, blank=True)
    # seabed_steep = models.FloatField(null=True, blank=True)
    # seabed_mid_flat = models.FloatField(null=True, blank=True)
    # seabed_side_slow = models.FloatField(null=True, blank=True)
    # seabed_high_flat = models.FloatField(null=True, blank=True)
    # seabed_high_slope = models.FloatField(null=True, blank=True)
    # seabed_total = models.FloatField(null=True, blank=True)
    #
    # discharge_min_distance = models.FloatField(null=True, blank=True)
    # discharge_max_distance = models.FloatField(null=True, blank=True)
    # discharge_mean_distance = models.FloatField(null=True, blank=True)
    # discharge_flow_min_distance = models.FloatField(null=True, blank=True)
    # discharge_flow_max_distance = models.FloatField(null=True, blank=True)
    # discharge_flow_mean_distance = models.FloatField(null=True, blank=True)
    #
    # dredge_site = models.IntegerField(null=True, blank=True)
    #
    # wpa = models.IntegerField(null=True, blank=True)
    # wpa_name = models.CharField(max_length=75, null=True, blank=True)
    #
    # shipwreck_density = models.IntegerField(null=True, blank=True)
    #
    # uxo = models.IntegerField(null=True, blank=True)
    #
    # substation_min_distance = models.FloatField(null=True, blank=True)
    # substation_max_distance = models.FloatField(null=True, blank=True)
    # substation_mean_distance = models.FloatField(null=True, blank=True)
    #
    # marco_region = models.IntegerField(null=True, blank=True)

    geometry = models.MultiPolygonField(srid=settings.GEOMETRY_DB_SRID, null=True, blank=True, verbose_name="Planning Unit Geometry")
    #geometry_client = models.MultiPolygonField(srid=settings.GEOMETRY_CLIENT_SRID, null=True, blank=True, verbose_name="Planning Unit Client Geometry")
    objects = models.GeoManager()

    # @property
    # def avg_wind_speed(self):
    #     try:
    #         return (self.min_wind_speed_rev + self.max_wind_speed_rev) / 2.0
    #     except:
    #         return None
    #
    # @property
    # def substrate(self):
    #     try:
    #         return Substrate.objects.get(substrate_id=self.majority_seabed).substrate_name
    #     except:
    #         return 'Unknown'
    #
    # @property
    # def sediment(self):
    #     try:
    #         return Sediment.objects.get(sediment_name=self.majority_sediment).sediment_output
    #     except:
    #         return 'Unknown'
    #
    # @property
    # def wea_label(self):
    #     if self.wea_name is None:
    #         return ""
    #     else:
    #         return "Wind Energy Area: "
    #
    # @property
    # def wea_state_name(self):
    #     if self.wea_name is None:
    #         return ""
    #     else:
    #         return self.wea_name
    #
    # @property
    # def wind_speed_output(self):
    #     if self.min_wind_speed == self.max_wind_speed:
    #         return "%.1f mph" % (mps_to_mph(self.min_wind_speed))
    #     else:
    #         return "%.1f - %.1f mph" % (mps_to_mph(self.min_wind_speed),
    #                                     mps_to_mph(self.max_wind_speed))
    #
    # @property
    # def ais_density(self):
    #     if self.ais_all_vessels_maj <= 1:
    #         return 'Low'
    #     else:
    #         return 'Moderate/High'
    #
    # @property
    # def depth_range_output(self):
    #     if self.min_depth == self.max_depth:
    #         return "$.0f meters" % (-self.min_depth)
    #     else:
    #         return "%.0f - %.0f meters" % (-self.min_depth, -self.max_depth)

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
#
# #still needed?
# class Substrate(models.Model):
#     substrate_id = models.IntegerField()
#     substrate_name = models.CharField(max_length=35)
#     substrate_shortname = models.CharField(max_length=35)
#
#     def __unicode__(self):
#         return u'%s' % self.substrate_name
# #still needed?
# class Sediment(models.Model):
#     sediment_id = models.IntegerField()
#     sediment_name = models.CharField(max_length=35)
#     sediment_output = models.CharField(max_length=55)
#     sediment_shortname = models.CharField(max_length=35)
#
#     def __unicode__(self):
#         return u'%s' % self.sediment_output
# #still needed?
# class WEA(models.Model):
#     wea_id = models.IntegerField()
#     wea_name = models.CharField(max_length=35)
#     wea_shortname = models.CharField(max_length=35)
#
#     def __unicode__(self):
#         return u'%s' % self.wea_name

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
