'use strict';

var Search = (function() {

  function Search(config) {
    var defaults = {
      'endpoint': 'https://5go2sczyy9.execute-api.us-east-1.amazonaws.com/production/search',
      'facets': ['city', 'county', 'creators', 'honorees', 'object_types', 'source', 'sponsors', 'state', 'status', 'subjects', 'use_types', 'year_constructed', 'year_dedicated'], // note if these are changed, you must also update the allowed API Gateway queryParams for facet.X
      'facetSize': 20,
      'size': 100,
      'sort': '_score desc'
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
    var queryText = this.$query.val();
    var isStructured = queryText.startsWith('(');
    var facetSize = this.opt.facetSize;
    var q = {
      q: queryText,
      size: this.size,
      start: this.start,
      sort: this.sort
    };
    var filters = _.clone(this.filters);

    // build query string, e.g. 'title^5','description'
    if (!isStructured) {
      // we need to add a filter to an empty search
      if (queryText.length < 1 && _.isEmpty(filters)) {
        filters.object_types = 'Monument';
      }

      // build filter string
      if (!_.isEmpty(filters)) {
        var fqstring = '(and ';
        var filterString = _.map(filters, function(value, key){
          if (isNaN(value)) {
            return key + ":'" + value + "'";
          } else {
            return key + ":" + value;
          }
        });
        filterString = filterString.join(' ');
        fqstring += filterString + ')';
        q.fq = fqstring;
      }

      // build search fields string
      if (queryText.length > 0) {
        var fieldsString = $('#input-field-list input:checked').map(function(){
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
    var facetString = _.each(this.opt.facets, function(facet){
      q['facet.'+facet] = '{sort:\'count\', size:'+facetSize+'}';
    });

    var qstring = $.param(q);

    return qstring;
  };

  Search.prototype.load = function(){
    this.isLoading = false;
    this.$form = $('#search-form');
    this.$facets = $('#facets');
    this.$results = $('#search-results');
    this.$query = $('input[name="query"]').first();
    this.filters = {};
    this.size = this.opt.size;
    this.start = 0;
    this.sort = this.opt.sort;

    if (this.opt.q) {
      this.$query.val(this.opt.q);
    } else {
      this.$query.val('monument');
    }

    this.loadListeners();
    this.$form.trigger('submit');
  };

  Search.prototype.loading = function(isLoading){
    this.isLoading = isLoading;

    if (isLoading) {
      $('body').addClass('loading');
      $('button').prop('disabled', true);
    } else {
      $('body').removeClass('loading');
      $('button').prop('disabled', false);
    }
  };

  Search.prototype.loadListeners = function(){
    var _this = this;

    this.$form.on('submit', function(e){
      e.preventDefault();
      _this.onSearchSubmit();
    })
  };

  Search.prototype.onQueryResponse = function(resp){
    console.log(resp);
    this.loading(false);

    if (resp && resp.hits && resp.hits.found && resp.hits.found > 0) {
      this.renderResults(resp.hits.hit, resp.facets);
    } else {
      this.renderEmpty();
    }


  };

  Search.prototype.onSearchSubmit = function(){
    if (this.isLoading) return;
    this.loading(true);

    this.query();
  };

  Search.prototype.query = function(){
    var _this = this;
    var queryString = this.getQueryString();
    var url = this.opt.endpoint + '?' + queryString;

    console.log('Search URL: ', url);

    $.getJSON(url, function(resp) {
      _this.onQueryResponse(resp);
    });
  };

  Search.prototype.renderEmpty = function(){
    this.renderFacets({});
    this.$results.empty();
  };

  Search.prototype.renderFacets = function(facets){
    facets = facets || {};

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
        _.each(buckets, function(bucket, j){
          var id = 'facet-'+key+'-'+j;
          html += '<label for="'+id+'"><input type="checkbox" name="'+key+'" id="'+id+'" value="'+bucket.value+'" class="facet-checkbox" />'+bucket.value+' ('+Util.formatNumber(bucket.count)+')</label>'
        });
      html += '</fieldset>';
    });

    this.$facets.html(html);
  };

  Search.prototype.renderResults = function(results, facets){
    if (!results || !results.length) {
      this.renderEmpty();
      return;
    }

    this.renderFacets(facets);

    this.$results.empty();
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
            html += '<td>'+key.replace('_', ' ')+'</td>';
            if (isList) {
              value = _.map(value, function(v){
                return '<span class="data-item">'+v+'</span>'
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

  return Search;

})();

$(function() {
  var app = new Search({});
});
