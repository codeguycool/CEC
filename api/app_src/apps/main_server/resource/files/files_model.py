"""Model class
"""

# std
import hashlib
import os
from datetime import datetime

# 3rd party
from psycopg2 import Binary

# app module
from framework.common_tools import response_json_out, streaming_generator
from framework.db_client.pg_client import PGClient
from framework.err import ERR_DB_NOT_FOUND, ERR_REQUEST_ARG, RequestError
from framework.response import Response
from lib.app_const import FILE_CACHE_PATH, TMP_PATH
from lib.app_var import MAX_NUM_ADDONS


class FilesModel:

    def get_addon(self, url, params, request, response):
        """ Get addon file.

        [Arguments]
            url[0] : string.
                Addon version.
        """
        # API args
        if len(url):
            version = url[0]
        else:
            raise RequestError(ERR_REQUEST_ARG, str_data=('version error.'))

        # Compose cache file path
        file_name = 'CEC_%s.addon' % version
        cache_file_path = '%s/%s' % (FILE_CACHE_PATH, file_name)

        path_to_save = None  # Save file if this file does not cached.
        
        # Get file
        if os.path.isfile(cache_file_path):  # Take cached file if it found.
            iter_data = open(cache_file_path)
        else:  # get file and cache it
            db_inst = PGClient(db='file', timeout=False)
            addons, rowcount = db_inst.query(
                table='addons', condition=[u'version=%(version)s', {'version': version}], ret_type='all'
            )
            if not rowcount:
                raise RequestError(ERR_DB_NOT_FOUND)

            iter_data = iter(addons[0]['data'])  # covert it to iter obj for avoiding multiple use.
            path_to_save = cache_file_path

        response.stream = True
        response.headers['Content-Type'] = 'application/octet-stream'
        response.headers['Content-Disposition'] = 'attachment; filename="%s"' % file_name

        return streaming_generator(iter_data=iter_data, file_name=path_to_save)

    @response_json_out
    def get_addon_version(self, url, params, request, response):
        """ Get addon version.
        """
        # API args
        version = url[0] if len(url) else None

        db_inst = PGClient(db='file')
        if version:
            addons, rowcount = db_inst.query(
                table='addons', fields=['version', 'md5sum'],
                condition=[u'version=%(version)s', {'version': version}], ret_type='all'
            )
        else:  # latest version
            addons, rowcount = db_inst.query(
                table='addons', fields=['version', 'md5sum'], ret_type='all', else_sql='ORDER BY version DESC LIMIT 1'
            )

        if not rowcount:
            raise RequestError(ERR_DB_NOT_FOUND)

        return Response({
            'version': addons[0]['version'],
            'md5sum': addons[0]['md5sum']
        })

    @response_json_out
    def upload_addon(self, url, params, request, response):
        """ Upload addon file.

        [Arguments]
            url[0] : string.
                Addon version of this file.
            md5sum : string. (opt)
                md5sum of this file to check data is complete.
        """
        # API args
        if len(url):
            version = url[0]
        else:
            raise RequestError(ERR_REQUEST_ARG, str_data=('version error.'))

        if not params.has_key('file'):
            raise RequestError(ERR_REQUEST_ARG, str_data=('file error.'))

        file_md5sum = params.get_string('md5sum', None)

        # check data exist
        db_inst = PGClient(db='file', timeout=False)
        cur, rowcount = db_inst.query(
            table='addons', fields=['version'], condition=[u'version=%(version)s', {'version': version}]
        )
        if rowcount:
            raise RequestError(ERR_REQUEST_ARG, str_data=('data existed.'))

        # handle updating file
        upload_file = params['file']
        tmp_file_path = '%s/%s' % (TMP_PATH, upload_file.filename)

        try:
            # save file
            md5 = hashlib.md5()
            with open(tmp_file_path, mode='wb') as fp:
                while True:
                    data = upload_file.file.read(8192)
                    if data:
                        fp.write(data)
                        md5.update(data)
                    else:
                        break

            # compare md5sum
            md5sum = md5.hexdigest()
            if file_md5sum and md5sum != file_md5sum:
                raise RequestError(ERR_REQUEST_ARG, str_data=('md5sum check error.'))

            # insert data to db
            with open(tmp_file_path, mode='rb') as f:
                db_inst.insert(table='addons', data={
                    'version': version,
                    'name': upload_file.filename,
                    'data': Binary(f.read()),
                    'md5sum': md5sum,
                    'udate': datetime.utcnow().isoformat()
                })

            # remove redundant data
            addons, rowcount = db_inst.query(
                table='addons', fields=['version'], ret_type='all', else_sql='ORDER BY version DESC'
            )
            if rowcount > MAX_NUM_ADDONS:
                versions_to_remove = [addons[-1*index]['version'] for index in xrange(1, rowcount-MAX_NUM_ADDONS+1)]
                db_inst.remove(
                    table='addons', condition=['version IN %(versions)s', {'versions': tuple(versions_to_remove)}]
                )

            db_inst.commit()

            return Response({
                'version': version,
                'md5sum': md5sum
            })
        finally:
            os.remove(tmp_file_path)

    @response_json_out
    def delete_addon(self, url, params, request, response):
        """ delete addon file.

        [Arguments]
            url[0] : string.
                Addon version of file to remove.
        """
        # API args
        if len(url):
            version = url[0]
        else:
            raise RequestError(ERR_REQUEST_ARG, str_data=('version error.'))

        db_inst = PGClient(db='file', timeout=False)
        # check data exist
        cur, rowcount = db_inst.query(
            table='addons', fields=['version'], condition=[u'version=%(version)s', {'version': version}]
        )
        if not rowcount:
            raise RequestError(ERR_REQUEST_ARG, str_data=('data does not exist.'))

        db_inst.remove(table='addons', condition=[u'version=%(version)s', {'version': version}])
        db_inst.commit()

        return Response({
            'version': version
        })
