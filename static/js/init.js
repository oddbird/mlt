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
            MLT.addressListHeight('#addresstable > div > .actions', '#addressform > .managelist');
            MLT.addressPopups();
            MLT.mapAddress();
            MLT.sorting('#addresstable');
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
            MLT.addressLoading.reloadList();
            MLT.addImportTag();
        }

        // history.js
        if ($('#history').length) {
            MLT.historyAjaxPagination();
            MLT.sorting('#history');
            MLT.addressListHeight('#history > .actions', '#history .revisionlist');
            MLT.filtering();
            MLT.filterByAddress();
            MLT.revertChange();
        }

        // load-parcels.js
        if ($('#load-parcels-status').length) {
            MLT.loadNewParcels();
        }
    });

    return MLT;

}(MLT || {}, jQuery));
