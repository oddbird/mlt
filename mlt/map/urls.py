from django.conf.urls.defaults import patterns, url



urlpatterns = patterns(
    "mlt.map.views",

    url(r"^_addresses/$", "addresses", name="map_addresses"),
    url(r"^_add_address/$", "add_address", name="map_add_address"),
    url(r"^_geojson/$", "geojson", name="map_geojson"),
    )
