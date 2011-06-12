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
        mapinfo = $("#mapinfo");

        $.getJSON(
            "/map/geojson/",
            function(data) {
                var gj = new L.GeoJSON();

                gj.on(
                    'featureparse',
                    function(e) {
                        var info =
                            '<h3>' + e.properties.pl + '</h3>' +
                            '<h4>' + e.properties.address + '</h4>' +
                            '<p>' + e.properties.classcode + '</p>' +
                            '<p>' + e.properties.first_owner + '</p>';
                        e.layer.select = function() {
                            this.selected = true;
                            this.setStyle({color: "red"});
                        };
                        e.layer.unselect = function() {
                            this.selected = false;
                            this.setStyle({color: "blue"});
                        };
                        e.layer.unselect();
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

                gj.addGeoJSON(data);
                map.addLayer(gj);
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
