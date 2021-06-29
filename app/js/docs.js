'use strict';

var Docs = (function() {

  function Docs(config) {
    var defaults = {
      dataUrl: 'data/docs.json',
    };
    var q = Util.queryParams();
    this.opt = $.extend({}, defaults, config, q);
    this.init();
  }

  Docs.prototype.init = function(){
    var _this = this;

    _.templateSettings = {
      interpolate: /\{\{(.+?)\}\}/g
    };

    this.loadToc();
    $.when(this.loadData()).done(function(){
      console.log('Loaded data.');
      _this.onDataLoaded();
    });
  };

  Docs.prototype.loadBars = function($container, title, barData){
    if (!$container.length) {
      console.log('Warning: No container found for '+title);
      return;
    }
    var html = '';
    if (title && title.length) {
      html += '<h5>' + title + '</h5>';
    }
    _.each(barData, function(bar){
      var value = bar.percent + '%';
      if (_.has(bar, 'count')) value = Util.formatNumber(bar.count) + ' ('+value+')';
      var label = bar.value;
      if (bar.url) label = '<a href="'+bar.url+'">'+label+'</a>';
      html += '<div class="bar-container">';
        html += '<div class="bar" style="width: '+bar.percent+'%"></div>';
        html += '<div class="label"><div>'+label+'</div> <div>'+value+'</div></div>';
      html += '</div>';
    });
    $container.html(html);
  };

  Docs.prototype.loadCharts = function(){
    var _this = this;
    _.each(this.data.charts, function(chart, key){
      _this.loadBars($('#'+key), chart.title, chart.data);
    });
  };

  Docs.prototype.loadData = function(){
    var _this = this;
    return $.getJSON(this.opt.dataUrl, function(data){
      _this.data = data;
    });
  };

  Docs.prototype.loadSources = function(){
    var sources = this.data.sources;
    var $container = $('#data-sources-list');
    var codeBaseUrl = 'https://github.com/MonumentLab/national-monument-audit/tree/main/';

    sources = _.filter(sources, function(s){ return s.percentOfTotal > 0; });

    var html = '';
    _.each(sources, function(s){
      html += '<div class="data-source">';
        var name = s.verboseName ? s.verboseName : s.name;
        var searchQ = {
          q: '',
          facets: 'source~'+s.name
        };
        var searchUrl = 'map.html?' + $.param(searchQ);
        html += '<div class="source-title">'+name+'</div>';

        html += '<div class="record-count-container">';
          if (s.percentOfTotal > 0) html += '<div class="record-count-bar" style="width: '+s.percentOfTotal+'%"></div>';
          html += '<div class="record-count-text">'+Util.formatNumber(s.recordCount)+' records ('+s.percentOfTotal+'% of total)</div>';
        html += '</div>';

        html += '<button type="button" class="toggle-parent" data-active="Hide details" data-inactive="Show details">Show details</button>';

        html += '<div class="data-source-details">';
          html += '<table class="data-table data-source-table">';

            html += '<tr>';
              html += '<td>&nbsp;</td>';
              html += '<td><a href="'+s.url+'" target="_blank" class="button small">source link</a> <a href="'+searchUrl+'" class="button small">browse data</a></td>';
            html += '</tr>';

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

  Docs.prototype.loadStats = function(){
    var stats = this.data.stats;
    var $el = $('#stats-summary');
    var html = $el.html();

    var template = _.template(html);
    var newHtml = template(stats);
    $el.html(newHtml);
  };

  Docs.prototype.loadToc = function(){
    tocbot.init({
      // Where to render the table of contents.
      tocSelector: '#toc',
      // Where to grab the headings to build the table of contents.
      contentSelector: '#content',
      // Which headings to grab inside of the contentSelector element.
      headingSelector: 'h1, h2, h3, h4',
      // For headings inside relative or absolute positioned containers within content.
      hasInnerContainers: true,
    });
  };

  Docs.prototype.onDataLoaded = function(){
    this.loadSources();
    this.loadCharts();
    this.loadStats();
  };

  return Docs;

})();

$(function() {
  var app = new Docs({});
});
