'use strict';

var STATE_CODES = {"01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO", "09": "CT", "10": "DE", "11": "DC", "12": "FL", "13": "GA", "15": "HI", "16": "ID", "17": "IL", "18": "IN", "19": "IA", "20": "KS", "21": "KY", "22": "LA", "23": "ME", "24": "MD", "25": "MA", "26": "MI", "27": "MN", "28": "MS", "29": "MO", "30": "MT", "31": "NE", "32": "NV", "33": "NH", "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND", "39": "OH", "40": "OK", "41": "OR", "42": "PA", "44": "RI", "45": "SC", "46": "SD", "47": "TN", "48": "TX", "49": "UT", "50": "VT", "51": "VA", "53": "WA", "54": "WV", "55": "WI", "56": "WY", "60": "AS", "64": "FM", "66": "GU", "67": "JA", "68": "MH", "69": "MP", "70": "PW", "72": "PR", "74": "UM", "76": "NI", "78": "VI", "81": "BI", "86": "JI", "89": "KR"};

var BASE_URL = 'https://monumentlab.github.io/national-monument-audit/app/';

var Map = (function() {

  function Map(config) {
    var defaults = {
      'requireAuth': true,

      // search values
      'endpoint': 'https://5go2sczyy9.execute-api.us-east-1.amazonaws.com/production/search',
      'returnFacets': ['object_groups', 'sources', 'monument_types', 'entities_people', 'gender_represented', 'ethnicity_represented', 'state', 'year_dedicated_or_constructed', 'county_geoid'], // note if these are changed, you must also update the allowed API Gateway queryParams for facet.X and redeploy the API
      'facetLabels': {
        'entities_people': 'People',
        'entities_events': 'Events',
        'state': 'State or Territory'
      },
      'returnValues': 'name,latlon,city,state,source,sources,url,image,duplicates,geo_type',
      'facetSize': 100,
      'customFacetSizes': {
        'county_geoid': 4000,
        'year_dedicated_or_constructed': 1000,
        'entities_people': 1000
      },
      'start': 0,
      'size': 500,
      'sort': '',
      'fields': '', // e.g. name,street_address
      'q': '',
      'facets': 'object_groups~Monument__is_duplicate~0', // e.g. facetName1~value1!!value2!!value3__facetName2~value1
      'searchCacheSize': 5, // store this many responses in memory
      'maxDupeRequest': 100, // request this many items that are duplicates
      'maxResultSize': 10000, // no direct pagination after 10K https://docs.aws.amazon.com/cloudsearch/latest/developerguide/paginating-results.html#deep-paging

      // map values
      'mapEl': 'search-map',
      'tileUrlTemplate': 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      'minZoom': 3,
      'maxZoom': 18,
      'startZoom': 4, // see the whole country
      'attribution': '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      'centerLatLon': "38.5767,-92.1736", // Jefferson City, MO as center
      'nominatimUrl': 'https://nominatim.openstreetmap.org/search?q={q}&format=json',
      'countyData': 'data/counties.json',
      'markerZoomThreshold': 10, // start showing markers at this zoom level
      'itemZoomLevel': 17,
      'maxMarkerCount': 500,
      'flyDuration': 0.25,
      'highlightMarker': false,

      // timeline values
      'yearRange': [1700, 2020]
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

  function resultToHtml(result, start, index, linkToMap){
    var id = result.id;
    var fields = result.fields;
    var html = '';

    // display city, state
    var cityState = false;
    if (_.has(fields, 'city') && _.has(fields, 'state') && fields.city && fields.state) cityState = fields.city + ', ' + fields.state;
    else if (_.has(fields, 'state') && fields.state) cityState = fields.state;

    // display name
    var itemUrl = '';
    var name = _.has(fields, 'name') ? fields.name : '<em>[Untitled]</em>';
    var indexString = (start !== undefined && index !== undefined) ? (index+1+start) + '. ' : '';
    if (cityState) name += ' (' + cityState + ')';
    if (linkToMap && _.has(fields, 'latlon')) {
      html += '<h3>'+indexString+'<a href="#'+id+'" data-id="'+id+'" data-latlon="'+fields.latlon+'" class="item-link">'+name+'</a></h3>';
    } else {
      var itemParams = {'id': id}
      itemUrl = 'item.html?' + $.param(itemParams);
      // html += '<h3>'+indexString+'<a href="'+itemUrl+'"  target="_blank">'+name+'</a></h3>';
      html += '<h3>'+indexString+'<a href="'+itemUrl+'" data-url="'+itemUrl+'" class="item-modal-button" target="_blank">'+name+'</a></h3>';
    }

    // display source
    if (_.has(fields, 'source')) {
      if (fields.source == "Multiple" && _.has(fields, 'duplicates') && fields.duplicates.length > 0) {
        html += '<p>Multiple sources: ';
          var sourceStrings = _.map(fields.duplicates, function(dupeId){ return '<span class="duplicate-source" data-id="'+dupeId+'"></span>'; });
          html += sourceStrings.join(', ');
        html += '</p>';
      } else if (_.has(fields, 'url')) html += '<p>Source: <a href="'+fields.url+'" target="_blank">'+fields.source+'</a></p>';
      else html += '<p>Source: '+fields.source+'</p>';
    }

    // display latlon
    if (_.has(fields, 'latlon')) {
      html += '<p>Location: <a href="https://www.google.com/maps/search/?api=1&query='+fields.latlon.replace(' ','')+'" target="_blank">'+fields.latlon+'</a></p>';
      if (_.has(fields, 'geo_type') && fields.geo_type == 'Approximate coordinates provided'){
        html += '<p class="alert">⚠ Coordinates provided by source are likely inaccurate</p>';
      }
    } else {
      html += '<p><em>No geographic coordinate data</em></p>';
    }

    // display image
    if (_.has(fields, 'image')) {
      html += '<p><a href="'+fields.image+'" target="_blank">Image link</a></p>';
    }

    // display report a problem
    if (!linkToMap) {
      html += '<p>'
        html += '<button class="small item-modal-button" data-url="'+itemUrl+'">View full record</button>';
        html += '<a href="https://docs.google.com/forms/d/e/1FAIpQLSchwiivhPxl6DGxdrO0Bk56zaa73AwzAH-GWt44Pmmnr2HDhQ/viewform?usp=sf_link&entry.846962896='+name+'&entry.632814286='+BASE_URL+itemUrl+'" class="small button" target="_blank">Report a problem</a>';
      html += '</p>';
    }

    return html;
  }

  Map.prototype.init = function(){
    if (this.opt.requireAuth) {
      var isValid = Auth.authenticate();
      if (isValid) this.load();

    } else {
      this.load();
    }
  };

  Map.prototype.applyFacet = function(field, value){
    var _this = this;
    var $select = $('select.facet-select[data-field="'+field+'"]').first();

    // add value to drop down if it does not exist
    var facetDropdowns = this.facetDropdowns;
    if (_.has(facetDropdowns, field)) {
      var dropdownValues = facetDropdowns[field];
      if (! _.find(dropdownValues, function(r){ return ""+r.value === ""+value; }) ) {
        $select.append('<option value="'+Util.escapeQuotes(value)+'">'+value+'</option>');
        _this.facetDropdowns[field].push({value: value})
      }
    }

    $select.val(value);
    this.$facetModal.removeClass('active');
    this.updateFacets();
  };

  Map.prototype.cacheAdd = function(queryString, resp){
    if (this.searchCache.length >= this.opt.searchCacheSize) {
      var removed = this.searchCache.shift();
    }

    this.searchCache.push({
      queryString: queryString,
      resp: resp
    });
  };

  Map.prototype.cacheGet = function(queryString){
    var found = _.find(this.searchCache, function(entry){ return entry.queryString === queryString; });
    if (found) return found.resp;
    else return false;
  };

  Map.prototype.countyInfoOn = function(e){
    var layer = e.target;
    layer.setStyle({
      weight: 2,
      opacity: 1
    });
    this.activeCountyFeature = layer.feature.properties;
    this.renderInfo();
  };

  Map.prototype.countyInfoOff = function(e){
    e.target.setStyle({
      weight: 1,
      opacity: 0.4
    });
    this.activeCountyFeature = false;
    this.renderInfo();
  };

  Map.prototype.getMapBoundsValue = function(){
    var bounds = this.map.getBounds();
    var boundsValue = [bounds.getNorthWest().lat + ',' + bounds.getNorthWest().lng, bounds.getSouthEast().lat + ',' + bounds.getSouthEast().lng];
    return JSON.stringify(boundsValue).replaceAll('"', "'");
  };

  Map.prototype.getQueryObject = function(customFacets, customStart){
    var queryText = this.$query.val().trim();
    queryText = queryText.replace(/\//g, " "); // slashes break search
    var facetSize = this.opt.facetSize;
    var customFacetSizes = this.opt.customFacetSizes;
    var q = {
      q: queryText,
      size: this.size
    };
    if (customStart !== undefined && customStart > 0) q.start = customStart;
    else if (customStart === undefined && this.start > 0) q.start = this.start;
    if (this.sort && this.sort.length) q.sort = this.sort;
    var facets = customFacets ? _.clone(customFacets) : _.clone(this.facets);
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

  Map.prototype.getQueryString = function(customFacets, customStart){
    var q = this.getQueryObject(customFacets, customStart);
    var qstring = $.param(q);
    return qstring;
  };

  Map.prototype.goToPageOffset = function(start){
    this.start = start;
    this.query();
    $('.panel-content').scrollTop(0);
  };

  Map.prototype.isMarkerView = function(){
    return (this.zoomLevel >= this.opt.markerZoomThreshold);
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
    this.$info = $('#info-panel');
    this.$searchMapButton = $('.search-in-map');
    this.$timeline = $('#timeline');
    this.$timelineSlider = $('#timeline-slider');
    this.$timelineSliderLabel = $('#timeline-slider-label');
    this.$facetModal = $('#facet-modal');
    this.$facetSearchResults = $('#facet-search-results');
    this.$facetSearchInput = $('#search-facet-input');
    this.$colorKey = $('#color-key');
    this.$itemModal = $('#item-modal');
    this.$itemModalContent = $('#item-modal-content');
    this.facets = {};
    this.size = parseInt(this.opt.size);
    this.start = parseInt(this.opt.start);
    this.sort = this.opt.sort;
    this.centerLatLon = _.map(this.opt.centerLatLon.split(","), function(v){ return parseFloat(v); } );
    this.zoomLevel = this.opt.startZoom;
    this.highlightMarker = this.opt.highlightMarker;
    this.countyDataLayer = false;
    this.activeCountyFeature = false;
    this.markerLayer = false;
    this.heatLayer = false;
    this.visibleLayer = '';
    this.mapData = false;
    this.countyCounts = {};
    this.facetResults = {};
    this.facetDropdowns = {};
    this.searchCache = [];
    this.itemCache = {};
    this.opt.yearRange[1] = parseInt(new Date().getFullYear());
    this.yearRangeValue = false;

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
      setTimeout(function(){
        _this.map.invalidateSize();
        _this.onResize();
      }, 600);

    });

    $(window).on('resize', function(){
      _this.onResize();
    });

    this.$form.on('submit', function(e){
      e.preventDefault();
      _this.onSearchSubmit();
    });

    this.loadTimelineSlider();

    this.$timelineSlider.on('mousemove', function(e){
      _this.updateTimelineLabel(e);
    });

    this.map.on('moveend', function(e){
      var latlon = _this.map.getCenter();
      _this.zoomLevel = _this.map.getZoom();
      _this.centerLatLon = [latlon.lat, latlon.lng];
      _this.$searchMapButton.addClass('active');
      _this.updateMarkers();
      _this.updateURL();
      _this.renderMap();
      _this.renderInfo();
    });

    this.$searchMapButton.on('click', function(e){
      e.preventDefault();
      _this.onSearchMapSubmit();
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

    $('body').on('click', '.item-link', function(e){
      e.preventDefault();
      _this.zoomToItem($(this).attr('data-id'), $(this).attr('data-latlon'));
    });

    $('body').on('click', '.go-to-offset', function(e){
      _this.goToPageOffset(parseInt($(this).attr('data-start')));
    });

    $('body').on('change', '.select-offset', function(e){
      _this.goToPageOffset(parseInt($(this).val()));
    });

    $('body').on('click', '.apply-facet', function(e){
      var $el = $(this);
      _this.applyFacet($el.attr('data-field'), $el.attr('data-value'));
    });

    $('body').on('click', '.item-modal-button', function(e){
      e.preventDefault();
      _this.renderItemModal($(this).attr('data-url'));
    });

    this.$facetSearchInput.on('input', function(e){
      _this.renderAllFacets();
    });

    $('.search-facet-sort').on('change', function(e){
      _this.renderAllFacets();
    });
  };

  Map.prototype.loadTimelineSlider = function(){
    var _this = this;
    var yearRange = this.opt.yearRange;
    var selectedRange = this.yearRangeValue !== false ? this.yearRangeValue : yearRange;

    this.$timelineSlider.slider({
      range: true,
      min: yearRange[0],
      max: yearRange[1],
      values: selectedRange,
      create: function(event, ui) {
        $(this).children('.ui-slider-handle').each(function(index){
          $(this).html('<span class="label">'+selectedRange[index]+'</span>');
        });
      },
      slide: function(e, ui){
        $(this).children('.ui-slider-handle').each(function(index){
          $(this).html('<span class="label">'+ui.values[index]+'</span>');
        });
      },
      change: function(e, ui) {
        _this.onChangeYearRange(ui.values[0], ui.values[1]);
      }
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

    this.markerLayer = L.markerClusterGroup({
      // disableClusteringAtZoom: this.opt.itemZoomLevel
    });

    this.heatLayer = L.heatLayer([], {
      minOpacity: 0.3,
      maxZoom: 20,
      gradient: Util.getColorGradient(20, true)
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

    this.facets = facetStringToObject(this.opt.facets);
    this.defaultFacets = facetStringToObject(this.defaults.facets);

    if (_.has(this.facets, 'year_dedicated_or_constructed') && isArrayString(this.facets.year_dedicated_or_constructed[0])) {
      var yearRangeValue = this.facets.year_dedicated_or_constructed[0];
      this.yearRangeValue = JSON.parse(yearRangeValue);
    }
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

  Map.prototype.onChangeYearRange = function(minYear, maxYear){
    console.log('UI range change heard', minYear, maxYear);

    var yearRange = _.map([minYear, maxYear], function(y){ return parseInt(y); });
    this.yearRangeValue = JSON.stringify(yearRange).replaceAll('"', "'");

    var fullRange = this.opt.yearRange;
    // if selected range is full range, ignore facet
    if (yearRange[0] <= fullRange[0] && yearRange[1] >= fullRange[1]) {
      this.yearRangeValue = false;
      this.facets = _.omit(this.facets, 'year_dedicated_or_constructed');
    } else {
      this.facets.year_dedicated_or_constructed = [this.yearRangeValue];
    }
    this.query()
  };

  Map.prototype.onFacetSearch = function(value){
    var activeFacetSearchField = this.activeFacetSearchField;
    var facetResults = this.facetResults;

    if (!activeFacetSearchField || !_.has(facetResults, activeFacetSearchField)) return;

    var results = facetResults[activeFacetSearchField];
  };

  Map.prototype.onPopup = function(p){
    var itemId = p.options.itemId;

    if (itemId) {
      this.highlightMarker = itemId;
      this.updateURL();
      this.highlightMarker = false;
    }

    // check for duplicates
    // console.log('Popup', p);
    var content = p.getContent();
    var $content = $(content);
    var $dupes = $content.find('.duplicate-source');
    if ($dupes.length > 0) {
      var dupeIds = $dupes.map(function(){
        return $(this).attr('data-id');
      }).get();
      this.renderDuplicates(dupeIds);
    }
  };

  Map.prototype.onQueryResponse = function(resp){
    var _this = this;

    console.log('Query response: ', resp);
    this.loading(false);

    this.updateMap(resp);
    this.updateTimeline(resp);

    var hitCount = 0
    var hits = [];
    var facets = {};

    if (resp && resp.hits && resp.hits.hit && resp.hits.hit.length > 0) {
      hitCount = resp.hits.found;
      hits = resp.hits.hit;
      facets = resp.facets;
    }

    this.lastSearchResults = hits;

    this.renderResultMessage(hitCount);
    this.renderResults(hits);
    this.renderFacets(facets);
    this.renderPagination(hitCount);
    this.renderMap();

    this.renderInfo();

    setTimeout(function(){
      _this.renderTimeline();
    }, 600);

  };

  Map.prototype.onResize = function(){
    this.renderTimeline();
  };

  Map.prototype.onSearchSubmit = function(){
    if (this.isLoading) return;
    this.start = 0;
    this.query();
  };

  Map.prototype.onSearchMapSubmit = function(){
    if (this.isLoading) return;
    this.$searchMapButton.removeClass('active');

    var bounds = this.getMapBoundsValue();
    this.facets.latlon = [bounds];
    this.start = 0;
    this.query();
  };

  Map.prototype.query = function(){
    var _this = this;

    this.loading(true);
    var queryString = this.getQueryString();
    var url = this.opt.endpoint + '?' + queryString;

    this.updateURL();
    console.log('Search URL: ', url);

    // check for response in cache
    var cachedResp = this.cacheGet(queryString);
    if (cachedResp !== false) {
      console.log('Found cached response.');
      this.onQueryResponse(cachedResp);
      return;
    }

    $.getJSON(url, function(resp) {
      _this.cacheAdd(queryString, resp);
      _this.onQueryResponse(resp);
    });
  };

  Map.prototype.queryBounds = function(bounds){
    var _this = this;
    this.loading(true);

    var facetsWithBounds =  _.extend({}, this.facets, {latlon: [bounds]});
    var queryString = this.getQueryString(facetsWithBounds, 0);
    var url = this.opt.endpoint + '?' + queryString;
    var promise = $.Deferred();

    console.log('Marker Search URL: ', url);

    // check for response in cache
    var cachedResp = this.cacheGet(queryString);
    if (cachedResp) {
      console.log('Found cached bounds response.');
      promise.resolve(cachedResp);
      return promise;
    }

    $.getJSON(url, function(resp) {
      _this.cacheAdd(queryString, resp);
      promise.resolve(resp);
    });

    return promise;
  };

  Map.prototype.queryFacets = function(facetName, onFinished){
    var _this = this;
    var query = this.getQueryObject();
    query.return = "_no_fields";
    query = _.omit(query, 'start');
    query = _.omit(query, function(value, key, object){ return key.startsWith('facet.'); });
    query['facet.'+facetName] = "{sort:'bucket', size:4000}";
    var url = this.opt.endpoint + '?' + $.param(query);
    console.log('Facet Search URL: ', url);

    $.getJSON(url, function(resp) {
      var results = [];
      if (resp.facets && resp.facets[facetName] && resp.facets[facetName].buckets) results = resp.facets[facetName].buckets;
      onFinished && onFinished(results);
    });
  };

  Map.prototype.removeFacet = function(key, value){
    if (!_.has(this.facets, key) || this.isLoading) return;

    console.log('Removing ', key, value);

    if (key === 'year_dedicated_or_constructed'){
      this.resetTimeline(); // this will automatically trigger change
      return;
    }

    this.facets[key] = _.without(this.facets[key], value);
    if (this.facets[key].length < 1) {
      this.facets = _.omit(this.facets, key);
    }
    this.start = 0;
    this.query();
  };

  Map.prototype.renderAllFacets = function(facetName, sortBy){
    facetName = facetName || this.activeFacetSearchField;
    sortBy = sortBy || $('input[name="search-facet-sort"]:checked').val();

    var results = _.has(this.facetResults, facetName) ? this.facetResults[facetName] : [];
    var query = this.$facetSearchInput.val().trim() + '';

    if (results.length > 0 && query.length > 0) {
      var searchResults = fuzzysort.go(query, results, {
        keys: ['value']
      });
      // console.log(searchResults)
      results = _.map(searchResults, function(r){
        var obj = r.obj;
        obj.fvalue = fuzzysort.highlight(r[0]);
        return obj;
      })
    }

    if (sortBy) {
      results = _.sortBy(results, function(r){
        if (sortBy === 'count') return -r.count;
        else return r[sortBy];
      });
    }
    var html = '<ul class="facet-list">';
    _.each(results, function(r){
      var displayValue = _.has(r, 'fvalue') && query.length > 0 ? r.fvalue : r.value;
      html += '<li><button class="apply-facet small" data-field="'+facetName+'" data-value="'+Util.escapeQuotes(r.value)+'">'+displayValue+' ('+r.count+')</button>'
    });
    html += '</ul>';
    this.$facetSearchResults.html(html);
    // this.$facetSearchResults.find('.apply-facet').first().focus();
  };

  Map.prototype.renderDuplicates = function(duplicateIds){
    var _this = this;
    duplicateIds = _.uniq(duplicateIds);
    console.log('Found duplicates: ', duplicateIds);
    var itemCache = this.itemCache;
    var idsToUpdate = _.filter(duplicateIds, function(id){ return _.has(itemCache, id); });
    var idsToRequest = _.filter(duplicateIds, function(id){ return !_.has(itemCache, id); });
    if (idsToRequest.length > 0) {
      if (idsToRequest.length > this.opt.maxDupeRequest) {
        idsToRequest = idsToRequest.slice(0, this.opt.maxDupeRequest);
      }
      console.log('Requesting duplicates: ', idsToRequest);
      var qstring = _.map(idsToRequest, function(id){ return "_id:'"+id+"'" });
      qstring = qstring.join(" ");
      qstring = '(or '+qstring+')';
      var q = {
        q: qstring,
        size: idsToRequest.length,
        return: this.opt.returnValues
      };
      q['q.parser'] = 'structured';
      var queryString = $.param(q);

      var url = this.opt.endpoint + '?' + queryString;
      console.log('Duplicates URL: ', url);

      $.getJSON(url, function(resp) {
        if (resp && resp.hits && resp.hits.hit && resp.hits.hit.length > 0) {
          _.each(resp.hits.hit, function(result){
            _this.itemCache[result.id] = result.fields;
          });
          _this.renderDuplicateItems(idsToRequest);
        }
      });
    }

    if (idsToUpdate.length > 0) {
      this.renderDuplicateItems(idsToUpdate);
    }
  };

  Map.prototype.renderDuplicateItems = function(duplicateIds){
    var itemCache = this.itemCache;
    _.each(duplicateIds, function(id){
      if (_.has(itemCache, id)){
        var fields = itemCache[id];
        if (_.has(fields, 'source')) {
          var $el = $('.duplicate-source[data-id="'+id+'"]');
          var html = '';
          if (_.has(fields, 'url')) {
            html += '<a href="'+fields.url+'" target="_blank">'+fields.source+'</a>';
          } else {
            html += fields.source;
          }
          $el.html(html);
        }

      }
    });
  };

  Map.prototype.renderFacets = function(facets){
    facets = facets || {};

    var _this = this;
    var facetLabels = this.opt.facetLabels;
    var selectedFacets = this.facets;
    var excludeFields = ['county_geoid', 'object_groups', 'year_dedicated_or_constructed'];

    facets = _.pick(facets, function(obj, key) {
      return obj && obj.buckets && obj.buckets.length > 0 && _.indexOf(excludeFields, key) < 0;
    });

    this.facetDropdowns = {};

    this.$facets.empty();
    var html = '';
    _.each(this.opt.returnFacets, function(key){
      if (!_.has(facets, key)) return;
      var obj = facets[key];
      var title = Util.capitalize(key.replace('_', ' '));
      if (_.has(facetLabels, key)) title = facetLabels[key];
      var buckets = obj.buckets;
      _this.facetDropdowns[key] = buckets;
      var isSelected = _.has(selectedFacets, key);
      html += '<fieldset class="facet active">';
        html += '<label for="facet-select-'+key+'">';
          html += title;
          if (_.indexOf(['entities_people', 'gender_represented', 'ethnicity_represented'], key) >= 0) html += '<a href="#'+key+'-modal" class="open-modal alert">⚠</a>';
          else html += '<a href="#'+key+'-modal" class="open-modal">🛈</a>';
        html += '</label>';
        if (isSelected) {
          var value = selectedFacets[key];
          html += '<button type="button" class="remove-facet" data-key="'+key+'" data-value="'+value+'">"'+value+'" <strong>×</strong></button>';
        } else {
          html += '<select id="facet-select-'+key+'" class="facet-select" data-field="'+key+'">';
            html += '<option value="">- Any -</option>';
            if (buckets.length > 10) html += '<option value="_all">- View all -</option>';
            _.each(buckets, function(bucket, j){
              var id = 'facet-'+key+'-'+j;
              var selected = '';
              if (_.has(selectedFacets, key) && _.indexOf(selectedFacets[key], bucket.value) >= 0) selected = 'selected ';
              var label = ''+bucket.value;
              html += '<option value="'+Util.escapeQuotes(bucket.value)+'" '+selected+'/>'+label+' ('+Util.formatNumber(bucket.count)+')</option>'
            });
          html += '</select>';
        }
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

  Map.prototype.renderInfo = function(){
    var _this = this;

    var columns = [];
    var markerView = this.isMarkerView();
    var html = '';

    if (!isNaN(this.recordsWithCounty)) {
      html += '<div class="info-column">';
        html += '<h3>Geographic coverage</h3>';
        html += '<div class="value">';
          html += '<p><strong>' + Util.formatNumber(this.recordsWithCounty) + ' ('+this.recordsWithCountyPercent+'%) entries</strong> have a lat/lon coordinate</p>';
        html += '</div>';
      html += '</div>';
    }

    if (!isNaN(this.recordsWithYear)) {
      html += '<div class="info-column">';
        html += '<h3>Temporal coverage</h3>';
        html += '<div class="value">';
          html += '<p><strong>' + Util.formatNumber(this.recordsWithYear) + ' ('+this.recordsWithYearPercent+'%) entries</strong> have a date dedicated or constructed</p>';
        html += '</div>';
      html += '</div>';
    }

    if (!markerView) {
      html += '<div id="info-county" class="info-column">';
        html += '<h3>Active county</h3>';
        html += '<div class="value">';
        if (!this.activeCountyFeature) {
          html += '<p>Hover over a county for more details</p>';
        } else {
          var props = this.activeCountyFeature;
          var countyName = props.NAME + ' County';
          var state = _.has(STATE_CODES, props.STATEFP) ? STATE_CODES[props.STATEFP] : '??';
          var countyId = props.GEOID;
          var count = 0;
          if (_.has(_this.countyCounts, countyId)) count = _this.countyCounts[countyId];
          html += '<p><strong>' + countyName + ', ' + state + '</strong></p>';
          html += '<p><em>' + Util.formatNumber(count) + ' entries</em></p>';
        }
        html += '</div>';
      html += '</div>';
      // this.$colorKey.addClass('active');
    } else {
      // this.$colorKey.removeClass('active');
    }


    this.$info.html(html);

    if (html.length > 0) this.$info.addClass('active');
    else this.$info.removeClass('active');
  };

  Map.prototype.renderItemModal = function(url){
    var html = '';

    html += '<a href="'+url+'" target="_blank" class="button">Open in new window</a>'
    html += '<iframe src="'+url+'&embedded=1"></iframe>';

    this.$itemModalContent.html(html);
    this.$itemModal.addClass('active');
  };

  Map.prototype.renderMap = function(){
    var _this = this;
    var visibleLayer = this.isMarkerView() ? 'marker' : 'county';

    // check to see if we should switch layers
    if (visibleLayer !== this.visibleLayer) {
      console.log('Switching to layer: ' + visibleLayer);
      this.visibleLayer = visibleLayer;
      this.featureLayer.clearLayers();
      if (visibleLayer === 'county') {
        this.featureLayer.addLayer(this.countyDataLayer);
      } else {
        this.featureLayer.addLayer(this.heatLayer);
        this.featureLayer.addLayer(this.markerLayer);

      }
    }
  };

  Map.prototype.renderPagination = function(totalCount){
    var $pagination = $('.search-results-pagination');
    $pagination.empty();
    if (totalCount <= 0) return;

    totalCount = Math.min(this.opt.maxResultSize, totalCount);
    var offsetStart = this.start;
    var size = this.size;
    var pages = Math.ceil(totalCount / size);
    var currentPage = Math.floor(offsetStart / size);

    var queryObj = _.clone(this.currentQueryParams);
    queryObj = _.omit(queryObj, 'start');

    $pagination.each(function(i){
      var html = '';
      if (offsetStart > 0) {
        var prevOffset = offsetStart-size;
        if (prevOffset <= 1) prevOffset = 0;
        html += '<button type="button" class="go-to-offset small" data-start="'+prevOffset+'">❮ Previous</button>';
      }
      html += '<div class="select-container">'
        html += '<label for="select-offset-'+(i+1)+'">Go to page</label>'
        html += '<select id="select-offset-'+(i+1)+'" class="select-offset">'
        _.times(pages, function(page){
          var start = page * size + 1;
          if (page < 1) start = 0;
          if (page === currentPage) {
            html += '<option value="'+start+'" selected>'+(page+1)+'</option>';
          } else {
            html += '<option value="'+start+'">'+(page+1)+'</option>';
          }
        });
        html += '</select>';
      html += '</div>';

      if (currentPage < pages) {
        var nextOffset = offsetStart+size;
        if (offsetStart < 1) nextOffset += 1;
        html += '<button type="button" class="go-to-offset small" data-start="'+nextOffset+'">Next ❯</button>';
      }

      $(this).html(html);
    });

  };

  Map.prototype.renderResultMessage = function(totalCount){
    var $container = this.$resultMessage;
    var offsetStart = this.start;
    var queryText = this.$query.val().trim();
    var size = this.size;
    var startNumber = Math.max(1, offsetStart);
    var endNumber = Math.min(totalCount, startNumber + size - 1);
    var facets = _.omit(this.facets, 'object_groups', 'is_duplicate');

    var html = '<p>';
      html += 'Found <strong>' + Util.formatNumber(totalCount) + '</strong> records';
      if (queryText.length > 0) html +=' with query <button type="button" class="reset-query small">"' + queryText + '" <strong>×</strong></button>';
      if (!_.isEmpty(facets)){
        html += ' with facets: ';
        _.each(facets, function(values, key){
          if (key == 'latlon') {
            html += '<button type="button" class="remove-facet small" data-key="'+key+'" data-value="'+values[0]+'"><strong>Custom map bounds</strong> <strong>×</strong></button>';
            return;
          }
          var title = key.replace('_', ' ');
          _.each(values, function(value){
            html += '<button type="button" class="remove-facet small" data-key="'+key+'" data-value="'+value+'"><strong>'+title+'</strong>: "'+value+'" <strong>×</strong></button>';
          });
        });
      }
      if (totalCount > endNumber) html += '. Showing results ' + Util.formatNumber(startNumber) + ' to ' + Util.formatNumber(endNumber) + '.';
      else html += '. Showing all ' + Util.formatNumber(endNumber) + ' results.';
    html += '</p>';
    $container.html(html);
  };

  Map.prototype.renderResults = function(results){
    this.$results.empty();
    if (!results || !results.length) return;
    var html = '';
    var start = this.start;
    var duplicateIds = [];

    html += '<ul class="result-list">';
    _.each(results, function(result, i){

      html += '<li class="result-item">';

        html += resultToHtml(result, start, i, true);

        if (_.has(result.fields, 'duplicates') && result.fields.duplicates.length > 0) {
          duplicateIds = duplicateIds.concat(result.fields.duplicates);
        }

      html += '</li>';
    });
    html += '</ul>';
    this.$results.html(html);

    if (duplicateIds.length > 0) {
      this.renderDuplicates(duplicateIds);
    }
  };

  Map.prototype.renderTimeline = function(){
    var $bars = this.$timeline.find('.timeline-bars').first();
    $bars.empty();
    var buckets = this.timelineData;

    if (buckets.length < 1) {
      this.$timeline.removeClass('active');
      return;
    }
    this.$timeline.addClass('active');
    var width = $bars.width();
    var height = $bars.height();
    var yearRange = this.opt.yearRange;
    var yearWidth = MathUtil.round(width / (this.opt.yearRange[1] - this.opt.yearRange[0] + 1), 4);
    var maxCount = _.max(buckets, function(b) { return b.count; }).count;
    var html = '';

    _.each(buckets, function(year){
      var x = MathUtil.norm(year.value, yearRange[0], yearRange[1]+1) * width;
      var sy = maxCount > 0 ? year.count / maxCount * height : 0;
      var css = 'transform: translateX('+x+'px) scaleX('+yearWidth+') scaleY('+sy+');';
      html += '<div class="bar" title="'+year.count+' entries constructed or dedicated in '+year.value+'" style="'+css+'"></div>';
    });
    $bars.html(html);
  };

  Map.prototype.resetQuery = function(){
    this.$query.val('');
    this.onSearchSubmit();
  };

  Map.prototype.resetTimeline = function(){
    this.$timelineSlider.slider("values", this.opt.yearRange);
  };

  Map.prototype.showAllFacets = function(facetName) {
    var _this = this;
    var $modal = this.$facetModal;

    var facetLabels = this.opt.facetLabels;
    var title = Util.capitalize(facetName.replace('_', ' '));
    if (_.has(facetLabels, facetName)) title = facetLabels[facetName];
    $modal.find('h2').first().text('All values for "'+title+'"');

    $modal.addClass('active loading');
    this.$facetSearchResults.html('<p>Loading data...</p>');
    this.$facetSearchInput.val('');

    this.activeFacetSearchField = facetName;

    var facetResults = this.facetResults;
    if (_.has(facetResults, facetName)) {
      this.renderAllFacets(facetName);
      return;
    }

    var onFinished = function(results){
      $modal.removeClass('loading');
      // console.log(results);
      _this.facetResults[facetName] = results;
      _this.renderAllFacets(facetName);
    };

    this.queryFacets(facetName, onFinished);
  };

  Map.prototype.updateCountyData = function(countyFacetData){
    var _this = this;
    var countyCounts = {};
    var total = 0;
    var unknownTotal = 0;
    var values = [];
    _.each(countyFacetData, function(f){
      if (f.value == "Unknown") {
        unknownTotal = f.count;

      } else {
        var countyId = f.value;
        if (countyId.length < 5) countyId = countyId.padStart(5, '0');
        countyCounts[countyId] = f.count;
        values.push(f.count);
      }
      total += f.count;
    });
    this.countyCounts = countyCounts;

    this.recordsWithCounty = total - unknownTotal;
    this.recordsWithCountyPercent = total > 0 ? Math.round((this.recordsWithCounty / total) * 100) : 0;

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
        color: '#444',
        fillOpacity: 0.667,
        fillColor: Util.getGradientColor(1-density)
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
      this.countyDataLayer = countyDataLayer;
      return true;

    } else {
      this.countyDataLayer.setStyle(style);
      return false;
    }
  };

  Map.prototype.updateFacets = function(){
    if (this.isLoading) return;

    var _this = this;
    var facets = _.extend({}, this.defaultFacets);
    var invokedShowAllFacets = false;

    // retain latlon, year if present
    var latlon = _.has(this.facets, 'latlon') ? this.facets.latlon : false;
    var year_dedicated_or_constructed = _.has(this.facets, 'year_dedicated_or_constructed') ? this.facets.year_dedicated_or_constructed : false;

    // check selects
    $('.facet-select').each(function(){
      var $select = $(this);
      var facetName = $select.attr('data-field');
      var facetValue = $select.val().trim();
      if (facetValue.length > 0 && !facetValue.startsWith("_")) facets[facetName] = [facetValue];
      if (facetValue === "_all") {
        $select.val("");
        invokedShowAllFacets = true;
        _this.showAllFacets(facetName);
      }
    });

    if (invokedShowAllFacets) return;

    // check buttons
    $('.facet .remove-facet').each(function(){
      var $button = $(this);
      var facetName = $button.attr('data-key');
      var facetValue = $button.attr('data-value').trim();
      if (facetValue.length > 0 && !facetValue.startsWith("_")) facets[facetName] = [facetValue];
    });

    if (latlon !== false) facets.latlon = latlon;
    if (year_dedicated_or_constructed !== false) facets.year_dedicated_or_constructed = year_dedicated_or_constructed;

    // console.log('Facets', facets)
    this.facets = facets;
    this.start = 0;
    this.query();
  };

  Map.prototype.updateHeat = function(points){
    this.heatLayer.setLatLngs(points);
  };

  Map.prototype.updateMarkers = function(){
    var _this = this;

    this.markerLayer.clearLayers();

    // only update markers if we're zoomed in enough
    if (!this.isMarkerView()) return;

    var boundsValue = this.getMapBoundsValue();
    var queryFinished = this.queryBounds(boundsValue);

    $.when(queryFinished).done(function(resp){
      console.log('Marker response: ', resp);
      _this.loading(false);

      var hits = [];
      if (resp && resp.hits && resp.hits.hit && resp.hits.hit.length > 0) {
        hits = resp.hits.hit;
      }
      var highlightedMarker = false;
      var duplicateIds = [];
      var points = [];

      _.each(hits, function(result){
        var fields = result.fields;
        var latlon = _.has(fields, 'latlon') && fields.latlon ? fields.latlon : false;
        if (latlon === false) return;


        latlon = _.map(latlon.split(","), function(v){ return parseFloat(v); });
        var point = new L.LatLng(latlon[0], latlon[1]);
        points.push(point);
        var marker = L.marker(point);
        var html = resultToHtml(result);
        marker.bindPopup(html, {itemId: result.id});
        if (_this.highlightMarker && _this.highlightMarker === result.id) {
          highlightedMarker = marker;
        }
        _this.markerLayer.addLayer(marker);
        // _this.markerLayer.refreshClusters();
        if (_.has(result.fields, 'duplicates') && result.fields.duplicates.length > 0) {
          duplicateIds.concat(result.fields.duplicates);
        }
      });

      _this.updateHeat(points);

      if (highlightedMarker) {
        highlightedMarker.openPopup();
      }

      if (_this.highlightMarker) {
        _this.highlightMarker = false;
      }

      if (duplicateIds.length > 0) {
        this.renderDuplicates(duplicateIds);
      }
    });


  };

  Map.prototype.updateMap = function(resp) {
    var buckets = _.has(resp.facets, 'county_geoid') ? resp.facets.county_geoid.buckets : [];
    this.updateCountyData(buckets);
    this.updateMarkers();
  };

  Map.prototype.updateTimeline = function(resp) {
    var buckets = _.has(resp.facets, 'year_dedicated_or_constructed') ? resp.facets.year_dedicated_or_constructed.buckets : [];
    var total = resp.hits && resp.hits.found ? resp.hits.found : 0;

    buckets = _.map(buckets, function(b){
      return {
        value: parseInt(b.value),
        count: b.count
      }
    });
    buckets = _.sortBy(buckets, 'value');
    if (buckets.length > 0) console.log('Year range: ' + buckets[0].value + ' - ' + _.last(buckets).value);

    var yearRange = this.opt.yearRange;
    buckets = _.filter(buckets, function(b){ return b.value >= yearRange[0] && b.value <= yearRange[1]; });
    var validTotal = _.reduce(buckets, function(memo, b){ return memo + b.count; }, 0);
    this.recordsWithYear = validTotal;
    this.recordsWithYearPercent = total > 0 ? Math.round(validTotal / total * 100) : 0;

    this.timelineData = buckets;
  };

  Map.prototype.updateTimelineLabel = function(e){
    var p = Util.getRelativePoint(this.$timelineSlider, e.pageX, e.pageY);
    var nx = p.x;
    if (nx < 0 || nx > 1) {
      this.$timelineSliderLabel.removeClass('active');
      return;
    }

    var percentLeft = (nx * 100) + '%';
    this.$timelineSliderLabel.css('left', percentLeft);

    var yearRange = this.opt.yearRange;
    var year = Math.round(MathUtil.lerp(yearRange[0], yearRange[1], nx));

    this.$timelineSliderLabel.html('<div class="label">'+year+'</div>');
    this.$timelineSliderLabel.addClass('active');
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

    if (this.highlightMarker) {
      params.highlightMarker = this.highlightMarker;
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

  Map.prototype.zoomToCounty = function(e){
    var latLon = e.target.getCenter();
    var zoom = this.opt.markerZoomThreshold;
    this.map.flyTo(latLon, zoom, {
      duration: this.opt.flyDuration
    });
  };

  Map.prototype.zoomToItem = function(itemId, latlon){
    console.log('Item: ', itemId, latlon);
    latlon = _.map(latlon.split(","), function(v){ return parseFloat(v); });

    this.highlightMarker = false;
    if (this.lastSearchResults) {
      var foundItem = _.find(this.lastSearchResults, function(result){ return result.id === itemId; });
      if (foundItem) {
        this.highlightMarker = foundItem.id;
      }
    }

    var zoom = _.max([this.opt.itemZoomLevel, this.zoomLevel]);
    this.map.flyTo(new L.LatLng(latlon[0], latlon[1]), zoom, {
      duration: this.opt.flyDuration
    });
  };

  return Map;

})();

$(function() {
  var app = new Map({});
});
