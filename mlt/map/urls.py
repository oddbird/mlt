from django.conf.urls.defaults import patterns, url



urlpatterns = patterns(
    "mlt.map.views",

    url(r"^geojson/(?P<westlat>[-.0-9]+)/(?P<eastlat>[-.0-9]+)/(?P<southlon>[-.0-9]+)/(?P<northlon>[-.0-9]+)/$", "geojson", name="map_geojson"),
    )
