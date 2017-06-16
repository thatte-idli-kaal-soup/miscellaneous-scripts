#!/usr/bin/env python3
"""Script to create an iCal file with birthdays, from the roster csv.

Usage:

    ./birthdays.py /path/to/csv

"""

import csv
from datetime import datetime
from icalendar import Calendar, Event

DATE_FMT = '%d/%m/%Y'


def create_calendar():
    cal = Calendar()
    cal.add('prodid', '-//TIKS script//python//')
    cal.add('version', '2.0')
    return cal


def read_csv(info_csv):
    with open(info_csv) as f:
        reader = csv.reader(f)
        return [row[1:3] for row in reader][1:]


def add_event(calendar, event):
    name, date = event
    e = Event()
    e.add('summary', "{}'s birthday".format(name))
    e.add('dtstart', datetime.strptime(date, DATE_FMT))
    e.add('rrule', {'freq': 'yearly'})
    calendar.add_component(e)


def create_ical(info_csv):
    cal = create_calendar()
    birthdays = read_csv(info_csv)
    for birthday in birthdays:
        add_event(cal, birthday)
    with open('{}.ics'.format(info_csv), 'wb') as f:
        f.write(cal.to_ical())


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    create_ical(sys.argv[1])
