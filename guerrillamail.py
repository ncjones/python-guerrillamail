#!/usr/bin/env python

import argparse
import json
from os.path import expanduser
import sys

import requests


class GuerrillaMailException(Exception):
    def __init__(self, *args, **kwargs):
        super(GuerrillaMailException, self).__init__(*args, **kwargs)


class GuerrillaMailClient(object):
    """
    A client to the Guerrillamail web service API
    (https://www.guerrillamail.com/GuerrillaMailAPI.html).

    The client automatically manages the session key.

    This class is not thread safe.
    """
    def __init__(self, base_url='http://api.guerrillamail.com', client_ip='127.0.0.1', session_id=None):
        self.base_url = base_url
        self.client_ip = client_ip
        self.session_id = session_id

    def _do_request(self, **kwargs):
        url = self.base_url + '/ajax.php'
        kwargs['ip'] = self.client_ip
        if self.session_id is not None:
            kwargs['sid_token'] = self.session_id
        response = requests.get(url, params=kwargs)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            raise GuerrillaMailException(e)
        data = json.loads(response.text)
        new_session_id = data.get('sid_token')
        if new_session_id is not None:
            self.session_id = new_session_id
        return data

    def get_email_address(self):
        data = self._do_request(f='get_email_address')
        return data['email_addr']

    def get_email_list(self, offset=0):
        data = self._do_request(f='get_email_list', offset=offset)
        email_list = data.get('list')
        return email_list if email_list else []

    def get_email(self, email_id):
        return self._do_request(f='fetch_email', email_id=email_id)


SETTINGS_FILE = '~/.guerrillamail'


def load_settings():
    try:
        with open(expanduser(SETTINGS_FILE)) as f:
            return json.load(f)
    except IOError:
        return {}


def save_settings(settings):
    with open(expanduser(SETTINGS_FILE), 'w+') as f:
        json.dump(settings, f)


class Command(object):
    params = []


class GetAddressCommand(Command):
    name = 'address'
    help = 'Get the current email address'
    description = 'Get the email address of the current Guerrillamail session'
    
    def invoke(self, client, args):
        return client.get_email_address()
    
    
class ListEmailCommand(Command):
    name = 'list'
    help = 'Get the current inbox contents'
    description = 'Get the contents of the inbox associated with the current session'
    
    def invoke(self, client, args):
        return client.get_email_list()


class GetEmailCommand(Command):
    name = 'get'
    help = 'Get an email message by id.'
    description = 'Get an email message by id. The email id need not be associated with the current session.'
    params = [{
        'name': 'id',
        'help': 'an email id'
    }]
    
    def invoke(self, client, args):
        client.get_email(args.id)


COMMANDS = [GetAddressCommand(), ListEmailCommand(), GetEmailCommand()]


def _create_args_parser():
    parser = argparse.ArgumentParser(description='''Call a Guerrillamail web service.
        All commands operate on the current Guerrillamail session which is stored in {0}. If a session does not exist or
        has timed out a new one will be created.'''.format(SETTINGS_FILE))
    subparsers = parser.add_subparsers(dest='command', metavar='<command>')
    for command in COMMANDS:
        command_parser = subparsers.add_parser(command.name, help=command.help, description=command.description)
        for param in command.params:
            command_parser.add_argument(param['name'], help=param['help'])
    return parser


def main(*args):
    parser = _create_args_parser()
    args = parser.parse_args(args)
    settings = load_settings()
    client = GuerrillaMailClient(**settings)
    command = [c for c in COMMANDS if c.name == args.command][0]
    print command.invoke(client, args)
    settings['session_id'] = client.session_id
    save_settings(settings)


if __name__ == '__main__':
    main(*sys.argv[1:])
