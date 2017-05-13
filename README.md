# Python module for getting Wahlrecht.de polling data

Install:

     pip install wahlrecht

Run like this:

    $ python -m wahlrecht <jurisdiction> > output.csv

`jurisdiction` determines which kind of election will be downloaded. It can be a state election with a state slug (like 'baden-wuerttemberg') or for the federal election 'bund'.

Or just download everything:

    $ sh download.sh


Or use like this as a Python module.:

    from wahlrecht import get_state_polls

    for info in get_state_polls('nrw'):
        print(info)
