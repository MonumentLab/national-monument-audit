'use strict';

var Map = (function() {

  function Map(config) {
    var defaults = {
      el: 'data-map',
      countEl: '#record-count',
      data: [], // pass this in
      urlTemplate: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      minZoom: 4,
      maxZoom: 18,
      startZoom: 4, // see the whole country
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      centerLatLon: [38.5767, -92.1736], // Jefferson City, MO as center
      showRecordsWithNoYear: true,
      dataUrl: 'data/locations.json'
      // searchUrl: 'https://5go2sczyy9.execute-api.us-east-1.amazonaws.com/production/search'
    };
    this.opt = _.extend({}, defaults, config);
    this.init();
  }

  Map.prototype.init = function(){

    this.mapType = 'cluster';
    this.clusterLayer = false;
    this.heatLayer = false;
    this.activeYearRange = this.opt.yearRange ? this.opt.yearRange : false;
    this.activeFacets = false;
    this.$countEl = $(this.opt.countEl);
    this.showRecordsWithNoYear = this.opt.showRecordsWithNoYear;

    // only take data with lat lon set
    this.data = _.filter(this.opt.data, function(d){
      return !isNaN(d.lat) && !isNaN(d.lon) && d.lat > -999 && d.lon > -999;
    });

    // add search id
    this.data = _.map(this.data, function(d){
      d.searchId = Util.stringToId(d.source) + '_' + d.id;
      return d;
    });

    var diff = this.opt.data.length - this.data.length;
    console.log(diff + ' records with no lat/lon');

    this.loadMap();
    this.loadListeners();
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
        var p = {q: '_id:\''+d.searchId+'\''};
        html += '<p><a href="search.html?'+$.param(p)+'" target="_blank">[View full record]</a></p>';
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

  Map.prototype.loadMap = function(){
    var opt = this.opt;
    var _this = this;

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

    // map.on('popupopen', function(e) {
    //   _this.onPopup(e.popup);
    // });

    this.refreshLayers();
  };

  Map.prototype.loadListeners = function(){
    var _this = this;

    $('input[name="map-type"]').on('change', function(e){
      _this.onChangeMapType($(this).val());
    });

    $('input[name="map-no-year"]').on('change', function(e){
      var value = $('input[name="map-no-year"]:checked').val();
      _this.onChangeMapShowNoYear((value == "yes"));
    });

    $(document).on('change-year-range', function(e, newRange) {
      _this.onChangeYearRange(newRange);
    });

    $(document).on('change-facets', function(e, newFacets) {
      _this.onChangeFacets(newFacets);
    });
  };

  Map.prototype.onChangeFacets = function(newFacets){
    this.clusterLayer = false;
    this.heatLayer = false;
    this.activeFacets = newFacets;

    this.refreshLayers();
  };

  Map.prototype.onChangeMapType = function(type){
    if (type === this.mapType) return;

    this.mapType = type;
    this.refreshLayers();
  };

  Map.prototype.onChangeMapShowNoYear = function(showRecordsWithNoYear){
    this.showRecordsWithNoYear = showRecordsWithNoYear;
    this.clusterLayer = false;
    this.heatLayer = false;
    this.refreshLayers();
  };

  Map.prototype.onChangeYearRange = function(newRange){
    this.clusterLayer = false;
    this.heatLayer = false;
    this.activeYearRange = newRange;

    this.refreshLayers();
  };

  Map.prototype.onPopup = function(p){
    var content = p.getContent();
    if (content.indexOf('Loading') < 0) return;

    var searchId = '';
    var p = {
      'q.parser': 'structured',
      'q': '_id:\''+searchId+'\''
    }
    var url = this.opt.searchUrl + '?q='
    $.getJSON(url, function(resp) {
      if (p.isOpen()) {

      }
    });
  };

  Map.prototype.refreshLayers = function(){
    var activeFacets = this.activeFacets;
    var activeYearRange = this.activeYearRange;
    var showRecordsWithNoYear = this.showRecordsWithNoYear;
    if ((activeFacets !== false || activeYearRange !== false)) {
      this.filteredData = _.filter(this.data, function(d){
        var isValid = true;
        if (!showRecordsWithNoYear) {
          if (isNaN(d.year) || d.year < 0) return false;
          // check for valid year range
          if (activeYearRange !== false) {
            isValid = d.year >= activeYearRange[0] && d.year <= activeYearRange[1];
          }
        }
        // check for valid facets
        if (isValid && activeFacets !== false) {
          isValid = Util.isValidFacetValue(d, activeFacets);
        }
        return isValid;
      });
    }

    this.featureLayer.clearLayers();
    var dataLayer;
    if (this.mapType === 'cluster') dataLayer = this.loadClusters();
    else dataLayer = this.loadHeat();
    this.featureLayer.addLayer(dataLayer);

    this.$countEl.text(Util.formatNumber(this.filteredData.length));
  };

  return Map;

})();
