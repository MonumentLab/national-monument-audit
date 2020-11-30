'use strict';

var CSV = (function() {

  function CSV(config) {
    var defaults = {
      'el': '#table',
      'f': '../data/compiled/monumentlab_national_monuments_audit_final_category_counts.csv'
    };
    var q = Util.queryParams();
    this.opt = $.extend({}, defaults, config, q);
    this.init();
  }

  CSV.prototype.init = function(){
    var _this = this;

    Papa.parse(this.opt.f, {
      download: true,
      header: true,
      dynamicTyping: true,
      skipEmptyLines: true,
      complete: function(results) {
        _this.onDataLoaded(results);
      }
    });
  };

  CSV.prototype.onDataLoaded = function(results){
    var $el = $(this.opt.el);

    var data = results.data;
    var columns = _.map(results.meta.fields, function(field){
      var dataType = 'string';
      if (field === 'count') dataType = 'int';
      return {name: field, type: dataType};
    });

    var grid = $el.grid(data, columns, {
      sortable: true
    });
    grid.registerEditor(BasicEditor);

    grid.events.on('column:sort', function (col, order, $el) {
      console.info('column sort:', col, order, $el);
      var sorted = _.sortBy(data, col);
      if (order === 'desc') {
          sorted = sorted.reverse();
      }
      grid.updateData(sorted);
  });

    grid.render();
  };

  return CSV;

})();

$(function() {
  var app = new CSV({});
});
