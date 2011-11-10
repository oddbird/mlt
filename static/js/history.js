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
        },
        reloadList = function (opts, preserveScroll) {
            var defaults = {
                    sort: sortData,
                    start: 1,
                    num: 20,
                    count: true
                },
                options = $.extend({}, defaults, filters, opts);
            if (preserveScroll) {
                scroll = $(window).scrollTop();
            }
            // if (!preserveSelectAll) {
            //     $('#addressform .actions .bulkselect').data('selectall', false).find('#select_all_none').prop('checked', false);
            // }
            // preserveSelectAll = false;
            loadingMessage.css('opacity', 1).find('p').html('loading changes...');
            changesList.find('.revision').remove();
            if (loadingURL && sortData) {
                currentlyLoading = true;
                $.get(loadingURL, options, newChanges);
            }
        };

    MLT.loadMoreChanges = function (opts) {
        var count = changesList.find('.revision').length + 1,
            defaults = {
                sort: sortData,
                start: count
            },
            options = $.extend({}, defaults, filters, opts);
        if (loadingURL && sortData) {
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

    MLT.changesSorting = function () {
        var list = context.find('.actions .listordering > ul'),
            items = list.find('li[class^="by"]'),
            fields = items.find('.field'),
            directions = items.find('.dir'),
            sortList = function () {
                list.find('.none').insertAfter(list.find('li:not(.none)').last());
            },
            updateSortData = function () {
                sortData = items.not('.none').map(function () {
                    var thisName = $(this).find('.field').data('field');
                    if ($(this).find('.dir').hasClass('desc')) {
                        thisName = '-' + thisName;
                    }
                    return thisName;
                }).get();
                // preserveSelectAll = true;
                reloadList();
            };

        fields.click(function () {
            if (!($(this).closest('li[class^="by"]').hasClass('none'))) {
                $(this).closest('li[class^="by"]').find('.dir').removeClass('asc desc').html('none');
            } else {
                $(this).closest('li[class^="by"]').find('.dir').addClass('asc').html('ascending');
            }
            $(this).closest('li[class^="by"]').toggleClass('none');
            sortList();
            updateSortData();
            return false;
        });

        directions.click(function () {
            if ($(this).closest('li[class^="by"]').hasClass('none')) {
                $(this).closest('li[class^="by"]').removeClass('none');
            }
            if ($(this).hasClass('asc') || $(this).hasClass('desc')) {
                if ($(this).hasClass('asc')) {
                    $(this).html('descending');
                }
                if ($(this).hasClass('desc')) {
                    $(this).html('ascending');
                }
                $(this).toggleClass('asc desc');
            } else {
                $(this).addClass('asc').html('ascending');
            }
            sortList();
            updateSortData();
            return false;
        });

        list.sortable({
            delay: 30,
            update: function (event, ui) {
                if (ui.item.hasClass('none')) {
                    ui.item.removeClass('none').find('.dir').addClass('asc').html('ascending');
                }
                sortList();
                updateSortData();
            }
        });

        updateSortData();
    };

    return MLT;

}(MLT || {}, jQuery));
