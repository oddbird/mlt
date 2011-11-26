from django.conf.urls.defaults import patterns, url



urlpatterns = patterns(
    "mlt.map.api.views",
    url("^$", "home", name="api_home"),
    url("^addresses/$", "addresses", name="api_addresses"),
    url("^batches/$", "batches", name="api_batches"),
)
