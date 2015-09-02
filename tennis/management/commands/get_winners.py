# -*- coding: utf-8 -*-
import requests
import threading
import random
import time
import re
import os
import datetime
from bs4 import BeautifulSoup
import requests

import xml.etree.ElementTree as ET

from django.core.management import BaseCommand
from django.conf import settings
from django.db.models import Q
from django.db import transaction
from django.db import IntegrityError

from tennis.models import (
    Tournament,
    AssociationType,
    Player,
    Match,
    Set,
    Game,
    Point,
    Gender
)


def getResult(b_type, rows, m):

    got_res = False
    i = 0

    player0 = 1
    player1 = 2
    void = 0

    for row in rows:
        i += 1
        td = row.findAll('td')
        if td:
            h_td = td[0]
            if h_td.text.strip().lower() == b_type.strip().lower():
                t = td[2].text.strip()
                if t.lower().find(m.player0.getName().lower()) >= 0:
                    return True, player0

                elif t.lower().find(m.player1.getName().lower()) >= 0:
                    return True, player1

                else:
                    try:
                        if rows[i].findAll('td')[0].text.find('(void)') >= 0:
                            return True, void
                    except:
                        pass

    return got_res, -1


class Command(BaseCommand):

    requires_model_validation = True

    def handle(self, *args, **options):
        ts = datetime.date.today() - datetime.timedelta(days=5)
        n_errors = 0

        matches = Match.objects.filter(winner__isnull=True, start_ts__gte=ts).exclude(
            void=True,
        ).order_by('start_ts')
        im = 0
        for m in matches:
            print "================="
            print m.getTitle(), m.id, m.tournament.id, " %d of %d " % (im, len(matches))
            im += 1
            url = "http://sports.williamhill.com/bet/en-gb/results///E/{0}/thisDate/{1}/{2}/{3}///".format(m.wh_match_id, m.start_ts.year, m.start_ts.month, m.start_ts.day)
            print url
            r = requests.get(url)
            soup = BeautifulSoup(r.text)
            res_table = soup.find(
                "table", {"class": "tableData tableSearchResults"}
            )

            if not res_table:
                print "Results not found"
                continue
            rows = res_table.findAll('tr')
            if not len(rows):
                print "Empty results!"
                continue

            match_results = getResult("Match Betting", rows, m)
            match_live_results = getResult("Match Betting Live", rows, m)
            match_betting_has_result = match_results[0]
            match_live_betting_has_result = match_live_results[0]

            mb_void = mb_live_void = False

            if match_betting_has_result:
                # Match betting not void
                has_winner = match_results[1] != 0
                if has_winner:
                    winner = m.player0 if match_results[1] == 1 else m.player1
                    print "Match betting has winner!", winner.getName()
                    m.winner = winner
                    m.save()
                    continue
                else:
                    mb_void = True

            if match_live_betting_has_result:
                # Match betting live not void
                has_winner = match_live_results[1] != 0
                if has_winner:
                    winner = m.player0 if match_live_results[1] == 1 else m.player1

                    print "Match betting live has winner!", winner.getName()
                    m.winner = winner
                    m.save()
                    continue
                else:
                    mb_live_void = True

            if mb_live_void:
                m.setVoid()
