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
            jqxhr = null,
            updateLoadingStatus = function () {
                jqxhr = $.get(ajax_url, function (data) {
                    var newInfo;
                    data.url = try_again_url;
                    newInfo = ich.loading_parcels(data);
                    container.html(newInfo);
                    if (data.ready) {
                        container.removeClass('loading-parcels');
                        ready = true;
                        if (data.successful) {
                            container.addClass('ready');
                        } else {
                            container.addClass('failed');
                        }
                    }
                    jqxhr = null;
                }).error(function () {
                    var failedInfo = ich.loading_parcels({
                        status: 'FAILURE',
                        ready: true,
                        info: 'Ajax error.',
                        successful: false
                    });
                    container.html(failedInfo).removeClass('loading-parcels').addClass('failed');
                    ready = true;
                });
            },
            refreshStatus = function () {
                updateLoadingStatus();
                $.doTimeout(1000, function () {
                    if (!ready) {
                        if (!jqxhr) {
                            updateLoadingStatus();
                        }
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
