from stix_shifter_utils.utils.base_entry_point import BaseEntryPoint


class EntryPoint(BaseEntryPoint):

    def __init__(self, connection={}, configuration={}, options={}, custom_mapping=None):
        super().__init__(connection, configuration, options)
        self.set_async(False)

        if connection:
            self.setup_transmission_basic(connection, configuration)

        self.setup_translation_simple(dialect_default='default')

        if custom_mapping:
            table_names = custom_mapping['to_stix_mapping'].keys()
            print("table_names: ", table_names)
            for table_name in table_names:
                self.add_dialect(dialect=table_name, custom_mapping=custom_mapping)
