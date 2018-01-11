class madronaMap extends ol.Map {
  getLayers() {
    return ol.Map.prototype.getLayers.call(this).getArray();
  }
  zoomToExtent(extent) {
    ol.Map.prototype.getView.call(this).fit(extent, {duration: 1500});
  }
}

app.setLayerZIndex = function(layer, index) {
    layer.layer.setZIndex(index);
};

app.updateUrl = function () {
  if (app.getState) {
    var state = app.getState();

    // save the restore state
    if (app.saveStateMode) {
      app.restoreState = state;
    }
    window.location.hash = $.param(state);
    app.viewModel.currentURL(window.location.pathname + window.location.hash);
  }
};

var mapSettings = {
  getInitMap: function() {
    map = new madronaMap({
      layers: [
        new ol.layer.Tile({
          source: new ol.source.OSM(),
          name: 'OSM Base Layer'
        }),
        // app.planningUnitsLayer,
        // app.scenariosLayer
      ],
      target: 'map',
      view: new ol.View({
        center: [0, 0],
        zoom: 2
      })
    });
    // map.addLayer = function(layer) {}
    return map
  },
  configureLayer: function(layer) {
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
    layer.addGeoJSONFeatures = function(geojson_features) {
      layer.addFeatures(new ol.format.GeoJSON().readFeatures(geojson_features));
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
    layer.getDataExtent = function() {
      return this.getSource().getExtent();
    }
    return layer;
  },
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
    layer = mapSettings.configureLayer(layer);

    return layer;
  },
  loadFilterLayer: function(scenarioModel) {
    var filterLayer = new ol.layer.Vector({
      source: app.planningUnitSource
    });
  }
}
