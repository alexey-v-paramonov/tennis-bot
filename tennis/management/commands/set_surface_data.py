import random
import datetime
from django.core.management import BaseCommand
from django.db.transaction import commit_on_success
from django.conf import settings
from django.db.models import Q
from django.core.serializers import json

from tennis.models import (
    Bet,
    BetSelection,
    SurfaceType,
    HARDS,
    CLAYS,
    GRASS,
    Match
)


class Command(BaseCommand):

    requires_model_validation = True

    @commit_on_success
    def handle(self, *args, **options):
        ts = datetime.date(2015, 1, 1)
        matches = Match.objects.filter(start_ts__gte=ts).order_by('start_ts')
        c = 0
        for m in matches:

            c += 1
            if m.tournament.surface in HARDS:
                target_surfaces = HARDS
            elif m.tournament.surface in CLAYS:
                target_surfaces = CLAYS
            elif m.tournament.surface in GRASS:
                target_surfaces = GRASS
            else:
                print "Unknown surface: ", m.pk, m.tournament.surface
                continue

            d1_s = m.player0.get_winner_data(m.start_ts, target_surfaces)
            d2_s = m.player1.get_winner_data(m.start_ts, target_surfaces)

            m.winner_data1_surface = d1_s
            m.winner_data2_surface = d2_s

            m.winner_data1_surface_size = d1_s.get('num_games', 0)
            m.winner_data2_surface_size = d2_s.get('num_games', 0)

            m.save()
            print "%d of %d done" % (c, len(matches)), m.start_ts

        return "OK"
