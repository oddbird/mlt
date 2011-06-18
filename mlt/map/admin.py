from django.contrib.gis import admin

from . import models



class StreetSuffixAliasInline(admin.TabularInline):
    model = models.StreetSuffixAlias
    extra = 0



class StreetSuffixAdmin(admin.ModelAdmin):
    list_display = ["__unicode__", "joined_aliases"]
    inlines = [StreetSuffixAliasInline]


    def joined_aliases(self, obj):
        return ", ".join([a.alias for a in obj.aliases.all()])
    joined_aliases.short_description = "Alternate spellings"



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
        "complex",
        "state",
        ]
    date_hierarchy = "import_timestamp"
    search_fields = [
        "street_number",
        "street_name",
        "city",
        "state",
        "zip",
        ]
    fieldsets = [
        (None, {
                "fields": [
                    (
                        "street_number",
                        "street_name",
                        "street_suffix",
                        "multi_units"
                        ),
                    ("city", "state", "zip"),
                    "complex_name",
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
    list_display = ["__unicode__", "address", "first_owner", "classcode"]
    search_fields = ["pl", "address", "first_owner", "classcode"]



admin.site.register(models.StreetSuffix, StreetSuffixAdmin)
admin.site.register(models.Address, AddressAdmin)
admin.site.register(models.Parcel, ParcelAdmin)
