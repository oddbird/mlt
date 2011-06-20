from datetime import datetime

import floppyforms as forms

from ..core.forms import BareTextarea
from . import models



WEB_UI_IMPORT_SOURCE = "web-ui"



class AddressForm(forms.ModelForm):
    street = forms.CharField(max_length=100)


    class Meta:
        model = models.Address
        widgets = {"notes": BareTextarea}
        fields = [
            "city", "state", "zip", "multi_units", "complex_name", "notes"]


    def clean_street(self):
        try:
            number, name, suffix = models.Address.parse_street(
                self.cleaned_data["street"])
        except models.Address.StreetNumberError:
            raise forms.ValidationError("Street address must have a number.")
        except models.Address.StreetSuffixError:
            raise forms.ValidationError(
                "Street address must have a valid suffix.")

        self.cleaned_data["street_number"] = number
        self.cleaned_data["street_name"] = name
        self.cleaned_data["street_suffix"] = suffix

        return self.cleaned_data


    def save(self, user):
        address = super(AddressForm, self).save(commit=False)

        address.street_number = self.cleaned_data["street_number"]
        address.street_name = self.cleaned_data["street_name"]
        address.street_suffix = self.cleaned_data["street_suffix"]

        address.imported_by = user
        address.import_source = WEB_UI_IMPORT_SOURCE
        address.import_timestamp = datetime.utcnow()

        address.save()

        return address
