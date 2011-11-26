from django.conf.urls.defaults import patterns, url



urlpatterns = patterns(
    "mlt.map.views",

    url(r"^import/$", "import_addresses", name="map_import_addresses"),
    url(r"^load_parcels/$", "load_parcels", name="map_load_parcels"),
    url(r"^load_parcels/status/(?P<task_id>.+)/$",
        "load_parcels_status", name="map_load_parcels_status"),

    url(r"^_addresses/$", "addresses", name="map_addresses"),
    url(r"^_history/$", "history", name="map_history"),
    url(r"^_export/$", "export_addresses", name="map_export_addresses"),
    url(r"^_add_address/$", "add_address", name="map_add_address"),
    url(r"^_edit_address/(?P<address_id>\d+)/$",
        "edit_address", name="map_edit_address"),
    url(r"^_add_tag/(?P<address_id>\d+)/$",
        "add_tag", name="map_add_tag"),
    url(r"^_associate/$", "associate", name="map_associate"),
    url(r"^_geojson/$", "geojson", name="map_geojson"),
    url(r"^_filter_autocomplete/$", "filter_autocomplete", name="map_filter_autocomplete"),
    url(r"^_history_autocomplete/$", "history_autocomplete", name="map_history_autocomplete"),
    url(r"^_geocode/$", "geocode", name="map_geocode"),
    url(r"^_action/$", "address_actions", name="map_address_actions"),
    url(r"^_revert/(?P<change_id>\d+)/$",
        "revert_change", name="map_revert_change"),
    )
