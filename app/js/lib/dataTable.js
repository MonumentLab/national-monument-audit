'use strict';

var DataTable = (function() {

  function DataTable(config) {
    var defaults = {
      'rows': [],
      'cols': false,
      '$parent': false,
      'resourceLink': false,
      'title': false,
      'resourceBaseUrl': '../data/compiled/'
    };
    this.opt = _.extend({}, defaults, config);
    this.init();
  }

  DataTable.prototype.init = function(){
    var opt = this.opt;

    var html = '';
    html = '<div class="data-table-container">';
      if (opt.title) html += '<h3>' + opt.title + '</h3>';
      html += '<table class="data-table">';
        if (opt.cols) {
          html += '<tr>';
          _.each(opt.cols, function(col){
            html += '<th>' + col + '</th>';
          });
          html += '</tr>';
        }
        _.each(opt.rows, function(cols){
          html += '<tr>';
          _.each(cols, function(col){
            html += '<td>' + col + '</td>';
          });
          html += '</tr>';
        });
      html += '</table>';
      if (opt.resourceLink) {
        html += '<p><a href="'+opt.resourceBaseUrl+opt.resourceLink+'" class="button" target="_blank">Download the full dataset</a></p>';
      }
    html += '</div>';
    opt.$parent.append($(html));
  };

  return DataTable;

})();
