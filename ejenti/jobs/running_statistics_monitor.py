import os
import json
import time
import logging
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

from slack_bot import generate_slack_sending_message
from lib.common.commonUtil import StatusRecorder


DEFAULT_VERIFY_KWARGS_LIST = ['sync_queue', 'async_queue', 'slack_sending_queue', 'configs']

DEFAULT_LINE = '=' * 20

SLACK_LOGGING_LEVEL_INFO = '*[INFO]*'
SLACK_LOGGING_LEVEL_WARN = '*[WARN]*'
SLACK_LOGGING_LEVEL_ERROR = '*[ERROR]*'

DEFAULT_SLEEP_SECONDS = 86400

CURRENT_HASAL_FOLDER = os.getcwd()
RUNNING_STATISTICS_FILENAME = 'running_statistics.json'

KEY_CASE_INFO = 'case_info'
KEY_CASE_INFO_CASE_NAME = 'case_name'
KEY_CASE_INFO_CASE_TIMESTAMP = 'case_time_stamp'

KEY_CURRENT_STATUS = StatusRecorder.DEFAULT_FIELD_CURRENT_STATUS
KEY_CURRENT_STATUS_STATUS_IMG_COMPARE_RESULT = StatusRecorder.STATUS_IMG_COMPARE_RESULT
DEFAULT_SUCCESS_STATUS_IMG_COMPARE_RESULT = StatusRecorder.PASS_IMG_COMPARE_RESULT
KEY_CURRENT_STATUS_SIKULI_RUNNING_STAT = StatusRecorder.STATUS_SIKULI_RUNNING_VALIDATION
DEFAULT_SUCCESS_SIKULI_RUNNING_STAT = '0'
KEY_CURRENT_STATUS_FPS_STAT = StatusRecorder.STATUS_FPS_VALIDATION


def verify_consumer_kwargs(kwargs):
    for verify_kwargs_key in DEFAULT_VERIFY_KWARGS_LIST:
        if verify_kwargs_key not in kwargs:
            raise Exception("The current input consumer kwargs didn't contain the kwarg [%s]" % verify_kwargs_key)


def init_consumer(kwargs):
    """
    verify kwargs
    """
    verify_consumer_kwargs(kwargs)


class RunningStatisticsHandler(PatternMatchingEventHandler):
    """
    Handle the events of running_statistics JSON file.
    """

    def set_sending_queue(self, sending_queue=None):
        logging.debug('Setup Sending Queue ...')
        self.sending_queue = sending_queue
        logging.debug('Setup Sending Queue done.')

    def on_created(self, event):
        logging.debug('Found the file be created: {fp}'.format(fp=event.src_path))
        self.check_running_statistics(event.src_path)

    def on_modified(self, event):
        logging.debug('Found the file be modified: {fp}'.format(fp=event.src_path))
        self.check_running_statistics(event.src_path)

    @staticmethod
    def check_sending_queue(sending_queue):
        """
        if the queue is full, then get one item from queue
        """
        if sending_queue.full():
            message_item = sending_queue.get()
            logging.error('The Slack Sending Queue is full, pop one item.\n{line}\n{obj}\n{line}\n'.format(
                line=DEFAULT_LINE,
                obj=message_item))

    def check_running_statistics(self, file_path):
        """
        Checking running_statistics.
        """
        logging.debug('Checking running_statistics ...')
        running_statistics_file_path = file_path

        if os.path.exists(running_statistics_file_path) and os.path.isfile(running_statistics_file_path):

            msg = ''
            try:
                with open(running_statistics_file_path, 'r') as f:
                    running_statistics = json.load(f)

                    if running_statistics:
                        error_img_compare = False
                        error_sikuli_running = False

                        case_info = running_statistics.get(KEY_CASE_INFO, {})
                        current_status = running_statistics.get(KEY_CURRENT_STATUS, {})

                        # checking the status_img_compare_result
                        if current_status.get(
                                KEY_CURRENT_STATUS_STATUS_IMG_COMPARE_RESULT) != DEFAULT_SUCCESS_STATUS_IMG_COMPARE_RESULT:
                            error_img_compare = True

                        # checking the sikuli_running_stat
                        if current_status.get(
                                KEY_CURRENT_STATUS_SIKULI_RUNNING_STAT) != DEFAULT_SUCCESS_SIKULI_RUNNING_STAT:
                            error_sikuli_running = True

                        if error_img_compare or error_sikuli_running:
                            msg = 'We found some error occurred from running_statistics file.\n' \
                                  '*[Case Name]* {casename}\n' \
                                  '*[Timestamp]* {ts}\n' \
                                  '*[Sikuli Running Stat]* {stat_s}\n' \
                                  '*[Image Comapre Stat]* {stat_i}\n' \
                                  '*[FPS Stat]* {stat_f}'.format(casename=case_info.get(KEY_CASE_INFO_CASE_NAME),
                                                                 ts=case_info.get(KEY_CASE_INFO_CASE_TIMESTAMP),
                                                                 stat_s=current_status.get(KEY_CURRENT_STATUS_SIKULI_RUNNING_STAT),
                                                                 stat_i=current_status.get(KEY_CURRENT_STATUS_STATUS_IMG_COMPARE_RESULT),
                                                                 stat_f=current_status.get(KEY_CURRENT_STATUS_FPS_STAT))
            except:
                msg = 'Can not loading *{}* file.'.format(running_statistics_file_path)

            if msg:
                logging.warn(msg)
                slack_msg = '{level} {msg}\n*[Time]* {time}\n{line}'.format(level=SLACK_LOGGING_LEVEL_ERROR,
                                                                            msg=msg,
                                                                            time=datetime.now().strftime(
                                                                                '%Y-%m-%d %H:%M:%S'),
                                                                            line=DEFAULT_LINE)
                # sending to slack sending queue
                msg_obj = generate_slack_sending_message(slack_msg)

                RunningStatisticsHandler.check_sending_queue(sending_queue=self.sending_queue)
                self.sending_queue.put(msg_obj)
        logging.debug('Checking running_statistics done.')


def monitor_running_statistics(**kwargs):
    """
    [Job Entry Point]
    Monitor the upload result failed status, and report it.
    """
    init_consumer(kwargs)

    # get Slack Sending queue
    sending_queue = kwargs.get('slack_sending_queue')

    # prepare configs
    # we do not use configs right now
    # configs = kwargs.get('configs')

    event_handler = RunningStatisticsHandler(patterns=['*{}'.format(RUNNING_STATISTICS_FILENAME)], ignore_directories=True)
    event_handler.set_sending_queue(sending_queue=sending_queue)
    observer = Observer()
    observer.schedule(event_handler, CURRENT_HASAL_FOLDER, recursive=False)
    observer.start()

    while True:
        time.sleep(DEFAULT_SLEEP_SECONDS)
