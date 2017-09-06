import sys
import socket
import pickle
import logging
import platform

from mozillapulse.messages.base import GenericMessage

# The job will be imported by ejenti. Top level will be `ejenti`, not `hasal` or `ejenti.jobs`.
try:
    from ..pulse_modules.hasal_consumer import HasalConsumer  # NOQA
    from ..pulse_modules.hasal_publisher import HasalPublisher  # NOQA
    from ..pulse_modules.hasalPulsePublisher import HasalPulsePublisher  # NOQA
except:
    from pulse_modules.hasal_consumer import HasalConsumer  # NOQA
    from pulse_modules.hasal_publisher import HasalPublisher  # NOQA
    from pulse_modules.hasalPulsePublisher import HasalPulsePublisher  # NOQA


PULSE_KEY_TASK = 'task'
PULSE_KEY_DEBUG_PREFIX = 'debug_'
DEFAULT_VERIFY_KWARGS_LIST = ["sync_queue", "async_queue", "configs"]


def verify_consumer_kwargs(kwargs):
    for verify_kwargs_key in DEFAULT_VERIFY_KWARGS_LIST:
        if verify_kwargs_key not in kwargs:
            raise Exception("The current input consumer kwargs didn't contain the kwarg [%s]" % verify_kwargs_key)


def init_consumer(kwargs):
    # verify kwargs
    verify_consumer_kwargs(kwargs)


def get_topic():
    """
    Getting the pulse topic base on local agent's platform.
    @return: topic string base on platform. ex: 'win7', 'win10', 'darwin', 'linux2'. Raise Exception if not supported.
    """
    platform_name = sys.platform

    if 'win32' == platform_name:
        # Windows will have 'win7' and 'win10'
        platform_release = platform.release()
        if '10' == platform_release:
            return 'win10'
        elif '7' == platform_release:
            return 'win7'
        else:
            raise Exception('Does not support this Windows Release: {}'.format(platform_release))
    else:
        # 'darwin' and 'linux2'
        return platform_name


def listen_pulse(**kwargs):
    """
    Listen the message on Pulse.
    It will load the 'configs' from kwargs, and then get 'username' and 'password' from 'configs'.
    Please setting them up in job_config.json.

    ex:
    "listen_pulse": {
        "module-path": "jobs.pulse",
        "trigger-type": "interval",
        "interval": 0,
        "max-instances": 1,
        "default-loaded": true,
        "configs":{
            "username": "<PULSE_USERNAME>",
            "password": "<PULSE_PASSWORD>"
    }
    """
    init_consumer(kwargs)

    # prepare username, password, and label
    configs = kwargs.get('configs')
    username = configs.get('username')
    password = configs.get('password')

    # verify Pulse configs
    if not username or not password:
        # there is no Pulse account information in "job_config.json"
        logging.error('Cannot access Pulse due to there is no Pulse account information,'
                      ' please check {} file.'.format('job_config'))
        return

    topic = get_topic()
    consumer_label = topic

    queue_type_sync = 'sync'
    queue_type_async = 'async'
    sync_queue = kwargs.get('sync_queue')
    async_queue = kwargs.get('async_queue')
    queue_mapping = {
        queue_type_sync: sync_queue,
        queue_type_async: async_queue
    }

    def got_msg(body, message):
        """
        handle the message
        ack then broker will remove this message from queue
        """
        message.ack()

        data_payload = body.get('payload')

        # handle response info to Trigger
        try:
            response_agent_info(data_payload)
        except Exception as e:
            logging.error(e)

        # logging debug information
        debug_message = ''
        for debug_key in [key for key in data_payload.keys() if key.startswith(PULSE_KEY_DEBUG_PREFIX)]:
            debug_message += '{key}: {value}\n'.format(key=debug_key, value=data_payload.get(debug_key, ''))
        if debug_message:
            logging.debug('### Pulse Got MSG ###\n{line}\n{dbg_msg}{line}'.format(dbg_msg=debug_message,
                                                                                  line='-' * 20))

        # get MetaTask
        meta_task = data_payload.get(PULSE_KEY_TASK)
        meta_task_object = pickle.loads(meta_task)

        # Handle command into specify queue
        task_command_key = meta_task_object.command_key
        task_queue_type = meta_task_object.queue_type
        logging.debug('Task Command Key: {}, and Queue Type: {}'.format(task_command_key, task_queue_type))

        if task_queue_type not in queue_mapping:
            logging.error('Not supported queue type. Skip push task into queue.')
            return

        target_queue = queue_mapping.get(task_queue_type)
        # push task into queue
        task_obj = meta_task_object.get_cmd()
        target_queue.put(task_obj)
        logging.debug('Push task into [{}] queue with command name {}.'.format(task_queue_type,
                                                                               task_command_key))

    def response_agent_info(data_payload):
        """
        Return back the received MetaTask UID and agent information to Pulse "mgt" topic channel.
        """
        # the debug information key name
        DEBUG_QUEUE_TYPE = 'debug_queue_type'
        DEBUG_COMMAND_NAME = 'debug_command_name'
        DEBUG_OVERWRITE_COMMAND_CONFIGS = 'debug_overwrite_command_configs'
        DEBUG_UID = 'debug_UID'
        # define mgt keys
        PULSE_MGT_TOPIC = 'mgt'
        PULSE_MGT_OBJECT_KEY = 'message'
        PULSE_MGT_OBJECT_TASK_UID = 'task_uid'
        PULSE_MGT_OBJECT_HOSTNAME = 'hostname'
        PULSE_MGT_OBJECT_IP = 'ip'
        PULSE_MGT_OBJECT_TOPIC = 'topic'
        PULSE_MGT_OBJECT_PLATFORM = 'platform'
        PULSE_MGT_OBJECT_CMD_NAME = 'cmd_name'
        PULSE_MGT_OBJECT_CMD_CFG = 'cmd_configs'
        PULSE_MGT_OBJECT_QUEUE_TYPE = 'queue_type'
        # getting the agent information
        ret_uid = data_payload.get(DEBUG_UID, '')
        ret_hostname = socket.gethostname()
        ret_ip = socket.gethostbyname(socket.gethostname())
        ret_topic = get_topic()
        ret_platform = sys.platform
        ret_cmd_name = data_payload.get(DEBUG_COMMAND_NAME, '')
        ret_cmd_cfg = data_payload.get(DEBUG_OVERWRITE_COMMAND_CONFIGS, '')
        ret_queue_type = data_payload.get(DEBUG_QUEUE_TYPE, '')
        # prepare the sending data
        data = {
            PULSE_MGT_OBJECT_TASK_UID: ret_uid,
            PULSE_MGT_OBJECT_HOSTNAME: ret_hostname,
            PULSE_MGT_OBJECT_IP: ret_ip,
            PULSE_MGT_OBJECT_TOPIC: ret_topic,
            PULSE_MGT_OBJECT_PLATFORM: ret_platform,
            PULSE_MGT_OBJECT_CMD_NAME: ret_cmd_name,
            PULSE_MGT_OBJECT_CMD_CFG: ret_cmd_cfg,
            PULSE_MGT_OBJECT_QUEUE_TYPE: ret_queue_type
        }

        # check queue
        queue_exists = HasalPulsePublisher.check_pulse_queue_exists(username=username,
                                                                    password=password,
                                                                    topic=topic)
        if not queue_exists:
            logging.error('There is not Queue for Topic [{topic}]. Message might be ignored.'.format(topic=topic))

        # make publisher
        p = HasalPublisher(user=username, password=password)
        # prepare message
        mymessage = GenericMessage()
        # setup topic
        mymessage.routing_parts.append(PULSE_MGT_TOPIC)
        mymessage.set_data(PULSE_MGT_OBJECT_KEY, data)
        # send
        p.publish(mymessage)
        # disconnect
        p.disconnect()

    # create consumer
    c = HasalConsumer(user=username, password=password, applabel=consumer_label)
    c.configure(topic=topic, callback=got_msg)

    c.listen()
