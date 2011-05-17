$(function() {
    $('#hcard-client-name .email').defuscate();
    $('input[placeholder], textarea[placeholder]').placeholder();
    $('#filter .toggle a').click(
        function() {
            $('#filter .visual').toggleClass('compact').toggleClass('expanded');
            return false;
        }
    );
    // $('details').html5accordion('summary');
    // $('.details').html5accordion('.summary');
});
