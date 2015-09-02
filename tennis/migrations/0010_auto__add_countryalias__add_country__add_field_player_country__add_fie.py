# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'CountryAlias'
        db.create_table(u'tennis_countryalias', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('country', self.gf('django.db.models.fields.related.ForeignKey')(related_name='aliases', to=orm['tennis.Country'])),
            ('alias', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
        ))
        db.send_create_signal(u'tennis', ['CountryAlias'])

        # Adding model 'Country'
        db.create_table(u'tennis_country', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
        ))
        db.send_create_signal(u'tennis', ['Country'])

        # Adding field 'Player.country'
        db.add_column(u'tennis_player', 'country',
                      self.gf('django.db.models.fields.related.ForeignKey')(related_name='players', null=True, to=orm['tennis.Country']),
                      keep_default=False)

        # Adding field 'Tournament.country'
        db.add_column(u'tennis_tournament', 'country',
                      self.gf('django.db.models.fields.related.ForeignKey')(related_name='tournaments', null=True, to=orm['tennis.Country']),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting model 'CountryAlias'
        db.delete_table(u'tennis_countryalias')

        # Deleting model 'Country'
        db.delete_table(u'tennis_country')

        # Deleting field 'Player.country'
        db.delete_column(u'tennis_player', 'country_id')

        # Deleting field 'Tournament.country'
        db.delete_column(u'tennis_tournament', 'country_id')


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
            'player1': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': u"orm['tennis.Player']"}),
            'player1_max_live_odd': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'player1_odd': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
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
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
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