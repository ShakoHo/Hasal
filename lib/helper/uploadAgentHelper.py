import os
import json
import sys
import urllib
import urllib2
import platform
import desktopHelper
import videoHelper
from datetime import datetime
from ..common.pyDriveUtil import PyDriveUtil
from ..common.environment import Environment
from ..common.logConfig import get_logger

DEFAULT_BROWSER_TYPE_FIREFOX = Environment.DEFAULT_BROWSER_TYPE_FIREFOX
DEFAULT_BROWSER_TYPE_CHROME = Environment.DEFAULT_BROWSER_TYPE_CHROME
DEFAULT_UPLOAD_VIDEO_YAML_SETTING = "./mozhasalvideo.yaml"
DEFAULT_UPLOAD_VIDEO_MYCRED_TXT = "./mycreds_mozhasalvideo.txt"
DEFAULT_UPLOAD_FOLDER_URI = "0B6LePZQnd-uOMWpEVFN2NXVBTG8"
DEFAULT_CONVERT_VIDEO_RESOLUTION = "320x240"
DEFAULT_BUILD_RESULT_URL_FOR_JENKINS_DESC = "build_result_for_jenkins_desc.txt"
DEFAULT_UPLOAD_VIDEO_QUEUE_JSON = "upload_video_queue.json"
DEFAULT_UPLOAD_VIDEO_STATUS = ['INIT', 'VIDEO_CONVERTED', 'PYDRIVE_UPLOADED', 'SERVER_UPLOADED']

logger = get_logger(__name__)


class UploadAgent(object):

    def __init__(self, **kwargs):
        for variable_name in kwargs.keys():
            setattr(self, variable_name, kwargs[variable_name])

        # get default installation path's browser version
        self.current_browser_version = {
            DEFAULT_BROWSER_TYPE_FIREFOX: desktopHelper.get_browser_version(DEFAULT_BROWSER_TYPE_FIREFOX),
            DEFAULT_BROWSER_TYPE_CHROME: desktopHelper.get_browser_version(DEFAULT_BROWSER_TYPE_CHROME)}

        # init test target variable
        self.test_target = "%s_%s" % (DEFAULT_BROWSER_TYPE_FIREFOX, self.current_browser_version[DEFAULT_BROWSER_TYPE_FIREFOX])

        # convert test comment
        if self.test_comment == "<today>":
            self.test_comment_str = datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
        else:
            self.test_comment_str = self.test_comment.strip()
        logger.info('Current Test Comment: {c} (source: {sc})'.format(c=self.test_comment_str,
                                                                      sc=self.test_comment))

    def generate_url_str(self, api_root=None):
        url_format = "http://%s:%s/%s"
        if api_root is None:
            api_root = self.svr_config["project_name"]
        os_str = platform.system().strip() + "_" + platform.release().strip()
        path_str = "/".join([api_root, os_str, self.test_target, self.test_comment_str])
        logger.debug('URL path: {u}'.format(u=path_str))
        return url_format % (self.svr_config['svr_addr'], self.svr_config['svr_port'], path_str)

    def upload_register_data(self, input_suite_fp, test_type, perfherder_suite_name=None):
        # Sample data
        # hasal_perf_reg/os/target/comment
        # sampe output {'firefox':{'regression_gsheet':['test_firefox_gsheet_1000r_number_chars_deleteallcell']},
        #               'chrome': {'regression_gsheet':['test_chrome_gsheet_1000r_number_chars_deleteallcell']}}
        with open(input_suite_fp) as input_suite_fh:
            upload_data = {}
            for tmp_line in input_suite_fh.read().strip().splitlines():
                case_full_path = tmp_line.split(",")[0]
                if test_type == "pt":
                    tmp_list = case_full_path.split(os.sep)
                else:
                    tmp_list = case_full_path.split(".")
                browser_type = tmp_list[3].split("_")[1].lower()
                app_name = tmp_list[2].lower()
                t_type = tmp_list[1].lower()[:2]
                c_name = tmp_list[3].lower()
                if browser_type not in upload_data:
                    upload_data[browser_type] = {}
                if perfherder_suite_name:
                    suite_name = perfherder_suite_name
                else:
                    if app_name == "topsites":
                        suite_name = "topsites"
                    else:
                        suite_name = t_type + "_" + app_name
                if suite_name in upload_data[browser_type]:
                    upload_data[browser_type][suite_name].append(c_name)
                else:
                    upload_data[browser_type][suite_name] = [c_name]
            url_str = self.generate_url_str("hasal_perf_reg")
            logger.info("===== Upload register suite data =====")
            logger.debug(url_str)
            logger.info(upload_data)
            logger.info("===== Upload register suite data =====")
            self.send_post_data(upload_data, url_str)

    def upload_result(self, input_result_fp):
        if os.path.exists(input_result_fp):
            with open(input_result_fp) as json_fh:
                result_data = json.load(json_fh)
            if 'video-recording-fps' in result_data:
                result_data.pop('video-recording-fps')
            if len(result_data.keys()) != 1:
                logger.error("current result file consist over 1 test case result!")
                return None
            else:
                # init test data
                test_name = result_data.keys()[0]
                test_browser_type = test_name.split("_")[1]
                test_time_list = result_data[test_name]['time_list']
                test_video_fp = result_data[test_name]['video_fp']
                web_app_name = result_data[test_name]['web_app_name']
                revision = result_data[test_name]['revision']
                if result_data[test_name]['pkg_platform']:
                    pkg_platform = result_data[test_name]['pkg_platform']
                else:
                    pkg_platform = platform.machine()
                if len(test_time_list) != 1:
                    logger.error("current time list is not equal to 1, current: %d!" % len(test_time_list))
                    return None
                else:
                    test_value = test_time_list[0].get('run_time', 0)
                    si_value = test_time_list[0].get('si', 0)
                    psi_value = test_time_list[0].get('psi', 0)
                url_str = self.generate_url_str()

                # compose post data
                json_data = {"os": sys.platform,
                             "target": self.test_target,
                             "test": test_name,
                             "browser": test_browser_type,
                             "version": self.current_browser_version[test_browser_type],
                             "revision": revision,
                             "platform": pkg_platform,
                             "webappname": web_app_name,
                             "value": test_value,
                             "si": si_value,
                             "psi": psi_value,
                             "video": test_video_fp,
                             "comment": self.test_comment_str}

                # print post data
                logger.debug(self.current_browser_version)
                logger.info("===== Upload result post data =====")
                logger.info(json_data)
                logger.info("===== Upload result post data =====")
                r_data = self.send_post_data(json_data, url_str).read()
                logger.info('response object data : [%s]' % r_data)

                # write result link to physical file for jenkins
                with open(DEFAULT_BUILD_RESULT_URL_FOR_JENKINS_DESC, 'w') as write_fh:
                    write_str = "TestResult\t%s\t/userContent/result.png" % url_str
                    write_fh.write(write_str)
                return json.loads(r_data)
        else:
            logger.error("Can't find the result file, ignore upload result!")
            return None

    def send_post_data(self, post_data, url_str):
        query_args = {}
        # compose query and send request
        json_data_str = json.dumps(post_data)
        query_args['json'] = json_data_str
        encoded_args = urllib.urlencode(query_args)
        try:
            response_obj = urllib2.urlopen(url_str, encoded_args)
        except Exception as e:
            logger.error("Send post data failed, error message [%s]" % e.message)
            return None
        if response_obj.getcode() == 200:
            return response_obj
        else:
            logger.error("response status code is [%d]" % response_obj.getcode())
            return None

    def upload_videos(self, input_upload_data):

        # load previous upload video queue data
        upload_video_queue_fp = os.path.join(os.getcwd(), DEFAULT_UPLOAD_VIDEO_QUEUE_JSON)
        if os.path.exists(upload_video_queue_fp):
            with open(upload_video_queue_fp) as read_fh:
                upload_video_queue = json.load(read_fh)
        else:
            upload_video_queue = []

        # init pydrive object
        pyDriveObj = PyDriveUtil(settings={"settings_file": DEFAULT_UPLOAD_VIDEO_YAML_SETTING,
                                           "local_cred_file": DEFAULT_UPLOAD_VIDEO_MYCRED_TXT})

        # check the key value, and converting the video to small size
        if input_upload_data['video_path'] and os.path.exists(input_upload_data['video_path']):
            # init current data variable
            new_video_path = input_upload_data['video_path'].replace(".mkv", ".mp4")
            upload_video_data = {'video_fp': new_video_path, 'input_data': input_upload_data, 'video_preview_url': None,
                                 'status': DEFAULT_UPLOAD_VIDEO_STATUS[0]}
            # add to current video queue
            if upload_video_data not in upload_video_queue:
                upload_video_queue.insert(0, upload_video_data)
        else:
            logger.info("No upload video action need to follow, due the current input upload data is [%s]" % input_upload_data)

        for upload_data in upload_video_queue:
            # clean up upload data with no-existing video file
            if not os.path.exists(upload_data['input_data']['video_path']):
                logger.info(
                    "Converting video source file not exist, remove the data [%s]!" % upload_data)
                upload_video_queue.remove(upload_data)
                continue

            if not os.path.exists(upload_data['video_fp']) and (upload_data['status'] == DEFAULT_UPLOAD_VIDEO_STATUS[1] or upload_data['status'] == DEFAULT_UPLOAD_VIDEO_STATUS[3]):
                logger.info("Converted video file not exist, remove the data [%s]!" % upload_data)
                upload_video_queue.remove(upload_data)
                continue

            # converting video
            if upload_data['status'] == DEFAULT_UPLOAD_VIDEO_STATUS[0]:
                videoHelper.convert_video_to_specify_size(upload_data['input_data']['video_path'], new_video_path,
                                                          DEFAULT_CONVERT_VIDEO_RESOLUTION)
                if os.path.exists(new_video_path):
                    upload_data['status'] = DEFAULT_UPLOAD_VIDEO_STATUS[1]
                    logger.info("Converting video success! The converted video path: [%s]" % new_video_path)
                else:
                    logger.error(
                        "Converted video file[%s] not exist, something could be wrong during converting!" % new_video_path)

            # upload to pydrive
            if upload_data['status'] == DEFAULT_UPLOAD_VIDEO_STATUS[1]:
                upload_result = pyDriveObj.upload_file(DEFAULT_UPLOAD_FOLDER_URI, upload_data['video_fp'])
                if upload_result:
                    upload_data['status'] = DEFAULT_UPLOAD_VIDEO_STATUS[2]
                    upload_data['video_preview_url'] = "/".join(upload_result['alternateLink'].split("/")[:-1]) + "/preview"
                else:
                    logger.error("Upload video file to google drive failed, skip the video file upload to server!")

            # upload to server
            if upload_data['status'] == DEFAULT_UPLOAD_VIDEO_STATUS[2]:
                test_browser_type = upload_data['input_data']['test_name'].split("_")[1]
                json_data = {"os": sys.platform, "target": self.test_target, "test": upload_data['input_data']['test_name'],
                             "browser": test_browser_type, "version": self.current_browser_version[test_browser_type],
                             "video_path": upload_data['video_preview_url'], "comment": self.test_comment_str}
                url_str = self.generate_url_str("video_profile")
                logger.info("===== Upload video post data =====")
                logger.debug(url_str)
                logger.info(json_data)
                logger.info("===== Upload video post data =====")
                if self.send_post_data(json_data, url_str):
                    upload_data['status'] = DEFAULT_UPLOAD_VIDEO_STATUS[3]
                    logger.info("Upload video file success, upload data: [%s]" % upload_data)
                else:
                    logger.error("Upload video to server failed, upload data: [%s]" % upload_data)

            # remove from queue
            if upload_data['status'] == DEFAULT_UPLOAD_VIDEO_STATUS[3]:
                logger.info("Remove successful upload data: [%s]" % upload_data)
                upload_video_queue.remove(upload_data)

        # rewrite all the upload_video_queue to local json file
        with open(upload_video_queue_fp, 'w+') as write_fh:
            json.dump(upload_video_queue, write_fh)
