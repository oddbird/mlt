/*jslint    browser:    true,
            indent:     4 */
/*global    ich, jQuery */

var MLT = (function (MLT, $) {

    'use strict';

    $(function () {
        // plugins
        $('input[placeholder], textarea[placeholder]').placeholder();
        $('.details:not(html)').html5accordion();
        $('#messages').messages({ handleAjax: true });

        // map.js
        if ($('#addresstable').length) {
            MLT.addressListHeight('#addressform', '.managelist');
            MLT.addressPopups();
            MLT.mapAddress();
            MLT.sorting('#addressform');
            MLT.addressDetails();
            MLT.addressSelect();
            MLT.addressZoom();
            MLT.exportAddresses();
            MLT.editAddress();
            MLT.addAddress();
            MLT.addressActions();
            MLT.filtering();
            MLT.selectAll();
            MLT.mapInfo();
            MLT.ajaxPagination();
            MLT.importAddressesLightbox();
            MLT.initializeMap();
        }

        // history.js
        if ($('#history').length) {
            MLT.historyAjaxPagination();
            MLT.sorting('#history');
            MLT.addressListHeight('#history > .actions', '#history .revisionlist');
            MLT.filtering();
            MLT.filterByAddress();
        }
    });

    return MLT;

}(MLT || {}, jQuery));
