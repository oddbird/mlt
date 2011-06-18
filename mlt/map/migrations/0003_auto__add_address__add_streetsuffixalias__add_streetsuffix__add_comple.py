# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Address'
        db.create_table('map_address', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('street_number', self.gf('django.db.models.fields.CharField')(max_length=50, db_index=True)),
            ('street_name', self.gf('django.db.models.fields.CharField')(max_length=100, db_index=True)),
            ('street_suffix', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['map.StreetSuffix'])),
            ('multi_units', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('city', self.gf('django.db.models.fields.CharField')(max_length=200, db_index=True)),
            ('state', self.gf('django.contrib.localflavor.us.models.USStateField')(max_length=2, db_index=True)),
            ('zip', self.gf('django.db.models.fields.CharField')(max_length=5, db_index=True)),
            ('complex', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['map.Complex'], null=True)),
            ('notes', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('pl', self.gf('django.db.models.fields.CharField')(max_length=8, db_index=True)),
            ('mapped_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name='addresses_mapped', null=True, to=orm['auth.User'])),
            ('mapped_timestamp', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('needs_review', self.gf('django.db.models.fields.BooleanField')(default=True, db_index=True)),
            ('imported_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name='addresses_imported', to=orm['auth.User'])),
            ('import_timestamp', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.utcnow)),
            ('import_source', self.gf('django.db.models.fields.CharField')(max_length=100, db_index=True)),
        ))
        db.send_create_signal('map', ['Address'])

        # Adding model 'StreetSuffixAlias'
        db.create_table('map_streetsuffixalias', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('suffix', self.gf('django.db.models.fields.related.ForeignKey')(related_name='aliases', to=orm['map.StreetSuffix'])),
            ('alias', self.gf('django.db.models.fields.CharField')(max_length=20)),
        ))
        db.send_create_signal('map', ['StreetSuffixAlias'])

        # Adding model 'StreetSuffix'
        db.create_table('map_streetsuffix', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('suffix', self.gf('django.db.models.fields.CharField')(max_length=20)),
        ))
        db.send_create_signal('map', ['StreetSuffix'])

        # Adding model 'Complex'
        db.create_table('map_complex', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=250)),
        ))
        db.send_create_signal('map', ['Complex'])


    def backwards(self, orm):
        
        # Deleting model 'Address'
        db.delete_table('map_address')

        # Deleting model 'StreetSuffixAlias'
        db.delete_table('map_streetsuffixalias')

        # Deleting model 'StreetSuffix'
        db.delete_table('map_streetsuffix')

        # Deleting model 'Complex'
        db.delete_table('map_complex')


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
            'city': ('django.db.models.fields.CharField', [], {'max_length': '200', 'db_index': 'True'}),
            'complex': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['map.Complex']", 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'import_source': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'import_timestamp': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow'}),
            'imported_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'addresses_imported'", 'to': "orm['auth.User']"}),
            'mapped_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'addresses_mapped'", 'null': 'True', 'to': "orm['auth.User']"}),
            'mapped_timestamp': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'multi_units': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'needs_review': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'pl': ('django.db.models.fields.CharField', [], {'max_length': '8', 'db_index': 'True'}),
            'state': ('django.contrib.localflavor.us.models.USStateField', [], {'max_length': '2', 'db_index': 'True'}),
            'street_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'street_number': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'street_suffix': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['map.StreetSuffix']"}),
            'zip': ('django.db.models.fields.CharField', [], {'max_length': '5', 'db_index': 'True'})
        },
        'map.complex': {
            'Meta': {'object_name': 'Complex'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250'})
        },
        'map.parcel': {
            'Meta': {'object_name': 'Parcel'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '27'}),
            'classcode': ('django.db.models.fields.CharField', [], {'max_length': '55'}),
            'first_owner': ('django.db.models.fields.CharField', [], {'max_length': '254'}),
            'geom': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pl': ('django.db.models.fields.CharField', [], {'max_length': '8'})
        },
        'map.streetsuffix': {
            'Meta': {'object_name': 'StreetSuffix'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'suffix': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'map.streetsuffixalias': {
            'Meta': {'object_name': 'StreetSuffixAlias'},
            'alias': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'suffix': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'aliases'", 'to': "orm['map.StreetSuffix']"})
        }
    }

    complete_apps = ['map']
