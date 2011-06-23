from datetime import datetime

import floppyforms as forms

from ..core.forms import BareTextarea
from . import models



WEB_UI_IMPORT_SOURCE = "web-ui"



class AddressForm(forms.ModelForm):
    class Meta:
        model = models.Address
        widgets = {"notes": BareTextarea}
        fields = [
            "street_number", "street_name", "street_suffix",
            "city", "state", "multi_units", "complex_name", "notes"]


    def save(self, user):
        address = super(AddressForm, self).save(commit=False)

        address.street_number = self.cleaned_data["street_number"]
        address.street_name = self.cleaned_data["street_name"]
        address.street_suffix = self.cleaned_data["street_suffix"]

        address.input_street = address.street

        address.imported_by = user
        address.import_source = WEB_UI_IMPORT_SOURCE
        address.import_timestamp = datetime.utcnow()

        address.save()

        return address
