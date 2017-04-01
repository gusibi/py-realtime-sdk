#! -*- coding: utf-8 -*-

import hmac
import time
from hashlib import sha256

import requests
from six.moves.urllib.parse import urlencode

from .json_import import json
from .helper import md5_constructor as md5


class OAuth2AuthExchangeError(Exception):

    def __init__(self, description):
        self.description = description

    def __str__(self):
        return self.description


class OAuth2API(object):

    host = None
    base_path = None
    access_token_field = 'access_token'
    protocol = "https"
    api_name = "LeanCloud API"

    def __init__(self,
                 app_id=None,
                 app_key=None,
                 master_key=None,
                 client_ips=None,
                 access_token=None):
        self.app_id = app_id
        self.app_key = app_key
        self.master_key = master_key
        self.client_ips = client_ips
        self.access_token = access_token


class OAuth2Request(object):

    def __init__(self, api):
        self.api = api

    def _generate_sign(self, endpoint, params, secret):
        sign = endpoint
        for key in sorted(params.keys()):
            sign += '|%s=%s' % (key, params[key])
        return hmac.new(secret.encode(), sign.encode(), sha256).hexdigest()

    def url_for_get(self, path, parameters):
        return self._full_url_with_params(path, parameters)

    def get_request(self, path, **kwargs):
        return self.make_request(self.prepare_request("GET", path, kwargs))

    def post_request(self, path, **kwargs):
        return self.make_request(self.prepare_request("POST", path, kwargs))

    def _full_url(self, path,
                  include_signed_request=False):
        return "%s://%s%s%s%s" % (self.api.protocol,
                                  self.api.host,
                                  self.api.base_path,
                                  path,
                                  self._signed_request(path, {},
                                                       include_signed_request))

    def _full_url_with_params(self, path, params,
                              include_signed_request=False):
        return (self._full_url(path, include_signed_request) +
                self._full_query_with_params(params) +
                self._signed_request(path, params,
                                     include_signed_request))

    def _full_query_with_params(self, params):
        params = ("?" + urlencode(params)) if params else ""
        return params

    def _auth_headers(self, include_secret=False, include_signed=False):
        headers = {
            'Content-type': 'application/json',
            'X-LC-Id': self.api.app_id,
        }
        if include_signed:
            timestamp = int(time.time() * 1000)
            if include_secret:
                signed_str = md5('%s%s' % (timestamp, self.api.master_key)).hexdigest()
                headers['X-LC-Sign'] = '%s,%s,master' % (signed_str, timestamp)
            else:
                signed_str = md5('%s%s' % (timestamp, self.api.app_key)).hexdigest()
                headers['X-LC-Sign'] = '%s,%s' % (signed_str, timestamp)
        else:
            if include_secret:
                headers['X-LC-Key'] = '{master_key},master'.format(master_key=self.api.master_key)
            else:
                headers['X-LC-Key'] = self.api.app_key
        return headers

    def _signed_request(self, path, params, include_signed_request):
        print include_signed_request
        if include_signed_request and self.api.app_key is not None:
            if self.api.access_token:
                params['access_token'] = self.api.access_token
            elif self.api.app_id:
                params['app_id'] = self.api.app_id
            return "&sig=%s" % self._generate_sign(path, params,
                                                   self.api.app_key)
        else:
            return ''

    def _post_body(self, params):
        json_body = params.pop('json_body', None)
        return urlencode(params), json_body

    def prepare_and_make_request(self, method, path, params,
                                 include_secret=False, include_signed=False):
        url, method, body, json_body, headers = self.prepare_request(method,
                                                          path,
                                                          params,
                                                          include_secret,
                                                          include_signed)
        return self.make_request(url, method, body, json_body, headers)

    def prepare_request(self, method, path, params,
                        include_secret=False, include_signed=True,
                        include_secret_request=False):
        url = body = json_body = None
        headers = self._auth_headers(include_secret=include_secret,
                                     include_signed=include_signed)

        if method in ['POST', 'PUT']:
            body, json_body = self._post_body(params)
            url = self._full_url(path, include_secret_request)
        else:
            url = self._full_url_with_params(path, params, include_secret_request)

        return url, method, body, json_body, headers

    def make_request(self, url, method="GET", body=None, json_body=None, headers=None):
        headers = headers or {}
        headers.update({"User-Agent": "%s Python Client" % self.api.api_name})
        if json_body:
            data = json.dumps(json_body)
        elif body:
            data = body
        else:
            data = None
        print method
        print url
        print data
        print headers
        return requests.request(method, url, data=data, headers=headers)
