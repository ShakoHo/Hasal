import os
import json
import time
import logging
from datetime import datetime
from slack_bot import generate_slack_sending_message


DEFAULT_VERIFY_KWARGS_LIST = ['sync_queue', 'async_queue', 'slack_sending_queue', 'configs']

DEFAULT_LINE = '=' * 20

SLACK_LOGGING_LEVEL_INFO = '*[INFO]*'
SLACK_LOGGING_LEVEL_WARN = '*[WARN]*'
SLACK_LOGGING_LEVEL_ERROR = '*[ERROR]*'

# We will suggest setup the range more than Job's interval time.
DEFAULT_FILE_CHANGE_TIME_RANGE = 3600
KEY_FILE_CHANGE_TIME_RANGE = 'file_change_time_range_sec'

UPLOAD_RESULT_FAILED_FILENAME = 'upload_result_failed.json'


def verify_consumer_kwargs(kwargs):
    for verify_kwargs_key in DEFAULT_VERIFY_KWARGS_LIST:
        if verify_kwargs_key not in kwargs:
            raise Exception("The current input consumer kwargs didn't contain the kwarg [%s]" % verify_kwargs_key)


def init_consumer(kwargs):
    """
    verify kwargs
    """
    verify_consumer_kwargs(kwargs)


def monitor_upload_result(**kwargs):
    """
    [Job Entry Point]
    Monitor the upload result failed status, and report it.
    """
    init_consumer(kwargs)

    # get Slack Sending queue
    sending_queue = kwargs.get('slack_sending_queue')

    # prepare configs
    configs = kwargs.get('configs')

    # checking disk usage
    check_upload_result(sending_queue=sending_queue, configs=configs)


def check_upload_result(sending_queue, configs):
    """
    Sending alert if the upload_result.
    @param sending_queue:
    @param configs:
    @return:
    """
    alert_file_diff_range = configs.get(KEY_FILE_CHANGE_TIME_RANGE, DEFAULT_FILE_CHANGE_TIME_RANGE)

    upload_result_file_path = os.path.join(os.getcwd(), UPLOAD_RESULT_FAILED_FILENAME)

    if os.path.exists(upload_result_file_path) and os.path.isfile(upload_result_file_path):

        timestamp = os.stat(upload_result_file_path).st_mtime
        time_diff = time.time() - timestamp

        # checking file content when file was changed int alert_file_diff_range seconds
        if time_diff < alert_file_diff_range:
            msg = ''
            try:
                with open(upload_result_file_path, 'r') as f:
                    upload_result_status = json.load(f)

                    if upload_result_status:
                        msg = 'There are some upload result failed in *{}* file.'.format(UPLOAD_RESULT_FAILED_FILENAME)
            except:
                msg = 'Can not loading *{}* file.'.format(UPLOAD_RESULT_FAILED_FILENAME)

            if msg:
                logging.warn(msg)
                slack_msg = '{level} {msg}\n*[Time]* {time}\n{line}'.format(level=SLACK_LOGGING_LEVEL_ERROR,
                                                                            msg=msg,
                                                                            time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                                                            line=DEFAULT_LINE)
                # sending to slack sending queue
                msg_obj = generate_slack_sending_message(slack_msg)

                check_sending_queue(sending_queue=sending_queue)
                sending_queue.put(msg_obj)


def check_sending_queue(sending_queue):
    """
    if the queue is full, then get one item from queue
    """
    if sending_queue.full():
        message_item = sending_queue.get()
        logging.error('The Slack Sending Queue is full, pop one item.\n{line}\n{obj}\n{line}\n'.format(line=DEFAULT_LINE,
                                                                                                       obj=message_item))
