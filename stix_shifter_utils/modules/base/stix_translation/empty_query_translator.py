from .base_query_translator import BaseQueryTranslator


class EmptyQueryTranslator(BaseQueryTranslator):

    def __init__(self, options, dialect, basepath=None, custom_mapping=None):
        self.options = options
        self.dialect = dialect
        self.map_data = {}
        self.select_fields = {}
