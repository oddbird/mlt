/*jslint    browser:    true,
            indent:     4 */
/*global    jQuery */

(function ($) {

    'use strict';

    $.ajaxSettings.traditional = true;
    $("body").ajaxError(function (event, request, settings, error) {
        var login_url;
        $('body').loadingOverlay('remove');
        if (error === "UNAUTHORIZED") {
            login_url = $("body").data("login-url");
            window.location = login_url + "?next=" + window.location.pathname;
        } // @@@ any global default error handling needed?
    });
}(jQuery));
