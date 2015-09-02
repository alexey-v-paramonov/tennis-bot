from datetime import datetime, timedelta, time, date as dt_date
from django.shortcuts import render_to_response, redirect
from django.conf import settings

from tennis.models import (
    Tournament,
    Match,
    Player,
    Bet,
    BetSelection,
    BetStatus
)


def index(request):

    return render_to_response(
        "index.html",
        {
            'tournaments': Tournament.objects.all(),
        }
    )


def tournament(request, tournament_pk):

    tournament = Tournament.objects.get(pk=tournament_pk)

    return render_to_response(
        "tournament.html",
        {
            'matches': tournament.matches.all(),
        }
    )

# def bet_won(request, bet_pk):

#     bet = Bet.objects.get(pk=bet_pk)
#     match = bet.match
#     match.winner = bet.winner
#     match.save()
#     return redirect('recent_matches')

# def bet_lost(request, bet_pk):

#     bet = Bet.objects.get(pk=bet_pk)
#     match = bet.match
#     match.winner = match.player1
#     if bet.winner == match.player0 else match.player0
#     match.save()
#     return redirect('recent_matches')

# def bet_void(request, bet_pk):

#     bet = Bet.objects.get(pk=bet_pk)
#     bet.status = BetStatus.RETURN
#     bet.save()
#     return redirect('recent_matches')


def recent_matches(request):

    today = datetime.now().date()
    yesterday = today - timedelta(1)
    today_start = datetime.combine(today, time())
    d = yesterday
    matches = Match.objects.filter(start_ts__gte=d).select_related(
        'tournament',
        'player0',
        'player1',
        'winner'
    ).order_by('-start_ts')
    result = 0
    for m in matches:
        bet = m.match_bets.first()

        if bet and bet.winner:
            bet.plus = bet.odd - 1
            m.bet = bet
            m.bet_on = bet.winner.name

            if bet.winner == m.winner:
                m.won = bet.odd - 1
                m.bet.plus = bet.odd - 1
                result += m.won
            elif m.winner and (bet.winner != m.winner):
                m.won = -1
                result += m.won

    DAYS = 60
    DAYS_H = []
    TOTAL = 0
    y2015 = dt_date(2015, 1, 1)
    for i in range(DAYS):
        date = datetime.today() - timedelta(i)
        if date.date() < y2015:
            continue
        bets = Bet.objects.filter(
            selection=BetSelection.MATCH_WINNER,
            winner__isnull=False,
            ts_created__range=(
                datetime.combine(date, time.min),
                datetime.combine(date, time.max)
            )
        ).order_by('-ts_created')
        total = 0
        for b in bets:
            if b.isWon():
                total += b.odd - 1
                TOTAL += b.odd - 1
            elif b.isLost():
                total -= 1
                TOTAL -= 1
        DAYS_H.append({'date': date.date(), 'total': total})

    return render_to_response(
        "recent_matches.html",
        {
            'matches': matches,
            'result': result,
            'daily': DAYS_H,
            'total': TOTAL
        }
    )


def match(request, tournament_pk, match_pk):

    tournament = Tournament.objects.get(pk=tournament_pk)
    match = Match.objects.get(pk=match_pk)

    return render_to_response(
        "match.html",
        {
            'match': match,
        }
    )


def player(request, player_pk):

    player = Player.objects.get(pk=player_pk)

    return render_to_response(
        "player.html",
        {
            'player': player,
        }
    )
