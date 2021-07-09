// Utility functions

var COLOR_GRADIENT = ['rgb(9,7,32)', 'rgb(10,8,34)', 'rgb(11,9,36)', 'rgb(12,9,38)', 'rgb(13,10,41)', 'rgb(14,11,43)', 'rgb(16,11,45)', 'rgb(17,12,47)', 'rgb(18,13,49)', 'rgb(19,13,52)', 'rgb(20,14,54)', 'rgb(21,14,56)', 'rgb(22,15,59)', 'rgb(24,15,61)', 'rgb(25,16,63)', 'rgb(26,16,66)', 'rgb(28,16,68)', 'rgb(29,17,71)', 'rgb(30,17,73)', 'rgb(32,17,75)', 'rgb(33,17,78)', 'rgb(34,17,80)', 'rgb(36,18,83)', 'rgb(37,18,85)', 'rgb(39,18,88)', 'rgb(41,17,90)', 'rgb(42,17,92)', 'rgb(44,17,95)', 'rgb(45,17,97)', 'rgb(47,17,99)', 'rgb(49,17,101)', 'rgb(51,16,103)', 'rgb(52,16,105)', 'rgb(54,16,107)', 'rgb(56,16,108)', 'rgb(57,15,110)', 'rgb(59,15,112)', 'rgb(61,15,113)', 'rgb(63,15,114)', 'rgb(64,15,116)', 'rgb(66,15,117)', 'rgb(68,15,118)', 'rgb(69,16,119)', 'rgb(71,16,120)', 'rgb(73,16,120)', 'rgb(74,16,121)', 'rgb(76,17,122)', 'rgb(78,17,123)', 'rgb(79,18,123)', 'rgb(81,18,124)', 'rgb(82,19,124)', 'rgb(84,19,125)', 'rgb(86,20,125)', 'rgb(87,21,126)', 'rgb(89,21,126)', 'rgb(90,22,126)', 'rgb(92,22,127)', 'rgb(93,23,127)', 'rgb(95,24,127)', 'rgb(96,24,128)', 'rgb(98,25,128)', 'rgb(100,26,128)', 'rgb(101,26,128)', 'rgb(103,27,128)', 'rgb(104,28,129)', 'rgb(106,28,129)', 'rgb(107,29,129)', 'rgb(109,29,129)', 'rgb(110,30,129)', 'rgb(112,31,129)', 'rgb(114,31,129)', 'rgb(115,32,129)', 'rgb(117,33,129)', 'rgb(118,33,129)', 'rgb(120,34,129)', 'rgb(121,34,130)', 'rgb(123,35,130)', 'rgb(124,35,130)', 'rgb(126,36,130)', 'rgb(128,37,130)', 'rgb(129,37,129)', 'rgb(131,38,129)', 'rgb(132,38,129)', 'rgb(134,39,129)', 'rgb(136,39,129)', 'rgb(137,40,129)', 'rgb(139,41,129)', 'rgb(140,41,129)', 'rgb(142,42,129)', 'rgb(144,42,129)', 'rgb(145,43,129)', 'rgb(147,43,128)', 'rgb(148,44,128)', 'rgb(150,44,128)', 'rgb(152,45,128)', 'rgb(153,45,128)', 'rgb(155,46,127)', 'rgb(156,46,127)', 'rgb(158,47,127)', 'rgb(160,47,127)', 'rgb(161,48,126)', 'rgb(163,48,126)', 'rgb(165,49,126)', 'rgb(166,49,125)', 'rgb(168,50,125)', 'rgb(170,51,125)', 'rgb(171,51,124)', 'rgb(173,52,124)', 'rgb(174,52,123)', 'rgb(176,53,123)', 'rgb(178,53,123)', 'rgb(179,54,122)', 'rgb(181,54,122)', 'rgb(183,55,121)', 'rgb(184,55,121)', 'rgb(186,56,120)', 'rgb(188,57,120)', 'rgb(189,57,119)', 'rgb(191,58,119)', 'rgb(192,58,118)', 'rgb(194,59,117)', 'rgb(196,60,117)', 'rgb(197,60,116)', 'rgb(199,61,115)', 'rgb(200,62,115)', 'rgb(202,62,114)', 'rgb(204,63,113)', 'rgb(205,64,113)', 'rgb(207,64,112)', 'rgb(208,65,111)', 'rgb(210,66,111)', 'rgb(211,67,110)', 'rgb(213,68,109)', 'rgb(214,69,108)', 'rgb(216,69,108)', 'rgb(217,70,107)', 'rgb(219,71,106)', 'rgb(220,72,105)', 'rgb(222,73,104)', 'rgb(223,74,104)', 'rgb(224,76,103)', 'rgb(226,77,102)', 'rgb(227,78,101)', 'rgb(228,79,100)', 'rgb(229,80,100)', 'rgb(231,82,99)', 'rgb(232,83,98)', 'rgb(233,84,98)', 'rgb(234,86,97)', 'rgb(235,87,96)', 'rgb(236,88,96)', 'rgb(237,90,95)', 'rgb(238,91,94)', 'rgb(239,93,94)', 'rgb(240,95,94)', 'rgb(241,96,93)', 'rgb(242,98,93)', 'rgb(242,100,92)', 'rgb(243,101,92)', 'rgb(244,103,92)', 'rgb(244,105,92)', 'rgb(245,107,92)', 'rgb(246,108,92)', 'rgb(246,110,92)', 'rgb(247,112,92)', 'rgb(247,114,92)', 'rgb(248,116,92)', 'rgb(248,118,92)', 'rgb(249,120,93)', 'rgb(249,121,93)', 'rgb(249,123,93)', 'rgb(249,125,94)', 'rgb(249,127,94)', 'rgb(249,129,95)', 'rgb(249,131,95)', 'rgb(249,133,96)', 'rgb(249,135,97)', 'rgb(249,137,97)', 'rgb(249,138,98)', 'rgb(249,140,99)', 'rgb(249,142,100)', 'rgb(249,144,101)', 'rgb(249,146,102)', 'rgb(249,148,103)', 'rgb(249,150,104)', 'rgb(249,152,105)', 'rgb(249,154,106)', 'rgb(249,155,107)', 'rgb(249,157,108)', 'rgb(249,159,109)', 'rgb(249,161,110)', 'rgb(249,163,111)', 'rgb(249,165,113)', 'rgb(249,167,114)', 'rgb(249,169,115)', 'rgb(249,170,116)', 'rgb(249,172,118)', 'rgb(249,174,119)', 'rgb(249,176,120)', 'rgb(249,178,122)', 'rgb(249,180,123)', 'rgb(249,182,124)', 'rgb(249,183,126)', 'rgb(249,185,127)', 'rgb(249,187,129)', 'rgb(249,189,130)', 'rgb(249,191,132)', 'rgb(249,193,133)', 'rgb(249,194,135)', 'rgb(249,196,136)', 'rgb(249,198,138)', 'rgb(249,200,140)', 'rgb(249,202,141)', 'rgb(249,204,143)', 'rgb(249,205,144)', 'rgb(249,207,146)', 'rgb(249,209,148)', 'rgb(249,211,149)', 'rgb(249,213,151)', 'rgb(249,215,153)', 'rgb(249,216,154)', 'rgb(249,218,156)', 'rgb(249,220,158)', 'rgb(249,222,160)', 'rgb(249,224,161)', 'rgb(249,226,163)', 'rgb(249,227,165)', 'rgb(249,229,167)'];
var COLOR_GRADIENT_LEN = COLOR_GRADIENT.length;

(function() {
  window.Util = {};

  Util.capitalize = function(string){
    return string.charAt(0).toUpperCase() + string.slice(1);
  };

  Util.cookieGet = function(name) {
    var nameEQ = name + "=";
    var ca = document.cookie.split(';');
    for(var i=0;i < ca.length;i++) {
      var c = ca[i];
      while (c.charAt(0)==' ') c = c.substring(1,c.length);
      if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
    }
    return null;
  };

  Util.cookieSet = function(name, value, days) {
    var expires = "";
    if (days) {
      var date = new Date();
      date.setTime(date.getTime() + (days*24*60*60*1000));
      expires = "; expires=" + date.toUTCString();
    }
    document.cookie = name + "=" + (value || "")  + expires + "; path=/";
  };

  Util.cookieRemove = function(name) {
    document.cookie = name +'=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;';
  };

  Util.escapeQuotes = function(value){
    value = ""+value;
    value = value.replaceAll('"', '&quot;');
    return value;
  };

  Util.formatNumber = function(number){
    if (number === undefined) return '';
    return number.toLocaleString();
  };

  Util.getColorGradient = function(steps, reverse){
    var gradient = {};
    _.times(steps, function(n){
      var t = n / steps;
      var index = Math.round(t * (COLOR_GRADIENT_LEN-1));
      if (reverse) index = COLOR_GRADIENT_LEN-1-index;
      gradient[t] = COLOR_GRADIENT[index];
    });
    if (reverse) gradient[1.0] = COLOR_GRADIENT[0];
    else gradient[1.0] = COLOR_GRADIENT[COLOR_GRADIENT_LEN-1];
    return gradient;
  };

  Util.getGradientColor = function(t){
    var index = Math.round(t * (COLOR_GRADIENT_LEN-1));
    return COLOR_GRADIENT[index];
  };

  Util.getRelativePoint = function($parent, pageX, pageY) {
    var x = pageX - $parent.offset().left;
    var nx = x / $parent.width();
    var y = pageY - $parent.offset().top;
    var ny = y / $parent.height();
    return {
      x: nx,
      y: ny
    }
  };

  Util.isValidFacetValue = function(d, facets){
    var isValid = true;
    _.each(facets, function(value, key){
      if (value.length && _.has(d, key)){
        // check for literal value
        if (!Array.isArray(d[key]) && d[key] !== value) {
          isValid = false;
        // check for list value
        } else if (Array.isArray(d[key]) && _.indexOf(d[key], value) < 0) {
          isValid = false;
        }
      }
    });
    return isValid;
  };

  Util.listToString = function(arr){
    var arrLen = arr.length;
    if (arrLen < 1) return "Unknown";
    if (arrLen < 2) return arr[0];
    if (arrLen < 3) return arr.join(' and ');

    var string = '';
    _.each(arr, function(value, i){
      if (i===arrLen-1) string += value;
      else if (i===arrLen-2) string += (value + ', and ');
      else string += (value + ', ');
    });
    return string;
  };

  Util.mapVars = function(obj, map, reverse){
    if (reverse===true) {
      map = _.invert(map);
    }
    _.each(obj, function(value, key){
      if (_.has(map, key)) {
        obj[map[key]] = value;
        obj = _.omit(obj, key);
      }
    });
    return obj;
  };

  Util.queryParams = function(){
    if (location.search.length) {
      var search = location.search.substring(1);
      var parsed = JSON.parse('{"' + search.replace(/&/g, '","').replace(/=/g,'":"') + '"}', function(key, value) { return key===""?value:decodeURIComponent(value) });
      _.each(parsed, function(value, key){
        var dkey = decodeURIComponent(key);
        parsed[dkey] = value;
      });
      return parsed;
    }
    return {};
  };

  Util.parseData = function(rawData){
    var cols = rawData.cols;
    var data = _.map(rawData.rows, function(row){
      var obj = _.object(cols, row);
      if (rawData.groups) {
        _.each(rawData.groups, function(groupList, key){
          var rawValue = obj[key];
          obj[key+'Index'] = rawValue;
          if (Array.isArray(rawValue)) {
            obj[key] = _.map(rawValue, function(v){
              return groupList[v];
            });
          } else {
            obj[key] = groupList[rawValue];
          }
        });
      }
      return obj;
    });
    return data;
  };

  Util.scrollTo = function(el, offset){
    offset = offset || 0;
    // $(el)[0].scrollIntoView();

    $([document.documentElement, document.body]).animate({
      scrollTop: $(el).offset().top + offset
    }, 1000);
  };

  Util.stringToId = function(string) {
    string = string.toLowerCase();
    string = string.replace(/[^a-z0-9]+/gi, '_');
    return string
  };


  Util.uniqueString = function(prefix){
    prefix = prefix || '';
    var dt = new Date().getTime();
    return ''+prefix+dt;
  };

})();


(function() {
  window.MathUtil = {};

  MathUtil.ceilToNearest = function(value, nearest) {
    return Math.ceil(value / nearest) * nearest;
  };

  MathUtil.clamp = function(value, min, max) {
    value = Math.min(value, max);
    value = Math.max(value, min);
    return value;
  };

  MathUtil.ease = function(n){
    return (Math.sin((n+1.5)*Math.PI)+1.0) / 2.0;
  };

  MathUtil.floorToNearest = function(value, nearest) {
    return Math.floor(value / nearest) * nearest;
  };

  MathUtil.lerp = function(a, b, percent) {
    return (1.0*b - a) * percent + a;
  };

  MathUtil.mod = function(n, m) {
    return ((n % m) + m) % m;
  }

  MathUtil.norm = function(value, a, b){
    var denom = (b - a);
    if (denom > 0 || denom < 0) {
      return (1.0 * value - a) / denom;
    } else {
      return 0;
    }
  };

  MathUtil.pad = function(num, size) {
    var s = num+"";
    while (s.length < size) s = "0" + s;
    return s;
  };

  MathUtil.round = function(value, precision) {
    return +value.toFixed(precision);
  };

  MathUtil.roundToNearest = function(value, nearest) {
    return Math.round(value / nearest) * nearest;
  };

  MathUtil.stats = function(array) {
    const n = array.length;
    if (n <= 0) {
      return {mean: 0, std: 0};
    }
    const mean = array.reduce((a, b) => a + b) / n;
    return {
      mean: mean,
      std: Math.sqrt(array.map(x => Math.pow(x - mean, 2)).reduce((a, b) => a + b) / n)
    };
  };

  MathUtil.within = function(num, min, max) {
    if (num < min) return false;
    if (num > max) return false;
    return true;
  };

  MathUtil.wrap = function(num, min, max) {
    if (num >= min && num <= max) return num;
    else if (num < min) return max;
    else return min;
    // var delta = max - min;
    // if (delta < 1) return 0;
    // return ((num-min) % delta) + min;
  };

})();



'use strict';

var UI = (function() {

  function UI(config) {
    var defaults = {};
    this.opt = _.extend({}, defaults, config);
    this.init();
  }

  UI.prototype.init = function(){
    this.loadListeners();
  };

  UI.prototype.loadListeners = function(){
    $('body').on('click', '.toggle-parent', function(e){
      e.preventDefault();
      var $el = $(this);
      var $parent = $el.parent();
      $parent.toggleClass('active');
      var activeText = $el.attr('data-active');
      if (activeText && activeText.length) {
        if ($parent.hasClass('active')) {
          $el.text($el.attr('data-active'));
        } else {
          $el.text($el.attr('data-inactive'));
        }
      }
    });
  };

  return UI;

})();

$(function() {
  var ui = new UI({});
});
