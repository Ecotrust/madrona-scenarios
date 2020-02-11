import datetime

from django.contrib.gis.gdal import SpatialReference
import shapefile
import io
import zipfile

def get_shp_projection(srid):
    # RDH 20200210 - two different solutions for spatialRefSys below.
    #   I implemented the 'connection' approach more recently, but if it works
    #   gdal's SpatialReference looks MUCH better
    try:
        s = SpatialReference(srid)
    except Exception as e:
        try:
            from django.db import connection
            SpatialRefSys = connection.ops.spatial_ref_sys()
            s = SpatialRefSys.objects.get(srid=srid)
        except SpatialRefSys.DoesNotExist as e2:
            return None

    return s.wkt

def zip_objects(items, compress_type=zipfile.ZIP_DEFLATED):
    """Given an array of items, write them all to a zip file (stored in memory).

    Items is an array of dictionaries:
    [{
        "timestamp": datetime.datetime(),
        "bytes": BytesIO object,
        "name": file name to use
    }, ...]

    Returns a BytesIO object containing zipped data.
    """

    zip = io.BytesIO()
    with zipfile.ZipFile(zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for item in items:
            info = zipfile.ZipInfo(item['name'], item['timestamp'])
            item['bytes'].seek(0)
            zf.writestr(info, item['bytes'].read(), compress_type=compress_type)

    zip.seek(0)
    return zip

def attrs_to_csv(attrs):
    decoded = ((attr['title'].decode('utf8'), attr['data'].decode('utf8'))
               for attr in attrs)
    lines = (u'"%s","%s"' % (k, v) for k, v in decoded)
    desc = u'\n'.join(lines)
    return desc

def attrs_to_description(attrs):
    # Note: the attributes have raw UTF8 escapes in them
    # ArcMap only seems to recognize caps HTML tags in some special HTML subset
    decoded = ((attr['title'].decode('utf8'), attr['data'].decode('utf8'))
               for attr in attrs)
    lines = ('<DIV><P>%s: %s</P></DIV>' % (k, v)
             for k, v in decoded)
    desc = u'\n'.join(lines)
    return desc

def geometries_to_shp(base_name, geom_attrs, srid=4326):
    """Produce an item dictionary file containing shp, shx, dbf, and prj files.
    base_name is the base name for the shape files.
    The item dict is for use with the zip_objects function above.

    Geometries and attributes are provided as a list of tuples in geom_attrs:
    geom_attrs = ((geom1, geom1_attrs), (geom2, geom2_attrs), ...)

    Geometries are a tuple of points (currently) assumed to be a polygon.
    Data can be generated via geodjango GEOSGeometry.tuple()

    Attributes is a dictionary of {field_name: value}
    Field type is determined based on content.
    bool -> L, logical
    str -> C, character
    int -> N, number with 0 decimal places
    float -> N, number with 4 decimal places
    datetime -> D, YYYYMMDD date stamp

    field_names and types are determined by the first attribute dictionary,
    i.e., names from from geom_attrs[0][1].keys(), and types come from examining
    geom_attrs[0][1].values()

    If srid is specified, then the geometries are transformed to that SRID prior
    to being written to the shape file. The default value is 4326; ArcMap
    doesn't seem to recognize 3857 (Web mercator) as a valid projection.
    """
    shp_bytes = io.BytesIO()
    shx_bytes = io.BytesIO()
    dbf_bytes = io.BytesIO()

    writer = shapefile.Writer(shapefile.POLYGON)

    # type_map and field_transform should be extracted
    field_data = geom_attrs[0][1]
    type_map = {
        bool: {"fieldType": "L", "size": "1"},
        str: {"fieldType": "C"},
        int: {"fieldType": "N", "size": "18", "decimal": 0},
        float: {"fieldType": "N", "size": "18", "decimal": 4},
        datetime: {"fieldType": "D", "size": 8},
    }
    try:
        str_or_unicode = unicode
        type_map[str_or_unicode] = type_map[str]
    except NameError:
        str_or_unicode = str

    for name, field_type in field_data.items():
        args = type_map[type(field_type)]
        args['name'] = name
        writer.field(**args)

    field_transform = {
        bool: lambda s: ['F', 'T'][s],
        str: lambda s: s,
        int: lambda s: str(s),
        float: lambda s: '%.4f' % s,
        datetime: lambda s: s.strftime('%Y%m%d'),
    }
    if not str_or_unicode == str:
        field_transform[str_or_unicode] = field_transform[str]

    geometry = geom_attrs[0][0]
    if not srid:
        srid = geometry.srid

    for geometry, attrs in geom_attrs:
        if srid != geometry.srid:
            geometry = geometry.transform(srid, clone=True)

        transformed_attrs = dict((k, field_transform[type(v)](v))
                         for k, v in attrs.items())

        import json
        coord_list = json.loads(geometry.geojson)['coordinates']
        # Multipolygon; shapefiles apparently support polygons with multiple
        # exterior rings, but pyshp doesn't know how to write multipolygons
        if isinstance(coord_list[0][0], list) and isinstance(coord_list[0][0][0], list):
            for poly in coord_list:
                writer.poly(parts=poly)
                writer.record(**transformed_attrs)
        else:
            writer.poly(parts=coord_list)
            writer.record(**transformed_attrs)

    writer.saveShp(shp_bytes)
    writer.saveShx(shx_bytes)
    writer.saveDbf(dbf_bytes)

    shp_bytes.seek(0)
    shx_bytes.seek(0)
    dbf_bytes.seek(0)

    now = datetime.datetime.now().timetuple()

    # Now, fetch the srtext from spatial_ref_sys and put that in the prj file.
    prj_bytes = io.StringIO()

    srtext = get_shp_projection(srid)
    prj_bytes.write(srtext)
    prj_bytes.seek(0)

    items = [
        {'name': '%s.shp' % base_name, 'timestamp': now, 'bytes': shp_bytes},
        {'name': '%s.shx' % base_name, 'timestamp': now, 'bytes': shx_bytes},
        {'name': '%s.dbf' % base_name, 'timestamp': now, 'bytes': dbf_bytes},
        {'name': '%s.prj' % base_name, 'timestamp': now, 'bytes': prj_bytes},
    ]

    return items

def create_metadata_xml(drawing, attributes, timestamp):
    try:
        description = attrs_to_description(attributes['attributes'])
    except TypeError:
        description = ''

    metadata_context = {
        'title': drawing.name,
        'description': description,
        'summary': drawing.description,
        # 'purpose': '...',
    }
    t = get_template('shape_metadata.xml')
    metadata_xml = t.render(Context(metadata_context))
    metadata_xml = metadata_xml.encode('utf8')
    metadata_xml = io.BytesIO(metadata_xml)

    return {
        "timestamp": timestamp,
        "bytes": metadata_xml,
        "name": '%s.shp.xml' % drawing.name,
    }
