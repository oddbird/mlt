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

    var mapPopups = function() {
        $('#addresstable .managelist .address input[id^="select_"]').live('click', function() {
            if ($(this).is(':checked')) {
                var popupContent = 'A',
                    lat = $(this).closest('.address').data('latitude'),
                    lng = $(this).closest('.address').data('longitude');
                this.popup = new L.Popup({
                    closeButton: false,
                    closeMapOnClick: false
                });
                this.popup.setLatLng(new L.LatLng(lat, lng));
                this.popup.setContent(popupContent);
                MLT.map.addLayer(this.popup);
            } else {
                MLT.map.removeLayer(this.popup);
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

    var autoLoad = function() {
        var container = $('.managelist');
        container.scroll(function() {
            if (container.outerHeight() === (container.get(0).scrollHeight - container.scrollTop())) {
                // This function mimics an ajax call with a delay of 300ms
                var fakeAjaxCall = function(number, callback) {
                    var response =
                        '<article class="address new" id="address-id-' + number + '">' +
                            '<input type="checkbox" value="" name="select" id="select_' + number + '">' +
                            '<div class="content">' +
                                '<label for="select_' + number + '">' +
                                    '<h3 class="adr">' +
                                        '<div class="street-address">3635 Van Gordon St.</div>' +
                                        '<div class="locality">Providence</div>, ' +
                                        '<div class="region">RI</div> ' +
                                        '<div class="postal-code">02909</div>' +
                                    '</h3>' +
                                '</label>' +
                                '<div class="id unmapped">' +
                                    '<label class="value" for="select_' + number + '">not mapped</label>' +
                                '</div>' +
                                '<ul class="controls">' +
                                    '<li><a title="edit" href="#">edit</a></li>' +
                                    '<li><a title="history" href="#">history</a></li>' +
                                    '<li><button value="" name="delete" type="submit">delete</button></li>' +
                                '</ul>' +
                                '<div class="details">' +
                                    '<p class="summary" tabindex="0">details</p>' +
                                    '<div class="more">' +
                                        '<div class="complex">' +
                                            '<button class="multiple" type="submit" name="complex">multiple units</button>' +
                                            '<p class="name">single unit</p>' +
                                        '</div>' +
                                        '<div class="byline">' +
                                            '<p class="hcard">' +
                                                'Imported by <cite class="fn">[username]</cite> from [source] on <time pubdate="">[timestamp]</time>.' +
                                            '</p>' +
                                        '</div>' +
                                    '</div>' +
                                '</div>' +
                            '</div>' +
                        '</article>';
                    function callbackfn() { callback(response); }
                    window.setTimeout(callbackfn, 300);
                };
                var currentTotal = container.find('article.address').length;
                for (var i = currentTotal + 1; i < currentTotal + 27; i++) {
                    // Add returned data
                    fakeAjaxCall(
                        i,
                        function(data) {
                            container.append(data);
                            container.find('.address.new .details').html5accordion('.summary');
                            container.find('.address.new').removeClass('new');
                        }
                    );
                }
            }
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
        messages();
        sorting();
        autoLoad();
    });

})(jQuery);
