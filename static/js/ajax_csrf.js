/*jslint    browser:    true,
            indent:     4 */
/*global    jQuery */

(function ($) {

    'use strict';

    // from http://docs.djangoproject.com/en/1.3/ref/contrib/csrf/#ajax
    $('html').ajaxSend(
        function (event, xhr, settings) {
            var getCookie = function (name) {
                var cookies, cookie, i,
                    cookieValue = null;
                if (document.cookie && document.cookie !== '') {
                    cookies = document.cookie.split(';');
                    for (i = 0; i < cookies.length; i = i + 1) {
                        cookie = $.trim(cookies[i]);
                        // Does this cookie string begin with the name we want?
                        if (cookie.substring(0, name.length + 1) === (name + '=')) {
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }
                    }
                }
                return cookieValue;
            };
            xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
        }
    );

}(jQuery));
