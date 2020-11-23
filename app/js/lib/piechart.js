'use strict';

var PieChart = (function() {

  function PieChart(config) {
    var defaults = {
      type: 'doughnut',
      circumference: Math.PI,
      rotation: -Math.PI,
      legendPosition: 'bottom',
      titleFontSize: 18,
      fontSize: 12,
      fontFamily: 'sans-serif',
      fontColor: '#000',
      colors: ['#003f5c', '#ffa600', '#665191', '#ff7c43', '#2f4b7c', '#f95d6a', '#a05195', '#d45087']
    };
    this.opt = _.extend({}, defaults, config);
    this.init();
  }

  PieChart.prototype.init = function(){
    var opt = this.opt;

    if (!_.has(opt, 'el')) {
      console.log("You must pass in an element ID to pie chart.");
      return;
    }

    var $el = $(opt.el);
    if (!$el.length) {
      console.log("Could not find pie chart element: " + opt.el);
      return;
    }

    var aspectRatio = $el.width() / $el.height();
    var colors = opt.colors;
    if (opt.values.length > colors.length) {
      console.log("Not enough colors for pie chart " + opt.el);
      return;
    }
    if (colors.length > opt.values.length) {
      colors = colors.slice(0, opt.values.length);
    }

    var chartConfig = {
      type: opt.type,
      data: {
        datasets: [{
          data: opt.values,
          backgroundColor: colors
        }],
        labels: opt.labels
      },
      options: {
        responsive: true,
        aspectRatio: aspectRatio,
        legend: {
          position: opt.legendPosition,
          labels: {
            fontSize: opt.fontSize,
            fontFamily: opt.fontFamily,
            fontColor: opt.fontColor
          }
        },
        title: {
          display: true,
          text: opt.title,
          fontSize: opt.titleFontSize,
          fontFamily: opt.fontFamily,
          fontColor: opt.fontColor
        },
        circumference: opt.circumference,
        rotation: opt.rotation
      }
    };

    var ctx = $el[0].getContext('2d');
    var chart = new Chart(ctx, chartConfig);
  };

  return PieChart;

})();
