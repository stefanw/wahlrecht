__version__ = '0.0.2'

from .download import (download_state_election_polls,
                       download_federal_election_polls)
from .parser import get_polls


def get_state_polls(state):
    html = download_state_election_polls(state)
    for info in get_polls(state, html):
        yield info


def get_federal_polls():
    html = download_federal_election_polls()
    for info in get_polls('bund', html):
        yield info
