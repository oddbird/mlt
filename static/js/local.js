var MLT = MLT || {};

(function($) {

    var initializeMap = function() {
        if ($('#map').length) {
            var layer = new L.TileLayer(
                MLT.tileServerUrl, {attribution: MLT.mapCredits}),
            map = new L.Map(
                'map',
                {
                    center: new L.LatLng(MLT.mapDefaultLat, MLT.mapDefaultLon),
                    zoom: MLT.mapDefaultZoom,
                    layers: [layer]
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
            geojson = new L.GeoJSON(),
            selectedId = null,
            selectedInfo = null,
            selectedLayer = null,
            refreshParcels = function() {
                var bounds = map.getBounds(),
                ne = bounds.getNorthEast(),
                sw = bounds.getSouthWest();

                if (map.getZoom() > 16) {
                    $.getJSON(
                        "/map/geojson/" + sw.lng + "/" + ne.lng +
                            "/" + sw.lat + "/" + ne.lat + "/",
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
                                            showInfo(info, this.selected);
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
        var bootstrapForm = function() {
            var updateComplexName = function() {
                if ($('#lightbox-add-address #multi_units').is(':checked')) {
                    $('#lightbox-add-address #complex_name').show();
                } else {
                    $('#lightbox-add-address #complex_name').hide();
                }
            },
            form = $('#lightbox-add-address form').ajaxForm(
                {
                    target: "#lightbox-add-address",
                    success: bootstrapForm
                });
            $('#lightbox-add-address #multi_units').change(
                function() {
                    updateComplexName();
                });
            updateComplexName();
        };

        $('a[href=#lightbox-add-address]').click(
            function() {
                $("#lightbox-add-address").load(
                    "/map/add_address/",
                    bootstrapForm
                );
            });
    };

    var messages = function() {
        var allSuccess = true;
        $('#messages .close').click(function() {
            $('#messages').fadeOut('fast');
            return false;
        });
        $('#messages li.message').each(function() {
            if (!($(this).hasClass('success'))) {
                allSuccess = false;
            }
        });
        if (allSuccess === true) {
            $(document).bind('mousedown keydown', function(event) {
                $.doTimeout(500, function() {
                    $('#messages').fadeOut(3000);
                    $(this).unbind(event);
                });
            });
        }
    };

    var sorting = function() {
        var list = $('.actions .listordering > ul'),
            item = list.find('li[class^="by"]'),
            field = item.find('.field'),
            direction = item.find('.dir');

        field.click(function() {
            if (!($(this).closest('li[class^="by"]').hasClass('none'))) {
                $(this).closest('li[class^="by"]').find('.dir').removeClass('asc').removeClass('desc');
            } else {
                $(this).closest('li[class^="by"]').find('.dir').addClass('asc');
            }
            $(this).closest('li[class^="by"]').toggleClass('none');
            return false;
        });

        direction.click(function() {
            if ($(this).hasClass('asc') || $(this).hasClass('desc')) {
                $(this).toggleClass('asc').toggleClass('desc');
            } else {
                $(this).addClass('asc');
            }
            return false;
        });

        $('.actions .listordering > ul').sortable();
    };

    $(function() {
        $('#hcard-client-name .email').defuscate();
        $('input[placeholder], textarea[placeholder]').placeholder();
        $('.details:not(html)').html5accordion('.summary');
        addressListHeight();
        addAddressLightbox();
        initializeMap();
        $('#addresstable .managelist .address .content .details .summary').click(function() {
            $(this).blur();
        });
        messages();
        sorting();
    });

})(jQuery);
