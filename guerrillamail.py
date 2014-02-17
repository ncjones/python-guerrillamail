#!/usr/bin/env python

from __future__ import print_function

import argparse
from datetime import tzinfo, timedelta, datetime
from time import time
import json
from os.path import expanduser
import sys

import requests


# UTC timezone implementation from
# http://docs.python.org/2/library/datetime.html#tzinfo-objects

ZERO = timedelta(0)


class UTC(tzinfo):
    """UTC"""
#
    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO


utc = UTC()


class GuerrillaMailException(Exception):
    def __init__(self, *args, **kwargs):
        super(GuerrillaMailException, self).__init__(*args, **kwargs)


def _transform_dict(original, key_map):
    result = {}
    for (new_key, (old_key, transform_fn)) in key_map.items():
        try:
            result[new_key] = transform_fn(original[old_key])
        except KeyError:
            pass
    return result


class Mail(object):
    @classmethod
    def from_response(cls, response_data):
        """
        Factory method to create a Mail instance from a Guerrillamail response
        dict.
        """
        identity = lambda x: x
        return Mail(**_transform_dict(response_data, {
            'guid': ('mail_id', identity),
            'subject': ('mail_subject', identity),
            'sender': ('mail_from', identity),
            'datetime': ('mail_timestamp', lambda x: datetime.utcfromtimestamp(int(x)).replace(tzinfo=utc)),
            'read': ('mail_read', int),
            'exerpt': ('mail_exerpt', identity),
            'body': ('mail_body', identity),
        }))

    def __init__(self, guid=None, subject=None, sender=None, datetime=None, read=False, exerpt=None, body=None):
        self.guid = guid
        self.subject = subject
        self.sender = sender
        self.datetime = datetime
        self.read = read
        self.exerpt = exerpt
        self.body = body

    @property
    def time(self):
        return self.datetime.time().replace(tzinfo=self.datetime.tzinfo) if self.datetime else None


SESSION_TIMEOUT_SECONDS = 3600


class GuerrillaMailSession(object):
    """
    An abstraction over a GuerrillamailClient which maintains session state.

    This class is not thread safe.
    """
    def __init__(self, session_id=None, email_address=None, email_timestamp=0, **kwargs):
        self.client = GuerrillaMailClient(**kwargs)
        self.session_id = session_id
        self.email_timestamp = email_timestamp
        self.email_address = email_address

    def _update_session_state(self, response_data):
        try:
            self.session_id = response_data['sid_token']
        except KeyError:
            pass
        try:
            self.email_address = response_data['email_addr']
        except KeyError:
            pass
        try:
            self.email_timestamp = response_data['email_timestamp']
        except KeyError:
            pass

    def is_expired(self):
        current_time = int(time())
        expiry_time = self.email_timestamp + SESSION_TIMEOUT_SECONDS - 5
        return current_time >= expiry_time

    def _delegate_to_client(self, method_name, *args, **kwargs):
        client_method = getattr(self.client, method_name)
        response_data = client_method(session_id=self.session_id, *args, **kwargs)
        self._update_session_state(response_data)
        return response_data

    def get_session_state(self):
        data = self._delegate_to_client('get_email_address')
        return {
            'email_address': data['email_addr']
        }

    def set_email_address(self, address_local_part):
        self._delegate_to_client('set_email_address', address_local_part=address_local_part)

    def _renew_session(self):
        if self.email_address:
            self.set_email_address(self.email_address)
        else:
            self.get_session_state()

    def _ensure_valid_session(self):
        if self.session_id is None or self.is_expired():
            self._renew_session()
        if self.session_id is None:
            raise GuerrillaMailException('Failed to obtain session id')

    def get_email_list(self, offset=0):
        self._ensure_valid_session()
        response_data = self._delegate_to_client('get_email_list', offset=offset)
        email_list = response_data.get('list')
        return [Mail.from_response(e) for e in email_list] if email_list else []

    def get_email(self, email_id):
        return Mail.from_response(self._delegate_to_client('get_email', email_id=email_id))


class GuerrillaMailClient(object):
    """
    A client to the Guerrillamail web service API
    (https://www.guerrillamail.com/GuerrillaMailAPI.html).
    """
    def __init__(self, base_url='http://api.guerrillamail.com', client_ip='127.0.0.1'):
        self.base_url = base_url
        self.client_ip = client_ip

    def _do_request(self, session_id, **kwargs):
        url = self.base_url + '/ajax.php'
        kwargs['ip'] = self.client_ip
        if session_id is not None:
            kwargs['sid_token'] = session_id
        response = requests.get(url, params=kwargs)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            raise GuerrillaMailException(e)
        data = json.loads(response.text)
        return data

    def get_email_address(self, session_id=None):
        return self._do_request(session_id, f='get_email_address')

    def get_email_list(self, session_id, offset=0):
        if session_id is None:
            raise ValueError('session_id is None')
        return self._do_request(session_id, f='get_email_list', offset=offset)

    def get_email(self, email_id, session_id=None):
        response_data = self._do_request(session_id, f='fetch_email', email_id=email_id)
        if not response_data:
            raise GuerrillaMailException('Not found: ' + str(email_id))
        return response_data

    def set_email_address(self, address_local_part, session_id=None):
        return self._do_request(session_id, f='set_email_user', email_user=address_local_part)


SETTINGS_FILE = '~/.guerrillamail'


def load_settings():
    try:
        with open(expanduser(SETTINGS_FILE)) as f:
            return json.load(f)
    except IOError:
        return {}


def save_settings(settings):
    with open(expanduser(SETTINGS_FILE), 'w+') as f:
        json.dump(settings, f, indent=4)
        f.write('\n')


class Command(object):
    params = []


class GetAddressCommand(Command):
    name = 'address'
    help = 'Get the current email address'
    description = 'Get the email address of the current Guerrillamail session'
    
    def invoke(self, session, args):
        return session.get_session_state()['email_address']


class SetAddressCommand(Command):
    name = 'setaddr'
    help = 'Set the current email address'
    description = 'Set the email address of the current Guerrillamail session'
    params = [{
        'name': 'address',
        'help': 'an email address local part (excludes domain and @ symbol)'
    }]

    def invoke(self, session, args):
        session.set_email_address(args.address)
    
    
class ListEmailCommand(Command):
    name = 'list'
    help = 'Get the current inbox contents'
    description = 'Get the contents of the inbox associated with the current session'
    
    def invoke(self, session, args):
        email_list = session.get_email_list()
        output = ''
        for email in email_list:
            output += self.format_email_summary(email) + '\n'
        return output

    def format_email_summary(self, email):
        unread_indicator = '*' if not email.read else ' '
        email_format = u'({unread_indicator}) {email.guid:<8}  {email.time}  {email.sender}\n{email.subject}\n'
        return email_format.format(email=email, unread_indicator=unread_indicator)


class GetEmailCommand(Command):
    name = 'get'
    help = 'Get an email message by id.'
    description = 'Get an email message by id. The email id need not be associated with the current session.'
    params = [{
        'name': 'id',
        'help': 'an email id'
    }]
    
    def invoke(self, session, args):
        email = session.get_email(args.id)
        return self.format_email(email)

    def format_email(self, email):
        email_format = u'From: {email.sender}\nDate: {email.datetime}\nSubject: {email.subject}\n\n{email.body}\n'
        return email_format.format(email=email)


COMMAND_TYPES = [GetAddressCommand, SetAddressCommand, ListEmailCommand, GetEmailCommand]


def parse_args(args):
    parser = argparse.ArgumentParser(description='''Call a Guerrillamail web service.
        All commands operate on the current Guerrillamail session which is stored in {0}. If a session does not exist
        or has timed out a new one will be created.'''.format(SETTINGS_FILE))
    subparsers = parser.add_subparsers(dest='command', metavar='<command>')
    for Command in COMMAND_TYPES:
        command_parser = subparsers.add_parser(Command.name, help=Command.help, description=Command.description)
        for param in Command.params:
            param_name = param['name']
            command_parser.add_argument(param_name, metavar='<{0}>'.format(param_name), help=param['help'])
    return parser.parse_args(args)


def get_command(command_name):
    try:
        return [C() for C in COMMAND_TYPES if C.name == command_name][0]
    except IndexError:
        raise ValueError('Invalid command: ' + command_name)


def update_settings(settings, session):
    settings['session_id'] = session.session_id
    settings['email_timestamp'] = session.email_timestamp
    settings['email_address'] = session.email_address


def main(*args):
    args = parse_args(args)
    settings = load_settings()
    session = GuerrillaMailSession(**settings)
    try:
        output = get_command(args.command).invoke(session, args)
    except GuerrillaMailException as e:
        print(e.message, file=sys.stderr)
    else:
        if output is not None:
            print(output)
    update_settings(settings, session)
    save_settings(settings)


if __name__ == '__main__':
    main(*sys.argv[1:])
