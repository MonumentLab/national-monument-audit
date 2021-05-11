'use strict';

var STATE_CODES = {"01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO", "09": "CT", "10": "DE", "11": "DC", "12": "FL", "13": "GA", "15": "HI", "16": "ID", "17": "IL", "18": "IN", "19": "IA", "20": "KS", "21": "KY", "22": "LA", "23": "ME", "24": "MD", "25": "MA", "26": "MI", "27": "MN", "28": "MS", "29": "MO", "30": "MT", "31": "NE", "32": "NV", "33": "NH", "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND", "39": "OH", "40": "OK", "41": "OR", "42": "PA", "44": "RI", "45": "SC", "46": "SD", "47": "TN", "48": "TX", "49": "UT", "50": "VT", "51": "VA", "53": "WA", "54": "WV", "55": "WI", "56": "WY", "60": "AS", "64": "FM", "66": "GU", "67": "JA", "68": "MH", "69": "MP", "70": "PW", "72": "PR", "74": "UM", "76": "NI", "78": "VI", "81": "BI", "86": "JI", "89": "KR"};

var Map = (function() {

  function Map(config) {
    var defaults = {
      // search values
      'endpoint': 'https://5go2sczyy9.execute-api.us-east-1.amazonaws.com/production/search',
      'returnFacets': ['object_groups', 'source', 'subjects', 'state', 'year_dedicated_or_constructed', 'county_geoid'], // note if these are changed, you must also update the allowed API Gateway queryParams for facet.X and redeploy the API
      'facetLabels': {
        'entities_people': 'People',
        'entities_events': 'Events'
      },
      'returnValues': 'name,latlon,city,state,source,url,image',
      'facetSize': 100,
      'customFacetSizes': {
        'county_geoid': 4000
      },
      'start': 0,
      'size': 500,
      'sort': '',
      'fields': '', // e.g. name,street_address
      'q': '',
      'facets': 'object_groups~Monument', // e.g. facetName1~value1!!value2!!value3__facetName2~value1

      // map values
      'mapEl': 'search-map',
      'tileUrlTemplate': 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      'minZoom': 4,
      'maxZoom': 18,
      'startZoom': 5, // see the whole country
      'attribution': '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      'centerLatLon': "38.5767,-92.1736", // Jefferson City, MO as center
      'nominatimUrl': 'https://nominatim.openstreetmap.org/search?q={q}&format=json',
      'countyData': 'data/counties.json'
    };
    var q = Util.queryParams();
    this.defaults = _.extend({}, defaults);
    this.opt = _.extend({}, defaults, config, q);
    this.init();
  }

  // e.g. facets=facetName1~value1!!value2!!value3__facetName2~value1
  function facetStringToObject(string){
    if (!string || !string.length) return {};

    var pairs = _.map(string.split('__'), function(str){
      var pair = str.split('~');
      var facetName = pair[0];
      var facetValues = pair[1].split('!!');
      return [facetName, facetValues];
    });
    return _.object(pairs);
  }

  function isArrayString(value) {
    var returnValue = false;
    if (typeof value === 'string' || value instanceof String) {
      if (value.startsWith('[')) returnValue = true;
    }
    return returnValue;
  }

  Map.prototype.init = function(){
    var isValid = Auth.authenticate();
    if (isValid) this.load();
  };

  Map.prototype.countyInfoOn = function(e){
    var layer = e.target;
    layer.setStyle({
      weight: 2,
      opacity: 1
    });
    this.countyInfoLayer.update(layer.feature.properties);
  };

  Map.prototype.countyInfoOff = function(e){
    e.target.setStyle({
      weight: 1,
      opacity: 0.4
    });
    this.countyInfoLayer && this.countyInfoLayer.update();
  };

  Map.prototype.getQueryObject = function(){
    var queryText = this.$query.val().trim();
    var facetSize = this.opt.facetSize;
    var customFacetSizes = this.opt.customFacetSizes;
    var q = {
      q: queryText,
      size: this.size
    };
    if (this.start > 0) q.start = this.start;
    if (this.sort && this.sort.length) q.sort = this.sort;
    var facets = _.clone(this.facets);
    facets = _.omit(facets, function(values, key) {
      return values.length < 1;
    });
    var isEmptyQuery = queryText.length < 1;
    var isEmptyFacets = _.isEmpty(facets);

    // individual document search
    if (isEmptyQuery && isEmptyFacets) {
      q.q = 'matchall';
      q['q.parser'] = 'structured';

    } else {
      // build filter string
      if (!isEmptyFacets) {
        // e.g. (and title:'star' (or actors:'Harrison Ford' actors:'William Shatner'))
        var fqstring = '(and ';
        var filterString = _.map(facets, function(values, key){
          if (values.length === 1) {
            if (isNaN(values[0]) && !isArrayString(values[0])) {
              return key + ":'" + values[0] + "'";
            } else {
              return key + ":" + values[0];
            }
          } else {
            var orString = '(or ';
            var orValuesString = _.map(values, function(value){
              if (isNaN(value) && !isArrayString(value)) {
                return key + ":'" + value + "'";
              } else {
                return key + ":" + value;
              }
            });
            orValuesString = orValuesString.join(' ');
            orString += orValuesString + ')';
            return orString;
          }
        });
        filterString = filterString.join(' ');
        fqstring += filterString + ')';

        if (isEmptyQuery) {
          q.q = fqstring;
          q['q.parser'] = 'structured';
        } else {
          q.fq = fqstring;
        }
      }

      // build search fields string
      if (!isEmptyQuery) {
        var fieldsString = $('.field-checkbox:checked').map(function(){
          var $input = $(this);
          var fstring = "'" + $input.val();
          var boost = $input.attr('data-boost');
          if (boost && boost.length) fstring += '^' + boost;
          fstring += "'";
          return fstring;
        }).get();
        fieldsString = fieldsString.join(',');
        q['q.options'] = '{fields: ['+fieldsString+']}';
      }
    }

    // build facet string
    var facetString = _.each(this.opt.returnFacets, function(facet){
      var _size = facetSize;
      if (_.has(customFacetSizes, facet)) _size = customFacetSizes[facet];
      q['facet.'+facet] = '{sort:\'count\', size:'+_size+'}';
    });

    q['return'] = this.opt.returnValues;

    console.log('Query object: ', q);

    return q;
  };

  Map.prototype.getQueryString = function(){
    var q = this.getQueryObject();
    var qstring = $.param(q);
    return qstring;
  };

  Map.prototype.load = function(){
    var _this = this;

    this.isLoading = true;
    this.$form = $('#search-form');
    this.$facets = $('#facets');
    this.$results = $('#search-results');
    this.$sort = $('#search-sort-select');
    this.$resultMessage = $('#search-results-message');
    this.$pagination = $('#search-results-pagination');
    this.$query = $('input[name="query"]').first();
    this.facets = {};
    this.size = parseInt(this.opt.size);
    this.start = parseInt(this.opt.start);
    this.sort = this.opt.sort;
    this.centerLatLon = _.map(this.opt.centerLatLon.split(","), function(v){ return parseFloat(v); } );
    this.zoomLevel = this.opt.startZoom;
    this.countyDataLayer = false;
    this.countyInfoLayer = false;
    this.markerLayer = false;
    this.mapData = false;
    this.countyCounts = {};

    this.loadOptions();
    var mapLoaded = this.loadMap();
    var countiesLoaded = this.loadCounties();

    $.when(mapLoaded, countiesLoaded).done(function(){
      console.log('Ready.');
      _this.loadListeners();
      _this.query();
    });
  };

  Map.prototype.loadCounties = function(){
    var _this = this;
    var promise = $.Deferred();

    $.getJSON(this.opt.countyData, function(data) {
      console.log('Loaded county data');
      _this.countyData = data;
      promise.resolve();
    });

    return promise;
  };

  Map.prototype.loadListeners = function(){
    var _this = this;

    $('.panel .toggle-parent').on('click', function(){
      _this.onResize();
    });

    this.$form.on('submit', function(e){
      e.preventDefault();
      _this.onSearchSubmit();
    });

    this.map.on('moveend', function(e){
      var latlon = _this.map.getCenter();
      _this.centerLatLon = [latlon.lat, latlon.lng];
      _this.updateURL();
    });

    this.map.on('zoomend', function(e){
      var latlon = _this.map.getCenter();
      _this.zoomLevel = _this.map.getZoom();
      _this.centerLatLon = [latlon.lat, latlon.lng];
      _this.updateURL();
    });

    $('body').on('click', '.remove-facet', function(e){
      var $el = $(this);
      var key = $el.attr('data-key');
      var value = $el.attr('data-value');
      _this.removeFacet(key, value);
    });

    $('body').on('click', '.reset-query', function(e){
      _this.resetQuery();
    });

    $('body').on('change', '.facet-select', function(e){
      // _this.onFacetCheckboxChange($(this));
      _this.updateFacets();
    });
  };

  Map.prototype.loadMap = function(){
    var _this = this;
    var promise = $.Deferred();
    var opt = this.opt;
    var tiles = L.tileLayer(opt.tileUrlTemplate, {
      minZoom: opt.minZoom,
      maxZoom: opt.maxZoom,
      attribution: opt.attribution
    });
    var latlng = L.latLng(this.centerLatLon[0], this.centerLatLon[1]);
    var map = L.map(opt.mapEl, {center: latlng, zoom: this.zoomLevel, layers: [tiles]});

    this.featureLayer = new L.FeatureGroup();
    map.addLayer(this.featureLayer);
    this.map = map;
    map.on('popupopen', function(e) {
      _this.onPopup(e.popup);
    });

    // control that shows county info on hover
    var info = L.control();
    info.onAdd = function (map) {
      this._div = L.DomUtil.create('div', 'info');
      this.update();
      return this._div;
    };
    info.update = function (props) {
      if (!props) {
        // this._div.innerHTML = '<h4>Hover over a county</h4>';
        this._div.style.display = 'none';
        return;
      }
      this._div.style.display = '';
      var countyName = props.NAME + ' County';
      var state = _.has(STATE_CODES, props.STATEFP) ? STATE_CODES[props.STATEFP] : '??';
      var countyId = props.GEOID;
      var count = 0;
      if (_.has(_this.countyCounts, countyId)) count = _this.countyCounts[countyId];

      var html = '<h4>' + countyName + ', ' + state + ': </h4>';
      html += '<p>' + Util.formatNumber(count) + ' entries</p>'
      this._div.innerHTML = html;
    };
    info.addTo(map);
    this.countyInfoLayer = info;

    console.log('Loaded map');
    promise.resolve();
    return promise;
  };

  Map.prototype.loadOptions = function(){
    var q = this.opt.q.trim();
    this.$query.val(q);
    this.$sort.val(this.sort);

    // select specific fields to search in
    if (this.opt.fields && this.opt.fields.length) {
      var selectedFields = this.opt.fields.split(',');
      $('.field-checkbox').each(function(){
        var $input = $(this);
        var value = $input.val();
        if (_.indexOf(selectedFields, value) >= 0) {
          $input.prop('checked', true);
        } else {
          $input.prop('checked', false);
        }
      });
    }

    this.facets = facetStringToObject(this.opt.facets);
    this.defaultFacets = facetStringToObject(this.defaults.facets);

    // TODO: map options, timeline
    // if (_.has(this.facets, 'year_dedicated_or_constructed') && isArrayString(this.facets.year_dedicated_or_constructed[0])) {
    //   this.yearRangeValue = this.facets.year_dedicated_or_constructed[0];
    //   var yearRange = JSON.parse(this.yearRangeValue);
    //   this.timeline.setRange(yearRange);
    // }

  };

  Map.prototype.loading = function(isLoading){
    this.isLoading = isLoading;

    if (isLoading) {
      $('body').addClass('loading');
      $('button, input, select').prop('disabled', true);
    } else {
      $('body').removeClass('loading');
      $('button, input, select').prop('disabled', false);
    }
  };

  Map.prototype.onPopup = function(p){

  };

  Map.prototype.onQueryResponse = function(resp){
    console.log(resp);
    this.loading(false);

    this.renderMap(resp.facets.county_geoid.buckets);

    var hitCount = 0
    var hits = [];
    var facets = {};

    if (resp && resp.hits && resp.hits.hit && resp.hits.hit.length > 0) {
      hitCount = resp.hits.found;
      hits = resp.hits.hit;
      facets = resp.facets;
    }

    this.renderResultMessage(hitCount);
    this.renderResults(hits);
    this.renderFacets(facets);
  };

  Map.prototype.onResize = function(){
    var _this = this;
    setTimeout(function(){ _this.map.invalidateSize()}, 600);
  };

  Map.prototype.onSearchSubmit = function(){
    if (this.isLoading) return;
    this.start = 0;
    this.query();
  };

  Map.prototype.query = function(){
    var _this = this;

    this.loading(true);
    var queryString = this.getQueryString();
    var url = this.opt.endpoint + '?' + queryString;

    console.log('Search URL: ', url);
    this.updateURL();

    $.getJSON(url, function(resp) {
      _this.onQueryResponse(resp);
    });
  };

  Map.prototype.removeFacet = function(key, value){
    if (!_.has(this.facets, key) || this.isLoading) return;

    console.log('Removing ', key, value);

    // if (key === 'latlon'){
    //   this.map.reset();
    //   this.mapData = false;
    // }
    //
    // if (key === 'year_dedicated_or_constructed'){
    //   this.yearRangeValue = false;
    //   this.timeline.reset();
    // }

    this.facets[key] = _.without(this.facets[key], value);
    if (this.facets[key].length < 1) {
      this.facets = _.omit(this.facets, key);
    }
    this.start = 0;
    this.query();
  };

  Map.prototype.renderFacets = function(facets){
    facets = facets || {};

    var facetLabels = this.opt.facetLabels;
    var selectedFacets = this.facets;
    var excludeFields = ['county_geoid', 'object_groups', 'year_dedicated_or_constructed'];

    facets = _.pick(facets, function(obj, key) {
      return obj && obj.buckets && obj.buckets.length > 0 && _.indexOf(excludeFields, key) < 0;
    });

    this.$facets.empty();
    var html = '';
    _.each(this.opt.returnFacets, function(key){
      if (!_.has(facets, key)) return;
      var obj = facets[key];
      var title = Util.capitalize(key.replace('_', ' '));
      if (_.has(facetLabels, key)) title = facetLabels[key];
      var buckets = obj.buckets;
      html += '<fieldset class="facet active">';
        html += '<label for="facet-select-'+key+'">'+title+'</label>';
        html += '<select id="facet-select-'+key+'" class="facet-select" data-field="'+key+'">';
          html += '<option value="">Any</option>';
          _.each(buckets, function(bucket, j){
            var id = 'facet-'+key+'-'+j;
            var selected = '';
            if (_.has(selectedFacets, key) && _.indexOf(selectedFacets[key], bucket.value) >= 0) selected = 'selected ';
            var label = ''+bucket.value;
            html += '<option value="'+bucket.value+'" '+selected+'/>'+label+' ('+Util.formatNumber(bucket.count)+')</option>'
          });
        html += '</select>';
      html += '</fieldset>';
    });

    // if (_.has(facets, 'state')) {
    //   this.map.renderResults(facets.state.buckets);
    // } else {
    //   this.map.renderResults([]);
    // }
    //
    // var years = [];
    // if (_.has(facets, 'year_dedicated_or_constructed')) years = facets.year_dedicated_or_constructed.buckets;
    // this.timeline.renderResults(years);

    this.$facets.html(html);
  };

  Map.prototype.renderMap = function(countyFacetData){
    var _this = this;
    var countyCounts = {};
    var total = 0;
    var unknownTotal = 0;
    var values = [];
    _.each(countyFacetData, function(f){
      if (f.value == "Unknown") unknownTotal = f.count;
      else {
        var countyId = f.value;
        if (countyId.length < 5) countyId = countyId.padStart(5, '0');
        countyCounts[countyId] = f.count;
        values.push(f.count);
      }
    });
    this.countyCounts = countyCounts;
    console.log(unknownTotal + ' records with no county data');

    var stats = MathUtil.stats(values);
    var stds = 1.5; // this many standard deviations of mean
    var minValue = stats.mean - stats.std * stds;
    var maxValue = stats.mean + stats.std * stds;

    var style = function(feature){
      var density = 0;
      var countyId = feature.properties.GEOID;
      if (_.has(countyCounts, countyId) && maxValue > 0) {
        var t = MathUtil.norm(countyCounts[countyId], minValue, maxValue);
        density = MathUtil.ease(t);
        // density = t;
      }
      return {
        weight: 1,
        opacity: 0.4,
        color: 'white',
        fillOpacity: 0.667,
        fillColor: Util.getGradientColor(density)
      };
    };

    if (this.countyDataLayer === false) {
      var countyDataLayer = L.geoJson(this.countyData, {
        style: style,
        onEachFeature: function(feature, layer){
          layer.on({
            mouseover: function(e){ _this.countyInfoOn(e) },
            mouseout: function(e){ _this.countyInfoOff(e) },
            click: function(e){ _this.zoomToCounty(e) },
          });
        }
      });
      this.featureLayer.addLayer(countyDataLayer);
      this.countyDataLayer = countyDataLayer;

    } else {
      this.countyDataLayer.setStyle(style);
    }

  };

  Map.prototype.renderResultMessage = function(totalCount){
    var $container = this.$resultMessage;
    var offsetStart = this.start;
    var queryText = this.$query.val().trim();
    var size = this.size;
    var startNumber = Math.max(1, offsetStart);
    var endNumber = Math.min(totalCount, startNumber + size - 1);
    var facets = _.omit(this.facets, 'object_groups');

    var html = '<p>';
      html += 'Found <strong>' + Util.formatNumber(totalCount) + '</strong> records';
      if (queryText.length > 0) html +=' with query <button type="button" class="reset-query small">"' + queryText + '" <strong>×</strong></button>';
      if (!_.isEmpty(facets)){
        html += ' with facets: ';
        _.each(facets, function(values, key){
          var title = key.replace('_', ' ');
          _.each(values, function(value){
            html += '<button type="button" class="remove-facet small" data-key="'+key+'" data-value="'+value+'"><strong>'+title+'</strong>: "'+value+'" <strong>×</strong></button>';
          });
        });
      }
      if (totalCount > endNumber) html += '. Showing first ' + Util.formatNumber(endNumber) + ' results.';
      else html += '. Showing all ' + Util.formatNumber(endNumber) + ' results.';
    html += '</p>';
    $container.html(html);
  };

  Map.prototype.renderResults = function(results){
    this.$results.empty();
    if (!results || !results.length) return;
    var html = '';
    var start = this.start;

    html += '<ul class="result-list">';
    _.each(results, function(result, i){
      var id = result.id;
      var fields = result.fields;

      html += '<li class="result-item">';

        // display city, state
        var cityState = false;
        if (_.has(fields, 'city') && _.has(fields, 'state') && fields.city && fields.state) cityState = fields.city + ', ' + fields.state;
        else if (_.has(fields, 'state') && fields.state) cityState = fields.state;

        // display name
        var name = _.has(fields, 'name') ? fields.name : '<em>[Untitled]</em>';
        if (cityState) name += ' (' + cityState + ')';
        html += '<h3>'+(i+1+start)+'. <a href="#'+id+'" data-id="'+id+'" class="item-link">'+name+'</a></h3>';

        // display source
        if (_.has(fields, 'source')) {
          if (_.has(fields, 'url')) html += '<p>Source: <a href="'+fields.url+'" target="_blank">'+fields.source+'</a></p>';
          else html += '<p>Source: '+fields.source+'</p>';
        }

        // display latlon
        if (_.has(fields, 'latlon')) {
          html += '<p>Location: <a href="https://www.google.com/maps/search/?api=1&query='+fields.latlon.replace(' ','')+'" target="_blank">'+fields.latlon+'</a></p>';
        }

        // display image
        if (_.has(fields, 'image')) {
          html += '<p><a href="'+fields.image+'" target="_blank">Image link</a></p>';
        }

      html += '</li>';
    });
    html += '</ul>';
    this.$results.html(html);
  };

  Map.prototype.resetQuery = function(){
    this.$query.val('');
    this.onSearchSubmit();
  };

  Map.prototype.updateFacets = function(){
    if (this.isLoading) return;

    var facets = _.extend({}, this.defaultFacets);
    // retain latlon, year if present
    // var latlon = _.has(this.facets, 'latlon') ? this.facets.latlon : false;
    $('.facet-select').each(function(){
      var $select = $(this);
      var facetName = $select.attr('data-field');
      var facetValue = $select.val().trim();
      if (facetValue.length > 0) facets[facetName] = [facetValue];
    });
    // if (latlon !== false) facets.latlon = latlon;
    // // add year range if year not present
    // var yearRangeValue = this.yearRangeValue;
    // if (!_.has(facets, 'year_dedicated_or_constructed') && yearRangeValue !== false) {
    //   facets.year_dedicated_or_constructed = [yearRangeValue];
    // // year facet has been selected; ignore year range
    // } else if (_.has(facets, 'year_dedicated_or_constructed')) {
    //   this.yearRangeValue = false;
    //   this.timeline.reset();
    // }
    this.facets = facets;
    this.start = 0;
    this.query();
  };

  Map.prototype.updateURL = function(){
    var params = {};

    params.q = this.$query.val().trim();
    if (this.start > 0) params.start = this.start;
    if (this.sort && this.sort.length) params.sort = this.sort;

    // selected specific fields to search in
    var selectedFields = [];
    var allChecked = true;
    $('.field-checkbox').each(function(){
      var $input = $(this);
      if ($input.prop('checked')) {
        selectedFields.push($input.val());
      } else {
        allChecked = false;
      }
    });
    if (!allChecked) {
      params.fields = selectedFields.join(',');
    }

    // selected facets
    // e.g. facets=facetName1~value1!!value2!!value3__facetName2~value1
    var facets = _.clone(this.facets);
    facets = _.omit(facets, function(values, key) {
      return values.length < 1;
    });
    if (!_.isEmpty(facets)) {
      var facetsString = _.map(facets, function(values, key){
        return key + '~' + values.join('!!');
      });
      facetsString = facetsString.join('__');
      params.facets = facetsString;
    }

    params.centerLatLon = this.centerLatLon.join(",");
    params.startZoom = this.zoomLevel;

    this.currentQueryParams = params;

    if (window.history.pushState) {
      var queryString = $.param(params);
      var baseUrl = window.location.href.split('?')[0];
      var currentState = window.history.state;
      var newUrl = baseUrl + '?' + queryString;

      // ignore if state is the same
      if (currentState) {
        var currentUrl = baseUrl + '?' + $.param(currentState);
        if (newUrl === currentUrl) return;
      }

      window.historyInitiated = true;
      // console.log('Updating url', newUrl);
      window.history.replaceState(params, '', newUrl);
      // window.history.pushState(data, '', newUrl);
    }

  };

  Map.prototype.zoomToCounty = function(e){

  };

  return Map;

})();

$(function() {
  var app = new Map({});
});
