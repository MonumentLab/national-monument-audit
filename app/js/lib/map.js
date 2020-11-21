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

    $.getJSON(this.opt.dataUrl, function(data){
      _this.onDataLoaded(data);
    });
  };

  Map.prototype.onDataLoaded = function(rawData){
    var opt = this.opt;

    var tiles = L.tileLayer(opt.urlTemplate, {
      minZoom: opt.minZoom,
      maxZoom: opt.maxZoom,
      attribution: opt.attribution
    });
    var latlng = L.latLng(opt.centerLatLon[0], opt.centerLatLon[1]);
    var map = L.map(opt.el, {center: latlng, zoom: opt.startZoom, layers: [tiles]});
    var markers = L.markerClusterGroup();

    var data = this.parseData(rawData);
    _.each(data, function(d){
        var marker = L.marker(new L.LatLng(d.lat, d.lon), { title: d.name });
        var html = '<h3>'+d.name+'</h3>';
        html += '<p><strong>Source:</strong> '+d.source+'</p>';
        html += '<p><strong>Year:</strong> '+d.year+'</p>';
        marker.bindPopup(html);
        markers.addLayer(marker);
    });

    map.addLayer(markers);
  };

  Map.prototype.parseData = function(rawData){
    var _this = this;
    var cols = rawData.cols;
    var data = _.map(rawData.rows, function(row){
      var obj = _.object(cols, row);
      if (rawData.groups) {
        _.each(rawData.groups, function(groupList, key){
          obj[key+'Index'] = obj[key];
          obj[key] = groupList[obj[key]];
        });
      }
      return obj;
    });
    return data;
  };

  return Map;

})();
