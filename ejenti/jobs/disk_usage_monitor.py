import os
import psutil
import logging
from datetime import datetime
from slack_bot import generate_slack_sending_message


DEFAULT_VERIFY_KWARGS_LIST = ['sync_queue', 'async_queue', 'slack_sending_queue', 'configs']

DEFAULT_LINE = '=' * 20

SLACK_LOGGING_LEVEL_INFO = '*[INFO]*'
SLACK_LOGGING_LEVEL_WARN = '*[WARN]*'
SLACK_LOGGING_LEVEL_ERROR = '*[ERROR]*'

DEFAULT_ALERT_USAGE_PERCENT = 80
KEY_ALERT_USAGE_PERCENT = 'alert_usage_percent'


def verify_consumer_kwargs(kwargs):
    for verify_kwargs_key in DEFAULT_VERIFY_KWARGS_LIST:
        if verify_kwargs_key not in kwargs:
            raise Exception("The current input consumer kwargs didn't contain the kwarg [%s]" % verify_kwargs_key)


def init_consumer(kwargs):
    """
    verify kwargs
    """
    verify_consumer_kwargs(kwargs)


def monitor_disk_usage(**kwargs):
    """
    [Job Entry Point]
    Monitor the monitor_disk_usage, and report it.
    @return:
    """
    init_consumer(kwargs)

    # get Slack Sending queue
    sending_queue = kwargs.get('slack_sending_queue')

    # prepare configs
    configs = kwargs.get('configs')

    # checking disk usage
    check_disk_usage(sending_queue=sending_queue, configs=configs)


def check_disk_usage(sending_queue, configs):
    """
    Sending alert if the disk usage exceed the alert percent.
    @param sending_queue:
    @param configs:
    @return:
    """
    alert_usage_percent = float(configs.get(KEY_ALERT_USAGE_PERCENT, DEFAULT_ALERT_USAGE_PERCENT))
    disk_usage = psutil.disk_usage(os.path.abspath(os.sep))
    current_percent = disk_usage.percent

    if current_percent > alert_usage_percent:
        # current usage percent more than alert setting
        msg = 'Current disk usage is *{percent}%* ({used}/{total} bytes), exceed {alert}%.'.format(percent=current_percent,
                                                                                                   used=disk_usage.used,
                                                                                                   total=disk_usage.total,
                                                                                                   alert=alert_usage_percent)

        logging.warn(msg)

        slack_msg = '{level} {msg}\n*[Time]* {time}\n{line}'.format(level=SLACK_LOGGING_LEVEL_WARN,
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
