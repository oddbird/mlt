//** CSS-Lightboxes **//

/*jslint    browser:    true,
            indent:     4 */
/*global    jQuery */

(function ($) {

    'use strict';

    // Settings ------------------------------------------------------------------
    // Edit these settings to match your lightbox HTML code. These will act as
    // defaults, which you can override per application as needed:

    var lightboxes = $('#lightboxes aside'),
        closeLinkSelector = 'a[title*="close"]',
        showClass = 'active',
        hideClass = 'hidden';

    // Function ------------------------------------------------------------------
    // Call this function to implement lightbox bootstrapping
    // on any given lightboxes:

    function lightboxBootstrap(boxes, close_sel, sClass, hClass) {

        $(boxes).not('.' + sClass).addClass(hClass);

        function lightboxClose(lightbox) {
            $(lightbox).removeClass(sClass).addClass(hClass);
        }

        function lightboxOpen(lightbox) {
            $(boxes).removeClass(sClass).addClass(hClass);
            $(lightbox).removeClass(hClass).addClass(sClass);
        }

        boxes.each(function () {
            $('a[href="#' + $(this).attr('id') + '"]').click(function () {
                lightboxOpen($(this).attr('href'));
                return false;
            });
        });

        boxes.on('click', close_sel, function () {
            lightboxClose($(this).parents(boxes));
            return false;
        });
    }

    // Application ---------------------------------------------------------------
    $(function () {
        lightboxBootstrap(lightboxes, closeLinkSelector, showClass, hideClass);
    });

}(jQuery));
