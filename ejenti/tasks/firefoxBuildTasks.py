import os
import re
import sys
import json
import shutil
import urllib2
import platform
import requests
import logging
import tarfile
import zipfile
from tqdm import tqdm
from baseTasks import init_task
from baseTasks import parse_cmd_parameters

ARCHIVE_URL = "https://archive.mozilla.org"
NIGHTLY_LATEST_URL_FOLDER = "/pub/firefox/nightly/latest-mozilla-central/"
PLATFORM_FN_MAPPING = {'linux32': {'key': 'linux-i686', 'ext': 'tar.bz2', 'trydl': 'linux', 'job': ['linux32']},
                       'linux64': {'key': 'linux-x86_64', 'ext': 'tar.bz2', 'trydl': 'linux64', 'job': ['linux64']},
                       'mac': {'key': 'mac', 'ext': 'dmg', 'trydl': 'macosx64', 'job': ['osx']},
                       'win32': {'key': 'win32', 'ext': 'zip', 'trydl': 'win32', 'job': ['windows', '32']},
                       'win64': {'key': 'win64', 'ext': 'zip', 'trydl': 'win64', 'job': ['windows', '64']}}
FIREFOX_BIN_LINUX_FP = "/usr/bin/firefox"
FIREFOX_BIN_WIN_FP = "C:\\Program Files (x86)\\Mozilla Firefox"
FIREFOX_BIN_MAC_FP = "/Applications/Firefox.app"


def download_file(output_dp, download_link):
    logging.info("Prepare to download the build from link [%s]" % download_link)
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
        logging.error("ERROR: [%s]" % e.message)
        return None


def get_files_from_remote_url_folder(remote_url_str):
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
            logging.error("fetch remote file list error with code [%s]" % str(response_obj.getcode()))
    except Exception as e:
        logging.error("ERROR: [%s]" % e.message)
    return return_dict


def download_from_remote_url_folder(dl_pkg_platform, remote_url_str, output_dp):
    """
    get latest nightly build list from remote url folder
    @param dl_pkg_platform: linux64/mac/win64
    @param remote_url_str: https://archive...etc.
    @param output_dp: output directory path
    @return: True: success, False exception happened
    """
    remote_file_dict = get_files_from_remote_url_folder(remote_url_str)

    # filter with platform, and return file name with extension
    if len(remote_file_dict.keys()) == 0:
        logging.error("can't get remote file list, could be the network error, or url path[%s] wrong!!" % remote_url_str)
        return False
    else:
        if dl_pkg_platform not in PLATFORM_FN_MAPPING:
            logging.error("we are currently not support the platform[%s] you specified!" % dl_pkg_platform)
            logging.error("We are currently support the platform tag: [%s]" % PLATFORM_FN_MAPPING.keys())
            return False
        else:
            matched_keyword = PLATFORM_FN_MAPPING[dl_pkg_platform]['key'] + "." + PLATFORM_FN_MAPPING[dl_pkg_platform]['ext']
            matched_file_list = [fn for fn in remote_file_dict.keys()
                                 if ((matched_keyword in fn) and ('firefox' in fn) and (not fn.endswith('.asc')))]
            if len(matched_file_list) != 1:
                logging.warn("the possible match file list is not equal 1, list as below: [%s]" % matched_file_list)
                if len(matched_file_list) < 1:
                    return False
                matched_file_list = sorted(matched_file_list)[-1:]
                logging.warn("select following file [%s]" % matched_file_list)

    # combine file name with json
    matched_file_name = matched_file_list[0]
    json_file_name = matched_file_name.replace(
        PLATFORM_FN_MAPPING[dl_pkg_platform]['key'] + "." + PLATFORM_FN_MAPPING[dl_pkg_platform]['ext'],
        PLATFORM_FN_MAPPING[dl_pkg_platform]['key'] + ".json")
    if json_file_name not in remote_file_dict:
        logging.error("can't find the json file[%s] in remote file list[%s]!" % (json_file_name, remote_file_dict))
        return False
    else:
        logging.debug("matched file name: [%s], json_file_name: [%s]" % (matched_file_name, json_file_name))

    # download files
    download_fx_url = ARCHIVE_URL + remote_file_dict[matched_file_name]
    download_fx_fp = download_file(output_dp, download_fx_url)
    download_json_url = ARCHIVE_URL + remote_file_dict[json_file_name]
    download_json_fp = download_file(output_dp, download_json_url)

    # check download status
    if download_fx_fp and download_json_fp:
        logging.info("SUCCESS: build files download in [%s], [%s] " % (download_fx_fp, download_json_fp))
        return (download_fx_fp, download_json_fp)
    else:
        logging.error("build files download in [%s,%s] " % (download_fx_fp, download_json_fp))
        return None


def download_latest_nightly_build(**kwargs):
    """
    you can specify output_dp in task configs or after the cmd
    @param kwargs:

        kwargs['cmd_obj']['configs']['DOWNLOAD_PKG_OUTPUT_DP'] :: the path where your downloaded firefox package want to store, default: current dir

    @return: json obj
    """

    # get queue msg, consumer config from kwargs
    queue_msg, consumer_config, task_config = init_task(kwargs)

    # init return result
    return_result = {}

    # init download url
    remote_url_str = ARCHIVE_URL + NIGHTLY_LATEST_URL_FOLDER

    # init platform value
    if sys.platform == "linux2":
        dl_pkg_platform = "linux64"
    elif sys.platform == "darwin":
        dl_pkg_platform = "mac"
    else:
        dl_pkg_platform = "win64"

    # get output dir path from kwargs
    cmd_parameter_list = parse_cmd_parameters(queue_msg)
    if len(cmd_parameter_list) == 2:
        output_dp = cmd_parameter_list[1]
    else:
        output_dp = task_config.get("DOWNLOAD_PKG_OUTPUT_DP", os.getcwd())
    return_result['output_dp'] = output_dp

    # get download fx package local path and json path
    download_fx_fp, download_json_fp = download_from_remote_url_folder(dl_pkg_platform, remote_url_str, output_dp)
    return_result['FX-DL-PACKAGE-PATH'] = download_fx_fp
    return_result['FX-DL-JSON-PATH'] = download_json_fp

    if download_fx_fp is None or download_json_fp is None:
        logging.error("something wrong with your build download process, please check the setting and job status.")
        return return_result
    else:
        current_platform_release = platform.release().strip()

        # parse downloaded fx pkg json file
        with open(download_json_fp) as dl_json_fh:
            dl_json_data = json.load(dl_json_fh)
            perfherder_revision = dl_json_data['moz_source_stamp']
            build_pkg_platform = dl_json_data['moz_pkg_platform']
            # mapping the perfherder pkg platform to nomenclature of builddot
            builddot_mapping_platform = {"linux-i686": {"_": "linux32"},
                                         "linux-x86_64": {"_": "linux64"},
                                         "mac": {"_": "osx-10-10"},
                                         "win32": {"_": "windows7-32"},
                                         "win64": {"_": "windows8-64",
                                                   "7": "windows8-64",
                                                   "10": "windows10-64"}
                                         }

            return_result['PERFHERDER-REVISION'] = perfherder_revision
            if current_platform_release in builddot_mapping_platform[build_pkg_platform].keys():
                return_result['PERFHERDER-PKG-PLATFORM'] = builddot_mapping_platform[build_pkg_platform][
                    current_platform_release]
            else:
                return_result['PERFHERDER-PKG-PLATFORM'] = builddot_mapping_platform[build_pkg_platform]["_"]

        return return_result


def link_fx_pkg():
        if sys.platform == "linux2":
            firefox_fp = FIREFOX_BIN_LINUX_FP
        elif sys.platform == "win32":
            firefox_fp = FIREFOX_BIN_WIN_FP
        else:
            firefox_fp = FIREFOX_BIN_MAC_FP
        # Create and check backup
        # Move default firefox to backup folder, and we want to always keep one copy of default firefox package,
        # so we won't always replace the backup one.
        backup_path = firefox_fp + ".bak"
        if os.path.exists(backup_path):
            if os.path.exists(firefox_fp):
                if sys.platform == "linux2":
                    os.remove(firefox_fp)
                else:
                    shutil.rmtree(firefox_fp)
        else:
            if os.path.exists(firefox_fp):
                os.rename(firefox_fp, backup_path)

        if sys.platform == "linux2":
            src_link = os.path.join(os.getcwd(), "firefox", "firefox")
            os.symlink(src_link, FIREFOX_BIN_LINUX_FP)
        elif sys.platform == "darwin":
            DEFAULT_NIGHLTY_ATTACTED_PATH = "/Volumes/Nightly"
            if os.path.exists(DEFAULT_NIGHLTY_ATTACTED_PATH):
                shutil.copytree(os.path.join(DEFAULT_NIGHLTY_ATTACTED_PATH, "FirefoxNightly.app"), FIREFOX_BIN_MAC_FP)
                detach_cmd_format = "hdiutil detach %s"
                detach_cmd_str = detach_cmd_format % DEFAULT_NIGHLTY_ATTACTED_PATH
                if os.system(detach_cmd_str) != 0:
                    logging.error("detach dmg file[%s] failed! cmd string: [%s]" % (DEFAULT_NIGHLTY_ATTACTED_PATH, detach_cmd_str))
            else:
                logging.error("can't find the nightly attached path [%s]" % DEFAULT_NIGHLTY_ATTACTED_PATH)
        else:
            src_path = os.path.join(os.getcwd(), "firefox")
            os.rename(src_path, FIREFOX_BIN_WIN_FP)


def extract_fx_pkg(input_fx_pkg_fp, input_fx_extract_dir="firefox"):
    if os.path.exists(input_fx_extract_dir):
        shutil.rmtree(input_fx_extract_dir)
    if input_fx_pkg_fp.endswith(".tar.bz2"):
        target_file = tarfile.open(input_fx_pkg_fp, "r:bz2")
        target_file.extractall()
        target_file.close()
    elif input_fx_pkg_fp.endswith(".zip"):
        target_file = zipfile.ZipFile(input_fx_pkg_fp, "r")
        target_file.extractall()
        target_file.close()
    else:
        attach_cmd_format = "hdiutil attach -noautoopen -quiet %s"
        attach_cmd_str = attach_cmd_format % input_fx_pkg_fp
        if os.system(attach_cmd_str) != 0:
            logging.error("attach dmg file[%s] failed! cmd string: [%s]" % (input_fx_pkg_fp, attach_cmd_str))
            return False
        else:
            logging.info("attach dmg file[%s] sucessfully!" % input_fx_pkg_fp)
    return True


def deploy_fx_package(**kwargs):
    """
    deploy firefox package to system default path
    @param kwargs:

        kwargs['cmd_obj']['configs']['INPUT_FX_DL_PKG_PATH'] :: the firefox package path your want to deploy to system default path

    @return:
    """

    # get queue msg, consumer config from kwargs
    queue_msg, consumer_config, task_config = init_task(kwargs)

    # get fx pkg path
    cmd_parameter_list = parse_cmd_parameters(queue_msg)
    if len(cmd_parameter_list) == 2:
        fx_dl_pkg_path = cmd_parameter_list[1]
    else:
        fx_dl_pkg_path = task_config.get("INPUT_FX_DL_PKG_PATH", None)

    if fx_dl_pkg_path:
        if extract_fx_pkg(fx_dl_pkg_path):
            link_fx_pkg()
            return True
        else:
            logging.error("cannot extract firefox package [%s]" % fx_dl_pkg_path)
    else:
        logging.warn("please specify firefox downloaded package path after cmd")
    return False
