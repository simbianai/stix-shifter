from stix_shifter_utils.utils.base_entry_point import BaseEntryPoint


class EntryPoint ( BaseEntryPoint ) :

    def __init__ ( self , connection={} , configuration={} , options={} ) :
        super ( ).__init__ ( connection , configuration , options )
        self.set_async ( True )

        if connection :
            self.setup_transmission_basic ( connection , configuration )

        self.add_dialect ( 'default' , default = True )

    def get_translated_queries ( self , data , query , options={} ) :
        # This returns the raw query, bypassing the STIX parsing
        return [ query ]