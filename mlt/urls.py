from django.conf.urls.defaults import patterns, url, include

from django.contrib import admin

admin.autodiscover()



urlpatterns = patterns(
    "",
    url("^$", "mlt.views.home", name="home"),

    url(r"^account/", include("mlt.account.urls")),
    url(r"^map/", include("mlt.map.urls")),

    url(r"^admin/", include(admin.site.urls)),

    # wireframes
    url(r"^history/$",
        "django.views.generic.simple.direct_to_template",
        {"template": "history/history.html"}),
)
