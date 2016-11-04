# -*- coding: utf-8 -*-

# 3rd
import psycopg2

# project
from conf.settings import (
    IMDB_DB_NAME, IMDB_DB_HOST, IMDB_DB_ACCOUNT, IMDB_DB_PASSWORD,
    LMDB_DB_NAME, LMDB_DB_HOST, LMDB_DB_ACCOUNT, LMDB_DB_PASSWORD, LMDB_DB_SCHEMA,
    LSDB_DB_NAME, LSDB_DB_HOST, LSDB_DB_ACCOUNT, LSDB_DB_PASSWORD, LSDB_DB_SCHEMA,
    LADB_DB_NAME, LADB_DB_HOST, LADB_DB_ACCOUNT, LADB_DB_PASSWORD, LADB_DB_SCHEMA
)


def create_database(host, dbname, account, passwd):
    conn = psycopg2.connect(host=host, user=account)
    conn.autocommit = True
    cur = conn.cursor()

    try:
        cur.execute("Create Database %s;" % dbname)
    except psycopg2.ProgrammingError as e:
        print e.message

    cur.close()
    conn.close()


def init_database(host, dbname, account, passwd, schema_path):
    conn = psycopg2.connect(host=host, user=account, database=dbname)
    conn.autocommit = True
    cur = conn.cursor()
    try:
        cur.execute(open(schema_path, mode='r').read())
    except psycopg2.ProgrammingError as e:
        print e.message
    cur.close()
    conn.close()

if __name__ == '__main__':
    # create db
    create_database(IMDB_DB_HOST, IMDB_DB_NAME, IMDB_DB_ACCOUNT, IMDB_DB_PASSWORD)
    create_database(LMDB_DB_HOST, LMDB_DB_NAME, LMDB_DB_ACCOUNT, LMDB_DB_PASSWORD)
    create_database(LSDB_DB_HOST, LSDB_DB_NAME, LSDB_DB_ACCOUNT, LSDB_DB_PASSWORD)
    create_database(LADB_DB_HOST, LADB_DB_NAME, LADB_DB_ACCOUNT, LADB_DB_PASSWORD)

    # init db
    init_database(LMDB_DB_HOST, LMDB_DB_NAME, LMDB_DB_ACCOUNT, LMDB_DB_PASSWORD, LMDB_DB_SCHEMA)
    init_database(LSDB_DB_HOST, LSDB_DB_NAME, LSDB_DB_ACCOUNT, LSDB_DB_PASSWORD, LSDB_DB_SCHEMA)
    init_database(LADB_DB_HOST, LADB_DB_NAME, LADB_DB_ACCOUNT, LADB_DB_PASSWORD, LADB_DB_SCHEMA)
