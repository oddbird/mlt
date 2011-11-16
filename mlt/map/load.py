import datetime

from django.db import transaction

from django.contrib.gis.utils import LayerMapping

from .models import Parcel



parcel_mapping = {
    'pl' : 'PL',
    'address' : 'ADD',
    'first_owner' : 'FIRST_OWNE',
    'classcode' : 'CLASSCODE',
    'geom' : 'POLYGON',
    }



@transaction.commit_on_success
def load_parcels(shapefile_path, verbose=True):
    # monkeypatch no-op transaction handling into LayerMapping, as we
    # wrap it in a transaction including more operations.
    LayerMapping.TRANSACTION_MODES['none'] = lambda func: func

    # first delete existing parcels
    Parcel.objects.all().delete()

    lm = LayerMapping(
        get_parcel_proxy(datetime.datetime.utcnow()),
        shapefile_path, parcel_mapping, transform=True,
        transaction_mode='none')

    lm.save(strict=True, verbose=verbose)



def get_parcel_proxy(timestamp):
    """
    Return a dynamic proxy subclass of Parcel that automatically sets its own
    import_timestamp field to the given timestamp.

    Needed because LayerMapping doesn't allow us to pass in extra model data.

    """
    class ParcelProxy(Parcel):
        class Meta:
            proxy = True


        def save(self, *args, **kwargs):
            self.import_timestamp = timestamp
            super(ParcelProxy, self).save(*args, **kwargs)


    return ParcelProxy
