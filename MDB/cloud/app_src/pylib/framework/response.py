# -*-coding: utf-8 -*-
'''Response class.
'''
# app module
from framework.err import ERR_MSG, InternalError, ERR_RESPONSE_FORMAT, SUCCESS


class Response(dict):
    '''API response data in 'dict' foramt which can used for 'json_out' decoratored API.
    Bulitin response status part information.
    '''
    def __init__(self, content=None, success=True, err_code=SUCCESS, err_msg=None, model_data=None):
        '''
        [Arguments]
            content  : dict.
                Response data.

            success  : bool.
                Response status.

            err_code : int.
                Error code.

            err_msg  : str. 
                Error message. Auto set value according by 'err_code' if 'err_msg' is not given.

            model_data : dict. 
                Data added during the Model, uesd to create response content for View.
        '''
        # data from model used for view.
        self.model_data = model_data if model_data else {}

        if not isinstance(success, bool):
            raise InternalError(code=ERR_RESPONSE_FORMAT, str_data=('success is not bool'))

        if not isinstance(err_code, int):
            raise InternalError(code=ERR_RESPONSE_FORMAT, str_data=('err_code is not int'))

        if not err_msg: # auto set err_msg
            err_msg = ERR_MSG.get(err_code, '')

        resp_formated_data = {
            'result':{
                'success': success,
                'err_code': err_code,
                'err_msg': err_msg
            }
        }

        if content and isinstance(content, dict):
            resp_formated_data.update(content)

        super(Response,self).__init__(**resp_formated_data)

