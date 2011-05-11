from django.conf.urls.defaults import patterns, url, include

from django.contrib import admin
    
admin.autodiscover()
        


urlpatterns = patterns(
    "",
    url("^$", "django.views.generic.simple.direct_to_template", 
        {"template": "home.html"}, name="home"),
    url(r"^admin/", include(admin.site.urls)),
)
        