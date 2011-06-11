from django.contrib.gis.utils import LayerMapping

from .models import Parcel



parcel_mapping = {
    'pl' : 'PL',
    'address' : 'ADD',
    'first_owner' : 'FIRST_OWNE',
    'classcode' : 'CLASSCODE',
    'geom' : 'POLYGON',
    }



def load(shapefile_path, verbose=True):
    lm = LayerMapping(
        Parcel, shapefile_path, parcel_mapping, transform=False)

    lm.save(strict=True, verbose=verbose)
