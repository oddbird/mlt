/*jslint    browser:    true,
            indent:     4,
            confusion:  true */
/*global    L, ich, jQuery */

var MLT = (function (MLT, $) {

    'use strict';

    var MIN_PARCEL_ZOOM = 17,
        mapinfoHover = false,
        mapinfo = $('#mapinfo'),
        mapinfoTimeout = null,
        geojson_url = $('#mapping').data('parcel-geojson-url'),
        geojson = new L.GeoJSON(),
        selectedLayer = null,
        selectedId = null,
        selectedInfo = null,
        selectedParcelInfo = null,
        sortData = {},
        filters = {},
        addressContainer = $('#addresstable .managelist'),
        loadingURL = addressContainer.data('addresses-url'),
        loadingMessage = addressContainer.find('.load'),
        refreshButton = $('#addresstable #filter .refresh'),
        bulkSelect = $('#addressform .actions .bulkselect'),
        preserveSelectAll = null,
        parcelMap = {},
        listXHR = null,
        listCounter = 0,
        parcelXHR = null,
        parcelCounter = 0;

    MLT.keycodes = {
        SPACE: 32,
        ENTER: 13,
        TAB: 9,
        ESC: 27,
        BACKSPACE: 8,
        SHIFT: 16,
        CTRL: 17,
        ALT: 18,
        CAPS: 20,
        LEFT: 37,
        UP: 38,
        RIGHT: 39,
        DOWN: 40
    };

    MLT.addressLoading = {
        moreAddresses: true,
        currentlyLoading: false,
        scroll: false,
        newAddresses: function (data) {
            if (data.addresses && data.addresses.length) {
                $.each(data.addresses, function (i, address) {
                    var addressHTML = ich.address(address);

                    if (!(addressContainer.find('.address[data-id="' + address.id + '"]').length)) {
                        loadingMessage.before(addressHTML);
                        addressHTML.find('.details').html5accordion();
                    }
                });
                loadingMessage.css('opacity', 0).find('p').html('loading addresses...');
                MLT.addressLoading.moreAddresses = true;
                if (MLT.addressLoading.scroll) {
                    addressContainer.scrollTop(MLT.addressLoading.scroll);
                }
                if (bulkSelect.data('selectall')) {
                    addressContainer.find('.address .item-select').prop('checked', true);
                }
            } else {
                loadingMessage.find('p').html('no more addresses');
                MLT.addressLoading.moreAddresses = false;
            }
            if (data.count || data.count === 0) {
                $('#addressform .actions .listlength').html(data.count);
            }
            if (addressContainer.data('trusted') !== 'trusted') {
                addressContainer.find('.address input[name="flag_for_review"]:checked').attr('disabled', 'disabled');
            }
            MLT.addressLoading.currentlyLoading = false;
            MLT.addressLoading.scroll = false;
        },
        replaceAddress: function (data) {
            var thisAddress, updatedAddress, address, id, index, checked, popup;
            if (data.success && data.address) {
                address = data.address;
                id = address.id;
                thisAddress = addressContainer.find('.address[data-id="' + id + '"]');
                index = thisAddress.find('.mapkey').text();

                if (thisAddress.find('.item-select').is(':checked')) {
                    checked = true;
                    address.checked = true;
                    popup = thisAddress.find('.item-select').get(0).popup;
                }
                address.index = index;
                updatedAddress = ich.address(address);

                if (thisAddress.find('.info.details').hasClass('open')) {
                    updatedAddress.find('.info.details').addClass('open');
                }
                thisAddress.replaceWith(updatedAddress);
                updatedAddress.find('.details').html5accordion();
                refreshButton.addClass('expired');
                if (checked && popup) {
                    updatedAddress.find('.item-select').get(0).popup = popup;
                }
                if (addressContainer.data('trusted') !== 'trusted') {
                    addressContainer.find('.address input[name="flag_for_review"]:checked').attr('disabled', 'disabled');
                }
            }
        },
        replaceAddresses: function (data, removePopup) {
            if (data.addresses && data.addresses.length) {
                $.each(data.addresses, function (i, address) {
                    var updatedAddress,
                        id = address.id,
                        thisAddress = addressContainer.find('.address[data-id="' + id + '"]'),
                        index = thisAddress.find('.mapkey').text(),
                        checked,
                        popup;

                    if (thisAddress.length) {
                        if (thisAddress.find('.item-select').is(':checked')) {
                            checked = true;
                            address.checked = true;
                            if (removePopup) {
                                MLT.map.removeLayer(thisAddress.find('.item-select').get(0).popup);
                            } else {
                                popup = thisAddress.find('.item-select').get(0).popup;
                            }
                        }
                        address.index = index;
                        updatedAddress = ich.address(address);

                        if (thisAddress.find('.info.details').hasClass('open')) {
                            updatedAddress.find('.info.details').addClass('open');
                        }
                        thisAddress.replaceWith(updatedAddress);
                        updatedAddress.find('.details').html5accordion();
                        if (checked && popup) {
                            updatedAddress.find('.item-select').get(0).popup = popup;
                        }
                    }
                });
                refreshButton.addClass('expired');
                if (addressContainer.data('trusted') !== 'trusted') {
                    addressContainer.find('.address input[name="flag_for_review"]:checked').attr('disabled', 'disabled');
                }
            }
        },
        reloadList: function (opts, preserveScroll) {
            var defaults = {
                    sort: sortData,
                    start: 1,
                    num: 20,
                    count: true
                },
                options = $.extend({}, defaults, filters, opts),
                counter;

            if (listXHR) { listXHR.abort(); }
            listCounter = listCounter + 1;
            counter = listCounter;

            if (preserveScroll) {
                MLT.addressLoading.scroll = addressContainer.scrollTop();
            }
            addressContainer.find('.address .item-select:checked').click();
            if (!preserveSelectAll) {
                bulkSelect.data('selectall', false).find('#select_all_none').prop('checked', false);
            }
            preserveSelectAll = false;
            loadingMessage.css('opacity', 1).find('p').html('loading addresses...');
            addressContainer.find('.address').remove();
            refreshButton.removeClass('expired');
            if (loadingURL && sortData) {
                MLT.addressLoading.currentlyLoading = true;
                // @@@ if this returns with errors, subsequent ajax calls will be prevented unless currentlyLoading is set to `false`
                listXHR = $.get(loadingURL, options, function (data) {
                    if (counter === listCounter) {
                        MLT.addressLoading.newAddresses(data);
                        listXHR = null;
                    }
                });
            }
        },
        addMore: function (opts) {
            var count = addressContainer.find('.address').length + 1,
                defaults = {
                    sort: sortData,
                    start: count
                },
                options = $.extend({}, defaults, filters, opts),
                counter;

            if (listXHR) { listXHR.abort(); }
            listCounter = listCounter + 1;
            counter = listCounter;

            if (loadingURL && sortData) {
                loadingMessage.animate({opacity: 1}, 'fast');
                MLT.addressLoading.currentlyLoading = true;
                // @@@ if this returns with errors, subsequent ajax calls will be prevented unless currentlyLoading is set to `false`
                listXHR = $.get(loadingURL, options, function (data) {
                    if (counter === listCounter) {
                        MLT.addressLoading.newAddresses(data);
                        listXHR = null;
                    }
                });
            }
        }
    };

    MLT.addressListHeight = function (actions, list) {
        var headerHeight = $('header[role="banner"]').outerHeight(),
            actionsHeight = $(actions).outerHeight(),
            addressListHeight,
            updateHeight = function () {
                addressListHeight = $(window).height() - headerHeight - actionsHeight;
                $(list).css('height', addressListHeight.toString() + 'px');
            };
        updateHeight();
        $(window).resize(function () {
            $.doTimeout('resize', 250, function () {
                updateHeight();
            });
        });
    };

    MLT.initializeMap = function () {
        if ($('#map').length) {
            MLT.map = new L.Map('map', {
                center: new L.LatLng(MLT.mapDefaultLat, MLT.mapDefaultLon),
                zoom: MLT.mapDefaultZoom,
                layers: [new L.TileLayer(MLT.tileServerUrl, {attribution: MLT.mapCredits})],
                closePopupOnClick: false
            });

            MLT.map.on('moveend', function () {
                MLT.refreshParcels();
            });
        }
    };

    MLT.showInfo = function (newInfo, selected) {
        var mapped_toIDs, i, already_mapped,
            selectedAddresses = addressContainer.find('.address .item-select:checked');
        if (mapinfoTimeout) {
            clearTimeout(mapinfoTimeout);
            mapinfoTimeout = null;
        }
        mapinfo.html(newInfo).show();
        if (selected) {
            mapinfo.addClass("selected");
            mapped_toIDs = mapinfo.find('.mapped-addresses ul li').map(function () {
                return $(this).data('id');
            }).get();
            selectedAddresses.each(function () {
                var this_is_mapped;
                for (i = 0; i < mapped_toIDs.length; i = i + 1) {
                    if ($(this).closest('.address').data('id') === mapped_toIDs[i]) {
                        this_is_mapped = true;
                    }
                }
                if (this_is_mapped !== true) {
                    already_mapped = false;
                }
            });
            // Only show `map to selected` button if an address is selected
            if (selectedAddresses.length && already_mapped === false) {
                mapinfo.find('.mapit').show();
            } else {
                mapinfo.find('.mapit').hide();
            }
        } else {
            mapinfo.removeClass("selected");
            mapinfo.find('.mapit').hide();
        }
    };

    MLT.hideInfo = function () {
        if (!selectedInfo) {
            mapinfoTimeout = setTimeout(function () {
                if (!mapinfoHover) {
                    mapinfo.empty().hide();
                }
            }, 100);
        }
    };

    MLT.refreshParcels = function () {
        var bounds = MLT.map.getBounds(),
            ne = bounds.getNorthEast(),
            sw = bounds.getSouthWest(),
            counter;

        if (parcelXHR) { parcelXHR.abort(); }
        parcelCounter = parcelCounter + 1;
        counter = parcelCounter;

        if (MLT.map.getZoom() >= MIN_PARCEL_ZOOM) {
            parcelXHR = $.getJSON(
                geojson_url + "?southlat=" + sw.lat + "&northlat=" + ne.lat + "&westlng=" + sw.lng + "&eastlng=" + ne.lng,
                function (data) {
                    if (counter === parcelCounter) {
                        parcelXHR = null;
                        MLT.map.removeLayer(geojson);
                        selectedLayer = null;
                        parcelMap = {};
                        geojson = new L.GeoJSON();

                        geojson.on('featureparse', function (e) {
                            var id = e.id,
                                pl = e.properties.pl;

                            e.layer.info = ich.parcelinfo(e.properties);
                            parcelMap[pl] = e;

                            e.layer.select = function () {
                                if (selectedLayer) {
                                    selectedLayer.unselect();
                                }
                                selectedParcelInfo = e.properties;
                                selectedId = id;
                                selectedInfo = this.info;
                                selectedLayer = this;
                                this.selected = true;
                                this.setStyle({
                                    color: "red",
                                    weight: 5
                                });
                            };
                            e.layer.unselect = function () {
                                if (this.selected) {
                                    selectedId = null;
                                    selectedInfo = null;
                                    selectedLayer = null;
                                }
                                this.selected = false;
                                this.setStyle({
                                    color: "blue",
                                    weight: 2
                                });
                            };
                            if (id === selectedId) {
                                e.layer.select();
                            } else {
                                e.layer.unselect();
                            }
                            e.layer.on('mouseover', function (ev) {
                                if (!selectedInfo) {
                                    MLT.showInfo(e.layer.info, false);
                                }
                            });
                            e.layer.on('mouseout', function (ev) {
                                MLT.hideInfo();
                            });
                            e.layer.on('click', function (ev) {
                                if (ev.target.selected) {
                                    ev.target.unselect();
                                    MLT.showInfo(e.layer.info, false);
                                } else {
                                    ev.target.select();
                                    MLT.showInfo(e.layer.info, true);
                                }
                            });
                        });

                        geojson.addGeoJSON(data);
                        MLT.map.addLayer(geojson);
                    }
                }
            );
        } else {
            MLT.map.removeLayer(geojson);
        }
    };

    MLT.updateParcelMapping = function (action, array, PLs, id, updateMapInfo, addressData) {
        var rejectButton,
            removeMapping = function (pl) {
                var index;
                if (parcelMap[pl]) {
                    $.each(parcelMap[pl].properties.mapped_to, function (i, properties) {
                        if (properties.id === id) {
                            index = i;
                        }
                    });
                    parcelMap[pl].properties.mapped_to.splice(index, 1);
                    if (!(parcelMap[pl].properties.mapped_to.length)) {
                        parcelMap[pl].properties.mapped = false;
                    }
                    parcelMap[pl].layer.info = ich.parcelinfo(parcelMap[pl].properties);
                }
            },
            updateMapping = function (pl) {
                if (parcelMap[pl]) {
                    $.each(parcelMap[pl].properties.mapped_to, function (i, properties) {
                        if (properties.id === id) {
                            parcelMap[pl].properties.mapped_to[i] = addressData;
                            parcelMap[pl].layer.info = ich.parcelinfo(parcelMap[pl].properties);
                        }
                    });
                }
            };

        if (array) {
            $.each(PLs, function (i, pl) {
                if (action === 'remove') {
                    removeMapping(pl);
                } else if (action === 'update') {
                    updateMapping(pl);
                }
            });
        } else {
            if (action === 'remove') {
                removeMapping(PLs);
            } else if (action === 'update') {
                updateMapping(PLs);
            }
        }
        if (updateMapInfo) {
            if (action === 'remove') {
                mapinfo.find('.mapped-addresses li[data-id="' + id + '"]').remove();
                if (!(mapinfo.find('.mapped-addresses ul > li').length)) {
                    mapinfo.find('.mapped-addresses h4, .mapped-addresses ul').remove();
                }
            } else if (action === 'update') {
                if (updateMapInfo === 'street') {
                    if (mapinfo.find('li[data-id="' + id + '"]').length) {
                        rejectButton = mapinfo.find('li[data-id="' + id + '"] .action-reject');
                        mapinfo.find('li[data-id="' + id + '"]').html(addressData.street).append(rejectButton);
                    }
                } else if (updateMapInfo === 'flag-approve') {
                    if (addressData.needs_review) {
                        mapinfo.find('li[data-id="' + id + '"]').addClass('flagged');
                    } else {
                        mapinfo.find('li[data-id="' + id + '"]').removeClass('flagged');
                    }
                }
            }
        }
    };

    MLT.addressPopups = function () {
        addressContainer.on('change', '.address .item-select', function () {
            var input, mapped_toIDs, i, already_mapped,
                thisAddress = $(this).closest('.address'),
                id = thisAddress.data('id'),
                popupContent = thisAddress.find('.mapkey').html(),
                lat = thisAddress.data('latitude'),
                lng = thisAddress.data('longitude'),
                geolat = thisAddress.data('geocode-latitude'),
                geolng = thisAddress.data('geocode-longitude'),
                geoURL = addressContainer.data('geocode-url'),
                geocoding_failed = thisAddress.data('geocoding-failed');
            if ($(this).is(':checked')) {
                if (lat && lng) {
                    this.popup = new L.Popup({ autoPan: false });
                    this.popup.setLatLng(new L.LatLng(lat, lng));
                    this.popup.setContent(popupContent);
                    MLT.map.addLayer(this.popup);
                    MLT.map.panTo(new L.LatLng(lat, lng));
                    if (MLT.map.getZoom() < MIN_PARCEL_ZOOM) {
                        MLT.map.setZoom(MIN_PARCEL_ZOOM);
                    }
                } else {
                    if (geolat && geolng) {
                        this.popup = new L.Popup({ autoPan: false });
                        this.popup.setLatLng(new L.LatLng(geolat, geolng));
                        this.popup.setContent(popupContent);
                        MLT.map.addLayer(this.popup);
                        $('#map .leaflet-map-pane .leaflet-objects-pane .leaflet-popup-pane .leaflet-popup-content').filter(function (index) {
                            return $(this).html() === popupContent;
                        }).closest('.leaflet-popup').addClass('geocoded');
                        MLT.map.panTo(new L.LatLng(geolat, geolng));
                        if (MLT.map.getZoom() < MIN_PARCEL_ZOOM) {
                            MLT.map.setZoom(MIN_PARCEL_ZOOM);
                        }
                    } else {
                        if (geoURL && id && !geocoding_failed) {
                            thisAddress.loadingOverlay();
                            $.get(geoURL, {id: id}, function (data) {
                                if (data.address) {
                                    var updatedAddress,
                                        index = thisAddress.find('.mapkey').html(),
                                        address = data.address;

                                    $.extend(address, {'index': index, 'checked': true});
                                    updatedAddress = ich.address(address);

                                    thisAddress.replaceWith(updatedAddress);
                                    updatedAddress.find('.details').html5accordion();
                                    refreshButton.addClass('expired');

                                    if (address.geocoded && address.geocoded.latitude && address.geocoded.longitude) {
                                        input = updatedAddress.find('.item-select').get(0);
                                        input.popup = new L.Popup({ autoPan: false });
                                        input.popup.setLatLng(new L.LatLng(address.geocoded.latitude, address.geocoded.longitude));
                                        input.popup.setContent(popupContent);
                                        MLT.map.addLayer(input.popup);
                                        MLT.map.panTo(new L.LatLng(address.geocoded.latitude, address.geocoded.longitude));
                                        if (MLT.map.getZoom() < MIN_PARCEL_ZOOM) {
                                            MLT.map.setZoom(MIN_PARCEL_ZOOM);
                                        }
                                        $('#map .leaflet-map-pane .leaflet-objects-pane .leaflet-popup-pane .leaflet-popup-content').filter(function (index) {
                                            return $(this).html() === popupContent;
                                        }).closest('.leaflet-popup').addClass('geocoded');
                                    }

                                    if (addressContainer.data('trusted') !== 'trusted') {
                                        addressContainer.find('.address input[name="flag_for_review"]:checked').attr('disabled', 'disabled');
                                    }
                                } else {
                                    thisAddress.data('geocoding-failed', true).loadingOverlay('remove');
                                }
                            });
                        }
                    }
                }
            } else {
                if (this.popup) {
                    MLT.map.removeLayer(this.popup);
                }
            }

            // Only show `map to selected` button if an address is selected
            // and isn't already mapped to the selected parcel
            mapped_toIDs = mapinfo.find('.mapped-addresses ul li').map(function () {
                return $(this).data('id');
            }).get();
            addressContainer.find('.address .item-select:checked').each(function () {
                var this_is_mapped;
                for (i = 0; i < mapped_toIDs.length; i = i + 1) {
                    if ($(this).closest('.address').data('id') === mapped_toIDs[i]) {
                        this_is_mapped = true;
                    }
                }
                if (this_is_mapped !== true) {
                    already_mapped = false;
                }
            });
            if (addressContainer.find('.address .item-select:checked').length && already_mapped === false) {
                mapinfo.find('.mapit').show();
            } else {
                mapinfo.find('.mapit').hide();
            }
        });
    };

    MLT.mapAddress = function () {
        var url = $('#mapping').data('associate-url');
        mapinfo.on('click', '.mapit', function () {
            var options,
                notID,
                selectedAddressInput = addressContainer.find('.address .item-select:checked'),
                selectedAddressID = selectedAddressInput.map(function () {
                    return $(this).closest('.address').data('id');
                }).get(),
                selectedAddressPL = selectedAddressInput.map(function () {
                    return $(this).closest('.address').data('pl');
                }).get(),
                pl = selectedParcelInfo.pl,
                lat = selectedParcelInfo.latitude,
                lng = selectedParcelInfo.longitude,
                success = function (data) {
                    selectedAddressInput.each(function () { $(this).closest('.address').loadingOverlay('remove'); });
                    $.each(data.mapped_to, function (i, address) {
                        var updatedAddress,
                            id = address.id,
                            thisAddress = addressContainer.find('.address[data-id="' + id + '"]'),
                            index = thisAddress.find('.mapkey').html();

                        if (thisAddress.length && thisAddress.find('.item-select').is(':checked')) {
                            address.index = index;
                            updatedAddress = ich.address(address);

                            thisAddress.find('.item-select').click();
                            thisAddress.replaceWith(updatedAddress);
                            updatedAddress.find('.details').html5accordion();
                            refreshButton.addClass('expired');

                            MLT.updateParcelMapping('remove', true, selectedAddressPL, id, false);
                        }
                    });

                    var updatedParcelInfo = ich.parcelinfo(data);
                    mapinfo.removeClass('selected').html(updatedParcelInfo);
                    mapinfo.find('.mapit').hide();
                    selectedLayer.info = updatedParcelInfo;
                    if (selectedLayer) {
                        selectedLayer.unselect();
                    }

                    if (bulkSelect.data('selectall')) {
                        bulkSelect.data('selectall', false).find('#select_all_none').prop('checked', false);
                    }
                    if (addressContainer.data('trusted') !== 'trusted') {
                        addressContainer.find('.address input[name="flag_for_review"]:checked').attr('disabled', 'disabled');
                    }
                };

            selectedAddressInput.each(function () { $(this).closest('.address').loadingOverlay(); });

            if (bulkSelect.data('selectall')) {
                options = $.extend({}, filters, { maptopl: pl, aid: selectedAddressID });
                if (addressContainer.find('.address .item-select').not(':checked').length) {
                    notID = addressContainer.find('.address .item-select').not(':checked').map(function () {
                        return $(this).closest('.address').data('id');
                    }).get();
                    $.extend(options, { notid: notID });
                }
                $.post(url, options, success);
            } else {
                $.post(url, { maptopl: pl, aid: selectedAddressID }, success);
            }
        });
    };

    MLT.sorting = function (container) {
        var context = $(container),
            list = context.find('.actions .listordering > ul'),
            items = list.find('li[class^="by"]'),
            fields = items.find('.field'),
            directions = items.find('.dir'),
            localSortData,
            localPreserveSelectAll,
            reloadList = function () {
                if ($('#addresstable').length) {
                    MLT.addressLoading.reloadList();
                } else if ($('#history').length) {
                    MLT.reloadChangesList();
                }
            },
            sortList = function () {
                list.find('.none').insertAfter(list.find('li:not(.none)').last());
            },
            updateSortData = function () {
                localSortData = list.find('li[class^="by"]').not('.none').map(function () {
                    var thisName = $(this).find('.field').data('field');
                    if ($(this).find('.dir').hasClass('desc')) {
                        thisName = '-' + thisName;
                    }
                    return thisName;
                }).get();
                localPreserveSelectAll = true;
                if ($('#addresstable').length) {
                    preserveSelectAll = localPreserveSelectAll;
                    sortData = localSortData;
                } else if ($('#history').length) {
                    MLT.history.sortData = localSortData;
                }
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
            reloadList();
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
            reloadList();
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
                reloadList();
            }
        });

        updateSortData();
    };

    MLT.addressDetails = function () {
        addressContainer.on('click', '[id^="address-id"] .details .summary', function () {
            if ($(this).closest('.details').hasClass('open')) {
                $(this).closest('.address').addClass('expanded');
            } else {
                $(this).closest('.address').removeClass('expanded');
            }
            $(this).blur();
        });
    };

    MLT.addressSelect = function () {
        addressContainer.on('click', '.address .content', function (event) {
            if (!$(event.target).is('button, a, label, input, .summary, .adr, .street-address, .street-number, .street-prefix, .street-name, .street-type, .street-suffix, .locality, .region, .mapkey, .error, [contenteditable]')) {
                $(this).closest('.address').find('.item-select').click();
            }
        });
    };

    MLT.addressZoom = function () {
        addressContainer.on('click', '.address .content .mapkey', function (event) {
            var lat, lng,
                thisAddress = $(this).closest('.address');
            if (thisAddress.find('.item-select').is(':checked')) {
                lat = thisAddress.data('latitude') || thisAddress.data('geocode-latitude');
                lng = thisAddress.data('longitude') || thisAddress.data('geocode-longitude');
                if (lat && lng) {
                    MLT.map.panTo(new L.LatLng(lat, lng));
                    if (MLT.map.getZoom() < MIN_PARCEL_ZOOM) {
                        MLT.map.setZoom(MIN_PARCEL_ZOOM);
                    }
                }
            } else {
                thisAddress.find('.item-select').click();
            }
        });
    };

    MLT.exportAddresses = function () {
        var form = $('#export-address-form'),
            url = form.attr('action');

        form.submit(function () {
            var input, i;
            form.find('.export-filter').remove();
            $.each(filters, function (field, filter) {
                if (field === 'status') {
                    input = ich.export_filter({
                        field: field,
                        filter: filter
                    });
                    form.append(input);
                } else {
                    for (i = 0; i < filter.length; i = i + 1) {
                        input = ich.export_filter({
                            field: field,
                            filter: filter[i]
                        });
                        form.append(input);
                    }
                }
            });
        });
    };

    MLT.editAddress = function () {
        var originalStreet;

        addressContainer.on('click', '.action-edit', function (e) {
            e.preventDefault();
            var button = $(this),
                address = button.closest('.address'),
                addressInfo = address.find('.adr'),
                street = addressInfo.find('.street-address'),
                content = address.find('.content'),
                notes = address.find('.notes');

            content.addClass('editing').append('<button class="savechanges" title="save changes">save changes</button>');
            addressInfo.unwrap().find('.locality, .region, .complex-name').each(function () {
                $(this).attr('contenteditable', true).data('original', $(this).text());
            });
            if (street.data('parsed')) {
                street.find('span[class^="street-"]').each(function () {
                    $(this).attr('contenteditable', true).data('original', $(this).text());
                });
                originalStreet = street.find('span').map(function () { return $(this).text(); }).get().join(' ');
            } else {
                street.attr('contenteditable', true).data('original', street.text());
                originalStreet = street.text();
            }
            button.removeClass('action-edit').addClass('action-cancel').attr('title', 'cancel').html('cancel');
            notes.attr('contenteditable', true).data('original', notes.text());

            address.on('keydown', '[contenteditable]', function (e) {
                if (e.keyCode === MLT.keycodes.ENTER) {
                    e.preventDefault();
                    address.find('.savechanges').click();
                }
            });
        });

        addressContainer.on('click', '.action-cancel', function (e) {
            e.preventDefault();
            var button = $(this),
                address = button.closest('.address'),
                id = address.data('id'),
                addressInfo = address.find('.adr'),
                street = addressInfo.find('.street-address'),
                content = address.find('.content'),
                notes = address.find('.notes'),
                save = address.find('.savechanges');

            content.removeClass('editing');
            save.remove();
            button.removeClass('action-cancel').addClass('action-edit').attr('title', 'edit').html('edit');
            notes.removeAttr('contenteditable').text(notes.data('original'));
            addressInfo.wrap('<label for="select_' + id + '" />').find('.locality, .region, .complex-name').each(function () {
                $(this).removeAttr('contenteditable').text($(this).data('original'));
            });
            if (street.data('parsed')) {
                street.find('span[class^="street-"]').each(function () {
                    $(this).removeAttr('contenteditable').text($(this).data('original'));
                });
            } else {
                street.removeAttr('contenteditable').text(street.data('original'));
            }
        });

        addressContainer.on('click', '.savechanges', function () {
            var button = $(this),
                address = button.closest('.address'),
                url = address.find('.action-cancel').data('url'),
                id = address.data('id'),
                pl = address.data('pl'),
                addressInfo = address.find('.adr'),
                street = addressInfo.find('.street-address'),
                content = address.find('.content'),
                notes = address.find('.notes'),
                editedStreet,
                rejectButton,
                edits;

            if (street.data('parsed')) {
                edits = {
                    street_number: street.find('.street-number').text(),
                    street_prefix: street.find('.street-prefix').text(),
                    street_name: street.find('.street-name').text(),
                    street_type: street.find('.street-type').text(),
                    street_suffix: street.find('.street-suffix').text(),
                    city: addressInfo.find('.locality').text(),
                    state: addressInfo.find('.region').text(),
                    complex_name: addressInfo.find('.complex-name').text(),
                    notes: notes.text()
                };
                editedStreet = street.find('span').map(function () { return $(this).text(); }).get().join(' ');
            } else {
                edits = {
                    edited_street: street.text(),
                    city: addressInfo.find('.locality').text(),
                    state: addressInfo.find('.region').text(),
                    complex_name: addressInfo.find('.complex-name').text(),
                    notes: notes.text()
                };
                editedStreet = street.text();
            }

            if (url) {
                address.loadingOverlay();
                $.post(url, edits, function (data) {
                    $('#messages .message').filter(function () {
                        return $(this).data('address-id') === id;
                    }).remove();
                    if (data.errors) {
                        address.loadingOverlay('remove');
                        $.each(data.errors, function (i, error) {
                            $(ich.message({message: error, tags: "error"})).data('address-id', id).appendTo($('#messages'));
                            $('#messages').messages();
                        });
                    } else {
                        MLT.addressLoading.replaceAddress(data);
                        if (editedStreet !== originalStreet && pl) {
                            MLT.updateParcelMapping('update', false, pl, id, 'street', data.address);
                        }
                    }
                });
            }
        });
    };

    MLT.addAddress = function () {
        var success, bootstrapForm,
            link = $('a[href=#lightbox-add-address]'),
            target = $("#lightbox-add-address"),
            url = target.data('add-address-url');

        success = function (data) {
            var number = addressContainer.find('.address').length;
            if (number < 20) { number = 20; }
            if (data.success) {
                target.find('a[title*="close"]').click();
                MLT.addressLoading.reloadList({num: number}, true);
            } else {
                target.find('> div').html(data.html);
                bootstrapForm();
                $(document).on('keydown.closeAddLightbox', function (event) {
                    if (event.keyCode === 27) {
                        target.find('a[title*="close"]').click();
                    }
                });
            }
        };

        bootstrapForm = function () {
            var form = target.find('form').ajaxForm({
                success: success
            });
        };

        link.click(function () {
            $.get(url, success);
        });

        target.on('click', 'a[title*="close"]', function () {
            var form = target.find('form');
            if (form.length) {
                form.get(0).reset();
            }
            $(document).off('keydown.closeAddLightbox');
        });
    };

    MLT.addressActions = function () {
        var url = addressContainer.data('actions-url');

        $('#addressform .actions .bools .addremove .action-delete').click(function () {
            var number = addressContainer.find('.address').length,
                selectedAddressInput = addressContainer.find('.address .item-select:checked'),
                selectedAddressID = selectedAddressInput.map(function () {
                    return $(this).closest('.address').data('id');
                }).get(),
                selectedAddressPL = selectedAddressInput.map(function () {
                    return $(this).closest('.address').data('pl');
                }).get(),
                options,
                notID;
            if (number < 20) { number = 20; }
            selectedAddressInput.each(function () { $(this).closest('.address').loadingOverlay(); });
            if (bulkSelect.data('selectall')) {
                options = $.extend({}, filters, { aid: selectedAddressID, action: "delete" });
                if (addressContainer.find('.address .item-select').not(':checked').length) {
                    notID = addressContainer.find('.address .item-select').not(':checked').map(function () {
                        return $(this).closest('.address').data('id');
                    }).get();
                    $.extend(options, { notid: notID });
                }
                $.post(url, options, function (data) {
                    selectedAddressInput.each(function () { $(this).closest('.address').loadingOverlay('remove'); });
                    if (data.success) {
                        MLT.addressLoading.reloadList({num: number}, true);
                        if (selectedLayer) {
                            selectedLayer.unselect();
                        }
                        mapinfo.empty().hide();
                        MLT.refreshParcels();
                    }
                });
            } else {
                $.post(url, { aid: selectedAddressID, action: "delete" }, function (data) {
                    selectedAddressInput.each(function () { $(this).closest('.address').loadingOverlay('remove'); });
                    if (data.success) {
                        MLT.addressLoading.reloadList({num: number}, true);
                        $.each(selectedAddressID, function (i, id) {
                            MLT.updateParcelMapping('remove', true, selectedAddressPL, id, true);
                        });
                    }
                });
            }
            return false;
        });

        addressContainer.on('click', '.address .content .controls .action-delete', function () {
            var number = addressContainer.find('.address').length,
                selectedAddress = $(this).closest('.address'),
                selectedAddressID = selectedAddress.data('id'),
                selectedAddressPL = selectedAddress.data('pl');
            selectedAddress.loadingOverlay();
            if (number < 20) { number = 20; }
            $.post(url, { aid: selectedAddressID, action: "delete" }, function (data) {
                selectedAddress.loadingOverlay('remove');
                if (data.success) {
                    MLT.addressLoading.reloadList({num: number}, true);
                    MLT.updateParcelMapping('remove', false, selectedAddressPL, selectedAddressID, true);
                }
            });
            return false;
        });

        $('#addressform .actions .bools .approval button').click(function () {
            var action,
                selectedAddressInput = addressContainer.find('.address .item-select:checked'),
                selectedAddressID = selectedAddressInput.map(function () {
                    return $(this).closest('.address').data('id');
                }).get(),
                selectedAddressPL = selectedAddressInput.map(function () {
                    return $(this).closest('.address').data('pl');
                }).get(),
                options,
                notID,
                removePopup = false,
                number = addressContainer.find('.address').length;
            selectedAddressInput.each(function () { $(this).closest('.address').loadingOverlay(); });
            if (number < 20) { number = 20; }
            if ($(this).hasClass('disabled')) {
                $(ich.message({message: "You don't have permission to perform this action.", tags: "error"})).appendTo($('#messages'));
                $('#messages').messages();
                return false;
            }
            if ($(this).hasClass('action-flag')) {
                action = 'flag';
            }
            if ($(this).hasClass('action-approve')) {
                action = 'approve';
            }
            if ($(this).hasClass('action-reject')) {
                action = 'reject';
                removePopup = true;
            }
            if (bulkSelect.data('selectall')) {
                options = $.extend({}, filters, { aid: selectedAddressID, action: action });
                if (addressContainer.find('.address .item-select').not(':checked').length) {
                    notID = addressContainer.find('.address .item-select').not(':checked').map(function () {
                        return $(this).closest('.address').data('id');
                    }).get();
                    $.extend(options, { notid: notID });
                }
                $.post(url, options, function (data) {
                    selectedAddressInput.each(function () { $(this).closest('.address').loadingOverlay('remove'); });
                    if (data.success) {
                        MLT.addressLoading.replaceAddresses(data, removePopup);
                        if (selectedLayer) {
                            selectedLayer.unselect();
                        }
                        mapinfo.empty().hide();
                        MLT.refreshParcels();
                    }
                });
            } else {
                $.post(url, { aid: selectedAddressID, action: action }, function (data) {
                    selectedAddressInput.each(function () { $(this).closest('.address').loadingOverlay('remove'); });
                    if (data.success) {
                        MLT.addressLoading.replaceAddresses(data, removePopup);
                        if (action === 'flag' || action === 'approve') {
                            $.each(data.addresses, function (i, address) {
                                MLT.updateParcelMapping('update', true, selectedAddressPL, address.id, 'flag-approve', address);
                            });
                        }
                        if (action === 'reject') {
                            $.each(selectedAddressID, function (i, id) {
                                MLT.updateParcelMapping('remove', true, selectedAddressPL, id, true);
                            });
                        }
                    }
                });
            }
            return false;
        });

        addressContainer.on('click', '.address .action-flag', function () {
            var action,
                selectedAddress = $(this).closest('.address'),
                selectedAddressID = selectedAddress.data('id'),
                selectedAddressPL = selectedAddress.data('pl'),
                thisDiv = $(this).closest('.id');
            selectedAddress.loadingOverlay();
            if ($(this).siblings('input[name="flag_for_review"]').attr('disabled') === 'disabled') {
                $(ich.message({message: "You don't have permission to approve this mapping.", tags: "error"})).appendTo($('#messages'));
                $('#messages').messages();
                return false;
            }
            if (thisDiv.hasClass('approved')) {
                action = "flag";
            } else {
                action = "approve";
            }
            $.post(url, { aid: selectedAddressID, action: action }, function (data) {
                selectedAddress.loadingOverlay('remove');
                if (data.success) {
                    MLT.addressLoading.replaceAddresses(data);
                    $.each(data.addresses, function (i, address) {
                        MLT.updateParcelMapping('update', false, selectedAddressPL, selectedAddressID, 'flag-approve', address);
                    });
                }
            });
            return false;
        });

        addressContainer.on('click', '.address .action-reject', function (e) {
            var action = 'reject',
                selectedAddress = $(this).closest('.address'),
                selectedAddressID = selectedAddress.data('id'),
                selectedAddressPL = selectedAddress.data('pl');
            selectedAddress.loadingOverlay();
            $.post(url, { aid: selectedAddressID, action: action }, function (data) {
                selectedAddress.loadingOverlay('remove');
                MLT.addressLoading.replaceAddresses(data, true);
                if (data.success) {
                    MLT.updateParcelMapping('remove', false, selectedAddressPL, selectedAddressID, true);
                }
            });
            e.preventDefault();
        });

        mapinfo.on('click', '.mapped-addresses .action-reject', function (e) {
            var action = 'reject',
                thisMapping = $(this).closest('li'),
                selectedAddressID = thisMapping.data('id'),
                pl = mapinfo.find('.id').text(),
                index;
            thisMapping.loadingOverlay();
            $.post(url, { aid: selectedAddressID, action: action }, function (data) {
                thisMapping.loadingOverlay('remove');
                MLT.addressLoading.replaceAddresses(data, true);
                if (data.success) {
                    MLT.updateParcelMapping('remove', false, pl, selectedAddressID, true);
                }
            });
            e.preventDefault();
        });

        addressContainer.on('click', '.address .action-complex', function (e) {
            var action,
                selectedAddress = $(this).closest('.address'),
                selectedAddressID = selectedAddress.data('id');
            selectedAddress.loadingOverlay();
            if ($(this).hasClass('multiple')) {
                action = 'multi';
            } else if ($(this).hasClass('single')) {
                action = 'single';
            }
            $.post(url, { aid: selectedAddressID, action: action }, function (data) {
                selectedAddress.loadingOverlay('remove');
                MLT.addressLoading.replaceAddresses(data);
            });
            e.preventDefault();
        });

        if (addressContainer.data('trusted') !== 'trusted') {
            $('#addressform .actions .bools .approval .action-approve').addClass('disabled');
        }
    };

    MLT.filtering = function () {
        var typedText,
            localFilters,
            updateFilters,
            textbox = $('#filter_input'),
            url = textbox.data('autocomplete-url'),
            filterList = $('#filter .visual > ul'),
            suggestionList = $('#filter .textual .suggest').hide(),
            refresh = $('#filter .refresh'),
            status = $('#filter .bystatus a'),

            reloadList = function (opts, preserveScroll) {
                if ($('#addresstable').length) {
                    MLT.addressLoading.reloadList(opts, preserveScroll);
                } else if ($('#history').length) {
                    MLT.reloadChangesList(opts, preserveScroll);
                }
            },

            updateSuggestions = function (data) {
                var newSuggestions = ich.filter_suggestion(data);
                textbox.removeClass('loading');
                newSuggestions = newSuggestions.filter(function (index) {
                    var thisField = $(this).find('a').data('field'),
                        thisValue = $(this).find('a').data('value');
                    return !(filterList.find('input[type="checkbox"][name="' + thisField + '_' + thisValue + '"]:checked').length);
                });
                suggestionList.html(newSuggestions);
                if (suggestionList.find('li').length) {
                    suggestionList.show().find('li:first-child a').addClass('selected');
                }
            };

        if ($('#addresstable').length) {
            localFilters = filters;
        } else if ($('#history').length) {
            localFilters = MLT.history.filters;
        }

        updateFilters = function () {
            var currentStatus;
            if (localFilters.status) {
                currentStatus = localFilters.status;
                localFilters = {};
                localFilters.status = currentStatus;
            } else {
                localFilters = {};
            }
            filterList.find('input[id$="filter"]:checked').each(function () {
                var field = $(this).data('field'),
                    value = $(this).data('value');
                if (localFilters[field]) {
                    localFilters[field].push(value);
                } else {
                    localFilters[field] = [value];
                }
            });
            if (filterList.find('input[id$="filter"]:checked').length) {
                $('#filter .visual').addClass('active-filters');
            } else {
                $('#filter .visual').removeClass('active-filters');
            }
            if ($('#addresstable').length) {
                filters = localFilters;
            } else if ($('#history').length) {
                MLT.history.filters = localFilters;
            }
            reloadList();
        };

        textbox.keyup(function () {
            $(this).doTimeout('autocomplete', 250, function () {
                // Updates suggestion-list if typed-text has changed
                if (textbox.val() !== typedText) {
                    typedText = $(this).val();
                    if (typedText.length && typedText.trim() !== '') {
                        textbox.addClass('loading');
                        $.get(url, {q: typedText}, updateSuggestions);
                    } else {
                        suggestionList.empty().hide();
                    }
                }
            });
        }).keydown(function (event) {
            // Prevent default actions on ENTER
            if (event.keyCode === MLT.keycodes.ENTER) {
                event.preventDefault();
            }
            // If the suggestion list is not visible...
            if (!suggestionList.is(':visible')) {
                // ...and if the keydown was a non-meta key other than shift, ctrl, alt, caps, or esc...
                if (!event.metaKey && event.keyCode !== MLT.keycodes.SHIFT && event.keyCode !== MLT.keycodes.CTRL && event.keyCode !== MLT.keycodes.ALT && event.keyCode !== MLT.keycodes.CAPS && event.keyCode !== MLT.keycodes.ESC) {
                    // ...prevent normal TAB function
                    if (event.keyCode === MLT.keycodes.TAB && textbox.val() !== '' && suggestionList.find('li').length) {
                        event.preventDefault();
                    }
                    // ...show the suggestion list
                    suggestionList.show();
                }
            // If the suggestion list is already visible...
            } else {
                var thisFilterName = suggestionList.find('.selected').data('value');
                // UP and DOWN move "active" suggestion
                if (event.keyCode === MLT.keycodes.UP) {
                    event.preventDefault();
                    if (!suggestionList.find('.selected').parent().is(':first-child')) {
                        suggestionList.find('.selected').removeClass('selected').parent().prev().children('a').addClass('selected');
                    }
                }
                if (event.keyCode === MLT.keycodes.DOWN) {
                    event.preventDefault();
                    if (!suggestionList.find('.selected').parent().is(':last-child')) {
                        suggestionList.find('.selected').removeClass('selected').parent().next().children('a').addClass('selected');
                    }
                }
                // ENTER selects the "active" filter suggestion.
                if (event.keyCode === MLT.keycodes.ENTER) {
                    event.preventDefault();
                    if (suggestionList.find('.selected').length) {
                        suggestionList.find('.selected').click();
                    }
                }
                // TAB auto-completes the "active" suggestion if it isn't already completed...
                if (event.keyCode === MLT.keycodes.TAB) {
                    if (thisFilterName && textbox.val().toLowerCase() !== thisFilterName.toString().toLowerCase()) {
                        event.preventDefault();
                        textbox.val(thisFilterName);
                    // ...otherwise, TAB selects the "active" filter suggestion (if exists)
                    } else if (suggestionList.find('.selected').length) {
                        event.preventDefault();
                        suggestionList.find('.selected').click();
                    }
                }
                // RIGHT auto-completes the "active" suggestion if it isn't already completed
                if (event.keyCode === MLT.keycodes.RIGHT) {
                    if (thisFilterName && textbox.val().toLowerCase() !== thisFilterName.toString().toLowerCase() && textbox.get(0).selectionStart === textbox.val().length) {
                        event.preventDefault();
                        textbox.val(thisFilterName);
                    }
                }
                // ESC hides the suggestion list
                if (event.keyCode === MLT.keycodes.ESC) {
                    event.preventDefault();
                    suggestionList.hide();
                }
            }
        }).focus(function () {
            // Resets textbox data-clicked to ``false`` (becomes ``true`` when an autocomplete suggestion is clicked)
            textbox.data('clicked', false);
        // On blur, hides the suggestion list after 150 ms if textbox data-clicked is ``false``
        }).blur(function () {
            function hideList() {
                if (textbox.data('clicked') !== true) {
                    suggestionList.hide();
                    textbox.data('clicked', false);
                }
            }
            window.setTimeout(hideList, 150);
        });

        suggestionList.on({
            // Adds ``.selected`` to suggestion on mouseover, removing ``.selected`` from other suggestions
            mouseover: function () {
                var thisSuggestion = $(this).addClass('selected'),
                    otherSuggestions = thisSuggestion.parent('li').siblings('li').find('a').removeClass('selected');
            },
            // Prevent the suggestion list from being hidden (by textbox blur event) when clicking a suggestion
            mousedown: function () {
                textbox.data('clicked', true);
            },
            click: function (e) {
                e.preventDefault();
                var newFilter,
                    field = $(this).data('field'),
                    value = $(this).data('value'),
                    desc = $(this).data('desc'),
                    name = $(this).data('name');
                if (field && value) {
                    if (filterList.find('input[type="checkbox"][name="' + field + '_' + value + '"]').length) {
                        if (filterList.find('input[type="checkbox"][name="' + field + '_' + value + '"]').not(':checked').length) {
                            filterList.find('input[type="checkbox"][name="' + field + '_' + value + '"]').not(':checked').prop('checked', true);
                            updateFilters();
                        }
                    } else {
                        newFilter = ich.filter_applied({
                            field: field,
                            value: value,
                            desc: desc,
                            name: name
                        });
                        if (newFilter.length) {
                            filterList.append(newFilter);
                            updateFilters();
                        }
                    }
                }

                // Reset the textbox, and reset and hide the suggestion list
                textbox.val(null);
                typedText = null;
                suggestionList.empty().hide();
            }
        }, 'a');

        filterList.on('change', 'input[id$="filter"]', function () {
            updateFilters();
        });

        filterList.on('update-filters', function () {
            updateFilters();
        });

        refresh.click(function (e) {
            e.preventDefault();
            var number = addressContainer.find('.address').length;
            if (number < 20) { number = 20; }
            preserveSelectAll = true;
            reloadList({num: number}, true);
        });

        status.click(function () {
            var thisStatus = $(this).attr('class');
            if (!$(this).closest('.bystatus').hasClass(thisStatus)) {
                if (thisStatus === 'none') {
                    delete localFilters.status;
                } else {
                    localFilters.status = thisStatus;
                }
                $(this).closest('.bystatus').removeClass('approved flagged unmapped none').addClass(thisStatus);
                if ($('#addresstable').length) {
                    filters = localFilters;
                } else if ($('#history').length) {
                    MLT.history.filters = localFilters;
                }
                reloadList();
            }
            $(this).blur();
            return false;
        });
    };

    MLT.selectAll = function () {
        $('#addressform .actions .bulkselect #select_all_none').change(function () {
            if ($(this).is(':checked')) {
                $(this).closest('.bulkselect').data('selectall', true);
                addressContainer.find('.address .item-select').prop('checked', true);
            } else {
                $(this).closest('.bulkselect').data('selectall', false);
                addressContainer.find('.address .item-select').prop('checked', false);
            }
        });
    };

    MLT.mapInfo = function () {
        mapinfo
            .hide()
            .hover(
                function () { mapinfoHover = true; },
                function () {
                    mapinfoHover = false;
                    MLT.hideInfo();
                }
            )
            .click(function (event) {
                if ($(this).hasClass('selected') && !$(event.target).is('.mapit')) {
                    var lat = selectedParcelInfo.latitude,
                        lng = selectedParcelInfo.longitude;
                    MLT.map.panTo(new L.LatLng(lat, lng));
                    if (MLT.map.getZoom() < MIN_PARCEL_ZOOM) {
                        MLT.map.setZoom(MIN_PARCEL_ZOOM);
                    }
                }
            });
    };

    MLT.ajaxPagination = function () {
        addressContainer.scroll(function () {
            $.doTimeout('scroll', 150, function () {
                if ((addressContainer.get(0).scrollHeight - addressContainer.scrollTop() - addressContainer.outerHeight()) <= loadingMessage.outerHeight() && MLT.addressLoading.moreAddresses && !MLT.addressLoading.currentlyLoading) {
                    MLT.addressLoading.addMore();
                }
            });
        });
    };

    MLT.importAddressesLightbox = function () {
        var link = $('a[href=#lightbox-import-addresses]'),
            target = $("#lightbox-import-addresses"),
            url = target.data('import-addresses-url'),
            success = function (data) {
                target.find('> div').html(data.html);
                $(document).on('keydown.closeImportLightbox', function (event) {
                    if (event.keyCode === 27) {
                        target.find('a[title*="close"]').click();
                    }
                });
            };

        link.click(function () {
            $.get(url, success);
        });

        target.on('click', 'a[title*="close"]', function () {
            var form = target.find('form');
            if (form.length) {
                form.get(0).reset();
            }
            $(document).off('keydown.closeImportLightbox');
        });
    };

    MLT.addImportTag = function () {
        addressContainer.on('keydown', '.address .byline .addtag input.tag-input', function (e) {
            if (e.keyCode === MLT.keycodes.ENTER) {
                var input = $(this),
                    tag = input.val(),
                    url = input.data('url'),
                    thisAddress = input.closest('.address');
                thisAddress.loadingOverlay();
                $.post(url, {'tag': tag}, function (data) {
                    thisAddress.loadingOverlay('remove');
                    if (data.success) {
                        MLT.addressLoading.replaceAddress(data);
                    }
                });
            }
        });
    };

    return MLT;

}(MLT || {}, jQuery));
