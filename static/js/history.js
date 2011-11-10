/*jslint    browser:    true,
            indent:     4 */
/*global    ich, jQuery */

var MLT = (function (MLT, $) {

    'use strict';

    var context = $('#history'),
        changesList = context.find('.revisionlist'),
        actions = context.find('.actions'),
        loadingURL = changesList.data('changes-url'),
        loadingMessage = changesList.find('.load'),
        sortData,
        filters,
        currentlyLoading,
        moreChanges,
        newChanges = function (data) {
            if (data.changes && data.changes.length) {
                var changesHTML = ich.revision(data);

                loadingMessage.before(changesHTML).css('opacity', 0).find('p').html('loading changes...');
                changesHTML.find('.details').html5accordion();
                moreChanges = true;
                // if (scroll) {
                //     addressContainer.scrollTop(scroll);
                // }
                // if ($('#addressform .actions .bulkselect').data('selectall')) {
                //     addressContainer.find('.address input[id^="select"]').prop('checked', true);
                // }
            } else {
                loadingMessage.find('p').html('no more changes');
                moreChanges = false;
            }
            if (data.count || data.count === 0) {
                $('#filter .filtercontrols .listlength').html(data.count);
            }
            // if (addressContainer.data('trusted') !== 'trusted') {
            //     addressContainer.find('.address input[name="flag_for_review"]:checked').attr('disabled', 'disabled');
            // }
            currentlyLoading = false;
            // scroll = false;
        };

    MLT.loadChanges = function (opts) {
        var count = changesList.find('.revision').length + 1,
            defaults = {
                // sort: sortData,
                start: count
            },
            // options = $.extend({}, defaults, filters, opts);
            options = $.extend({}, defaults, opts);
        // if (loadingURL && sortData) {
        if (loadingURL) {
            loadingMessage.animate({opacity: 1}, 'fast');
            currentlyLoading = true;
            // @@@ if this returns with errors, subsequent ajax calls will be prevented unless currentlyLoading is set to `false`
            $.get(loadingURL, options, newChanges);
        }
    };

    MLT.historyAjaxPagination = function () {
        $(window).scroll(function () {
            $.doTimeout('scroll', 150, function () {
                if ($(document).height() - ($(window).scrollTop() + $(window).height()) <= loadingMessage.outerHeight() && moreChanges && !currentlyLoading) {
                    MLT.loadChanges();
                }
            });
        });
    };

    return MLT;

}(MLT || {}, jQuery));
