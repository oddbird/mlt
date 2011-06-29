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
            if ($(this).is(':checked')) {
                var popupContent = 'A',
                    lat = $(this).closest('.address').data('latitude'),
                    lng = $(this).closest('.address').data('longitude');
                this.popup = new L.Popup({
                    closeButton: false,
                    autoPan: false
                });
                this.popup.setLatLng(new L.LatLng(lat, lng));
                this.popup.setContent(popupContent);
                MLT.map.addLayer(this.popup);
                MLT.map.setView(new L.LatLng(lat, lng), MIN_PARCEL_ZOOM);
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
            var form = $('#lightbox-add-address form').ajaxForm({
                target: "#lightbox-add-address",
                success: bootstrapForm
            });
        };

        $('a[href=#lightbox-add-address]').click(function() {
            $("#lightbox-add-address").load(
                "/map/add_address/",
                bootstrapForm
            );
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

    var autoLoad = function() {
        var container = $('.managelist'),
            loading = container.find('.load').css('opacity', 0);
        container.scroll(function() {
            $.doTimeout('scroll', 250, function() {
                if ((container.get(0).scrollHeight - container.scrollTop() - container.outerHeight()) <= loading.outerHeight()) {
                    loading.animate({opacity: 1}, 'fast');
                    // This function mimics an ajax call with a delay of 300ms
                    var fakeAjaxCall = function(number, callback) { // @@@ faked ajax
                        var response =
                            '<article class="address new" id="address-id-' + number + '" data-latitude="41.822001" data-longitude="-71.392436">' +
                                '<input type="checkbox" value="" name="select" id="select_' + number + '">' +
                                '<div class="content">' +
                                    '<span class="mapkey">A.</span>' +
                                    '<label for="select_' + number + '">' +
                                        '<h3 class="adr">' +
                                            '<div class="street-address">27 Fremont St.</div>' +
                                            '<div class="locality">Providence</div>, ' +
                                            '<div class="region">RI</div> ' +
                                        '</h3>' +
                                    '</label>' +
                                    '<div class="id approved">' +
                                      '<input type="checkbox" name="flag_for_review_' + number + '" value="" id="flag_for_review_' + number + '">' +
                                      '<label for="flag_for_review_' + number + '">flag for review</label>' +
                                      '<label for="select_' + number + '" class="value">21 313</label>' +
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
                                container.find('.load').before(data);
                                container.find('.address.new .details').html5accordion('.summary');
                                container.find('.address.new').removeClass('new');
                                loading.css('opacity', 0);
                            }
                        );
                    }
                }
            });
        });
    };

    $(function() {
        $('#hcard-client-name .email').defuscate();
        $('input[placeholder], textarea[placeholder]').placeholder();
        $('.details:not(html)').html5accordion('.summary');
        $('#messages').messages({
            handleAjax: true,
            closeLink: '.message'
        });
        addressListHeight();
        addAddressLightbox();
        initializeMap();
        mapPopups();
        $('#addresstable .managelist .address .content .details .summary').live('click', function() {
            $(this).blur();
        });
        sorting();
        autoLoad();
    });

})(jQuery);
