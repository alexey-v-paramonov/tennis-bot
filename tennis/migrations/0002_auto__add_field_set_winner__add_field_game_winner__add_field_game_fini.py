# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Set.winner'
        db.add_column(u'tennis_set', 'winner',
                      self.gf('django.db.models.fields.related.ForeignKey')(related_name='sets_won', null=True, to=orm['tennis.Player']),
                      keep_default=False)

        # Adding field 'Game.winner'
        db.add_column(u'tennis_game', 'winner',
                      self.gf('django.db.models.fields.related.ForeignKey')(related_name='games_won', null=True, to=orm['tennis.Player']),
                      keep_default=False)

        # Adding field 'Game.finished'
        db.add_column(u'tennis_game', 'finished',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'Tournament.gender'
        db.add_column(u'tennis_tournament', 'gender',
                      self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0),
                      keep_default=False)

        # Adding field 'Tournament.qualifying'
        db.add_column(u'tennis_tournament', 'qualifying',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Set.winner'
        db.delete_column(u'tennis_set', 'winner_id')

        # Deleting field 'Game.winner'
        db.delete_column(u'tennis_game', 'winner_id')

        # Deleting field 'Game.finished'
        db.delete_column(u'tennis_game', 'finished')

        # Deleting field 'Tournament.gender'
        db.delete_column(u'tennis_tournament', 'gender')

        # Deleting field 'Tournament.qualifying'
        db.delete_column(u'tennis_tournament', 'qualifying')


    models = {
        u'tennis.game': {
            'Meta': {'ordering': "['number']", 'unique_together': "[('set', 'number', 'server', 'receiver')]", 'object_name': 'Game'},
            'finished': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'receiver': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': u"orm['tennis.Player']"}),
            'server': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': u"orm['tennis.Player']"}),
            'set': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'games'", 'to': u"orm['tennis.Set']"}),
            'winner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'games_won'", 'null': 'True', 'to': u"orm['tennis.Player']"})
        },
        u'tennis.match': {
            'Meta': {'unique_together': "[('tournament', 'player0', 'player1', 'wh_match_id')]", 'object_name': 'Match'},
            'consistent': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'finished': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'player0': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': u"orm['tennis.Player']"}),
            'player1': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': u"orm['tennis.Player']"}),
            'singles': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'start_ts': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'started': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'tournament': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'matches'", 'to': u"orm['tennis.Tournament']"}),
            'wh_match_id': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'winner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'matches_won'", 'null': 'True', 'to': u"orm['tennis.Player']"})
        },
        u'tennis.player': {
            'Meta': {'object_name': 'Player'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        u'tennis.point': {
            'Meta': {'ordering': "['number']", 'unique_together': "[('game', 'number', 'player', 'ace', 'dbl')]", 'object_name': 'Point'},
            'ace': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'dbl': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'game': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'points'", 'to': u"orm['tennis.Game']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'player': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': u"orm['tennis.Player']"})
        },
        u'tennis.set': {
            'Meta': {'ordering': "['number']", 'unique_together': "[('match', 'number')]", 'object_name': 'Set'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'match': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sets'", 'to': u"orm['tennis.Match']"}),
            'number': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'winner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sets_won'", 'null': 'True', 'to': u"orm['tennis.Player']"})
        },
        u'tennis.tournament': {
            'Meta': {'unique_together': "[('title', 'association')]", 'object_name': 'Tournament'},
            'association': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '3'}),
            'date_finish': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'date_start': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'qualifying': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'rank': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'surface': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '6'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'})
        }
    }

    complete_apps = ['tennis']