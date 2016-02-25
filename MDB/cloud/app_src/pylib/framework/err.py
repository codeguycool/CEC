# -*-coding: utf-8 -*-
''' Error information
'''


class BaseError(RuntimeError):
    '''Common exception class.
    '''
    def __init__(self, code, message=None, str_data=()):
        '''
        [Arguments]
            code     : int.
                Error code.

            message  : str.  (optional)
                Error message.

            str_data : tuple. (optional)
                Formated data to compose error message.
        '''
        if not isinstance(code, int):
            raise ValueError('code value error')

        self.code = code
        self.message = message if message else ERR_MSG.get(self.code, '')
        self.str_data = str_data

    def get_msg(self):
        return self.message % self.str_data

class RequestError(BaseError):
    '''This exception information will display to API response.
    '''
    pass

class InternalError(BaseError):
    '''This exception information ONLY display to log. And response 500 error to client.
    '''
    pass


## [ERROR CODE] 
# HTTP status code section.
# Just mapping them. (Need?)
METHOD_NOT_IMPLEMENTED = 405
INTERNAL_SERVER_ERROR = 500

# APP section.
# To response to client.
SUCCESS = 0 # request success
ERR_DB_QUERY = 1000 # common error
ERR_DB_NOT_FOUND = 1001
ERR_REQUEST_ARG = 2000

# APP internal section (Need?)
# For logging information.
ERR_RESPONSE_FORMAT = 9000 

## [ERROR MESSAGE]
ERR_MSG = {
	# For HTTP status code.
	METHOD_NOT_IMPLEMENTED: 'Method Not Implemented.',
    INTERNAL_SERVER_ERROR: 'Sorry, an error occured.',

	# APP section
    SUCCESS: '',
    ERR_DB_QUERY: 'Database Query Failure.',
    ERR_DB_NOT_FOUND : 'Data Not Found.',
    ERR_REQUEST_ARG: 'Request Args Error: %s',

    # APP internal section
    ERR_RESPONSE_FORMAT: 'Response Format Error: %s'
}
