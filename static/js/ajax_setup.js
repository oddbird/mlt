(function($) {
    $.ajaxSettings.traditional = true;
    $("body").ajaxError(function(event, request, settings, error) {
        var data;
        $('body').loadingOverlay('remove');
        if(error === "UNAUTHORIZED") {
            var login_url = $("body").data("login-url");
            window.location = login_url + "?next=" + window.location.pathname;
        } // @@@ any global default error handling needed?
    });
})(jQuery);
