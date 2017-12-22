#!/usr/bin/env python3

"""Rudolph: Pair kiddos with Secret Santas

Usage: rudolph.py --run

Reads the list of participants from ../data/secret-santa.csv. The CSV file must
have column headings, and a column named 'Email'. The first column MUST be the
names of the participants.

NOTE: Change the subject line and other globals before running the script.

"""

import getpass
from os.path import abspath, dirname, exists, join
import random
import smtplib
from textwrap import dedent

import pandas as pd

SENDER = "Fun Committee, TIKS"
SUBJECT = "TIKS Secret Santa 2017"
BODY = dedent("""
Dear {santa},

Wish you Merry Christmas and a Happy New Year!

Your secret santa kiddo is *{kiddo}*!

We'll exchange gifts on the 30th of December at practice. If you can't make it
on that day, please find another means of doing this.

We hope that you'll be a good santa and give your kiddo an apt gift.

Regards,
{from}

Secret Santa is powered by Rudolph --
https://github.com/punchagan/thatte-idli/blob/master/scripts/rudolph.py

""")
HEADERS = """\
From: {from} <{from_id}>\r
To: {santa} <{santa_id}>\r
Subject: {subject}\r
\r
"""
HERE = dirname(abspath(__file__))
PEOPLE = join(HERE, '..', 'data', 'secret-santa.csv')


def get_people():
    """Reads list of participants from ../data/secret-santa.csv

    The CSV file needs to have column headers and a column named 'Email'. The
    first column MUST be the names of the participants.

    """
    if exists(PEOPLE):
        people = pd.read_csv(PEOPLE, index_col=0)['Email'].to_dict()
    else:
        people = {
            'foo': 'foo@example.com',
            'bar': 'bar@example.com',
            'baz': 'baz@example.com',
        }
    return people


def is_good_pairing(pairs):
    """Function to test if a pairing is valid."""
    santas = set()
    kiddos = set()

    for santa, kiddo in pairs:
        if santa == kiddo:
            return False
        santas.add(santa)
        kiddos.add(kiddo)

    return len(santas) == len(kiddos) == len(list(pairs))


def pick_pairs(people):
    """Pick pairs from a given name:email mapping."""
    n = len(people)
    m = n//2
    names = list(people.keys())
    santas = random.sample(names, n)
    santas_1, santas_2 = random.sample(santas[:m], m), random.sample(santas[m:], n-m)
    kiddos_1, kiddos_2 = santas[n-m:], santas[:n-m]
    return list(zip(santas_1, kiddos_1)) + list(zip(santas_2, kiddos_2))


def notify_santa(**kwargs):
    """Notify a Santa about their kiddo."""
    email = HEADERS + BODY
    msg = email.format(**kwargs)
    from_id = kwargs['from_id']
    password = kwargs['password']
    to_id = kwargs['santa_id']

    if not kwargs.get('password'):
        print(msg)
        print(from_id, password, to_id)

    else:
        send_email(from_id, password, to_id, msg)


def send_email(from_id, password, to_id, msg, host='smtp.gmail.com', port=587):
    """Send an email."""
    mail = smtplib.SMTP(host, port)
    mail.ehlo()
    mail.starttls()
    mail.login(from_id, password)
    mail.sendmail(from_id, to_id, msg)
    mail.close()


def persist_pairs(pairs):
    """Persist the pairing data to disk

    Ideally, this data needn't/shouldn't be persisted, but in case of any
    problems, this would be good to have around.

    """
    PAIRS = join(HERE, '..', 'data', 'secret-santa-paired-people.pkl')
    pd.Series(dict(pairs)).to_pickle(PAIRS)


def main(test=True):
    people = get_people()
    pairs = pick_pairs(people)
    assert is_good_pairing(pairs), 'Pairing is buggy!'

    if not test:
        persist_pairs(pairs)
        from_id = input("Your Email: ")
        password = getpass.getpass()

    else:
        from_id = password = None

    n = len(pairs)
    for i, (santa, kiddo) in enumerate(pairs, 1):
        santa_id = people[santa]
        print('Sending an e-mail to {} ({} of {})'.format(santa_id, i, n))
        notify_santa(**{
            'santa_id': santa_id,
            'santa': santa,
            'kiddo': kiddo,
            'from': SENDER,
            'from_id': from_id,
            'subject': SUBJECT,
            'password': password,
        })


if __name__ == '__main__':
    import sys
    test = len(sys.argv) != 2 or sys.argv[1] != '--run'
    main(test=test)
