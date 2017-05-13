import csv
import sys

from . import get_federal_polls, get_state_polls


def get_header_keys(keys):
    return set(keys) | {'client', 'count', 'institute'}


def write_csv(file, stream, writer=None):
    for row in stream:
        if writer is None:
            writer = csv.DictWriter(file, get_header_keys(row.keys()))
            writer.writeheader()
        writer.writerow(row)
    return writer


def main(jurisdiction):
    if jurisdiction == 'bund':
        stream = get_federal_polls()
    else:
        stream = get_state_polls(jurisdiction)
    write_csv(sys.stdout, stream)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Please give a state slug or "bund" as argument', file=sys.stderr)
        sys.exit(1)
    main(sys.argv[1])
