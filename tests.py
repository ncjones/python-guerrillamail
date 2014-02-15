import json
from unittest.case import TestCase

import httpretty
from mock import patch, DEFAULT, Mock
from sure import expect

from guerrillamail import GuerrillaMailClient, GuerrillaMailException, GuerrillaMailSession, main, GetAddressCommand, \
    ListEmailCommand, GetEmailCommand, parse_args, get_command


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
    def test_get_email_list_should_send_query_params(self):
        response_body = '{"list":[]}'
        httpretty.register_uri(httpretty.GET, 'http://test-host/ajax.php',
                               body=response_body, match_querystring=True)
        self.client.get_email_list()
        expect(httpretty.last_request()).to.have.property('querystring').being.equal({
            'f': ['get_email_list'],
            'ip': ['127.0.0.1'],
            'offset': ['0'],
        })

    @httpretty.activate
    def test_get_email_list_should_include_session_id_query_param_when_present(self):
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

    @httpretty.activate
    def test_get_email_list_should_return_deserialized_json(self):
        response_body = '{"list":[{"subject":"Hello"}]}'
        httpretty.register_uri(httpretty.GET, 'http://test-host/ajax.php',
                               body=response_body, match_querystring=True)
        email_list = self.client.get_email_list()
        expect(email_list).to.equal({'list':[{'subject': 'Hello'}]})

    @httpretty.activate
    def test_get_email_list_should_return_empty_list_when_response_has_no_list_field(self):
        response_body = '{}'
        httpretty.register_uri(httpretty.GET, 'http://test-host/ajax.php',
                               body=response_body, match_querystring=True)
        email_list = self.client.get_email_list()
        expect(email_list).to.be.empty

    @httpretty.activate
    def test_get_email_list_should_raise_exception_on_failed_request(self):
        httpretty.register_uri(httpretty.GET, 'http://test-host/ajax.php', status=500)
        expect(self.client.get_email_list).when.called_with().should.throw(GuerrillaMailException)

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


@patch.multiple('guerrillamail', GuerrillaMailClient=DEFAULT)
class GuerrillaMailSessionTest(TestCase):
    def setup_mocks(self, GuerrillaMailClient, **kwargs):
        self.mock_client = Mock()
        GuerrillaMailClient.return_value = self.mock_client
        self.session = GuerrillaMailSession()

    def test_get_email_address_should_extract_email_address_from_response(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_client.get_email_address.return_value = {'email_addr': 'test@example.com'}
        email_address = self.session.get_email_address()
        expect(email_address).to.equal('test@example.com')

    def test_get_email_address_should_call_client(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_client.get_email_address.return_value = {'email_addr': ''}
        self.session.get_email_address()
        self.mock_client.get_email_address.assert_called_once_with(session_id=None)

    def test_get_email_address_should_call_client_with_session_id_when_set(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_client.get_email_address.return_value = {'email_addr': ''}
        self.session.session_id = 1
        self.session.get_email_address()
        self.mock_client.get_email_address.assert_called_once_with(session_id=1)

    def test_get_email_address_should_update_session_id_when_included_in_response(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_client.get_email_address.return_value = {'email_addr': '', 'sid_token': 1}
        assert self.session.session_id == None
        self.session.get_email_address()
        expect(self.session.session_id).to.equal(1)

    def test_get_email_address_should_not_update_session_id_when_not_included_in_response(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_client.get_email_address.return_value = {'email_addr': ''}
        self.session.session_id = 1
        self.session.get_email_address()
        expect(self.session.session_id).to.equal(1)

    def test_get_email_list_should_extract_list_from_response(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_client.get_email_list.return_value = {'list': [{'subject': 'Hello'}]}
        email_list = self.session.get_email_list()
        expect(email_list).to.equal([{'subject': 'Hello'}])

    def test_get_email_list_should_call_client(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_client.get_email_list.return_value = {'list': []}
        self.session.get_email_list()
        self.mock_client.get_email_list.assert_called_once_with(session_id=None, offset=0)

    def test_get_email_list_should_call_client_with_session_id_when_set(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_client.get_email_list.return_value = {'list': []}
        self.session.session_id = 1
        self.session.get_email_list()
        self.mock_client.get_email_list.assert_called_once_with(session_id=1, offset=0)

    def test_get_email_list_should_update_session_id_when_included_in_response(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_client.get_email_list.return_value = {'list': [], 'sid_token': 1}
        assert self.session.session_id == None
        self.session.get_email_list()
        expect(self.session.session_id).to.equal(1)

    def test_get_email_list_should_not_update_session_id_when_not_included_in_response(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_client.get_email_list.return_value = {'list': []}
        self.session.session_id = 1
        self.session.get_email_list()
        expect(self.session.session_id).to.equal(1)

    def test_get_email_should_return_client_response_data(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_client.get_email.return_value = {'subject': 'Hello'}
        email = self.session.get_email('123')
        expect(email).to.equal({'subject': 'Hello'})

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


class GetAddressCommandTest(TestCase):
    def setUp(self):
        self.command = GetAddressCommand()

    def test_invoke_should_get_email_address_from_session(self):
        mock_session = Mock(get_email_address=lambda: 'test@example.com')
        output = self.command.invoke(mock_session, None)
        expect(output).to.equal('test@example.com')


class ListEmailCommandTest(TestCase):
    def setUp(self):
        self.command = ListEmailCommand()

    def test_invoke_should_pretty_format_list_from_session_as_json(self):
        mock_session = Mock(get_email_list=lambda: [{'subject': 'Test'}])
        output = self.command.invoke(mock_session, None)
        expect(output).to.equal(json.dumps([{'subject': 'Test'}], indent=2))


class GetEmailCommandTest(TestCase):
    def setUp(self):
        self.command = GetEmailCommand()

    def test_invoke_should_pretty_format_email_from_session_as_json(self):
        mock_session = Mock(get_email=lambda _: {'subject': 'Test'})
        mock_args = Mock(id=1)
        output = self.command.invoke(mock_session, mock_args)
        expect(output).to.equal(json.dumps({'subject': 'Test'}, indent=2))


class GuerrillaMailParseArgsTest(TestCase):
    def test_parse_args_should_extract_address_command(self, **kwargs):
        args = parse_args(['address'])
        expect(args.command).to.equal('address')

    def test_parse_args_should_extract_list_command(self, **kwargs):
        args = parse_args(['list'])
        expect(args.command).to.equal('list')

    def test_parse_args_should_extract_get_command(self, **kwargs):
        args = parse_args(['get', '123'])
        expect(args.command).to.equal('get')
        expect(args.id).to.equal('123')

    def test_parse_args_should_reject_unknown_command(self, **kwargs):
        self.assertRaises(SystemExit, parse_args, ['cheese'])

    def test_parse_args_should_reject_get_command_with_id_missing(self, **kwargs):
        self.assertRaises(SystemExit, parse_args, ['get'])


class GuerrillaMailGetCommandTest(TestCase):
    def test_get_address_command_should_return_get_address_command_instance(self):
        command = get_command('address')
        expect(command).to.be.a('guerrillamail.GetAddressCommand')

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
class GuerrillaMailMainTest(TestCase):
    def setup_mocks(self, GuerrillaMailSession, load_settings, parse_args, get_command, **kwargs):
        load_settings.return_value = {}
        self.mock_session = Mock()
        self.mock_args = Mock()
        self.mock_command = Mock()
        GuerrillaMailSession.return_value = self.mock_session
        parse_args.return_value = self.mock_args
        get_command.return_value = self.mock_command

    def test_main_should_create_session_using_settings(self, GuerrillaMailSession, load_settings, **kwargs):
        self.setup_mocks(GuerrillaMailSession=GuerrillaMailSession, load_settings=load_settings, **kwargs)
        load_settings.return_value = {'arg1': 1, 'arg2': 'cheese'}
        main()
        GuerrillaMailSession.assert_called_with(arg1=1, arg2='cheese')

    def test_main_should_get_command_by_command_name_arg(self, get_command, **kwargs):
        self.setup_mocks(get_command=get_command, **kwargs)
        self.mock_args.command = 'cheese'
        main()
        get_command.assert_called_with('cheese')

    def test_main_should_invoke_command(self, **kwargs):
        self.setup_mocks(**kwargs)
        main()
        self.mock_command.invoke.assert_called_once_with(self.mock_session, self.mock_args)

    def test_main_should_save_settings_with_updated_session_id(self, save_settings, **kwargs):
        self.setup_mocks(**kwargs)
        self.mock_args.command = 'cheese'
        def set_session_id(*args):
            self.mock_session.session_id = 123
        self.mock_command.invoke.side_effect = set_session_id
        main()
        save_settings.assert_called_with({'session_id': 123})
