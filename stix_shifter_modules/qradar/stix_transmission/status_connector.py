import asyncio
from stix_shifter_utils.modules.base.stix_transmission.base_status_connector import (
    BaseStatusConnector,
)
from stix_shifter_utils.modules.base.stix_transmission.base_status_connector import (
    Status,
)
from stix_shifter_utils.utils.error_response import ErrorResponder
from stix_shifter_utils.utils import logger as utils_logger
from enum import Enum
import json


class QRadarStatus(Enum):
    # WAIT, EXECUTE, SORTING, COMPLETED, CANCELED, ERROR
    WAIT = "WAIT"
    EXECUTE = "EXECUTE"
    SORTING = "SORTING"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"
    ERROR = "ERROR"


class StatusConnector(BaseStatusConnector):
    def __init__(self, api_client):
        self.api_client = api_client
        self.logger = utils_logger.set_logger(__name__)
        self.connector = __name__.split(".")[1]

    def __getStatus(self, qradar_status):
        switcher = {
            QRadarStatus.WAIT.value: Status.RUNNING,
            QRadarStatus.EXECUTE.value: Status.RUNNING,
            QRadarStatus.SORTING.value: Status.RUNNING,
            QRadarStatus.COMPLETED.value: Status.COMPLETED,
            QRadarStatus.CANCELED.value: Status.CANCELED,
            QRadarStatus.ERROR.value: Status.ERROR,
        }
        return switcher.get(qradar_status).value

    async def create_status_connection(self, search_id):
        self.logger.debug("Getting search status...")

        max_retries = 10  # Maximum number of retries
        retry_delay = 20  # Seconds to wait before retrying

        for attempt in range(1, max_retries + 1):
            try:
                # Grab the response, extract the response code, and convert it to readable json
                response = await self.api_client.get_search(search_id)
                response_code = response.code
                response_text = response.read()

                error = None
                response_dict = dict()
                self.logger.debug(f"Status response: {response_code}")
                self.logger.debug(f"Status response: {response_text}")

                try:
                    response_dict = json.loads(response_text)
                except Exception as ex:
                    self.logger.debug(response_text)
                    error = Exception(f"Cannot parse response: {ex} : {response_text}")

                self.logger.debug(f"Status response: {response_dict}")
                self.logger.debug(f"Status error: {error}")

                # Construct a response object
                return_obj = dict()

                if response_code == 200:
                    return_obj["success"] = True
                    return_obj["status"] = self.__getStatus(response_dict["status"])
                    if return_obj["status"] == Status.RUNNING.value:
                        await asyncio.sleep(10)
                        if response_dict["progress"] == 100:
                            return_obj["progress"] = 10
                        else:
                            return_obj["progress"] = response_dict.get("progress", 0)
                    else:
                        return_obj["progress"] = response_dict.get("progress", 0)
                else:
                    ErrorResponder.fill_error(
                        return_obj,
                        response_dict,
                        ["message"],
                        error=error,
                        connector=self.connector,
                    )
                    if 400 <= response_code <= 499:
                        return return_obj
                    else:
                        self.logger.warning(
                            f"Attempt {attempt}/{max_retries} failed with error: {error}"
                        )
                        if attempt < max_retries:
                            await asyncio.sleep(retry_delay)  # Wait before retrying
                        else:
                            raise Exception("Error in retrieving search results")
                self.logger.debug(f"Status result: {return_obj}")
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
