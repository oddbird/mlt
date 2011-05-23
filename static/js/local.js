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
});
