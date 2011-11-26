from uuid import uuid4

from django import forms

from django.contrib.gis import admin

from . import models


class AddressBatchAssociationInline(admin.TabularInline):
    model = models.Address.batches.through


class AddressAdmin(admin.ModelAdmin):
    list_display = [
        "__unicode__",
        "pl",
        ]
    list_filter = [
        "multi_units",
        "mapped_by",
        "batches",
        "complex_name",
        "state",
        ]
    search_fields = [
        "input_street",
        "parsed_street",
        "city",
        "state",
        ]
    inlines = [AddressBatchAssociationInline]
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
        ]



class ParcelAdmin(admin.OSMGeoAdmin):
    list_display = [
        "__unicode__", "address", "first_owner", "classcode", "import_timestamp"
        ]
    search_fields = ["pl", "address", "first_owner", "classcode"]
    exclude = ["deleted"]



class AddressBatchAdmin(admin.ModelAdmin):
    list_display = ["__unicode__", "user", "timestamp"]
    search_fields = ["tag", "user", "timestamp"]



class ApiKeyCreationForm(forms.ModelForm):
    class Meta:
        model = models.ApiKey
        exclude = ["key"]


    def save(self, commit=True):
        instance = super(ApiKeyCreationForm, self).save(commit=False)
        instance.key = uuid4()
        if commit:
            instance.save()
        return instance



class ApiKeyAdmin(admin.ModelAdmin):
    list_display = ["__unicode__", "key"]
    search_fields = ["name"]


    def get_form(self, request, obj=None, **kwargs):
        """
        Use special form for API key creation.

        """
        defaults = {}
        if obj is None:
            defaults.update({
                'form': ApiKeyCreationForm,
            })
        defaults.update(kwargs)
        return super(ApiKeyAdmin, self).get_form(request, obj, **defaults)


admin.site.register(models.Address, AddressAdmin)
admin.site.register(models.Parcel, ParcelAdmin)
admin.site.register(models.AddressBatch, AddressBatchAdmin)
admin.site.register(models.ApiKey, ApiKeyAdmin)
