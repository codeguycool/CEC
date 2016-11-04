# -*-coding: utf-8 -*-
"""Python programming utilities.
"""


class NotSet:
    """ This class is used to check input args is given.
    """
    pass


class Singleton(type):
    """ The metaclass for Singleton pattern.
    """
    _instances = {}  # Collection of singleton objects.

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
