import requests

BASE_URL = 'http://www.wahlrecht.de'


def get_url(url):
    url = BASE_URL + url
    response = requests.get(url)
    response.encoding = 'utf-8'
    if response.status_code != 200:
        response.raise_for_status()
    return response.text


def download_state_election_polls(state):
    return get_url('/umfragen/landtage/%s.htm' % state)


def download_federal_election_polls():
    return get_url('/umfragen/laender.htm')
