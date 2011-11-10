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
        currentlyLoading,
        moreChanges,
        scroll,
        newChanges = function (data) {
            if (data.changes && data.changes.length) {
                var changesHTML = ich.revision(data);

                loadingMessage.before(changesHTML).css('opacity', 0).find('p').html('loading changes...');
                changesHTML.find('.details').html5accordion();
                moreChanges = true;
                if (scroll) {
                    $(window).scrollTop(scroll);
                }
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
            scroll = false;
        };

    MLT.history = {
        sortData: null,
        filters: null,
        preserveSelectAll: null
    };

    MLT.reloadChangesList = function (opts, preserveScroll) {
        var defaults = {
                sort: MLT.history.sortData,
                start: 1,
                num: 20,
                count: true
            },
            options = $.extend({}, defaults, MLT.history.filters, opts);
        if (preserveScroll) {
            scroll = $(window).scrollTop();
        }
        // if (!MLT.history.preserveSelectAll) {
        //     $('#addressform .actions .bulkselect').data('selectall', false).find('#select_all_none').prop('checked', false);
        // }
        // MLT.history.preserveSelectAll = false;
        loadingMessage.css('opacity', 1).find('p').html('loading changes...');
        changesList.find('.revision').remove();
        if (loadingURL && MLT.history.sortData) {
            currentlyLoading = true;
            $.get(loadingURL, options, newChanges);
        }
    };

    MLT.loadMoreChanges = function (opts) {
        var count = changesList.find('.revision').length + 1,
            defaults = {
                sort: MLT.history.sortData,
                start: count
            },
            options = $.extend({}, defaults, MLT.history.filters, opts);
        if (loadingURL && MLT.history.sortData) {
            loadingMessage.animate({opacity: 1}, 'fast');
            currentlyLoading = true;
            $.get(loadingURL, options, newChanges);
        }
    };

    MLT.historyAjaxPagination = function () {
        $(window).scroll(function () {
            $.doTimeout('scroll', 150, function () {
                if ($(document).height() - ($(window).scrollTop() + $(window).height()) <= loadingMessage.outerHeight() && moreChanges && !currentlyLoading) {
                    MLT.loadMoreChanges();
                }
            });
        });
    };

    return MLT;

}(MLT || {}, jQuery));
