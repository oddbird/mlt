from django.conf.urls.defaults import patterns, url



urlpatterns = patterns(
    "mlt.map.views",

    url(r"^add_address/$", "add_address", name="map_add_address"),
    url(r"^geojson/(?P<westlat>[-.0-9]+)/(?P<eastlat>[-.0-9]+)/(?P<southlng>[-.0-9]+)/(?P<northlng>[-.0-9]+)/$", "geojson", name="map_geojson"),
    )
