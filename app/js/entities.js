'use strict';

var WordCloud = (function() {

  function WordCloud(config) {
    var defaults = {
      'id': 'PERSON',
      'dataUrl': 'data/entities.json',
      'linkPattern': 'https://monumentlab.github.io/national-monument-audit/app/search.html?q={}',
      'maxEm': 4,
      'minEm': 1,
      'minImageH': 16,
      'maxImageH': 300,
      'showTopImages': 200
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
      $.when(this.loadData()).done(function(data){
        console.log('Loaded data');
        _this.onDataLoaded(data);
      });
    }
  };

  WordCloud.prototype.load = function(id){
    var _this = this;
    var entity = this.entities[id];

    var html = '';
    var mean = entity.mean;

    var linkPattern = this.opt.linkPattern;
    var showTopImages = this.opt.showTopImages;
    _.each(entity.rows, function(row, i){
      var text = row['Name'];
      var count = row['Count'];
      var em = row.em;
      var url = linkPattern.replaceAll('{}', text);
      if (_.has(row, 'Image Filename') && row['Image Filename'].length > 0 && i < showTopImages) {
        var imgH = row.imageH;
        html += '<a href="'+url+'" target="_blank" style="font-size: '+em+'em">';
          html += '<img src="https://commons.wikimedia.org/w/thumb.php?width='+imgH+'&f='+row['Image Filename']+'" /> '
          html += '<small class="label">'+(i+1)+'. '+text+' ('+Util.formatNumber(count)+')</small>';
        html += '</a>';
      } else {
        html += '<a href="'+url+'" target="_blank" style="font-size: '+em+'em">'+(i+1)+'. '+text+' ('+Util.formatNumber(count)+')</a>';
      }

    });

    this.$cloud.html(html);

    this.updateURL(id);
  };

  WordCloud.prototype.loadData = function(){
    var _this = this;
    return $.getJSON(this.opt.dataUrl, function(data){
      _this.data = data;
    });
  };

  WordCloud.prototype.loadListeners = function(id){
    var _this = this;

    this.$select.on('change', function(e){
      _this.load($(this).val());
    });
  };

  WordCloud.prototype.onDataLoaded = function(data){
    // console.log(this.data)

    var pow = 0.5;
    var minEm = this.opt.minEm;
    var maxEm = this.opt.maxEm;
    var minImageH = this.opt.minImageH;
    var maxImageH = this.opt.maxImageH;

    this.entities = _.mapObject(data.entities, function(entity, key) {
      var parsedRows = Util.parseData(entity);
      entity.rows = _.map(parsedRows, function(row){
        var ncount = MathUtil.norm(Math.pow(row['Count'], pow), Math.pow(entity.min, pow), Math.pow(entity.max, pow));
        row.em = MathUtil.lerp(minEm, maxEm, ncount);
        row.imageH = parseInt(MathUtil.lerp(minImageH, maxImageH, ncount));
        return row;
      });
      return entity;
    });

    this.loadListeners();
    this.$select.trigger('change');
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
