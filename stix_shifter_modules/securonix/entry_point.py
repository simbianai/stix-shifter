from stix_shifter_utils.utils.base_entry_point import BaseEntryPoint
import asyncio


class EntryPoint(BaseEntryPoint):

    def __init__(self, connection={}, configuration={}, options={}):
        super().__init__(connection, configuration, options)
        self.set_async(False)

        if connection:
            self.setup_transmission_basic(connection, configuration)

        self.add_dialect('default', default=True)

    def get_translated_queries(self, data, query, options={}):
        # This returns the raw query, bypassing the STIX parsing
        return [query]

    def create_results_connection(self, query, offset, length, metadata=None):
        # Wrap the async call in asyncio.run
        return asyncio.run(super().create_results_connection(query, offset, length, metadata=metadata))

    def ping_connection(self):
        # Wrap the async call in asyncio.run
        return asyncio.run(self.transmission.ping_connection())

    def get_query_translator(self, dialect):
        # Ensure we pass parameters to query translator
        return self.stix_translation.QueryTranslator(self.connection, self.configuration)