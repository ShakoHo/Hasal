import os
import re
import shutil
import socket
import json
import hashlib
import logging
import urllib2
import urlparse
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from hasal_consumer import HasalConsumer
from hasalPulsePublisher import HasalPulsePublisher


class TasksTrigger(object):
    """
    MD5_HASH_FOLDER is ".md5"
    """
    ARCHIVE_ROOT_URL = 'https://archive.mozilla.org'
    ARCHIVE_LATEST_FOLDER = '/pub/firefox/nightly/latest-mozilla-central/'
    ARCHIVE_LINK_RE_STRING = r'(?<=href=").*?(?=")'

    KEY_CONFIG_PULSE_USER = 'pulse_username'
    KEY_CONFIG_PULSE_PWD = 'pulse_password'
    KEY_CONFIG_JOBS = 'jobs'
    KEY_JOBS_ENABLE = 'enable'
    KEY_JOBS_AMOUNT = 'amount'
    KEY_JOBS_TOPIC = 'topic'
    KEY_JOBS_PLATFORM_BUILD = 'platform_build'
    KEY_JOBS_INTERVAL_MINUTES = 'interval_minutes'
    KEY_JOBS_CMD = 'cmd'
    KEY_JOBS_CONFIGS = 'configs'

    MD5_HASH_FOLDER = '.md5'

    # filename example: 'firefox-56.0a1.en-US.linux-x86_64.json'
    MATCH_FORMAT = '.{platform_key}.{ext}'

    PLATFORM_MAPPING = {
        'linux32': {
            'key': 'linux-i686',
            'ext': 'tar.bz2'
        },
        'linux64': {
            'key': 'linux-x86_64',
            'ext': 'tar.bz2'
        },
        'mac': {
            'key': 'mac',
            'ext': 'dmg'
        },
        'win32': {
            'key': 'win32',
            'ext': 'zip'
        },
        'win64': {
            'key': 'win64',
            'ext': 'zip'
        }
    }

    def __init__(self, config, cmd_config_obj):
        self.all_config = config
        self.cmd_config_obj = cmd_config_obj

        # get jobs config
        self.jobs_config = config.get(TasksTrigger.KEY_CONFIG_JOBS, {})
        self.pulse_username = config.get(TasksTrigger.KEY_CONFIG_PULSE_USER)
        self.pulse_password = config.get(TasksTrigger.KEY_CONFIG_PULSE_PWD)

        self._validate_data()

        self.scheduler = BackgroundScheduler()
        self.scheduler.start()

    def _validate_data(self):
        # validate Pulse account
        if not self.pulse_username or not self.pulse_password:
            # there is no Pulse account information in "job_config.json"
            raise Exception('Cannot access Pulse due to there is no Pulse account information.')

    @staticmethod
    def get_all_latest_files():
        """
        Get all latest files from ARCHIVE server.
        @return: dict object {'<filename>': '<folder/path/with/filename>', ...}
        """
        latest_url = urlparse.urljoin(TasksTrigger.ARCHIVE_ROOT_URL, TasksTrigger.ARCHIVE_LATEST_FOLDER)
        ret_dict = {}
        try:
            res_obj = urllib2.urlopen(latest_url)
            if res_obj.getcode() == 200:
                for line in res_obj.readlines():
                    match = re.search(TasksTrigger.ARCHIVE_LINK_RE_STRING, line)
                    if match:
                        href_link = match.group(0)
                        name = href_link.split('/')[-1]
                        ret_dict[name] = href_link
            else:
                logging.error('Fetch builds failed. Code: {code}, Link: {link}'.format(code=res_obj.getcode(),
                                                                                       link=latest_url))
        except Exception as e:
            logging.error(e)
        return ret_dict

    @staticmethod
    def get_latest_info_json_url(platform):
        """
        Get latest platform build's JSON file URL base on specify platform.
        @param platform: the specify platform. Defined in PLATFORM_MAPPING[<name>]['key'].
        @return: the latest platform build's JSON file URL.
        """
        ext_json = 'json'
        match_endswith_string = TasksTrigger.MATCH_FORMAT.format(platform_key=platform, ext=ext_json)

        # get latest files
        all_files = TasksTrigger.get_all_latest_files()

        # find the matched files base on platform, e.g. "win64.json"
        matched_files = {k: v for k, v in all_files.items() if k.endswith(match_endswith_string)}

        if len(matched_files) >= 1:
            # when get matched files, then get the latest file URL folder path
            matched_filename = sorted(matched_files.keys())[-1]
            ret_url = matched_files.get(matched_filename)
            return urlparse.urljoin(TasksTrigger.ARCHIVE_ROOT_URL, ret_url)
        else:
            logging.error('There is no matched filename endswith "{}".'.format(match_endswith_string))
            return None

    @staticmethod
    def get_remote_md5(url, max_size=1 * 1024 * 1024):
        """
        Get remote resource's MD5 hash string.
        @param url: remote resource URL.
        @param max_size: max download size. default is 1*1024*1024 bytes (1 MB).
        @return: the MD5 hash string (lowercase).
        """
        remote_resource = urllib2.urlopen(url)
        md5_handler = hashlib.md5()
        counter = 0
        while True:
            data = remote_resource.read(1024)
            counter += 1024

            if not data or counter >= max_size:
                break
            md5_handler.update(data)
        return md5_handler.hexdigest()

    @staticmethod
    def get_latest_info_json_md5_hash(platform):
        """
        Get MD5 hash string of latest platform build's JSON file base on specify platform.
        @param platform: the specify platform. Defined in PLATFORM_MAPPING[<name>]['key'].
        @return: the MD5 hash string of latest platform build's JSON file.
        """
        json_file_url = TasksTrigger.get_latest_info_json_url(platform)
        hash_string = TasksTrigger.get_remote_md5(json_file_url)
        return hash_string

    @staticmethod
    def check_latest_info_json_md5_changed(job_name, platform):
        """
        @param job_name: the job name which will set as identify name.
        @param platform: the platform archive server.
        @return: True if changed, False if not changed.
        """
        current_file_folder = os.path.dirname(os.path.realpath(__file__))

        md5_folder = os.path.join(current_file_folder, TasksTrigger.MD5_HASH_FOLDER)

        # prepare MD5 folder
        if os.path.exists(md5_folder):
            if not os.path.isdir(md5_folder):
                shutil.rmtree(md5_folder)
                os.makedirs(md5_folder)
        else:
            os.makedirs(md5_folder)

        # get new MD5 hash
        new_hash = TasksTrigger.get_latest_info_json_md5_hash(platform)

        # check MD5 file
        job_md5_file = os.path.join(md5_folder, job_name)
        if os.path.exists(job_md5_file):
            with open(job_md5_file, 'r') as f:
                origin_hash = f.readline()

            if origin_hash == new_hash:
                # no changed
                return False
            else:
                # changed
                logging.info('Job "{}" platform "{}": Latest Hash [{}], Origin Hash: [{}]'.format(job_name,
                                                                                                  platform,
                                                                                                  new_hash,
                                                                                                  origin_hash))
                with open(job_md5_file, 'w') as f:
                    f.write(new_hash)
                return True
        else:
            # found the file for the 1st time
            logging.info('Job "{}" platform "{}": Latest Hash [{}], no origin hash.'.format(job_name,
                                                                                            platform,
                                                                                            new_hash))
            with open(job_md5_file, 'w') as f:
                f.write(new_hash)
            return True

    @staticmethod
    def _validate_job_config(job_config):
        """
        Validate the job config. Required keys: topic, platform_build, and cmd.
        @param job_config: job detail config.
        @return: True or False.
        """
        required_keys = [TasksTrigger.KEY_JOBS_TOPIC,
                         TasksTrigger.KEY_JOBS_PLATFORM_BUILD,
                         TasksTrigger.KEY_JOBS_CMD]

        for required_key in required_keys:
            if required_key not in job_config:
                logging.error('There is no required key [{}] in job config.'.format(required_key))
                return False
        return True

    @staticmethod
    def job_pushing_meta_task(username, password, command_config, job_name, topic, amount, platform_build, cmd_name, overwrite_cmd_config=None):
        """
        [JOB]
        Pushing the MetaTask if the remote build's MD5 was changed.
        @param username: Pulse username.
        @param password: Pulse password.
        @param command_config: The overall command config dict object.
        @param job_name: The job name which be defined in trigger_config.json.
        @param topic: The Topic on Pulse. Refer to `get_topic()` method of `jobs.pulse`.
        @param amount: The MetaTask amount per time.
        @param platform_build: The platform on Archive server.
        @param cmd_name: The MetaTask command name.
        @param overwrite_cmd_config: The overwrite command config.
        """
        changed = TasksTrigger.check_latest_info_json_md5_changed(job_name=job_name, platform=platform_build)
        if changed:
            # check queue
            queue_exists = HasalPulsePublisher.check_pulse_queue_exists(username=username,
                                                                        password=password,
                                                                        topic=topic)
            if not queue_exists:
                logging.error('There is not Queue for Topic [{topic}]. Message might be ignored.'.format(topic=topic))

            # Push MetaTask to Pulse
            publisher = HasalPulsePublisher(username=username,
                                            password=password,
                                            command_config=command_config)

            now = datetime.now()
            now_string = now.strftime('%Y-%m-%d_%H:%M:%S.%f')
            uid_prefix = '{time}.{job}'.format(time=now_string, job=job_name)
            # push meta task
            logging.info('Pushing to Pulse...\n'
                         '{line}\n'
                         'UID prefix: {uid_prefix}\n'
                         'Trigger Job: {job_name}\n'
                         'Platform: {platform}\n'
                         'Topic: {topic}\n'
                         'Amount: {amount}\n'
                         'command {cmd}\n'
                         'cmd_config: {cmd_config}\n'
                         '{line}\n'.format(uid_prefix=uid_prefix,
                                           job_name=job_name,
                                           platform=platform_build,
                                           topic=topic,
                                           amount=amount,
                                           cmd=cmd_name,
                                           cmd_config=overwrite_cmd_config,
                                           line='-' * 10))
            for idx in range(amount):
                uid = '{prefix}.{idx}'.format(prefix=uid_prefix, idx=idx + 1)
                publisher.push_meta_task(topic=topic,
                                         command_name=cmd_name,
                                         overwrite_cmd_configs=overwrite_cmd_config,
                                         uid=uid)

    @staticmethod
    def job_listen_response_from_agent(username, password, rotating_file_path):
        """
        [JOB]
        Logging the message from Agent by Pulse "mgt" topic channel.
        @param username: Pulse username.
        @param password: Pulse password.
        @param rotating_file_path: The rotating file path.
        """
        PULSE_MGT_TOPIC = 'mgt'
        PULSE_MGT_OBJECT_KEY = 'message'

        rotating_logger = logging.getLogger("RotatingLog")
        rotating_logger.setLevel(logging.INFO)

        # create Rotating File Handler, 1 day, backup 30 times.
        rotating_handler = TimedRotatingFileHandler(rotating_file_path,
                                                    when='midnight',
                                                    interval=1,
                                                    backupCount=30)

        rotating_formatter = logging.Formatter('%(asctime)s, %(levelname)s, %(message)s')
        rotating_handler.setFormatter(rotating_formatter)
        rotating_logger.addHandler(rotating_handler)

        def got_response(body, message):
            """
            handle the message
            ack then broker will remove this message from queue
            """
            message.ack()
            data_payload = body.get('payload')
            msg_dict_obj = data_payload.get(PULSE_MGT_OBJECT_KEY)
            try:
                msg_str = json.dumps(msg_dict_obj)
                rotating_logger.info(msg_str)
            except:
                rotating_logger.info(msg_dict_obj)

        hostname = socket.gethostname()
        consumer_label = 'TRIGGER-{hostname}'.format(hostname=hostname)
        topic = PULSE_MGT_TOPIC
        c = HasalConsumer(user=username, password=password, applabel=consumer_label)
        c.configure(topic=topic, callback=got_response)

        c.listen()

    def _job_exception_listener(self, event):
        if event.exception:
            logging.error("Job [%s] crashed [%s]" % (event.job_id, event.exception))
            logging.error(event.traceback)

    def _add_event_listener(self):
        self.scheduler.add_listener(self._job_exception_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    def run(self):
        """
        Adding jobs into scheduler.
        """
        # add event listener
        self._add_event_listener()

        # create "mgt" channel listener
        logging.info('Adding Rotating Logger for listen Agent information ...')
        MGT_ID = 'trigger_mgt_listener'
        MGT_LOG_PATH = 'rotating_mgt.log'
        self.scheduler.add_job(func=TasksTrigger.job_listen_response_from_agent,
                               trigger='interval',
                               id=MGT_ID,
                               max_instances=1,
                               seconds=10,
                               args=[],
                               kwargs={'username': self.pulse_username,
                                       'password': self.pulse_password,
                                       'rotating_file_path': MGT_LOG_PATH})
        logging.info('Adding Rotating Logger done: {fp}'.format(fp=os.path.abspath(MGT_LOG_PATH)))

        # create each Trigger jobs
        for job_name, job_detail in self.jobs_config.items():
            """
            ex:
            {
                "win7_x64": {
                    "enable": true,
                    "topic": "win7",
                    "platform_build": "win64",
                    "interval_minutes": 10,
                    "cmd": "download-latest-nightly",
                    "configs": {}
                },
                ...
            }
            """
            if not TasksTrigger._validate_job_config(job_detail):
                logging.error('There is not valid job.\n{}: {}\n'.format(job_name, job_detail))

            # have default config
            enable = job_detail.get(TasksTrigger.KEY_JOBS_ENABLE, False)
            interval_minutes = job_detail.get(TasksTrigger.KEY_JOBS_INTERVAL_MINUTES, 10)
            configs = job_detail.get(TasksTrigger.KEY_JOBS_CONFIGS, {})
            amount = job_detail.get(TasksTrigger.KEY_JOBS_AMOUNT, 1)
            # required
            topic = job_detail.get(TasksTrigger.KEY_JOBS_TOPIC)
            platform_build = job_detail.get(TasksTrigger.KEY_JOBS_PLATFORM_BUILD)
            cmd = job_detail.get(TasksTrigger.KEY_JOBS_CMD)

            if enable:
                logging.info('Job [{}] is enabled.'.format(job_name))

                # adding Job Trigger
                self.scheduler.add_job(func=TasksTrigger.job_pushing_meta_task,
                                       trigger='interval',
                                       id=job_name,
                                       max_instances=1,
                                       minutes=interval_minutes,
                                       args=[],
                                       kwargs={'username': self.pulse_username,
                                               'password': self.pulse_password,
                                               'command_config': self.cmd_config_obj,
                                               'job_name': job_name,
                                               'topic': topic,
                                               'amount': amount,
                                               'platform_build': platform_build,
                                               'cmd_name': cmd,
                                               'overwrite_cmd_config': configs})

            else:
                logging.info('Job [{}] is disabled.'.format(job_name))
