# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models
from django.conf import settings

from django.contrib.gis.geos import MultiPolygon

class Migration(DataMigration):

    def forwards(self, orm):
        for g in orm.Geometry.objects.all().iterator():
            g.areas.add( g.area )
            g.save()

    def backwards(self, orm):
        # Going backwards, we're moving from the situation where a
        # geometry can be in multiple areas, to only being in a single
        # area.  Please note that this isn't guaranteed to recreate
        # exactly the same areas and geometries after going forwards
        # and backwards through this migration, but for most purposes
        # it'll be functionally the same.
        for a in orm.Area.objects.all():
            # Find any Geometry where area was set to this area, and
            # set its area to NULL.  This won't be necessary if you've
            # just migrated backwards through 0007, but there might be
            # some if you've just migrated forward to 0006:
            a.polygons.clear()
            # We want to duplicate every geometry associated with the
            # area, and set this area on it - we duplicate them
            # because any given geometry might be associated with
            # other areas too.
            polygons_to_duplicate = [g.polygon for g in a.geometries.all()]
            # However, it's quite possible that these geometries are
            # adjacent, so do a cascaded union of them to simplify the
            # number of polygons used.  (Unfortunately, we can't just
            # do unionagg on the query set, because with South's
            # unfrozen models it's a QuerySet, not a GeoQuerySet.)
            mp = MultiPolygon(polygons_to_duplicate)
            unioned = mp.cascaded_union
            if unioned.geom_type == 'Polygon':
                unioned = [unioned]
            for polygon in unioned:
                a.polygons.create(polygon=polygon)
        # Now remove any geometries that have area_id set to NULL -
        # these will be those only associated with areas via the old
        # join table.
        orm.Geometry.objects.filter(area=None).delete()

    models = {
        'mapit.area': {
            'Meta': {'object_name': 'Area'},
            'country': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'areas'", 'null': 'True', 'to': "orm['mapit.Country']"}),
            'generation_high': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'final_areas'", 'null': 'True', 'to': "orm['mapit.Generation']"}),
            'generation_low': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'new_areas'", 'null': 'True', 'to': "orm['mapit.Generation']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'parent_area': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['mapit.Area']"}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'areas'", 'to': "orm['mapit.Type']"})
        },
        'mapit.code': {
            'Meta': {'unique_together': "(('area', 'type'),)", 'object_name': 'Code'},
            'area': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'codes'", 'to': "orm['mapit.Area']"}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'codes'", 'to': "orm['mapit.CodeType']"})
        },
        'mapit.codetype': {
            'Meta': {'object_name': 'CodeType'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '10'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'mapit.country': {
            'Meta': {'object_name': 'Country'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        },
        'mapit.generation': {
            'Meta': {'object_name': 'Generation'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'mapit.geometry': {
            'Meta': {'object_name': 'Geometry'},
            'area': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'polygons'", 'null': 'True', 'to': "orm['mapit.Area']"}),
            'areas': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'geometries'", 'symmetrical': 'False', 'to': "orm['mapit.Area']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'polygon': ('django.contrib.gis.db.models.fields.PolygonField', [], {'srid': str(settings.MAPIT_AREA_SRID)})
        },
        'mapit.name': {
            'Meta': {'unique_together': "(('area', 'type'),)", 'object_name': 'Name'},
            'area': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'names'", 'to': "orm['mapit.Area']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'names'", 'to': "orm['mapit.NameType']"})
        },
        'mapit.nametype': {
            'Meta': {'object_name': 'NameType'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '10'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'mapit.postcode': {
            'Meta': {'object_name': 'Postcode'},
            'areas': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'postcodes'", 'blank': 'True', 'to': "orm['mapit.Area']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.contrib.gis.db.models.fields.PointField', [], {'null': 'True'}),
            'postcode': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '7', 'db_index': 'True'})
        },
        'mapit.type': {
            'Meta': {'object_name': 'Type'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '3'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['mapit']
