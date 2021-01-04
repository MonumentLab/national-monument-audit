'use strict';

var Dashboard = (function() {

  function Dashboard(config) {
    var defaults = {
      'summaryDataUrl': 'data/dashboard.json',
      'recordsUrl': 'data/records.json'
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

    $.when(this.loadRecords()).done(function(){
      console.log('Loaded record data.');
      _this.onRecordDataLoaded();
    });

  };

  Dashboard.prototype.loadDataTables = function(){
    var $parent = $('#data-frequencies');

    _.each(this.summaryData.frequencies, function(entry){
      var table = new DataTable(_.extend(entry, {'$parent': $parent}));
    });
  };

  Dashboard.prototype.loadMap = function(){
    var map = new Map({data: this.recordData, yearRange: this.timeline.range});
  };

  Dashboard.prototype.loadFacets = function(){
    var facets = new Facets({data: this.recordData, yearRange: this.timeline.range});
  };

  Dashboard.prototype.loadPieCharts = function(){
    _.each(this.summaryData.pieCharts, function(params, key){
      var chart = new PieChart(_.extend(params, {el: '#'+key}));
    });
  };

  Dashboard.prototype.loadRecords = function(){
    var _this = this;
    return $.getJSON(this.opt.recordsUrl, function(data){
      _this.recordData = Util.parseData(data);
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

  Dashboard.prototype.onRecordDataLoaded = function(){
    $('.explore-container').removeClass('loading');
    this.loadTimeline();
    this.loadMap();
    this.loadFacets();
  };

  Dashboard.prototype.onSummaryDataLoaded = function(){
    $('body').removeClass('loading');
    this.loadSummary();
    this.loadSources();
    this.loadPieCharts();
    this.loadDataTables();
  };

  return Dashboard;

})();

$(function() {
  var app = new Dashboard({});
});
