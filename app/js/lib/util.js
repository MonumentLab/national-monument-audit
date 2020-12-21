// Utility functions

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

  Util.formatNumber = function(number){
    return number.toLocaleString();
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
      return JSON.parse('{"' + search.replace(/&/g, '","').replace(/=/g,'":"') + '"}', function(key, value) { return key===""?value:decodeURIComponent(value) });
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
