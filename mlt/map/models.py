from django.contrib.gis.db import models



class Parcel(models.Model):
    pl = models.CharField(max_length=8)
    address = models.CharField(max_length=27)
    first_owner = models.CharField(max_length=254)
    classcode = models.CharField(max_length=55)
    geom = models.MultiPolygonField(srid=3438)

    objects = models.GeoManager()


    def __unicode__(self):
        return self.pl
