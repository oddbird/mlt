(function($) {

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
        $('#addresstable .managelist .address .content .details .summary').click(function() {
            $(this).blur();
        });
    });

})(jQuery);