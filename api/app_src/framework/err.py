# -*-coding: utf-8 -*-
""" Error information
"""


class BaseError(RuntimeError):
    """Common exception class.
    """
    def __init__(self, code, message=None, str_data=None):
        """
        [Arguments]
            code     : int.
                Error code.

            message  : str.  (optional)
                Error message.

            str_data : tuple. (optional)
                Formated data to compose error message.
        """
        if not isinstance(code, int):
            raise ValueError('code value error')

        if message and not isinstance(message, basestring):
            raise ValueError('message value error')

        if str_data and not isinstance(str_data, (basestring, tuple)):
            raise ValueError('str_data value error')

        self.code = code
        self.message = message if message else ERR_MSG.get(self.code, '')
        self.str_data = str_data if str_data else ()

    def get_msg(self):
        return self.message % self.str_data


class RequestError(BaseError):
    """This exception information will display to API response.
    """
    def __init__(self, code=None, message=None, str_data=None, http_status=400):
        """
        [Arguments]
            http_status: int.
                Set HTTP status code.
        """
        if not code:  # Use http_status if it not set code.
            code = http_status

        super(RequestError, self).__init__(code, message, str_data)
        self.http_status = http_status


class InternalError(BaseError):
    """This exception information ONLY display to log. And response 500 error to client.
    """
    pass


# [ERROR CODE]
# HTTP status code section.
# Just mapping them.
OK = 200
BAD_REQUEST = 400
UNAUTHORIZED = 401
FORBIDDEN = 403
NOT_FOUND = 404
METHOD_NOT_IMPLEMENTED = 405
INTERNAL_SERVER_ERROR = 500

# APP section.
# To response to client.
SUCCESS = 0  # request success
ERR_DB_QUERY = 1000  # common error
ERR_DB_NOT_FOUND = 1001
ERR_DB_TIME_OUT = 1002
ERR_REQUEST_ARG = 2000

# APP internal section (Need?)
# For logging information.
ERR_RESPONSE_FORMAT = 9000 

# [ERROR MESSAGE]
ERR_MSG = {
    # For HTTP status code.
    BAD_REQUEST: 'Bad Request.',
    UNAUTHORIZED: 'Unauthorized.',
    FORBIDDEN: 'Forbidden.',
    NOT_FOUND: 'Page Not Found.',
    METHOD_NOT_IMPLEMENTED: 'Method Not Implemented.',
    INTERNAL_SERVER_ERROR: 'Sorry, an error occured.',

    # APP section
    SUCCESS: '',
    ERR_DB_QUERY: 'Database Query Failure.',
    ERR_DB_NOT_FOUND: 'Data Not Found.',
    ERR_DB_TIME_OUT: 'Database Query Time Out',
    ERR_REQUEST_ARG: 'Request Args Error: %s',

    # APP internal section
    ERR_RESPONSE_FORMAT: 'Response Format Error: %s'
}
