# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Changing field 'Address.complex_name'
        db.alter_column('map_address', 'complex_name', self.gf('mlt.map.fields.CICharField')(max_length=250))

        # Changing field 'AddressSnapshot.complex_name'
        db.alter_column('map_addresssnapshot', 'complex_name', self.gf('mlt.map.fields.CICharField')(max_length=250))


    def backwards(self, orm):
        
        # Changing field 'Address.complex_name'
        db.alter_column('map_address', 'complex_name', self.gf('django.db.models.fields.CharField')(max_length=250))

        # Changing field 'AddressSnapshot.complex_name'
        db.alter_column('map_addresssnapshot', 'complex_name', self.gf('django.db.models.fields.CharField')(max_length=250))


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'map.address': {
            'Meta': {'object_name': 'Address'},
            'batches': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'addresses'", 'symmetrical': 'False', 'to': "orm['map.AddressBatch']"}),
            'city': ('mlt.map.fields.CICharField', [], {'max_length': '200', 'db_index': 'True'}),
            'complex_name': ('mlt.map.fields.CICharField', [], {'max_length': '250', 'blank': 'True'}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'edited_street': ('mlt.map.fields.CICharField', [], {'max_length': '200', 'blank': 'True'}),
            'geocode_failed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'geocoded': ('django.contrib.gis.db.models.fields.PointField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'input_street': ('mlt.map.fields.CICharField', [], {'max_length': '200', 'db_index': 'True'}),
            'mapped_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'address_mapped'", 'null': 'True', 'to': "orm['auth.User']"}),
            'mapped_timestamp': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'multi_units': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'needs_review': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'pl': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '8', 'blank': 'True'}),
            'state': ('django.contrib.localflavor.us.models.USStateField', [], {'max_length': '2', 'db_index': 'True'}),
            'street': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '200', 'blank': 'True'}),
            'street_name': ('mlt.map.fields.CICharField', [], {'max_length': '100', 'blank': 'True'}),
            'street_number': ('mlt.map.fields.CICharField', [], {'max_length': '50', 'blank': 'True'}),
            'street_prefix': ('mlt.map.fields.CICharField', [], {'max_length': '20', 'blank': 'True'}),
            'street_suffix': ('mlt.map.fields.CICharField', [], {'max_length': '20', 'blank': 'True'}),
            'street_type': ('mlt.map.fields.CICharField', [], {'max_length': '20', 'blank': 'True'})
        },
        'map.addressbatch': {
            'Meta': {'object_name': 'AddressBatch'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tag': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'address_batches'", 'to': "orm['auth.User']"})
        },
        'map.addresschange': {
            'Meta': {'object_name': 'AddressChange'},
            'address': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'address_changes'", 'to': "orm['map.Address']"}),
            'changed_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'address_changes'", 'to': "orm['auth.User']"}),
            'changed_timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'post': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'post_for'", 'null': 'True', 'to': "orm['map.AddressSnapshot']"}),
            'pre': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pre_for'", 'null': 'True', 'to': "orm['map.AddressSnapshot']"})
        },
        'map.addresssnapshot': {
            'Meta': {'object_name': 'AddressSnapshot'},
            'city': ('mlt.map.fields.CICharField', [], {'max_length': '200', 'db_index': 'True'}),
            'complex_name': ('mlt.map.fields.CICharField', [], {'max_length': '250', 'blank': 'True'}),
            'edited_street': ('mlt.map.fields.CICharField', [], {'max_length': '200', 'blank': 'True'}),
            'geocoded': ('django.contrib.gis.db.models.fields.PointField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'input_street': ('mlt.map.fields.CICharField', [], {'max_length': '200', 'db_index': 'True'}),
            'mapped_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'addresssnapshot_mapped'", 'null': 'True', 'to': "orm['auth.User']"}),
            'mapped_timestamp': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'multi_units': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'needs_review': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'pl': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '8', 'blank': 'True'}),
            'snapshot_timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'state': ('django.contrib.localflavor.us.models.USStateField', [], {'max_length': '2', 'db_index': 'True'}),
            'street': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '200', 'blank': 'True'}),
            'street_name': ('mlt.map.fields.CICharField', [], {'max_length': '100', 'blank': 'True'}),
            'street_number': ('mlt.map.fields.CICharField', [], {'max_length': '50', 'blank': 'True'}),
            'street_prefix': ('mlt.map.fields.CICharField', [], {'max_length': '20', 'blank': 'True'}),
            'street_suffix': ('mlt.map.fields.CICharField', [], {'max_length': '20', 'blank': 'True'}),
            'street_type': ('mlt.map.fields.CICharField', [], {'max_length': '20', 'blank': 'True'})
        },
        'map.parcel': {
            'Meta': {'unique_together': "[('pl', 'import_timestamp')]", 'object_name': 'Parcel'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '27'}),
            'classcode': ('django.db.models.fields.CharField', [], {'max_length': '55'}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'first_owner': ('django.db.models.fields.CharField', [], {'max_length': '254'}),
            'geom': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'import_timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'pl': ('django.db.models.fields.CharField', [], {'max_length': '8'})
        }
    }

    complete_apps = ['map']
