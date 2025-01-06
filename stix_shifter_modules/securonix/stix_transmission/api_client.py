import json
import requests
from urllib.parse import urlencode
from stix_shifter_utils.stix_transmission.utils.RestApiClientAsync import RestApiClientAsync
from datetime import datetime, timedelta
from stix_shifter_utils.utils import logger
import time


class APIResponseException(Exception):
    def __init__(self, error_code, error_message, content_header_type, response):
        self.error_code = error_code
        self.error_message = error_message
        self.content_header_type = content_header_type
        self.response = response

    pass


class APIClient:
    TOKEN_ENDPOINT = '/Snypr/ws/token/generate'
    SEARCH_ENDPOINT = '/Snypr/ws/spotter/search'
    logger = logger.set_logger(__name__)

    """API Client to handle all calls."""

    def __init__(self):
        """Initialization.
        :param connection: dict, connection dict
        :param configuration: dict,config dict"""

        self.timeout = 60

        self.headers = dict()
        self.headers['Content-Type'] = 'application/json'
        self.headers['Accept'] = '*/*'
        self.headers['user-agent'] = 'oca_stixshifter_1.0'

        self.auth_headers = dict()
        self.auth_headers['Content-Type'] = 'application/json'
        self.auth_headers['user-agent'] = 'oca_stixshifter_1.0'

        self._token_time = datetime.now() - timedelta(days=7)

    def ping_box(self, client, base_url, auth_headers, headers, timeout):
        token = self._get_token(client, base_url, auth_headers, timeout)
        headers['token'] = token
        params = {
            "query": "index=activity"
        }
        try:
            response = requests.get(f"{base_url}{self.SEARCH_ENDPOINT}", headers=headers, params=params,
                                    timeout=self.timeout, verify=False)

            response_obj = type('response_obj', (), {})()
            response_obj.code = response.status_code
            response_obj.content = response.content
            response_obj.headers = response.headers
            return response_obj
        except Exception as e:
            self.logger.error(f"Error during ping box: {e}")
            raise e

    def get_securonix_data(self, query, client, base_url, auth_headers, headers, timeout, queryId=None,
                           count_only=False):
        token = self._get_token(client, base_url, auth_headers, timeout)
        headers['token'] = token
        headers['Accept'] = '*/*'
        headers['Content-Type'] = 'application/json'
        headers['user-agent'] = 'oca_stixshifter_1.0'
        now = datetime.now()
        past_24_hours = now - timedelta(hours=24)

        params = {
            "query": f"index=activity AND {query}",
            "eventtime_from": past_24_hours.strftime("%m/%d/%Y %H:%M:%S"),
            "eventtime_to": now.strftime("%m/%d/%Y %H:%M:%S")
        }

        if (queryId != None):
            params["queryId"] = queryId

        if (count_only == True):
            params["count_only"] = "true"

        self.logger.debug(f"Final Request URL : {base_url}{self.SEARCH_ENDPOINT}?{urlencode(params)}")
        try:
            response = requests.get(f"{base_url}{self.SEARCH_ENDPOINT}", headers=headers, params=params,
                                    timeout=timeout, verify=False)

            response_obj = type('response_obj', (), {})()
            response_obj.code = response.status_code
            response_obj.content = response.content
            response_obj.headers = response.headers
            return response_obj
        except Exception as e:
            self.logger.error(f"Error getting securonix data: {e}")
            raise e

    def _get_token(self) -> str:
        self.logger.debug(f"Checking if the current token has expired. Token Creation time was {self._token_time}")
        if (datetime.now() - self._token_time) >= timedelta(minutes=30):
            self.logger.debug(f"Attempting to get a new authenctication token")

            self.auth_headers['username'] = self.username
            self.auth_headers['password'] = self.password
            self.auth_headers['validity'] = '365'

            try:
                response = requests.get(self.base_url + self.TOKEN_ENDPOINT, headers=self.auth_headers,
                                        timeout=self.timeout, verify=False)
                # A successful response can be 200 or 201.
                if response.status_code >= 200 and response.status_code < 300:

                    self.logger.debug(f"Get authentication token was successful.")
                    token_text = response.text
                    token = token_text.strip('"')
                    self._token = token
                    self._token_time = datetime.now()
                    return token
                else:
                    self.logger.debug(f"Get authentication token was not successful.")
                    raise APIResponseException(response.status_code, response.text,
                                               response.headers.get('Content-Type'), response)
            except Exception as e:
                self.logger.error(f"Error getting token: {e}")
                raise e
        return self._token