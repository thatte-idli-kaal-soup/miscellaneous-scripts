#!/usr/bin/env python3
"""Script to manage lists for the team."""

from cmd import Cmd
from collections import OrderedDict
import pprint
import random
import string


def random_string(n=10):
    return ''.join(random.choice(string.ascii_letters) for _ in range(n))


class NoSuchListError(Exception):
    pass


class NoSuchItemError(Exception):
    pass


class DuplicateListError(Exception):
    pass


class DuplicateUserItemError(Exception):
    pass


class Bot():

    SINGLE_ENTRY_PER_USER = True

    def __init__(self):
        self.data = OrderedDict()

    def get_list(self, list_id):
        if list_id not in self.data:
            raise NoSuchListError('List "{}" does not exist'.format(list_id))
        return self.data[list_id]

    def create_list(self, list_id=None):
        if not list_id:
            list_id = random_string()
        self.data.setdefault(list_id, OrderedDict())
        return list_id

    def delete_list(self, list_id):
        self.get_list(list_id)
        self.data.pop(list_id)

    def list_lists(self):
        return self.data.keys()

    def add_item(self, list_id, entry, user='default'):
        list_ = self.get_list(list_id)
        if user in list_:
            raise DuplicateUserItemError(
                '{} already has an entry in {}'.format(user, list_id)
            )
        list_[user] = entry
        return list_

    def delete_item(self, list_id, user='default'):
        list_ = self.get_list(list_id)
        if user not in list_:
            raise NoSuchItemError(
                '{} does not have an entry for {}'.format(list_id, user)
            )
        list_.pop(user)
        return list_

    def update_item(self, list_id, entry, user='default'):
        self.delete_item(list_id, user)
        return self.add_item(list_id, entry, user)


class Shell(Cmd):
    intro = 'Welcome to the list bot. Type help or ? to list commands.\n'
    prompt = '(bot-command) '

    def initialize(self):
        self.bot = Bot()

    def do_create_list(self, list_id):
        list_id = self.bot.create_list(list_id)
        print('Created list: {}'.format(list_id))

    def do_show_all(self, arg):
        list_ids = self.bot.list_lists()
        print('Tracking {} lists: \n    '.format(len(list_ids)), end='')
        print('\n    '.join(list_ids))

    def do_show_list(self, list_id):
        list_ = self.bot.get_list(list_id)
        pprint.pprint(list_)

    def do_add_item(self, arg):
        list_id, entry = arg.split(' ', 1)
        self.bot.add_item(list_id, entry)


if __name__ == '__main__':
    shell = Shell()
    shell.initialize()
    while True:
        try:
            shell.cmdloop()
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(e)
