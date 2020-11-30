'use strict';

var Facets = (function() {

  function Facets(config) {
    var defaults = {
      el: '#facets',
      messageEl: '#facet-message',
      data: [], // pass this in
      keys: ['source']
    };
    this.opt = _.extend({}, defaults, config);
    this.init();
  }

  Facets.prototype.init = function(){
    this.loadUI();

    this.loadListeners();
  };

  Facets.prototype.loadListeners = function(){
    var _this = this;

    $('.facet-select').on('change', function(e){
      _this.onFacetSelect($(this));
    });
  };

  Facets.prototype.loadUI = function(){
    var _this = this;
    var data = this.opt.data;
    var $el = $(this.opt.el);
    var facets = {};

    _.each(this.opt.keys, function(key){
      var html = '';
      var values = _.pluck(data, key);
      values = _.uniq(values);
      values.sort();
      var id = key + '-facet-select';
      html += '<div class="facet">';
        html += '<label for="'+id+'">'+key+'</label>';
        html += '<select name="'+key+'" id="'+id+'" class="facet-select">';
          html += '<option value="" selected>Any</option>';
        _.each(values, function(value){
          html += '<option value="'+value+'">'+value+'</option>';
        });
        html += '</select>';
      html += '</div>';
      $el.append($(html));
      facets[key] = '';
    });

    this.facets = facets;
  };

  Facets.prototype.onFacetSelect = function($select){
    var property = $select.attr('name');
    var value = $select.val();
    console.log('Facet change', property, value);

    this.facets[property] = value;
    $(document).trigger('change-facets', [ this.facets ]);
  };

  return Facets;

})();
