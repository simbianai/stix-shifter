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

    def __init__(self, options, dialect, basepath, custom_mapping=None):
        super().__init__(options, dialect, basepath, custom_mapping=custom_mapping)

    def transform_antlr(self, data, antlr_parsing_object):
        logger.info("Converting STIX2 Pattern to Securonix Query")

        query_params = query_constructor.translate_pattern(
            antlr_parsing_object, self, self.options)

        # Extract the components from the query_params dictionary
        base_query = query_params['query']
        eventtime_from = query_params['parameters']['eventtime_from']
        eventtime_to = query_params['parameters']['eventtime_to']

        # Construct the complete query string with all components
        complete_query = f"index=activity AND {base_query} AND eventtime>=\"{eventtime_from}\" AND eventtime<=\"{eventtime_to}\""

        return complete_query


