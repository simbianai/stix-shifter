import json
from stix_shifter_utils.modules.base.stix_transmission.base_json_sync_connector import BaseJsonSyncConnector
from .api_client import APIClient
from stix_shifter_utils.utils.error_response import ErrorResponder
from stix_shifter_utils.utils import logger
from stix_shifter_modules.securonix.stix_transmission.api_client import APIResponseException
from requests.exceptions import ConnectionError
from datetime import datetime, timezone


class Connector(BaseJsonSyncConnector):
    init_error = None
    logger = logger.set_logger(__name__)
    PROVIDER = 'Securonix'

    def __init__(self, connection, configuration):
        self.connector = __name__.split('.')[1]
        self.api_client = APIClient(connection, configuration)
        self.result_limit = connection['options'].get('result_limit', 1000)
        self.status = dict()

    def ping_connection(self):
        return_obj = {}
        try:
            self.logger.debug(f"Attempting to ping the service for an auth token")
            response = self.api_client.ping_box()
            response_code = response.code
            response_msg = response.read().decode('utf-8')
            if response_code == 200:
                self.logger.debug(f"Successfully pinged the device for an auth token")
                return_obj['success'] = True
            else:
                response_type = response.headers.get('Content-Type')
                raise APIResponseException(response_code, response_msg, response_type, response)
        except Exception as e:
            return self._handle_Exception(e)

        return return_obj

    def create_results_connection(self, query, offset, length, metadata=None):
        # Initialize the starting offset and initial variables to empty.
        return_obj = dict()
        length = int(length)
        offset = int(offset)

        if (metadata == None):
            metadata = dict()
            current_offset = offset
            metadata["result_count"] = 0
        else:
            current_offset = metadata["offset"]

        try:
            # Query the alert endpoint to get a list of ID's. The ID's are in a list of list format.
            securonix_data = self._get_securonix_data(length, query, current_offset, metadata)
        except Exception as e:
            return self._handle_Exception(e)

        # If the total count is greater than the result limit,
        if (metadata["offset"] > self.result_limit):
            securonix_data = securonix_data[0:(self.result_limit - offset) - 1]

        if (metadata["result_count"] >= self.result_limit) or len(securonix_data) < length:
            metadata = None

        return_obj["success"] = True
        return_obj["metadata"] = metadata
        return_obj["data"] = self.translate_results(self, securonix_data)

        self.logger.debug(f"Data being returned : {return_obj}")
        print(json.dumps(return_obj, indent=4))
        return return_obj

    def _get_securonix_data(self, length, query, current_offset, metadata):
        securonix_data = []
        self.logger.debug(f"Collecting results using the following query/filter : {query}")

        # Get the next batch of ID's to process. We use length as batch size as this only gets the ID, not the data.
        # 10000 is the maximum amount that can be asked for at once.
        self.logger.debug(
            f"Using the following settings to get a batch of ID's: offset : {current_offset}, length : {length}")

        get_data_response = self.api_client.get_securonix_data(query)
        if get_data_response.code == 200:
            self.logger.debug(f"Successfully got a list of results")

            get_data_response_data = get_data_response.read().decode('utf-8')
            self.logger.debug(f"Raw Response from API : {get_data_response_data}")

            try:
                get_data_response_json = json.loads(get_data_response_data)

                if "results" in get_data_response_json:
                    securonix_data.extend(get_data_response_json.get('results'))
                    metadata["result_count"] = metadata["result_count"] + len(get_data_response_json.get('results'))

                else:
                    self.logger.warning(
                        f"Response did not contain 'results' key. Assuming empty result. Full response: {get_data_response_json}")
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to decode JSON: {e}. Full response: {get_data_response_data}")
                raise e

            if (len(securonix_data) < length or len(securonix_data) == 0):
                current_offset = current_offset + len(securonix_data)
            else:
                current_offset = current_offset + length
        else:
            raise APIResponseException(get_data_response.code, get_data_response.content,
                                       get_data_response.headers.get('Content-Type'), get_data_response)

        # We now know the next meta_data offset
        metadata["offset"] = current_offset
        return securonix_data

    def _handle_Exception(self, exception):
        response_dict = {}
        return_obj = {}
        try:
            raise exception
        except APIResponseException as ex:
            return self._handle_api_response(ex)
        except Exception as ex:
            ErrorResponder.fill_error(return_obj, response_dict, error=ex, connector=self.connector)
            return return_obj

    def _handle_api_response(self, rest_api_exception):
        response_dict = {}
        return_obj = {}
        connection_error = None

        if (rest_api_exception.content_header_type == 'application/json'):
            response = json.loads(rest_api_exception.error_message)
            if 'error' in response:
                response_dict['message'] = response['error']
            elif 'message' in response:
                response_dict['message'] = response['message']
            else:
                response_dict['message'] = str(rest_api_exception.error_message)
            if (rest_api_exception.error_code == 400):
                response_dict['type'] = 'ValidationError'
            elif (rest_api_exception.error_code == 401):
                response_dict['type'] = 'AuthenticationError'
            elif (rest_api_exception.error_code == 403):
                response_dict['type'] = 'TokenError'
        elif (rest_api_exception.content_header_type == 'text/html'):
            response = rest_api_exception.error_message
            connection_error = ConnectionError(f'Error connecting the datasource: {rest_api_exception.error_message}')
        else:
            raise Exception(rest_api_exception.error_message)

        ErrorResponder.fill_error(return_obj, response_dict, ['message'], error=connection_error,
                                  connector=self.connector)
        return return_obj