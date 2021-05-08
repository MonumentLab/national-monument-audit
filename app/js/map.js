'use strict';

var STATE_CODES = {"01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO", "09": "CT", "10": "DE", "11": "DC", "12": "FL", "13": "GA", "15": "HI", "16": "ID", "17": "IL", "18": "IN", "19": "IA", "20": "KS", "21": "KY", "22": "LA", "23": "ME", "24": "MD", "25": "MA", "26": "MI", "27": "MN", "28": "MS", "29": "MO", "30": "MT", "31": "NE", "32": "NV", "33": "NH", "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND", "39": "OH", "40": "OK", "41": "OR", "42": "PA", "44": "RI", "45": "SC", "46": "SD", "47": "TN", "48": "TX", "49": "UT", "50": "VT", "51": "VA", "53": "WA", "54": "WV", "55": "WI", "56": "WY", "60": "AS", "64": "FM", "66": "GU", "67": "JA", "68": "MH", "69": "MP", "70": "PW", "72": "PR", "74": "UM", "76": "NI", "78": "VI", "81": "BI", "86": "JI", "89": "KR"};

var Map = (function() {

  function Map(config) {
    var defaults = {
      // search values
      'endpoint': 'https://5go2sczyy9.execute-api.us-east-1.amazonaws.com/production/search',
      'returnFacets': ['source', 'entities_people', 'entities_events', 'theme', 'state', 'year_dedicated_or_constructed', 'county_geoid'], // note if these are changed, you must also update the allowed API Gateway queryParams for facet.X and redeploy the API
      'facetSize': 100,
      'customFacetSizes': {
        'county_geoid': 4000
      },
      'start': 0,
      'size': 100,
      'sort': '',
      'fields': '', // e.g. name,street_address
      'q': '',
      'facets': '', // e.g. facetName1~value1!!value2!!value3__facetName2~value1

      // map values
      'mapEl': 'search-map',
      'tileUrlTemplate': 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      'minZoom': 4,
      'maxZoom': 18,
      'startZoom': 5, // see the whole country
      'attribution': '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      'centerLatLon': [38.5767, -92.1736], // Jefferson City, MO as center
      'nominatimUrl': 'https://nominatim.openstreetmap.org/search?q={q}&format=json',
      'countyData': 'data/counties.json'
    };
    var q = Util.queryParams();
    this.opt = _.extend({}, defaults, config, q);
    this.init();
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
    this.mapData = false;

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

  Map.prototype.loadListeners = function(){};

  Map.prototype.loadMap = function(){
    var _this = this;
    var promise = $.Deferred();
    var opt = this.opt;
    var tiles = L.tileLayer(opt.tileUrlTemplate, {
      minZoom: opt.minZoom,
      maxZoom: opt.maxZoom,
      attribution: opt.attribution
    });
    var latlng = L.latLng(opt.centerLatLon[0], opt.centerLatLon[1]);
    var map = L.map(opt.mapEl, {center: latlng, zoom: opt.startZoom, layers: [tiles]});

    this.featureLayer = new L.FeatureGroup();
    map.addLayer(this.featureLayer);
    this.map = map;
    map.on('popupopen', function(e) {
      _this.onPopup(e.popup);
    });

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

    // e.g. facets=facetName1~value1!!value2!!value3__facetName2~value1
    if (this.opt.facets && this.opt.facets.length) {
      var pairs = _.map(this.opt.facets.split('__'), function(str){
        var pair = str.split('~');
        var facetName = pair[0];
        var facetValues = pair[1].split('!!');
        return [facetName, facetValues];
      });
      this.facets = _.object(pairs);
    }

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

    this.renderMap();

    // if (resp && resp.hits && resp.hits.hit && resp.hits.hit.length > 0) {
    //   this.renderResultMessage(resp.hits.found);
    //   this.renderResults(resp.hits.hit);
    //   this.renderFacets(resp.facets);
    //   this.renderPagination(resp.hits.found);
    //
    // } else {
    //   this.renderResultMessage(0);
    //   this.renderResults([]);
    //   this.renderFacets({});
    //   this.renderPagination(0);
    // }
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

  Map.prototype.renderMap = function(){
    this.featureLayer.clearLayers();
    var dataLayer = L.geoJson(this.countyData, {
      style: function(feature){
        return {
          weight: 1,
          opacity: 1,
          color: 'white',
          fillOpacity: 0.667,
          fillColor: 'red'
        };
      }
    });
    this.featureLayer.addLayer(dataLayer);
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

    if (this.mapData !== false) {
      params = _.extend({}, params, this.mapData.urlProps);
    }

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

  return Map;

})();

$(function() {
  var app = new Map({});
});
