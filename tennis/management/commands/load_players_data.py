import re
import requests
import BeautifulSoup
import urllib

from django.core.management import BaseCommand
from django.db.transaction import commit_on_success
from django.conf import settings
from django.db.models import Q

from tennis.models import Tournament, AssociationType, Player, Match, Set, Game, Country, Gender, SurfaceType

headers = {
    'User-Agent': settings.USER_AGENT,
}


def get_google_country(player_name):
    url = "https://www.google.ru/search?q=www.atpworldtour.com:+{}".format(urllib.quote_plus(player_name))
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup.BeautifulSoup(r.text)
    results = soup.find(
        "div", {"id": "ires"}
    )
    a = results.find("a")
    try:
        url = a['href']
    except:
        return

    url_valid = url.find('Tennis/Players') >= 0
    if not url_valid:
        return

    return get_country(url)


def get_country(url):

    try:
        r = requests.get(url, headers=headers)
    except:
        print "HTTP error!"
        return
    soup = BeautifulSoup.BeautifulSoup(r.text)
    flag = soup.find(
        "div", {"id": "playerBioInfoFlag"}
    )

    if flag:
        return flag.text.strip()


class Command(BaseCommand):

    requires_model_validation = True

    @commit_on_success
    def handle(self, *args, **options):
        i = 0
        matches = Match.objects.filter(
            tournament__association__in=(AssociationType.ATP, AssociationType.ITF),
            tournament__gender=Gender.MALE,
            singles=True
        )
        for m in matches:
            i += 1
            print "Match {} of {}".format(i, len(matches))

            p0_name = m.player0.getName()
            p1_name = m.player1.getName()

            if p0_name.find('/') >= 0 and p0_name.find('/') >= 0:
                m.setDoubles()
                continue

            if p0_name.find('Doubles') >= 0 and p1_name.find('Doubles') >= 0:
                m.setDoubles()
                continue

            if p0_name.endswith('.'):
                p0_name = p0_name[:-1]
                print "Cut dot!", p0_name

            if p1_name.endswith('.'):
                p1_name = p1_name[:-1]
                print "Cut dot!", p1_name

            try:
                (p0_name, p0_lastname) = p0_name.split()
                (p1_name, p1_lastname) = p1_name.split()
            except:
                pass

            print m.player0.getName()
            print m.player1.getName()

            url0_1 = "http://www.atpworldtour.com/Tennis/Players/{}/{}/{}-{}.aspx".format(p0_lastname[:2], p0_name[:1], p0_name, p0_lastname)
            url0_2 = "http://www.atpworldtour.com/Tennis/Players/Top-Players/{}-{}.aspx".format(p0_name, p0_lastname)

            url1_1 = "http://www.atpworldtour.com/Tennis/Players/{}/{}/{}-{}.aspx".format(p1_lastname[:2], p1_name[:1], p1_name, p1_lastname)
            url1_2 = "http://www.atpworldtour.com/Tennis/Players/Top-Players/{}-{}.aspx".format(p1_name, p1_lastname)
            # Player0
            if m.player0.country is None:

                # 1
                country0 = get_country(url0_1)

                # 2
                if not country0:
                    country0 = get_country(url0_2)

                # 3
                if not country0:
                    country0 = get_google_country(m.player0.getName())
                    if country0:
                        print "Found in google: ", country0

                if country0:
                    print "Player0 country: ", country0
                    c, created = Country.objects.get_or_create(title=country0)
                    m.player0.country = c
                    m.player0.save()

            # Player1
            if m.player1.country is None:
                # 1
                country1 = get_country(url1_1)

                # 2
                if not country1:
                    country1 = get_country(url1_2)

                # 3
                if not country1:
                    country1 = get_google_country(m.player1.getName())
                    if country1:
                        print "Found in google: ", country1

                if country1:
                    print "Player1 country: ", country1
                    c, created = Country.objects.get_or_create(title=country1)
                    m.player1.country = c
                    m.player1.save()

        return "OK"
