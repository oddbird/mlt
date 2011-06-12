var MLT = MLT || {};

(function($) {

    var initializeMap = function() {
        var layer = new L.TileLayer(
            MLT.tileServerUrl, {attribution: MLT.mapCredits}),
        map = new L.Map(
            'map',
            {
                center: new L.LatLng(MLT.mapDefaultLat, MLT.mapDefaultLon),
                zoom: MLT.mapDefaultZoom,
                layers: [layer]
            }),
        mapinfo = $("#mapinfo"),
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
                                var info =
                                    '<h3>' + e.properties.pl + '</h3>' +
                                    '<h4>' + e.properties.address + '</h4>' +
                                    '<p>' + e.properties.classcode + '</p>' +
                                    '<p>' + e.properties.first_owner + '</p>',
                                id = e.id;
                                e.layer.select = function() {
                                    if (selectedIds.indexOf(id) === -1) {
                                        selectedIds.push(id);
                                    }
                                    this.selected = true;
                                    this.setStyle({color: "red"});
                                };
                                e.layer.unselect = function() {
                                    var idx = selectedIds.indexOf(id);
                                    if (idx != -1) {
                                        selectedIds.splice(idx, 1);
                                    }
                                    this.selected = false;
                                    this.setStyle({color: "blue"});
                                };
                                if (selectedIds.indexOf(id) != -1) {
                                    e.layer.select();
                                } else {
                                    e.layer.unselect();
                                }
                                e.layer.on(
                                    'mouseover',
                                    function(ev) {
                                        mapinfo.html(info);
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
            } else { map.removeLayer(geojson); };
        };

        map.on(
            'moveend',
            function() {
                refreshParcels();
            });

        MLT.map = map; // for playing in Firebug
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

    $(function() {
        $('#hcard-client-name .email').defuscate();
        $('input[placeholder], textarea[placeholder]').placeholder();
        // $('#filter .toggle a').click(
        //     function() {
        //         $('#filter .visual').toggleClass('compact').toggleClass('expanded');
        //         return false;
        //     }
        // );
        // if ($('html').hasClass('no-details')) {
        //     $('details').html5accordion('summary');
        // }
        $('.details:not(html)').html5accordion('.summary');
        addressListHeight();
        lightboxBootstrap();
        initializeMap();
        $('#addresstable .managelist .address .content .details .summary').click(function() {
            $(this).blur();
        });
    });

})(jQuery);
