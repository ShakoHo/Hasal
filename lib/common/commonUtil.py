import os
import re
import time
import copy
import json
import platform
import subprocess
import numpy as np
from environment import Environment
from logConfig import get_logger
from datetime import datetime
logger = get_logger(__name__)


class StatusRecorder(object):
    """
    output sample 2017/05/22
    {
      "case_info": {
        "case_time_stamp": "20170522144114",                       <= test case time stamp will renew when call loop_test func of runtest.py
        "case_name": "test_firefox_gdoc_ail_pagedown_10_text"      <= current test case name
      },
      "current_status": {
        "sikuli_running_stat": "0",                                <= return code of self.sikuli.run_test
        "status_img_compare_result": "PASS_IMG_COMPARE_RESULT",    <= image compare result define in record_runtime_current_status of baseGenerator.py, will record the corresponse status according to the running time
        "time_list_counter": "6",                                  <= current executed times
        "fps_stat": 0,                                             <= current fps valdiation result (0: pass)
        "validator_result": {
          "validate_result": true,
          "FileExistValidator": {
            "output_result": null,
            "validate_result": true
          },
          "FPSValidator": {
            "output_result": 60,
            "validate_result": true
          }
        }
      },
      "case_status_history": {
        "test_firefox_gdoc_ail_pagedown_10_text": {
          "20170522144114": {
            "RUNNING_STATUS": "PASS_IMG_COMPARE_RESULT",
            "TOTAL_EXEC_TIME": 106.55035996437073
          }
        }
      }
    }
    """
    # Result for STATUS_IMG_COMPARE_RESULT
    PASS_IMG_COMPARE_RESULT = "PASS_IMG_COMPARE_RESULT"

    ERROR_EVENT_IMAGE_LESS_THAN_2 = "ERROR_EVENT_IMAGE_LESS_THAN_2"
    ERROR_EVENT_IMAGE_BOTH_SAME = "ERROR_EVENT_IMAGE_BOTH_SAME"
    ERROR_EVENT_IMAGE_START_AFTER_END = "ERROR_EVENT_IMAGE_START_AFTER_END"
    ERROR_MISSING_FIELD_IMG_COMPARE_RESULT = "ERROR_MISSING_FIELD_IMG_COMPARE_RESULT"
    ERROR_CANT_FIND_STATUS_FILE = "ERROR_CANT_FIND_STATUS_FILE"
    ERROR_FPS_STAT_ABNORMAL = "ERROR_FPS_STAT_ABNORMAL"
    ERROR_ROUND_STAT_ABNORMAL = "ERROR_ROUND_STAT_ABNORMAL"
    ERROR_COMPARING_IMAGE_FAILED = "ERROR_COMPARING_IMAGE_FAILED"
    ERROR_LOOP_TEST_RAISE_EXCEPTION = "ERROR_LOOP_TEST_RAISE_EXCEPTION"
    ERROR_COMPARE_RESULT_IS_NONE = "ERROR_COMPARE_RESULT_IS_NONE"

    STATUS_IMG_COMPARE_RESULT = "status_img_compare_result"
    STATUS_SIKULI_RUNNING_VALIDATION = "sikuli_running_stat"
    STATUS_FPS_VALIDATION = "fps_stat"
    STATUS_TIME_LIST_COUNTER = "time_list_counter"
    STATUS_VALIDATOR_RESULT = "validator_result"

    DEFAULT_FIELD_CASE_NAME = "case_name"
    DEFAULT_FIELD_CASE_TIME_STAMP = "case_time_stamp"

    STATUS_FPS_VALIDATION_NORMAL = 0
    STATUS_FPS_VALIDATION_ABNORMAL = 1

    DEFAULT_FIELD_CURRENT_STATUS = "current_status"
    DEFAULT_FIELD_CASE_STATUS_HISTORY = "case_status_history"
    DEFAULT_FIELD_CASE_INFO = "case_info"

    STATUS_DESC_CASE_TOTAL_EXEC_TIME = "TOTAL_EXEC_TIME"
    STATUS_DESC_CASE_RUNNING_STATUS = "RUNNING_STATUS"

    SIKULI_KEY_REGION = 'region'
    SIKULI_KEY_REGION_OVERRIDE = 'region_override'

    def __init__(self, status_fp):
        self.status_fp = status_fp
        self.current_data = CommonUtil.load_json_file(status_fp)

    def get_current_status(self):
        return self.current_data[self.DEFAULT_FIELD_CURRENT_STATUS]

    def get_case_basic_info(self):
        return self.current_data[self.DEFAULT_FIELD_CASE_INFO]

    def set_case_basic_info(self, case_name):
        current_time_stamp = datetime.strftime(datetime.now(), '%Y%m%d%H%M%S')
        # reset case info, which contains case name and timestamp
        if self.DEFAULT_FIELD_CASE_INFO in self.current_data:
            self.current_data[self.DEFAULT_FIELD_CASE_INFO][self.DEFAULT_FIELD_CASE_NAME] = case_name
            self.current_data[self.DEFAULT_FIELD_CASE_INFO][self.DEFAULT_FIELD_CASE_TIME_STAMP] = current_time_stamp
        else:
            self.current_data[self.DEFAULT_FIELD_CASE_INFO] = {self.DEFAULT_FIELD_CASE_NAME: case_name, self.DEFAULT_FIELD_CASE_TIME_STAMP: current_time_stamp}
        # dump to file
        with open(self.status_fp, "w+") as fh:
            json.dump(self.current_data, fh)
        # re-load data
        self.current_data = CommonUtil.load_json_file(self.status_fp)

    def clean_legacy_status(self):
        # reset current status
        if self.DEFAULT_FIELD_CURRENT_STATUS in self.current_data:
            self.current_data[self.DEFAULT_FIELD_CURRENT_STATUS] = {}
        # dump to file
        with open(self.status_fp, "w+") as fh:
            json.dump(self.current_data, fh)
        # re-load data
        self.current_data = CommonUtil.load_json_file(self.status_fp)

    def get_current_sikuli_status(self):
        """
        Get the "sikuli" status from current status.
        @return: the status object of "current_status/sikuli".
        """
        # reference: "lib/sikuli.py"
        KEY_NAME_SIKULI = 'sikuli'
        return self.current_data.get(self.DEFAULT_FIELD_CURRENT_STATUS, {}).get(KEY_NAME_SIKULI, {})

    def record_current_status(self, input_status_dict):
        self.current_data = CommonUtil.load_json_file(self.status_fp)
        if self.DEFAULT_FIELD_CURRENT_STATUS in self.current_data:
            self.current_data[self.DEFAULT_FIELD_CURRENT_STATUS].update(input_status_dict)
        else:
            self.current_data[self.DEFAULT_FIELD_CURRENT_STATUS] = input_status_dict
        with open(self.status_fp, "w+") as fh:
            json.dump(self.current_data, fh)

    def create_current_case_status_history(self):
        self.current_data = CommonUtil.load_json_file(self.status_fp)
        current_case_time_stamp = self.current_data[self.DEFAULT_FIELD_CASE_INFO][self.DEFAULT_FIELD_CASE_TIME_STAMP]
        current_case_name = self.current_data[self.DEFAULT_FIELD_CASE_INFO][self.DEFAULT_FIELD_CASE_NAME]
        if self.DEFAULT_FIELD_CASE_STATUS_HISTORY in self.current_data:
            if current_case_name in self.current_data[self.DEFAULT_FIELD_CASE_STATUS_HISTORY]:
                if current_case_time_stamp not in self.current_data[self.DEFAULT_FIELD_CASE_STATUS_HISTORY][current_case_name]:
                    self.current_data[self.DEFAULT_FIELD_CASE_STATUS_HISTORY][current_case_name][current_case_time_stamp] = {}
            else:
                self.current_data[self.DEFAULT_FIELD_CASE_STATUS_HISTORY][current_case_name] = {current_case_time_stamp: {}}
        else:
            self.current_data[self.DEFAULT_FIELD_CASE_STATUS_HISTORY] = {current_case_name: {current_case_time_stamp: {}}}

    def record_case_status_history(self, status_desc, value=None):
        self.create_current_case_status_history()
        current_case_name = self.current_data[self.DEFAULT_FIELD_CASE_INFO][self.DEFAULT_FIELD_CASE_NAME]
        current_case_time_stamp = self.current_data[self.DEFAULT_FIELD_CASE_INFO][self.DEFAULT_FIELD_CASE_TIME_STAMP]
        self.current_data[self.DEFAULT_FIELD_CASE_STATUS_HISTORY][current_case_name][current_case_time_stamp][status_desc] = value
        with open(self.status_fp, "w+") as fh:
            json.dump(self.current_data, fh)

    def record_case_exec_time_history(self, status_desc):
        self.create_current_case_status_history()
        current_case_name = self.current_data[self.DEFAULT_FIELD_CASE_INFO][self.DEFAULT_FIELD_CASE_NAME]
        current_case_time_stamp = self.current_data[self.DEFAULT_FIELD_CASE_INFO][self.DEFAULT_FIELD_CASE_TIME_STAMP]
        if status_desc in self.current_data[self.DEFAULT_FIELD_CASE_STATUS_HISTORY][current_case_name][current_case_time_stamp]:
            self.current_data[self.DEFAULT_FIELD_CASE_STATUS_HISTORY][current_case_name][current_case_time_stamp][status_desc] = time.time() - self.current_data[self.DEFAULT_FIELD_CASE_STATUS_HISTORY][current_case_name][current_case_time_stamp][status_desc]
        else:
            self.current_data[self.DEFAULT_FIELD_CASE_STATUS_HISTORY][current_case_name][current_case_time_stamp][status_desc] = time.time()
        with open(self.status_fp, "w+") as fh:
            json.dump(self.current_data, fh)


class CalculationUtil(object):

    @staticmethod
    def Q_MooreMcCabe(seq):
        seq_len = len(seq)
        if seq_len % 2:
            if (seq_len + 1) % 4:
                Q1 = float((seq[(seq_len + 1) / 4] + seq[(seq_len + 1) / 4 - 1])) / 2
            else:
                Q1 = float(seq[(seq_len + 1) / 4 - 1])
            if (3 * seq_len + 3) % 4:
                Q3 = float((seq[(3 * seq_len + 3) / 4] + seq[(3 * seq_len + 3) / 4 - 1])) / 2
            else:
                Q3 = float(seq[(3 * seq_len + 3) / 4 - 1])
        else:
            if (seq_len + 2) % 4:
                Q1 = float((seq[(seq_len + 2) / 4] + seq[(seq_len + 2) / 4 - 1])) / 2
            else:
                Q1 = float(seq[(seq_len + 2) / 4 - 1])
            if (3 * seq_len + 2) % 4:
                Q3 = float((seq[(3 * seq_len + 2) / 4] + seq[(3 * seq_len + 2) / 4 - 1])) / 2
            else:
                Q3 = float(seq[(3 * seq_len + 2) / 4 - 1])
        return [Q1, Q3]

    @staticmethod
    def Q_Tukey(seq):
        seq_len = len(seq)
        if seq_len % 2:
            if (seq_len + 1) % 4:
                Q1 = float((seq[(seq_len + 3) / 4] + seq[(seq_len + 3) / 4 - 1])) / 2
            else:
                Q1 = float(seq[(seq_len + 3) / 4 - 1])
            if (3 * seq_len + 3) % 4:
                Q3 = float((seq[(3 * seq_len + 1) / 4] + seq[(3 * seq_len + 1) / 4 - 1])) / 2
            else:
                Q3 = float(seq[(3 * seq_len + 1) / 4 - 1])
        else:
            if (seq_len + 2) % 4:
                Q1 = float((seq[(seq_len + 2) / 4] + seq[(seq_len + 2) / 4 - 1])) / 2
            else:
                Q1 = float(seq[(seq_len + 2) / 4 - 1])
            if (3 * seq_len + 2) % 4:
                Q3 = float((seq[(3 * seq_len + 2) / 4] + seq[(3 * seq_len + 2) / 4 - 1])) / 2
            else:
                Q3 = float(seq[(3 * seq_len + 2) / 4 - 1])
        return [Q1, Q3]

    @staticmethod
    def Q_FreundPerles(seq):
        seq_len = len(seq)
        if seq_len % 2:
            if (seq_len + 1) % 4:
                Q1 = float((seq[(seq_len + 3) / 4] + seq[(seq_len + 3) / 4 - 1])) / 2
            else:
                Q1 = float(seq[(seq_len + 3) / 4 - 1])
            if (3 * seq_len + 3) % 4:
                Q3 = float((seq[(3 * seq_len + 1) / 4] + seq[(3 * seq_len + 1) / 4 - 1])) / 2
            else:
                Q3 = float(seq[(3 * seq_len + 1) / 4 - 1])
        else:
            if (seq_len + 2) % 4:
                Q1 = float((seq[(seq_len + 3) / 4] + seq[(seq_len + 3) / 4 - 1])) / 2
            else:
                Q1 = float(seq[(seq_len + 3) / 4 - 1])
            if (3 * seq_len + 2) % 4:
                Q3 = float((seq[(3 * seq_len + 1) / 4] + seq[(3 * seq_len + 1) / 4 - 1])) / 2
            else:
                Q3 = float(seq[(3 * seq_len + 1) / 4 - 1])
        return [Q1, Q3]

    @staticmethod
    def Q_Minitab(seq):
        seq_len = len(seq)
        if seq_len % 2:
            if (seq_len + 1) % 4:
                Q1 = float((seq[(seq_len + 1) / 4] + seq[(seq_len + 1) / 4 - 1])) / 2
            else:
                Q1 = float(seq[(seq_len + 1) / 4 - 1])
            if (3 * seq_len + 3) % 4:
                Q3 = float((seq[(3 * seq_len + 3) / 4] + seq[(3 * seq_len + 3) / 4 - 1])) / 2
            else:
                Q3 = float(seq[(3 * seq_len + 3) / 4 - 1])
        else:
            if (seq_len + 2) % 4:
                Q1 = float((seq[(seq_len + 1) / 4] + seq[(seq_len + 1) / 4 - 1])) / 2
            else:
                Q1 = float(seq[(seq_len + 1) / 4 - 1])
            if (3 * seq_len + 2) % 4:
                Q3 = float((seq[(3 * seq_len + 3) / 4] + seq[(3 * seq_len + 3) / 4 - 1])) / 2
            else:
                Q3 = float(seq[(3 * seq_len + 3) / 4 - 1])
        return [Q1, Q3]

    @staticmethod
    def drop_outlier_value(seq, outliers):
        for outlier in outliers:
            seq.remove(outlier)
        return seq

    @staticmethod
    def remove_outlier(input_list, key_name, method=1):
        outliers = []
        outliers_value = []
        sorted_list = sorted(input_list, key=lambda k: k[key_name])
        seq_value = [d[key_name] for d in sorted_list]
        if len(input_list) >= 3:
                # Default using Moore and McCabe method to calculate quartile value
                Q_Calculation = {
                    '1': CalculationUtil.Q_MooreMcCabe,
                    '2': CalculationUtil.Q_Tukey,
                    '3': CalculationUtil.Q_FreundPerles,
                    '4': CalculationUtil.Q_Minitab
                }
                [Q1, Q3] = Q_Calculation.setdefault(str(method), CalculationUtil.Q_MooreMcCabe)(seq_value)
                IQR = Q3 - Q1
                lower = Q1 - 1.5 * IQR
                upper = Q3 + 1.5 * IQR
                for data in sorted_list:
                    if data[key_name] < lower or data[key_name] > upper:
                        outliers.append(data)
                        outliers_value.append(data[key_name])
                sorted_list = CalculationUtil.drop_outlier_value(sorted_list, outliers)
        return sorted_list, outliers

    @staticmethod
    def get_median_avg_sigma_value(input_list, key_name):
        sorted_list = sorted(input_list, key=lambda k: k[key_name])
        seq_value = [d[key_name] for d in sorted_list]
        if len(sorted_list) == 0:
            median_time_index = 0
            mean = 0
            median = 0
            sigma = 0
            min = 0
            max = 0
        elif len(sorted_list) == 1:
            median_time_index = 0
            mean = float(sorted_list[median_time_index][key_name])
            median = float(sorted_list[median_time_index][key_name])
            sigma = 0
            min = seq_value[0]
            max = seq_value[0]
        else:
            if len(sorted_list) % 2:
                median_time_index = (len(input_list) - 1) / 2
                median = float(sorted_list[median_time_index][key_name])
                mean = np.mean(seq_value)
                sigma = np.std(seq_value)
            else:
                median_time_index = len(input_list) / 2 - 1
                median = float(sorted_list[median_time_index][key_name] + sorted_list[median_time_index + 1][key_name]) / 2
                mean = np.mean(seq_value)
                sigma = np.std(seq_value)
            min = seq_value[0]
            max = seq_value[-1]
        return sorted_list, median_time_index, median, mean, sigma, min, max

    @staticmethod
    def generate_statistics_value_for_server(input_list, enable_remove_outlier=True):
        if enable_remove_outlier:
            tmp_list, outliers = CalculationUtil.remove_outlier(input_list, 'run_time')
        else:
            outliers = []
            tmp_list = input_list
        sorted_list, median_time_index, median_value, mean_value, sigma_value, min_value, max_value = CalculationUtil.get_median_avg_sigma_value(tmp_list, 'run_time')
        if len(sorted_list) % 2:
            si_value = input_list[median_time_index]['si']
            psi_value = input_list[median_time_index]['psi']
        else:
            si_value = (input_list[median_time_index]['si'] + input_list[median_time_index + 1]['si']) / 2
            psi_value = (input_list[median_time_index]['psi'] + input_list[median_time_index + 1]['psi']) / 2
        return mean_value, median_value, sigma_value, tmp_list, outliers, si_value, psi_value


class CommonUtil(object):

    RECORDER_LIST = [Environment.PROFILER_FLAG_AVCONV, Environment.PROFILER_FLAG_OBS]
    logger = get_logger(__file__)

    @staticmethod
    def get_username():
        """
        Get current username.
        The UNIX platform will return the value of `pwd.getpwuid(os.getuid()).pw_name`.
        The Windows platform will return 'USERNAME' of environ, or default username `user`.
        @return: current username.
        """
        if platform.system().lower() == 'windows':
            username = os.environ.get('USERNAME')
            if not username:
                # default user name
                username = 'user'
        else:
            import pwd
            username = pwd.getpwuid(os.getuid()).pw_name
        return username

    @staticmethod
    def get_appdata_dir():
        """
        Get current user's AppData folder.

        Availability: Windows.
        @return: current user's AppData folder.
        """
        if platform.system().lower() == 'windows':
            appdata_path = os.environ.get('APPDATA')
            if not appdata_path:
                # default user APPDATA folder
                appdata_path = r'C:\Users\{username}\AppData\Roaming'.format(username=CommonUtil.get_username())
        else:
            logger.error('Doesn\'t support get APPDATA at platform {}.'.format(platform.system()))
            appdata_path = ''
        return appdata_path

    @staticmethod
    def get_user_dir():
        """
        Get current user's home folder.
        The UNIX platform will return the value of `pwd.getpwuid(os.getuid()).pw_dir`.
        The Windows platform will return 'USERPROFILE' of environ.
        @return: current user's home folder.
        """
        if platform.system().lower() == 'windows':
            user_dir = os.environ.get('USERPROFILE')
            if not user_dir:
                # default user dir
                user_dir = r'C:\Users\{username}'.format(username=CommonUtil.get_username())
        else:
            import pwd
            user_dir = pwd.getpwuid(os.getuid()).pw_dir
        return user_dir

    @staticmethod
    def execute_runipy_cmd(input_template_fp, output_ipynb_fp, **kwargs):
        default_runipy_cmd = 'runipy'
        ipynb_env = os.environ.copy()
        for variable_name in kwargs.keys():
            ipynb_env[variable_name] = str(kwargs[variable_name])
        cmd_list = [default_runipy_cmd, input_template_fp, output_ipynb_fp]
        return subprocess.call(cmd_list, env=ipynb_env)

    @staticmethod
    def get_mac_os_display_channel():
        if platform.system().lower() == "darwin":
            proc = subprocess.Popen(
                ['ffmpeg', '-f', 'avfoundation', '-list_devices', 'true', '-i', '""'],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            stdout = proc.stdout.read()
            if "Capture screen" in stdout:
                display_channel = stdout[stdout.index('Capture screen') - 3]
                if display_channel in [str(i) for i in range(10)]:
                    return display_channel
            return "1"
        else:
            return ":0.0"

    @staticmethod
    def load_json_string(input_string):
        try:
            json_object = json.loads(input_string)
        except ValueError:
            return {}
        return json_object

    @staticmethod
    def load_json_file(fp):
        if os.path.exists(fp):
            try:
                with open(fp) as fh:
                    json_obj = json.load(fh)
                return json_obj
            except Exception as e:
                print e
                return {}
        else:
            return {}

    @staticmethod
    def atoi(text):
        return int(text) if text.isdigit() else text

    @classmethod
    def natural_keys(cls, text):
        return [cls.atoi(c) for c in re.split('(\d+)', text)]

    @staticmethod
    def _find_recorder_stat(total_recorder_settings):
        recorder_name_list = []
        total_recorder_flags = dict((item, False) for item in CommonUtil.RECORDER_LIST)
        for k in total_recorder_flags.keys():
            v = total_recorder_settings.get(k, {})
            if v:
                is_enabled = v.get('enable', False)
                total_recorder_flags[k] = is_enabled
                if is_enabled:
                    recorder_name_list.append(k)
        CommonUtil.logger.debug('Enabled Recorders: {}'.format(recorder_name_list))
        return recorder_name_list, total_recorder_flags

    @staticmethod
    def is_video_recording(settings):
        """
        Checking the Video Recording settings.
        @return: True if there is one Recorder, False if there is no Recorder. Raise exception when there are multiple Recorders.
        """
        # TODO: load recorder settings from firefox_config now, it might be changed...
        total_recorder_settings = settings.get('extensions', {})

        recorder_name_list, total_recorder_flags = CommonUtil._find_recorder_stat(total_recorder_settings)

        recording_enable_amount = sum(map(bool, total_recorder_flags.values()))
        if recording_enable_amount == 0:
            CommonUtil.logger.info('No Recorder.')
            return False
        elif recording_enable_amount == 1:
            CommonUtil.logger.info('Enabled Recorder: {}'.format(recorder_name_list[0]))
            return True
        elif recording_enable_amount > 1:
            CommonUtil.logger.error('More than one Recorder.')
            raise Exception('More than one video recorders are enabled.\n{}'.format(total_recorder_flags))

    @staticmethod
    def is_validate_fps(settings):
        """
        Checking the FPS validation settings.
        @return: True if FPS validation is enabled, False if FPS validation is disabled
        """
        try:
            if CommonUtil.is_video_recording(settings):
                total_recorder_settings = settings.get('extensions', {})

                recorder_name_list, _ = CommonUtil._find_recorder_stat(total_recorder_settings)

                if len(recorder_name_list) == 1:
                    recorder_name = recorder_name_list[0]
                    recorder_setting = total_recorder_settings.get(recorder_name, {})
                    is_validate_fps = recorder_setting.get('validate-fps', False)
                    CommonUtil.logger.info('The validate-fps of {} Recorder: {}.'.format(recorder_name, is_validate_fps))
                    return is_validate_fps
                else:
                    return False
            else:
                return False
        except:
            return False

    @staticmethod
    def get_value_from_config(config, key):
        value = config.get(key)
        if value is None:
            logger.warn('There is no {key} in {config} config file (or the value is None).'.format(key=key,
                                                                                                   config=config))
        return value

    @staticmethod
    def update_json(input_data, filename, mode="r+"):
        with open(filename, mode) as fh:
            origin_data = json.load(fh)
            origin_data.update(input_data)
            fh.seek(0)
            fh.write(json.dumps(origin_data))

    @staticmethod
    def subprocess_checkoutput_wrapper(input_cmd_list, **kwargs):
        try:
            output = subprocess.check_output(input_cmd_list, **kwargs)
            return 0, output
        except subprocess.CalledProcessError as e:
            return e.returncode, e.message

    @staticmethod
    def deep_merge_dict(source_dict, destination_dict):
        """
        >>> a = { 'first' : { 'all_rows' : { 'pass' : 'dog', 'number' : '1' } } }
        >>> b = { 'first' : { 'all_rows' : { 'fail' : 'cat', 'number' : '5' } } }
        >>> merge(b, a) == { 'first' : { 'all_rows' : { 'pass' : 'dog', 'fail' : 'cat', 'number' : '5' } } }
        @param source_dict:
        @param destination_dict:
        @return:
        """
        for key, value in source_dict.items():
            if isinstance(value, dict):
                # get node or create one
                node = destination_dict.setdefault(key, {})
                CommonUtil.deep_merge_dict(value, node)
            else:
                destination_dict[key] = value
        return destination_dict


class HasalConfigUtil(object):

    @staticmethod
    # be careful to have "default" value for each and every platform in conf file, or it would raise exception.
    def extract_platform_dep_settings(config_value, current_platform_name, current_platform_ver):
        platform_dep_variables = {}
        # get current platform value or default value of it
        if current_platform_name in config_value:
            if current_platform_ver in config_value[current_platform_name]:
                platform_dep_variables = copy.deepcopy(
                    config_value[current_platform_name][current_platform_ver])
            elif 'default' in config_value[current_platform_name]:
                platform_dep_variables = copy.deepcopy(config_value[current_platform_name]['default'])

        # return {} if no matching system platform and no default value
        return platform_dep_variables

    @staticmethod
    def overwrite_platform_dep_settings_into_configs(selfObj, config_variable_name, config_value,
                                                     acceptable_config_list, current_platform_name,
                                                     current_platform_ver):
        if config_variable_name not in acceptable_config_list:
            raise Exception('Invalid configuration name {config_name}: {config_value}'
                            .format(config_name=config_variable_name, config_value=config_value))

        default_platform_dep_settings_key = "platform-dep-settings"
        if default_platform_dep_settings_key in config_value:
            # Load the index config's settings under "platform-dep-settings" base on platform
            platform_dep_variables = HasalConfigUtil.extract_platform_dep_settings(
                config_value[default_platform_dep_settings_key], current_platform_name, current_platform_ver)
            config_value.update(platform_dep_variables)
            config_value.pop(default_platform_dep_settings_key)

        if hasattr(selfObj, config_variable_name):
            # getattr is a way to get variable by reference and doesn't need to be set back
            new_config_value = getattr(selfObj, config_variable_name)
            new_config_value.update(config_value)
            setattr(selfObj, config_variable_name, new_config_value)
        else:
            setattr(selfObj, config_variable_name, config_value)

        return selfObj
