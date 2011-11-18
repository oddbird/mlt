from django.contrib.gis import admin

from . import models



class AddressAdmin(admin.ModelAdmin):
    list_display = [
        "__unicode__",
        "pl",
        "import_source",
        "imported_by",
        "import_timestamp",
        ]
    list_filter = [
        "multi_units",
        "mapped_by",
        "imported_by",
        "import_source",
        "complex_name",
        "state",
        ]
    date_hierarchy = "import_timestamp"
    search_fields = [
        "input_street",
        "parsed_street",
        "city",
        "state",
        ]
    fieldsets = [
        (None, {
                "fields": [
                    "input_street",
                    (
                        "street_prefix",
                        "street_number",
                        "street_name",
                        "street_type",
                        "street_suffix",
                        ),
                    ("city", "state"),
                    ("multi_units", "complex_name"),
                    "notes",
                    ]
                }),
        ("Mapping", {
                "fields": [
                    ("pl", "needs_review"),
                    ("mapped_by", "mapped_timestamp"),
                    ]
                }),
        ("Import", {
                "fields": [
                    "import_source",
                    ("imported_by", "import_timestamp"),
                    ]
                }),
        ]



class ParcelAdmin(admin.OSMGeoAdmin):
    list_display = [
        "__unicode__", "address", "first_owner", "classcode", "import_timestamp"
        ]
    search_fields = ["pl", "address", "first_owner", "classcode"]
    exclude = ["deleted"]



admin.site.register(models.Address, AddressAdmin)
admin.site.register(models.Parcel, ParcelAdmin)
