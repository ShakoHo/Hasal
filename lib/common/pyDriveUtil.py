import os
import argparse
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from argparse import ArgumentDefaultsHelpFormatter
from logConfig import get_logger

logger = get_logger(__name__)


class PyDriveUtil(object):

    KEY_MIME_TYPE = 'mimeType'
    FOLDER_MIME_TYPE = 'application/vnd.google-apps.folder'

    def __init__(self, settings=None):
        if settings is None:
            settings = {"settings_file": None, "local_cred_file": "mycreds.txt"}
        if os.path.exists(settings['local_cred_file']):
            gauth = self.get_gauth(settings)
            self.drive = GoogleDrive(gauth)
        else:
            raise Exception(
                "Your current working dir doesn't include the client certificate file [%s]. Please make sure firefox/chrome profile creation is turned off, online mode is disabled, and GSuite and FB cases are not test targets!" % settings['local_cred_file'])

    def get_file_object(self, folder_uri, file_name):
        file_list = self.get_file_list(folder_uri=folder_uri)
        for file_obj in file_list:
            if file_name in file_obj['title']:
                return file_obj
        return None

    def get_file_list(self, folder_uri):
        search_string = "'%s' in parents and trashed=false" % folder_uri
        return self.drive.ListFile({'q': search_string}).GetList()

    def create_folder_object(self, parent_folder_uri, folder_name):
        ret_obj = self.get_file_object(folder_uri=parent_folder_uri, file_name=folder_name)

        # already has the folder
        if ret_obj and ret_obj.get(self.KEY_MIME_TYPE) == self.FOLDER_MIME_TYPE:
            return ret_obj
        else:
            folder_metadata = {
                'title': folder_name,
                'parents': [{'id': parent_folder_uri}],
                'mimeType': 'application/vnd.google-apps.folder'}
            file_obj = self.drive.CreateFile(folder_metadata)
            file_obj.Upload()
            return file_obj

    def update_file_content(self, folder_uri, file_name, content):
        file_obj = self.get_file_object(folder_uri, file_name)
        file_obj.SetContentString(content)
        file_obj.Upload()

    def get_gauth(self, settings):
        if settings['settings_file']:
            gauth = GoogleAuth(settings_file=settings['settings_file'])
        else:
            gauth = GoogleAuth()
        # Try to load saved client credentials
        gauth.LoadCredentialsFile(settings['local_cred_file'])
        if gauth.credentials is None:
            # Authenticate if they're not there
            gauth.LocalWebserverAuth()
        elif gauth.access_token_expired:
            # Refresh them if expired
            gauth.Refresh()

        # Initialize the saved creds
        gauth.Authorize()
        # Save the current credentials to a file
        gauth.SaveCredentialsFile(settings['local_cred_file'])
        return gauth

    def copy_file(self, file_id, folder_uri, new_title):
        return self.drive.auth.service.files().copy(fileId=file_id,
                                                    body={"parents": [{"kind": "drive#fileLink", "id": folder_uri}],
                                                          'title': new_title}).execute()

    def delete_file(self, file_id):
        self.drive.auth.service.files().delete(fileId=file_id).execute()

    def upload_file(self, folder_uri, upload_fp):
        try:
            file_obj = self.drive.CreateFile({"parents": [{"kind": "drive#fileLink", "id": folder_uri}]})
            file_obj.SetContentFile(upload_fp)
            file_obj.Upload()
            return file_obj
        except Exception as e:
            logger.error("Exception happened during PyDrive upload video file!")
            logger.error(e.message)
            return None


def main():
    arg_parser = argparse.ArgumentParser(description='Pydrive util',
                                         formatter_class=ArgumentDefaultsHelpFormatter)
    arg_parser.add_argument('input_folder_uri', default=None, help='Specify the uri path of folder.')
    arg_parser.add_argument('input_file_name', default=None, help='Specify file name your want to update.')
    arg_parser.add_argument('input_content', default=None, help='Specify content want to update.')
    arg_parser.add_argument('-s', action='store', dest='input_settings_file', default=None,
                            help='Specify the settings file using in getting auth')
    arg_parser.add_argument('-l', action='store', dest='input_local_cred_file', default=None,
                            help='Specify the local cred file using in getting auth')
    args = arg_parser.parse_args()

    folder_uri = args.input_folder_uri
    file_name = args.input_file_name
    content = args.input_content

    if args.input_settings_file and args.input_local_cred_file:
        pydrive_obj = PyDriveUtil(
            settings={"settings_file": args.input_settings_file, "local_cred_file": args.input_local_cred_file})
    elif args.input_settings_file is None and args.input_local_cred_file is None:
        pydrive_obj = PyDriveUtil()
    else:
        logger.error("pleas specify the -s and -l at same time!")
    pydrive_obj.update_file_content(folder_uri, file_name, content)

if __name__ == '__main__':
    main()
