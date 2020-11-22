// Utility functions

(function() {
  window.Util = {};

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
          obj[key+'Index'] = obj[key];
          obj[key] = groupList[obj[key]];
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
