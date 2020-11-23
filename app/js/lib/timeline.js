'use strict';

var Timeline = (function() {

  function Timeline(config) {
    var defaults = {
      el: '#data-timeline',
      legendPosition: 'bottom',
      fontSize: 12,
      fontFamily: 'sans-serif',
      fontColor: '#000',
      colors: ['#000000', '#003f5c', '#ffa600', '#2f4b7c', '#ff7c43', '#665191', '#f95d6a', '#a05195', '#d45087'],
      dataUrl: 'data/years.json',
      yearRange: [1800, 2050]
    };
    this.opt = _.extend({}, defaults, config);
    this.init();
  }

  Timeline.prototype.init = function(){
    var _this = this;
    $.getJSON(this.opt.dataUrl, function(data){
      _this.onDataLoaded(data);
    });
  };

  Timeline.prototype.onDataLoaded = function(rawData){
    var opt = this.opt;

    if (!_.has(opt, 'el')) {
      console.log('You must pass in an element ID to timeline.');
      return;
    }

    var $el = $(opt.el);
    if (!$el.length) {
      console.log('Could not find timeline element: ' + opt.el);
      return;
    }

    var aspectRatio = $el.width() / $el.height();
    var colors = opt.colors;
    var data = Util.parseData(rawData);
    data = this.parseYears(data);

    var labels = _.pluck(data, 'label');
    var values = _.pluck(data, 'value');

    var chartConfig = {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Number of objects constructed or dedicated this year',
          backgroundColor: colors[0],
          data: values
        }]
      },
      options: {
        responsive: true,
        aspectRatio: aspectRatio,
        legend: {
          display: false,
          position: opt.legendPosition,
          labels: {
            fontSize: opt.fontSize,
            fontFamily: opt.fontFamily,
            fontColor: opt.fontColor
          }
        },
        layout: {
          padding: {
            left: 0,
            right: 0,
            top: 20,
            bottom: 0
          }
        },
        scales: {
          xAxes: [{
            type: 'time',
            display: true,
            time: {
              unit: 'year',
              parser: 'YYYY'
            },
            scaleLabel: {
              fontFamily: opt.fontFamily,
              fontColor: opt.fontColor
            }
          }]
        },
      }
    };

    var ctx = $el[0].getContext('2d');
    var chart = new Chart(ctx, chartConfig);
  };

  Timeline.prototype.parseYears = function(data){
    var dataByYear = _.groupBy(data, function(row){ return row.year; });
    var years = _.keys(dataByYear);
    var minYear = _.min(years);
    var maxYear = _.max(years);

    var yearData = [];
    var yearRange = this.opt.yearRange;
    if (minYear < yearRange[0]) minYear = yearRange[0];
    if (maxYear > yearRange[1]) maxYear = yearRange[1];
    for (var year=minYear; year <= maxYear; year++) {
      if (_.has(dataByYear, year)) {
        var dataYear = dataByYear[year];
        var sum = _.reduce(dataYear, function(memo, d){ return memo + d.count; }, 0);
        yearData.push({
          label: year + ': ' + sum,
          value: {x: new Date(year, 0), y: sum}
        });
      } else {
        yearData.push({
          label: year + ': 0',
          value: {x: new Date(year, 0), y: 0}
        });
      }
    }
    return yearData;
  };

  return Timeline;

})();
