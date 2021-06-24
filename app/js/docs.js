'use strict';

var Docs = (function() {

  function Docs(config) {
    var defaults = {

    };
    var q = Util.queryParams();
    this.opt = $.extend({}, defaults, config, q);
    this.init();
  }

  Docs.prototype.init = function(){
    var _this = this;

    tocbot.init({
      // Where to render the table of contents.
      tocSelector: '#toc',
      // Where to grab the headings to build the table of contents.
      contentSelector: '#content',
      // Which headings to grab inside of the contentSelector element.
      headingSelector: 'h1, h2, h3, h4',
      // For headings inside relative or absolute positioned containers within content.
      hasInnerContainers: true,
    });
  };

  return Docs;

})();

$(function() {
  var app = new Docs({});
});
