import asyncio
from stix_shifter_utils.modules.base.stix_transmission.base_connector import (
    BaseQueryConnector,
)
from stix_shifter_utils.utils.error_response import ErrorResponder
from stix_shifter_utils.utils import logger
import json


class QueryConnector(BaseQueryConnector):
    def __init__(self, api_client):
        self.api_client = api_client
        self.logger = logger.set_logger(__name__)
        self.connector = __name__.split(".")[1]

    async def create_query_connection(self, query):
        self.logger.info("Creating query connection...")

        max_retries = 10  # Maximum number of retries
        retry_delay = 20  # Seconds to wait before retrying

        for attempt in range(1, max_retries + 1):
            try:
                # Grab the response, extract the response code, and convert it to readable json
                response = await self.api_client.create_search(query)
                response_code = response.code
                response_text = response.read()

                error = None
                response_dict = dict()
                self.logger.info(f"Query response: {response_code}")

                try:
                    response_dict = json.loads(response_text)
                except ValueError as ex:
                    self.logger.debug(response_text)
                    error = Exception(f"Cannot parse response: {ex} : {response_text}")

                self.logger.info(f"Query response: {response_dict}")
                self.logger.info(f"Query error: {error}")

                # Construct a response object
                return_obj = dict()

                if response_code == 201:
                    return_obj["success"] = True
                    return_obj["search_id"] = response_dict["search_id"]
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
                        raise Exception("Error in getting search status")
                self.logger.info(f"Query result: {return_obj}")
                return return_obj

            except Exception as e:
                self.logger.warning(
                    f"Attempt {attempt}/{max_retries} failed with error: {e}"
                )
                if attempt < max_retries:
                    await asyncio.sleep(retry_delay)  # Wait before retrying
                else:
                    self.logger.error(f"Max retries reached for query: {query}")
                    raise  # Re-raise the exception after max retries
