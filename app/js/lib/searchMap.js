'use strict';

var SearchMap = (function() {

  function SearchMap(config) {
    var defaults = {
      el: 'search-map',
      urlTemplate: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      minZoom: 4,
      maxZoom: 4,
      startZoom: 4, // see the whole country
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetSearchMap</a> contributors',
      mapCenterLat: 37.8,
      mapCenterLon: -96,
      mapWidth: 580,
      mapHeight: 320,
      onQuery: function(){ /* override me */ }
    };
    var q = Util.queryParams();
    this.opt = _.extend({}, defaults, config, q);
    this.init();
  }

  function getColor(d) {
    return d > 1000 ? '#800026' :
          d > 500  ? '#BD0026' :
          d > 200  ? '#E31A1C' :
          d > 100  ? '#FC4E2A' :
          d > 50   ? '#FD8D3C' :
          d > 20   ? '#FEB24C' :
          d > 10   ? '#FED976' : '#FFEDA0';
  }

  SearchMap.prototype.init = function(){
    this.bbox = false;
    this.$el = $('#'+this.el);
    this.$button = $('.map-query-button');

    this.loadMap();
    this.loadListeners();
  };

  SearchMap.prototype.doQuery = function(){
    if (this.bbox === false) return;
    var d = {}

    var center = this.map.getCenter();
    d.mapCenterLat = center.lat,
    d.mapCenterLon = center.lng,
    d.mapWidth = this.boxWidth;
    d.mapHeight = this.boxHeight;

    var data = {
      urlProps: d,
      latlon: this.bbox
    };
    this.opt.onQuery(data);
    this.$button.removeClass('active');
  };

  SearchMap.prototype.loadListeners = function(){
    var _this = this;

    this.$button.on('click', function(e){
      _this.doQuery();
    });
  };

  SearchMap.prototype.loadMap = function(){
    var opt = this.opt;
    var _this = this;

    var tiles = L.tileLayer(opt.urlTemplate, {
      minZoom: opt.minZoom,
      maxZoom: opt.maxZoom,
      attribution: opt.attribution
    });
    var latlng = L.latLng(parseFloat(opt.mapCenterLat), parseFloat(opt.mapCenterLon));
    var map = L.map(this.opt.el, {center: latlng, zoom: opt.startZoom, layers: [tiles]});
    this.featureLayer = new L.FeatureGroup();
    map.addLayer(this.featureLayer);

    // add legend
    var legend = L.control({position: 'bottomright'});
    legend.onAdd = function (map) {
      var div = L.DomUtil.create('div', 'info legend'),
        grades = [0, 10, 20, 50, 100, 200, 500, 1000],
        labels = [],
        from, to;
      for (var i = 0; i < grades.length; i++) {
        from = grades[i];
        to = grades[i + 1];
        labels.push(
          '<i style="background:' + getColor(from + 1) + '"></i> ' +
          from + (to ? '&ndash;' + to : '+'));
      }
      div.innerHTML = labels.join('<br>');
      return div;
    };
    legend.addTo(map);

    // add area select
    this.firstLoad = true;
    var areaSelect = L.areaSelect({width: parseInt(this.opt.mapWidth), height: parseInt(this.opt.mapHeight)});
    areaSelect.on('change', function() {
      var bounds = this.getBounds();
      var bbox = [bounds.getNorthWest().lat + ',' + bounds.getNorthWest().lng, bounds.getSouthEast().lat + ',' + bounds.getSouthEast().lng]
      _this.onChangeBounds(bbox, this._width, this._height);
    });
    areaSelect.addTo(map);
    this.areaSelect = areaSelect;

    this.map = map;
  };

  SearchMap.prototype.onChangeBounds = function(bbox, newW, newH){
    var _this = this;
    this.boxWidth = newW;
    this.boxHeight = newH;
    this.bbox = bbox;
    // console.log(bbox, newW, newH);
    if (this.firstLoad) this.firstLoad = false;
    else this.$button.addClass('active');
  };

  // https://leafletjs.com/examples/choropleth/
  SearchMap.prototype.renderResults = function(states){
    this.featureLayer.clearLayers();

    if (states.length < 1) return;

    // console.log(states)
    var statesLookup = _.object(_.map(states, function(state) { return [state.value, state.count]; }));
    var statesData = STATES_DATA;
    var features = _.map(statesData.features, function(f){
      var stateKey = false;
      if (_.has(STATE_CODES, f.id)) {
        stateKey = STATE_CODES[f.id];
      } else {
        console.log('Could not find state code for '+f.id);
        return;
      }

      var density = 0;
      if (_.has(statesLookup, stateKey)) {
        density = statesLookup[stateKey];
      }
      f.properties.density = density;
      return f;
    });
    statesData.features = features;

    var dataLayer = L.geoJson(statesData, {
      style: function(feature){
        return {
          weight: 2,
          opacity: 1,
          color: 'white',
          fillOpacity: 0.7,
          fillColor: getColor(feature.properties.density)
        };
      }
    });
    this.featureLayer.addLayer(dataLayer);
  };

  SearchMap.prototype.reset = function(){
    this.areaSelect.setDimensions({width: 580, height: 320});
    this.map.setView(L.latLng(37.8, -96));
  };

  return SearchMap;

})();
