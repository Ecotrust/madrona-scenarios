var mapSettings = {
  getInitFilterResultsLayer: function(layerName, style) {
    if (style) {
      var defaultStyle = style;
    } else {
      var defaultStyle = new ol.style.Style({
          fill: new ol.style.Fill({color: [238,153,0, 0.5]}),
          stroke: new ol.style.Stroke({
            color:[221, 221, 221, 0.6],
            width: 1
          }),
      });
    }
    var source = new ol.source.Vector({
      projection: 'EPSG:3857',
      features: []
    });
    layer = new ol.layer.Vector({
        name: layerName,
        source: source,
        style: defaultStyle
    });
    layer.addFeatures = function(features) {
      for (var i=0; i < features.length; i++) {
        feature = features[i];
        layersource = layer.getSource();
        layersource.addFeature(feature);
      }
    }
    layer.addWKTFeatures = function(wkt) {
      var format = new ol.format.WKT();
      geometry = format.readGeometry(wkt);
      feature = format.readFeature(wkt, {
        // Re-write to take dataProjection in and determine featureProjection itself
        dataProjection: 'EPSG:3857',
        featureProjection: 'EPSG:3857'
      });
      layer.addFeatures([feature]);
    }
    layer.setVisibility = function(visibility) {
      layer.setVisible(visibility);
    }
    layer.removeAllFeatures = function() {
      var layersource = layer.getSource();
      if (layersource) {
        layersource.clear();
      }
    }
    return layer;
  },
  loadFilterLayer: function(scenarioModel) {
    var filterLayer = new ol.layer.Vector({
      source: app.planningUnitSource
    });
  }
}
