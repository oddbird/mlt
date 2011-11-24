/*jslint    browser:    true,
            indent:     4 */
/*global    ich, jQuery */

var MLT = (function (MLT, $) {

    'use strict';

    MLT.loadNewParcels = function () {
        var container = $('#load-parcels-status'),
            ajax_url = window.location.pathname,
            try_again_url = container.data('load-parcels-url'),
            ready = false,
            updateLoadingStatus = function () {
                var jqxhr = $.get(ajax_url, function (data) {
                    var newInfo;
                    data.url = try_again_url;
                    newInfo = ich.loading_parcels(data);
                    container.html(newInfo);
                    if (data.ready) {
                        container.addClass('ready');
                        ready = true;
                        if (!data.successful) {
                            container.addClass('failed');
                        }
                    }
                }).error(function () {
                    var failedInfo = ich.loading_parcels({
                        status: 'FAILURE',
                        ready: true,
                        info: 'Ajax error.',
                        successful: false
                    });
                    container.html(failedInfo).addClass('ready failed');
                    ready = true;
                });
            },
            refreshStatus = function () {
                updateLoadingStatus();
                $.doTimeout(3000, function () {
                    if (!ready) {
                        updateLoadingStatus();
                    } else {
                        return false;
                    }
                    return true;
                });
            };

        refreshStatus();
    };

    return MLT;

}(MLT || {}, jQuery));
