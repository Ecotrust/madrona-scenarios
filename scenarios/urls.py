from django.conf.urls import url
from .views import (sdc_analysis, delete_design, get_attributes, get_scenarios,
                   get_leaseblocks, get_leaseblock_features,
                   share_design, copy_design, get_selections, ExportShapefile,
                   ExportGeoJSON, ExportWKT, ExportKML)

urlpatterns = [
    # feature reports
    # user requested sdc analysis
    url(r'sdc_report/(\d+)', sdc_analysis, name='sdc_analysis'),
    # user deletes scenario (or cancels empty geometry result)
    url(r'delete_design/(?P<uid>[\w_]+)/$', delete_design),
    # get attributes for a given scenario
    url(r'get_attributes/(?P<uid>[\w_]+)/$', get_attributes),
    url(r'get_scenarios$', get_scenarios),
    url(r'get_leaseblocks$', get_leaseblocks),
    url(r'share_design$', share_design),
    url(r'copy_design/(?P<uid>[\w_]+)/$', copy_design),
    url(r'get_selections$', get_selections),
    url(r'get_leaseblock_features$', get_leaseblock_features),

    url(r'export/shp/(?P<feature_id>[\w_]+).zip$',
        ExportShapefile.as_view(), name='export_shp'),
    url(r'export/geojson/(?P<feature_id>[\w_]+).geojson$',
        ExportGeoJSON.as_view(), name='export_geojson'),
    url(r'export/wkt/(?P<feature_id>[\w_]+)-wkt.txt',
        ExportWKT.as_view(), name='export_wkt'),
    url(r'export/kml/(?P<feature_id>[\w_]+).kml',
        ExportKML.as_view(), name='export_kml'),
]
