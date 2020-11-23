'use strict';

var Map = (function() {

  function Map(config) {
    var defaults = {
      el: 'data-map',
      urlTemplate: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      minZoom: 4,
      maxZoom: 18,
      startZoom: 4, // see the whole country
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      centerLatLon: [38.5767, -92.1736], // Jefferson City, MO as center
      dataUrl: 'data/locations.json'
    };
    this.opt = _.extend({}, defaults, config);
    this.init();
  }

  Map.prototype.init = function(){
    var _this = this;

    this.mapType = 'cluster';
    this.clusterLayer = false;
    this.heatLayer = false;

    $.getJSON(this.opt.dataUrl, function(data){
      _this.onDataLoaded(data);
      _this.loadListeners();
    });
  };

  Map.prototype.loadClusters = function(){
    if (this.clusterLayer !== false) return this.clusterLayer;

    var markers = L.markerClusterGroup();

    _.each(this.data, function(d){
        var marker = L.marker(new L.LatLng(d.lat, d.lon), { title: d.name });
        var html = '<h3>'+d.name+'</h3>';
        html += '<p><strong>Source:</strong> '+d.source+'</p>';
        html += '<p><strong>Year:</strong> '+d.year+'</p>';
        marker.bindPopup(html);
        markers.addLayer(marker);
    });

    this.clusterLayer = markers;

    return markers;
  };

  Map.prototype.loadHeat = function(){
    if (this.heatLayer !== false) return this.heatLayer;

    var points = _.map(this.data, function(d){ return [d.lat, d.lon]; });
    var heat = L.heatLayer(points, {
      minOpacity: 0.3
    });
    this.heatLayer = heat;

    return heat;
  };

  Map.prototype.loadListeners = function(){
    var _this = this;

    $('input[name="map-type"]').on('change', function(e){
      _this.onChangeMapType($(this).val());
    });
  };

  Map.prototype.onChangeMapType = function(type){
    if (type === this.mapType) return;

    this.mapType = type;
    this.featureLayer.clearLayers();

    var dataLayer;
    if (type === 'cluster') dataLayer = this.loadClusters();
    else dataLayer = this.loadHeat();
    this.featureLayer.addLayer(dataLayer);
  };

  Map.prototype.onDataLoaded = function(rawData){
    var opt = this.opt;

    this.data = Util.parseData(rawData);

    var tiles = L.tileLayer(opt.urlTemplate, {
      minZoom: opt.minZoom,
      maxZoom: opt.maxZoom,
      attribution: opt.attribution
    });
    var latlng = L.latLng(opt.centerLatLon[0], opt.centerLatLon[1]);
    var map = L.map(opt.el, {center: latlng, zoom: opt.startZoom, layers: [tiles]});

    this.featureLayer = new L.FeatureGroup();
    map.addLayer(this.featureLayer);

    var dataLayer = this.loadClusters();
    this.featureLayer.addLayer(dataLayer);
  };

  return Map;

})();
