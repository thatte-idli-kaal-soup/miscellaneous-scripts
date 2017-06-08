#!/usr/bin/env python3

"""Script to roster players from a CSV file to an event.

Usage:
    {program} /path/to/csv event_url

The CSV file should have the following columns:
    Gender, Full Name, Email

"""

from collections import namedtuple
import csv
from os.path import abspath, dirname, join
import time

HERE = dirname(abspath(__file__))
Player = namedtuple('Player', ('first_name', 'last_name', 'gender', 'email'))

# Helpers

def _login(driver):
    email, password = _read_config()
    email_field = driver.find_element_by_name('signin[email]')
    email_field.send_keys(email)
    password_field = driver.find_element_by_name('signin[password]')
    password_field.send_keys(password)
    form = driver.find_element_by_class_name('signin')
    form.submit()

def _open_event(url):
    from selenium import webdriver
    driver = webdriver.Chrome()
    driver.get(url)
    _login(driver)
    return driver


def _add_player(browser, player):
    create = browser.find_element_by_link_text('"Create {}"'.format(player.email))
    create.click()
    time.sleep(3)
    gender = browser.find_element_by_name('gender')
    gender.send_keys('female' if player.gender == 'F' else 'male')
    first_name = browser.find_element_by_name('first_name')
    first_name.send_keys(player.first_name)
    last_name = browser.find_element_by_name('last_name')
    last_name.send_keys(player.last_name)
    birth_date = browser.find_element_by_class_name('toggle-birth-date')
    birth_date.click()
    age = browser.find_element_by_class_name('click-labels')
    age.click()
    form = browser.find_element_by_xpath('//div[@class="popup-content"]/form')
    form.submit()
    time.sleep(5)


def _make_player(row):
    """Return a player given a csv row."""
    gender, full_name, email = row
    first_name, last_name = full_name.split(' ', 1)
    return Player(first_name, last_name, gender, email)


def _read_config():
    config_path = join(HERE, '.config')
    email, password = open(config_path).read().strip().splitlines()[:2]
    return email, password


def _read_csv(csv_file):
    """Read a CSV file and return a list of players."""
    with open(csv_file) as f:
        reader = csv.reader(f)
        return [_make_player(row) for row in reader]


# Public API

def register_player(browser, player):
    """Registers a player for the current event."""
    if isinstance(browser, str):
        browser = _open_event(browser)
    player_field = browser.find_element_by_name('autocomplete_person_id')
    player_field.clear()
    player_field.send_keys(player.email)
    time.sleep(3)  # FIXME: There should be a better way of doing this
    autocomplete = browser.find_element_by_class_name('ui-autocomplete')
    completions = autocomplete.find_elements_by_tag_name('a')
    if len(completions) == 1:
        _add_player(browser, player)

    elif len(completions) == 2:
        completions[0].click()

    else:
        print('Could not add player: {}'.format(player.email))


def register_players(csv_file, event_url):
    """Registers players from the CSV file to the specified event."""
    players = _read_csv(csv_file)
    browser = _open_event(event_url)
    for player in players:
        register_player(browser, player)


def main():
    import sys
    if len(sys.argv) != 3:
        print(__doc__.format(program=sys.argv[0]))
        sys.exit(1)
    else:
        csv_file, event_url = sys.argv[1:3]
        register_players(csv_file, event_url)

if __name__ == '__main__':
    main()
