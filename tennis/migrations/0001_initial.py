# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Player'
        db.create_table(u'tennis_player', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
        ))
        db.send_create_signal(u'tennis', ['Player'])

        # Adding model 'Tournament'
        db.create_table(u'tennis_tournament', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255, null=True)),
            ('date_start', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('date_finish', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('association', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=3)),
            ('surface', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=6)),
            ('rank', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0)),
        ))
        db.send_create_signal(u'tennis', ['Tournament'])

        # Adding unique constraint on 'Tournament', fields ['title', 'association']
        db.create_unique(u'tennis_tournament', ['title', 'association'])

        # Adding model 'Match'
        db.create_table(u'tennis_match', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('tournament', self.gf('django.db.models.fields.related.ForeignKey')(related_name='matches', to=orm['tennis.Tournament'])),
            ('player0', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', to=orm['tennis.Player'])),
            ('player1', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', to=orm['tennis.Player'])),
            ('winner', self.gf('django.db.models.fields.related.ForeignKey')(related_name='matches_won', null=True, to=orm['tennis.Player'])),
            ('start_ts', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('singles', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('consistent', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('started', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('finished', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('wh_match_id', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
        ))
        db.send_create_signal(u'tennis', ['Match'])

        # Adding unique constraint on 'Match', fields ['tournament', 'player0', 'player1', 'wh_match_id']
        db.create_unique(u'tennis_match', ['tournament_id', 'player0_id', 'player1_id', 'wh_match_id'])

        # Adding model 'Set'
        db.create_table(u'tennis_set', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('match', self.gf('django.db.models.fields.related.ForeignKey')(related_name='sets', to=orm['tennis.Match'])),
            ('number', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=1)),
        ))
        db.send_create_signal(u'tennis', ['Set'])

        # Adding unique constraint on 'Set', fields ['match', 'number']
        db.create_unique(u'tennis_set', ['match_id', 'number'])

        # Adding model 'Game'
        db.create_table(u'tennis_game', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('set', self.gf('django.db.models.fields.related.ForeignKey')(related_name='games', to=orm['tennis.Set'])),
            ('number', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=1)),
            ('server', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', to=orm['tennis.Player'])),
            ('receiver', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', to=orm['tennis.Player'])),
        ))
        db.send_create_signal(u'tennis', ['Game'])

        # Adding unique constraint on 'Game', fields ['set', 'number', 'server', 'receiver']
        db.create_unique(u'tennis_game', ['set_id', 'number', 'server_id', 'receiver_id'])

        # Adding model 'Point'
        db.create_table(u'tennis_point', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('game', self.gf('django.db.models.fields.related.ForeignKey')(related_name='points', to=orm['tennis.Game'])),
            ('player', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', to=orm['tennis.Player'])),
            ('number', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('ace', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('dbl', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'tennis', ['Point'])

        # Adding unique constraint on 'Point', fields ['game', 'number', 'player', 'ace', 'dbl']
        db.create_unique(u'tennis_point', ['game_id', 'number', 'player_id', 'ace', 'dbl'])


    def backwards(self, orm):
        # Removing unique constraint on 'Point', fields ['game', 'number', 'player', 'ace', 'dbl']
        db.delete_unique(u'tennis_point', ['game_id', 'number', 'player_id', 'ace', 'dbl'])

        # Removing unique constraint on 'Game', fields ['set', 'number', 'server', 'receiver']
        db.delete_unique(u'tennis_game', ['set_id', 'number', 'server_id', 'receiver_id'])

        # Removing unique constraint on 'Set', fields ['match', 'number']
        db.delete_unique(u'tennis_set', ['match_id', 'number'])

        # Removing unique constraint on 'Match', fields ['tournament', 'player0', 'player1', 'wh_match_id']
        db.delete_unique(u'tennis_match', ['tournament_id', 'player0_id', 'player1_id', 'wh_match_id'])

        # Removing unique constraint on 'Tournament', fields ['title', 'association']
        db.delete_unique(u'tennis_tournament', ['title', 'association'])

        # Deleting model 'Player'
        db.delete_table(u'tennis_player')

        # Deleting model 'Tournament'
        db.delete_table(u'tennis_tournament')

        # Deleting model 'Match'
        db.delete_table(u'tennis_match')

        # Deleting model 'Set'
        db.delete_table(u'tennis_set')

        # Deleting model 'Game'
        db.delete_table(u'tennis_game')

        # Deleting model 'Point'
        db.delete_table(u'tennis_point')


    models = {
        u'tennis.game': {
            'Meta': {'ordering': "['number']", 'unique_together': "[('set', 'number', 'server', 'receiver')]", 'object_name': 'Game'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'receiver': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': u"orm['tennis.Player']"}),
            'server': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': u"orm['tennis.Player']"}),
            'set': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'games'", 'to': u"orm['tennis.Set']"})
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
            'number': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'})
        },
        u'tennis.tournament': {
            'Meta': {'unique_together': "[('title', 'association')]", 'object_name': 'Tournament'},
            'association': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '3'}),
            'date_finish': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'date_start': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rank': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'surface': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '6'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'})
        }
    }

    complete_apps = ['tennis']