/*jslint    browser:    true,
            indent:     4,
            confusion:  true */
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

                changesHTML.each(function () {
                    var revision = $(this),
                        changedFields;

                    if (revision.data('changed-fields')) {
                        changedFields = revision.data('changed-fields').trim().split(' ');
                        $.each(changedFields, function (i, field) {
                            revision.find('.' + field).wrapInner('<mark />');
                        });
                    }
                });
                loadingMessage.before(changesHTML).css('opacity', 0).find('p').html('loading changes...');
                changesHTML.find('.details').html5accordion();
                moreChanges = true;
                if (scroll) {
                    changesList.scrollTop(scroll);
                }
            } else {
                loadingMessage.find('p').html('no more changes');
                moreChanges = false;
            }
            if (data.count || data.count === 0) {
                $('#filter .filtercontrols .listlength').html(data.count);
            }
            currentlyLoading = false;
            scroll = false;
        };

    MLT.history = {
        sortData: {},
        filters: {}
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
            scroll = changesList.scrollTop();
        }
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
        changesList.scroll(function () {
            $.doTimeout('scroll', 150, function () {
                if ((changesList.get(0).scrollHeight - changesList.scrollTop() - changesList.outerHeight()) <= loadingMessage.outerHeight() && moreChanges && !currentlyLoading) {
                    MLT.loadMoreChanges();
                }
            });
        });
    };

    MLT.filterByAddress = function () {
        var filterList = context.find('#filter .visual > ul'),
            hash,
            addFilter = function (id) {
                var newFilter = ich.filter_applied({
                        field: 'address_id',
                        value: id,
                        desc: 'address id',
                        name: id
                    });

                if (newFilter.length) {
                    filterList.html(newFilter);
                    filterList.trigger('update-filters');
                }
            };

        changesList.on('click', '.revision .controls .action-history', function () {
            addFilter($(this).closest('.revision').data('address-id'));
            return false;
        });

        if (window.location.hash && window.location.hash.split('_')[2]) {
            hash = window.location.hash.split('_')[2];
            addFilter(hash);
        } else {
            MLT.reloadChangesList();
        }
    };

    MLT.revertChange = function () {
        changesList.on('click', '.revision .controls .action-revert', function (e) {
            e.preventDefault();
            var url = $(this).data('revert-url'),
                thisChange = $(this).closest('.revision');
            thisChange.loadingOverlay();
            $.post(url, function (data) {
                thisChange.loadingOverlay('remove');
                if (data.success) {
                    MLT.reloadChangesList(data);
                }
            });
        });
    };

    return MLT;

}(MLT || {}, jQuery));
