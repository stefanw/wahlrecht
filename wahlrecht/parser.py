from collections import defaultdict
from datetime import datetime, timedelta
import re

from lxml import html


MULTI_SPACE = re.compile('\s+')

BEFRAGTE_RE = re.compile(u'''
    (?P<kind>[TO])?
    (?:\s*•\s*)?
    (?:(?P<count>[\d\.]+)\s+)?
    (?:(?P<start>\d+\.\d+\.)\s*(?:[-–]\s*(?P<end>\d+\.\d+\.))?)?
    (?:KW\s*(?P<week>\d+))?
''', re.UNICODE | re.VERBOSE)

PARTY_PERCENT_RE = re.compile(r'''
    (?:(?P<party>[\w ]+\.?)\s+)?
    (?P<percent>[\d,]+)\s*\%\,?
''', re.UNICODE | re.VERBOSE)

INSTITUT_DATUM_RE = re.compile(r'''
    ^(?P<name>[^\(]+)
    (?:\s+\(?(?P<date>\d+\.\d+\.\d+)\)?)$
''', re.UNICODE | re.VERBOSE)
DATE_RE = re.compile(r'\d+\.\d+\.\d{4}')

COLUMNNAME_MAPPING = {
    'Quelle': 'client',
    'Institut': 'institute',
    'Auftraggeber': 'client',
    'Auftrag- geber': 'client',
    'Institut (Datum)': 'institute'
}

META_COLUMNS = ('institute', 'client', 'Befragte', 'Datum')

PARTYNAME_MAPPING = {
    'Sonst.': 'Sonstige'
}

INSTITUTE_MAPPING = {
    re.compile(r'Forschungs-[\s\n]*gruppe', re.M): 'Forschungsgruppe',
    re.compile('^dimap$'): 'Infratest dimap'
}

STATE_MAPPING = {
    'nrw': 'Nordrhein-Westfalen',
    'baden-wuerttemberg': 'Baden-Württemberg',
    'thueringen': 'Thüringen'
}


def get_state_name(state):
    return STATE_MAPPING.get(state, state.upper())


def get_text(cell):
    text = " ".join(x for x in cell.xpath('.//text()'))
    return MULTI_SPACE.sub(' ', text).strip()


def is_party_column(cell):
    if cell.attrib.get('class') == 'part':
        return True
    return bool(len(cell.xpath('./a')))


def parse_header_cell(cell):
    is_party = is_party_column(cell)
    label = get_text(cell) or None
    label = COLUMNNAME_MAPPING.get(label, label)
    if not is_party and label is not None and not any(
                                c in label for c in META_COLUMNS):
        is_party = True
    return {'label': label, 'party': is_party}


def parse_header(table):
    if len(table.xpath('./thead')) == 0:
        for row in table.xpath('./tbody//tr'):
            found_header_row = True
            for cell in row.xpath('./th'):
                if cell.attrib.get('colspan') is not None:
                    found_header_row = False
                    break
                yield parse_header_cell(cell)
            if found_header_row:
                break
    else:
        for cell in table.xpath('.//thead//th'):
            yield parse_header_cell(cell)


def parse_befragte(key, cell):
    text = get_text(cell)
    match = BEFRAGTE_RE.match(text)
    result = match.groupdict()
    if result.get('count'):
        result['count'] = int(result['count'].replace('.', ''))
    if result.get('week'):
        result['week'] = int(result['week'])
    return result


def parse_state_from_header(cell):
    text = get_text(cell)
    state_name = text.split('(')[0].strip()
    return state_name


def _parse_date(text):
    try:
        date = datetime.strptime(text, '%d.%m.%Y').isoformat()
    except ValueError:
        date = None
    return date


def parse_datum(key, cell):
    return {
        'date': _parse_date(get_text(cell))
    }


def parse_institute(key, cell):
    text = get_text(cell)
    match = INSTITUT_DATUM_RE.match(text)
    if match is not None:
        institute = fix_institute(match.group('name'))
        date = match.group('date')
        if len(date) == 8:
            date = datetime.strptime(date, '%d.%m.%y').isoformat()
        else:
            date = datetime.strptime(date, '%d.%m.%Y').isoformat()
        return {
            'date': date,
            'institute': institute
        }
    institute = text.strip()
    institute = fix_institute(institute)
    return {
        'institute': institute
    }


def fix_institute(name):
    for k, v in INSTITUTE_MAPPING.items():
        name = k.sub(v, name)
    return name


def parse_election(key, cell):
    text = get_text(cell)
    match = DATE_RE.search(text)
    if match is None:
        return {
            'date': None
        }
    return {
        'date': _parse_date(match.group(0))
    }


PARSE_FUNC = {
    'Befragte': parse_befragte,
    'Befragte Zeitraum': parse_befragte,
    'Datum': parse_datum,
    'institute': parse_institute,
    'election': parse_election
}


def parse_default(key, cell):
    return {key: get_text(cell)}


def clean_party_name(name):
    name = name.strip()
    return PARTYNAME_MAPPING.get(name, name)


def clean_percentage(text):
    if text in (u'\u2013', '?') or not text:
        return None
    return float(text.replace(',', '.').replace('%', '').strip())


def parse_party(name, cell):
    text = get_text(cell)
    matches = PARTY_PERCENT_RE.findall(text)
    return {
        clean_party_name(party or name): clean_percentage(percentage)
        for party, percentage in matches
    }


def fix_dates(date, year):
    if not date:
        return None
    date = date.split('.')[:-1]
    return datetime(year, int(date[1]), int(date[0])).isoformat()


def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return d + timedelta(days_ahead)


def get_start_end_of_kw(week_no, year):
    '''
    Converts KW to date range
    https://de.wikipedia.org/wiki/Woche#Kalenderwoche
    '''
    # Find the first thursday of the year (=First KW)
    thursday = next_weekday(datetime(year, 1, 1), 3)
    # Thursday of KW in question
    thursday += timedelta(days=(week_no - 1) * 7)
    # Return the monday til sunday
    return (thursday - timedelta(days=3), thursday + timedelta(days=3))


def parse_poll_row(ident, header, cells, remove_cols):
    info = {}
    for i, (key, cell) in enumerate(zip(header, cells)):
        if cell is None:
            continue
        if cell.attrib.get('rowspan') is not None:
            remove_cols[i] = int(cell.attrib['rowspan']) - 1
        if key['label'] is None:
            continue
        if key['party']:
            info.setdefault('results', {})
            info['results'].update(parse_party(key['label'], cell))
            continue
        parse_func = PARSE_FUNC.get(key['label'], parse_default)
        info.update(parse_func(key['label'], cell))
    if info['date'] is not None:
        year = int(info['date'].split('-')[0])
        info['start'] = fix_dates(info.get('start'), year)
        info['end'] = fix_dates(info.get('end'), year)
        week = info.pop('week', None)
        if week is not None:
            start, end = get_start_end_of_kw(week, year)
            info.update({'start': start.isoformat(), 'end': end.isoformat()})

    info.pop('week', None)
    return info


def parse_poll_table(ident, table):
    header_cells = list(parse_header(table))
    remove_cols = defaultdict(int)
    current_state = None
    for row in table.xpath('.//tbody/tr'):
        cells = row.xpath('./*')
        # cell_text = '|'.join([get_text(c) for c in cells if c is not None])
        # print(cell_text)
        # if current_state is not None and 'Thüringen' in current_state:
        # import ipdb; ipdb.set_trace()

        if len(cells) == 1 and cells[0].tag == 'th' and 'id' in cells[0].attrib:
            current_state = parse_state_from_header(cells[0])
            remove_cols = defaultdict(int)
        if len(cells) >= 1 and cells[0].tag == 'th':
            continue
        offset = int(cells[0].attrib.get('colspan', 1))

        custom_header = list(header_cells)
        for i, c in remove_cols.items():
            if c > 0:
                custom_header.pop(i)
                remove_cols[i] -= 1

        if len(cells) < len(custom_header):
            election_cell = [{'label': 'election', 'party': False}]
            custom_header = election_cell + custom_header[offset:]
            info = parse_poll_row(ident, custom_header, cells, remove_cols)
            info['start'] = None
            info['end'] = None
            info['kind'] = 'election'
            if current_state is not None:
                info['state'] = current_state
            else:
                info['state'] = ident
            info['site_id'] = '{}@{}@{}@{}'.format(ident, 'election',
                                                   info['date'], info['state'])
            yield info
            continue

        info = parse_poll_row(ident, custom_header, cells, remove_cols)
        info['kind'] = 'poll'
        if current_state is not None:
            info['state'] = current_state
        else:
            info['state'] = ident
        info['site_id'] = '{}@{}@{}@{}'.format(ident, info['institute'],
                                            info['date'], info['state'])
        yield info


def get_flat_results(row):
    info = dict(row)
    if info['date'] is None:
        return
    results = info.pop('results')
    for key, value in results.items():
        info = dict(info)
        info['party'] = key
        info['percentage'] = value
        yield info


def get_poll_results(ident, root):
    tables = root.xpath('//table[@class="wilko"]')
    uniques = set()
    for table in tables:
        gen = parse_poll_table(ident, table)
        for row in gen:
            if row['site_id'] in uniques:
                continue
            uniques.add(row['site_id'])
            for info in get_flat_results(row):
                info.setdefault('state', get_state_name(ident))
                info['jurisdiction'] = ident
                yield info


def get_polls(ident, text):
    root = html.fromstring(text)
    for info in get_poll_results(ident, root):
        yield info
