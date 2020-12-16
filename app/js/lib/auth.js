'use strict';

(function() {
  window.Auth = {};

  Auth.authenticate = function(msg){
    var isValid = false;
    msg = msg || 'Please enter password:';

    var authenticated = Util.cookieGet('authenticated');

    if (!authenticated) {
      var answer = prompt(msg);
      if (answer != null) {
        var hash = CryptoJS.MD5(answer).toString();
        if (hash === '293577d3615f67c577ed0f19075555b5') isValid = true;
      }
    } else {
      isValid = true;
    }

    if (isValid) {
      Util.cookieSet('authenticated', 1, 30); // keep for 30 days
      return true;
    } else {
      return Auth.authenticate('Incorrect password. Please try again:');
    }
  };

})();
