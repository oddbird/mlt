from django.conf.urls.defaults import patterns, url, include
from django.views.generic.simple import direct_to_template

from django.contrib import admin
from django.contrib.auth.decorators import login_required

admin.autodiscover()


direct_to_template_login = login_required(direct_to_template)


urlpatterns = patterns(
    "",
    url("^$",
        direct_to_template_login,
        {"template": "home.html"},
        name="home"),

    url(r"^account/", include("mlt.account.urls")),

    url(r"^admin/", include(admin.site.urls)),

    # wireframes
    url(r"^history/$",
        "django.views.generic.simple.direct_to_template",
        {"template": "history/history.html"}),
)
