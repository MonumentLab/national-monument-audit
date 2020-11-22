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

    Chart.defaults.global.defaultFontColor = 'black';

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

  Dashboard.prototype.loadTimeline = function(){
    var timeline = new Timeline();
  };

  Dashboard.prototype.onDataLoaded = function(data){
    console.log("Loaded data");
    this.data = data;
    this.loadPieCharts();
  };

  return Dashboard;

})();

$(function() {
  var app = new Dashboard({});
});
