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

    _.each(this.filteredData, function(d){
        var marker = L.marker(new L.LatLng(d.lat, d.lon), { title: d.name });
        var html = '<h3>'+d.name+'</h3>';
        html += '<p><strong>Source:</strong> '+d.source+'</p>';
        var year = d.year > 0 ? d.year : 'Unknown';
        html += '<p><strong>Year:</strong> '+year+'</p>';
        marker.bindPopup(html);
        markers.addLayer(marker);
    });

    this.clusterLayer = markers;

    return markers;
  };

  Map.prototype.loadHeat = function(){
    if (this.heatLayer !== false) return this.heatLayer;

    var points = _.map(this.filteredData, function(d){ return [d.lat, d.lon]; });
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

    $(document).on('change-year-range', function(e, newRange) {
      _this.onChangeYearRange(newRange);
    });
  };

  Map.prototype.onChangeMapType = function(type){
    if (type === this.mapType) return;

    this.mapType = type;
    this.refreshLayers();
  };

  Map.prototype.onChangeYearRange = function(newRange){
    this.clusterLayer = false;
    this.heatLayer = false;

    this.filteredData = _.filter(this.data, function(d){
      if (isNaN(d.year) || d.year < 0) return false;
      return d.year >= newRange[0] && d.year <= newRange[1];
    });

    this.refreshLayers();
  };

  Map.prototype.onDataLoaded = function(rawData){
    var opt = this.opt;

    this.data = Util.parseData(rawData);
    this.filteredData = this.data.slice(0);

    // var dataWithYears = _.filter(this.data, function(d){ return !isNaN(d.year) && d.year > 0; });
    // dataWithYears = _.sortBy(dataWithYears, function(d){ return d.year; });
    // this.yearRange = [dataWithYears[0].year, dataWithYears[dataWithYears.length-1].year];

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

  Map.prototype.refreshLayers = function(){
    this.featureLayer.clearLayers();

    var dataLayer;
    if (this.mapType === 'cluster') dataLayer = this.loadClusters();
    else dataLayer = this.loadHeat();
    this.featureLayer.addLayer(dataLayer);
  };

  return Map;

})();
