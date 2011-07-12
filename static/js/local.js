var MLT = MLT || {};

(function($) {

    var mapping = function() {

        var MIN_PARCEL_ZOOM = 17,
        layer = new L.TileLayer(
            MLT.tileServerUrl, {attribution: MLT.mapCredits}),
        map = new L.Map('map', {
            center: new L.LatLng(MLT.mapDefaultLat, MLT.mapDefaultLon),
            zoom: MLT.mapDefaultZoom,
            layers: [layer],
            closePopupOnClick: false
        }),
        mapinfoHover = false,
        mapinfo = $("#mapinfo").hide().hover(
            function() { mapinfoHover = true; },
            function() {
                mapinfoHover = false;
                hideInfo();
            }
        ).click(function(event) {
            if ($(this).hasClass('selected') && !$(event.target).is('.mapit')) {
                var lat = selectedParcelInfo.latitude,
                lng = selectedParcelInfo.longitude;
                map.panTo(new L.LatLng(lat, lng));
                if (map.getZoom() < MIN_PARCEL_ZOOM) {
                    map.setZoom(MIN_PARCEL_ZOOM);
                }
            }
        }),
        mapinfoTimeout = null,
        geojson_url = $('#mapping').data('parcel-geojson-url'),
        geojson = new L.GeoJSON(),
        selectedLayer = null,
        selectedId = null,
        selectedInfo = null,
        selectedParcelInfo,

        initializeMap = function() {
            map.on(
                'moveend',
                function() {
                    refreshParcels();
                });

            MLT.map = map;
        },

        showInfo = function(newInfo, selected) {
            if (mapinfoTimeout) {
                clearTimeout(mapinfoTimeout);
                mapinfoTimeout = null;
            }
            mapinfo.html(newInfo).show();
            if (selected) {
                mapinfo.addClass("selected");
                // Only show `map to selected` button if an address is selected
                if ($('#addresstable .address input[id^="select"]:checked').length) {
                    mapinfo.find('.mapit').show();
                } else {
                    mapinfo.find('.mapit').hide();
                }
            } else {
                mapinfo.removeClass("selected");
                mapinfo.find('.mapit').hide();
            }
        },

        hideInfo = function() {
            if (!selectedInfo) {
                mapinfoTimeout = setTimeout(function() {
                    if (!mapinfoHover) {
                        mapinfo.empty().hide();
                    }
                }, 100);
            }
        },

        refreshParcels = function() {
            var bounds = map.getBounds(),
            ne = bounds.getNorthEast(),
            sw = bounds.getSouthWest();

            if (map.getZoom() >= MIN_PARCEL_ZOOM) {
                $.getJSON(
                    geojson_url +
                        "?southlat=" + sw.lat +
                        "&northlat=" + ne.lat +
                        "&westlng=" + sw.lng +
                        "&eastlng=" + ne.lng,
                    function(data) {
                        map.removeLayer(geojson);
                        selectedLayer = null;
                        geojson = new L.GeoJSON();

                        geojson.on(
                            'featureparse',
                            function(e) {
                                var id = e.id;
                                e.layer.info = ich.parcelinfo(e.properties);
                                e.layer.select = function() {
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
                                e.layer.unselect = function() {
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
                                e.layer.on(
                                    'mouseover',
                                    function(ev) {
                                        if (!selectedInfo) {
                                            showInfo(e.layer.info, false);
                                        }
                                    });
                                e.layer.on(
                                    'mouseout',
                                    function(ev) {
                                        hideInfo();
                                    });
                                e.layer.on(
                                    'click',
                                    function(ev) {
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
                    });
            } else {
                map.removeLayer(geojson);
            };
        },

        addressPopups = function() {
            $('#addresstable .managelist .address input[id^="select"]').live('change', function() {
                var thisAddress = $(this).closest('.address'),
                popupContent = thisAddress.find('.mapkey').html(),
                lat = thisAddress.data('latitude'),
                lng = thisAddress.data('longitude');
                if ($(this).is(':checked')) {
                    if (lat && lng) {
                        this.popup = new L.Popup({
                            closeButton: false,
                            autoPan: false
                        });
                        this.popup.setLatLng(new L.LatLng(lat, lng));
                        this.popup.setContent(popupContent);
                        map.addLayer(this.popup);
                        map.panTo(new L.LatLng(lat, lng));
                        if (map.getZoom() < MIN_PARCEL_ZOOM) {
                            map.setZoom(MIN_PARCEL_ZOOM);
                        }
                    }
                } else {
                    if (this.popup) {
                        map.removeLayer(this.popup);
                    }
                }
                // Only show `map to selected` button if an address is selected
                if ($('#addresstable .address input[id^="select"]:checked').length) {
                    $('#mapinfo .mapit').show();
                } else {
                    $('#mapinfo .mapit').hide();
                }
            });
        },

        addressMapping = function() {
            var url = $('#mapping').data('associate-url');
            $('#mapinfo .mapit').live('click', function() {
                var selectedAddressID = $('#addresstable .address input[id^="select"]:checked').map(function() {
                    return $(this).closest('.address').data('id');
                }).get(),
                pl = selectedParcelInfo.pl,
                lat = selectedParcelInfo.latitude,
                lng = selectedParcelInfo.longitude;
                $.post(url, {
                    pl: pl,
                    aid: selectedAddressID
                }, function(data) {
                    $.each(data.mapped_to, function(i, address) {
                        var byline, web_ui,
                        id = address.id,
                        thisAddress = $('#addresstable .address[data-id="' + id + '"]'),
                        index = thisAddress.find('.mapkey').html();

                        if (address.import_source || address.mapped_by) { byline = true; }
                        if (address.import_source === 'web-ui') { web_ui = true; }

                        var updatedAddress = ich.address({
                            id: id,
                            pl: address.pl,
                            latitude: lat,
                            longitude: lng,
                            index: index,
                            street: address.street,
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
                    });

                    var updatedParcelInfo = ich.parcelinfo(data);
                    $('#mapinfo').removeClass('selected').html(updatedParcelInfo);
                    $('#mapinfo .mapit').hide();
                    selectedLayer.info = updatedParcelInfo;
                    selectedLayer.unselect();
                });
            });
        };

        if ($('#map').length) {
            initializeMap();
        }
        addressPopups();
        addressMapping();
    },

    addressListHeight = function() {
        var headerHeight = $('header[role="banner"]').outerHeight(),
            actionsHeight = $('.actions').outerHeight(),
            footerHeight = $('footer[role="contentinfo"]').outerHeight(),
            addressListHeight,
            updateHeight = function() {
                addressListHeight = $(window).height() - headerHeight - actionsHeight - footerHeight - 2;
                $('.managelist').css('height', addressListHeight + 'px');
            };
        updateHeight();
        $(window).resize(function() {
            $.doTimeout(250, function() {
                updateHeight();
            });
        });
    },

    addAddressLightbox = function() {
        var link = $('a[href=#lightbox-add-address]'),
        target = $("#lightbox-add-address"),
        url = target.data('add-address-url'),
        success = function(data) {
            target.html(data.html);
            bootstrapForm();
        },
        bootstrapForm = function() {
            var form = target.find('form').ajaxForm({
                success: success
            });
        };

        link.click(function() {
            $.get(url, success);
        });

        target.find('a[title*="close"]').live('click', function() {
            var form = target.find('form');
            if (form.length) {
                form.get(0).reset();
            }
        });
    },

    importAddressesLightbox = function() {
        var link = $('a[href=#lightbox-import-addresses]'),
        target = $("#lightbox-import-addresses"),
        url = target.data('import-addresses-url'),
        success = function(data) {
            target.html(data.html);
        };

        link.click(function() {
            $.get(url, success);
        });

        target.find('a[title*="close"]').live('click', function() {
            var form = target.find('form');
            if (form.length) {
                form.get(0).reset();
            }
        });
    },

    sorting = function() {
        var list = $('.actions .listordering > ul'),
            item = list.find('li[class^="by"]'),
            field = item.find('.field'),
            direction = item.find('.dir'),
            resetList = function() {
                $('.actions .listordering > ul > li.none').insertAfter($('.actions .listordering > ul > li:not(.none)').last());
            };

        field.click(function() {
            if (!($(this).closest('li[class^="by"]').hasClass('none'))) {
                $(this).closest('li[class^="by"]').find('.dir').removeClass('asc').removeClass('desc');
            } else {
                $(this).closest('li[class^="by"]').find('.dir').addClass('asc');
            }
            $(this).closest('li[class^="by"]').toggleClass('none');
            resetList();
            return false;
        });

        direction.click(function() {
            if ($(this).closest('li[class^="by"]').hasClass('none')) {
                $(this).closest('li[class^="by"]').removeClass('none');
            }
            if ($(this).hasClass('asc') || $(this).hasClass('desc')) {
                $(this).toggleClass('asc').toggleClass('desc');
            } else {
                $(this).addClass('asc');
            }
            resetList();
            return false;
        });

        $('.actions .listordering > ul').sortable({
            delay: 30,
            update: function(event, ui) {
                if (ui.item.hasClass('none')) {
                    ui.item.removeClass('none').find('.dir').addClass('asc');
                }
                resetList();
            }
        });
    },

    addressListLoading = function() {
        var container = $('#addresstable .managelist'),
        url = container.data('addresses-url'),
        loading = container.find('.load'),
        moreAddresses = true,
        currentlyLoading,
        newAddresses = function(data) {
            if (data.addresses.length) {
                $.each(data.addresses, function(i, address) {
                    var byline, web_ui, lat, lng;

                    if (address.parcel) {
                        lat = address.parcel.latitude,
                        lng = address.parcel.longitude;
                    }
                    if (address.import_source || address.mapped_by) { byline = true; }
                    if (address.import_source === 'web-ui') { web_ui = true; }

                    var addressHTML = ich.address({
                        id: address.id,
                        pl: address.pl,
                        latitude: lat,
                        longitude: lng,
                        index: address.index,
                        street: address.street,
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

                    loading.before(addressHTML).css('opacity', 0);
                    addressHTML.find('.details').html5accordion();
                });
            } else {
                loading.find('p').html('No more addresses');
                moreAddresses = false;
            }
            currentlyLoading = false;
        };

        // load some addresses to start out with
        // @@@ if this returns with errors, subsequent ajax calls will be prevented unless currentlyLoading is set to `false`
        if(url) {
            currentlyLoading = true;
            $.get(url, newAddresses);
        }

        container.scroll(function() {
            $.doTimeout('scroll', 150, function() {
                if ((container.get(0).scrollHeight - container.scrollTop() - container.outerHeight()) <= loading.outerHeight() && moreAddresses && !currentlyLoading) {
                    var count = container.find('.address').length + 1;
                    loading.animate({opacity: 1}, 'fast');
                    currentlyLoading = true;
                    // @@@ if this returns with errors, subsequent ajax calls will be prevented unless currentlyLoading is set to `false`
                    $.get(url + '?start=' + count, newAddresses);
                }
            });
        });
    },

    addressDetails = function() {
        var info = $('#addresstable .managelist [id^="address-id"] .details .summary');
        info.live('click', function() {
            if ($(this).closest('.details').hasClass('open')) {
                $(this).closest('.address').addClass('expanded');
            } else {
                $(this).closest('.address').removeClass('expanded');
            }
        });
    },

    addressSelect = function() {
        $('#addresstable .managelist .address .content').live('click', function(event) {
            if (!$(event.target).is('button, a, label, input, .summary, .adr, .street-address, .locality, .region')) {
                $(this).closest('.address').find('input[id^="select"]').click();
            }
        });
    };

    $(function() {
        $('#hcard-client-name .email').defuscate();
        $('input[placeholder], textarea[placeholder]').placeholder();
        $('.details:not(html)').html5accordion();
        $('#messages').messages({
            handleAjax: true,
            closeLink: '.message'
        });
        addressListHeight();
        addAddressLightbox();
        importAddressesLightbox();
        mapping();
        $('#addresstable .managelist .address .content .details .summary').live('click', function() {
            $(this).blur();
        });
        sorting();
        addressListLoading();
        addressDetails();
        addressSelect();
    });

})(jQuery);
