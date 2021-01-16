'use strict';

var Timeline = (function() {

  function Timeline(config) {
    var defaults = {
      el: '#data-timeline',
      data: [], // pass this in
      timeRangeEl: '#time-range-selector',
      timeDisplayMinEl: '#active-year-min',
      timeDisplayMaxEl: '#active-year-max',
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
    this.range = false;
    this.noTrigger = false;
    if (this.opt.data.length < 1) {
      this.range = this.opt.yearRange;
    }
    this.data = _.filter(this.opt.data, function(d){
      return !isNaN(d.year) && d.year > 0;
    });
    var diff = this.opt.data.length - this.data.length;
    console.log(diff + ' records with no year set');

    this.loadChart();
    this.loadListeners();
  };

  Timeline.prototype.loadChart = function(){
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
    var data = this.data;
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
            right: 20,
            top: 30,
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
    this.chart = chart;

    this.$minYear = $(this.opt.timeDisplayMinEl);
    this.$maxYear = $(this.opt.timeDisplayMaxEl);
    this.$minYear.text(this.range[0]);
    this.$maxYear.text(this.range[1]);
  };

  Timeline.prototype.loadListeners = function(){
    var _this = this;
    var range = this.range;

    this.$slider = $(this.opt.timeRangeEl);
    this.$slider.slider({
      range: true,
      min: range[0],
      max: range[1],
      values: range,
      create: function(event, ui) {
        $(this).children('.ui-slider-handle').each(function(index){
          $(this).html('<span class="label">'+range[index]+'</span>');
        });
      },
      slide: function(e, ui){
        $(this).children('.ui-slider-handle').each(function(index){
          $(this).html('<span class="label">'+ui.values[index]+'</span>');
        });
      },
      change: function(e, ui) {
        _this.onChangeRange(ui.values[0], ui.values[1]);
      }
    });

    $(document).on('change-facets', function(e, newFacets) {
      _this.onChangeFacets(newFacets);
    });
  };

  Timeline.prototype.onChangeFacets = function(newFacets){
    var filteredData = _.filter(this.data, function(d){
      if (isNaN(d.year) || d.year < 0) return false;
      return Util.isValidFacetValue(d, newFacets);
    });
    filteredData = this.parseYears(filteredData);

    var labels = _.pluck(filteredData, 'label');
    var values = _.pluck(filteredData, 'value');

    this.chart.data.labels = labels;
    this.chart.data.datasets[0].data = values;
    this.chart.update();

    // var range = this.range;
    // this.$slider.slider('option', {
    //   'min': range[0],
    //   'max': range[1],
    //   'values': range
    // });
    // this.$slider.children('.ui-slider-handle').each(function(index){
    //   $(this).html('<span class="label">'+range[index]+'</span>');
    // });
  };

  Timeline.prototype.onChangeRange = function(minYear, maxYear){
    console.log('UI range change heard', minYear, maxYear);
    var trigger = true;
    if (this.noTrigger !== false) {
      var now = new Date().getTime();
      var delta = now - this.noTrigger;
      if (delta < 1000) trigger = false;
    }
    if (trigger) $(document).trigger('change-year-range', [ [minYear, maxYear] ]);
    this.$minYear.text(minYear);
    this.$maxYear.text(maxYear);
  };

  Timeline.prototype.parseYears = function(data, hasCount){
    var dataByYear = _.groupBy(data, function(row){ return parseInt(row.year); });
    var years = _.keys(dataByYear);
    years = _.map(years, function(year){ return parseInt(year); })
    var minYear = _.min(years);
    var maxYear = _.max(years);

    var yearData = [];
    var yearRange = this.opt.yearRange;
    if (minYear < yearRange[0]) minYear = yearRange[0];
    if (maxYear > yearRange[1]) maxYear = yearRange[1];

    if (this.range === false) {
      this.range = [minYear, maxYear];
      console.log('Year range: '+this.range);
    } else {
      minYear = this.range[0];
      maxYear = this.range[1];
    }

    for (var year=minYear; year <= maxYear; year++) {
      if (_.has(dataByYear, year)) {
        var dataYear = dataByYear[year];
        var sum = dataYear.length;
        if (hasCount) {
          sum = _.reduce(dataYear, function(memo, d){ return memo + d.count; }, 0);
        }
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

  Timeline.prototype.renderResults = function(results){
    var data = _.map(results, function(d){
      d.year = d.value;
      return d;
    });
    data = this.parseYears(data, true);

    var labels = _.pluck(data, 'label');
    var values = _.pluck(data, 'value');

    this.chart.data.labels = labels;
    this.chart.data.datasets[0].data = values;
    this.chart.update();
  };

  Timeline.prototype.reset = function(){
    this.setRange(this.range);
  };

  Timeline.prototype.setRange = function(range){
    if (range && range.length === 2) {
      range = _.map(range, function(year){ return parseInt(year); });
    }
    this.noTrigger = new Date().getTime();
    console.log('Setting new range: ', range);
    this.$slider.slider( "values", range );

    this.$slider.children('.ui-slider-handle').each(function(index){
      $(this).html('<span class="label">'+range[index]+'</span>');
    });

  };

  return Timeline;

})();
