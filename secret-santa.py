#!/usr/bin/env python3

"""Script to choose secret kiddos

Usage: secret-santa.py --run

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

We hope that you'll be a good santa and give your kiddo an apt gift.

Regards,
{from}

PS: Secret Santa is powered by Rudolph --
https://github.com/punchagan/thatte-idli/blob/master/scripts/secret-santa.py
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
    santas = set()
    kiddos = set()

    for santa, kiddo in pairs:
        if santa == kiddo: return False
        santas.add(santa)
        kiddos.add(kiddo)

    return len(santas) == len(kiddos) == len(list(pairs))


def pick_pairs(people):
    n = len(people)
    m = n//2
    names = list(people.keys())
    santas = random.sample(names, n)
    santas_1, santas_2 = santas[:m], santas[m:]
    kiddos_1, kiddos_2 = santas[n-m:], santas[:n-m]
    return list(zip(santas_1, kiddos_1)) + list(zip(santas_2, kiddos_2))


def notify_santa(**kwargs):
    email = HEADERS + BODY
    msg = email.format(**kwargs)
    from_id = kwargs['from_id']
    password = kwargs['password']
    to_id = kwargs['santa_id']
    print('Sending an e-mail to {}'.format(to_id))

    if not kwargs.get('password'):
        print(msg)
        print(from_id, password, to_id)

    else:
        send_email(from_id, password, to_id, msg)


def send_email(from_id, password, to_id, msg, host='smtp.gmail.com', port=587):
    mail = smtplib.SMTP(host, port)
    mail.ehlo()
    mail.starttls()
    mail.login(from_id, password)
    mail.sendmail(from_id, to_id, msg)
    mail.close()


def persist_pairs(pairs):
    PAIRS = join(HERE, '..', 'data', 'secret-santa-paired-people.pkl')
    pd.Series(dict(pairs)).to_pickle(PAIRS)


def main(test=True):
    people = get_people()
    pairs = pick_pairs(people)
    assert is_good_pairing(pairs), 'Pairing is buggy!'
    persist_pairs(pairs)

    if not test:
        from_id = input("Your Email: ")
        password = getpass.getpass()

    else:
        from_id = password = None

    for santa, kiddo in pairs:
        santa_id = people[santa]
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
