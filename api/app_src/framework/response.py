# -*-coding: utf-8 -*-
"""Response class.
"""
# app module
from framework.err import BAD_REQUEST, InternalError, ERR_RESPONSE_FORMAT, OK, RequestError, SUCCESS
from framework.py_utilities import NotSet


class Response(dict):
    """API response data in 'dict' foramt which can used for 'json_out' decoratored API.
    Bulitin response status part information.
    """
    def __init__(self, content=None, model_data=None, success=NotSet, err_code=SUCCESS, err_msg=None,
        err_msg_data=None, http_status=BAD_REQUEST):
        """
        [Arguments]
            content  : dict.
                Response data.

            model_data : dict. 
                Data added during the Model, uesd to create response content for View.

            success  : bool.
                Response status.

            err_code : int.
                Error code.

            err_msg  : str. 
                Error message. Auto set value according by 'err_code' if 'err_msg' is not given.

            err_msg_data: tuple.
                Formated data to compose error message.

            http_status: int.
                Set HTTP status code.
        """
        # data from model used for view.
        self.model_data = model_data if model_data else {}

        if content and isinstance(content, dict):
            self.update(content)

        self.http_status = OK  # Only used when failed response.
        self.set_err(success, err_code, err_msg, err_msg_data, http_status)

    def set_err(self, success=NotSet, err_code=SUCCESS, err_msg=None, err_msg_data=None, http_status=BAD_REQUEST):
        """ Set error information.
        [Arguments]
            See __init__.
        [Notes]
            Compare using a error Response with raising a RequestError, the error Response can include
            more information, but the RequestError only has error information.
        """
        if success is NotSet:
            return self  # nothing change
        elif not isinstance(success, bool):
            raise InternalError(code=ERR_RESPONSE_FORMAT, str_data=('success is not bool'))

        if not isinstance(err_code, int):
            raise InternalError(code=ERR_RESPONSE_FORMAT, str_data=('err_code is not int'))

        if not err_msg:  # auto set err_msg
            err = RequestError(code=err_code, str_data=err_msg_data, http_status=http_status)
            err_msg, http_status = err.get_msg(), err.http_status

        if success:
            self.pop('error', None)  # Success response has no error information.
            self.http_status = OK
        else:
            self.update({
                'error': {  # Not include success flag here because that is not useful.
                    'err_code': err_code,
                    'err_msg': err_msg
                }
            })
            self.http_status = http_status
        return self

    def is_success(self):
        """ Check response success.
        """
        return not self.has_key('error')
