from stix_shifter_utils.modules.base.stix_translation.base_query_translator import BaseQueryTranslator
import logging
from . import query_constructor
from stix_shifter_utils.utils.file_helper import read_json

logger = logging.getLogger(__name__)


class QueryTranslator(BaseQueryTranslator):

    def __init__(self, options, dialect, basepath, custom_mapping):
        super().__init__(options, dialect, basepath, custom_mapping)
        self.select_fields = read_json(f"aql_{self.dialect}_fields", options)

    def map_selections(self):
        return ", ".join(self.select_fields['default'])

    def transform_antlr(self, data, antlr_parsing_object):
        """
        Transforms STIX pattern into a different query format. Based on a mapping file
        :param antlr_parsing_object: Antlr parsing objects for the STIX pattern
        :type antlr_parsing_object: object
        :param mapping: The mapping file path to use as instructions on how to transform the given STIX query into another format. This should default to something if one isn't passed in
        :type mapping: str (filepath)
        :return: transformed query string
        :rtype: str
        """

        logger.info("Converting STIX2 Pattern to ariel")

        query_string = query_constructor.translate_pattern(
            antlr_parsing_object, self, self.options)
        return query_string
