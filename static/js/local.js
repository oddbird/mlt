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
            mapinfo = $("#mapinfo").hide(),
            geojson = new L.GeoJSON(),
            selectedIds = [],
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
                            geojson = new L.GeoJSON();

                            geojson.on(
                                'featureparse',
                                function(e) {
                                    var info = ich.parcelinfo(e.properties);
                                    id = e.id;
                                    e.layer.select = function() {
                                        if (selectedIds.indexOf(id) === -1) {
                                            selectedIds.push(id);
                                        }
                                        this.selected = true;
                                        this.setStyle(
                                            {color: "red", weight: 5});
                                    };
                                    e.layer.unselect = function() {
                                        var idx = selectedIds.indexOf(id);
                                        if (idx != -1) {
                                            selectedIds.splice(idx, 1);
                                        }
                                        this.selected = false;
                                        this.setStyle(
                                            {color: "blue", weight: 2});
                                    };
                                    if (selectedIds.indexOf(id) != -1) {
                                        e.layer.select();
                                    } else {
                                        e.layer.unselect();
                                    }
                                    e.layer.on(
                                        'mouseover',
                                        function(ev) {
                                            mapinfo.empty().prepend(info).show();
                                        });
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

    var lightboxBootstrap = function() {
        var update = function() {
            if ($('#lightbox-add-address #complex').is(':checked')) {
                $('#lightbox-add-address #complex_name').show();
            } else {
                $('#lightbox-add-address #complex_name').hide();
            }
        };
        $('#lightbox-add-address #complex').change(function() {
            update();
        });
        update();
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
                    $('#messages').fadeOut('fast');
                    $(this).unbind(event);
                });
            });
        }
    };

    $(function() {
        $('#hcard-client-name .email').defuscate();
        $('input[placeholder], textarea[placeholder]').placeholder();
        $('.details:not(html)').html5accordion('.summary');
        addressListHeight();
        lightboxBootstrap();
        initializeMap();
        $('#addresstable .managelist .address .content .details .summary').click(function() {
            $(this).blur();
        });
        messages();
    });

})(jQuery);
