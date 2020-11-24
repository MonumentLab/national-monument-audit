'use strict';

var Dashboard = (function() {

  function Dashboard(config) {
    var defaults = {
      "dataUrl": "data/dashboard.json"
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

    $.getJSON(this.opt.dataUrl, function(data){
      _this.onDataLoaded(data);
    });
    this.loadMap();
    this.loadTimeline();
  };

  Dashboard.prototype.loadMap = function(){
    var map = new Map();
  };

  Dashboard.prototype.loadPieCharts = function(data){
    var data = this.data;
    _.each(data.pieCharts, function(params, key){
      var chart = new PieChart(_.extend(params, {el: "#"+key}));
    });
  };

  Dashboard.prototype.loadSummary = function(){
    var $table = $('.dashboard-table');
    var html = $table.html();

    var template = _.template(html);
    var newHtml = template(this.data.summary);
    $table.html(newHtml);
    $table.removeClass('loading');
  };

  Dashboard.prototype.loadTimeline = function(){
    var timeline = new Timeline();
  };

  Dashboard.prototype.onDataLoaded = function(data){
    console.log("Loaded data");
    this.data = data;
    this.loadSummary();
    this.loadPieCharts();
  };

  return Dashboard;

})();

$(function() {
  var app = new Dashboard({});
});
