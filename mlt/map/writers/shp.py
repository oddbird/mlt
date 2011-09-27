from .base import AddressWriter



class SHPWriter(AddressWriter):
    mimetype = "application/shapefile"
    extension = "shp"


    def save(self, stream):
        pass
