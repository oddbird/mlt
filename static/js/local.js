(function($) {

    var addressListHeight = function() {
        var headerHeight = $('header[role="banner"]').outerHeight(),
            actionsHeight = $('.actions').outerHeight(),
            footerHeight = $('footer[role="contentinfo"]').outerHeight(),
            addressListHeight = $(window).height() - headerHeight - actionsHeight - footerHeight;
            $('.managelist').css('height', addressListHeight + 'px');
        $(window).resize(function() {
            addressListHeight = $(window).height() - headerHeight - actionsHeight - footerHeight;
            $('.managelist').css('height', addressListHeight + 'px');
        });
    };

    $(function() {
        $('#hcard-client-name .email').defuscate();
        $('input[placeholder], textarea[placeholder]').placeholder();
        $('#filter .toggle a').click(
            function() {
                $('#filter .visual').toggleClass('compact').toggleClass('expanded');
                return false;
            }
        );
        if ($('html').hasClass('no-details')) {
            $('details').html5accordion('summary');
        }
        $('.details:not(html)').html5accordion('.summary');
        addressListHeight();
    });

})(jQuery);