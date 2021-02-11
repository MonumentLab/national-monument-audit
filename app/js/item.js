'use strict';

var Item = (function() {

  function Item(config) {
    var defaults = {
      'endpoint': 'https://5go2sczyy9.execute-api.us-east-1.amazonaws.com/production/search',
      'id': ''
    };
    var q = Util.queryParams();
    this.opt = _.extend({}, defaults, config, q);
    this.init();
  }

  Item.prototype.init = function(){
    this.id = this.opt.id;
    this.load();
  };

  Item.prototype.getQueryObject = function(){
    var q = {
      q: "_id:'"+this.id+"'",
      size: 1
    };
    q['q.parser'] = 'structured';
    return q;
  };

  Item.prototype.getQueryString = function(){
    var q = this.getQueryObject();
    var qstring = $.param(q);
    return qstring;
  };

  Item.prototype.load = function(){
    this.$results = $('#search-results');
    this.query();
  };

  Item.prototype.onQueryResponse = function(resp){
    console.log(resp);

    if (resp && resp.hits && resp.hits.hit && resp.hits.hit.length > 0) {
      this.renderResults(resp.hits.hit);

    } else {
      this.renderResults([]);
    }

  };

  Item.prototype.query = function(){
    var _this = this;
    var queryString = this.getQueryString();
    var url = this.opt.endpoint + '?' + queryString;
    console.log('Item URL: ', url);

    $.getJSON(url, function(resp) {
      _this.onQueryResponse(resp);
    });
  };

  Item.prototype.renderResults = function(results){
    this.$results.empty();
    if (!results || !results.length) return;
    var html = '';

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
        html += '<h4>'+name+'</h4>';
        html += '<table class="data-table">';
        _.each(fields, function(value, key){
          var isList = Array.isArray(value);
          html += '<tr>';
            html += '<td>'+key.replace('_search', '').replaceAll('_', ' ')+'</td>';
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
            } else if (key === 'url') {
              value = '<a href="'+value+'" target="_blank">'+value+'</a>';
            } else if (key === 'latlon') {
              value = '<a href="https://www.google.com/maps/search/?api=1&query='+value.replace(' ','')+'" target="_blank">'+value+'</a>';
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

  return Item;

})();

$(function() {
  var app = new Item({});
});
