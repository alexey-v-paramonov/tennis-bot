# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Player.rank'
        db.add_column(u'tennis_player', 'rank',
                      self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0),
                      keep_default=False)

        # Adding field 'Player.points'
        db.add_column(u'tennis_player', 'points',
                      self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0),
                      keep_default=False)

        # Adding field 'Match.player0_rank'
        db.add_column(u'tennis_match', 'player0_rank',
                      self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0),
                      keep_default=False)

        # Adding field 'Match.player1_rank'
        db.add_column(u'tennis_match', 'player1_rank',
                      self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0),
                      keep_default=False)

        # Adding field 'Match.player0_points'
        db.add_column(u'tennis_match', 'player0_points',
                      self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0),
                      keep_default=False)

        # Adding field 'Match.player1_points'
        db.add_column(u'tennis_match', 'player1_points',
                      self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Player.rank'
        db.delete_column(u'tennis_player', 'rank')

        # Deleting field 'Player.points'
        db.delete_column(u'tennis_player', 'points')

        # Deleting field 'Match.player0_rank'
        db.delete_column(u'tennis_match', 'player0_rank')

        # Deleting field 'Match.player1_rank'
        db.delete_column(u'tennis_match', 'player1_rank')

        # Deleting field 'Match.player0_points'
        db.delete_column(u'tennis_match', 'player0_points')

        # Deleting field 'Match.player1_points'
        db.delete_column(u'tennis_match', 'player1_points')


    models = {
        u'tennis.bet': {
            'Meta': {'unique_together': "(('match', 'set', 'game', 'selection'),)", 'object_name': 'Bet'},
            'game': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'match': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'match_bets'", 'to': u"orm['tennis.Match']"}),
            'odd': ('django.db.models.fields.FloatField', [], {'default': '0.0', 'null': 'True'}),
            'retries_num': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'selection': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'serie': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'serie_bets'", 'null': 'True', 'to': u"orm['tennis.BetSerie']"}),
            'serie_step': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'set': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'stake': ('django.db.models.fields.FloatField', [], {'default': '0.0', 'null': 'True'}),
            'status': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'ts_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'winner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'won_bets'", 'null': 'True', 'to': u"orm['tennis.Player']"}),
            'winner_data1': ('jsonfield.fields.JSONField', [], {'default': '{}', 'null': 'True'}),
            'winner_data1_recent': ('jsonfield.fields.JSONField', [], {'default': '{}', 'null': 'True'}),
            'winner_data1_surface': ('jsonfield.fields.JSONField', [], {'default': '{}', 'null': 'True'}),
            'winner_data2': ('jsonfield.fields.JSONField', [], {'default': '{}', 'null': 'True'}),
            'winner_data2_recent': ('jsonfield.fields.JSONField', [], {'default': '{}', 'null': 'True'}),
            'winner_data2_surface': ('jsonfield.fields.JSONField', [], {'default': '{}', 'null': 'True'})
        },
        u'tennis.betserie': {
            'Meta': {'object_name': 'BetSerie'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'tennis.country': {
            'Meta': {'object_name': 'Country'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        u'tennis.countryalias': {
            'Meta': {'object_name': 'CountryAlias'},
            'alias': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'aliases'", 'to': u"orm['tennis.Country']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
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
            'bet_status': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'consistent': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'finished': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'player0': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': u"orm['tennis.Player']"}),
            'player0_max_live_odd': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'player0_odd': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'player0_points': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'player0_rank': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'player1': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': u"orm['tennis.Player']"}),
            'player1_max_live_odd': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'player1_odd': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'player1_points': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'player1_rank': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'singles': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'start_ts': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'started': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'tournament': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'matches'", 'to': u"orm['tennis.Tournament']"}),
            'void': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'wh_match_id': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'winner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'matches_won'", 'null': 'True', 'to': u"orm['tennis.Player']"}),
            'winner_data1': ('jsonfield.fields.JSONField', [], {'default': '{}', 'null': 'True'}),
            'winner_data1_recent': ('jsonfield.fields.JSONField', [], {'default': '{}', 'null': 'True'}),
            'winner_data1_recent_size': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'winner_data1_size': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'winner_data1_surface': ('jsonfield.fields.JSONField', [], {'default': '{}', 'null': 'True'}),
            'winner_data1_surface_size': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'winner_data2': ('jsonfield.fields.JSONField', [], {'default': '{}', 'null': 'True'}),
            'winner_data2_recent': ('jsonfield.fields.JSONField', [], {'default': '{}', 'null': 'True'}),
            'winner_data2_recent_size': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'winner_data2_size': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'winner_data2_surface': ('jsonfield.fields.JSONField', [], {'default': '{}', 'null': 'True'}),
            'winner_data2_surface_size': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        },
        u'tennis.player': {
            'Meta': {'object_name': 'Player'},
            'country': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'players'", 'null': 'True', 'to': u"orm['tennis.Country']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'points': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'rank': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'})
        },
        u'tennis.point': {
            'Meta': {'ordering': "['number']", 'unique_together': "[('game', 'number', 'player')]", 'object_name': 'Point'},
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
            'country': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tournaments'", 'null': 'True', 'to': u"orm['tennis.Country']"}),
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