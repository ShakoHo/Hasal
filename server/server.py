"""
1. run `python server/server.py <IP_ADDRESS>:<PORT>` for normal usage.
2. run `CONFIG_PATH=<PATH_TO_CONFIG_FOLDER> python server/server.py <IP_ADDRESS>:<PORT>` for specify config settings.`
"""

import os
import re
import web
import json
import time
from datetime import datetime
import random
import shutil
import logging
from logging import handlers  # NOQA
import operator
import urlparse
from threading import Lock
from lib.common.commonUtil import CalculationUtil
from perfherder_uploader import PerfherderUploader


ENV_CONFIG_PATH = os.environ.get('CONFIG_PATH', '~/.hasal_server/')


def geometric_mean(iterable):
    filtered = list(filter(lambda x: x > 0, iterable))
    return (reduce(operator.mul, filtered)) ** (1.0 / len(filtered))


def get_logger(logger_name, log_level="info"):
    inner_logger = logging.getLogger(logger_name)
    if log_level == "debug":
        inner_logger.setLevel(logging.DEBUG)
    else:
        inner_logger.setLevel(logging.INFO)
    if len(inner_logger.handlers) == 0:
        console_handler = logging.StreamHandler()
        file_handler = logging.handlers.RotatingFileHandler('{}.log'.format(logger_name), 'a', 10 * 1024 * 1024, 5)
        format_string = "[%(asctime)s] %(filename)s:%(lineno)d(%(funcName)s): [%(levelname)s] %(message)s"
        format_object = logging.Formatter(format_string)
        file_handler.setFormatter(format_object)
        inner_logger.addHandler(console_handler)
        inner_logger.addHandler(file_handler)
    return inner_logger

logger_hasal = get_logger("HasalServer", "info")
pub_register_mutex = Lock()

urls = (
    '/', 'Index',
    '/all_result/', 'AllResult',
    '/hasal/(.*)/(.*)/(.*)', 'HasalServer',
    '/hasal_perf_reg/(.*)/(.*)/(.*)', 'HasalServerPerfherderRegister',
    '/video_profile/(.*)/(.*)/(.*)', 'VideoProfileUpdater'
)


class Formater:

    @staticmethod
    def timestamp_to_date_string(timestamp):
        # For Javascript, 'var d = new Date(timestamp * 1000)' can work.
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')


class StorageHandler:
    """
    Please add the 'config.json' file under '~/.hasal_server/'.
    The file content example:
        {"test_times": 30}
    If there is no config file, the default value will be 30 times.
    """
    _storage_mutex = Lock()
    _storage_dir = os.path.expanduser(ENV_CONFIG_PATH)
    _storage_path = os.path.join(_storage_dir, 'dump.json')
    _config_path = os.path.join(_storage_dir, 'config.json')
    _register_mutex = Lock()
    _register_path = os.path.join(_storage_dir, 'register.json')

    def __init__(self):
        if not os.path.exists(self._storage_dir):
            os.makedirs(self._storage_dir)

    def load_config(self):
        """
        Return the config from config.json of '~/.hasal_server/'
        :return: The config json. ex: {"test_times": 30}
        """
        DEFAULT_CONFIG = {
            "test_times": 30,
            "perfherder_protocol": "http",
            "perfherder_host": "local.treeherder.mozilla.org",
            "perfherder_client_id": "",
            "perfherder_secret": "",
            "perfherder_repo": "mozilla-central",
            "dashboard_host": "",
            "dashboard_ssh": ""
        }
        logger_hasal.info('Loading config file from {} ...'.format(self._config_path))
        if os.path.isfile(self._config_path):
            with open(self._config_path, 'r') as f:
                ret_obj = json.load(f)
                test_times = ret_obj.get('test_times', '')
                perf_protocol = ret_obj.get('perfherder_protocol', '')
                perf_host = ret_obj.get('perfherder_host', '')
                perf_repo = ret_obj.get('perfherder_repo', '')
                if test_times:
                    logger_hasal.info('Test Times: {}'.format(test_times))
                if perf_protocol:
                    logger_hasal.info('Perfherder Protocol: {}'.format(perf_protocol))
                if perf_host:
                    logger_hasal.info('Perfherder Host: {}'.format(perf_host))
                if perf_repo:
                    logger_hasal.info('Perfherder Repo: {}'.format(perf_repo))
                return ret_obj
        else:
            with open(self._config_path, 'w') as f:
                f.write(json.dumps(DEFAULT_CONFIG))
                logger_hasal.info('No config.json file {}. Generate default config.'.format(self._config_path))
        return DEFAULT_CONFIG

    def load_register(self):
        """
        Return the info from dump.json from '~/.hasal_server/'
        :return: json if file exists, or {}
        """
        if os.path.isfile(self._register_path):
            try:
                with open(self._register_path, 'r') as f:
                    return json.load(f)
            except:
                seed = random.random()
                logger_hasal.info('### Seed {} acquire! [StorageHandler.load_register]'.format(seed))
                StorageHandler._register_mutex.acquire()
                data = {}
                with open(self._register_path, 'r') as f:
                    try:
                        data = json.load(f)
                    finally:
                        StorageHandler._register_mutex.release()
                        logger_hasal.info('### Seed {} release! [StorageHandler.load_register]'.format(seed))
                return data
        return {}

    def save_register(self, json_obj):
        seed = random.random()
        logger_hasal.info('### Seed {} acquire! [StorageHandler.save_register]'.format(seed))
        StorageHandler._register_mutex.acquire()
        try:
            if not os.path.exists(self._storage_dir):
                os.makedirs(self._storage_dir)
            if os.path.isdir(self._register_path):
                shutil.rmtree(self._register_path)
            with open(self._register_path, 'w') as f:
                json.dump(json_obj, f)
        except Exception as e:
            logger_hasal.error(e)
        finally:
            StorageHandler._register_mutex.release()
            logger_hasal.info('### Seed {} release! [StorageHandler.save_register]'.format(seed))

    def load(self):
        """
        Return the info from dump.json from '~/.hasal_server/'
        :return: json if file exists, or {}
        """
        if os.path.isfile(self._storage_path):
            try:
                with open(self._storage_path, 'r') as f:
                    return json.load(f)
            except:
                seed = random.random()
                logger_hasal.info('### Seed {} acquire! [StorageHandler.load]'.format(seed))
                StorageHandler._storage_mutex.acquire()
                data = {}
                with open(self._storage_path, 'r') as f:
                    try:
                        data = json.load(f)
                    finally:
                        StorageHandler._storage_mutex.release()
                        logger_hasal.info('### Seed {} release! [StorageHandler.load]'.format(seed))
                return data
        return {}

    def save(self, json_obj):
        seed = random.random()
        logger_hasal.info('### Seed {} acquire! [StorageHandler.save]'.format(seed))
        StorageHandler._storage_mutex.acquire()
        try:
            if not os.path.exists(self._storage_dir):
                os.makedirs(self._storage_dir)
            if os.path.isdir(self._storage_path):
                shutil.rmtree(self._storage_path)
            with open(self._storage_path, 'w') as f:
                json.dump(json_obj, f)
        except Exception as e:
            logger_hasal.error(e)
        finally:
            StorageHandler._storage_mutex.release()
            logger_hasal.info('### Seed {} release! [StorageHandler.save]'.format(seed))

    def remove(self):
        if os.path.isdir(self._storage_path):
            shutil.rmtree(self._storage_path)
        elif os.path.isfile(self._storage_path):
            os.remove(self._storage_path)


class AllResult:
    render = web.template.render('templates', base='layout')

    def __init__(self):
        HasalServer.storage = HasalServer.storage_handler.load()

    def GET(self):
        md = []

        for os_name in HasalServer.storage.keys():
            md.append('# {}'.format(os_name))

            targets = HasalServer.storage[os_name]
            for target in targets.keys():
                md.append('## {}'.format(target))

                comments = HasalServer.storage[os_name][target]
                for comment in comments.keys():
                    md.append('### {}'.format(comment))

                    tests = HasalServer.storage[os_name][target][comment]
                    for test in sorted(tests.keys(), key=lambda k: re.sub(r'test_[\w]+_', '', k)):
                        md.append('#### {}'.format(test))

                        browsers = HasalServer.storage[os_name][target][comment][test]
                        for browser in browsers.keys():
                            if len(browsers) > 1:
                                md.append('  * {}'.format(browser))
                            data = browsers[browser]
                            if data.get('revision', '') != '':
                                md.append('    * Revision: {}'.format(data.get('revision')))
                            md.append('    * Median: {}'.format(data.get('median_value')))
                            md.append('    * Sigma: {}'.format(data.get('sigma_value')))
                            md.append('    * Mean: {}'.format(data.get('median_value')))
                            md.append('    * SI: {}'.format(data.get('si')))
                            md.append('    * PSI: {}'.format(data.get('psi')))
                            if data.get('webappname', '') != '':
                                md.append('    * Web App: {}'.format(data.get('webappname')))
                            if data.get('video_path', '') != '':
                                md.append('    * Video: {}'.format(data.get('video_path')))
                            if data.get('profile_path', '') != '':
                                md.append('    * Profile: {}'.format(data.get('profile_path')))
                            md.append('\n')
        markdown_str = '\n'.join(md)
        return self.render.all_result(markdown=markdown_str)


class HasalServerPerfherderRegister:
    """
    Hasal Server Register.
    """
    RET_FAIL = -1
    RET_OK = 0
    RET_DROP = 1

    storage_handler = StorageHandler()
    register = {}

    def __init__(self):
        HasalServerPerfherderRegister.register = HasalServerPerfherderRegister.storage_handler.load_register()

    def gen_result_status(self, status, message=""):
        return {'status': status, 'message': message}

    def save_register(self):
        HasalServerPerfherderRegister.storage_handler.save_register(HasalServerPerfherderRegister.register)

    def POST(self, os_name, target, comment):
        """
        The input json example:
            URL: hasal_perf_reg/ darwin/firefox_47.0/2016-10-13
            json=
            {
                "firefox": {
                    "regression_gsheet": [
                        "test_firefox_gsheet_1000r_number_chars_deleteallcell"
                    ]
                },
                "chrome": {
                    "regression_gsheet": [
                        "test_chrome_gsheet_1000r_number_chars_deleteallcell"
                    ]
                }
            }
        It will convert to following entries:
            {
                "darwin": {
                    "firefox_47.0": {
                        "2016-10-13": {
                            "firefox": {
                                "regression_gsheet": [
                                    "test_firefox_gsheet_1000r_number_chars_deleteallcell"
                                ]
                            },
                            "chrome": {
                                "regression_gsheet": [
                                    "test_chrome_gsheet_1000r_number_chars_deleteallcell"
                                ]
                            }
                        }
                    }
                }
            }
        :param os_name: os. ex: 'linux'
        :param target: target. ex: 'firefox 36'
        :param comment: comment. ex: '2016-01-01'
        :return: status. 0 is okay. 1 is drop. -1 is fail.
            ex:
            {
                "firefox": {
                    "status": 0
                },
                "chrome": {
                    "status": 0
                }
            }
        """
        try:
            # check the url, server/hasal_perf_reg/<os>/<target_browser>/<comment>
            assert os_name is not None and os_name.strip() != '', '[os] is empty.'
            assert target is not None and target.strip() != '', '[target] is empty.'
            assert comment is not None and comment.strip() != '', '[comment] is empty.'
            os_name = os_name.strip()
            target = target.strip()
            comment = comment.strip()

            # get the POST data
            data = web.data()
            parameters = urlparse.parse_qs(data)
            # check the POST data contain 'json'
            assert 'json' in parameters, 'Can not get "json" parameter from POST data.'

            # check the input json object
            json_obj = json.loads(parameters['json'][0])

            if not isinstance(json_obj, dict):
                raise Exception('The parameter is not JSON object: {}'.format(parameters['json'][0]))

            result_dict = {}
            for browser_name, suite_obj in json_obj.items():
                if not isinstance(suite_obj, dict):
                    result_dict[browser_name] = self.gen_result_status(self.RET_FAIL,
                                                                       'The value under "{}" is not JSON object: {}'.format(
                                                                           browser_name, suite_obj))

                for suite_name, suite_tests_list in suite_obj.items():
                    if not isinstance(suite_tests_list, list):
                        result_dict[browser_name] = self.gen_result_status(self.RET_FAIL,
                                                                           'The value under "{}" is not list: {}'.format(
                                                                               suite_name, suite_tests_list))

                    try:
                        seed = random.random()
                        logger_hasal.info('### Seed {} acquire! [HasalServerPerfherderRegister.POST]'.format(seed))
                        pub_register_mutex.acquire()
                        HasalServerPerfherderRegister.register = HasalServerPerfherderRegister.storage_handler.load_register()

                        if os_name not in HasalServerPerfherderRegister.register:
                            HasalServerPerfherderRegister.register[os_name] = {}
                        if target not in HasalServerPerfherderRegister.register[os_name]:
                            HasalServerPerfherderRegister.register[os_name][target] = {}
                        if comment not in HasalServerPerfherderRegister.register[os_name][target]:
                            HasalServerPerfherderRegister.register[os_name][target][comment] = {}
                        if browser_name not in HasalServerPerfherderRegister.register[os_name][target][comment]:
                            HasalServerPerfherderRegister.register[os_name][target][comment][browser_name] = {}

                        if suite_name not in HasalServerPerfherderRegister.register[os_name][target][comment][browser_name]:
                            HasalServerPerfherderRegister.register[os_name][target][comment][browser_name][suite_name] = suite_tests_list
                            self.save_register()
                            result_dict[browser_name] = self.gen_result_status(self.RET_OK)
                        else:
                            # if there is already value in "os_name/target/comment", drop it and return status 1
                            result_dict[browser_name] = self.gen_result_status(self.RET_DROP)
                    finally:
                        pub_register_mutex.release()
                        logger_hasal.info('### Seed {} release! [HasalServerPerfherderRegister.POST]'.format(seed))
            return result_dict
        except AssertionError as e:
            raise web.badrequest(e.message)


class HasalServer:
    """
    Hasal Server handler.
    """
    storage_handler = StorageHandler()
    storage = {}
    perfherder_mode = False

    _config = storage_handler.load_config()
    _config_test_times = _config.get('test_times', 30)
    _config_perfherder_protocol = _config.get('perfherder_protocol', 'http')
    _config_perfherder_host = _config.get('perfherder_host', 'local.treeherder.mozilla.org')
    _config_perfherder_client_id = _config.get('perfherder_client_id', '')
    _config_perfherder_secret = _config.get('perfherder_secret', '')
    _config_perfherder_repo = _config.get('perfherder_repo', 'mozilla-central')
    _config_dashboard_host = _config.get('dashboard_host', '')
    _config_dashboard_ssh = _config.get('dashboard_ssh', '')
    _config_dashboard_link = _config.get('dashboard_link', 'https://askeing.github.io/hasal-dashboard/')

    _keys = ['os', 'target_browser', 'test', 'browser']
    # The "value" is "run_time" from agent, the "si", "psi", and "revision" are optional.
    _checks = ['os', 'target', 'test', 'comment', 'webappname', 'browser', 'version', 'platform', 'value', 'video']
    _count = 0
    _template = {
        'os': '',
        'target': '',
        'test': '',
        'comment': '',
        'webappname': '',
        'browser': '',
        'version': '',
        'revision': '',
        'platform': '',
        'median_value': -1,
        'mean_value': -1,
        'sigma_value': -1,
        'si': -1,
        'psi': -1,
        'origin_values': [],  # the list of (value, video, ip)
        'video_path': '',
        'profile_path': '',
        'timestamp': 0,
    }

    def __init__(self):
        HasalServer.storage = HasalServer.storage_handler.load()
        if HasalServer._config_perfherder_client_id and HasalServer._config_perfherder_secret:
            logger_hasal.info('[Perfherder] The "Client ID" and "Secret" of Perfherder are ready ...')
            HasalServer.perfherder_mode = True
        else:
            logger_hasal.info('[Perfherder] There are no "Client ID" and "Secret" of Perfherder ...')
            HasalServer.perfherder_mode = False

    @staticmethod
    def check_input_json(json_obj):
        for item in HasalServer._checks:
            assert item in json_obj, 'The json should have "{}" value.'.format(item)

    @staticmethod
    def remove_tuple_from_values(list_obj, removed_values_list):
        """
        :param list_obj: [ [run_time, si, psi, video, ip], [...], ...]
        :param removed_values_list: [ {"run_time": 0, "si": 0, "psi": 0}, {...}, ...]
        :return: list after remove items
        """
        tmp = list_obj[:]
        for v in removed_values_list:
            tmp = [item for item in tmp if item[0] != v.get('run_time')]
        return tmp

    @staticmethod
    def find_video_ip_by_median(list_obj, median):
        index = min([item[0] for item in list_obj], key=lambda x: abs(x - median))
        return [item for item in list_obj if index in item][0]

    @staticmethod
    def _generate_current_test_obj(json_obj, ip):
        # "si", "psi", and "revision" are optional
        info = HasalServer._template.copy()
        info['os'] = json_obj.get('os')
        info['target'] = json_obj.get('target')
        info['test'] = json_obj.get('test')
        info['comment'] = json_obj.get('comment')
        info['webappname'] = json_obj.get('webappname')
        info['browser'] = json_obj.get('browser')
        info['version'] = json_obj.get('version')
        info['revision'] = json_obj.get('revision', '')
        info['platform'] = json_obj.get('platform')
        info['origin_values'] = []  # TODO, add new value into it
        info['origin_values'].append([json_obj.get('value'), json_obj.get('si', -1), json_obj.get('psi', -1), json_obj.get('video'), ip])
        return info

    @staticmethod
    def return_json(current_test_obj):
        HasalServer.storage_handler.save(HasalServer.storage)

        values_list = current_test_obj['origin_values']
        median_value = current_test_obj['median_value']
        mean_value = current_test_obj['mean_value']
        sigma_value = current_test_obj['sigma_value']
        timestamp = current_test_obj['timestamp']
        datestring = Formater.timestamp_to_date_string(timestamp) if timestamp else ''

        _, _, _, video, ip = HasalServer.find_video_ip_by_median(values_list, median_value)

        ret = {
            'median_value': median_value,
            'mean_value': mean_value,
            'sigma_value': sigma_value,
            'current_test_times': len(values_list),
            'video': video,
            'ip': ip,
            'config_test_times': HasalServer._config_test_times,
            'timestamp': timestamp,
            'date': datestring
        }
        return json.dumps(ret)

    @staticmethod
    def update_dashboard():
        # TODO update dashboard by SSH deployment key
        # logger_hasal.info('[Dashboard] starting update to dashboard ...')
        pass

    @staticmethod
    def update_perfherder():
        # TODO update Perfherder
        if not HasalServer.perfherder_mode:
            logger_hasal.info('### Skip Perfherder ###')
            return

        try:
            seed = random.random()
            logger_hasal.info('### Seed {} acquire! [HasalServer.update_perfherder]'.format(seed))
            pub_register_mutex.acquire()
            date_result = HasalServer.storage_handler.load()
            data_register = HasalServer.storage_handler.load_register()
            # check if there are all tests in suite have the result (median vaule large than 0), then prepare uploading to perfherder

            for os_name in data_register:
                for target_name in data_register[os_name]:
                    for comment_name in data_register[os_name][target_name]:
                        for browser_name in data_register[os_name][target_name][comment_name]:
                            for suite_name in data_register[os_name][target_name][comment_name][browser_name]:
                                perf_data_suites = []

                                suite = data_register[os_name][target_name][comment_name][browser_name][suite_name]
                                perf_data_suite_median = {
                                    'name': '{} Median'.format(suite_name),
                                    'value': 0,
                                    'extraOptions': [browser_name],
                                    'subtests': []
                                }
                                perf_data_suite_si = {
                                    'name': '{} SI'.format(suite_name),
                                    'value': 0,
                                    'extraOptions': [browser_name],
                                    'subtests': []
                                }
                                perf_data_suite_psi = {
                                    'name': '{} PSI'.format(suite_name),
                                    'value': 0,
                                    'extraOptions': [browser_name],
                                    'subtests': []
                                }

                                test_result = {}
                                video_links = {}
                                start_timestamp = time.time()
                                for test_name in suite:
                                    testname_without_browser = test_name.split('_', 2)[-1]
                                    test_result = date_result.get(os_name, {}).get(target_name, {}).get(comment_name, {}).get(test_name, {}).get(browser_name, {})

                                    if test_result.get('timestamp') > 0:
                                        start_timestamp = min(start_timestamp, test_result.get('timestamp'))

                                    median = test_result.get('median_value', -1)
                                    si = test_result.get('si', -1)
                                    psi = test_result.get('psi', -1)
                                    if median > 0 and test_result.get('video_path'):
                                        perf_data_suite_median['subtests'].append({
                                            'name': testname_without_browser,
                                            'value': median
                                        })
                                    if si > 0 and test_result.get('video_path'):
                                        perf_data_suite_si['subtests'].append({
                                            'name': testname_without_browser,
                                            'value': si
                                        })
                                    if psi > 0 and test_result.get('video_path'):
                                        perf_data_suite_psi['subtests'].append({
                                            'name': testname_without_browser,
                                            'value': psi
                                        })
                                    if test_result.get('video_path'):
                                        video_links[testname_without_browser] = test_result.get('video_path')

                                # if the suite tests and the median result number are the same, that means the suite is finished.
                                for perf_suite in [perf_data_suite_median, perf_data_suite_si, perf_data_suite_psi]:
                                    if len(suite) > 0 and len(suite) == len(perf_suite['subtests']):
                                        perf_suite['value'] = geometric_mean([item.get('value') for item in perf_suite['subtests']])
                                        perf_data_suites.append(perf_suite)
                                if len(perf_data_suites) > 0:
                                    # Prepare
                                    link = '{}?os={}&target={}&comment={}'.format(HasalServer._config_dashboard_link,
                                                                                  os_name,
                                                                                  target_name,
                                                                                  comment_name)

                                    info_browser_type = browser_name
                                    info_browser_link = ''
                                    if info_browser_type.lower() == 'firefox':
                                        info_browser_link = 'http://hg.mozilla.org/mozilla-central/rev/{}'.format(test_result.get('revision'))
                                    elif info_browser_type.lower() == 'chrome':
                                        info_browser_link = 'https://chromium.googlesource.com/chromium/src.git/+/{}'.format(test_result.get('version'))
                                    extra_info_obj = {
                                        'OS/Target/Comment': '{}/{}/{}'.format(os_name, target_name, comment_name),
                                        'Suites': suite_name
                                    }

                                    perf_data = {
                                        'performance_data': {
                                            'framework': {
                                                'name': 'hasal'
                                            },
                                            'suites': perf_data_suites
                                        }
                                    }
                                    # Upload to Perfherder
                                    try:
                                        server_url = '{protocol}://{host}'.format(protocol=HasalServer._config_perfherder_protocol,
                                                                                  host=HasalServer._config_perfherder_host)

                                        uploader = PerfherderUploader(HasalServer._config_perfherder_client_id,
                                                                      HasalServer._config_perfherder_secret,
                                                                      os_name=os_name,
                                                                      platform=test_result.get('platform'),
                                                                      machine_arch=test_result.get('platform'),
                                                                      build_arch=test_result.get('platform'),
                                                                      server_url=server_url,
                                                                      repo=HasalServer._config_perfherder_repo)
                                        uploader.submit(revision=test_result.get('revision'),
                                                        browser=browser_name,
                                                        timestamp=start_timestamp,
                                                        perf_data=perf_data,
                                                        link=link,
                                                        version=test_result.get('version'),
                                                        repo_link=info_browser_link,
                                                        video_links=video_links,
                                                        extra_info_obj=extra_info_obj)

                                        # Remove from Register
                                        data_register[os_name][target_name][comment_name][browser_name][suite_name] = []
                                        logger_hasal.info('### Finished, remove register: {}/{}/{}/{}/{}'.format(os_name, target_name, comment_name, browser_name, suite_name))
                                    except Exception as e:
                                        logger_hasal.error(e)
                                else:
                                    # logger_hasal.info('### not finished ###')
                                    pass
            HasalServer.storage_handler.save_register(data_register)
        finally:
            pub_register_mutex.release()
            logger_hasal.info('### Seed {} release! [HasalServer.update_perfherder]'.format(seed))

    @staticmethod
    def update_all():
        HasalServer.storage_handler.save(HasalServer.storage)
        HasalServer.storage = HasalServer.storage_handler.load()
        HasalServer.update_dashboard()
        HasalServer.update_perfherder()

    def calculate_result(self, current_test_obj):
        origin_seq = [{'run_time': item[0], 'si': item[1], 'psi': item[2]} for item in current_test_obj['origin_values']]

        # mean, median, sigma, seq, outliers, si, psi = outlier().detect(seq)
        mean, median, sigma, _, outliers, si, psi = CalculationUtil.generate_statistics_value_for_server(origin_seq)
        # disable outlier calculation all values are counted
        # current_test_obj['origin_values'] = HasalServer.remove_tuple_from_values(current_test_obj['origin_values'], outliers)
        values_list = current_test_obj['origin_values']

        if len(values_list) >= HasalServer._config_test_times:
            # update the median, mean, and sigma
            current_test_obj['median_value'] = median
            current_test_obj['mean_value'] = mean
            current_test_obj['sigma_value'] = sigma
            # update SI and PSI
            current_test_obj['si'] = si
            current_test_obj['psi'] = psi
            # add timestamp
            current_test_obj['timestamp'] = time.time()
            # self.update_all()
        return current_test_obj

    def GET(self, os_name, target, comment_name):
        # TODO: this it for checking the result of Hasal Server.
        try:
            # check the url, server/hasal/<os>/<target_browser>/<test>
            assert os_name is not None and os_name.strip() != '', '[os] is empty.'
            assert target is not None and target.strip() != '', '[target] is empty.'
            os_name = os_name.strip()
            target = target.strip()

            if comment_name is None or comment_name.strip() == '':
                # return all test result of provided target
                return json.dumps(HasalServer.storage[os_name][target], indent=4)
            else:
                comment_name = comment_name.strip()

            if os_name not in HasalServer.storage:
                return 'No os: {}'.format(os_name)
            elif target not in HasalServer.storage[os_name]:
                return 'No target: {}'.format(target)
            elif comment_name not in HasalServer.storage[os_name][target]:
                return 'No comment: {}'.format(comment_name)
            else:
                return json.dumps(HasalServer.storage[os_name][target][comment_name], indent=4)
        except AssertionError as e:
            raise web.badrequest(e.message)

    def POST(self, os_name, target, comment_name):
        """
        The input json example:
            json={
            "os": "mac",
            "target": "firefox-36.0.1",
            "test": "test_foo",
            "webappname": "WEB_APP",
            "browser": "firefox",
            "version": "36.0.1",
            "platform": "x86_64",
            "value": 500,
            "si": 1000,
            "psi": 1000,
            "video": "20160701_001.avi",
            "comment": "first test"
            }
        :param os_name: os. ex: 'linux'
        :param target: target. ex: 'firefox 36'
        :param comment_name: comment. ex: 'first test'
        :return: the json format string.
            ex: {
                "current_test_times": 3,
                "ip": "127.0.0.1",
                "mean_value": -1,
                "median_value": -1,
                "config_test_times": 5,
                "video": "20160701_001.avi",
                "sigma_value": -1
                }
        """
        try:
            # check the url, server/hasal/<os>/<target_browser>/<test>
            assert os_name is not None and os_name.strip() != '', '[os] is empty.'
            assert target is not None and target.strip() != '', '[target] is empty.'
            assert comment_name is not None and comment_name.strip() != '', '[comment] is empty.'
            os_name = os_name.strip()
            target = target.strip()
            comment_name = comment_name.strip()

            # get the POST data
            ip = web.ctx.ip
            data = web.data()
            parameters = urlparse.parse_qs(data)
            # check the POST data contain 'json'
            assert 'json' in parameters, 'Can not get "json" parameter from POST data.'

            # check the input json object
            json_obj = json.loads(parameters['json'][0])
            HasalServer.check_input_json(json_obj)

            test = json_obj.get('test')
            browser_name = json_obj.get('browser')

            # add the os/target/test into storage
            if os_name not in HasalServer.storage:
                HasalServer.storage[os_name] = {}
            if target not in HasalServer.storage[os_name]:
                HasalServer.storage[os_name][target] = {}
            if comment_name not in HasalServer.storage[os_name][target]:
                HasalServer.storage[os_name][target][comment_name] = {}
            if test not in HasalServer.storage[os_name][target][comment_name]:
                HasalServer.storage[os_name][target][comment_name][test] = {}

            if browser_name not in HasalServer.storage[os_name][target][comment_name][test]:
                HasalServer.storage[os_name][target][comment_name][test][browser_name] = {}

                # new data
                current_obj = HasalServer._generate_current_test_obj(json_obj, ip)
                HasalServer.storage[os_name][target][comment_name][test][browser_name] = current_obj

                # if the server config test times is 1, calculate result
                if HasalServer._config_test_times == 1:
                    self.calculate_result(current_obj)
                return HasalServer.return_json(current_obj)
            else:
                current_test_obj = HasalServer.storage[os_name][target][comment_name][test][browser_name]

                # check the test times
                values_list = current_test_obj['origin_values']
                median_value = current_test_obj['median_value']

                if median_value > 0:
                    # already have median value, just return to the client
                    return HasalServer.return_json(current_test_obj)
                else:
                    # add new value into values list
                    values_list.append([json_obj.get('value'), json_obj.get('si', -1), json_obj.get('psi', -1), json_obj.get('video'), ip])
                    # if reach the server config test times, calculate result
                    if len(values_list) >= HasalServer._config_test_times:
                        self.calculate_result(current_test_obj)
                return HasalServer.return_json(current_test_obj)

        except AssertionError as e:
            raise web.badrequest(e.message)


class VideoProfileUpdater:
    """
    Update the video and profile to Hasal server storage.
    """
    _checks = ['os', 'target', 'test', 'browser', 'version', 'comment']
    _keys = ['video_path', 'profile_path']

    def __init__(self):
        HasalServer.storage = HasalServer.storage_handler.load()

    @staticmethod
    def check_input_json(json_obj):
        for item in VideoProfileUpdater._checks:
            assert item in json_obj, 'The json should have "{}" value.'.format(item)

    def POST(self, os_name, target_browser, comment_name):
        """
        The input json example:
            json={
            "os": "mac",
            "target": "firefox-36.0.1",
            "test": "test_foo",
            "comment": "first test",
            "browser": "firefox",
            "version": "36.0.1",
            "video_path": "http://foo.bar/video",
            "profile_path": "http://foo.bar/profile"
            }
        :param os_name: os. ex: 'linux'
        :param target_browser: target. ex: 'firefox 36'
        :param comment_name: comment. ex: 'first test'
        :return: OK with 200 code.
        """
        HasalServer.storage = HasalServer.storage_handler.load()
        try:
            # check the url, server/hasal/<os>/<target_browser>/<test>
            assert os_name is not None and os_name.strip() != '', '[os] is empty.'
            assert target_browser is not None and target_browser.strip() != '', '[target_browser] is empty.'
            assert comment_name is not None and comment_name.strip() != '', '[comment] is empty.'
            os_name = os_name.strip()
            target_browser = target_browser.strip()
            comment_name = comment_name.strip()

            # get the POST data
            # ip = web.ctx.ip
            data = web.data()
            parameters = urlparse.parse_qs(data)
            # check the POST data contain 'json'
            assert 'json' in parameters, 'Can not get "json" parameter from POST data.'

            # check the input json object
            json_obj = json.loads(parameters['json'][0])
            VideoProfileUpdater.check_input_json(json_obj)

            test = json_obj.get('test')
            browser_name = json_obj.get('browser')

            # check the storage
            assert os_name in HasalServer.storage, \
                'No os [{}] in storage'.format(os_name)
            assert target_browser in HasalServer.storage[os_name], \
                'No target [{}] under os [{}]'.format(target_browser, os_name)
            assert comment_name in HasalServer.storage[os_name][target_browser], \
                'No comment_name [{}] under os [{}], target [{}]'.format(comment_name, os_name, target_browser)
            assert test in HasalServer.storage[os_name][target_browser][comment_name], \
                'No test [{}] under os [{}], target [{}], comment [{}]'.format(test, os_name, target_browser, comment_name)
            assert browser_name in HasalServer.storage[os_name][target_browser][comment_name][test], \
                'No browser [{}] under os [{}], target [{}], comment [{}], test [{}]'.format(
                    browser_name, os_name, target_browser, comment_name, test)

            # Update Video and Profile
            for key in VideoProfileUpdater._keys:
                value = json_obj.get(key, None)
                if value:
                    HasalServer.storage[os_name][target_browser][comment_name][test][browser_name][key] = value

            # Save
            HasalServer.storage_handler.save(HasalServer.storage)
            # Upload to Dashboard and Perfherder
            HasalServer.update_all()

            return 'OK'
        except AssertionError as e:
            raise web.badrequest(e.message)


class Index:
    render = web.template.render('templates', base='layout')

    def GET(self):
        return self.render.readme()


if __name__ == '__main__':
    app = web.application(urls, globals())
    app.run()
