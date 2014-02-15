from unittest.case import TestCase

import httpretty
from mock import patch, DEFAULT, Mock
from sure import expect

from guerrillamail import GuerrillaMailClient, GuerrillaMailException, main


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
    def test_get_email_address_should_extract_returned_address(self):
        response_body = '{"email_addr":"test@example.com"}'
        httpretty.register_uri(httpretty.GET, 'http://test-host/ajax.php',
                               body=response_body, match_querystring=True)
        email_address = self.client.get_email_address()
        expect(email_address).to.equal('test@example.com')

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
    def test_get_email_list_should_extract_returned_emails(self):
        response_body = '{"list":[{"subject":"Hello"}]}'
        httpretty.register_uri(httpretty.GET, 'http://test-host/ajax.php',
                               body=response_body, match_querystring=True)
        email_list = self.client.get_email_list()
        expect(email_list).to.equal([{'subject': 'Hello'}])

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
        self.client.get_email(123)
        expect(httpretty.last_request()).to.have.property('querystring').being.equal({
            'f': ['fetch_email'],
            'ip': ['127.0.0.1'],
            'email_id': ['123'],
        })

    @httpretty.activate
    def test_get_email_should_return_deserialized_json(self):
        response_body = '{"subject":"Hello"}'
        httpretty.register_uri(httpretty.GET, 'http://test-host/ajax.php',
                               body=response_body, match_querystring=True)
        email = self.client.get_email(123)
        expect(email).to.equal({'subject': 'Hello'})

    @httpretty.activate
    def test_get_email_should_raise_exception_on_failed_request(self):
        httpretty.register_uri(httpretty.GET, 'http://test-host/ajax.php', status=500)
        expect(self.client.get_email).when.called_with(email_id=123).should.throw(GuerrillaMailException)


@patch.multiple('guerrillamail', load_settings=DEFAULT, save_settings=DEFAULT, GuerrillaMailClient=DEFAULT)
class GuerillaMailMainTest(TestCase):

    def setup_mocks(self, GuerrillaMailClient, load_settings, **kwargs):
        load_settings.return_value = {}
        self.mock_client = Mock()
        GuerrillaMailClient.return_value = self.mock_client

    def test_address_command_should_invoke_get_email_address(self, **kwargs):
        self.setup_mocks(**kwargs)
        main('address')
        self.mock_client.get_email_address.assert_called_once_with()

    def test_list_command_should_invoke_get_email_list(self, **kwargs):
        self.setup_mocks(**kwargs)
        main('list')
        self.mock_client.get_email_list.assert_called_once_with()

    def test_get_command_should_invoke_get_email(self, **kwargs):
        self.setup_mocks(**kwargs)
        main('get', '123')
        self.mock_client.get_email.assert_called_once_with('123')

    def test_get_command_should_exit_when_id_missing(self, **kwargs):
        self.setup_mocks(**kwargs)
        self.assertRaises(SystemExit, main, 'get')
