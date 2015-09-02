# -*- coding: utf-8 -*-
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from django.core.management import BaseCommand
from django.conf import settings

from tennis.models import Player


def import_data(base_url):
    data = {}
    page = 0
    while 1:
        page += 1
        url = "%s%d" % (base_url, page)
        r = requests.get(url)
        soup = BeautifulSoup(r.text)
        rank_table = soup.find(
            "tbody", {"class": "flags"}
        )

        if page > 100 or not rank_table:
            break

        rows = rank_table.findAll('tr')
        print url
        print "Importing ", len(rows), " rows"

        for r in rows:
            td = r.findAll('td')
            th = r.findAll('th')
            if len(td) == 3 and len(th) == 1:
                pos = int(td[0].text.strip().replace('.', ''))
                names = th[0].text.strip().split()
                name = names[-1] + " " + " ".join(names[:-1])
                points = int(td[2].text.strip())
                data[name.lower()] = {
                    'rank': pos,
                    'points': points
                }
                # print name, pos, points
    return data


class Command(BaseCommand):

    def handle(self, *args, **options):

        wta_base = "http://www.tennisexplorer.com/ranking/wta-women/%s/?type=WTA&date=&page=" % datetime.now().year
        atp_base = "http://www.tennisexplorer.com/ranking/atp-men/%s/?type=ATP&date=&page=" % datetime.now().year
        data = {}
        data.update(import_data(atp_base))
        print len(data.keys()), " ATP imported"
        data.update(import_data(wta_base))
        print len(data.keys()), " imported total"

        names = data.keys()
        for player in Player.objects.all():
            name = player.name.lower()
            if name.find('/') >= 0:
                continue

            if name in names:
                print name, data[name]
                player.rank = data[name]['rank']
                player.points = data[name]['points']
                player.save()
            else:
                print player.name, " not found!"
