'use strict';

var Item = (function() {

  function Item(config) {
    var defaults = {
      'endpoint': 'https://5go2sczyy9.execute-api.us-east-1.amazonaws.com/production/search',
      'id': '',
      'displayFields': ['alternate_name', 'image', 'description', 'text', 'source', 'sources', 'url', 'street_address', 'city', 'county', 'state', 'latlon', 'location_description', 'year_dedicated_or_constructed', 'object_types_search', 'use_types', 'subjects_search', 'honorees_search', 'creators_search', 'sponsors_search', 'dimensions', 'material', 'status', 'year_removed', 'vendor_entry_id', 'wikipedia'],
      'generatedFields': ['duplicate_of', 'duplicates', 'object_groups', 'object_group_reason', 'monument_types', 'entities_people', 'ethnicity_represented', 'gender_represented', 'entities_events', 'themes', 'geo_type', 'county_geoid']
    };
    var q = Util.queryParams();
    this.opt = _.extend({}, defaults, config, q);
    this.init();
  }

  function fieldToHTML(value, key, fields){
    var isList = Array.isArray(value);
    var html = '<tr>';
      html += '<td>'+key.replace('_search', '').replaceAll('_', ' ')+'</td>';
      if (isList && key === 'duplicates') {
        value = _.map(value, function(v){
          var dupeUrl =  'item.html?' + $.param({'id': v});
          return '<a href="'+dupeUrl+'" target="_blank" class="button">'+v+'</a>';
        })
        value = value.join(' ');
      } else if (isList && key == 'object_group_reason') {
        value = value.join('<br />');
      } else if (isList && key == 'sources' && value.length <= 1) {
        // hide this if only one source
        return '';
      } else if (isList) {
        value = _.map(value, function(v){
          var params = {
            q: '',
            facets: key + '~' + v
          };
          var facetUrl = 'map.html?' + $.param(params);
          return '<a href="'+facetUrl+'" class="button">'+v+'</a>';
        })
        value = value.join(' ');
      } else if (key === 'url') {
        value = '<a href="'+value+'" target="_blank">'+value+'</a>';
      } else if (key === 'latlon') {
        value = '<a href="https://www.google.com/maps/search/?api=1&query='+value.replace(' ','')+'" target="_blank">'+value+'</a>';
        if (_.has(fields, 'geo_type') && fields.geo_type == 'Approximate coordinates provided'){
          value += '<p class="alert">⚠ Coordinates provided by source are likely inaccurate</p>';
        }
      } else if (key === 'image') {
        value = '<a href="'+value+'" target="_blank"><img src="'+value+'" alt="Photograph of object" /></a>';
      } else if (key === 'duplicate_of') {
        var parentItemUrl = 'item.html?' + $.param({'id': value});
        value = '<a href="'+parentItemUrl+'" target="_blank" class="button">'+value+'</a>';
      }
      html += '<td>'+value+'</td>';
    html += '</tr>';
    return html;
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
    this.$dupes = $('#dupe-results');
    this.$reportLink = $('#report-link');
    this.allFields = _.union(this.opt.displayFields, this.opt.generatedFields);
    this.query();
  };

  Item.prototype.onQueryResponse = function(resp){
    console.log(resp);

    if (resp && resp.hits && resp.hits.hit && resp.hits.hit.length > 0) {
      this.renderResults(resp.hits.hit);
      this.queryDuplicates(resp.hits.hit[0])

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

  Item.prototype.queryDuplicates = function(result){
    var _this = this;
    var id = result.id;
    var fields = result.fields;
    if (!_.has(fields, 'duplicates')) return;

    var duplicateIds = fields.duplicates;
    var qstring = _.map(duplicateIds, function(id){ return "_id:'"+id+"'" });
    qstring = qstring.join(" ");
    qstring = '(or '+qstring+')';

    var q = {
      q: qstring,
      size: duplicateIds.length
    };
    q['q.parser'] = 'structured';
    var queryString = $.param(q);

    var url = this.opt.endpoint + '?' + queryString;
    console.log('Duplicates URL: ', url);

    $.getJSON(url, function(resp) {
      if (resp && resp.hits && resp.hits.hit && resp.hits.hit.length > 0) {
        _this.renderResults(resp.hits.hit, _this.$dupes, true);
        _this.$dupes.prepend($('<h2>Duplicate entries</h2><p>The following records are believed to be duplicates of each other and were merged to create the single record above.</p>'));
      }
    });
  };

  Item.prototype.renderResults = function(results, $el, isDupe){
    $el = $el || this.$results;
    var $reportLink = this.$reportLink;
    $el.empty();
    if (!results || !results.length) return;
    var html = '';
    var allFields = this.allFields;
    var displayFields = this.opt.displayFields;
    var generatedFields = this.opt.generatedFields;

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
      if (isDupe) name = (i+1) + '. ' + name;
      var subtitle = 'The following metadata was provided by data source:';
      if (_.has(fields, 'source') && fields.source === 'Multiple') {
        var duplicateCount = _.has(fields, 'duplicates') ? ' '+fields.duplicates.length : '';
        subtitle = 'The following metadata was merged from'+duplicateCount+' different sources. Scroll to the bottom to see the individual sources.';
      } else if (_.has(fields, 'source')) {
        subtitle = 'The following metadata was provided by data source '+fields.source+':';
      }
      if (i <= 0) {
        var reportUrl = 'https://docs.google.com/forms/d/e/1FAIpQLSchwiivhPxl6DGxdrO0Bk56zaa73AwzAH-GWt44Pmmnr2HDhQ/viewform?usp=sf_link&entry.846962896='+name+'&entry.632814286='+window.location.href;
        $reportLink.attr('href', reportUrl);
      }
      html += '<li class="result-item">';
        var itemParams = {'id': id}
        var itemUrl = 'item.html?' + $.param(itemParams);
        html += '<h4>'+name+'</h4>';
        html += '<p>'+subtitle+'</p>';
        html += '<table class="data-table">';
        _.each(displayFields, function(key){
          if (_.has(fields, key)) {
            html += fieldToHTML(fields[key], key, fields);
          }
        });
        html += '</table>';
        html += '<p>The following metadata was generated by Monument Lab based on metadata provided by source:</p>';
        html += '<table class="data-table generated">';
        _.each(generatedFields, function(key){
          if (_.has(fields, key)) {
            html += fieldToHTML(fields[key], key, fields);
          }
        });
        html += '</table>';
      html += '</li>';
    });
    html += '</ul>';
    $el.html(html);
  };

  return Item;

})();

$(function() {
  var app = new Item({});
});
