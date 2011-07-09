var MLT = MLT || {};

(function($) {
    var MIN_PARCEL_ZOOM = 17;

    var initializeMap = function() {
        var layer = new L.TileLayer(
            MLT.tileServerUrl, {attribution: MLT.mapCredits}),
        map = new L.Map(
            'map',
            {
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
        ),
        mapinfoTimeout = null,
        showInfo = function(newInfo, selected) {
            if (mapinfoTimeout) {
                clearTimeout(mapinfoTimeout);
                mapinfoTimeout = null;
            }
            mapinfo.html(newInfo).show();
            if (selected) {
                mapinfo.addClass("selected");
                // Only show `map to selected` button if an address is selected
                if ($('#addresstable input[id^="select"]:checked').length) {
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
        geojson_url = $('#mapping').data('parcel-geojson-url'),
        geojson = new L.GeoJSON(),
        selectedId = null,
        selectedInfo = null,
        selectedLayer = null,
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
                                var info = ich.parcelinfo(e.properties),
                                id = e.id;
                                e.layer.select = function() {
                                    if (selectedLayer) {
                                        selectedLayer.unselect();
                                    }
                                    selectedId = id;
                                    selectedInfo = info;
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
                                            showInfo(info, false);
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
                                            showInfo(info, false);
                                        } else {
                                            ev.target.select();
                                            showInfo(info, true);
                                        }
                                    });
                            });

                        geojson.addGeoJSON(data);
                        map.addLayer(geojson);
                    });
            } else {
                map.removeLayer(geojson);
            };
        };

        map.on(
            'moveend',
            function() {
                refreshParcels();
            });

        MLT.map = map; // for playing in Firebug
    };

    var mapPopups = function() {
        $('#addresstable .managelist .address input[id^="select_"]').live('click', function() {
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
                    MLT.map.addLayer(this.popup);
                    MLT.map.panTo(new L.LatLng(lat, lng));
                    if (MLT.map.getZoom() < MIN_PARCEL_ZOOM) {
                        MLT.map.setZoom(MIN_PARCEL_ZOOM);
                    }
                }
            } else {
                if (this.popup) {
                    MLT.map.removeLayer(this.popup);
                }
            }
            // Only show `map to selected` button if an address is selected
            if ($(this).is(':checked')) {
                $('#mapinfo .mapit').show();
            } else {
                $('#mapinfo .mapit').hide();
            }
        });
    };

    var addressListHeight = function() {
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
    };

    var addAddressLightbox = function() {
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
    };


    var importAddressesLightbox = function() {
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
    };

    var sorting = function() {
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
    };

    var addressListLoading = function() {
        var container = $('#addresstable .managelist'),
        url = container.data('addresses-url'),
        loading = container.find('.load'),
        moreAddresses = true,
        newAddresses = function(data) {
            if ($.trim(data.html)) {
                var elems = $(data.html);
                loading.before(elems).css('opacity', 0);
                elems.find('.details').html5accordion();
            } else {
                loading.find('p').html('No more addresses');
                moreAddresses = false;
            }
        };

        // load some addresses to start out with
        if(url) {
            $.get(url, newAddresses);
        }

        container.scroll(function() {
            $.doTimeout('scroll', 250, function() {
                if ((container.get(0).scrollHeight - container.scrollTop() - container.outerHeight()) <= loading.outerHeight() && moreAddresses) {
                    var count = container.find('.address').length + 1;
                    loading.animate({opacity: 1}, 'fast');
                    $.get(url + '?start=' + count, newAddresses);
                }
            });
        });
    };

    var addressDetails = function() {
        var info = $('#addresstable .managelist [id^="address-id"] .details .summary');
        info.live('click', function() {
            if ($(this).closest('.details').hasClass('open')) {
                $(this).closest('.address').addClass('expanded');
            } else {
                $(this).closest('.address').removeClass('expanded');
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
        if ($('#map').length) {
            initializeMap();
        }
        mapPopups();
        $('#addresstable .managelist .address .content .details .summary').live('click', function() {
            $(this).blur();
        });
        sorting();
        addressListLoading();
        addressDetails();
    });

})(jQuery);
