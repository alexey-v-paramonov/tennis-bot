from django.conf.urls import patterns, url

urlpatterns = patterns(
    'tennis.views',
    url(r'^index.html$', 'recent_matches', name="index"),
    url(r'^tournament/(\d+)/match/(\d+)', 'match', name="match"),
    url(r'^tournament/(\d+)', 'tournament', name="tournament"),
)
