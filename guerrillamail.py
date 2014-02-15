import json
import requests
import sys

from os.path import join, expanduser


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


SETTINGS_FILE = join(expanduser('~'), '.guerrillamail')


def load_settings():
    try:
        with open(SETTINGS_FILE) as f:
            return json.load(f)
    except IOError:
        return {}


def save_settings(settings):
    with open(SETTINGS_FILE, 'w+') as f:
        json.dump(settings, f)


if __name__ == '__main__':
    settings = load_settings()
    client = GuerrillaMailClient(**settings)
    if len(sys.argv) < 2:
        print 'expected command'
        sys.exit(1)
    command = sys.argv[1]
    if len(sys.argv) > 2:
        args = sys.argv[2:]
    else:
        args = []
    print getattr(client, command)(*args)
    settings['session_id'] = client.session_id
    save_settings(settings)
