'use strict';

var Search = (function() {

  function Search(config) {
    var defaults = {
      'endpoint': 'https://5go2sczyy9.execute-api.us-east-1.amazonaws.com/production/search',
      'returnFacets': ['city', 'county', 'creators', 'honorees', 'object_types', 'source', 'sponsors', 'state', 'status', 'subjects', 'use_types', 'year_constructed', 'year_dedicated'], // note if these are changed, you must also update the allowed API Gateway queryParams for facet.X
      'facetSize': 20,
      'start': 0,
      'size': 100,
      'sort': false,
      'fields': '', // e.g. name,street_address
      'q': 'monument',
      'facets': '' // e.g. facetName1~value1!!value2!!value3__facetName2~value1
    };
    var q = Util.queryParams();
    this.opt = _.extend({}, defaults, config, q);
    this.init();
  }

  Search.prototype.init = function(msg){
    var isValid = Auth.authenticate();
    if (isValid) this.load();
  };

  Search.prototype.getQueryString = function(){
    var queryText = this.$query.val().trim();
    var isStructured = queryText.startsWith('(');
    var facetSize = this.opt.facetSize;
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

    // empty search
    if (isEmptyQuery && isEmptyFacets) {
      q.q = 'matchall';
      q['q.parser'] = 'structured';

    } else if (!isStructured) {
      // build filter string
      if (!isEmptyFacets) {
        // e.g. (and title:'star' (or actors:'Harrison Ford' actors:'William Shatner'))
        var fqstring = '(and ';
        var filterString = _.map(facets, function(values, key){
          if (values.length === 1) {
            if (isNaN(values[0])) {
              return key + ":'" + values[0] + "'";
            } else {
              return key + ":" + values[0];
            }
          } else {
            var orString = '(or ';
            var orValuesString = _.map(values, function(value){
              if (isNaN(value)) {
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
    var facetString = _.each(this.opt.returnFacets, function(facet){
      q['facet.'+facet] = '{sort:\'count\', size:'+facetSize+'}';
    });

    console.log('Query object: ', q);
    var qstring = $.param(q);

    return qstring;
  };

  Search.prototype.load = function(){
    this.isLoading = false;
    this.$form = $('#search-form');
    this.$facets = $('#facets');
    this.$results = $('#search-results');
    this.$resultMessage = $('#search-results-message');
    this.$query = $('input[name="query"]').first();
    this.facets = {};
    this.size = this.opt.size;
    this.start = this.opt.start;
    this.sort = this.opt.sort;

    this.loadFromOptions();
    this.loadListeners();
    this.$form.trigger('submit');
  };

  Search.prototype.loadFromOptions = function(){
    var q = this.opt.q.trim();
    this.$query.val(q);

    // select specific fields to search in
    if (this.opt.fields && this.opt.fields.length) {
      var selectedFields = this.opt.fields.split(',');
      $('.field-checkbox').each(function(){
        var $input = $(this);
        var value = $input.val();
        if (_.indexOf(selectedFields, value)) {
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
  };

  Search.prototype.loading = function(isLoading){
    this.isLoading = isLoading;

    if (isLoading) {
      $('body').addClass('loading');
      $('button, input').prop('disabled', true);
    } else {
      $('body').removeClass('loading');
      $('button, input').prop('disabled', false);
    }
  };

  Search.prototype.loadListeners = function(){
    var _this = this;

    this.$form.on('submit', function(e){
      e.preventDefault();
      if (!_this.isLoading) _this.onSearchSubmit();
    });

    $('body').on('change', '.facet-checkbox', function(e){
      _this.onFacetCheckboxChange($(this));
    });

    $('body').on('click', '.apply-facet-changes-button', function(e){
      if (!_this.isLoading) _this.updateFacets();
    });

    $('body').on('click', '.remove-facet', function(e){
      if (!_this.isLoading) {
        var $el = $(this);
        var key = $el.attr('data-key');
        var value = $el.attr('data-value');
        _this.removeFacet(key, value);
      }
    });
  };

  Search.prototype.onFacetCheckboxChange = function($input){
    var $parent = $input.closest('.facet');
    $parent.addClass('changed');
  };

  Search.prototype.onQueryResponse = function(resp){
    console.log(resp);
    this.loading(false);

    if (resp && resp.hits && resp.hits.hit && resp.hits.hit.length > 0) {
      this.renderResultMessage(resp.hits.found, resp.hits.start);
      this.renderResults(resp.hits.hit, resp.facets);
    } else {
      this.renderResultMessage(0, this.start);
      this.renderResults([], {});
    }

  };

  Search.prototype.onSearchSubmit = function(){
    if (this.isLoading) return;

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

    this.facets[key] = _.without(this.facets[key], value);
    if (this.facets[key].length < 1) {
      this.facets = _.omit(this.facets, key);
    }
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
      this.$facets.removeClass('active');
      return;
    }

    this.$facets.addClass('active');
    var html = '';
    _.each(facets, function(obj, key){
      var title = key.replace('_', ' ');
      var buckets = obj.buckets;
      html += '<fieldset class="facet active">';
        var sectionTitle = title+' ('+buckets.length+')';
        html += '<legend class="toggle-parent" data-active="'+sectionTitle+' ▼" data-inactive="'+sectionTitle+' ◀">'+sectionTitle+' ▼</legend>';
        html += '<div class="facet-input-group">';
        _.each(buckets, function(bucket, j){
          var id = 'facet-'+key+'-'+j;
          var checked = '';
          if (_.has(selectedFacets, key) && _.indexOf(selectedFacets[key], bucket.value) >= 0) checked = 'checked ';
          html += '<label for="'+id+'"><input type="checkbox" name="'+key+'" id="'+id+'" value="'+bucket.value+'" class="facet-checkbox" '+checked+'/>'+bucket.value+' ('+Util.formatNumber(bucket.count)+')</label>'
        });
        html += '<button type="button" class="apply-facet-changes-button">Apply all changes</button>';
        html += '</div>';
      html += '</fieldset>';
    });

    this.$facets.html(html);
  };

  Search.prototype.renderResultMessage = function(totalCount, offsetStart){
    var $container = this.$resultMessage;
    var queryText = this.$query.val().trim();
    var size = this.size;
    var startNumber = offsetStart * size + 1;
    var endNumber = Math.min(totalCount, startNumber + size - 1);

    var html = '<p>';
      html += 'Found ' + Util.formatNumber(totalCount) + ' records with query <strong>"' + queryText + '"</strong>';
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

  Search.prototype.renderResults = function(results, facets){
    this.renderFacets(facets);

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
        html += '<h4>'+(i+1+start)+'. '+name+'</h4>';
        html += '<table class="data-table">';
        _.each(fields, function(value, key){
          var isList = Array.isArray(value);
          html += '<tr>';
            html += '<td>'+key.replace('_search', '').replace('_', ' ')+'</td>';
            if (isList) {
              value = _.map(value, function(v){
                var params = {
                  q: '',
                  facets: key + '~' + v
                };
                var facetUrl = '?' + $.param(params);
                return '<a href="'+facetUrl+'" class="button">'+v+'</a>';
              })
              value = value.join(' ');
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
    this.facets = facets;
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
