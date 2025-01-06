from stix_shifter_utils.modules.base.stix_translation.base_query_translator import BaseQueryTranslator
import logging
from os import path
import json
from . import query_constructor
from stix_shifter_utils.utils.file_helper import read_json

logger = logging.getLogger(__name__)


class QueryTranslator(BaseQueryTranslator):

    @staticmethod
    def _get_ip_value(query_string):
        """Extract IP value from the query string"""
        # Extract IP address from patterns like device.external_ip = '192.168.1.100'
        import re
        ip_pattern = r"'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'"
        match = re.search(ip_pattern, query_string)
        if match:
            return match.group(1)
        return None

    def transform_antlr(self, data, antlr_parsing_object):
        logger.info("Converting STIX2 Pattern to Securonix Query")

        # Get the base query from the pattern
        query_string = query_constructor.translate_pattern(
            antlr_parsing_object, self, self.options)

        # Transform to Securonix Spotter format
        if "ipv4-addr:value" in str(antlr_parsing_object):
            # Handle IP address queries
            ip_value = self._get_ip_value(query_string)  # Extract IP from query
            formatted_query = f"index=activity AND sourceaddress='{ip_value}' AND resourcegroupname=TCC_MERAKI_FIREWALL"
        else:
            # Handle other query types
            formatted_query = f"index=activity AND {query_string}"

        return formatted_query
