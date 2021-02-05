'use strict';

var Dashboard = (function() {

  function Dashboard(config) {
    var defaults = {
      'entityDataUrl': 'data/entities-summary.json',
      'summaryDataUrl': 'data/dashboard.json',
      'recordsUrl': 'data/records.json',
      'searchUrl': 'https://5go2sczyy9.execute-api.us-east-1.amazonaws.com/production/search'
    };
    var q = Util.queryParams();
    this.opt = _.extend({}, defaults, config, q);
    this.init();
  }

  Dashboard.prototype.init = function(msg){
    var isValid = Auth.authenticate();
    if (isValid) this.load();
  };

  Dashboard.prototype.load = function(){
    var _this = this;
    // set globals
    Chart.defaults.global.defaultFontColor = 'black';
    _.templateSettings = {
      interpolate: /\{\{(.+?)\}\}/g
    };

    $('body').removeClass('hidden');

    $.when(this.loadSummaryData()).done(function(){
      console.log('Loaded summary data.');
      _this.onSummaryDataLoaded();
    });

    $.when(this.loadFacetData(), this.loadEntityData()).done(function(){
      console.log('Loaded facet and entity data.')
      _this.onFacetDataLoaded();
    });

    $.when(this.loadRecords()).done(function(){
      console.log('Loaded record data.');
      _this.onRecordDataLoaded();
    });

  };

  Dashboard.prototype.loadAvailabilities = function(){
    var barData = _.map(this.summaryData.availabilities, function(params, key){
      return {
        percent: params.values[0],
        label: params.title
      }
    });
    this.loadBars($('#data-field-availability'), barData);
  };

  Dashboard.prototype.loadBars = function($container, barData){
    var html = '';
    _.each(barData, function(bar){
      var value = bar.percent + '%';
      if (_.has(bar, 'count')) value = Util.formatNumber(bar.count) + ' ('+value+')';
      var label = bar.label;
      if (bar.url) label = '<a href="'+bar.url+'">'+label+'</a>';
      html += '<div class="bar-container">';
        html += '<div class="bar" style="width: '+bar.percent+'%"></div>';
        html += '<div class="label"><div>'+label+'</div> <div>'+value+'</div></div>';
      html += '</div>';
    });
    $container.html(html);
  };

  Dashboard.prototype.loadDataTables = function(){
    var $parent = $('#data-frequencies');
    $parent.empty();

    _.each(this.facetData, function(entry, key){
      entry.title = 'Top '+entry.buckets.length+' values for "'+key.replace('_', ' ')+'"';
      entry.resourceLink = 'monumentlab_national_monuments_audit_final_'+key+'.csv';
      entry.cols = ['Values', 'Count'];
      entry.rows = _.map(entry.buckets, function(bucket){ return [bucket.value, Util.formatNumber(bucket.count)]; })
      var table = new DataTable(_.extend(entry, {'$parent': $parent}));
    });

    $parent = $('#entity-frequencies');
    $parent.empty();
    _.each(this.entityData.frequencies, function(entry){
      var table = new DataTable(_.extend(entry, {'$parent': $parent}));
    });
  };

  Dashboard.prototype.loadEntityData = function(){
    var _this = this;
    return $.getJSON(this.opt.entityDataUrl, function(data){
      _this.entityData = data;
    });
  };

  Dashboard.prototype.loadFacetData = function(){
    var _this = this;
    var query = {
      "facet.creators": "{sort:'count', size:10}",
      "facet.honorees": "{sort:'count', size:10}",
      "facet.monument_types": "{sort:'count', size:10}",
      "facet.object_types": "{sort:'count', size:10}",
      "facet.sponsors": "{sort:'count', size:10}",
      "facet.status": "{sort:'count', size:10}",
      "facet.subjects": "{sort:'count', size:10}",
      "facet.use_types": "{sort:'count', size:10}",
      "q": "matchall",
      "q.parser": "structured",
      "return": "_no_fields"
    };
    var url = this.opt.searchUrl + '?' + $.param(query);

    return $.getJSON(url, function(resp) {
      _this.facetData =  _.omit(resp.facets, 'monument_types');
      _this.monumentTypes = resp.facets.monument_types;
    });

  };

  Dashboard.prototype.loadMap = function(){
    var map = new Map({data: this.recordData, yearRange: this.timeline.range});
  };

  Dashboard.prototype.loadFacets = function(){
    var facets = new Facets({data: this.recordData, yearRange: this.timeline.range});
  };

  Dashboard.prototype.loadObjectTypes = function(){
    var sum = _.reduce(this.monumentTypes.buckets, function(memo, bucket){ return memo + bucket.count; }, 0);
    var barData = _.map(this.monumentTypes.buckets, function(bucket){
      var params = {
        facets: 'monument_types~'+bucket.value,
        q: ''
      }
      return {
        percent: MathUtil.round(bucket.count / sum * 100, 2),
        count: bucket.count,
        label: bucket.value,
        url: 'search.html?' + $.param(params)
      }
    });
    this.loadBars($('#data-types'), barData);
  };

  Dashboard.prototype.loadPieCharts = function(){
    _.each(this.entityData.pieCharts, function(params, key){
      var chart = new PieChart(_.extend(params, {el: '#'+key}));
    });
  };

  Dashboard.prototype.loadRecords = function(){
    var _this = this;
    return $.getJSON(this.opt.recordsUrl, function(data){
      _this.recordData = Util.parseData(data);
      console.log('Loaded '+_this.recordData.length+ ' records');
    });
  };

  Dashboard.prototype.loadSources = function(){
    var sources = this.summaryData.sources;
    var $container = $('#data-sources');
    var codeBaseUrl = 'https://github.com/MonumentLab/national-monument-audit/tree/main/';

    var html = '';
    _.each(sources, function(s){
      html += '<div class="data-source">';
        var name = s.verboseName ? s.verboseName : s.name;
        html += '<h4><a href="'+s.url+'" target="_blank">'+name+' 🔗</a></h4>';

        html += '<div class="record-count-container">';
          if (s.percentOfTotal > 0) html += '<div class="record-count-bar" style="width: '+s.percentOfTotal+'%"></div>';
          html += '<div class="record-count-text">'+Util.formatNumber(s.recordCount)+' records ('+s.percentOfTotal+'% of total)</div>';
        html += '</div>';

        html += '<button type="button" class="toggle-parent" data-active="Hide details" data-inactive="Show details">Show details</button>';

        html += '<div class="data-source-details">';
          html += '<table class="data-table data-source-table">';
            // source
            var sourcePath = s.dataPath.split('/');
            var filename = sourcePath.pop();
            var sourceDir = sourcePath.join('/');
            var sourceLink = codeBaseUrl + sourceDir;
            html += '<tr>';
              html += '<td>Pre-processed data file:</td>';
              html += '<td><a href="'+sourceLink+'" target="_blank">'+sourceDir+'/'+filename+'</a></td>';
            html += '</tr>';

            var configLink = codeBaseUrl + s.configFile;
            html += '<tr>';
              html += '<td>Config file:</td>';
              html += '<td><a href="'+configLink+'" target="_blank">'+s.configFile+'</a></td>';
            html += '</tr>';

            // date
            html += '<tr>';
              html += '<td>Date accessed data:</td>';
              html += '<td>'+s.dateDataAccessed+'</td>';
            html += '</tr>';

            // field list
            html += '<tr>';
              html += '<td>Fields used</td>';
              html += '<td>';
              _.each(s.properties, function(p){
                html += '<span class="data-item">'+p+'</span>'
              });
              html += '</td>';
            html += '</tr>';

            // field list
            html += '<tr>';
              html += '<td>Field mappings</td>';
              html += '<td>';
              _.each(s.mappings, function(p, property){
                html += '<span class="data-item">'+property+' ⇒ '+p.to+'</span>';
              });
              html += '</td>';
            html += '</tr>';

            // filters
            if (_.has(s, 'filter')){
              html += '<tr>';
                html += '<td>Filter</td>';
                html += '<td><code>'+s.filter.replaceAll('\|', ', ')+'</code></td>';
              html += '</tr>';
              html += '<tr>';
                html += '<td>Records before filtering</td>';
                var percentFiltered = MathUtil.round(s.recordCount / s.recordCountBeforeFiltering * 100, 2);
                html += '<td>'+Util.formatNumber(s.recordCountBeforeFiltering)+' (filtered '+percentFiltered+'% of total records)</td>';
              html += '</tr>';
            }

            // filters
            if (_.has(s, 'notes')){
              html += '<tr>';
                html += '<td>Notes</td>';
                html += '<td>';
                _.each(s.notes, function(note){
                  html += '<p>'+note+'</p>';
                });
                html += '</td>';
              html += '</tr>';
            }

          html += '</table>'
        html += '</div>';
      html += '</div>';
    });

    $container.html(html);
  };

  Dashboard.prototype.loadSummaryData = function(){
    var _this = this;
    return $.getJSON(this.opt.summaryDataUrl, function(data){
      _this.summaryData = data;
    });
  };

  Dashboard.prototype.loadSummary = function(){
    var $table = $('.dashboard-table');
    var html = $table.html();

    var template = _.template(html);
    var newHtml = template(this.summaryData.summary);
    $table.html(newHtml);
    $table.removeClass('loading');
  };

  Dashboard.prototype.loadTimeline = function(){
    this.timeline = new Timeline({data: this.recordData});
  };

  Dashboard.prototype.onFacetDataLoaded = function(){
    this.loadDataTables();
    this.loadPieCharts();
    this.loadObjectTypes();
  };

  Dashboard.prototype.onRecordDataLoaded = function(){
    var _this = this;
    $('.explore-container').removeClass('loading');
    this.loadTimeline();
    setTimeout(function(){
      _this.loadMap();
    }, 10);
    this.loadFacets();
  };

  Dashboard.prototype.onSummaryDataLoaded = function(){
    $('body').removeClass('loading');
    this.loadSummary();
    this.loadSources();
    this.loadAvailabilities();
  };

  return Dashboard;

})();

$(function() {
  var app = new Dashboard({});
});
