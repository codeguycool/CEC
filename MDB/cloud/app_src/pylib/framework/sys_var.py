# -*-coding: utf-8 -*-
"""System variables.
"""
from sys_const import LOG_DEBUG


# API support method
ALLOW_HTTP_METHOD = ['COPY', 'DELETE', 'GET', 'HEAD', 'LINK', 'OPTIONS', 'PATCH', 'POST', 'PURGE', 'PUT', 'UNLINK']


# Database setting
DB_NAME="mdb"
DB_USER="postgres"
DB_PASSWORD="postgres"
DB_HOST="localhost"
DB_PORT="9999"


# CherryPy log setting
LOG_LEVEL = LOG_DEBUG #Default level is DEBUG
