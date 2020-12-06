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
    var _this = this;
    var isValid = false;
    msg = msg || 'Please enter password:';

    var authenticated = Util.cookieGet('authenticated');

    if (!authenticated) {
      var answer = prompt(msg);
      if (answer != null) {
        var hash = CryptoJS.MD5(answer).toString();
        if (hash === '293577d3615f67c577ed0f19075555b5') isValid = true;
      }
    } else {
      isValid = true;
    }

    if (isValid) {
      Util.cookieSet('authenticated', 1, 30); // keep for 30 days
      this.load();
    } else {
      this.init('Incorrect password. Please try again:')
    }

  };

  Dashboard.prototype.load = function(){
    var _this = this;
    // set globals
    Chart.defaults.global.defaultFontColor = 'black';
    _.templateSettings = {
      interpolate: /\{\{(.+?)\}\}/g
    };

    $('body').removeClass('hidden');
    $.when(
      this.loadSummaryData(),
      this.loadRecords()

    ).done(function(){
      console.log('Loaded data.');
      $('body').removeClass('loading');
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

  Dashboard.prototype.onDataLoaded = function(){
    console.log('Loaded data');
    this.loadSummary();
    this.loadPieCharts();
    this.loadDataTables();
    this.loadTimeline();
    this.loadMap();
    this.loadFacets();
  };

  return Dashboard;

})();

$(function() {
  var app = new Dashboard({});
});
