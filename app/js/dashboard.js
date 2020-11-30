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

  Dashboard.prototype.init = function(){
    var _this = this;

    // set globals
    Chart.defaults.global.defaultFontColor = 'black';
    _.templateSettings = {
      interpolate: /\{\{(.+?)\}\}/g
    };

    $.when(
      this.loadSummaryData(),
      this.loadRecords()

    ).done(function(){
      console.log('Loaded data.');
      _this.onDataLoaded();
    });

  };

  Dashboard.prototype.loadDataTables = function(){
    var $parent = $('#data-frequencies');

    _.each(this.summaryData.frequencies, function(entry){
      var table = new DataTable(_.extend(entry, {'$parent': $parent}));
    });
  };

  Dashboard.prototype.loadMap = function(){
    var map = new Map({data: this.recordData});
  };

  Dashboard.prototype.loadFacets = function(){
    var facets = new Facets({data: this.recordData});
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
    var timeline = new Timeline({data: this.recordData});
  };

  Dashboard.prototype.onDataLoaded = function(){
    console.log('Loaded data');
    this.loadSummary();
    this.loadFacets();
    this.loadPieCharts();
    this.loadDataTables();
    this.loadMap();
    this.loadTimeline();
  };

  return Dashboard;

})();

$(function() {
  var app = new Dashboard({});
});
