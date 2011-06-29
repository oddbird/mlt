var MLT = MLT || {};

(function($) {
    var MIN_PARCEL_ZOOM = 17;

    var initializeMap = function() {
        if ($('#map').length) {
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
                function() { mapinfoHover = false; hideInfo(); }),
            mapinfoTimeout = null,
            showInfo = function(newInfo, selected) {
                if (mapinfoTimeout) {
                    clearTimeout(mapinfoTimeout);
                    mapinfoTimeout = null;
                }
                mapinfo.empty().prepend(newInfo).show();
                if (selected) {
                    mapinfo.addClass("selected");
                } else {
                    mapinfo.removeClass("selected");
                }
            },
            hideInfo = function() {
                if (selectedInfo) {
                    showInfo(selectedInfo, true);
                } else {
                    if (!mapinfoHover) {
                        mapinfoTimeout = setTimeout(
                            function() {
                                mapinfo.empty().hide();
                            },
                            100);
                    }
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
                                        this.setStyle(
                                            {color: "red", weight: 5});
                                    };
                                    e.layer.unselect = function() {
                                        if (this.selected) {
                                            selectedId = null;
                                            selectedInfo = null;
                                            selectedLayer = null;
                                        }
                                        this.selected = false;
                                        this.setStyle(
                                            {color: "blue", weight: 2});
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
                                                showInfo(info, this.selected);
                                            }
                                        });
                                    e.layer.on(
                                        'mouseout',
                                        function(ev) { hideInfo(); });
                                    e.layer.on(
                                        'click',
                                        function(ev) {
                                            if (ev.target.selected) {
                                                ev.target.unselect();
                                            } else {
                                                ev.target.select();
                                            }
                                        });
                                });

                            geojson.addGeoJSON(data);
                            map.addLayer(geojson);
                        });
                } else {
                    map.removeLayer(geojson);
                    mapinfo.hide();
                };
            };

            map.on(
                'moveend',
                function() {
                    refreshParcels();
                });

            MLT.map = map; // for playing in Firebug
        }
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
                    MLT.map.setView(new L.LatLng(lat, lng), MIN_PARCEL_ZOOM);
                }
            } else {
                if (this.popup) {
                    MLT.map.removeLayer(this.popup);
                }
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
            var form = $('#lightbox-add-address form').ajaxForm({
                success: success
            });
        };

        link.click(function() {
            $.get(url, success);
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

    var addressList = function() {
        var container = $('#addresstable .managelist'),
        url = container.data('addresses-url'),
        loading = container.find('.load'),
        moreAddresses = true,
        newAddresses = function(data) {
            if ($.trim(data.html)) {
                var elems = $(data.html);
                elems.find('.details').html5accordion('.summary');
                loading.before(elems).css('opacity', 0);
            } else {
                loading.find('p').html('No more addresses');
                moreAddresses = false;
            }
        };

        // load some addresses to start out with
        $.get(url, newAddresses);

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

    $(function() {
        $('#hcard-client-name .email').defuscate();
        $('input[placeholder], textarea[placeholder]').placeholder();
        $('.details:not(html)').html5accordion('.summary');
        addressListHeight();
        addAddressLightbox();
        initializeMap();
        mapPopups();
        $('#addresstable .managelist .address .content .details .summary').live('click', function() {
            $(this).blur();
        });
        $('#messages').messages({handleAjax: true});
        sorting();
        addressList();
    });

})(jQuery);
