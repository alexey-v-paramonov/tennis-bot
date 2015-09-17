# coding=utf-8
import re
import math
import requests
import BeautifulSoup
from fractions import Fraction
import jsonfield
import urllib
from selenium import webdriver
import datetime
import json as core_json

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.db import transaction
from django.db import IntegrityError
from django.db.models import Q
from django.utils import timezone
from django.core.serializers import json
from django.core.mail import send_mail

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn import preprocessing


MIN_ODD_CUTOFF = 1.33
MAX_ODD_CUTOFF = 4.0
GAMES_STATS_PERIOD = 600


class AssociationType(object):
    ATP = 0
    WTA = 1
    ITF = 2
    UNK = 3

    choices = (
        (ATP, 'ATP'),
        (WTA, 'WTA'),
        (ITF, 'ITF'),
        (UNK, 'Unknown'),
    )


class Gender(object):

    MALE = 0
    FEMALE = 1

    choices = (
        (MALE, 'Male'),
        (FEMALE, 'Female'),
    )


class MatchBetStatus(object):

    NOT_SET = 0
    PLAYERS_DATA_TOO_SMALL = 1
    TRAINING_DATA_TOO_SMALL = 2
    NOT_WORTH_IT = 3
    SET = 4

    choices = (
        (NOT_SET, 'Bet not set yet'),
        (PLAYERS_DATA_TOO_SMALL, 'Bet not set: players data too small'),
        (TRAINING_DATA_TOO_SMALL, 'Bet not set: '),
        (NOT_WORTH_IT, 'Bet not set: odd not worth it'),
        (SET, 'Bet set'),
    )


class SurfaceType(object):

    HARD = 0
    CLAY = 1
    GRASS = 2
    CARPET = 3
    IHARD = 4
    ICLAY = 5
    OHARD = 7
    OCLAY = 8

    ICARPET = 9
    OCARPET = 10

    IGRASS = 11
    OGRASS = 12

    UNK = 6

    choices = (
        (HARD, 'Hard'),
        (CLAY, 'Clay'),
        (GRASS, 'Grass'),
        (CARPET, 'Carpet'),
        (IHARD, 'Indoor hard'),
        (ICLAY, 'Indoor clay'),
        (OHARD, 'Outdoor hard'),
        (OCLAY, 'Outdoor clay'),
        (ICARPET, 'Indoor carpet'),
        (OCARPET, 'Outdoor carpet'),
        (IGRASS, 'Indoor grass'),
        (OGRASS, 'Outdoor grass'),
        (UNK, 'Unknown'),
    )

    @classmethod
    def as_dict(cls):
        return dict(cls.choices)


HARDS = [
    SurfaceType.HARD,
    SurfaceType.IHARD,
    SurfaceType.OHARD,
    SurfaceType.CARPET,
    SurfaceType.ICARPET,
    SurfaceType.OCARPET
]

GRASS = [
    SurfaceType.GRASS,
    SurfaceType.IGRASS,
    SurfaceType.OGRASS
]

CLAYS = [
    SurfaceType.CLAY,
    SurfaceType.ICLAY,
    SurfaceType.OCLAY
]


class RankType(object):

    UNK = 0
    FUTURES = 1
    CHALLENGERS = 2

    choices = (
        (UNK, 'Unknown'),
        (FUTURES, 'Futures'),
        (CHALLENGERS, 'ChallengersK'),
    )


class Country(models.Model):

    title = models.CharField(_("Title"), max_length=255, unique=True)


class CountryAlias(models.Model):

    country = models.ForeignKey(Country, related_name="aliases")
    alias = models.CharField(_("Alias"), max_length=255, unique=True)


class Player(models.Model):

    country = models.ForeignKey(Country, related_name="players", null=True)
    name = models.CharField(_("Name"), max_length=255, unique=True)
    rank = models.PositiveSmallIntegerField(default=0)
    points = models.PositiveSmallIntegerField(default=0)

    def serveStats(self, up_to_date=None, surfaces=None):
        f = Q(server=self, finished=True)
        s = datetime.datetime.now()
        if up_to_date:
            f &= Q(set__match__start_ts__lt=up_to_date)
            s = up_to_date

        f &= Q(set__match__start_ts__gt=s - datetime.timedelta(days=GAMES_STATS_PERIOD))
        if surfaces:
            f &= Q(set__match__tournament__surface__in=surfaces)

        games = Game.objects.filter(f).order_by('-id').all().prefetch_related('points')
        histogram = {}
        for g in games:
            points = g.getTennisPoints()
            if not len(points):
                continue
            result = points[-1]
            key = u"{0}-{1}".format(result[0], result[1])

            try:
                histogram[key] += 1
            except:
                histogram[key] = 1

        tot = len(games)
        ret = []
        for k, v in histogram.items():
            p = float(v)/float(tot)*100.
            histogram[k] = p
        return histogram, tot

    def receiveStats(self, up_to_date=None, surfaces=None):
        f = Q(receiver=self, finished=True)
        s = datetime.datetime.now()

        if up_to_date:
            f &= Q(set__match__start_ts__lt=up_to_date)
            s = up_to_date
        if surfaces:
            f &= Q(set__match__tournament__surface__in=surfaces)
        f &= Q(set__match__start_ts__gt=s - datetime.timedelta(days=GAMES_STATS_PERIOD))
        games = Game.objects.filter(f).order_by('-id').all().prefetch_related('points')
        histogram = {}
        bp_won = 0
        bp_total = 0
        for g in games:
            points, breakpoints = g.getTennisPoints(with_breaks=True)
            if not len(points):
                continue
            broke = g.winner and g.receiver and g.winner.pk == g.receiver.pk
            if broke:
                bp_won += 1
                breakpoints -= 1
            bp_total += breakpoints
            
            result = points[-1]
            key = u"{0}-{1}".format(result[0], result[1])
            try:
                histogram[key] += 1
            except:
                histogram[key] = 1

        tot = len(games)
        ret = []
        for k, v in histogram.items():
            p = (float(v)/float(tot))*100.
            histogram[k] = p

        bp_percent = 0
	if bp_total > 0:
	    bp_percent = round((float(bp_won)/float(bp_total))*100, 2)

        return histogram, bp_percent, tot

    def get_winner_data(self, up_to_date=None, surfaces=None):
        ret = {}
        ret['point_stats'], s_games = self.serveStats(up_to_date, surfaces)
        ret['receive_stats'], ret['bp_won'], r_games = self.receiveStats(up_to_date, surfaces)
        ret['num_games'] = s_games + r_games
        return ret

    def getName(self):
        return self.name

    def getPage(self):
        searchfor = 'itftennis.com: {0}'.format(self.getName())
        query = urllib.urlencode({'q': searchfor})
        url = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&%s' % query
        search_response = urllib.urlopen(url)
        search_results = search_response.read()
        results = core_json.loads(search_results)
        data = results['responseData']
        if data['cursor']['estimatedResultCount'] > 0:
            hits = data['results']

            # search for pro profile
            for h in hits:
                if h['url'].find('procircuit/players/player/profile.aspx') > 0:
                    return urllib.unquote(h['url'])

            # search for junior profile
            for h in hits:
                if h['url'].find('juniors/players/player/profile.aspx') > 0:
                    return urllib.unquote(h['url'])

        return False
    
    def getCurrentRank(self):
        url = self.getPage()
        print url
        loaded = False
        try:
            driver = webdriver.PhantomJS(executable_path=settings.PHANTOM_BIN)
            driver.get(url)
            source = driver.page_source
            loaded = True
        except:
            print "Unable to fetch ", url
        finally:
            driver.close()
            driver.quit()

        if loaded:    
            soup = BeautifulSoup.BeautifulSoup(source)
            rows = soup.findAll('tr')
            for r in rows:
                tds = r.findAll('td')
                if tds:
                    for td in tds:
                        try:
                            t = td.text.strip()
                        except:
                            continue
                        
                        if t.find("Current Singles Ranking") >= 0:
                            try:
                                return tds[1].text
                            except:
                                pass
                            
        return 0
        
    def countMatches(self, up_to_date=None, surfaces=None):
        f = Q(player1=self) | Q(player0=self)
        if up_to_date:
            f &= Q(start_ts__lt=up_to_date)
        if surfaces:
            f &= Q(tournament__surface__in=surfaces)
        return Match.objects.filter(f).count()

    def countGames(self, up_to_date=None, surfaces=None):
        f = Q(server=self) | Q(receiver=self)
        s = datetime.datetime.now()
        if up_to_date:
            f &= Q(set__match__start_ts__lt=up_to_date)
            s = up_to_date
        if surfaces:
            f &= Q(set__match__tournament__surface__in=surfaces)

        f &= Q(set__match__start_ts__gt=s - datetime.timedelta(days=GAMES_STATS_PERIOD))

        return Game.objects.filter(f).count()


class Tournament(models.Model):

    title = models.CharField(
        'Tournament title',
        max_length=255,
        blank=False,
        null=True,
    )

    country = models.ForeignKey(Country, related_name="tournaments", null=True)

    date_start = models.DateField(
        _("Started on"),
        auto_now_add=True,
        blank=True
    )
    date_finish = models.DateField(_("Finished on"), null=True, blank=True)

    gender = models.PositiveSmallIntegerField(
        _("Gender"),
        default=Gender.MALE,
        choices=Gender.choices
    )

    qualifying = models.BooleanField(_("Qualifying"), default=False)

    association = models.PositiveSmallIntegerField(
        _("Association"),
        default=AssociationType.UNK,
        choices=AssociationType.choices
    )
    surface = models.PositiveSmallIntegerField(
        _("Surface"),
        default=SurfaceType.UNK,
        choices=SurfaceType.choices
    )

    rank = models.PositiveSmallIntegerField(
        _("Surface"),
        default=RankType.UNK,
        choices=RankType.choices
    )

    def is_challenger(self):
        return self.association == AssociationType.ATP\
            and self.title.lower().find('challenger tour') >= 0

    def guess_country(self):
        t = self.title
        mapping = {
            'moscow': 'Russian Federation',
            'Shanghai': 'China',
            'Valencia': 'Spain',
            'Paris': 'France',
            'Miami': 'United States',
            'London': 'Great Britain',
            'Cincinnati': 'United States',
            'Winston-Salem': 'United States',
            'Washington': 'United States',
            'Hamburg': 'Germany',
            'Stockholm': 'Sweden',
            'Madrid': 'Spain',
            'Vienna': 'Austria',
            'Rio De Janeiro': 'Brazil'
        }

        for k, v in mapping.items():
            if t.lower().find(k.lower()) >= 0:
                print "Guess: ", t, " is: ", v
                self.country = Country.objects.get(title=v)
                self.save()
                return

        for c in Country.objects.all():
            if t.lower().find(c.title.lower()) >= 0:
                print "Guess: ", t, " is: ", c.title
                self.country = c
                self.save()
                return

        for c in CountryAlias.objects.all():
            if t.lower().find(c.alias.lower()) >= 0:
                print "Guess: ", t, " is: ", c.alias
                self.country = c.country
                self.save()
                return

    def load_surface(self):

        headers = {
            'User-Agent': settings.USER_AGENT,
            'Accept': settings.ACCEPT,
            'Accept-Language': 'fr-fr,en-us;q=0.7,en;q=0.3',
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7'
        }

        def save_surf(surface):
            t = self
            s = surface.lower()
            if s.find('indoor') >= 0:
                if s.find('hard') >= 0:
                    t.surface = SurfaceType.IHARD
                    t.save()
                elif s.find('clay') >= 0:
                    t.surface = SurfaceType.ICLAY
                    t.save()
                elif s.find('carpet') >= 0:
                    t.surface = SurfaceType.ICARPET
                    t.save()
                elif s.find('grass') >= 0:
                    t.surface = SurfaceType.IGRASS
                    t.save()
                else:
                    print "Unknown surface: ", s

            elif s.find('outdoor') >= 0:
                if s.find('hard') >= 0:
                    t.surface = SurfaceType.OHARD
                    t.save()
                elif s.find('clay') >= 0:
                    t.surface = SurfaceType.OCLAY
                    t.save()
                elif s.find('carpet') >= 0:
                    t.surface = SurfaceType.OCARPET
                    t.save()
                elif s.find('grass') >= 0:
                    t.surface = SurfaceType.OGRASS
                    t.save()
                else:
                    print "Unknown surface: ", s
            else:
                if s.find('hard') >= 0:
                    t.surface = SurfaceType.HARD
                    t.save()
                elif s.find('clay') >= 0:
                    t.surface = SurfaceType.CLAY
                    t.save()
                elif s.find('carpet') >= 0:
                    t.surface = SurfaceType.CARPET
                    t.save()
                elif s.find('grass') >= 0:
                    t.surface = SurfaceType.GRASS
                    t.save()

                else:
                    print "Unknown surface: ", s

        if self.association == AssociationType.WTA:

            def patch_wta_title(t):
                t = re.sub("(.*?)WTA", '', t)
                return t.replace('Doubles', '')\
                        .replace('Qualifying', '')\
                        .replace('WTA', '')\
                        .replace(' - ', '')\
                        .strip()

            title = patch_wta_title(self.title)
            if self.date_start:
                y = self.date_start.year
            else:
                y = timezone.now().year

            search_url = u"http://en.wikipedia.org/wiki/{0}_WTA_Tour".format(y)
            try:
                r = requests.get(search_url)
            except:
                return False

            html = r.text.encode('utf-8')
            soup = BeautifulSoup.BeautifulSoup(html)
            data = soup.find(
                'td',
                text=re.compile(title.lower().strip(), re.UNICODE)
            )

            if not data:
                return False

            surf_data = None
            try:
                surf_data = re.compile("– (.*?)– ")\
                              .search(data.parent.parent.text.encode("utf-8"))\
                              .groups()[0]
            except:
                pass

            if not surf_data:
                return False

            s = surf_data.lower()
            t = self
            if s.find('(i)') >= 0:
                if s.find('hard') >= 0:
                    t.surface = SurfaceType.IHARD
                    t.save()
                elif s.find('clay') >= 0:
                    t.surface = SurfaceType.ICLAY
                    t.save()
                elif s.find('carpet') >= 0:
                    t.surface = SurfaceType.ICARPET
                    t.save()
                elif s.find('grass') >= 0:
                    t.surface = SurfaceType.IGRASS
                    t.save()
                else:
                    print "Unknown WTA surface (indoor): ", s
            else:
                if s.find('hard') >= 0:
                    t.surface = SurfaceType.HARD
                    t.save()
                elif s.find('clay') >= 0:
                    t.surface = SurfaceType.CLAY
                    t.save()
                elif s.find('carpet') >= 0:
                    t.surface = SurfaceType.CARPET
                    t.save()
                elif s.find('grass') >= 0:
                    t.surface = SurfaceType.GRASS
                    t.save()
                else:
                    print "Unknonw WTA surface (indoor): ", s

        elif self.association == AssociationType.ATP:

            def patch_atp_title(t):
                t = re.sub('ATP\s+Challenger\s+Tour\s*(-?)', '', t)
                return t.replace('Doubles', '')\
                        .replace('Qualifying', '')\
                        .replace('ATP', '')\
                        .replace(' - ', '')\
                        .strip()

            title = patch_atp_title(self.title)

            if self.date_start:
                y = self.date_start.year
            else:
                y = timezone.now().year

            t = "2"

            if self.is_challenger():
                t = "4"

            data = {
                't': t,
                'y': y,
            }
            search_url = settings.ATP_EVENTS_URL
            r = requests.get(search_url, params=data)
            atp_calendar_html = r.text.encode('utf-8')
            soup = BeautifulSoup.BeautifulSoup(atp_calendar_html)

            rows = soup.findAll('tr', {'class': 'calendarFilterItem'})
            tournaments_data = {}
            for tr in rows:

                tds = tr.findAll('td')
                title_td = tds[1]
                surface_td = tds[2]
                strongs = title_td.findAll('strong')

                if len(strongs) == 2:
                    t_title = strongs[0].text.strip()
                    country = strongs[1].text.strip()
                    surface = surface_td.text.strip()
                    tournaments_data[t_title] = [surface, country]

            import Levenshtein
            ratio_hist = []

            for k, v in tournaments_data.items():
                ratio_hist.append({k: Levenshtein.ratio(k, title)})

            def my_f(x1, x2):
                return int((x2.values()[0] - x1.values()[0])*1000.)

            country_set = False
            if len(ratio_hist) > 0:
                ratio_hist.sort(my_f)
                best_matching_title = ratio_hist[0].keys()[0]
                best_matching_ratio = ratio_hist[0].values()[0]
                if best_matching_ratio > 0.8:
                    print "Best match:  '%s' '%s' %f" % (
                        best_matching_title,
                        title,
                        best_matching_ratio
                    )
                    print "Surface: ", tournaments_data[best_matching_title][0]
                    print "Country:", tournaments_data[best_matching_title][1]
                    country = tournaments_data[best_matching_title][1]
                    try:
                        c = Country.objects.get(title=country)
                    except:
                        c = None
                    if c:
                        self.country = c
                        self.save()
                        country_set = True
                    else:
                        try:
                            a = CountryAlias.objects.get(alias=country)
                        except:
                            print "### Unknown country:", country
                            self.guess_country()
                        else:
                            self.country = a.country
                            self.save()
                            country_set = True

            if not country_set:
                self.guess_country()

        elif self.association == AssociationType.ITF:

            import calendar

            def patch_itf_title(t):
                t = re.sub('^ITF\s+Tour\s*(-?)\s*', '', t)
                return t.replace('Doubles', '').replace('Qualifying', '')

            title = patch_itf_title(self.title)
            last_day = calendar.monthrange(
                self.date_start.year,
                self.date_start.month
            )[1]
            data = {
                'tour': title.strip(),
                'fromDate': '01-%02d-2014' % self.date_start.month,
                'toDate': '%02d-%02d-2015' % (last_day, self.date_start.month),
                'reg': '',
                'nat': '',
                'sur': '',
                'cate': '',
                'iod': '',
            }
            if self.gender == Gender.MALE:
                search_url = settings.ITF_MEN_CALENDAR
            elif self.gender == Gender.FEMALE:
                search_url = settings.ITF_WOMEN_CALENDAR

            url = search_url + urllib.urlencode(data)
            print url
            try:
                driver = webdriver.PhantomJS(
                    executable_path=settings.PHANTOM_BIN
                )
                driver.get(url)
            except:
                return

            try:
                driver.find_element_by_id('lnkName0').click()
            except:
                driver.close()
                driver.quit()
                return

            try:
                html = driver.find_element_by_css_selector(
                    '.tnews'
                ).get_attribute("innerHTML")
            except:
                driver.close()
                driver.quit()
                return

            driver.close()
            soup2 = BeautifulSoup.BeautifulSoup(html)
            lis = soup2.findAll('li', {'class': "hlf fl"})
            for li in lis:
                    span = li.find('span', {'class': "subject"})
                    if span and span.text == 'Surface:':
                        surface = li.find('strong').text
                        save_surf(surface)
            return
            # soup = BeautifulSoup.BeautifulSoup(r.text)
            # links = soup.findAll('a', {'id': re.compile('^lnkName\d+')})
            # if len(links)>1:
            #     print "Warning: Several tournaments found"
            #     links = links[:1]

            # if len(links)==1:

            #     link = links[0]
            #     new_url = "http://www.itftennis.com" + link['href']
            #     r2 = requests.get(new_url)
            #     soup2 = BeautifulSoup.BeautifulSoup(r2.text)
            #     lis = soup2.findAll('li', {'class': "hlf fl"})
            #     for li in lis:
            #         span = li.find('span', {'class': "subject"})
            #         if span and span.text=='Surface:':
            #             surface = li.find('strong').text
            #             save_surf(surface)

    def fetchSurface(self):
        print "fetchSurface", self.association
        print "fetchSurface", self.title

    def get_absolute_url(self):
        return u"/tournament/{0}".format(self.pk)

    class Meta:
        unique_together = [
            ('title', 'association'),
        ]


class Match(models.Model):
    tournament = models.ForeignKey(Tournament, related_name="matches")
    player0 = models.ForeignKey(Player, related_name="+")
    player1 = models.ForeignKey(Player, related_name="+")

    player0_rank = models.PositiveSmallIntegerField(default=0)
    player1_rank = models.PositiveSmallIntegerField(default=0)

    player0_points = models.PositiveSmallIntegerField(default=0)
    player1_points = models.PositiveSmallIntegerField(default=0)

    winner = models.ForeignKey(Player, null=True, related_name="matches_won")
    start_ts = models.DateTimeField(_("Started on"), auto_now_add=True)

    singles = models.BooleanField(_("For singles"), default=True)
    consistent = models.BooleanField(_("Consistent"), default=True)
    started = models.BooleanField(_("Consistent"), default=False)
    finished = models.BooleanField(_("Consistent"), default=False)
    # William hill match id
    wh_match_id = models.PositiveIntegerField(default=0)

    player0_odd = models.FloatField(null=True)
    player1_odd = models.FloatField(null=True)

    player0_max_live_odd = models.FloatField(null=True)
    player1_max_live_odd = models.FloatField(null=True)

    winner_data1 = jsonfield.JSONField(null=True, default={})
    winner_data2 = jsonfield.JSONField(null=True, default={})

    winner_data1_size = models.PositiveIntegerField(default=0)
    winner_data2_size = models.PositiveIntegerField(default=0)

    winner_data1_surface = jsonfield.JSONField(null=True, default={})
    winner_data2_surface = jsonfield.JSONField(null=True, default={})

    winner_data1_surface_size = models.PositiveIntegerField(default=0)
    winner_data2_surface_size = models.PositiveIntegerField(default=0)

    winner_data1_recent = jsonfield.JSONField(null=True, default={})
    winner_data2_recent = jsonfield.JSONField(null=True, default={})

    winner_data1_recent_size = models.PositiveIntegerField(default=0)
    winner_data2_recent_size = models.PositiveIntegerField(default=0)

    void = models.BooleanField(
        _("Bets void (cancel or retire)"),
        default=False
    )

    bet_status = models.PositiveSmallIntegerField(
        _("Bet Status"),
        default=MatchBetStatus.NOT_SET,
        choices=MatchBetStatus.choices
    )

    def load_match_bets(self):
        match_url = u"{0}{1}/".format(
            settings.MATCH_BASE_URL, self.wh_match_id
        )
        r = requests.get(match_url)
        match_html = r.text.encode('utf-8')
        soup = BeautifulSoup.BeautifulSoup(match_html)
        match_bets_container = soup.find(
            text="Match Betting Live"
        ).findParent("table")

        if match_bets_container:
            def get_player_odd(c, player):

                txt = c.find(
                    text=re.compile(
                        u"\s*{0}\s*".format(player),
                        re.MULTILINE | re.DOTALL | re.IGNORECASE
                    )
                )
                if txt:
                    div = txt.parent
                    fractional_odd = div.parent.find(
                        "div",
                        {"class": "eventprice"}
                    ).text
                    if(fractional_odd):
                        try:
                            return float(Fraction(fractional_odd)) + 1.0
                        except:
                            return None

                print "Unable to find odd for ", player, self.wh_match_id
                return None

            odd1 = get_player_odd(match_bets_container, self.player0.name)
            odd2 = get_player_odd(match_bets_container, self.player1.name)
            if odd1 and odd2:
                self.player0_odd = odd1
                self.player1_odd = odd2
                self.save()

    def make_winner_bet(self):

        bet_exists = Bet.objects.filter(
            match=self,
            selection=BetSelection.MATCH_WINNER
        ).exists()
        
        if not bet_exists and self.tournament.surface != SurfaceType.UNK:
            t = self.getTitle()
            target_surfaces = HARDS
            if self.tournament.surface in HARDS:
                print t, "Target surface for training data: hard"
                target_surfaces = HARDS
                s = "hards"
            elif self.tournament.surface in CLAYS:
                print t, "Target surface for training data: clay"
                target_surfaces = CLAYS
                s = "clays"
            elif self.tournament.surface in GRASS:
                print t, "Target surface for training data: grass"
                target_surfaces = GRASS
                s = "grass"

            d1 = self.winner_data1_surface
            d2 = self.winner_data2_surface
            d1['rank'] = self.player0_rank
            d2['rank'] = self.player1_rank

            d1_s = self.winner_data1_surface_size
            d2_s = self.winner_data2_surface_size
            odds_loaded = self.player0_odd and self.player1_odd
            if not odds_loaded:
                print t, "Skip bet: player odds not loaded yet"
                return

            bet_possible = d1_s >= 200 and d2_s >= 200
            if bet_possible:
                surface = self.tournament.surface
                print "making bet!", surface, d1, d2, d1_s, d2_s
                TRAIN_DATA_MIN_SIZE = 1000
                matches2 = Match.objects.filter(
                    tournament__gender=self.tournament.gender,
                    start_ts__lt=self.start_ts,
                    singles=self.singles,
                    winner__isnull=False,
                    winner_data1_surface_size__gt=300,
                    winner_data2_surface_size__gt=300,
                    tournament__surface__in=target_surfaces
                )
                g = "men" if self.tournament.gender == 0 else "women"
                print t, "Stats matches num:", len(matches2)
                if len(matches2) < TRAIN_DATA_MIN_SIZE:
                    print t, "Train data too small", len(matches2)
                    return
                trainX = []
                trainY = []
                X = np.array(getX(d1, d2), dtype=float)
                for m2 in matches2:
                    dd1 = m2.winner_data1_surface
                    dd2 = m2.winner_data2_surface
                    dd1['rank'] = m2.player0_rank
                    dd2['rank'] = m2.player1_rank
                        
                    trainX.append(preprocessing.scale(getX(dd1, dd2)))
                    trainY.append(int(m2.winner == m2.player0),)
                print "TrainX0: ", trainX[0]

                XX = np.array(trainX, dtype=float)
                yy = np.array(trainY, dtype=int)
                model = LogisticRegression()
                model = model.fit(XX, yy)
                print "Model score:", model.score(XX, yy)
                print "Model coef:", model.coef_
                p = model.predict(preprocessing.scale(X))[0]
                winner = self.player0 if int(p) == 1 else self.player1
                odd = self.player0_odd if int(p) == 1 else self.player1_odd
                # live_odd = self.player0_max_live_odd
                # if int(p) == 1 else self.player1_max_live_odd

                print t, "Bet ON: ", winner.getName(), "(", p, ")"
                worth_it = odd >= MIN_ODD_CUTOFF
                too_risky = odd >= MAX_ODD_CUTOFF
                WORTH_LIVE = 2.5

                if not worth_it:

                    print t, " : ", winner.getName(), "Not worth it", odd
                    return
                if too_risky:
                    print t, " : ", winner.getName(), "too risky", odd
                    return

                b = Bet.objects.create(
                    match=self,
                    winner=winner,
                    selection=BetSelection.MATCH_WINNER,
                    winner_data1_surface=json.json.dumps(d1),
                    winner_data2_surface=json.json.dumps(d2),
                    set=1,
                    game=1,
                    odd=odd
                )

            else:
                print t, "To small player data, skip: ", d1_s, d2_s

    def checkStrategies(self):
        last_set = self.sets.last()
        g = last_set.games.last()
        if g.finished and not g.isLastSetGame():

            if g.closeToSetEnd() and not g.bigGap() and self.singles:
                bet, created = Bet.objects.get_or_create(
                    match=self,
                    set=last_set.number,
                    game=g.number + 1,
                    selection=BetSelection.DEUCE
                )

        return True

    def get_surface_title(self):
        return SurfaceType.as_dict().get(self.tournament.surface, 'Unknown')

    def get_surface_color(self):
        s = self.tournament.surface

        if s in (SurfaceType.HARD, SurfaceType.OHARD):
            return '#4081a0'
        elif s in (SurfaceType.CLAY, SurfaceType.OCLAY):
            return '#ff9966'
        elif s in (SurfaceType.GRASS, SurfaceType.IGRASS, SurfaceType.OGRASS):
            return '#57ed54'
        elif s in (SurfaceType.CARPET, SurfaceType.ICARPET, SurfaceType.OCARPET):
            return '#e7d95f'
        elif s == SurfaceType.IHARD:
            return '#99cdff'
        elif s == SurfaceType.ICLAY:
            return '#e2e2e2'
        else:
            return '#fff'

    def get_average_points(self, limit_game):
        g = 0
        summ = 0
        for set in self.sets.all():
            for game in set.games.all():
                g += 1
                points = game.getTennisPoints()
                if g > limit_game:
                    break
                summ += len(points)
        if g > 0:
            return float(summ)/float(limit_game-1)
        else:
            return -1

    def getTitle(self):
        return u"{0} ({2}) - {1} ({3})".format(self.player0.name, self.player1.name, self.player0_rank, self.player1_rank)

    def get_absolute_url(self):
        return u"/tournament/{0}/match/{1}".format(self.tournament.pk, self.pk)

    def setStarted(self):

        if not self.started:
            self.started = True
            self.save()

    def setDoubles(self):

        if self.singles:
            self.singles = False
            self.save()

    def setInconsistent(self):
        if self.consistent:
            self.consistent = False
            self.save()

    def setConsistent(self):
        if not self.consistent:
            self.consistent = True
            self.save()

    def setVoid(self):
        if not self.void:
            self.void = True
            self.winner = None
            self.save()

            bet = Bet.objects.filter(
                match=self,
                selection=BetSelection.MATCH_WINNER
            ).update(status=BetStatus.RETURN)

    def getGameServerReceiver(self, game_number):

        if 1:
            # Odd games
            if game_number % 2 != 0:
                return (self.odd_game_server, self.odd_game_receiver)
            # Even games
            else:
                return (self.odd_game_receiver, self.odd_game_server)
        else:
            # Odd games
            if game_number % 2 != 0:
                return (self.odd_game_receiver, self.odd_game_server)
            # Even games
            else:
                return (self.odd_game_server, self.odd_game_receiver)

    def createFromMessages(self, msgs):

        point_re = re.compile(
            '^Game\s+(\d+)\s+-\s+Point\s+(\d+)\s+-\s+(.*?)$',
            re.DOTALL | re.IGNORECASE
        )

        match_game_number = 0
        parsed_set_games = {}

        for m in msgs:

            if m.isMatchStart():
                self.setStarted()

            elif m.isFirstServer():

                self.setStarted()

                server = m.text.replace(' to serve first', '').strip()
                if server == self.player0.name:
                    self.odd_game_server = self.player0
                    self.odd_game_receiver = self.player1

                elif server == self.player1.name:
                    self.odd_game_server = self.player1
                    self.odd_game_receiver = self.player0

                else:
                    print "Unable to get server!"
                    return False

            elif m.isTieBreak():
                match_game_number += 1
                pass

            elif m.isPoint():
                if not self.started:
                    return False

                s, created = Set.objects.get_or_create(
                    match=self,
                    number=m.set
                )
                if created:
                    parsed_set_games[m.set] = []

                mm = point_re.match(m.text)
                if not mm:
                    continue

                (game_n, p_num, pl) = mm.groups()
                game_n = int(game_n)
                p_num = int(p_num)

                # New game
                if game_n not in parsed_set_games[m.set]:
                    # validate!
                    if len(parsed_set_games[m.set]) == 0:
                        if game_n != 1:
                            return False
                    else:
                        if game_n - parsed_set_games[m.set][-1] != 1:
                            return False

                    parsed_set_games[m.set].append(game_n)
                    match_game_number += 1

                (server, receiver) = self.getGameServerReceiver(
                    match_game_number
                )

                game, created = Game.objects.get_or_create(
                    set=s,
                    number=game_n,
                    server=server,
                    receiver=receiver,
                )

                if game.server.name == pl:
                    player = game.server
                else:
                    player = game.receiver

                point, created = Point.objects.get_or_create(
                    game=game,
                    player=player,
                    number=p_num,
                )

        return True

    class Meta:
        unique_together = [
            ('tournament', 'player0', 'player1', 'wh_match_id'),
        ]


class Set(models.Model):
    choices = (
        (1, "1"),
        (2, "2"),
        (3, "3"),
        (4, "4"),
        (5, "5"),
    )
    match = models.ForeignKey(Match, related_name="sets")
    winner = models.ForeignKey(Player, null=True, related_name="sets_won")
    number = models.PositiveSmallIntegerField(
        _("Association"),
        default=1,
        choices=choices
    )

    def heavyFirstPart(self):
        first_part_games = []
        for g in self.games.all():
            first_part_games.append(g)
            if g.number > 4:
                break

        total_points = 0
        for fg in first_part_games:
            points = fg.getTennisPoints()
            total_points += len(points)
        return float(total_points)/4. > 8

    def getNumber(self):
        return self.number

    def getPrevGame(self, game):

        for g in self.games.all():
            if(g.number == game.number - 1):
                return g

        return None

    def getScore(self, game=None):
        score = [0, 0]
        for g in self.games.all():
            if g.winner == self.match.player0:
                score[0] += 1
            elif g.winner == self.match.player1:
                score[1] += 1
            if g == game:
                break

        return score

    class Meta:
        unique_together = [
            ('match', 'number'),
        ]
        ordering = ['number']


class Game(models.Model):

    choices = (
        (1, "1"),
        (2, "2"),
        (3, "3"),
        (4, "4"),
        (5, "5"),
        (6, "6"),
        (7, "7"),
        (8, "8"),
        (9, "9"),
        (10, "10"),
        (11, "11"),
        (12, "12"),
        (13, "13"),
    )

    set = models.ForeignKey(Set, related_name="games")
    number = models.PositiveSmallIntegerField(
        _("Association"),
        default=1,
        choices=choices
    )
    server = models.ForeignKey(Player, related_name="+")
    receiver = models.ForeignKey(Player, related_name="+")
    winner = models.ForeignKey(Player, null=True, related_name="games_won")
    finished = models.BooleanField(_("Finished"), default=False)

    def leaderToServeNext(self):
        s = self.getScore()
        if s[0] > s[1]:
            return self.set.match.player1 == self.server
        elif s[1] > s[0]:
            return self.set.match.player0 == self.server
        else:
            return False

    def hardFirstPart(self):
        return self.set.heavyFirstPart() and self.closeToSetEnd()

    def isLastSetGame(self):
        return (self.number == 12) or (self.set.winner is not None)

    def isLong(self):
        return len(self.getTennisPoints()) > 8

    def afterlongGame(self):
        prev_game = self.set.getPrevGame(self)
        if(prev_game):
            return prev_game.isLong()
        else:
            return False

    def afterBreak(self):
        prev_game = self.set.getPrevGame(self)
        if(prev_game):
            return prev_game.isBreak()
        else:
            return False

    def bigGap(self):
        s1, s2 = self.set.getScore(self)
        return abs(s1 - s2) >= 3, abs(s1 - s2)

    def closeToSetStart(self):
        s1, s2 = self.set.getScore(self)
        return (s1 + s2) <= 4

    def closeToSetEnd(self):
        s1, s2 = self.set.getScore(self)
        return (12 - (s1 + s2) <= 5) or (s1 >= 5 or s2 >= 5)

    def getNumber(self):
        return self.number

    def isOdd(self):
        return len(self.getTennisPoints()) == 4

    def toDeuce(self):
        return len(self.getTennisPoints()) >= 6

    def toLove(self):
        return len(self.getTennisPoints()) == 3

    def isBreak(self):
        return self.winner and self.server != self.winner

    def getScore(self):
        return self.set.getScore(self)

    def getTennisPoints(self, with_breaks=False):

        p1_sum = 0
        p2_sum = 0
        ret = []
        breakpoints = 0

        if self.number == 13:
            for p in self.points.all():
                from_serve = p.player == self.server
                p1_sum += int(from_serve)
                p2_sum += int(not from_serve)

                ret.append([p1_sum, p2_sum])
            if with_breaks:
                return ret, 0
            else:
                return ret
        else:
            for p in self.points.all():
                from_serve = p.player == self.server
                p1_sum += int(from_serve)
                p2_sum += int(not from_serve)
                is_breakpoint = p2_sum >= 3 and p2_sum > p1_sum
                if is_breakpoint and not from_serve:
                    breakpoints += 1
                if (p1_sum + p2_sum) >= 7:
                    s1 = p1_sum
                    s2 = p2_sum
                    p1_sum = 4 if s1 > s2 else 3
                    p2_sum = 4 if s2 > s1 else 3
                else:
                    if p1_sum >= 4:
                        p1_sum = 3

                    if p2_sum >= 4:
                        p2_sum = 3
                ret.append([
                    settings.TENNIS_POINTS[p1_sum],
                    settings.TENNIS_POINTS[p2_sum]
                ])
            if with_breaks:
                return ret[:-1], breakpoints
            else:
                return ret[:-1]

    class Meta:
        unique_together = [
            ('set', 'number', 'server', 'receiver'),
        ]
        ordering = ['number']


class Point(models.Model):
    game = models.ForeignKey(Game, related_name="points")
    player = models.ForeignKey(Player, related_name="+")
    number = models.PositiveIntegerField()
    # Ace
    ace = models.BooleanField(default=False)
    # Double fault
    dbl = models.BooleanField(default=False)

    class Meta:
        unique_together = [
            ('game', 'number', 'player'),
        ]
        ordering = ['number']


class BetSerie(models.Model):
    
    step = models.PositiveIntegerField(default=1)
    finished = models.BooleanField(default=False)
    bet = models.ForeignKey('Bet', related_name="series", null=True)
    summ = models.FloatField(default=0., null=True)
    start_ts = models.DateTimeField(
        _("Started on"),
        auto_now_add=True,
        null=True
    )
    
    stake = models.FloatField(default=0., null=True)

    def finish(self):
        self.finished = True
        self.save()
    

class BetSelection:

    DEUCE = 1
    MATCH_WINNER = 2
    MATCH_WINNER_LIVE = 3
    choices = (
        (DEUCE, 'Deuce'),
        (MATCH_WINNER, 'Match winner'),
        (MATCH_WINNER_LIVE, 'match winner live'),
    )


class BetStatus:

    SET = 1
    WON = 2
    LOST = 3
    RETURN = 4
    NOT_FOUND = 5
    PROCESSED = 6
    
    choices = (
        (SET, 'Set'),
        (WON, 'Won'),
        (LOST, 'Lost'),
        (RETURN, 'Return'),
        (PROCESSED, 'Processed'),
    )


class Bet(models.Model):

    serie = models.ForeignKey(BetSerie, related_name="serie_bets", null=True)
    serie_step = models.PositiveSmallIntegerField(null=True)

    match = models.ForeignKey(Match, related_name="match_bets")

    winner = models.ForeignKey(Player, related_name="won_bets", null=True)

    winner_data1 = jsonfield.JSONField(null=True, default={})
    winner_data2 = jsonfield.JSONField(null=True, default={})

    winner_data1_surface = jsonfield.JSONField(null=True, default={})
    winner_data2_surface = jsonfield.JSONField(null=True, default={})

    winner_data1_recent = jsonfield.JSONField(null=True, default={})
    winner_data2_recent = jsonfield.JSONField(null=True, default={})

    set = models.PositiveSmallIntegerField(
        _("Set"),
        choices=Set.choices
    )

    game = models.PositiveSmallIntegerField(
        _("Game"),
        choices=Game.choices
    )

    selection = models.PositiveSmallIntegerField(
        _("Selection"),
        choices=BetSelection.choices
    )

    status = models.PositiveSmallIntegerField(
        _("Selection"),
        default=BetStatus.SET,
        choices=BetStatus.choices
    )

    ts_created = models.DateTimeField(
        auto_now_add=True
    )

    odd = models.FloatField(default=0., null=True)
    stake = models.FloatField(default=0., null=True)

    retries_num = models.PositiveSmallIntegerField(
        _("Number of bet retries by bot"),
        default=0,
    )

    def isWon(self):
        return self.winner == self.match.winner

    def isLost(self):
        return self.match.winner and (self.winner != self.match.winner)

    def isVoid(self):
        return self.status == BetStatus.RETURN
    
    def setLost(self):
        self.status = BetStatus.LOST
        self.save()

    def setWon(self):
        self.status = BetStatus.WON
        self.save()

    def setReturn(self):
        self.status = BetStatus.RETURN
        self.save()

    def setProcessed(self):
        self.status = BetStatus.PROCESSED
        self.save()
        
    class Meta:

        unique_together = (
            ('match', 'set', 'game', 'selection'),
        )


def getX(d1, d2):

    to_love_points = d1['point_stats'].get('40-0', 0) - d2['point_stats'].get('40-0', 0)
    to_odd_points = d1['point_stats'].get('40-15', 0) - d2['point_stats'].get('40-15', 0)
    to_30_points = d1['point_stats'].get('40-30', 0) - d2['point_stats'].get('40-30', 0)
    to_deuce_points = d1['point_stats'].get('A-40', 0) - d2['point_stats'].get('A-40', 0)

    break_deuce_points = d1['point_stats'].get('40-A', 0) - d2['point_stats'].get('40-A', 0)
    break_love_points = d1['point_stats'].get('0-40', 0) - d2['point_stats'].get('0-40', 0)
    break_odd_points = d1['point_stats'].get('15-40', 0) - d2['point_stats'].get('15-40', 0)
    break_30_points = d1['point_stats'].get('30-40', 0) - d2['point_stats'].get('30-40', 0)

    # Receive points = +
    r_breaks_to_love = d1['receive_stats'].get('0-40', 0) - d2['receive_stats'].get('0-40', 0)
    r_breaks_to_15 = d1['receive_stats'].get('15-40', 0) - d2['receive_stats'].get('15-40', 0)
    r_breaks_to_30 = d1['receive_stats'].get('30-40', 0) - d2['receive_stats'].get('30-40', 0)
    r_breaks_to_deuce = d1['receive_stats'].get('40-A', 0) - d2['receive_stats'].get('40-A', 0)

    # -
    r_loses_to_love = d1['receive_stats'].get('40-0', 0) - d2['receive_stats'].get('40-0', 0)
    r_loses_to_15 = d1['receive_stats'].get('40-15', 0) - d2['receive_stats'].get('40-15', 0)
    r_loses_to_30 = d1['receive_stats'].get('40-30', 0) - d2['receive_stats'].get('40-30', 0)
    r_loses_to_deuce = d1['receive_stats'].get('A-40', 0) - d2['receive_stats'].get('A-40', 0)

    #Rank
    if d1['rank'] > 0 and d2['rank'] > 0:
        rank = 1./math.log(1+d1['rank'], 10000) - 1./math.log(1+d2['rank'], 10000)
    else:
        rank = 0

    # BP
    bp_won = 0
    if d1.get('bp_won', 0) > 0 and d2.get('bp_won', 0) > 0:
        bp_won = d1['bp_won'] - d2['bp_won']

    data = (
        to_love_points,
        to_odd_points,
        to_30_points,
        to_deuce_points,
        break_deuce_points,
        break_love_points,
        break_odd_points,
        break_30_points,
        r_breaks_to_love,
        r_breaks_to_15,
        r_breaks_to_30,
        r_breaks_to_deuce,
        r_loses_to_love,
        r_loses_to_15,
        r_loses_to_30,
        r_loses_to_deuce,
        rank,
        #bp_won
    )

    return data


def tiePercent(data):
    serve_tiebreak_won = 0
    serve_tiebreak_lost = 0

    for k, v in data['point_stats'].items():
        score1, score2 = k.split('-')
        try:
            score1, score2 = map(int, [score1, score2])
        except:
            continue
        is_tiebreak = (score1 > 0 or score2 > 0) and (score1 < 15 and score2 < 15)

        if is_tiebreak:
            serve_tiebreak_won += score1
            serve_tiebreak_lost += score2

    for k, v in data['receive_stats'].items():
        score1, score2 = k.split('-')
        try:
            score1, score2 = map(int, [score1, score2])
        except:
            continue
        is_tiebreak = (score1 > 0 or score2 > 0) and (score1 < 15 and score2 < 15)

        if is_tiebreak:
            serve_tiebreak_won += score2
            serve_tiebreak_lost += score1

    percent = 0.
    if serve_tiebreak_won + serve_tiebreak_lost == 0:
        percent = 50.
    else:
        percent = float(serve_tiebreak_won) / (float(serve_tiebreak_won) + float(serve_tiebreak_lost)) * 100.

    return percent
