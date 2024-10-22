import asyncio
from stix_shifter_utils.modules.base.stix_transmission.base_json_results_connector import (
    BaseJsonResultsConnector,
)
from stix_shifter_utils.utils.error_response import ErrorResponder
from stix_shifter_utils.utils import logger
import json


class ResultsConnector(BaseJsonResultsConnector):
    def __init__(self, api_client):
        self.api_client = api_client
        self.logger = logger.set_logger(__name__)
        self.connector = __name__.split(".")[1]

    async def create_results_connection(self, search_id, offset, length):
        self.logger.debug("Getting search results...")

        max_retries = 10  # Maximum number of retries
        retry_delay = 20  # Seconds to wait before retrying

        min_range = int(offset)
        max_range = int(offset) + int(length) - 1

        for attempt in range(1, max_retries + 1):
            try:
                # Grab the response, extract the response code, and convert it to readable json
                response = await self.api_client.get_search_results(
                    search_id, "application/json", min_range, max_range
                )
                response_code = response.code

                # Construct a response object
                return_obj = dict()
                error = None
                response_text = response.read()
                response_dict = dict()

                self.logger.debug(f"Results response: {response_code}")
                self.logger.debug(f"Results response: {response_text}")

                try:
                    response_dict = json.loads(response_text)
                except ValueError as ex:
                    self.logger.debug(response_text)
                    error = Exception(
                        f"Cannot parse response from Qradar server. The response is not a valid JSON: {response_text} : {ex}"
                    )

                # self.logger.info(f"Results response: {response_dict}")
                self.logger.debug(f"Results error: {error}")

                if 200 <= response_code <= 299 and error is None:
                    return_obj["success"] = True
                    data = response_dict.get("events", response_dict.get("flows"))
                    ResultsConnector.modify_result(data)
                    return_obj["data"] = data
                else:
                    ErrorResponder.fill_error(
                        return_obj,
                        response_dict,
                        ["message"],
                        error=error,
                        connector=self.connector,
                    )
                    self.logger.warning(
                        f"Attempt {attempt}/{max_retries} failed with error: {error}"
                    )
                    if attempt < max_retries:
                        await asyncio.sleep(retry_delay)  # Wait before retrying
                    else:
                        raise Exception("Error in retrieving search results")

                self.logger.debug(f"Results result: {return_obj}")
                return return_obj

            except Exception as e:
                self.logger.warning(
                    f"Attempt {attempt}/{max_retries} failed with error: {e}"
                )
                if attempt < max_retries:
                    await asyncio.sleep(retry_delay)  # Wait before retrying
                else:
                    self.logger.error(f"Max retries reached for search_id: {search_id}")
                    raise  # Re-raise the exception after max retries

    @classmethod
    def modify_result(cls, results):
        for result in results:
            if result.get("eventpayload") or result.get("Message"):
                result["mime_type_eventpayload"] = "text/plain"

            if result.get("Message"):
                result["mime_type_message"] = "text/plain"

            if result.get("flowsourcepayload"):
                result["mime_type_flowsourcepayload"] = "application/octet-stream"

            if result.get("flowdestinationpayload"):
                result["mime_type_flowdestinationpayload"] = "application/octet-stream"

            if result.get("sourceip"):
                if result["sourceip"] == "0.0.0.0":
                    result["sourceip"] = None

            if result.get("destinationip"):
                if result["destinationip"] == "0.0.0.0":
                    result["destinationip"] = None

            if result.get("sourcemac"):
                if (
                    result["sourcemac"] == "00:00:00:00:00:00"
                    or result["sourcemac"] == "00-00-00-00-00-00"
                ):
                    result["sourcemac"] = None

            if result.get("destinationmac"):
                if (
                    result["destinationmac"] == "00:00:00:00:00:00"
                    or result["destinationmac"] == "00-00-00-00-00-00"
                ):
                    result["destinationmac"] = None

            if result.get("identityip"):
                if result["identityip"] == "0.0.0.0":
                    result["identityip"] = None

            if result.get("sourcev6"):
                if result["sourcev6"] == "0:0:0:0:0:0:0:0":
                    result["sourcev6"] = None

            if result.get("destinationv6"):
                if result["destinationv6"] == "0:0:0:0:0:0:0:0":
                    result["destinationv6"] = None
