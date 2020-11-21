'use strict';

var Dashboard = (function() {

  function Dashboard(config) {
    var defaults = {
      "dataFile": "data/dashboard.json"
    };
    var q = Util.queryParams();
    this.opt = _.extend({}, defaults, config, q);
    this.init();
  }

  Dashboard.prototype.init = function(){
    var _this = this;
    $.getJSON(this.opt.dataFile, function(data){
      _this.onDataLoad(data);
    });
  };

  Dashboard.prototype.loadPieCharts = function(data){
    var data = this.data;
    _.each(data.pieCharts, function(params, key){
      var chart = new PieChart(_.extend(params, {el: "#"+key}));
    });
  };

  Dashboard.prototype.onDataLoad = function(data){
    console.log("Loaded data", data);
    this.data = data;
    this.loadPieCharts();
  };

  return Dashboard;

})();

$(function() {
  var app = new Dashboard({});
});
