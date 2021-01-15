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
      centerLatLon: [37.8, -96]
    };
    this.opt = _.extend({}, defaults, config);
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
    this.isLoading = false;
    this.$el = $('#'+this.el);

    this.loadMap();
    this.loadListeners();
  };

  SearchMap.prototype.loadMap = function(){
    var opt = this.opt;
    var _this = this;

    var tiles = L.tileLayer(opt.urlTemplate, {
      minZoom: opt.minZoom,
      maxZoom: opt.maxZoom,
      attribution: opt.attribution
    });
    var latlng = L.latLng(opt.centerLatLon[0], opt.centerLatLon[1]);
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

    this.map = map;
  };

  SearchMap.prototype.loadListeners = function(){
    var _this = this;

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

  return SearchMap;

})();
