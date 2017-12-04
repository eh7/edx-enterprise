# -*- coding: utf-8 -*-
"""
Tests for clients in integrated_channels.
"""

from __future__ import absolute_import, unicode_literals, with_statement

import datetime
import json
import unittest

import requests
import responses
from freezegun import freeze_time
from integrated_channels.degreed.client import DegreedAPIClient
from pytest import mark

from django.utils import timezone

from six.moves.urllib.parse import urljoin  # pylint: disable=import-error
from test_utils import factories

NOW = datetime.datetime(2017, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
NOW_TIMESTAMP_FORMATTED = NOW.strftime('%F')


@mark.django_db
@freeze_time(NOW)
class TestDegreedApiClient(unittest.TestCase):
    """
    Test Degreed API client methods.
    """

    def setUp(self):
        super(TestDegreedApiClient, self).setUp()
        self.url_base = "http://betatest.degreed.com/"
        self.oauth_api_path = "oauth/token"
        self.oauth_url = urljoin(self.url_base, self.oauth_api_path)
        self.completion_status_api_path = "api/v1/provider/completion/course"
        self.completion_status_url = urljoin(self.url_base, self.completion_status_api_path)
        self.course_api_path = "api/v1/provider/content/course"
        self.course_url = urljoin(self.url_base, self.course_api_path)
        self.client_id = "client_id"
        self.client_secret = "client_secret"
        self.company_id = "company_id"
        self.user_id = "user_id"
        self.user_pass = "user_pass"
        self.expires_in = 1800
        self.access_token = "access_token"
        self.expected_token_response_body = {"expires_in": self.expires_in, "access_token": self.access_token}
        factories.DegreedGlobalConfigurationFactory(
            degreed_base_url=self.url_base,
            completion_status_api_path=self.completion_status_api_path,
            course_api_path=self.course_api_path,
            oauth_api_path=self.oauth_api_path,
            degreed_user_id=self.user_id,
            degreed_user_password=self.user_pass,
        )
        self.enterprise_config = factories.DegreedEnterpriseCustomerConfigurationFactory(
            key=self.client_id,
            secret=self.client_secret,
            degreed_company_id=self.company_id,
        )

    @responses.activate
    def test_create_course_completion(self):
        """
        ``create_course_completion`` should use the appropriate URLs for transmission.
        """
        responses.add(
            responses.POST,
            self.oauth_url,
            json=self.expected_token_response_body,
            status=200
        )
        responses.add(
            responses.POST,
            self.completion_status_url,
            json='{}',
            status=200
        )

        payload = {
            'orgCode': self.company_id,
            'completions': [{
                'employeeId': 'abc123',
                'id': "course-v1:ColumbiaX+DS101X+1T2016",
                'completionDate': NOW_TIMESTAMP_FORMATTED,
            }]
        }
        degreed_api_client = DegreedAPIClient(self.enterprise_config)
        output = degreed_api_client.create_course_completion('fake-user', json.dumps(payload))

        assert output == (200, '"{}"')
        assert len(responses.calls) == 2
        assert responses.calls[0].request.url == self.oauth_url
        assert responses.calls[1].request.url == self.completion_status_url

    @responses.activate
    def test_delete_course_completion(self):
        """
        ``delete_course_completion`` should use the appropriate URLs for transmission.
        """
        responses.add(
            responses.POST,
            self.oauth_url,
            json=self.expected_token_response_body,
            status=200
        )
        responses.add(
            responses.DELETE,
            self.completion_status_url,
            json='{}',
            status=200
        )

        payload = {
            'orgCode': self.company_id,
            'completions': [{
                'employeeId': 'abc123',
                'id': "course-v1:ColumbiaX+DS101X+1T2016",
            }]
        }
        degreed_api_client = DegreedAPIClient(self.enterprise_config)
        output = degreed_api_client.delete_course_completion('fake-user', json.dumps(payload))

        assert output == (200, '"{}"')
        assert len(responses.calls) == 2
        assert responses.calls[0].request.url == self.oauth_url
        assert responses.calls[1].request.url == self.completion_status_url

    @responses.activate
    def test_create_course_content(self):
        """
        ``create_course_content`` should use the appropriate URLs for transmission.
        """
        responses.add(
            responses.POST,
            self.oauth_url,
            json=self.expected_token_response_body,
            status=200
        )
        responses.add(
            responses.POST,
            self.course_url,
            json='{}',
            status=200
        )

        payload = {
            'orgCode': 'org-code',
            'providerCode': 'provider-code',
            'courses': [{
                'contentId': 'content-id',
                'authors': [],
                'categoryTags': [],
                'url': 'url',
                'imageUrl': 'image-url',
                'videoUrl': 'video-url',
                'title': 'title',
                'description': 'description',
                'difficulty': 'difficulty',
                'duration': 20,
                'publishDate': '2017-01-01',
                'format': 'format',
                'institution': 'institution',
                'costType': 'paid',
                'language': 'en'
            }],
        }
        degreed_api_client = DegreedAPIClient(self.enterprise_config)
        output = degreed_api_client.create_course_content(payload)
        assert output == (200, '"{}"')
        assert len(responses.calls) == 2
        assert responses.calls[0].request.url == self.oauth_url
        assert responses.calls[1].request.url == self.course_url

    @responses.activate
    def test_delete_course_content(self):
        """
        ``delete_course_content`` should use the appropriate URLs for transmission.
        """
        responses.add(
            responses.POST,
            self.oauth_url,
            json=self.expected_token_response_body,
            status=200
        )
        responses.add(
            responses.DELETE,
            self.course_url,
            json='{}',
            status=200
        )

        payload = {
            'orgCode': 'org-code',
            'providerCode': 'provider-code',
            'courses': [{
                'contentId': 'content-id',
            }],
        }
        degreed_api_client = DegreedAPIClient(self.enterprise_config)
        output = degreed_api_client.delete_course_content(payload)
        assert output == (200, '"{}"')
        assert len(responses.calls) == 2
        assert responses.calls[0].request.url == self.oauth_url
        assert responses.calls[1].request.url == self.course_url

    @responses.activate
    def test_expired_token(self):
        """
        If our token expires after some call, make sure to get it again.

        Make a call, have the token expire after waiting some time (technically no time since time is frozen),
        and make a call again and notice 2 OAuth calls in total are required.
        """
        responses.add(
            responses.POST,
            self.oauth_url,
            json={"expires_in": 0, "access_token": self.access_token},
            status=200
        )
        responses.add(
            responses.DELETE,
            self.course_url,
            json='{}',
            status=200
        )

        payload = {
            'orgCode': 'org-code',
            'providerCode': 'provider-code',
            'courses': [{
                'contentId': 'content-id',
            }],
        }
        degreed_api_client = DegreedAPIClient(self.enterprise_config)
        output1 = degreed_api_client.delete_course_content(payload)
        output2 = degreed_api_client.delete_course_content(payload)
        assert output1 == output2 == (200, '"{}"')
        assert len(responses.calls) == 4
        assert responses.calls[0].request.url == self.oauth_url
        assert responses.calls[1].request.url == self.course_url
        assert responses.calls[2].request.url == self.oauth_url
        assert responses.calls[3].request.url == self.course_url

    @responses.activate
    def test_existing_token_is_valid(self):
        """
        On a second call in the same session, if the token isn't expired we shouldn't need to do another OAuth2 call.
        """
        responses.add(
            responses.POST,
            self.oauth_url,
            json=self.expected_token_response_body,
            status=200
        )
        responses.add(
            responses.DELETE,
            self.course_url,
            json='{}',
            status=200
        )

        payload = {
            'orgCode': 'org-code',
            'providerCode': 'provider-code',
            'courses': [{
                'contentId': 'content-id',
            }],
        }
        degreed_api_client = DegreedAPIClient(self.enterprise_config)
        output1 = degreed_api_client.delete_course_content(payload)
        output2 = degreed_api_client.delete_course_content(payload)
        assert output1 == output2 == (200, '"{}"')
        assert len(responses.calls) == 3
        assert responses.calls[0].request.url == self.oauth_url
        assert responses.calls[1].request.url == self.course_url
        assert responses.calls[2].request.url == self.course_url

    @responses.activate
    def test_oauth_response_missing_keys(self):
        """
        A ``requests.RequestException`` is raised when the call for an OAuth2 access token returns no data.
        """
        responses.add(
            responses.POST,
            self.oauth_url,
            json={},
            status=200
        )
        responses.add(
            responses.DELETE,
            self.course_url,
            json={},
            status=200
        )

        degreed_api_client = DegreedAPIClient(self.enterprise_config)
        with self.assertRaises(requests.RequestException):
            degreed_api_client.delete_course_content({})