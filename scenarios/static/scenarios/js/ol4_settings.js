var mapSettings = {
  getInitFilterResultsLayer: function() {
    var defaultStyle = new ol.style.Style({
        fill: new ol.style.Fill({color: [238,153,0, 0.5]}),
        stroke: new ol.style.Stroke({
          color:[221, 221, 221, 0.6],
          width: 1
        }),
    });
    // var source = new ol.source.GeoJSON({
    //   projection: 'EPSG:3857',
    // });
    layer = new ol.layer.Vector({
        // 'Current Filter Results', {
        // displayInLayerSwitcher: false,
        // source: source,
        style: defaultStyle
    });
    layer.addFeatures = function(features) {
      for (var i=0; i < features.length; i++) {
        feature = features[i];
        source.addFeature(feature);
      }
    }
    layer.setVisibility = function(visibility) {
      layer.setVisible(visibility);
    }
    return layer;
  }
}
