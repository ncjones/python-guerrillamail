#!/usr/bin/env python

#  Copyright Nathan Jones 2014, 2016
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import contextlib
from datetime import datetime, time
import os
import sys
from time import time as timetime
from unittest.case import TestCase

import httpretty
from mock import patch, DEFAULT, Mock
from sure import expect

from guerrillamail import GuerrillaMailClient, GuerrillaMailException, GuerrillaMailSession, cli, GetInfoCommand, \
    ListEmailCommand, GetEmailCommand, parse_args, get_command, SetAddressCommand, Mail, utc


@contextlib.contextmanager
def redirect_file(src_file, dest_file_path):
    """
    A context manager to temporarily redirect open files, eg:

    with redirect_file(sys.stderr, os.devnull):
        fn_that_prints_unwantedly_to_stderr()

    https://stackoverflow.com/questions/977840/redirecting-fortran-called-via-f2py-output-in-python/17753573#17753573
    """
    try:
        src_file_copy = os.dup(src_file.fileno())
        dest_file = open(dest_file_path, 'w')
        os.dup2(dest_file.fileno(), src_file.fileno())
        yield
    finally:
        if src_file_copy is not None:
            os.dup2(src_file_copy, src_file.fileno())
        if dest_file is not None:
            dest_file.close()


class MailTest(TestCase):
    def test_from_response_should_map_subject(self):
        mail = Mail.from_response({'mail_subject': 'Hello'})
        expect(mail.subject).to.equal('Hello')

    def test_from_response_should_default_subject_to_none(self):
        mail = Mail.from_response({})
        expect(mail.subject).to.be.none

    def test_from_response_should_map_sender(self):
        mail = Mail.from_response({'mail_from': 'test@example.com'})
        expect(mail.sender).to.equal('test@example.com')

    def test_from_response_should_default_sender_to_none(self):
        mail = Mail.from_response({})
        expect(mail.sender).to.be.none

    def test_from_response_should_map_guid(self):
        mail = Mail.from_response({'mail_id': '12345'})
        expect(mail.guid).to.equal('12345')

    def test_from_response_should_default_guid_to_none(self):
        mail = Mail.from_response({})
        expect(mail.guid).to.be.none

    def test_from_response_should_map_read_as_bool_false(self):
        mail = Mail.from_response({'mail_read': '0'})
        expect(mail.read).to.be.false

    def test_from_response_should_map_read_as_bool_true(self):
        mail = Mail.from_response({'mail_read': '1'})
        expect(mail.read).to.be.true

    def test_from_response_should_default_read_to_false(self):
        mail = Mail.from_response({})
        expect(mail.read).to.be.false

    def test_from_response_should_map_datetime(self):
        mail = Mail.from_response({'mail_timestamp': '1392459985'})
        expect(mail.datetime).to.equal(datetime(2014, 2, 15, 10, 26, 25, tzinfo=utc))

    def test_from_response_should_default_datetime_to_none(self):
        mail = Mail.from_response({})
        expect(mail.datetime).to.be.none

    def test_from_response_should_map_excerpt(self):
        mail = Mail.from_response({'mail_excerpt': 'A brief message....'})
        expect(mail.excerpt).to.equal('A brief message....')

    def test_from_response_should_default_excerpt_to_none(self):
        mail = Mail.from_response({})
        expect(mail.excerpt).to.be.none

    def test_from_response_should_not_map_typo_exerpt_property(self):
        mail = Mail.from_response({'mail_exerpt': 'A brief message....'})
        mail = Mail.from_response({'mail_excerpt': 'A brief message....'})
        expect(mail.exerpt).to.be.none

    def test_from_response_should_map_body(self):
        mail = Mail.from_response({'mail_body': 'A brief message from our sponsors'})
        expect(mail.body).to.equal('A brief message from our sponsors')

    def test_from_response_should_default_body_to_none(self):
        mail = Mail.from_response({})
        expect(mail.body).to.be.none

    def test_from_response_should_ignore_unknown_properties(self):
        mail = Mail.from_response({
            "mail_recipient": "john",
        })
        expect(mail).to.not_have.property('recipient')

    def test_time_should_be_derived_from_datetime(self):
        mail = Mail(datetime=datetime(2014, 2, 16, 19, 34))
        expect(mail.time).to.equal(time(19, 34))

    def test_time_should_be_use_same_tz_as_datetime(self):
        mail = Mail(datetime=datetime(2014, 2, 16, 19, 34, tzinfo=utc))
        expect(mail.time).to.equal(time(19, 34, tzinfo=utc))

    def test_time_should_be_none_when_datetime_is_none(self):
        mail = Mail(datetime=None)
        expect(mail.time).to.be.none


class GuerrillaMailClientTest(TestCase):
    def setUp(self):
        self.client = GuerrillaMailClient(base_url='http://test-host')

    @httpretty.activate
    def test_get_email_address_should_send_query_params(self):
        response_body = '{"email_addr":""}'
        httpretty.register_uri(httpretty.GET, 'http://test-host/ajax.php',
                               body=response_body, match_querystring=True)
        self.client.get_email_address()
        expect(httpretty.last_request()).to.have.property('querystring').being.equal({
            'f': ['get_email_address'],
            'ip': ['127.0.0.1'],
        })

    @httpretty.activate
    def test_get_email_address_should_include_session_id_query_param_when_present(self):
        response_body = '{"email_addr":""}'
        httpretty.register_uri(httpretty.GET, 'http://test-host/ajax.php',
                               body=response_body, match_querystring=True)
        self.client.get_email_address(session_id=1)
        expect(httpretty.last_request()).to.have.property('querystring').being.equal({
            'f': ['get_email_address'],
            'ip': ['127.0.0.1'],
            'sid_token': ['1'],
        })

    @httpretty.activate
    def test_get_email_address_should_returned_deserialized_json(self):
        response_body = '{"email_addr":"test@example.com"}'
        httpretty.register_uri(httpretty.GET, 'http://test-host/ajax.php',
                               body=response_body, match_querystring=True)
        response = self.client.get_email_address()
        expect(response).to.equal({'email_addr': 'test@example.com'})

    @httpretty.activate
    def test_get_email_address_should_raise_exception_on_failed_request(self):
        httpretty.register_uri(httpretty.GET, 'http://test-host/ajax.php', status=500)
        expect(self.client.get_email_address).when.called_with().should.throw(GuerrillaMailException)

    @httpretty.activate
    def test_set_email_address_should_send_query_params(self):
        response_body = '{"email_addr":""}'
        httpretty.register_uri(httpretty.GET, 'http://test-host/ajax.php',
                               body=response_body, match_querystring=True)
        self.client.set_email_address('newaddr')
        expect(httpretty.last_request()).to.have.property('querystring').being.equal({
            'f': ['set_email_user'],
            'ip': ['127.0.0.1'],
            'email_user': ['newaddr'],
        })

    @httpretty.activate
    def test_set_email_address_should_include_session_id_query_param_when_present(self):
        response_body = '{"email_addr":""}'
        httpretty.register_uri(httpretty.GET, 'http://test-host/ajax.php',
                               body=response_body, match_querystring=True)
        self.client.set_email_address('newaddr', session_id=1)
        expect(httpretty.last_request()).to.have.property('querystring').being.equal({
            'f': ['set_email_user'],
            'ip': ['127.0.0.1'],
            'email_user': ['newaddr'],
            'sid_token': ['1'],
        })

    @httpretty.activate
    def test_set_email_address_should_returned_deserialized_json(self):
        response_body = '{"email_addr":"test@example.com"}'
        httpretty.register_uri(httpretty.GET, 'http://test-host/ajax.php',
                               body=response_body, match_querystring=True)
        response = self.client.set_email_address('newaddr')
        expect(response).to.equal({'email_addr': 'test@example.com'})

    @httpretty.activate
    def test_set_email_address_should_raise_exception_on_failed_request(self):
        httpretty.register_uri(httpretty.GET, 'http://test-host/ajax.php', status=500)
        expect(self.client.set_email_address).when.called_with('newaddr').should.throw(GuerrillaMailException)

    @httpretty.activate
    def test_get_email_list_should_send_query_params(self):
        response_body = '{"list":[]}'
        httpretty.register_uri(httpretty.GET, 'http://test-host/ajax.php',
                               body=response_body, match_querystring=True)
        self.client.get_email_list(session_id=1)
        expect(httpretty.last_request()).to.have.property('querystring').being.equal({
            'f': ['get_email_list'],
            'ip': ['127.0.0.1'],
            'offset': ['0'],
            'sid_token': ['1'],
        })

    def test_get_email_list_should_not_allow_session_id_to_be_none(self):
        expect(self.client.get_email_list).when.called_with(session_id=None).to.throw(ValueError)

    @httpretty.activate
    def test_get_email_list_should_return_deserialized_json(self):
        response_body = '{"list":[{"subject":"Hello"}]}'
        httpretty.register_uri(httpretty.GET, 'http://test-host/ajax.php',
                               body=response_body, match_querystring=True)
        email_list = self.client.get_email_list(session_id=1)
        expect(email_list).to.equal({'list':[{'subject': 'Hello'}]})

    @httpretty.activate
    def test_get_email_list_should_raise_exception_on_failed_request(self):
        httpretty.register_uri(httpretty.GET, 'http://test-host/ajax.php', status=500)
        expect(self.client.get_email_list).when.called_with(session_id=1).should.throw(GuerrillaMailException)

    @httpretty.activate
    def test_get_email_should_send_query_params(self):
        response_body = '{"list":[]}'
        httpretty.register_uri(httpretty.GET, 'http://test-host/ajax.php',
                               body=response_body, match_querystring=True)
        self.client.get_email(email_id=123)
        expect(httpretty.last_request()).to.have.property('querystring').being.equal({
            'f': ['fetch_email'],
            'ip': ['127.0.0.1'],
            'email_id': ['123'],
        })

    @httpretty.activate
    def test_get_email_should_send_session_id_query_param_when_present(self):
        response_body = '{"list":[]}'
        httpretty.register_uri(httpretty.GET, 'http://test-host/ajax.php',
                               body=response_body, match_querystring=True)
        self.client.get_email(email_id=123, session_id=1)
        expect(httpretty.last_request()).to.have.property('querystring').being.equal({
            'f': ['fetch_email'],
            'ip': ['127.0.0.1'],
            'email_id': ['123'],
            'sid_token': ['1'],
        })

    @httpretty.activate
    def test_get_email_should_return_deserialized_json(self):
        response_body = '{"subject":"Hello"}'
        httpretty.register_uri(httpretty.GET, 'http://test-host/ajax.php',
                               body=response_body, match_querystring=True)
        email = self.client.get_email(email_id=123)
        expect(email).to.equal({'subject': 'Hello'})

    @httpretty.activate
    def test_get_email_should_raise_exception_on_failed_request(self):
        httpretty.register_uri(httpretty.GET, 'http://test-host/ajax.php', status=500)
        expect(self.client.get_email).when.called_with(email_id=123).should.throw(GuerrillaMailException)

    @httpretty.activate
    def test_get_email_should_raise_exception_when_message_not_found(self):
        httpretty.register_uri(httpretty.GET, 'http://test-host/ajax.php', status=200, body='false')
        expect(self.client.get_email).when.called_with(email_id=123).should.throw(GuerrillaMailException)


def current_timestamp():
    return int(timetime())


@patch.multiple('guerrillamail', GuerrillaMailClient=DEFAULT)
class GuerrillaMailSessionTest(TestCase):
    def setup_mocks(self, GuerrillaMailClient, **kwargs):
        self.mock_client = Mock()
        GuerrillaMailClient.return_value = self.mock_client
        self.session = GuerrillaMailSession()

    def test_get_email_state_should_extract_email_address_from_response(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_client.get_email_address.return_value = {'email_addr': 'test@example.com', 'sid_token': 1}
        email_address = self.session.get_session_state()
        expect(email_address).to.equal({'email_address': 'test@example.com'})

    def test_get_email_state_should_call_client(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_client.get_email_address.return_value = {'email_addr': '', 'sid_token': 1}
        self.session.get_session_state()
        self.mock_client.get_email_address.assert_called_once_with(session_id=None)

    def test_get_session_state_should_call_client_with_session_id_when_set(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_client.get_email_address.return_value = {'email_addr': ''}
        self.session.session_id = 1
        self.session.get_session_state()
        self.mock_client.get_email_address.assert_called_once_with(session_id=1)

    def test_get_session_state_should_update_session_id_when_included_in_response(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_client.get_email_address.return_value = {'email_addr': '', 'sid_token': 1}
        assert self.session.session_id == None
        self.session.get_session_state()
        expect(self.session.session_id).to.equal(1)

    def test_get_session_state_should_not_update_session_id_when_not_included_in_response(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_client.get_email_address.return_value = {'email_addr': ''}
        self.session.session_id = 1
        self.session.get_session_state()
        expect(self.session.session_id).to.equal(1)

    def test_get_session_state_should_update_email_timestamp(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_client.get_email_address.return_value = {'email_addr': '', 'email_timestamp': 1234, 'sid_token': 1}
        assert self.session.email_timestamp == 0
        self.session.get_session_state()
        expect(self.session.email_timestamp).to.equal(1234)

    def test_get_session_state_should_update_email_address(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_client.get_email_address.return_value = {
            'email_addr': 'test@users.org', 'email_timestamp': 1234, 'sid_token': 1,
        }
        assert self.session.email_timestamp == 0
        self.session.get_session_state()
        expect(self.session.email_address).to.equal('test@users.org')

    def test_get_session_state_should_use_cached_data_when_available_and_current(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.session.session_id = 1
        self.session.email_address = 'test@users.org'
        self.session.email_timestamp = current_timestamp()
        self.session.get_session_state()
        expect(self.mock_client.get_email_address.called).to.equal(False)
        expect(self.mock_client.set_email_address.called).to.equal(False)

    def test_set_email_address_should_return_none(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_client.set_email_address.return_value = {'email_addr': 'test@example.com'}
        result = self.session.set_email_address('newaddr')
        expect(result).to.be.none

    def test_set_email_address_should_call_client(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_client.set_email_address.return_value = {'email_addr': ''}
        self.session.set_email_address('newaddr')
        self.mock_client.set_email_address.assert_called_once_with(session_id=None, address_local_part='newaddr')

    def test_set_email_address_should_call_client_with_session_id_when_set(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_client.set_email_address.return_value = {'email_addr': ''}
        self.session.session_id = 1
        self.session.set_email_address('newaddr')
        self.mock_client.set_email_address.assert_called_once_with(session_id=1, address_local_part='newaddr')

    def test_set_email_address_should_update_session_id_when_included_in_response(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_client.set_email_address.return_value = {'email_addr': '', 'sid_token': 1}
        assert self.session.session_id == None
        self.session.set_email_address('newaddr')
        expect(self.session.session_id).to.equal(1)

    def test_set_email_address_should_not_update_session_id_when_not_included_in_response(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_client.set_email_address.return_value = {'email_addr': ''}
        self.session.session_id = 1
        self.session.set_email_address('newaddr')
        expect(self.session.session_id).to.equal(1)

    def test_set_email_address_should_update_email_timestamp(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_client.set_email_address.return_value = {'email_addr': '', 'email_timestamp': 1234}
        assert self.session.email_timestamp == 0
        self.session.set_email_address('newaddr')
        expect(self.session.email_timestamp).to.equal(1234)

    def test_set_email_address_should_update_email_address(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_client.set_email_address.return_value = {'email_addr': 'test@users.org', 'email_timestamp': 1234}
        assert self.session.email_timestamp == 0
        self.session.set_email_address('newaddr')
        expect(self.session.email_address).to.equal('test@users.org')

    def test_get_email_list_should_extract_response_list(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_client.get_email_list.return_value = {'list': []}
        self.session.session_id = 1
        self.session.email_timestamp = current_timestamp()
        email_list = self.session.get_email_list()
        expect(email_list).to.have.length_of(0)

    def test_get_email_list_should_create_mail_instances_from_response_list(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_client.get_email_list.return_value = {
            'list': [{
                'mail_id': '1',
                'mail_subject': 'Hello',
                'mail_from': 'user@example.com',
                'mail_timestamp': '1392501749',
                'mail_read': '0',
                'mail_excerpt': 'Hi there....',
            }]
        }
        self.session.session_id = 1
        self.session.email_timestamp = current_timestamp()
        email_list = self.session.get_email_list()
        email = email_list[0]
        expect(email_list).to.have.length_of(1)
        expect(email).to.have.property('guid').with_value.being.equal('1')
        expect(email).to.have.property('subject').with_value.being.equal('Hello')
        expect(email).to.have.property('sender').with_value.being.equal('user@example.com')
        expect(email).to.have.property('datetime').with_value.being.equal(datetime(2014, 2, 15, 22, 2, 29, tzinfo=utc))
        expect(email).to.have.property('read').with_value.being.false
        expect(email).to.have.property('excerpt').with_value.being.equal('Hi there....')

    def test_get_email_list_should_call_client(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_client.get_email_list.return_value = {'list': []}
        self.session.session_id = 1
        self.session.email_timestamp = current_timestamp()
        self.session.get_email_list()
        self.mock_client.get_email_list.assert_called_once_with(session_id=1, offset=0)

    def test_get_email_list_should_call_client_with_session_id_when_set(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_client.get_email_list.return_value = {'list': []}
        self.session.session_id = 1
        self.session.email_timestamp = current_timestamp()
        self.session.get_email_list()
        self.mock_client.get_email_list.assert_called_once_with(session_id=1, offset=0)

    def test_get_email_list_should_update_session_id_when_included_in_response(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_client.get_email_list.return_value = {'list': [], 'sid_token': 1}
        self.session.session_id = 0
        self.session.email_timestamp = current_timestamp()
        self.session.get_email_list()
        expect(self.session.session_id).to.equal(1)

    def test_get_email_list_should_not_update_session_id_when_not_included_in_response(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_client.get_email_list.return_value = {'list': []}
        self.session.session_id = 1
        self.session.email_timestamp = current_timestamp()
        self.session.get_email_list()
        expect(self.session.session_id).to.equal(1)

    def test_get_email_list_should_not_invoke_get_address_when_session_id_set_and_not_expired(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.session.session_id = 1
        self.session.email_timestamp = current_timestamp()
        self.mock_client.get_email_list.return_value = {'list': []}
        self.session.get_email_list()
        expect(self.mock_client.get_email_address.called).to.equal(False)

    def test_get_email_list_should_first_create_session_when_session_id_not_set(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_client.get_email_list.return_value = {'list': []}
        self.mock_client.get_email_address.return_value = {'sid_token': '1', 'email_addr': ''}
        self.session.email_timestamp = current_timestamp()
        assert self.session.session_id == None
        self.session.get_email_list()
        expect(self.session.session_id).to.equal('1')
        self.mock_client.get_email_list.assert_called_once_with(session_id='1', offset=0)

    def test_get_email_list_should_first_create_session_and_reuse_address_when_session_id_not_set(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_client.get_email_list.return_value = {'list': []}
        self.mock_client.set_email_address.return_value = {'sid_token': '1', 'email_addr': ''}
        self.session.email_timestamp = current_timestamp()
        self.session.email_address = 'test@users.org'
        assert self.session.session_id == None
        self.session.get_email_list()
        expect(self.session.session_id).to.equal('1')
        self.mock_client.get_email_list.assert_called_once_with(session_id='1', offset=0)

    def test_get_email_list_should_fail_when_session_cannot_be_obtained(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_client.get_email_address.return_value = {'email_addr': ''}
        assert self.session.session_id == None
        expect(self.session.get_email_list).when.called.to.throw(GuerrillaMailException)
        expect(self.mock_client.get_email_list.called).to.equal(False)

    def test_get_email_list_should_refresh_session_when_email_expired(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_client.get_email_list.return_value = {'list': []}
        self.mock_client.get_email_address.return_value = {'email_addr': '', 'sid_token': '2', 'email_timestamp': 1234}
        self.session.session_id = 1
        self.session.email_timestamp = current_timestamp() - 3600
        self.session.get_email_list()
        expect(self.session.session_id).to.equal('2')
        expect(self.session.email_timestamp).to.equal(1234)
        self.mock_client.get_email_list.assert_called_once_with(session_id='2', offset=0)

    def test_get_email_list_should_refresh_session_and_reuse_address_when_email_expired(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_client.get_email_list.return_value = {'list': []}
        self.mock_client.set_email_address.return_value = {'email_addr': '', 'sid_token': '2', 'email_timestamp': 1234}
        self.session.session_id = 1
        self.session.email_address = 'user@test.com'
        self.session.email_timestamp = current_timestamp() - 3600
        self.session.get_email_list()
        expect(self.session.session_id).to.equal('2')
        expect(self.session.email_timestamp).to.equal(1234)
        self.mock_client.get_email_list.assert_called_once_with(session_id='2', offset=0)

    def test_get_email_list_should_not_refresh_session_when_email_not_expired(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_client.get_email_list.return_value = {'list': []}
        self.session.session_id = 1
        self.session.email_timestamp = current_timestamp() - 3590
        self.session.get_email_list()
        expect(self.mock_client.get_email_address.called).to.equal(False)

    def test_get_email_should_create_mail_instance_from_client_response_data(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_client.get_email.return_value = {
            'mail_id': '1',
            'mail_subject': 'Hello',
            'mail_from': 'user@example.com',
            'mail_timestamp': '1392501749',
            'mail_read': '0',
            'mail_excerpt': 'Hi there....',
            'mail_body': 'Hi there partner',
        }
        email = self.session.get_email('123')
        expect(email).to.have.property('guid').with_value.being.equal('1')
        expect(email).to.have.property('subject').with_value.being.equal('Hello')
        expect(email).to.have.property('sender').with_value.being.equal('user@example.com')
        expect(email).to.have.property('datetime').with_value.being.equal(datetime(2014, 2, 15, 22, 2, 29, tzinfo=utc))
        expect(email).to.have.property('read').with_value.being.false
        expect(email).to.have.property('excerpt').with_value.being.equal('Hi there....')
        expect(email).to.have.property('body').with_value.being.equal('Hi there partner')

    def test_get_email_should_call_client(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_client.get_email.return_value = {}
        self.session.get_email('123')
        self.mock_client.get_email.assert_called_once_with(email_id='123', session_id=None)

    def test_get_email_should_call_client_with_session_id_when_set(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_client.get_email.return_value = {}
        self.session.session_id = 1
        self.session.get_email('123')
        self.mock_client.get_email.assert_called_once_with(email_id='123', session_id=1)

    def test_get_email_should_update_session_id_when_included_in_response(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_client.get_email.return_value = {'sid_token': 1}
        assert self.session.session_id == None
        self.session.get_email('123')
        expect(self.session.session_id).to.equal(1)

    def test_get_email_should_not_update_session_id_when_not_included_in_response(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_client.get_email.return_value = {}
        self.session.session_id = 1
        self.session.get_email('123')
        expect(self.session.session_id).to.equal(1)


class GetInfoCommandTest(TestCase):
    def setUp(self):
        self.command = GetInfoCommand()

    def test_invoke_should_get_email_address_from_session(self):
        mock_session = Mock(get_session_state=lambda: {'email_address': 'test@example.com'})
        output = self.command.invoke(mock_session, None)
        expect(output).to.equal('Email: test@example.com')


class SetAddressCommandTest(TestCase):
    def setUp(self):
        self.command = SetAddressCommand()

    def test_invoke_should_call_set_email_address_on_session(self):
        mock_session = Mock()
        mock_args = Mock(address='john91')
        self.command.invoke(mock_session, mock_args)
        mock_session.set_email_address.assert_called_with('john91')

    def test_invoke_should_have_no_output(self):
        mock_session = Mock()
        mock_args = Mock(address='john91')
        output = self.command.invoke(mock_session, mock_args)
        expect(output).to.be.none


class ListEmailCommandTest(TestCase):
    def setUp(self):
        self.command = ListEmailCommand()

    def test_invoke_should_format_mail_summaries(self):
        date = datetime(2014, 2, 16, 12, 34)
        mail = Mail(subject='Test', sender='user@example.com', guid='1234567', datetime=date)
        mock_session = Mock(get_email_list=lambda: [mail])
        output = self.command.invoke(mock_session, None)
        expect(output).to.equal('(*) 1234567   12:34:00  user@example.com\nTest\n\n')

    def test_invoke_should_format_mail_summaries_without_star_when_read(self):
        date = datetime(2014, 2, 16, 12, 34)
        mail = Mail(subject='Test', sender='user@example.com', guid='1234567', datetime=date, read=True)
        mock_session = Mock(get_email_list=lambda: [mail])
        output = self.command.invoke(mock_session, None)
        expect(output).to.equal('( ) 1234567   12:34:00  user@example.com\nTest\n\n')

    def test_invoke_should_format_mail_summaries_with_left_aligned_guid(self):
        date = datetime(2014, 2, 16, 12, 34)
        mail = Mail(subject='Test', sender='user@example.com', guid='123', datetime=date)
        mock_session = Mock(get_email_list=lambda: [mail])
        output = self.command.invoke(mock_session, None)
        expect(output).to.equal('(*) 123       12:34:00  user@example.com\nTest\n\n')

    def test_invoke_should_format_mail_summaries_with_min_two_spaces_after_guid(self):
        date = datetime(2014, 2, 16, 12, 34)
        mail = Mail(subject='Test', sender='user@example.com', guid='1234567890', datetime=date)
        mock_session = Mock(get_email_list=lambda: [mail])
        output = self.command.invoke(mock_session, None)
        expect(output).to.equal('(*) 1234567890  12:34:00  user@example.com\nTest\n\n')

    def test_invoke_should_handle_unicode_chars(self):
        date = datetime(2014, 2, 16, 12, 34)
        mail = Mail(subject=u'Test\u0131', sender='user@example.com', guid='1234567', datetime=date)
        mock_session = Mock(get_email_list=lambda: [mail])
        output = self.command.invoke(mock_session, None)
        expect(output).to.equal(u'(*) 1234567   12:34:00  user@example.com\nTest\u0131\n\n')

    def test_invoke_should_format_mail_summaries_with_tz_when_present(self):
        date = datetime(2014, 2, 16, 12, 34, tzinfo=utc)
        mail = Mail(subject='Test', sender='user@example.com', guid='1234567', datetime=date, read=True)
        mock_session = Mock(get_email_list=lambda: [mail])
        output = self.command.invoke(mock_session, None)
        expect(output).to.equal('( ) 1234567   12:34:00+00:00  user@example.com\nTest\n\n')


class GetEmailCommandTest(TestCase):
    def setUp(self):
        self.command = GetEmailCommand()

    def test_invoke_should_format_mail(self):
        mail = Mail(
            subject='Test',
            sender='user@example.com',
            datetime=datetime(2014, 2, 15, 22, 2, 29),
            body='Hello'
        )
        mock_session = Mock(get_email=lambda _: mail)
        mock_args = Mock(id=1)
        output = self.command.invoke(mock_session, mock_args)
        expect(output).to.equal('From: user@example.com\nDate: {0}\nSubject: Test\n\nHello\n'.format(mail.datetime))


class GuerrillaMailParseArgsTest(TestCase):
    def test_parse_args_should_extract_info_command(self, **kwargs):
        args = parse_args(['info'])
        expect(args.command).to.equal('info')

    def test_parse_args_should_extract_set_address_command(self, **kwargs):
        args = parse_args(['setaddr', 'john91'])
        expect(args.command).to.equal('setaddr')
        expect(args.address).to.equal('john91')

    def test_parse_args_should_extract_list_command(self, **kwargs):
        args = parse_args(['list'])
        expect(args.command).to.equal('list')

    def test_parse_args_should_extract_get_command(self, **kwargs):
        args = parse_args(['get', '123'])
        expect(args.command).to.equal('get')
        expect(args.id).to.equal('123')

    def test_parse_args_should_reject_unknown_command(self, **kwargs):
        with redirect_file(sys.stderr, os.devnull):
            self.assertRaises(SystemExit, parse_args, ['cheese'])

    def test_parse_args_should_reject_get_command_with_id_missing(self, **kwargs):
        with redirect_file(sys.stderr, os.devnull):
            self.assertRaises(SystemExit, parse_args, ['get'])


class GuerrillaMailGetCommandTest(TestCase):
    def test_get_address_command_should_return_get_address_command_instance(self):
        command = get_command('info')
        expect(command).to.be.a('guerrillamail.GetInfoCommand')

    def test_set_address_command_should_return_set_address_command_instance(self):
        command = get_command('setaddr')
        expect(command).to.be.a('guerrillamail.SetAddressCommand')

    def test_get_list_command_should_return_get_list_command_instance(self):
        command = get_command('list')
        expect(command).to.be.a('guerrillamail.ListEmailCommand')

    def test_get_get_command_should_return_get_email_command_instance(self):
        command = get_command('get')
        expect(command).to.be.a('guerrillamail.GetEmailCommand')

    def test_get_unknown_command_should_raise_exception(self):
        expect(get_command).when.called_with('cheese').to.throw(ValueError)


@patch.multiple('guerrillamail', load_settings=DEFAULT, save_settings=DEFAULT, GuerrillaMailSession=DEFAULT,
                parse_args=DEFAULT, get_command=DEFAULT)
class GuerrillaMailCliTest(TestCase):
    def setup_mocks(self, GuerrillaMailSession, load_settings, parse_args, get_command, **kwargs):
        load_settings.return_value = {}
        self.mock_session = Mock()
        self.mock_args = Mock()
        self.mock_command = Mock()
        GuerrillaMailSession.return_value = self.mock_session
        parse_args.return_value = self.mock_args
        get_command.return_value = self.mock_command

    def test_cli_should_create_session_using_settings(self, GuerrillaMailSession, load_settings, **kwargs):
        self.setup_mocks(GuerrillaMailSession=GuerrillaMailSession, load_settings=load_settings, **kwargs)
        load_settings.return_value = {'arg1': 1, 'arg2': 'cheese'}
        cli()
        GuerrillaMailSession.assert_called_with(arg1=1, arg2='cheese')

    def test_cli_should_get_command_by_command_name_arg(self, get_command, **kwargs):
        self.setup_mocks(get_command=get_command, **kwargs)
        self.mock_args.command = 'cheese'
        cli()
        get_command.assert_called_with('cheese')

    def test_cli_should_invoke_command(self, **kwargs):
        self.setup_mocks(**kwargs)
        cli()
        self.mock_command.invoke.assert_called_once_with(self.mock_session, self.mock_args)

    def test_cli_should_save_settings_with_updated_session_id(self, save_settings, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_args.command = 'cheese'
        def set_session_state(*args):
            self.mock_session.session_id = 123
            self.mock_session.email_timestamp = 4321
            self.mock_session.email_address = 'test@users.com'
        self.mock_command.invoke.side_effect = set_session_state
        cli()
        expected_settings = {'session_id': 123, 'email_timestamp': 4321, 'email_address': 'test@users.com'}
        save_settings.assert_called_with(expected_settings)

    def test_cli_should_capture_guerrillamail_exception(self, **kwargs):
        self.setup_mocks(**kwargs)
        def raise_exception(*args):
            raise GuerrillaMailException(None)
        self.mock_command.invoke.side_effect = raise_exception
        cli()

    def test_cli_should_not_capture_unexpected_exception(self, **kwargs):
        self.setup_mocks(**kwargs)
        def raise_exception(*args):
            raise Exception()
        self.mock_command.invoke.side_effect = raise_exception
        expect(cli).when.called.to.throw(Exception)
