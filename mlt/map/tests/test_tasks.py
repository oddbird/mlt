from django.test import TestCase
from mock import patch



__all__ = ["LoadParcelsTaskTest"]



class LoadParcelsTaskTest(TestCase):
    @property
    def task(self):
        from mlt.map.tasks import load_parcels_task
        return load_parcels_task


    def test_basic(self):
        with patch("mlt.map.load.load_parcels") as load_parcels:
            with patch("mlt.map.tasks.shutil.rmtree") as rmtree:
                self.task.delay("target-dir", "shapefile-path")

        rmtree.assert_called_with("target-dir")
        args, kwargs = load_parcels.call_args
        self.assertEqual(args, ("shapefile-path",))
        self.assertEqual(kwargs["progress"], 1000)
        self.assertEqual(kwargs["verbose"], False)
        self.assertEqual(kwargs["silent"], True)
        from mlt.map.tasks import UpdateProgress
        self.assertIsInstance(kwargs["stream"], UpdateProgress)


    def test_update_progress(self):
        from mlt.map.tasks import UpdateProgress
        up = UpdateProgress()

        with patch("mlt.map.tasks.load_parcels_task.update_state") as update:
            up.write("something")

        update.assert_called_with(state="PROGRESS", meta="something")
