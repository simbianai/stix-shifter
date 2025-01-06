from stix_shifter_utils.modules.base.stix_translation.base_query_translator import BaseQueryTranslator
import logging
import re
from os import path
import json
from . import query_constructor
from stix_shifter_utils.utils.file_helper import read_json
from datetime import datetime

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

    @staticmethod
    def _get_resourcegroup_name(query_string):
        """Extract resourcegroup name from the query string"""
        resourcegroup_pattern = r"resourcegroupname = '([^']+)'"
        match = re.search(resourcegroup_pattern, query_string)
        if match:
            return match.group(1)
        return None

    def transform_antlr(self, data, antlr_parsing_object):
        logger.info("Converting STIX2 Pattern to Securonix Query")

        # Get the base query from the pattern
        query_string = query_constructor.translate_pattern(
            antlr_parsing_object, self, self.options)

        # Extract start and end times from the pattern
        timestamp_pattern = r"START t'([^']+)' STOP t'([^']+)'"
        match = re.search(timestamp_pattern, data)

        if match:
            start_time = datetime.strptime(match.group(1), '%Y-%m-%dT%H:%M:%S.%fZ')
            end_time = datetime.strptime(match.group(2), '%Y-%m-%dT%H:%M:%S.%fZ')

            # Format timestamps for Securonix API
            formatted_start = start_time.strftime('%m/%d/%Y %H:%M:%S')
            formatted_end = end_time.strftime('%m/%d/%Y %H:%M:%S')

            # Add timestamps to the query
            query_string = f"{query_string}&eventtime_from={formatted_start}&eventtime_to={formatted_end}"

        return query_string

