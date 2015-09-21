import requests
import threading
import random
import time
import re
import os

from datetime import datetime
import BeautifulSoup
import xml.etree.ElementTree as ET
from fractions import Fraction
from selenium import webdriver

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
    Gender,
    SurfaceType,
    HARDS,
    CLAYS,
    GRASS
)

MATCH_THREADS = {}
MATCH_THREADS_LAST_CHANCES = {}

point_re = re.compile(
    '^Game\s+(\d+)\s+-\s+Point\s+(\d+)\s+-\s+(.*?)$',
    re.DOTALL | re.IGNORECASE
)

tb_point_re = re.compile(
    '^Tie Break\s+-\s+Point\s+(\d+)\s+won\s+by\s+(.*?)$',
    re.DOTALL | re.IGNORECASE
)

game_win_re = re.compile(
    "^Set\s+(\d)+\s+Game\s+(\d+)+\s(.*?)(holds|breaks)\s+to\s+"
)
itf_gender_re = re.compile("^F\d+$")

  
class Message:
    def __init__(self, m):
        self.id = int(m.get('id'))
        self.type = m.get('type')
        self.text = m.text
        try:
            self.set = int(m.get('period').replace('st', ''))
        except:
            self.set = 0
        self.game = 0
        pos = self.text.find('Game')
        if pos >= 0:
            self.game = int(self.text[pos:].split()[1])

    def isMatchStart(self):
        return self.text == 'Match'

    def isFirstServer(self):
        return self.text.find('to serve first') >= 0

    def isGameEnd(self):
        return self.text.find('Set') >= 0 and self.text.find('Game') >= 0

    def isPoint(self):
        return (self.text.find('Point') >= 0
                and
                not self.text.startswith('Tie')) and self.set > 0

    def isTieBreakPoint(self):
        return self.text.startswith('Tie Break - ') and self.set > 0

    def isBreak(self):
        return self.type == 'brk'

    def isDouble(self):
        return self.type == 'dbl'

    def isAce(self):
        return self.type == 'ace'

    def isMatchWinner(self):
        return self.text.find('Match won by') >= 0

    def isGameWinner(self):
        return self.text.find(' Game ') >= 0 and self.text.find('Set ') >= 0

    def __str__(self):

        return """### Message:
ID: %d
Type: %s
Game: %d
Set: %d
Text: %s""" % (self.id, self.type, self.game, self.set, self.text)


def loadMatchXML(url):
    headers = {
        'User-Agent': settings.USER_AGENT,
    }
    try:
        r = requests.get(url, headers=headers)
        return r.text.encode('utf-8')

    except Exception, e:
        print "Unable to fetch URL", url, e
        return None


@transaction.commit_on_success
def my_get_or_create(cls, arg):

    try:
        obj = cls.objects.create(**arg)
    except IntegrityError:
        transaction.commit()
        obj = cls.objects.get(**arg)

    return obj


def loadMatchData(xml, tournament_pk, match_pk):

    root = ET.fromstring(xml)
    players = {}
    players_ids = {}

    for player in root.iter('competitor'):
        name = player.text.strip()
        if name.endswith('.'):
            name = name[:-1]
        p, created = Player.objects.get_or_create(name=name)
        players[p.name] = p
        players_ids[int(player.get('id'))] = p

    if len(players) == 2:
        m = root.find('messages')

        if len(m) > 0:
            msgs = m.findall('msg')
            msgs.reverse()
            i = 0
            messages = []
            for m in msgs:
                messages.append(Message(m))
                i += 1

            match, created = Match.objects.get_or_create(
                tournament_id=tournament_pk,
                player0=players_ids[0],
                player1=players_ids[1],
                wh_match_id=match_pk
            )

            if created:
                print "Match created, generating player surface data"
                has_surface = True
                if match.tournament.surface in HARDS:
                    target_surfaces = HARDS
                elif match.tournament.surface in CLAYS:
                    target_surfaces = CLAYS
                elif match.tournament.surface in GRASS:
                    target_surfaces = GRASS
                else:
                    print "Unknown surface: ", match.pk
                    has_surface = False

                if has_surface:
                    d1 = match.player0.get_winner_data(
                        match.start_ts,
                        target_surfaces
                    )
                    d2 = match.player1.get_winner_data(
                        match.start_ts,
                        target_surfaces
                    )
                    match.winner_data1_surface = d1
                    match.winner_data2_surface = d2

                    match.winner_data1_surface_size = d1.get('num_games', 0)
                    match.winner_data2_surface_size = d2.get('num_games', 0)
                    match.save()

                n1 = players_ids[0].getName()
                n2 = players_ids[1].getName()
                if n1.find('/') >= 0 and n2.find('/') >= 0:
                    match.setDoubles()

                match.player0_rank = players_ids[0].rank
                match.player1_rank = players_ids[1].rank

                match.player0_points = players_ids[0].points
                match.player1_points = players_ids[1].points

                if match.singles:
                    if match.player0_rank == 0:
                        match.player0_rank = players_ids[0].getCurrentRank()
                        print "Player {0} rank loaded successfully: {1}".format(n1, match.player0_rank)
                    

                    if match.player1_rank == 0:
                        match.player1_rank = players_ids[1].getCurrentRank()
                        print "Player {0} rank loaded successfully: {1}".format(n1, match.player0_rank)
                    
                match.save()

            if (not match.player0_odd or not match.player1_odd):
                print "Missing odds, trying to load..."
                res = match.load_match_bets()

            match.make_winner_bet()

            match_game_number = 0
            parsed_set_games = {}

            for msg in messages:

                if msg.isMatchStart():
                    match.setStarted()

                elif msg.isMatchWinner():
                    winner = msg.text.replace('Match won by ', '').strip()

                    if winner == match.player0.name:
                        match.setConsistent()
                        match.winner = match.player0
                        match.finished = True
                        match.save()

                        point, created = Point.objects.get_or_create(
                            game=game,
                            player=match.winner,
                            number=p_num + 1,
                            # ace=prev_msg.isAce(),
                            # dbl=prev_msg.isDouble(),
                        )

                        game.winner = match.player0
                        game.finished = True
                        game.save()
                        return True, True

                    elif winner == match.player1.name:
                        match.setConsistent()
                        match.winner = match.player1
                        match.finished = True
                        match.save()

                        point, created = Point.objects.get_or_create(
                            game=game,
                            player=match.winner,
                            number=p_num + 1,
                            # ace=prev_msg.isAce(),
                            # dbl=prev_msg.isDouble(),
                        )
                        game.winner = match.player1
                        game.finished = True
                        game.save()

                        return True, True
                    else:
                        match.setInconsistent()
                        return False, True

                elif msg.isGameWinner():
                    (g_set, g_game, player, act) = game_win_re.match(
                        msg.text
                    ).groups()

                    g_set = int(g_set)
                    g_game = int(g_game)
                    player = player.strip()

                    if (game.number == g_game) and (s.number == g_set) or (g_game == 0):

                        if player == match.player0.name:
                            game.winner = match.player0
                        elif player == match.player1.name:
                            game.winner = match.player1
                        else:
                            print "Error in game winner: ", match.wh_match_id
                            continue

                        game.finished = True
                        game.save()

                    else:
                        print "Error in game winner(2)", match.wh_match_id

                elif msg.isFirstServer():

                    match.setStarted()

                    server = msg.text.replace(' to serve first', '').strip()
                    if server.find('/') >= 0:
                        match.setDoubles()

                    if server == match.player0.name:
                        match.odd_game_server = match.player0
                        match.odd_game_receiver = match.player1

                    elif server == match.player1.name:
                        match.odd_game_server = match.player1
                        match.odd_game_receiver = match.player0

                    else:
                        print "Unable to get server!!", match.wh_match_id
                        match.setInconsistent()
                        return False, False

                elif msg.isPoint() or msg.isTieBreakPoint():
                    if not match.started:
                        match.setInconsistent()
                        return False, False

                    s, created = Set.objects.get_or_create(
                        match=match,
                        number=msg.set
                    )

                    if msg.set not in parsed_set_games.keys():
                        parsed_set_games[msg.set] = []

                    if msg.isTieBreakPoint():
                        mm = tb_point_re.match(msg.text)
                        (p_num, pl) = mm.groups()
                        game_n = 13

                    else:
                        mm = point_re.match(msg.text)
                        (game_n, p_num, pl) = mm.groups()
                        game_n = int(game_n)

                    if not mm:
                        # print "Unmatched point in game: ", msg.game, msg.text
                        continue

                    p_num = int(p_num)

                    # New game
                    if game_n not in parsed_set_games[msg.set]:
                        # validate!
                        if len(parsed_set_games[msg.set]) == 0:
                            if game_n != 1:
                                match.setInconsistent()
                                return False, False
                        else:
                            if game_n - parsed_set_games[msg.set][-1] != 1:
                                match.setInconsistent()
                                return False, False

                        parsed_set_games[msg.set].append(game_n)
                        match_game_number += 1

                    (server, receiver) = match.getGameServerReceiver(
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
                        # ace=prev_msg.isAce(),
                        # dbl=prev_msg.isDouble(),
                    )

                prev_msg = msg

            match.setConsistent()
            return True, False

    return False, False


class MatchThread(threading.Thread):

    def __init__(self, match_id, t):
        super(MatchThread, self).__init__()
        self._stop = threading.Event()
        self.match_id = match_id
        self.tournament_pk = t.pk
        self.tournament_title = t.title

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

    def run(self):

        url = settings.INFO_BASE_URL + self.match_id

        while 1:
            # print "Match thread %s is running" % ( self.match_id )
            print "Loading:", url
            xml = loadMatchXML(url)
            if xml:
                tournament_dir_success = os.path.join(
                    settings.DATADIR_SUCCES_BASE,
                    self.tournament_title
                )
                tournament_dir_error = os.path.join(
                    settings.DATADIR_ERROR_BASE,
                    self.tournament_title
                )

                if not os.path.exists(tournament_dir_success):
                    try:
                        os.mkdir(tournament_dir_success)
                    except:
                        pass

                if not os.path.exists(tournament_dir_error):
                    try:
                        os.mkdir(tournament_dir_error)
                    except:
                        pass

                match_xml_file = os.path.join(
                    tournament_dir_success,
                    "match_{0}.xml".format(self.match_id)
                )

                with open(match_xml_file, "w") as f:
                    f.write(xml)

                if 1:
                    save_error = False
                    finished = False
                    # good, finished = loadMatchData(xml, self.tournament_pk, self.match_id)
                    try:
                        good, finished = loadMatchData(xml, self.tournament_pk, self.match_id)
                        save_error = not good
                    except Exception, e:
                        save_error = True
                        print "Failed to load match data from XML: {0} ({1})".format(url, e)

                    if finished:
                        self.stop()

                    if save_error:
                        match_xml_file = os.path.join(
                            tournament_dir_success,
                            "match_error_{0}.xml".format(self.match_id)
                        )

                        with open(match_xml_file, "w") as f:
                            f.write(xml)

                if self.stopped():
                    # print "Terminating match thread %s" % (self.match_id)
                    break

            time.sleep(15)


def extract_tournaments_and_matches(html):
    soup = BeautifulSoup.BeautifulSoup(html)
    o2 = soup.findAll('div', {'id': re.compile('ip_type_(\d+)$')})
    running_matches = []

    for competition in o2:
        h3 = competition.find('h3')
        a = h3.find('a')
        competition_id = int(competition.attrMap['id'].split('_')[2])
        competition_title = a.text
        title = None
        assoc = AssociationType.UNK
        title = competition_title

        words = title.split()
        qualifying = "Qualifying" in words

        if "ITF" in words:
            gender = Gender.FEMALE
            assoc = AssociationType.ITF
            for w in words:
                if itf_gender_re.match(w):
                    gender = Gender.MALE
                    break

        elif "ATP" in words:
            assoc = AssociationType.ATP
            gender = Gender.MALE
        elif "WTA" in words:
            assoc = AssociationType.WTA
            gender = Gender.FEMALE
        elif title == "Davis Cup":
            assoc = AssociationType.ATP
            gender = Gender.MALE
        elif title == "Czech Extraliga":
            assoc = AssociationType.ATP
            gender = Gender.MALE
        elif title.find("Men's French Open") >= 0:
            assoc = AssociationType.ATP
            gender = Gender.MALE

        elif title.find("Gentlemen's Wimbledon Singles") >= 0:
            assoc = AssociationType.ATP
            gender = Gender.MALE

        elif title.find("Men's Australian Open") >= 0:
            assoc = AssociationType.ATP
            gender = Gender.MALE

        elif title.find("Women's Australian Open") >= 0:
            assoc = AssociationType.WTA
            gender = Gender.FEMALE

        elif title.find("Ladies' Wimbledon Singles") >= 0:
            assoc = AssociationType.WTA
            gender = Gender.FEMALE

        elif title.find("Women's French Open") >= 0:
            assoc = AssociationType.WTA
            gender = Gender.FEMALE

        elif title.find("Men's US Open") >= 0:
            assoc = AssociationType.ATP
            gender = Gender.MALE
            
        elif title.find("Women's US Open") >= 0:
            assoc = AssociationType.WTA
            gender = Gender.FEMALE

        else:
            print "Unknown league:", title
            continue

        tournament, created = Tournament.objects.get_or_create(
            title=competition_title,
            association=assoc,
            gender=gender,
            qualifying=qualifying
        )

        if created or tournament.surface == SurfaceType.UNK:
            tournament.load_surface()

        matches_table = competition.find('table')
        matches = matches_table.findAll('tr', {"class": "rowLive"})

        if len(matches) > 0:
            for m in matches:
                match_id = m.attrMap['id'].split('_')[2]
                running_matches.append(match_id)
                odds = m.findAll('div', {'class': 'eventprice'})
                if len(odds) == 2:
                    p0_odd = odds[0].text
                    p1_odd = odds[1].text

                    try:
                        p0_odd = float(Fraction(p0_odd)) + 1.0
                        p1_odd = float(Fraction(p1_odd)) + 1.0
                    except:
                        p0_odd = 0
                        p1_odd = 0
                    live_m = Match.objects.filter(wh_match_id=match_id)
                    if len(live_m):
                        live_m = live_m[0]
                        if not live_m.player0_max_live_odd or (p0_odd > live_m.player0_max_live_odd):
                            live_m.player0_max_live_odd = p0_odd
                            live_m.save()

                        if not live_m.player1_max_live_odd or (p1_odd > live_m.player1_max_live_odd):
                            live_m.player1_max_live_odd = p1_odd
                            live_m.save()
                    print "Live odds: ", p0_odd, p1_odd, match_id
                if match_id not in MATCH_THREADS.keys():
                    print "Starting thread for match {0} on {1}"\
                        .format(match_id, tournament.surface)
                    t = MatchThread(match_id, tournament)
                    t.setDaemon(True)
                    t.start()
                    MATCH_THREADS[match_id] = t

    print u"{0} Threads running [{1}]".format(len(MATCH_THREADS.keys()), ",".join(MATCH_THREADS.keys()))
    for m_id in MATCH_THREADS.keys():
        if not MATCH_THREADS[m_id].isAlive():
            MATCH_THREADS[m_id].stop()
            del MATCH_THREADS[m_id]
            continue
        if m_id not in running_matches:
            if m_id not in MATCH_THREADS_LAST_CHANCES.keys():
                MATCH_THREADS_LAST_CHANCES[m_id] = 0
            else:
                n = MATCH_THREADS_LAST_CHANCES[m_id]
                if n > 5:
                    MATCH_THREADS[m_id].stop()
                    del MATCH_THREADS[m_id]
                else:
                    MATCH_THREADS_LAST_CHANCES[m_id] += 1

    return 0


class Command(BaseCommand):

    requires_model_validation = True

    def handle(self, *args, **options):

        headers = {
            'User-Agent': settings.USER_AGENT,
        }
        print "Starting data collection..."
        # Rebuild database
        if 0:
            for m in Match.objects.all():
                t = m.tournament
                words = t.title.split()
                t.qualifying = "Qualifying" in words

                if t.association == 0:
                    t.gender = 0
                elif t.association == 1:
                    t.gender = 1
                elif t.association == 2:
                    t.gender = Gender.FEMALE
                    for w in words:
                        if itf_gender_re.match(w):
                            t.gender = Gender.MALE
                            break
                else:
                    print "WTF?", t.pk

                t.save()
                if 1:
                    tournament_dir_success = os.path.join(settings.DATADIR_SUCCES_BASE, t.title)
                    match_xml_file_1 = os.path.join(tournament_dir_success, "match_{0}.xml".format(m.wh_match_id))
                    match_xml_file_2 = os.path.join(tournament_dir_success, "match_error_{0}.xml".format(m.wh_match_id))
                    if os.path.exists(match_xml_file_1):
                        try:
                            xml = open(match_xml_file_1).read()
                            loadMatchData(xml, t.pk, m.wh_match_id)
                        except:
                            print "Malformed match(1): ", m.wh_match_id
                    elif os.path.exists(match_xml_file_1):
                        try:
                            xml = open(match_xml_file_1).read()
                            loadMatchData(xml, t.pk, m.wh_match_id)
                        except:
                            print "Malformed match(2): ", m.wh_match_id
                    else:
                        print "3"

        if 0:
            Tournament.objects.all().delete()

            t, c = Tournament.objects.get_or_create(
                title="TEST",
                association=0
            )

            t = Tournament.objects.all()[0]
            Match.objects.all().delete()

        while 1:

            print "Fetching matches..."
            loaded = False
            try:
                driver = webdriver.PhantomJS(executable_path=settings.PHANTOM_BIN)
                # r = requests.get(settings.TENNIS_URL, headers=headers)
                driver.get(settings.TENNIS_URL)
                source = driver.page_source
                loaded = True
            except:
                print "Unable to fetch ", settings.TENNIS_URL
            finally:
        	try:
            	    driver.close()
            	    driver.quit()
		except:
		    pass
		    
            if loaded:
                extract_tournaments_and_matches(source)
            sleep_time = random.randint(settings.TIMEOUT, settings.TIMEOUT * 5)
            time.sleep(sleep_time)

        return "OK"
