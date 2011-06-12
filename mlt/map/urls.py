from django.conf.urls.defaults import patterns, url



urlpatterns = patterns(
    "mlt.map.views",

    url(r"^geojson/$", "geojson", name="map_geojson"),
    )
