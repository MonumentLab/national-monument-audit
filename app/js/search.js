'use strict';

var Search = (function() {

  function Search(config) {
    var defaults = {
      'endpoint': 'https://5go2sczyy9.execute-api.us-east-1.amazonaws.com/production/search',
      'returnFacets': ['object_groups', 'monument_types', 'entities_people', 'entities_events', 'source', 'geo_type', 'subjects', 'object_types', 'is_duplicate', 'has_duplicates', 'creators', 'city', 'county', 'sponsors', 'state', 'status', 'use_types', 'year_dedicated_or_constructed'], // note if these are changed, you must also update the allowed API Gateway queryParams for facet.X and redeploy the API
      'facetSize': 30,
      'customFacetSizes': {
        'state': 100,
        'year_dedicated_or_constructed': 100
      },
      'start': 0,
      'size': 100,
      'sort': '',
      'fields': '', // e.g. name,street_address
      'q': 'monument',
      'facets': '' // e.g. facetName1~value1!!value2!!value3__facetName2~value1
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

  Search.prototype.init = function(){
    var isValid = Auth.authenticate();
    if (isValid) this.load();
  };

  Search.prototype.getQueryObject = function(){
    var queryText = this.$query.val().trim();
    var isStructured = queryText.startsWith('(');
    var isDocumentSearch = this.isDocumentSearch;
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
    if (isDocumentSearch) {
      q['q.parser'] = 'structured';

    // empty search
    } else if (isEmptyQuery && isEmptyFacets) {
      q.q = 'matchall';
      q['q.parser'] = 'structured';

    } else if (!isStructured) {
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

    // structured queries, simply submit as is
    } else {
      q['q.parser'] = 'structured';
    }

    // build facet string
    if (!isDocumentSearch) {
      var facetString = _.each(this.opt.returnFacets, function(facet){
        var _size = facetSize;
        if (_.has(customFacetSizes, facet)) _size = customFacetSizes[facet];
        q['facet.'+facet] = '{sort:\'count\', size:'+_size+'}';
      });
    }

    console.log('Query object: ', q);

    return q;
  };

  Search.prototype.getQueryString = function(){
    var q = this.getQueryObject();
    var qstring = $.param(q);
    return qstring;
  };

  Search.prototype.load = function(){
    var _this = this;
    this.isLoading = false;
    this.$form = $('#search-form');
    this.$facetsContainer = $('#facets-container');
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
    this.isDocumentSearch = this.opt.q.startsWith('_id');
    this.mapData = false;
    this.yearRangeValue = false;

    this.map = new SearchMap({
      onQuery: function(data){
        _this.onMapQuery(data);
      }
    });

    this.timeline = new Timeline({
      yearRange: [1700, 2021]
    });

    this.loadFromOptions();
    this.loadListeners();
    this.query();
  };

  Search.prototype.loadFromOptions = function(){
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

    if (this.opt.mapWidth) {
      this.mapData = {
        urlProps: {
          mapCenterLat: this.opt.mapCenterLat,
          mapCenterLon: this.opt.mapCenterLon,
          mapWidth: this.opt.mapWidth,
          mapHeight: this.opt.mapHeight
        }
      }
    }

    if (_.has(this.facets, 'year_dedicated_or_constructed') && isArrayString(this.facets.year_dedicated_or_constructed[0])) {
      this.yearRangeValue = this.facets.year_dedicated_or_constructed[0];
      var yearRange = JSON.parse(this.yearRangeValue);
      this.timeline.setRange(yearRange);
    }

  };

  Search.prototype.loading = function(isLoading){
    this.isLoading = isLoading;

    if (isLoading) {
      $('body').addClass('loading');
      $('button, input, select').prop('disabled', true);
    } else {
      $('body').removeClass('loading');
      $('button, input, select').prop('disabled', false);
    }
  };

  Search.prototype.loadListeners = function(){
    var _this = this;

    this.$form.on('submit', function(e){
      e.preventDefault();
      if (!_this.isLoading) _this.onSearchSubmit();
    });

    this.$sort.on('change', function(){
      _this.onSortChange($(this).val());
    });

    $('body').on('change', '.facet-checkbox', function(e){
      // _this.onFacetCheckboxChange($(this));
      if (!_this.isLoading) _this.updateFacets();
    });

    $(document).on('change-year-range', function(e, newRange) {
      if (!_this.isLoading) _this.onChangeYearRange(newRange);
    });

    // $('body').on('click', '.apply-facet-changes-button', function(e){
    //   if (!_this.isLoading) _this.updateFacets();
    // });

    $('body').on('click', '.remove-facet', function(e){
      if (!_this.isLoading) {
        var $el = $(this);
        var key = $el.attr('data-key');
        var value = $el.attr('data-value');
        _this.removeFacet(key, value);
      }
    });
  };

  Search.prototype.onChangeYearRange = function(newYearRange){
    console.log('New year range triggered: '+newYearRange);
    if (!newYearRange || newYearRange.length !== 2) return;
    var yearRange = _.map(newYearRange, function(y){ return parseInt(y); });
    this.yearRangeValue = JSON.stringify(yearRange).replaceAll('"', "'");
    if (_.has(this.facets, 'year_dedicated_or_constructed') && !isArrayString(this.facets.year_dedicated_or_constructed[0])) {
      console.log('Remove "year dedicated or constructed" facet before using year range selector');
    } else {
      this.facets.year_dedicated_or_constructed = [this.yearRangeValue];
    }
    this.query();
  };

  Search.prototype.onFacetCheckboxChange = function($input){
    var $parent = $input.closest('.facet');
    $parent.addClass('changed');
  };

  Search.prototype.onMapQuery = function(data){
    this.mapData = data;
    this.facets.latlon = [JSON.stringify(data.latlon).replaceAll('"', "'")];
    this.query();
  };

  Search.prototype.onQueryResponse = function(resp){
    console.log(resp);
    this.loading(false);

    if (resp && resp.hits && resp.hits.hit && resp.hits.hit.length > 0) {
      this.renderResultMessage(resp.hits.found);
      this.renderResults(resp.hits.hit);
      this.renderFacets(resp.facets);
      this.renderPagination(resp.hits.found);

    } else {
      this.renderResultMessage(0);
      this.renderResults([]);
      this.renderFacets({});
      this.renderPagination(0);
    }

  };

  Search.prototype.onSearchSubmit = function(){
    if (this.isLoading) return;
    this.start = 0;
    this.query();
  };

  Search.prototype.onSortChange = function(sortValue){
    if (this.isLoading) return;
    this.start = 0;
    this.sort = sortValue;
    this.query();
  };

  Search.prototype.query = function(){
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

  Search.prototype.removeFacet = function(key, value){
    if (!_.has(this.facets, key)) return;

    console.log('Removing ', key, value);

    if (key === 'latlon'){
      this.map.reset();
      this.mapData = false;
    }

    if (key === 'year_dedicated_or_constructed'){
      this.yearRangeValue = false;
      this.timeline.reset();
    }

    this.facets[key] = _.without(this.facets[key], value);
    if (this.facets[key].length < 1) {
      this.facets = _.omit(this.facets, key);
    }
    this.start = 0;
    this.query();
  };

  Search.prototype.renderFacets = function(facets){
    facets = facets || {};

    var selectedFacets = this.facets;
    facets = _.pick(facets, function(obj, key) {
      return obj && obj.buckets && obj.buckets.length > 0;
    });

    this.$facets.empty();
    if (_.isEmpty(facets)) {
      this.$facetsContainer.removeClass('active');
      return;
    }

    this.$facetsContainer.addClass('active');
    var html = '';
    var facetSize = this.opt.facetSize;
    _.each(this.opt.returnFacets, function(key){
      if (!_.has(facets, key)) return;
      var obj = facets[key];
      var title = key.replace('_', ' ');
      var buckets = obj.buckets;
      html += '<fieldset class="facet active">';
        if (buckets.length > facetSize) {
          buckets = buckets.slice(0, facetSize);
        }
        var sectionTitle = title+' ('+buckets.length+')';
        html += '<legend class="toggle-parent" data-active="'+sectionTitle+' ▼" data-inactive="'+sectionTitle+' ◀">'+sectionTitle+' ▼</legend>';
        html += '<div class="facet-input-group">';
        _.each(buckets, function(bucket, j){
          var id = 'facet-'+key+'-'+j;
          var checked = '';
          if (_.has(selectedFacets, key) && _.indexOf(selectedFacets[key], bucket.value) >= 0) checked = 'checked ';
          var label = ''+bucket.value;
          if (title.startsWith("is ") || title.startsWith("has ")) {
            if (label=="1") label = "yes";
            else if (label=="0") label = "no";
          }
          html += '<label for="'+id+'"><input type="checkbox" name="'+key+'" id="'+id+'" value="'+bucket.value+'" class="facet-checkbox" '+checked+'/>'+label+' ('+Util.formatNumber(bucket.count)+')</label>'
        });
        html += '<button type="button" class="apply-facet-changes-button">Apply all changes</button>';
        html += '</div>';
      html += '</fieldset>';
    });

    if (_.has(facets, 'state')) {
      this.map.renderResults(facets.state.buckets);
    } else {
      this.map.renderResults([]);
    }

    var years = [];
    if (_.has(facets, 'year_dedicated_or_constructed')) years = facets.year_dedicated_or_constructed.buckets;
    this.timeline.renderResults(years);

    this.$facets.html(html);
  };

  Search.prototype.renderPagination = function(totalCount){
    this.$pagination.empty();
    if (totalCount <= 0) return;

    var offsetStart = this.start;
    var size = this.size;
    var pages = Math.ceil(totalCount / size);
    var currentPage = Math.floor(offsetStart / size);

    var html = '<p>Go to page:';
    var queryObj = _.clone(this.currentQueryParams);
    queryObj = _.omit(queryObj, 'start');
    _.times(pages, function(page){
      if (page > 0) {
        queryObj.start = page * size + 1;
      }
      var url = '?' + $.param(queryObj);
      if (page === currentPage) {
        html += '<span class="page-link">'+(page+1)+'</span>';
      } else {
        html += '<a href="'+url+'" class="page-link">'+(page+1)+'</a>';
      }
    });
    html += '</p>';

    this.$pagination.html(html);
  };

  Search.prototype.renderResultMessage = function(totalCount){
    var $container = this.$resultMessage;
    var offsetStart = this.start;
    var queryText = this.$query.val().trim();
    var size = this.size;
    var startNumber = Math.max(1, offsetStart);
    var endNumber = Math.min(totalCount, startNumber + size - 1);

    var html = '<p>';
      html += 'Found ' + Util.formatNumber(totalCount) + ' records';
      if (queryText.length > 0) html +=' with query <strong>"' + queryText + '"</strong>';
      if (!_.isEmpty(this.facets)){
        html += ' with facets: ';
        _.each(this.facets, function(values, key){
          var title = key.replace('_', ' ');
          _.each(values, function(value){
            html += '<button type="button" class="remove-facet" data-key="'+key+'" data-value="'+value+'"><strong>'+title+'</strong>: "'+value+'" <strong>×</strong></button>';
          });
        });
      }
      html += '. Showing results ' + Util.formatNumber(startNumber) + ' to ' + Util.formatNumber(endNumber) + '.';
    html += '</p>';
    $container.html(html);
  };

  Search.prototype.renderResults = function(results){
    this.$results.empty();
    if (!results || !results.length) return;
    var html = '';
    var start = this.start;

    html += '<ul class="result-list">';
    _.each(results, function(result, i){
      var id = result.id;
      var fields = result.fields;
      var name = '';
      if (_.has(fields, 'name')) {
        name = fields.name;
        fields = _.omit(fields, 'name');
      }
      if (name.length < 1) name = '<em>[Untitled]</em>';
      html += '<li class="result-item">';
        var itemParams = {'id': id}
        var itemUrl = 'item.html?' + $.param(itemParams);
        html += '<h4>'+(i+1+start)+'. <a href="'+itemUrl+'" target="_blank">'+name+'</a></h4>';
        html += '<table class="data-table">';
        _.each(fields, function(value, key){
          var isList = Array.isArray(value);
          html += '<tr>';
            html += '<td>'+key.replace('_search', '').replaceAll('_', ' ')+'</td>';
            if (isList && key === 'duplicates') {
              value = _.map(value, function(v){
                var dupeUrl =  'item.html?' + $.param({'id': v});
                return '<a href="'+dupeUrl+'" target="_blank" class="button">'+v+'</a>';
              })
              value = value.join(' ');
            } else if (isList && key == 'object_group_reason') {
              value = value.join('<br />');
            } else if (isList) {
              value = _.map(value, function(v){
                var params = {
                  q: '',
                  facets: key + '~' + v
                };
                var facetUrl = '?' + $.param(params);
                return '<a href="'+facetUrl+'" class="button">'+v+'</a>';
              })
              value = value.join(' ');
            } else if (key === 'url') {
              value = '<a href="'+value+'" target="_blank">'+value+'</a>';
            } else if (key === 'latlon') {
              value = '<a href="https://www.google.com/maps/search/?api=1&query='+value.replace(' ','')+'" target="_blank">'+value+'</a>';
            } else if (key === 'image') {
              value = '<a href="'+value+'" target="_blank">Image link</a>';
            } else if (key === 'duplicate_of') {
              var parentItemUrl = 'item.html?' + $.param({'id': value});
              value = '<a href="'+parentItemUrl+'" target="_blank" class="button">'+value+'</a>';
            }
            html += '<td>'+value+'</td>';
          html += '</tr>';
        });
        html += '</table>';
      html += '</li>';
    });
    html += '</ul>';
    this.$results.html(html);
  };

  Search.prototype.updateFacets = function(){
    var facets = {};
    // retain latlon, year if present
    var latlon = _.has(this.facets, 'latlon') ? this.facets.latlon : false;
    $('.facet-checkbox:checked').each(function(){
      var $input = $(this);
      var facetName = $input.attr('name');
      var facetValue = $input.val();
      if (_.has(facets, facetName)) {
        facets[facetName].push(facetValue);
      } else {
        facets[facetName] = [facetValue];
      }
    });
    if (latlon !== false) facets.latlon = latlon;
    // add year range if year not present
    var yearRangeValue = this.yearRangeValue;
    if (!_.has(facets, 'year_dedicated_or_constructed') && yearRangeValue !== false) {
      facets.year_dedicated_or_constructed = [yearRangeValue];
    // year facet has been selected; ignore year range
    } else if (_.has(facets, 'year_dedicated_or_constructed')) {
      this.yearRangeValue = false;
      this.timeline.reset();
    }
    this.facets = facets;
    this.start = 0;
    this.query();
  };

  Search.prototype.updateURL = function(){
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

  return Search;

})();

$(function() {
  var app = new Search({});
});
