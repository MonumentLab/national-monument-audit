'use strict';

var Search = (function() {

  function Search(config) {
    var defaults = {
      'endpoint': 'https://search-national-monument-audit-nuccsr3nq7s5kshgvyx4kuxsdq.us-east-1.cloudsearch.amazonaws.com/2013-01-01/search',
      'facets': ['city', 'county', 'creators', 'honorees', 'object_types', 'source', 'sponsors', 'state', 'status', 'subjects', 'use_types', 'year_constructed', 'year_dedicated'],
      'facetSize': 20
    };
    var q = Util.queryParams();
    this.opt = _.extend({}, defaults, config, q);
    this.init();
  }

  Search.prototype.init = function(msg){

    this.isLoading = false;
    this.$form = $('#search-form');
    this.$query = $('input[name="query"]').first();
    this.filters = {};

    if (this.opt.q) {
      this.$query.val(this.opt.q);
    } else {
      this.$query.val('monument');
    }

    this.loadListeners();
    this.$form.trigger('submit');
  };

  Search.prototype.getQueryString = function(){
    var queryText = this.$query.val();
    var isStructured = queryText.startsWith('(');
    var facetSize = this.opt.facetSize;
    var qstring = 'q=' + queryText;
    var filters = _.clone(this.filters);

    // build query string, e.g. 'title^5','description'
    if (!isStructured) {
      // we need to add a filter to an empty search
      if (queryText.length < 1 && _.isEmpty(filters)) {
        filters.object_types = 'Monument';
      }

      // build filter string
      if (!_.isEmpty(filters)) {
        var fqstring = 'fq=(and ';
        var filterString = _.map(filters, function(value, key){
          if (isNaN(value)) {
            return key + ":'" + value + "'";
          } else {
            return key + ":" + value;
          }
        });
        filterString = filterString.join(' ');
        fqstring += filterString + ')';
        qstring += '&' + fqstring;
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
        var optionString = 'q.options={fields: ['+fieldsString+']}';
        qstring += '&' + optionString;
      }

    // structured queries, simply submit as is
    } else {
      qstring += '&q.parser=structured';
    }

    // build facet string
    var facetString = _.map(this.opt.facets, function(facet){
      return 'facet.'+facet+'={sort:\'count\', size:'+facetSize+'}';
    });
    facetString = facetString.join('&');
    qstring += '&' + facetString;

    return qstring;
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

    console.log(url);

    // $.getJSON(url, function(resp) {
    //   _this.onQueryResponse(resp);
    // });
  };

  return Search;

})();

$(function() {
  var app = new Search({});
});
