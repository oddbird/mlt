# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Changing field 'Parcel.geom'
        db.alter_column('map_parcel', 'geom', self.gf('django.contrib.gis.db.models.fields.MultiPolygonField')())


    def backwards(self, orm):
        
        # Changing field 'Parcel.geom'
        db.alter_column('map_parcel', 'geom', self.gf('django.contrib.gis.db.models.fields.PolygonField')(srid=3438))


    models = {
        'map.parcel': {
            'Meta': {'object_name': 'Parcel'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '27'}),
            'classcode': ('django.db.models.fields.CharField', [], {'max_length': '55'}),
            'first_owner': ('django.db.models.fields.CharField', [], {'max_length': '254'}),
            'geom': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pl': ('django.db.models.fields.CharField', [], {'max_length': '8'})
        }
    }

    complete_apps = ['map']
