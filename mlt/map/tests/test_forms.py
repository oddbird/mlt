from cStringIO import StringIO
from datetime import datetime
import shutil
import tempfile
import os
import zipfile

from mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from .backports import override_settings
from .utils import create_user, create_address, create_address_batch



__all__ = ["AddressFormTest", "AddressImportFormTest", "LoadParcelsFormTest"]



class AddressImportFormTest(TestCase):
    def setUp(self):
        self.user = create_user()


    @property
    def form(self):
        from mlt.map.forms import AddressImportForm
        return AddressImportForm


    def test_fields(self):
        self.assertEqual(
            [f.name for f in self.form()],
            ["file", "tag"]
            )


    def test_save(self):
        f = self.form(
            data={"tag": "mytag"},
            files={"file": SimpleUploadedFile(
                    "data.csv", "123 N Main St, Providence, RI")})

        self.assertTrue(f.is_valid(), f.errors)
        with patch("mlt.map.forms.datetime") as mock:
            mock.now.return_value = datetime(2011, 7, 8, 1, 2, 3)
            self.assertEqual(f.save(self.user), (1, 0))
        from mlt.map.models import Address
        self.assertEqual(Address.objects.count(), 1)
        a = Address.objects.get()
        self.assertEqual(a.street, "123 N Main St")
        self.assertEqual(a.city, "Providence")
        self.assertEqual(a.state, "RI")

        batches = a.batches.all()
        self.assertEqual(len(batches), 1)

        batch = batches[0]

        self.assertEqual(batch.user, self.user)
        self.assertEqual(batch.timestamp, datetime(2011, 7, 8, 1, 2, 3))
        self.assertEqual(batch.tag, "mytag")


    def test_dupe_batch_name(self):
        create_address_batch(tag="mytag")

        f = self.form(
            data={"tag": "mytag"},
            files={"file": SimpleUploadedFile(
                    "data.csv", "123 N Main St, Providence, RI")})

        self.assertFalse(f.is_valid())
        self.assertEqual(
            f.errors, {"tag": ["This batch tag is already used."]})


class AddressFormTest(TestCase):
    @property
    def form(self):
        from mlt.map.forms import AddressForm
        return AddressForm


    @override_settings(MLT_DEFAULT_STATE="SD")
    def test_default_state(self):
        f = self.form()

        self.assertEqual(f.fields["state"].initial, "SD")


    @override_settings(MLT_DEFAULT_STATE=None)
    def test_no_default_state(self):
        f = self.form()

        self.assertEqual(f.fields["state"].initial, None)


    def test_fields(self):
        self.assertEqual(
            [f.name for f in self.form()],
            [
                "street_prefix", "street_number", "street_name", "street_type",
                "street_suffix", "edited_street",
                "city", "state", "multi_units",
                "complex_name", "notes"
                ]
            )


    def test_create(self):
        u = create_user(username="blametern")
        f = self.form(
            {
                "street_number": "3635",
                "street_name": "Van Gordon",
                "street_type": "St",
                "edited_street": "",
                "city": "Providence",
                "state": "RI",
                "multi_units": 1,
                "complex_name": "The Van Gordon Building",
                "notes": "some notes",
                })

        self.assertTrue(f.is_valid())

        with patch("mlt.map.forms.datetime") as mockdt:
            mockdt.now.return_value = datetime(2011, 6, 17, 10, 14, 25)
            a = f.save(u)

        self.assertEqual(a.street_number, "3635")
        self.assertEqual(a.street_name, "Van Gordon")
        self.assertEqual(a.street_type, "St")
        self.assertEqual(a.input_street, "3635 Van Gordon St")
        self.assertEqual(a.parsed_street, "3635 Van Gordon St")
        self.assertEqual(a.edited_street, "")
        self.assertEqual(a.notes, "some notes")
        self.assertEqual(a.complex_name, "The Van Gordon Building")
        self.assertEqual(a.multi_units, True)

        self.assertEqual(a.batches.count(), 0)


    def test_create_no_street(self):
        f = self.form(
            {
                "street_number": "3635",
                "street_name": "",
                "street_type": "St",
                "edited_street": "",
                "city": "Providence",
                "state": "RI",
                "multi_units": 1,
                "complex_name": "The Van Gordon Building",
                "notes": "some notes",
                })

        self.assertFalse(f.is_valid())
        self.assertEqual(
            f.errors, {'__all__': [u'Please enter a street address.']})


    def test_edit(self):
        a = create_address(
            street_number="1234",
            street_name="Van Heusen",
            street_type="Ave",
            city="Albuquerque",
            state="NM",
            multi_units=False,
            complex_name="",
            notes="",
            )

        u2 = create_user(username="blametern")
        f = self.form(
            {
                "street_number": "3635",
                "street_name": "Van Gordon",
                "street_type": "St",
                "city": "Providence",
                "state": "RI",
                "multi_units": 1,
                "complex_name": "The Van Gordon Building",
                "notes": "some notes",
                },
            instance=a)

        self.assertTrue(f.is_valid())

        a = f.save(u2)

        self.assertEqual(a.street_number, "3635")
        self.assertEqual(a.street_name, "Van Gordon")
        self.assertEqual(a.street_type, "St")
        self.assertEqual(a.input_street, "3635 Van Gordon St")
        self.assertEqual(a.parsed_street, "3635 Van Gordon St")
        self.assertEqual(a.notes, "some notes")
        self.assertEqual(a.complex_name, "The Van Gordon Building")
        self.assertEqual(a.multi_units, True)


    def test_edit_unparsed(self):
        a = create_address(
            street_prefix="",
            street_number="",
            street_name="",
            street_type="",
            street_suffix="",
            input_street="123 Main St",
            city="Albuquerque",
            state="NM",
            multi_units=False,
            complex_name="",
            notes="",
            )

        u2 = create_user(username="blametern")
        f = self.form(
            {
                "edited_street": "3635 Van Gordon St",
                "city": "Providence",
                "state": "RI",
                "multi_units": 1,
                "complex_name": "The Van Gordon Building",
                "notes": "some notes",
                },
            instance=a)

        self.assertTrue(f.is_valid())

        a = f.save(u2)

        self.assertEqual(a.street_prefix, "")
        self.assertEqual(a.street_number, "")
        self.assertEqual(a.street_name, "")
        self.assertEqual(a.street_type, "")
        self.assertEqual(a.street_suffix, "")
        self.assertEqual(a.edited_street, "3635 Van Gordon St")
        self.assertEqual(a.input_street, "123 Main St")
        self.assertEqual(a.parsed_street, "")
        self.assertEqual(a.notes, "some notes")
        self.assertEqual(a.complex_name, "The Van Gordon Building")
        self.assertEqual(a.multi_units, True)


    def test_edit_no_street(self):
        a = create_address(
            street_prefix="",
            street_number="",
            street_name="",
            street_type="",
            street_suffix="",
            input_street="123 Main St",
            city="Albuquerque",
            state="NM",
            multi_units=False,
            complex_name="",
            notes="",
            )

        f = self.form(
            {
                "street_name": "",
                "edited_street": "",
                "city": "Providence",
                "state": "RI",
                "multi_units": 1,
                "complex_name": "The Van Gordon Building",
                "notes": "some notes",
                },
            instance=a)

        self.assertFalse(f.is_valid())
        self.assertEqual(
            f.errors, {'__all__': [u'Please enter a street address.']})



def zipstream(files):
    """
    Given a dictionary mapping file names to content buffers, return a StringIO
    instance containing a zipfile made up of those contents.

    """
    stream = StringIO()
    z = zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED)
    for filename, contents in files.items():
        z.writestr(filename, contents)
    z.close()
    stream.seek(0)
    return stream



class LoadParcelsFormTest(TestCase):
    @property
    def form(self):
        from mlt.map.forms import LoadParcelsForm
        return LoadParcelsForm


    def setUp(self):
        self.target_dir = tempfile.mkdtemp(prefix="-mlt-load-parcel-test")
        self.addCleanup(self._remove_target_dir)


    def _remove_target_dir(self):
        if os.path.exists(self.target_dir):
            shutil.rmtree(self.target_dir)


    def _is_valid(self, form):
        with patch("mlt.map.forms.tempfile.mkdtemp") as mock_mkdtemp:
            mock_mkdtemp.return_value = self.target_dir
            return form.is_valid()


    def test_bad_zipfile(self):
        f = self.form(
            data={},
            files={"shapefile": SimpleUploadedFile(
                    "some.zip", "not really a zip file", "application/zip")})

        self.assertFalse(self._is_valid(f))

        self.assertEqual(
            f.errors,
            {"shapefile": ["Uploaded file is not a valid zip file."]}
            )


    def test_no_shp_in_zipfile(self):

        f = self.form(
            data={},
            files={
                "shapefile": SimpleUploadedFile(
                    "parcels.zip",
                    zipstream({"parcels/parcels.prj": ""}).read(),
                    "application/zip"
                    )
                }
            )

        self.assertFalse(self._is_valid(f))

        self.assertEqual(
            f.errors,
            {"shapefile": ["Unable to find a .shp file in uploaded zip file."]})
        # form cleans up after itself
        self.assertFalse(os.path.exists(self.target_dir))


    def test_absolute_path_in_zipfile(self):
        f = self.form(
            data={},
            files={
                "shapefile": SimpleUploadedFile(
                    "parcels.zip",
                    zipstream({"/parcels/parcels.prj": ""}).read(),
                    "application/zip"
                    )
                }
            )

        self.assertFalse(self._is_valid(f))

        self.assertEqual(
            f.errors,
            {"shapefile": [
                    "Zip file contains unsafe paths (absolute or with ..)."]})
        # form cleans up after itself
        self.assertFalse(os.path.exists(self.target_dir))


    def test_valid(self):
        f = self.form(
            data={},
            files={
                "shapefile": SimpleUploadedFile(
                    "parcels.zip",
                    zipstream({"parcels/parcels.shp": ""}).read(),
                    "application/zip"
                    )
                }
            )

        self.assertTrue(self._is_valid(f))

        self.assertEqual(f.cleaned_data["target_dir"], self.target_dir)
        shapefile_path = os.path.join(self.target_dir, "parcels/parcels.shp")
        self.assertEqual(f.cleaned_data["shapefile_path"], shapefile_path)

        self.assertTrue(os.path.isdir(self.target_dir))
        self.assertTrue(os.path.isfile(shapefile_path))


    def test_save(self):
        f = self.form(
            data={},
            files={
                "shapefile": SimpleUploadedFile(
                    "parcels.zip",
                    zipstream({"parcels/parcels.shp": ""}).read(),
                    "application/zip"
                    )
                }
            )

        self.assertTrue(self._is_valid(f))

        with patch("mlt.map.forms.tasks.load_parcels_task.delay") as task_delay:
            ret = f.save()

        task_delay.assert_called_with(
            f.cleaned_data["target_dir"], f.cleaned_data["shapefile_path"])
        self.assertIs(ret, task_delay.return_value)
