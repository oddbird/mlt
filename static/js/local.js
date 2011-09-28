/*jslint    browser:    true,
            indent:     4,
            confusion:  true */
/*global    L, ich, jQuery */

var MLT = MLT || {};

(function ($) {

    'use strict';

    var keycodes = {
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
    },

        addressMapping = function () {

            var MIN_PARCEL_ZOOM = 17,
                layer = new L.TileLayer(MLT.tileServerUrl, {attribution: MLT.mapCredits}),
                map = new L.Map('map', {
                    center: new L.LatLng(MLT.mapDefaultLat, MLT.mapDefaultLon),
                    zoom: MLT.mapDefaultZoom,
                    layers: [layer],
                    closePopupOnClick: false
                }),
                mapinfoHover = false,
                mapinfo = $("#mapinfo"),
                mapinfoTimeout = null,
                geojson_url = $('#mapping').data('parcel-geojson-url'),
                geojson = new L.GeoJSON(),
                selectedLayer = null,
                selectedId = null,
                selectedInfo = null,
                selectedParcelInfo,
                sortData = {},
                filters = {},
                addressContainer = $('#addresstable .managelist'),
                loadingURL = addressContainer.data('addresses-url'),
                loadingMessage = addressContainer.find('.load'),
                preserveSelectAll,

                showInfo = function (newInfo, selected) {
                    var mapped_toIDs, i, already_mapped,
                        selectedAddresses = $('#addresstable .address input[id^="select"]:checked');
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
                },

                hideInfo = function () {
                    if (!selectedInfo) {
                        mapinfoTimeout = setTimeout(function () {
                            if (!mapinfoHover) {
                                mapinfo.empty().hide();
                            }
                        }, 100);
                    }
                },

                refreshParcels = function () {
                    var bounds = map.getBounds(),
                        ne = bounds.getNorthEast(),
                        sw = bounds.getSouthWest();

                    if (map.getZoom() >= MIN_PARCEL_ZOOM) {
                        $.getJSON(
                            geojson_url + "?southlat=" + sw.lat + "&northlat=" + ne.lat + "&westlng=" + sw.lng + "&eastlng=" + ne.lng,
                            function (data) {
                                map.removeLayer(geojson);
                                selectedLayer = null;
                                geojson = new L.GeoJSON();

                                geojson.on('featureparse', function (e) {
                                    var id = e.id;
                                    e.layer.info = ich.parcelinfo(e.properties);
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
                                            showInfo(e.layer.info, false);
                                        }
                                    });
                                    e.layer.on('mouseout', function (ev) {
                                        hideInfo();
                                    });
                                    e.layer.on('click', function (ev) {
                                        if (ev.target.selected) {
                                            ev.target.unselect();
                                            showInfo(e.layer.info, false);
                                        } else {
                                            ev.target.select();
                                            showInfo(e.layer.info, true);
                                        }
                                    });
                                });

                                geojson.addGeoJSON(data);
                                map.addLayer(geojson);
                            }
                        );
                    } else {
                        map.removeLayer(geojson);
                    }
                },

                addressPopups = function () {
                    $('#addresstable .managelist .address input[id^="select"]').live('change', function () {
                        var input, mapped_toIDs, i, already_mapped,
                            thisAddress = $(this).closest('.address'),
                            id = thisAddress.data('id'),
                            popupContent = thisAddress.find('.mapkey').html(),
                            lat = thisAddress.data('latitude'),
                            lng = thisAddress.data('longitude'),
                            geolat = thisAddress.data('geocode-latitude'),
                            geolng = thisAddress.data('geocode-longitude'),
                            geoURL = $('#addresstable .managelist').data('geocode-url');
                        if ($(this).is(':checked')) {
                            if (lat && lng) {
                                this.popup = new L.Popup({ autoPan: false });
                                this.popup.setLatLng(new L.LatLng(lat, lng));
                                this.popup.setContent(popupContent);
                                map.addLayer(this.popup);
                                map.panTo(new L.LatLng(lat, lng));
                                if (map.getZoom() < MIN_PARCEL_ZOOM) {
                                    map.setZoom(MIN_PARCEL_ZOOM);
                                }
                            } else {
                                if (geolat && geolng) {
                                    this.popup = new L.Popup({ autoPan: false });
                                    this.popup.setLatLng(new L.LatLng(geolat, geolng));
                                    this.popup.setContent(popupContent);
                                    map.addLayer(this.popup);
                                    $('#map .leaflet-map-pane .leaflet-objects-pane .leaflet-popup-pane .leaflet-popup-content').filter(function (index) {
                                        return $(this).html() === popupContent;
                                    }).closest('.leaflet-popup').addClass('geocoded');
                                    map.panTo(new L.LatLng(geolat, geolng));
                                    if (map.getZoom() < MIN_PARCEL_ZOOM) {
                                        map.setZoom(MIN_PARCEL_ZOOM);
                                    }
                                } else {
                                    if (geoURL && id) {
                                        thisAddress.loadingOverlay();
                                        $.get(geoURL, {id: id}, function (data) {
                                            var byline, web_ui, updatedAddress, newlat, newlng,
                                                index = thisAddress.find('.mapkey').html();

                                            if (data.address.parcel) {
                                                newlat = data.address.parcel.latitude;
                                                newlng = data.address.parcel.longitude;
                                            }
                                            if (data.address.latitude && data.address.longitude) {
                                                geolat = data.address.latitude;
                                                geolng = data.address.longitude;
                                            }
                                            if (data.address.import_source || data.address.mapped_by) { byline = true; }
                                            if (data.address.import_source === 'web-ui') { web_ui = true; }

                                            updatedAddress = ich.address({
                                                id: id,
                                                pl: data.address.pl,
                                                checked: true,
                                                latitude: newlat,
                                                longitude: newlng,
                                                geolat: geolat,
                                                geolng: geolng,
                                                index: index,
                                                edit_url: data.address.edit_url,
                                                street: data.address.street,
                                                street_is_parsed: data.address.street_is_parsed,
                                                street_number: data.address.street_number,
                                                street_prefix: data.address.street_prefix,
                                                street_name: data.address.street_name,
                                                street_type: data.address.street_type,
                                                street_suffix: data.address.street_suffix,
                                                city: data.address.city,
                                                state: data.address.state,
                                                complex_name: data.address.complex_name,
                                                needs_review: data.address.needs_review,
                                                multi_units: data.address.multi_units,
                                                notes: data.address.notes,
                                                byline: byline,
                                                import_source: data.address.import_source,
                                                web_ui: web_ui,
                                                imported_by: data.address.imported_by,
                                                import_timestamp: data.address.import_timestamp,
                                                mapped_by: data.address.mapped_by,
                                                mapped_timestamp: data.address.mapped_timestamp
                                            });

                                            thisAddress.replaceWith(updatedAddress);
                                            updatedAddress.find('.details').html5accordion();

                                            input = updatedAddress.find('input[id^="select"]').get(0);
                                            input.popup = new L.Popup({ autoPan: false });
                                            input.popup.setLatLng(new L.LatLng(geolat, geolng));
                                            input.popup.setContent(popupContent);
                                            map.addLayer(input.popup);
                                            map.panTo(new L.LatLng(geolat, geolng));
                                            if (map.getZoom() < MIN_PARCEL_ZOOM) {
                                                map.setZoom(MIN_PARCEL_ZOOM);
                                            }
                                            $('#map .leaflet-map-pane .leaflet-objects-pane .leaflet-popup-pane .leaflet-popup-content').filter(function (index) {
                                                return $(this).html() === popupContent;
                                            }).closest('.leaflet-popup').addClass('geocoded');
                                            if (addressContainer.data('trusted') !== 'trusted') {
                                                addressContainer.find('.address input[name="flag_for_review"]:checked').attr('disabled', 'disabled');
                                            }
                                        });
                                    }
                                }
                            }
                        } else {
                            if (this.popup) {
                                map.removeLayer(this.popup);
                            }
                        }

                        // Only show `map to selected` button if an address is selected
                        // and isn't already mapped to the selected parcel
                        mapped_toIDs = $('#mapinfo .mapped-addresses ul li').map(function () {
                            return $(this).data('id');
                        }).get();
                        $('#addresstable .address input[id^="select"]:checked').each(function () {
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
                        if ($('#addresstable .address input[id^="select"]:checked').length && already_mapped === false) {
                            $('#mapinfo .mapit').show();
                        } else {
                            $('#mapinfo .mapit').hide();
                        }
                    });
                },

                mapAddress = function () {
                    var url = $('#mapping').data('associate-url');
                    $('#mapinfo .mapit').live('click', function () {
                        var options,
                            notID,
                            selectedAddressID = $('#addresstable .address input[id^="select"]:checked').map(function () {
                                return $(this).closest('.address').data('id');
                            }).get(),
                            pl = selectedParcelInfo.pl,
                            lat = selectedParcelInfo.latitude,
                            lng = selectedParcelInfo.longitude,
                            success = function (data) {
                                $.each(data.mapped_to, function (i, address) {
                                    var byline, web_ui, updatedAddress,
                                        id = address.id,
                                        thisAddress = $('#addresstable .address[data-id="' + id + '"]'),
                                        index = thisAddress.find('.mapkey').html();

                                    if (address.import_source || address.mapped_by) { byline = true; }
                                    if (address.import_source === 'web-ui') { web_ui = true; }

                                    if (thisAddress.length) {
                                        updatedAddress = ich.address({
                                            id: id,
                                            pl: address.pl,
                                            latitude: lat,
                                            longitude: lng,
                                            index: index,
                                            edit_url: address.edit_url,
                                            street: address.street,
                                            street_is_parsed: address.street_is_parsed,
                                            street_number: address.street_number,
                                            street_prefix: address.street_prefix,
                                            street_name: address.street_name,
                                            street_type: address.street_type,
                                            street_suffix: address.street_suffix,
                                            city: address.city,
                                            state: address.state,
                                            complex_name: address.complex_name,
                                            needs_review: address.needs_review,
                                            multi_units: address.multi_units,
                                            notes: address.notes,
                                            byline: byline,
                                            import_source: address.import_source,
                                            web_ui: web_ui,
                                            imported_by: address.imported_by,
                                            import_timestamp: address.import_timestamp,
                                            mapped_by: address.mapped_by,
                                            mapped_timestamp: address.mapped_timestamp
                                        });

                                        thisAddress.find('input[id^="select"]').click();
                                        thisAddress.replaceWith(updatedAddress);
                                        updatedAddress.find('.details').html5accordion();
                                    }
                                });

                                var updatedParcelInfo = ich.parcelinfo(data);
                                $('#mapinfo').removeClass('selected').html(updatedParcelInfo);
                                $('#mapinfo .mapit').hide();
                                selectedLayer.info = updatedParcelInfo;
                                selectedLayer.unselect();
                                if ($('#addressform .actions .bulkselect').data('selectall')) {
                                    $('#addressform .actions .bulkselect').data('selectall', false).find('#select_all_none').prop('checked', false);
                                }
                                if (addressContainer.data('trusted') !== 'trusted') {
                                    addressContainer.find('.address input[name="flag_for_review"]:checked').attr('disabled', 'disabled');
                                }
                            };

                        if ($('#addressform .actions .bulkselect').data('selectall')) {
                            options = $.extend(filters, { maptopl: pl, aid: selectedAddressID });
                            if (addressContainer.find('.address input[id^="select"]').not(':checked').length) {
                                notID = addressContainer.find('.address input[id^="select"]').not(':checked').map(function () {
                                    return $(this).closest('.address').data('id');
                                }).get();
                                options = $.extend(options, { notid: notID });
                            }
                            $.post(url, options, success);
                        } else {
                            $.post(url, { maptopl: pl, aid: selectedAddressID }, success);
                        }
                    });
                },

                initializeMap = function () {
                    map.on('moveend', function () {
                        refreshParcels();
                    });

                    MLT.map = map;
                },

                addressLoading = {
                    moreAddresses: true,
                    currentlyLoading: false,
                    scroll: false,
                    newAddresses: function (data) {
                        if (data.addresses.length) {
                            $.each(data.addresses, function (i, address) {
                                var byline, web_ui, lat, lng, geolat, geolng, addressHTML;

                                if (address.parcel) {
                                    lat = address.parcel.latitude;
                                    lng = address.parcel.longitude;
                                }
                                if (address.latitude && address.longitude && !lat && !lng) {
                                    geolat = address.latitude;
                                    geolng = address.longitude;
                                }
                                if (address.import_source || address.mapped_by) { byline = true; }
                                if (address.import_source === 'web-ui') { web_ui = true; }

                                addressHTML = ich.address({
                                    id: address.id,
                                    pl: address.pl,
                                    latitude: lat,
                                    longitude: lng,
                                    geolat: geolat,
                                    geolng: geolng,
                                    index: address.index,
                                    edit_url: address.edit_url,
                                    street: address.street,
                                    street_is_parsed: address.street_is_parsed,
                                    street_number: address.street_number,
                                    street_prefix: address.street_prefix,
                                    street_name: address.street_name,
                                    street_type: address.street_type,
                                    street_suffix: address.street_suffix,
                                    city: address.city,
                                    state: address.state,
                                    complex_name: address.complex_name,
                                    needs_review: address.needs_review,
                                    multi_units: address.multi_units,
                                    notes: address.notes,
                                    byline: byline,
                                    import_source: address.import_source,
                                    web_ui: web_ui,
                                    imported_by: address.imported_by,
                                    import_timestamp: address.import_timestamp,
                                    mapped_by: address.mapped_by,
                                    mapped_timestamp: address.mapped_timestamp
                                });

                                loadingMessage.before(addressHTML).css('opacity', 0);
                                addressHTML.find('.details').html5accordion();
                            });
                            loadingMessage.find('p').html('loading addresses...');
                            addressLoading.moreAddresses = true;
                            if (addressLoading.scroll) {
                                addressContainer.scrollTop(addressLoading.scroll);
                            }
                            if ($('#addressform .actions .bulkselect').data('selectall')) {
                                addressContainer.find('.address input[id^="select"]').prop('checked', true);
                            }
                        } else {
                            loadingMessage.find('p').html('no more addresses');
                            addressLoading.moreAddresses = false;
                        }
                        if (data.count || data.count === 0) {
                            $('#addressform .actions .listlength').html(data.count);
                        }
                        if (addressContainer.data('trusted') !== 'trusted') {
                            addressContainer.find('.address input[name="flag_for_review"]:checked').attr('disabled', 'disabled');
                        }
                        addressLoading.currentlyLoading = false;
                        addressLoading.scroll = false;
                    },
                    replaceAddress: function (data) {
                        if (data.success) {
                            var byline, web_ui, lat, lng, geolat, geolng, updatedAddress,
                                address = data.address,
                                id = address.id,
                                thisAddress = addressContainer.find('.address[data-id="' + id + '"]'),
                                index = thisAddress.find('.mapkey').text();

                            if (address.pl) {
                                lat = address.latitude;
                                lng = address.longitude;
                            } else {
                                geolat = address.latitude;
                                geolng = address.longitude;
                            }
                            if (address.import_source || address.mapped_by) { byline = true; }
                            if (address.import_source === 'web-ui') { web_ui = true; }

                            updatedAddress = ich.address({
                                id: id,
                                pl: address.pl,
                                latitude: lat,
                                longitude: lng,
                                geolat: geolat,
                                geolng: geolng,
                                index: index,
                                edit_url: address.edit_url,
                                street: address.street,
                                street_is_parsed: address.street_is_parsed,
                                street_number: address.street_number,
                                street_prefix: address.street_prefix,
                                street_name: address.street_name,
                                street_type: address.street_type,
                                street_suffix: address.street_suffix,
                                city: address.city,
                                state: address.state,
                                complex_name: address.complex_name,
                                needs_review: address.needs_review,
                                multi_units: address.multi_units,
                                notes: address.notes,
                                byline: byline,
                                import_source: address.import_source,
                                web_ui: web_ui,
                                imported_by: address.imported_by,
                                import_timestamp: address.import_timestamp,
                                mapped_by: address.mapped_by,
                                mapped_timestamp: address.mapped_timestamp
                            });

                            thisAddress.replaceWith(updatedAddress);
                            updatedAddress.find('.details').html5accordion();
                            if ($('#addressform .actions .bulkselect').data('selectall')) {
                                $('#addressform .actions .bulkselect').data('selectall', false).find('#select_all_none').prop('checked', false);
                            }
                            if (addressContainer.data('trusted') !== 'trusted') {
                                addressContainer.find('.address input[name="flag_for_review"]:checked').attr('disabled', 'disabled');
                            }
                        }
                    },
                    replaceAddresses: function (data) {
                        if (data.addresses.length) {
                            addressContainer.find('.address input[id^="select"]:checked').click();
                            $.each(data.addresses, function (i, address) {
                                var byline, web_ui, lat, lng, geolat, geolng, updatedAddress,
                                    id = address.id,
                                    thisAddress = addressContainer.find('.address[data-id="' + id + '"]'),
                                    index = thisAddress.find('.mapkey').text();

                                if (address.pl) {
                                    lat = address.latitude;
                                    lng = address.longitude;
                                } else {
                                    geolat = address.latitude;
                                    geolng = address.longitude;
                                }
                                if (address.import_source || address.mapped_by) { byline = true; }
                                if (address.import_source === 'web-ui') { web_ui = true; }

                                updatedAddress = ich.address({
                                    id: id,
                                    pl: address.pl,
                                    latitude: lat,
                                    longitude: lng,
                                    geolat: geolat,
                                    geolng: geolng,
                                    index: index,
                                    edit_url: address.edit_url,
                                    street: address.street,
                                    street_is_parsed: address.street_is_parsed,
                                    street_number: address.street_number,
                                    street_prefix: address.street_prefix,
                                    street_name: address.street_name,
                                    street_type: address.street_type,
                                    street_suffix: address.street_suffix,
                                    city: address.city,
                                    state: address.state,
                                    complex_name: address.complex_name,
                                    needs_review: address.needs_review,
                                    multi_units: address.multi_units,
                                    notes: address.notes,
                                    byline: byline,
                                    import_source: address.import_source,
                                    web_ui: web_ui,
                                    imported_by: address.imported_by,
                                    import_timestamp: address.import_timestamp,
                                    mapped_by: address.mapped_by,
                                    mapped_timestamp: address.mapped_timestamp
                                });

                                thisAddress.replaceWith(updatedAddress);
                                updatedAddress.find('.details').html5accordion();
                            });
                            if ($('#addressform .actions .bulkselect').data('selectall')) {
                                $('#addressform .actions .bulkselect').data('selectall', false).find('#select_all_none').prop('checked', false);
                            }
                            if (addressContainer.data('trusted') !== 'trusted') {
                                addressContainer.find('.address input[name="flag_for_review"]:checked').attr('disabled', 'disabled');
                            }
                        }
                    },
                    // @@@ if this returns with errors, subsequent ajax calls will be prevented unless currentlyLoading is set to `false`
                    reloadList: function (opts, preserveScroll) {
                        var defaults = {
                            sort: sortData,
                            start: 1,
                            num: 20,
                            count: true
                        },
                            options = $.extend({}, defaults, filters, opts);
                        if (preserveScroll) {
                            addressLoading.scroll = addressContainer.scrollTop();
                        }
                        addressContainer.find('.address input[id^="select"]:checked').click();
                        if (!preserveSelectAll) {
                            $('#addressform .actions .bulkselect').data('selectall', false).find('#select_all_none').prop('checked', false);
                        }
                        preserveSelectAll = false;
                        loadingMessage.css('opacity', 1).find('p').html('loading addresses...');
                        addressContainer.find('.address').remove();
                        if (loadingURL && sortData) {
                            addressLoading.currentlyLoading = true;
                            $.get(loadingURL, options, addressLoading.newAddresses);
                        }
                    },
                    addMore: function (opts) {
                        var count = addressContainer.find('.address').length + 1,
                            defaults = {
                                sort: sortData,
                                start: count
                            },
                            options = $.extend({}, defaults, filters, opts);
                        if (loadingURL && sortData) {
                            loadingMessage.animate({opacity: 1}, 'fast');
                            addressLoading.currentlyLoading = true;
                            // @@@ if this returns with errors, subsequent ajax calls will be prevented unless currentlyLoading is set to `false`
                            $.get(loadingURL, options, addressLoading.newAddresses);
                        }
                    }
                },

                addressSorting = function () {
                    var list = $('#addressform .actions .listordering > ul'),
                        items = list.find('li[class^="by"]'),
                        fields = items.find('.field'),
                        directions = items.find('.dir'),
                        sortList = function () {
                            $('#addressform .actions .listordering > ul > li.none').insertAfter($('#addressform .actions .listordering > ul > li:not(.none)').last());
                        },
                        updateSortData = function () {
                            sortData = list.find('li[class^="by"]').not('.none').map(function () {
                                var thisName = $(this).find('.field').data('field');
                                if ($(this).find('.dir').hasClass('desc')) {
                                    thisName = '-' + thisName;
                                }
                                return thisName;
                            }).get();
                            preserveSelectAll = true;
                            addressLoading.reloadList();
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
                },

                addressDetails = function () {
                    var info = $('#addresstable .managelist [id^="address-id"] .details .summary');
                    info.live('click', function () {
                        if ($(this).closest('.details').hasClass('open')) {
                            $(this).closest('.address').addClass('expanded');
                        } else {
                            $(this).closest('.address').removeClass('expanded');
                        }
                    });
                },

                addressSelect = function () {
                    $('#addresstable .managelist .address .content').live('click', function (event) {
                        if (!$(event.target).is('button, a, label, input, .summary, .adr, .street-address, .street-number, .street-prefix, .street-name, .street-type, .street-suffix, .locality, .region, .mapkey, [contenteditable]')) {
                            $(this).closest('.address').find('input[id^="select"]').click();
                        }
                    });
                },

                addressZoom = function () {
                    $('#addresstable .managelist .address .content .mapkey').live('click', function (event) {
                        var lat, lng,
                            thisAddress = $(this).closest('.address');
                        if (thisAddress.find('input[name="select"]:checked').length) {
                            lat = thisAddress.data('latitude') || thisAddress.data('geocode-latitude');
                            lng = thisAddress.data('longitude') || thisAddress.data('geocode-longitude');
                            if (lat && lng) {
                                map.panTo(new L.LatLng(lat, lng));
                                if (map.getZoom() < MIN_PARCEL_ZOOM) {
                                    map.setZoom(MIN_PARCEL_ZOOM);
                                }
                            }
                        } else {
                            thisAddress.find('input[name="select"]').click();
                        }
                    });
                },

                exportAddresses = function () {
                    var form = $('#export-address-form'),
                        url = form.attr('action');

                    form.submit(function () {
                        form.find('.export-filter').remove();
                        $.each(filters, function (field, filter) {
                            if (field === 'status') {
                                var input = ich.export_filter({
                                    field: field,
                                    filter: filter
                                });
                                form.append(input);
                            } else {
                                for (var i = 0; i < filter.length; i = i + 1) {
                                    var input = ich.export_filter({
                                        field: field,
                                        filter: filter[i]
                                    });
                                    form.append(input);
                                }
                            }
                        });
                    });
                },

                editAddress = function () {
                    addressContainer.delegate('.action-edit', 'click', function (e) {
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
                        } else {
                            street.attr('contenteditable', true).data('original', street.text());
                        }
                        button.removeClass('action-edit').addClass('action-cancel').attr('title', 'cancel').html('cancel');
                        notes.attr('contenteditable', true).data('original', notes.text());
                    });

                    addressContainer.delegate('.action-cancel', 'click', function (e) {
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

                    addressContainer.delegate('.savechanges', 'click', function () {
                        var button = $(this),
                            address = button.closest('.address'),
                            url = address.find('.action-cancel').data('url'),
                            addressInfo = address.find('.adr'),
                            street = addressInfo.find('.street-address'),
                            content = address.find('.content'),
                            notes = address.find('.notes'),
                            data;

                        if (street.data('parsed')) {
                            data = {
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
                        } else {
                            data = {
                                edited_street: street.text(),
                                city: addressInfo.find('.locality').text(),
                                state: addressInfo.find('.region').text(),
                                complex_name: addressInfo.find('.complex-name').text(),
                                notes: notes.text()
                            };
                        }

                        if (url) {
                            address.loadingOverlay();
                            $.post(url, data, addressLoading.replaceAddress);
                        }
                    });
                },

                addAddress = function () {
                    var success, bootstrapForm,
                        link = $('a[href=#lightbox-add-address]'),
                        target = $("#lightbox-add-address"),
                        url = target.data('add-address-url');

                    success = function (data) {
                        var number = addressContainer.find('.address').length;
                        if (number < 20) { number = 20; }
                        if (data.success) {
                            target.find('a[title*="close"]').click();
                            addressLoading.reloadList({num: number}, true);
                        } else {
                            target.find('> div').html(data.html);
                            bootstrapForm();
                            $(document).bind('keydown.closeAddLightbox', function (event) {
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

                    target.find('a[title*="close"]').live('click', function () {
                        var form = target.find('form');
                        if (form.length) {
                            form.get(0).reset();
                        }
                        $(document).unbind('keydown.closeAddLightbox');
                    });
                },

                addressActions = function () {
                    var url = addressContainer.data('actions-url');

                    $('#addressform .actions .bools .addremove .delete_selected').live('click', function () {
                        var number = addressContainer.find('.address').length,
                            selectedAddressID = addressContainer.find('.address input[id^="select"]:checked').map(function () {
                                return $(this).closest('.address').data('id');
                            }).get(),
                            options,
                            notID;
                        if (number < 20) { number = 20; }
                        if ($('#addressform .actions .bulkselect').data('selectall')) {
                            options = $.extend(filters, { aid: selectedAddressID, action: "delete" });
                            if (addressContainer.find('.address input[id^="select"]').not(':checked').length) {
                                notID = addressContainer.find('.address input[id^="select"]').not(':checked').map(function () {
                                    return $(this).closest('.address').data('id');
                                }).get();
                                options = $.extend(options, { notid: notID });
                            }
                            $.post(url, options, function (data) {
                                if (data.success) {
                                    addressLoading.reloadList({num: number}, true);
                                }
                            });
                        } else {
                            $.post(url, { aid: selectedAddressID, action: "delete" }, function (data) {
                                if (data.success) {
                                    addressLoading.reloadList({num: number}, true);
                                }
                            });
                        }
                        return false;
                    });

                    addressContainer.find('.address .content .controls .action-delete').live('click', function () {
                        var number = addressContainer.find('.address').length,
                            selectedAddressID = $(this).closest('.address').data('id');
                        if (number < 20) { number = 20; }
                        $.post(url, { aid: selectedAddressID, action: "delete" }, function (data) {
                            if (data.success) {
                                addressLoading.reloadList({num: number}, true);
                            }
                        });
                        return false;
                    });

                    $('#addressform .actions .bools .approval button').click(function () {
                        var action,
                            selectedAddressID = addressContainer.find('.address input[id^="select"]:checked').map(function () {
                                return $(this).closest('.address').data('id');
                            }).get(),
                            options,
                            notID,
                            number = addressContainer.find('.address').length;
                        if (number < 20) { number = 20; }
                        if ($(this).hasClass('disabled')) {
                            $(ich.message({message: "You don't have permission to perform this action.", tags: "error"})).appendTo($('#messages'));
                            $('#messages').messages();
                            return false;
                        }
                        if ($(this).hasClass('action-flag')) {
                            action = "flag";
                        }
                        if ($(this).hasClass('approve')) {
                            action = "approve";
                        }
                        if ($('#addressform .actions .bulkselect').data('selectall')) {
                            options = $.extend(filters, { aid: selectedAddressID, action: action });
                            if (addressContainer.find('.address input[id^="select"]').not(':checked').length) {
                                notID = addressContainer.find('.address input[id^="select"]').not(':checked').map(function () {
                                    return $(this).closest('.address').data('id');
                                }).get();
                                options = $.extend(options, { notid: notID });
                            }
                            $.post(url, options, addressLoading.replaceAddresses);
                        } else {
                            $.post(url, { aid: selectedAddressID, action: action }, addressLoading.replaceAddresses);
                        }
                        return false;
                    });

                    addressContainer.find('.address label.action-flag[for^="flag_for_review"]').live('click', function () {
                        var action,
                            selectedAddressID = $(this).closest('.address').data('id'),
                            thisDiv = $(this).closest('.id');
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
                        $.post(url, { aid: selectedAddressID, action: action }, addressLoading.replaceAddresses);
                        return false;
                    });

                    if (addressContainer.data('trusted') !== 'trusted') {
                        $('#addressform .actions .bools .approval .approve').addClass('disabled');
                    }
                },

                filtering = function () {
                    var typedText,
                        textbox = $('#filter_input'),
                        url = textbox.data('autocomplete-url'),
                        filterList = $('#filter .visual > ul'),
                        suggestionList = $('#filter .textual .suggest').hide(),
                        refresh = $('#filter .refresh'),
                        status = $('#filter .bystatus a'),

                        updateSuggestions = function (data) {
                            var newSuggestions = ich.filter_suggestion(data);
                            newSuggestions = newSuggestions.filter(function (index) {
                                var thisSuggestion = $(this).find('a').data('value');
                                return !(filterList.find('input[id$="filter"][data-value="' + thisSuggestion + '"]:checked').length);
                            });
                            if (newSuggestions.length) {
                                suggestionList.html(newSuggestions).show().find('li:first-child a').addClass('selected');
                            }
                        },

                        updateFilters = function () {
                            var currentStatus;
                            if (filters.status) {
                                currentStatus = filters.status;
                                filters = {};
                                filters.status = currentStatus;
                            } else {
                                filters = {};
                            }
                            filterList.find('input[id$="filter"]:checked').each(function () {
                                var field = $(this).data('field'),
                                    value = $(this).data('value');
                                if (filters[field]) {
                                    filters[field].push(value);
                                } else {
                                    filters[field] = [value];
                                }
                            });
                            if (filterList.find('input[id$="filter"]:checked').length) {
                                $('#filter .visual').addClass('active-filters');
                            } else {
                                $('#filter .visual').removeClass('active-filters');
                            }
                            addressLoading.reloadList();
                        };

                    textbox.keyup(function () {
                        $(this).doTimeout(300, function () {
                            // Updates suggestion-list if typed-text has changed
                            if ($(this).val() !== typedText) {
                                typedText = $(this).val();
                                if (typedText.length) {
                                    $.get(url, {q: typedText}, updateSuggestions);
                                } else {
                                    suggestionList.empty().hide();
                                }
                            }
                        });
                    }).keydown(function (event) {
                        // If the suggestion list is not visible...
                        if (!suggestionList.is(':visible')) {
                            // ...and if the keydown was a non-meta key other than shift, ctrl, alt, caps, or esc...
                            if (!event.metaKey && event.keyCode !== keycodes.SHIFT && event.keyCode !== keycodes.CTRL && event.keyCode !== keycodes.ALT && event.keyCode !== keycodes.CAPS && event.keyCode !== keycodes.ESC) {
                                // ...prevent normal TAB function
                                if (event.keyCode === keycodes.TAB && textbox.val() !== '') {
                                    event.preventDefault();
                                }
                                // ...show the suggestion list
                                suggestionList.show();
                            }
                        // If the suggestion list is already visible...
                        } else {
                            var thisFilterName = suggestionList.find('.selected').data('value');
                            // UP and DOWN move "active" suggestion
                            if (event.keyCode === keycodes.UP) {
                                event.preventDefault();
                                if (!suggestionList.find('.selected').parent().is(':first-child')) {
                                    suggestionList.find('.selected').removeClass('selected').parent().prev().children('a').addClass('selected');
                                }
                                return false;
                            }
                            if (event.keyCode === keycodes.DOWN) {
                                event.preventDefault();
                                if (!suggestionList.find('.selected').parent().is(':last-child')) {
                                    suggestionList.find('.selected').removeClass('selected').parent().next().children('a').addClass('selected');
                                }
                                return false;
                            }
                            // ENTER selects the "active" filter suggestion.
                            if (event.keyCode === keycodes.ENTER) {
                                event.preventDefault();
                                if (suggestionList.find('.selected').length) {
                                    suggestionList.find('.selected').click();
                                }
                                return false;
                            }
                            // TAB auto-completes the "active" suggestion if it isn't already completed...
                            if (event.keyCode === keycodes.TAB) {
                                if (thisFilterName && textbox.val().toLowerCase() !== thisFilterName.toLowerCase()) {
                                    event.preventDefault();
                                    textbox.val(thisFilterName);
                                    return false;
                                // ...otherwise, TAB selects the "active" filter suggestion (if exists)
                                } else {
                                    if (suggestionList.find('.selected').length) {
                                        event.preventDefault();
                                        suggestionList.find('.selected').click();
                                        return false;
                                    }
                                }
                            }
                            // RIGHT auto-completes the "active" suggestion if it isn't already completed
                            if (event.keyCode === keycodes.RIGHT) {
                                if (thisFilterName && textbox.val().toLowerCase() !== thisFilterName.toLowerCase()) {
                                    event.preventDefault();
                                    textbox.val(thisFilterName);
                                    return false;
                                }
                            }
                            // ESC hides the suggestion list
                            if (event.keyCode === keycodes.ESC) {
                                event.preventDefault();
                                suggestionList.hide();
                                return false;
                            }
                            return true;
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

                    suggestionList.find('a').live({
                        // Adds ``.selected`` to suggestion on mouseover, removing ``.selected`` from other suggestions
                        mouseover: function () {
                            var thisSuggestion = $(this).addClass('selected'),
                                otherSuggestions = thisSuggestion.parent('li').siblings('li').find('a').removeClass('selected');
                        },
                        // Prevent the suggestion list from being hidden (by textbox blur event) when clicking a suggestion
                        mousedown: function () {
                            textbox.data('clicked', true);
                        },
                        click: function () {
                            var newFilter,
                                field = $(this).data('field'),
                                value = $(this).data('value');
                            if (field && value) {
                                if (filterList.find('input[type="checkbox"][name="' + value + '"]').length) {
                                    if (filterList.find('input[type="checkbox"][name="' + value + '"]').not(':checked').length) {
                                        filterList.find('input[type="checkbox"][name="' + value + '"]').not(':checked').prop('checked', true);
                                        updateFilters();
                                    }
                                } else {
                                    newFilter = ich.filter_applied({
                                        field: field,
                                        value: value
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
                            return false;
                        }
                    });

                    filterList.find('input[id$="filter"]').live('change', function () {
                        updateFilters();
                    });

                    refresh.click(function () {
                        var number = addressContainer.find('.address').length;
                        if (number < 20) { number = 20; }
                        preserveSelectAll = true;
                        addressLoading.reloadList({num: number}, true);
                        return false;
                    });

                    status.click(function () {
                        var thisStatus = $(this).attr('class');
                        if (!$(this).closest('.bystatus').hasClass(thisStatus)) {
                            if (thisStatus === 'none') {
                                delete filters.status;
                            } else {
                                filters.status = thisStatus;
                            }
                            $(this).closest('.bystatus').removeClass('approved flagged unmapped none').addClass(thisStatus);
                            addressLoading.reloadList();
                        }
                        $(this).blur();
                        return false;
                    });
                },

                selectAll = function () {
                    $('#addressform .actions .bulkselect #select_all_none').change(function () {
                        if ($(this).is(':checked')) {
                            $(this).closest('.bulkselect').data('selectall', true);
                            addressContainer.find('.address input[id^="select"]').prop('checked', true);
                        } else {
                            $(this).closest('.bulkselect').data('selectall', false);
                            addressContainer.find('.address input[id^="select"]').prop('checked', false);
                        }
                    });
                };

            mapinfo.hide().hover(
                function () { mapinfoHover = true; },
                function () {
                    mapinfoHover = false;
                    hideInfo();
                }
            ).click(function (event) {
                if ($(this).hasClass('selected') && !$(event.target).is('.mapit')) {
                    var lat = selectedParcelInfo.latitude,
                        lng = selectedParcelInfo.longitude;
                    map.panTo(new L.LatLng(lat, lng));
                    if (map.getZoom() < MIN_PARCEL_ZOOM) {
                        map.setZoom(MIN_PARCEL_ZOOM);
                    }
                }
            });

            addressContainer.scroll(function () {
                $.doTimeout('scroll', 150, function () {
                    if ((addressContainer.get(0).scrollHeight - addressContainer.scrollTop() - addressContainer.outerHeight()) <= loadingMessage.outerHeight() && addressLoading.moreAddresses && !addressLoading.currentlyLoading) {
                        addressLoading.addMore();
                    }
                });
            });

            initializeMap();
            addressPopups();
            mapAddress();
            addressSorting();
            addressDetails();
            addressSelect();
            addressZoom();
            exportAddresses();
            editAddress();
            addAddress();
            addressActions();
            filtering();
            selectAll();
        },

        addressListHeight = function () {
            var headerHeight = $('header[role="banner"]').outerHeight(),
                actionsHeight = $('#addressform').outerHeight(),
                addressListHeight,
                updateHeight = function () {
                    addressListHeight = $(window).height() - headerHeight - actionsHeight;
                    $('.managelist').css('height', addressListHeight.toString() + 'px');
                };
            updateHeight();
            $(window).resize(function () {
                $.doTimeout(250, function () {
                    updateHeight();
                });
            });
        },

        importAddressesLightbox = function () {
            var link = $('a[href=#lightbox-import-addresses]'),
                target = $("#lightbox-import-addresses"),
                url = target.data('import-addresses-url'),
                success = function (data) {
                    target.find('> div').html(data.html);
                    $(document).bind('keydown.closeImportLightbox', function (event) {
                        if (event.keyCode === 27) {
                            target.find('a[title*="close"]').click();
                        }
                    });
                };

            link.click(function () {
                $.get(url, success);
            });

            target.find('a[title*="close"]').live('click', function () {
                var form = target.find('form');
                if (form.length) {
                    form.get(0).reset();
                }
                $(document).unbind('keydown.closeImportLightbox');
            });
        };

    $(function () {
        $('#hcard-client-name .email').defuscate();
        $('input[placeholder], textarea[placeholder]').placeholder();
        $('.details:not(html)').html5accordion();
        $('#messages').messages({
            handleAjax: true,
            closeLink: '.message'
        });
        addressListHeight();
        $('#addresstable .managelist .address .content .details .summary').live('click', function () {
            $(this).blur();
        });
        if ($('#map').length) {
            addressMapping();
        }
        importAddressesLightbox();
    });

}(jQuery));
