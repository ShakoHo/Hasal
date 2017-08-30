"""

Usage:
  get_build.py <repo> <platform> [--user-email=<str>] [--build-hash=<str>] [--no-status-check] [--output-dp=<str>]
  get_build.py (-h | --help)

Options:
  -h --help                 Show this screen.
  --build-hash=<str>        Specify the build want to retrieve.
  --user-email=<str>        Specify the user email of build want to retrieve
  --no-status-check         Skip job status check
  --output-dp=<str>         Specify the build download path [default: .]
"""
import re
import os
import urllib2
import requests
from thclient import TreeherderClient
from docopt import docopt
from tqdm import tqdm


class GetBuild(object):
    ARCHIVE_URL = "https://archive.mozilla.org"
    NIGHTLY_LATEST_URL_FOLDER = "/pub/firefox/nightly/latest-mozilla-central/"
    PLATFORM_FN_MAPPING = {'linux32': {'key': 'linux-i686', 'ext': 'tar.bz2', 'trydl': 'linux', 'job': ['linux32']},
                           'linux64': {'key': 'linux-x86_64', 'ext': 'tar.bz2', 'trydl': 'linux64', 'job': ['linux64']},
                           'mac': {'key': 'mac', 'ext': 'dmg', 'trydl': 'macosx64', 'job': ['osx']},
                           'win32': {'key': 'win32', 'ext': 'zip', 'trydl': 'win32', 'job': ['windows', '32']},
                           'win64': {'key': 'win64', 'ext': 'zip', 'trydl': 'win64', 'job': ['windows', '64']}}

    def __init__(self, repo, platform, status_check):
        self.repo = repo
        self.platform = platform
        self.platform_option = 'opt'
        self.pushes = []
        self.skip_status_check = status_check
        self.thclient = TreeherderClient()

    def fetch_push(self, user_email, build_hash, default_count=500):
        tmp_pushes = self.thclient.get_pushes(self.repo, count=default_count)
        for push in tmp_pushes:
            if push['author'].lower() == user_email.lower():
                self.pushes.append(push)
                if build_hash is None:
                    return push
                elif push['revision'] == build_hash:
                    return push
        print "Can't find the specify build hash [%s] in resultsets!!" % build_hash
        return None

    def get_job(self, resultset, platform_keyword_list):
        jobs = self.thclient.get_jobs(self.repo, result_set_id=resultset['id'])
        for job in jobs:
            cnt = 0
            for platform_keyword in platform_keyword_list:
                if platform_keyword in job['platform']:
                    cnt += 1
            if job['platform_option'] == self.platform_option and cnt == len(platform_keyword_list):
                return job
        print "Can't find the specify platform [%s] and platform_options [%s] in jobs!!!" % (self.platform, self.platform_option)
        return None

    def get_files_from_remote_url_folder(self, remote_url_str):
        return_dict = {}
        try:
            response_obj = urllib2.urlopen(remote_url_str)
            if response_obj.getcode() == 200:
                for line in response_obj.readlines():
                    match = re.search(r'(?<=href=").*?(?=")', line)
                    if match:
                        href_link = match.group(0)
                        f_name = href_link.split("/")[-1]
                        return_dict[f_name] = href_link
            else:
                print "ERROR: fetch remote file list error with code [%s]" % str(response_obj.getcode())
        except Exception as e:
            print "ERROR: [%s]" % e.message
        return return_dict

    def download_file(self, output_dp, download_link):
        print "Prepare to download the build from link [%s]" % download_link
        response = requests.get(download_link, verify=False, stream=True)
        download_fn = download_link.split("/")[-1]
        if os.path.exists(output_dp) is False:
            os.makedirs(output_dp)
        download_fp = os.path.join(output_dp, download_fn)
        try:
            try:
                total_len = int(response.headers['content-length'])
            except:
                total_len = None
            with open(download_fp, 'wb') as fh:
                for data in tqdm(response.iter_content(chunk_size=512 * 1024), total=total_len / (512 * 1024)):
                    fh.write(data)
            return download_fp
        except Exception as e:
            print "ERROR: [%s]" % e.message
            return None

    def download_from_remote_url_folder(self, remote_url_str, output_dp):
        # get latest nightly build list from remote url folder
        remote_file_dict = self.get_files_from_remote_url_folder(remote_url_str)

        # filter with platform, and return file name with extension
        if len(remote_file_dict.keys()) == 0:
            print "ERROR: can't get remote file list, could be the network error, or url path[%s] wrong!!" % remote_url_str
            return False
        else:
            if self.platform not in self.PLATFORM_FN_MAPPING:
                print "ERROR: we are currently not support the platform[%s] you specified!" % self.platform
                print "We are currently support the platform tag: [%s]" % self.PLATFORM_FN_MAPPING.keys()
                return False
            else:
                matched_keyword = self.PLATFORM_FN_MAPPING[self.platform]['key'] + "." + self.PLATFORM_FN_MAPPING[self.platform]['ext']
                matched_file_list = [fn for fn in remote_file_dict.keys() if matched_keyword in fn and "firefox" in fn]
                if len(matched_file_list) != 1:
                    print "WARN: the possible match file list is not equal 1, list as below: [%s]" % matched_file_list
                    if len(matched_file_list) < 1:
                        return False
                    matched_file_list = sorted(matched_file_list)[-1:]
                    print "WARN: select following file [%s]" % matched_file_list

        # combine file name with json
        matched_file_name = matched_file_list[0]
        json_file_name = matched_file_name.replace(
            self.PLATFORM_FN_MAPPING[self.platform]['key'] + "." + self.PLATFORM_FN_MAPPING[self.platform]['ext'],
            self.PLATFORM_FN_MAPPING[self.platform]['key'] + ".json")
        if json_file_name not in remote_file_dict:
            print "ERROR: can't find the json file[%s] in remote file list[%s]!" % (json_file_name, remote_file_dict)
            return False
        else:
            print "DEBUG: matched file name: [%s], json_file_name: [%s]" % (matched_file_name, json_file_name)

        # download files
        download_fx_url = self.ARCHIVE_URL + remote_file_dict[matched_file_name]
        download_fx_fp = self.download_file(output_dp, download_fx_url)
        download_json_url = self.ARCHIVE_URL + remote_file_dict[json_file_name]
        download_json_fp = self.download_file(output_dp, download_json_url)

        # check download status
        if download_fx_fp and download_json_fp:
            print "SUCCESS: build files download in [%s], [%s] " % (download_fx_fp, download_json_fp)
            return True
        else:
            print "ERROR: build files download in [%s,%s] " % (download_fx_fp, download_json_fp)
            return False

    def get_try_build(self, user_email, build_hash, output_dp):
        resultset = self.fetch_push(user_email, build_hash)

        # check result set
        if resultset:
            # if build hash is not porvided, use the latest revision as build hash value
            if build_hash is None:
                build_hash = resultset['revision']
            print "Resultset is found, and build hash is [%s]" % build_hash

            # compose remote folder url
            build_folder_url_template = "%s/pub/firefox/%s-builds/%s-%s/%s-%s/"
            build_folder_url = build_folder_url_template % (self.ARCHIVE_URL,
                                                            self.repo, user_email, build_hash,
                                                            self.repo,
                                                            self.PLATFORM_FN_MAPPING[self.platform][
                                                                'trydl'])

            # skip status check will retrieve the files list from remote folder url
            if self.skip_status_check:
                return self.download_from_remote_url_folder(build_folder_url, output_dp)
            else:
                job = self.get_job(resultset, self.PLATFORM_FN_MAPPING[self.platform]['job'])
                if job:
                    if job['result'].lower() == "success":
                        return self.download_from_remote_url_folder(build_folder_url, output_dp)
                    else:
                        "Current job status is [%s] !!" % job['result'].lower()
                        return False
                else:
                    print "ERROR: can't find the job!"
                    return False
        else:
            print "ERROR: can't get result set! skip download build from try server, [%s, %s]" % (user_email, build_hash)
            return False

    def get_nightly_build(self, output_dp):
        remote_url_str = self.ARCHIVE_URL + self.NIGHTLY_LATEST_URL_FOLDER
        return self.download_from_remote_url_folder(remote_url_str, output_dp)


def main():
    arguments = docopt(__doc__)
    get_build_obj = GetBuild(arguments['<repo>'], arguments['<platform>'], arguments['--no-status-check'])
    if arguments['<repo>'] == "nightly":
        return get_build_obj.get_nightly_build(arguments['--output-dp'])
    elif arguments['<repo>'] == "try":
        if arguments['--user-email']:
            return get_build_obj.get_try_build(arguments['--user-email'], arguments['--build-hash'], arguments['--output-dp'])
        else:
            print "ERROR: please specify the user email with --user-email argument!"
            return False
    else:
        print "ERROR: we are currently not support the repo[%s] you specified! currently support [nightly, try]" % arguments['<repo>']
        return False

if __name__ == '__main__':
    main()
