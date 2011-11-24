from datetime import datetime
import shutil
import tempfile
import os
import zipfile

import floppyforms as forms

from ..core.conf import conf
from ..core.forms import BareTextarea
from .importer import CSVAddressImporter
from . import models, tasks



class AddressForm(forms.ModelForm):
    class Meta:
        model = models.Address
        widgets = {"notes": BareTextarea}
        fields = [
            "street_prefix", "street_number", "street_name", "street_type",
            "street_suffix", "edited_street",
            "city", "state", "multi_units", "complex_name", "notes"]


    def __init__(self, *args, **kwargs):
        super(AddressForm, self).__init__(*args, **kwargs)
        if conf.MLT_DEFAULT_STATE is not None:
            self.fields["state"].initial = conf.MLT_DEFAULT_STATE


    def clean(self):
        if not (
            self.cleaned_data["street_name"] or
            self.cleaned_data["edited_street"]
            ):
            raise forms.ValidationError("Please enter a street address.")

        return self.cleaned_data


    def save(self, user):
        address = super(AddressForm, self).save(commit=False)

        if address.pk is None:
            address.input_street = (
                address.parsed_street or address.edited_street)

        # default for new addresses, should be reset when an address is edited.
        address.geocode_failed = False
        address.save(user=user)

        return address



class AddressImportForm(forms.Form):
    file = forms.FileField()
    tag = forms.CharField()


    def clean_tag(self):
        tag = self.cleaned_data["tag"]
        if models.AddressBatch.objects.filter(tag=tag).exists():
            raise forms.ValidationError("This batch tag is already used.")
        return tag


    def save(self, user):
        i = CSVAddressImporter(
            timestamp=datetime.utcnow(),
            user=user,
            tag=self.cleaned_data["tag"])

        return i.process_file(self.cleaned_data["file"])



class LoadParcelsForm(forms.Form):
    shapefile = forms.FileField()


    def clean_shapefile(self):
        try:
            z = zipfile.ZipFile(self.cleaned_data["shapefile"], 'r')
        except zipfile.BadZipfile:
            raise forms.ValidationError(
                "Uploaded file is not a valid zip file.")

        shapefile_path = None
        target_dir = tempfile.mkdtemp(suffix="-mlt-parcel-shapefile")
        try:
            for name in z.namelist():
                if name.startswith(os.path.sep) or os.path.pardir in name:
                    raise forms.ValidationError(
                        "Zip file contains unsafe paths (absolute or with ..).")
                z.extract(name, target_dir)
                if name.endswith(".shp"):
                    shapefile_path = os.path.join(target_dir, name)

            if shapefile_path is None:
                raise forms.ValidationError(
                    "Unable to find a .shp file in uploaded zip file.")
        except forms.ValidationError:
            shutil.rmtree(target_dir)
            raise

        self.cleaned_data["target_dir"] = target_dir
        self.cleaned_data["shapefile_path"] = shapefile_path

        return self.cleaned_data["shapefile"]


    def save(self):
        return tasks.load_parcels_task.delay(
            self.cleaned_data["target_dir"],
            self.cleaned_data["shapefile_path"])
