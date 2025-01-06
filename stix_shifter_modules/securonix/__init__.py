from stix_shifter_modules.securonix.entry_point import EntryPoint

def entry(connection={}, configuration={}, options={}):
    return EntryPoint(connection, configuration, options)