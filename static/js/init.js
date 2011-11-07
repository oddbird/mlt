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

        // local.js
        MLT.addressListHeight();
        MLT.addressPopups();
        MLT.mapAddress();
        MLT.addressSorting();
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
    });

    return MLT;

}(MLT || {}, jQuery));
