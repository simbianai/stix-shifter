from stix_shifter_utils.modules.base.stix_transmission.base_ping_connector import (
    BasePingConnector,
)
from stix_shifter_utils.utils.error_response import ErrorResponder
from stix_shifter_utils.utils import logger as utils_logger
import json


class PingConnector(BasePingConnector):

    def __init__(self, api_client):
        self.api_client = api_client
        self.logger = utils_logger.set_logger(__name__)
        self.connector = __name__.split(".")[1]

    async def ping_connection(self):
        self.logger.info("Pinging Data Source...")
        response = await self.api_client.ping_box()
        response_code = response.code

        response_text = response.read()
        error = None
        response_dict = dict()
        self.logger.info("Ping status: {}".format(response_code))
        try:
            response_dict = json.loads(response_text)
        except Exception as ex:
            self.logger.debug(response_text)
            error = Exception(f"Can not parse response: {ex} : {response_text}")

        self.logger.info("Ping response: {}".format(response_dict))
        self.logger.info("Ping error: {}".format(error))

        return_obj = dict()
        return_obj["success"] = False

        if len(response_dict) > 0 and response_code == 200:
            return_obj["success"] = True
        else:
            ErrorResponder.fill_error(
                return_obj,
                response_dict,
                ["message"],
                error=error,
                connector=self.connector,
            )
        self.logger.info("Ping result: {}".format(return_obj))
        return return_obj
