from django.conf.urls.defaults import patterns, url



urlpatterns = patterns(
    "mlt.map.views",

    url(r"^import/$", "import_addresses", name="map_import_addresses"),

    url(r"^_addresses/$", "addresses", name="map_addresses"),
    url(r"^_add_address/$", "add_address", name="map_add_address"),
    url(r"^_associate/$", "associate", name="map_associate"),
    url(r"^_geojson/$", "geojson", name="map_geojson"),
    )
