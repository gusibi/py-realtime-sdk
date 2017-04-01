#! -*- coding: utf-8 -*-

import re
import hmac

import six
from six.moves.urllib.parse import quote

from .oauth2 import OAuth2Request
from .json_import import json


re_path_template = re.compile('{\w+}')


def encode_string(value):
    return value.encode('utf-8') \
        if isinstance(value, six.text_type) else str(value)


class RealtimeClientError(Exception):
    def __init__(self, error_message, status_code=None):
        self.status_code = status_code
        self.error_message = error_message

    def __str__(self):
        if self.status_code:
            return "(%s) %s" % (self.status_code, self.error_message)
        else:
            return self.error_message


class RealtimeAPIError(Exception):

    def __init__(self, status_code, error_message, *args, **kwargs):
        self.status_code = status_code
        self.error_message = error_message

    def __str__(self):
        return "(%s) %s" % (self.status_code,
                            self.error_message)


def bind_method(**config):

    class RealtimeAPIMethod(object):

        path = config['path']
        method = config.get('method', 'GET')
        accepts_parameters = config.get("accepts_parameters", [])
        response_type = config.get("response_type", 'entry')
        signature = config.get("signature", False)
        master_key = config.get("master_key", False)
        include_secret = config.get("include_secret", False)
        include_signed = config.get('include_signed', False)  # 是否使用 X-LC-Sign
        include_signed_request = config.get('include_signed_request', False)
        objectify_response = config.get("objectify_response", True)
        exclude_format = config.get('exclude_format', True)

        def __init__(self, api, *args, **kwargs):
            self.api = api
            self.return_json = kwargs.pop('return_json', True)
            self.parameters = {}
            self._build_parameters(args, kwargs)
            self._build_path()

        def _build_parameters(self, args, kwargs):
            for index, value in enumerate(args):
                if value is None:
                    continue

                try:
                    self.parameters[self.accepts_parameters[index]] = encode_string(value)
                except IndexError:
                    raise RealtimeClientError("Too many arguments supplied")

            for key, value in six.iteritems(kwargs):
                if value is None or key not in self.accepts_parameters:
                    continue
                if key in self.parameters:
                    raise RealtimeClientError("Parameter %s already supplied" % key)
                if key not in ['body', 'json_body']:
                    self.parameters[key] = encode_string(value)
                else:
                    self.parameters[key] = value

        def _build_path(self):
            for variable in re_path_template.findall(self.path):
                name = variable.strip('{}')

                try:
                    value = quote(self.parameters[name])
                except KeyError:
                    raise Exception('No parameter value found for path variable: %s' % name)
                del self.parameters[name]

                self.path = self.path.replace(variable, value)

            if self.api.format and not self.exclude_format:
                self.path = self.path + '.%s' % self.api.format

        def _do_api_request(self, url, method='GET', body=None,
                            json_body=None, headers=None):
            headers = headers or {}
            if (self.signature and
                    self.api.client_ips is not None and
                    self.api.client_secret is not None):
                secret = self.api.client_secret
                ips = self.api.client_ips
                signature = hmac.new(secret, ips, sha256).hexdigest()

            response = OAuth2Request(self.api).make_request(
                url, method=method, body=body, json_body=json_body, headers=headers)
            content = response.content
            status_code = response.status_code
            try:
                content_obj = json.loads(content)
            except ValueError:
                raise RealtimeClientError(
                    'Unable to parse response, not valid JSON.',
                    status_code=status_code)

            if 200 <= int(status_code) < 300:
                # success
                api_responses = []
                if not self.objectify_response:
                    return content_obj, None
                if self.response_type == 'list':
                    for entry in content_obj:
                        if self.return_json:
                            api_responses.append(entry)
                        else:
                            obj = self.root_class.object_from_dictionary(entry)
                            api_responses.append(obj)
                elif self.response_type == 'entry':
                    data = content_obj
                    if self.return_json:
                        api_responses = data
                    else:
                        api_responses = self.root_class.object_from_dictionary(data)
                elif self.response_type == 'empty':
                    pass
                for response in api_responses:
                    print response
                return api_responses, None
            else:
                code = content_obj.get('code')
                error = content_obj.get('error')

                if code in ['529', '430', '431']:
                    raise RealtimeAPIError(
                        response.status_code, "Rate limited",
                    "Your client is making too many request per second")

                if code and error:
                    raise RealtimeAPIError(code, error)

        def execute(self):
            url, method, body, json_body, headers = OAuth2Request(
                self.api).prepare_request(self.method,
                                          self.path,
                                          self.parameters,
                                          include_secret=self.include_secret,
                                          include_signed=self.include_signed,
                                          include_secret_request=self.include_signed_request)
            content, _ = self._do_api_request(url, method, body, json_body, headers)
            return content

    def _call(api, *args, **kwargs):
        method = RealtimeAPIMethod(api, *args, **kwargs)
        return method.execute()

    return _call
