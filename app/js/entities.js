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
      'showTopImages': 200,
      'Gender': -1,
      'Occupation': -1,
      'Ethnic_Group': -1,
      'Wikidata_Type': -1
    };
    var q = Util.queryParams();
    console.log(q)
    this.opt = _.extend({}, defaults, config, q);
    this.init();
  }

  WordCloud.prototype.init = function(msg){
    var _this = this;
    this.$cloud = $('#wordcloud');
    this.$select = $('#categories-select');
    this.$nav = $('#nav');
    this.loadedEntityId = false;

    this.facets = {
      'Gender': parseInt(this.opt.Gender),
      'Occupation': parseInt(this.opt.Occupation),
      'Ethnic Group': parseInt(this.opt['Ethnic_Group']),
      'Wikidata Type': parseInt(this.opt['Wikidata_Type'])
    };

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
    id = id || this.loadedEntityId;
    var entity = this.entities[id];

    this.loadedEntityId = id;
    var html = '';
    var facets = this.facets;
    var linkPattern = this.opt.linkPattern;
    var showTopImages = this.opt.showTopImages;
    var validKeys = _.keys(entity.groups);
    var entityFacets = _.pick(facets, function(value, key){ return (_.indexOf(validKeys, key) >= 0); })
    _.each(entity.rows, function(row, i){
      var text = row['Name'];
      var count = row['Count'];
      var em = row.em;
      var url = linkPattern.replaceAll('{}', text);
      var wikiurl = 'https://en.wikipedia.org/wiki/' + row['Name'].replaceAll(' ', '_');
      var isActive = true;

      _.each(entityFacets, function(index, key){
        if (index >= 0 && row[key+'Index'] !== index) isActive = false;
      });

      var active = isActive ? ' active' : '';
      if (_.has(row, 'Image Filename') && row['Image Filename'].length > 0 && i < showTopImages) {
        var imgH = row.imageH;
        html += '<div style="font-size: '+em+'em" class="entity '+active+'">';
          html += '<a href="'+wikiurl+'" target="_blank"><img src="https://commons.wikimedia.org/w/thumb.php?width='+imgH+'&f='+row['Image Filename']+'" /></a>'
          html += '<a href="'+url+'" target="_blank"><small class="label">'+(i+1)+'. '+text+' ('+Util.formatNumber(count)+')</small></a>';
        html += '</div>';
      } else {
        html += '<a href="'+url+'" target="_blank" style="font-size: '+em+'em" class="entity '+active+'">'+(i+1)+'. '+text+' ('+Util.formatNumber(count)+')</a>';
      }

    });
    this.$cloud.html(html);
    $('.group-select').removeClass('active');
    $('.group-select.group-'+id).addClass('active');

    this.updateURL();
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

    $('.facet-select').on('change', function(e){
      _this.onFacetChange($(this));
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

    var $nav = this.$nav;
    var facets = this.facets;
    _.each(this.entities, function(entity, key){
      var groupCounts = entity.groupCounts;
      _.each(entity.groups, function(groupValues, groupName){
        var selectedIndex = facets[groupName];
        var html = '<div class="group-select group-'+key+'">';
          html += '<label for="group-select-'+groupName+'">'+groupName+':</label>';
          html += '<select id="group-select-'+groupName+'" class="facet-select" data-property="'+groupName+'">'
            html += '<option value="-1">Any</option>';
            _.each(groupValues, function(value, i){
              var selected = selectedIndex === i ? 'selected' : '';
              if (value.length < 1) value = '&lt;Empty&gt;';
              var count = groupCounts[groupName][i];
              html += '<option value="'+i+'" '+selected+'>'+value+' ('+Util.formatNumber(count)+')</option>';
            });
          html += '</select>';
        html += '</div>';
        $nav.append($(html));
      });
    });

    this.loadListeners();
    this.$select.trigger('change');
  };

  WordCloud.prototype.onFacetChange = function($select){
    this.facets[$select.attr('data-property')] = parseInt($select.val());
    this.load();
  };

  WordCloud.prototype.updateURL = function(){
    var id = this.loadedEntityId;

    var params = {
      'id': id
    };
    _.each(this.facets, function(value, key){
      key = key.replaceAll(' ', '_');
      params[key] = value;
    });

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
