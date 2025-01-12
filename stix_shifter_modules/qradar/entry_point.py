from stix_shifter_utils.utils.base_entry_point import BaseEntryPoint
from .stix_translation.aql_query_translator import AqlQueryTranslator


class EntryPoint(BaseEntryPoint):

    def __init__(self, connection={}, configuration={}, options={}):
        super().__init__(connection, configuration, options)
        if connection:
            self.setup_transmission_simple(connection, configuration)

        self.setup_translation_simple(dialect_default='flows')
        dialect = 'aql'
        self.add_dialect(dialect,  AqlQueryTranslator(options, dialect, None), default_include=True, default=True)

    def handle_custom_mapping(self, custom_mapping):
        if custom_mapping:
            if custom_mapping.get('events_from_stix_mapping') and custom_mapping.get('events_to_stix_mapping') and custom_mapping.get('events_fields'):
                self.add_dialect(dialect='events', custom_mapping=custom_mapping)
            if custom_mapping.get('flows_from_stix_mapping') and custom_mapping.get('flows_to_stix_mapping') and custom_mapping.get('flows_fields'):
                self.add_dialect(dialect='flows', custom_mapping=custom_mapping)
