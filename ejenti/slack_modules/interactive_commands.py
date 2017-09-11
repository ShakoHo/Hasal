import os
import psutil


def cmd_disk_usage(sending_queue, cmd_configs={}):
    """
    [Slack Command]
    Return the agent disk usage.
    """
    disk_usage = psutil.disk_usage(os.path.abspath(os.sep))
    current_percent = disk_usage.percent
    msg = 'Current disk usage is *{percent}%* ({used}/{total} bytes).'.format(percent=current_percent,
                                                                              used=disk_usage.used,
                                                                              total=disk_usage.total)

    msg_obj = _generate_slack_sending_message(msg)
    sending_queue.put(msg_obj)


def _generate_slack_sending_message(message, channel='mgt'):
    """
    Return an object which contain the sending message which can be put into slack_sending_queue.
    """
    if channel not in ['mgt', 'election']:
        channel = 'mgt'
    ret_obj = {
        'message': message,
        'channel': channel
    }
    return ret_obj
