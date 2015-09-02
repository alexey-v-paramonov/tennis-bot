import re
import requests
import BeautifulSoup

from django.core.management import BaseCommand
from django.db.transaction import commit_on_success
from django.conf import settings
from django.db.models import Q

from tennis.models import (
    Tournament,
    AssociationType,
    Player,
    Match,
    Set,
    Game,
    Point,
    Gender,
    SurfaceType
)


class Command(BaseCommand):

    requires_model_validation = True

    @commit_on_success
    def handle(self, *args, **options):
        headers = {
            'User-Agent': settings.USER_AGENT,
        }

        i = 0
        tournaments = Tournament.objects.filter(
            association=AssociationType.ATP,
            country=None
        )
        for t in tournaments:
            i += 1
            print "Loading data for ", t.title, "[", t.id, "]", t.is_challenger(), i, " of ", len(tournaments)
            t.load_surface()
        return "OK"
