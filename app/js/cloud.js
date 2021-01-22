'use strict';

var WordCloud = (function() {

  function WordCloud(config) {
    var defaults = {
      'id': 'entities_people',
      'linkPattern': 'https://monumentlab.github.io/national-monument-audit/app/search.html?q={}',
      'maxEm': 4,
      'minEm': 0.8
    };
    var q = Util.queryParams();
    this.opt = _.extend({}, defaults, config, q);
    this.init();
  }

  WordCloud.prototype.init = function(msg){
    var _this = this;
    this.$cloud = $('#wordcloud');
    this.$select = $('#categories-select');
    var isValid = Auth.authenticate();
    if (isValid) {
      $('#categories-select option[value="'+this.opt.id+'"]').prop('selected', true);
      this.loadListeners();
      this.$select.trigger('change');
    }
  };

  WordCloud.prototype.load = function(id){
    var _this = this;

    $.when(this.loadData(id)).done(function(data){
      console.log('Loaded data for '+id);
      _this.onDataLoaded(id);
    });
  };

  WordCloud.prototype.loadData = function(id){
    var _this = this;
    return $.getJSON('data/'+id+'.json', function(data){
      _this.data = data;
    });
  };

  WordCloud.prototype.loadListeners = function(id){
    var _this = this;

    this.$select.on('change', function(e){
      _this.load($(this).val());
    });
  };

  WordCloud.prototype.onDataLoaded = function(id){
    // console.log(this.data)

    var html = '';
    var mean = this.data.mean;
    var minEm = this.opt.minEm;
    var maxEm = this.opt.maxEm;
    var linkPattern = this.opt.linkPattern;
    _.each(this.data.frequencies, function(row, i){
      var text = row[0];
      var count = row[1];
      var em = MathUtil.clamp(count / mean, minEm, maxEm);
      var url = linkPattern.replaceAll('{}', text);
      html += '<a href="'+url+'" target="_blank" style="font-size: '+em+'em">'+(i+1)+'. '+text+' ('+Util.formatNumber(count)+')</a>';
    });

    this.$cloud.html(html);

    this.updateURL(id);
  };

  WordCloud.prototype.updateURL = function(id){
    var params = {
      'id': id
    };

    if (window.history.pushState) {
      var queryString = $.param(params);
      var baseUrl = window.location.href.split('?')[0];
      var currentState = window.history.state;
      var newUrl = baseUrl + '?' + queryString;

      // ignore if state is the same
      if (currentState) {
        var currentUrl = baseUrl + '?' + $.param(currentState);
        if (newUrl === currentUrl) return;
      }

      window.historyInitiated = true;
      // console.log('Updating url', newUrl);
      window.history.replaceState(params, '', newUrl);
      // window.history.pushState(data, '', newUrl);
    }

  };

  return WordCloud;

})();

$(function() {
  var app = new WordCloud({});
});
