from django.conf.urls import url
from .views import *

urlpatterns = [
    url(r'demo', demo, name='demo'),
    # feature reports
    # user requested sdc analysis
    url(r'sdc_report/(\d+)', sdc_analysis, name='sdc_analysis'),
    # user deletes scenario (or cancels empty geometry result)
    url(r'delete_design/(?P<uid>[\w_]+)/$', delete_design),
    # get attributes for a given scenario
    url(r'get_attributes/(?P<uid>[\w_]+)/$', get_attributes),
    url(r'get_scenarios$', get_scenarios),
    url(r'get_planningunits$', get_planningunits),
    url(r'share_design$', share_design),
    url(r'copy_design/(?P<uid>[\w_]+)/$', copy_design),
    url(r'get_selections$', get_selections),
    url(r'get_planningunit_features$', get_planningunit_features),
    url(r'get_filter_count$', get_filter_count),
    url(r'get_filter_results$', get_filter_results),

    url(r'export/shp/(?P<feature_id>[\w_]+).zip$',
        ExportShapefile.as_view(), name='export_shp'),
    url(r'export/geojson/(?P<feature_id>[\w_]+).geojson$',
        ExportGeoJSON.as_view(), name='export_geojson'),
    url(r'export/wkt/(?P<feature_id>[\w_]+)-wkt.txt',
        ExportWKT.as_view(), name='export_wkt'),
    url(r'export/kml/(?P<feature_id>[\w_]+).kml',
        ExportKML.as_view(), name='export_kml'),
]
