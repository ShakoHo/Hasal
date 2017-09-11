import os
import re
import json
import time
import random
import socket
import logging

from datetime import datetime
from slackclient import SlackClient

# The job will be imported by ejenti. Top level will be `ejenti`, not `hasal` or `ejenti.jobs`.
try:
    from ejenti.slack_modules.interactive_commands import *  # NOQA
except:
    from slack_modules.interactive_commands import *  # NOQA


DEFAULT_VERIFY_KWARGS_LIST = ['sync_queue', 'async_queue', 'slack_sending_queue', 'configs']

DEFAULT_DELAY_SEC = 1

KEY_CMD_CONFIG = 'cmd_config'

KEY_BOT_NAME = 'bot_name'
KEY_BOT_API_TOKEN = 'bot_api_token'
KEY_BOT_MGT_CHANNEL = 'bot_mgt_channel'
KEY_BOT_ELECTION_CHANNEL = 'bot_election_channel'

ELECTION_SHORT_TIMEOUT = 15
ELECTION_TIMEOUT = 10 * 60
ELECTION_TIMEOUT_RANDOM_OFFSET = 60
ELECTION_LEADER_HEARTBEAT = 5 * 60
ELECTION_FOLLOWER_HEARTBEAT = 5 * 60
ELECTION_SEND_MSG_DELAY = 5

ELECTION_BOT_FOLLOWER = 'FOLLOWER'
ELECTION_BOT_CANDIDATE = 'CANDIDATE'
ELECTION_BOT_LEADER = 'LEADER'

ELECTION_MSG_HEARTBEAT = 'HB'
ELECTION_MSG_ELECTION = 'ELEC'
ELECTION_MSG_FOLLOWER_HEARTBEAT = 'FW'

KEY_FOLLOWER_INFO_TYPE = 'type'
KEY_FOLLOWER_INFO_HOSTNAME = 'hostname'
KEY_FOLLOWER_INFO_IP = 'ip'
KEY_FOLLOWER_INFO_PID = 'pid'
KEY_FOLLOWER_INFO_POWER = 'power'
KEY_FOLLOWER_INFO_TIME = 'time'
KEY_FOLLOWER_INFO_TIMESTAMP = 'ts'

SLACK_INTERACTIVE_CMD = {
    'slack-disk-usage': cmd_disk_usage
}


def verify_consumer_kwargs(kwargs):
    for verify_kwargs_key in DEFAULT_VERIFY_KWARGS_LIST:
        if verify_kwargs_key not in kwargs:
            raise Exception("The current input consumer kwargs didn't contain the kwarg [%s]" % verify_kwargs_key)


def init_consumer(kwargs):
    # verify kwargs
    verify_consumer_kwargs(kwargs)


def generate_slack_sending_message(message, channel='mgt'):
    """
    [Public]
    Return an object which contain the sending message which can be put into slack_sending_queue.
    @param message: string
    @param channel: mgt or election
    @return:
    """
    if channel not in ['mgt', 'election']:
        channel = 'mgt'
    ret_obj = {
        'message': message,
        'channel': channel
    }
    return ret_obj


def init_slack_bot(**kwargs):
    """
    [Job Entry Point]
    Init Slack Bot
    @param kwargs:
    @return:
    """
    init_consumer(kwargs)

    # get Sync and Async queue
    queue_type_sync = 'sync'
    queue_type_async = 'async'
    sync_queue = kwargs.get('sync_queue')
    async_queue = kwargs.get('async_queue')
    queue_mapping = {
        queue_type_sync: sync_queue,
        queue_type_async: async_queue
    }

    # get Slack Sending queue
    sending_queue = kwargs.get('slack_sending_queue')

    # prepare username, password, and label
    configs = kwargs.get('configs')
    bot_name = configs.get(KEY_BOT_NAME)
    bot_api_token = configs.get(KEY_BOT_API_TOKEN)
    bot_mgt_channel_name = configs.get(KEY_BOT_MGT_CHANNEL)
    bot_election_channel_name = configs.get(KEY_BOT_ELECTION_CHANNEL)

    # verify Slack configs
    if not bot_name or not bot_api_token \
            or not bot_mgt_channel_name or not bot_election_channel_name:
        # there is no Pulse account information in "job_config.json"
        logging.error('Cannot access Slack due to there is no Slack BOT API information,'
                      ' please check {} file.'.format('job_config'))
        return

    # get cmd_config
    cmd_config = kwargs.get(KEY_CMD_CONFIG)

    # init the slack_client
    slack_client = SlackClient(bot_api_token)

    try:
        # https://api.slack.com/methods/rtm.connect
        if slack_client.rtm_connect():
            # find Bot ID
            bot_user_obj = get_bot_user_obj(slack_client, bot_name)
            bot_id = bot_user_obj.id
            logging.debug('\nName: {botname}\nID: {botid}\nIP: {ip}\nPID: {pid}'.format(botname=bot_name,
                                                                                        botid=bot_id,
                                                                                        ip=get_current_ip(),
                                                                                        pid=os.getpid()))

            bot_mgt_channel_obj = find_channel(slack_client, bot_mgt_channel_name)
            bot_mgt_channel_id = bot_mgt_channel_obj.id

            # for Bots Election
            bot_election_channel_obj = find_channel(slack_client, bot_election_channel_name)
            bot_election_channel_id = bot_election_channel_obj.id
            election_leader_heartbeat = ELECTION_LEADER_HEARTBEAT
            election_timeout = ELECTION_SHORT_TIMEOUT
            election_follower_heartbeat_timeout = ELECTION_FOLLOWER_HEARTBEAT + random.randint(-60, 60)
            election_type = ELECTION_BOT_FOLLOWER

            follower_list = {}

            while True:
                rtm_ret_list = slack_client.rtm_read()
                if rtm_ret_list:
                    for rtm_ret in rtm_ret_list:
                        channel_id = rtm_ret.get('channel')

                        if channel_id == bot_election_channel_id:
                            # handle Bots election
                            election_leader_heartbeat, election_timeout, election_follower_heartbeat_timeout, election_type, follower_list = handle_election(slack_client,
                                                                                                                                                             rtm_ret,
                                                                                                                                                             election_leader_heartbeat,
                                                                                                                                                             election_timeout,
                                                                                                                                                             election_follower_heartbeat_timeout,
                                                                                                                                                             election_type,
                                                                                                                                                             bot_user_obj,
                                                                                                                                                             bot_election_channel_obj,
                                                                                                                                                             follower_list)

                        elif channel_id == bot_mgt_channel_id:
                            # handle RTM response
                            handle_rtm(slack_client, rtm_ret, configs, cmd_config, election_type, bot_user_obj, bot_mgt_channel_obj, queue_mapping, sending_queue, follower_list)

                # election counter
                election_leader_heartbeat, election_timeout, election_follower_heartbeat_timeout, election_type = handle_election_counter(slack_client,
                                                                                                                                          election_leader_heartbeat,
                                                                                                                                          election_timeout,
                                                                                                                                          election_follower_heartbeat_timeout,
                                                                                                                                          election_type,
                                                                                                                                          bot_election_channel_obj)

                time.sleep(DEFAULT_DELAY_SEC)

                # handle Slack Sending queue
                handle_sending_queue(slack_client, bot_mgt_channel_obj, bot_election_channel_obj, sending_queue)

    except Exception as e:
        logging.error(e)


def handle_sending_queue(slack_client, bot_mgt_channel_obj, bot_election_channel_obj, sending_queue):
    """
    Handle the Slack Sending queue.

    The item format in slack_sending_queue:
        {
            'message': message,
            'channel': channel
        }

    The message is string, and channel is one of ['mgt', 'election'].

    @param slack_client:
    @param configs:
    @param cmd_config:
    @param election_type:
    @param bot_user_obj:
    @param bot_mgt_channel_obj:
    @param sending_queue:
    @return:
    """
    if sending_queue.qsize() > 0:
        message_item = sending_queue.get()

        origin_message = message_item.get('message')

        if origin_message:
            input_message = '*[Agent]* {hn}/{ipaddr}\n{message}'.format(hn=get_current_hostname(),
                                                                        ipaddr=get_current_ip(),
                                                                        message=origin_message)
            input_channel = message_item.get('channel')
            if input_channel == 'election':
                channel_obj = bot_election_channel_obj
            else:
                channel_obj = bot_mgt_channel_obj

            send(slack_client, input_message, channel_obj)

            time.sleep(DEFAULT_DELAY_SEC)


def handle_election(slack_client, rtm_ret, election_leader_heartbeat, election_timeout, election_follower_heartbeat_timeout,
                    election_type, bot_user_obj, bot_election_channel_obj, follower_list):
    """
    Handle Bot Election.
    @param slack_client:
    @param rtm_ret:
    @param election_leader_heartbeat: Leader heartbeat counter
    @param election_timeout: Election timeout counter
    @param election_follower_heartbeat_timeout: Election follower timeout counter
    @param election_type: Election Type. 'FOLLOWER', 'CANDIDATE', or 'LEADER'
    @param bot_user_obj:
    @param bot_election_channel_obj:
    @param follower_list:
    @return: election_leader_heartbeat, election_timeout, election_type
    """
    user_id = rtm_ret.get('user')
    # if the election message comes from other user, then skip it.
    if user_id != bot_user_obj.id:
        return election_leader_heartbeat, election_timeout, election_follower_heartbeat_timeout, election_type, follower_list

    text = rtm_ret.get('text')
    if text:
        message = text.encode('utf-8')
    else:
        return election_leader_heartbeat, election_timeout, election_follower_heartbeat_timeout, election_type, follower_list

    try:
        dict_obj = json.loads(message)

        logging.debug('Handle Election Channel: {}'.format(dict_obj))

        input_type = dict_obj.get(KEY_FOLLOWER_INFO_TYPE)
        input_power = dict_obj.get(KEY_FOLLOWER_INFO_POWER)
        current_power = get_bot_power_for_election()

        if input_type == ELECTION_MSG_ELECTION:
            # all Bot will go into election mode
            logging.debug('Do Election ...')
            if current_power > input_power:
                logging.debug('Power more than other, do election! IP {ip}, PID {pid}'.format(ip=get_current_ip(),
                                                                                              pid=os.getpid()))
                if election_type == ELECTION_BOT_CANDIDATE:
                    # already be candidate, does not need to reset timeout
                    pass
                else:
                    election_type = ELECTION_BOT_CANDIDATE
                    election_leader_heartbeat = ELECTION_LEADER_HEARTBEAT
                    election_timeout = ELECTION_SHORT_TIMEOUT

                # wait 1~3 sec
                time.sleep(random.randint(0, ELECTION_SEND_MSG_DELAY))
                send_election(slack_client, ELECTION_MSG_ELECTION, bot_election_channel_obj)

            elif current_power < input_power:
                logging.debug('Power less than other, I am follower! IP {ip}, PID {pid}'.format(ip=get_current_ip(),
                                                                                                pid=os.getpid()))
                election_type = ELECTION_BOT_FOLLOWER
                election_leader_heartbeat = ELECTION_LEADER_HEARTBEAT
                election_timeout = ELECTION_TIMEOUT + random.randint(0, ELECTION_TIMEOUT_RANDOM_OFFSET)
                election_follower_heartbeat_timeout = ELECTION_SHORT_TIMEOUT + random.randint(ELECTION_SHORT_TIMEOUT, ELECTION_SHORT_TIMEOUT * 2)
            else:
                # if get the same power, skip
                pass

        elif input_type == ELECTION_MSG_HEARTBEAT:
            # if I am leader, and get heartbeat message comes from other bot, then election
            if election_type == ELECTION_BOT_LEADER and current_power != input_power:
                logging.debug('I found other leader, do election! IP {ip}, PID {pid}'.format(ip=get_current_ip(),
                                                                                             pid=os.getpid()))
                election_type = ELECTION_BOT_CANDIDATE
                election_leader_heartbeat = ELECTION_LEADER_HEARTBEAT
                election_timeout = ELECTION_SHORT_TIMEOUT
                # wait 1~3 sec
                time.sleep(random.randint(0, ELECTION_SEND_MSG_DELAY))
                send_election(slack_client, ELECTION_MSG_ELECTION, bot_election_channel_obj)

            elif election_type == ELECTION_BOT_LEADER and current_power == input_power:
                # if get the same power, skip
                pass

            else:
                # reset timeout counter
                election_leader_heartbeat = ELECTION_LEADER_HEARTBEAT
                election_timeout = ELECTION_TIMEOUT + random.randint(0, ELECTION_TIMEOUT_RANDOM_OFFSET)

        elif input_type == ELECTION_MSG_FOLLOWER_HEARTBEAT:
            if election_type == ELECTION_BOT_LEADER:
                # when getting Follower Heartbeat, update follower list
                hostname = dict_obj.get(KEY_FOLLOWER_INFO_HOSTNAME)
                ip_addr = dict_obj.get(KEY_FOLLOWER_INFO_IP)
                pid = dict_obj.get(KEY_FOLLOWER_INFO_PID)
                ts = dict_obj.get(KEY_FOLLOWER_INFO_TIMESTAMP)
                follower_list['{hn}/{ip}'.format(hn=hostname, ip=ip_addr)] = {
                    KEY_FOLLOWER_INFO_HOSTNAME: hostname,
                    KEY_FOLLOWER_INFO_IP: ip_addr,
                    KEY_FOLLOWER_INFO_PID: pid,
                    KEY_FOLLOWER_INFO_TIMESTAMP: ts
                }

    except Exception as e:
        logging.error(e)

    return election_leader_heartbeat, election_timeout, election_follower_heartbeat_timeout, election_type, follower_list


def handle_election_counter(slack_client, election_leader_heartbeat, election_timeout, election_follower_heartbeat_timeout,
                            election_type, bot_election_channel_obj):
    """
    Handle the Bot Election counter.
    @param slack_client:
    @param election_leader_heartbeat: Leader heartbeat counter
    @param election_timeout: Election timeout counter
    @param election_follower_heartbeat_timeout: Election timeout counter
    @param election_type: Election Type. 'FOLLOWER', 'CANDIDATE', or 'LEADER'
    @param bot_election_channel_obj:
    @return: election_leader_heartbeat, election_timeout, election_type
    """
    if election_type == ELECTION_BOT_LEADER:
        # Leader will send HeartBeat to other when election_leader_heartbeat less than 0
        election_leader_heartbeat -= 1
        if election_leader_heartbeat <= 0:
            # send heartbeat
            election_leader_heartbeat = ELECTION_LEADER_HEARTBEAT
            send_election(slack_client, ELECTION_MSG_HEARTBEAT, bot_election_channel_obj)

    elif election_type == ELECTION_BOT_FOLLOWER:
        # Follower will wait HeartBeat or Election, send election when election_timeout less than 0.
        election_timeout -= 1
        election_follower_heartbeat_timeout -= 1
        if election_timeout <= 0:
            election_type = ELECTION_BOT_CANDIDATE
            election_timeout = ELECTION_SHORT_TIMEOUT
            election_follower_heartbeat_timeout = ELECTION_FOLLOWER_HEARTBEAT + random.randint(-60, 60)
            # send election
            send_election(slack_client, ELECTION_MSG_ELECTION, bot_election_channel_obj)
        # Follower will send follower heartbeat to leader
        if election_follower_heartbeat_timeout <= 0:
            election_follower_heartbeat_timeout = ELECTION_FOLLOWER_HEARTBEAT
            send_election(slack_client, ELECTION_MSG_FOLLOWER_HEARTBEAT, bot_election_channel_obj)

    elif election_type == ELECTION_BOT_CANDIDATE:
        # Candidate will wait election_timeout to 0, become Leader if there is no other candidates.
        election_timeout -= 1
        if election_timeout <= 0:
            logging.debug('Wow... I am Leader! I will tell other bots.')
            election_type = ELECTION_BOT_LEADER
            election_timeout = ELECTION_TIMEOUT
            election_leader_heartbeat = ELECTION_LEADER_HEARTBEAT
            # send heartbeat
            send_election(slack_client, ELECTION_MSG_HEARTBEAT, bot_election_channel_obj)

    return election_leader_heartbeat, election_timeout, election_follower_heartbeat_timeout, election_type


def send_election(slack_client, message_type, bot_election_channel_obj):
    """
    Send Election message or HeartBeat message.
    @param slack_client:
    @param message_type: string. 'HB' or 'ELEC'.
    @param bot_election_channel_obj:
    """
    now = datetime.now()
    now_string = now.strftime('%Y-%m-%d_%H:%M:%S.%f')
    message = {
        KEY_FOLLOWER_INFO_TYPE: message_type,
        KEY_FOLLOWER_INFO_HOSTNAME: get_current_hostname(),
        KEY_FOLLOWER_INFO_IP: get_current_ip(),
        KEY_FOLLOWER_INFO_PID: os.getpid(),
        KEY_FOLLOWER_INFO_POWER: get_bot_power_for_election(),
        KEY_FOLLOWER_INFO_TIME: now_string,
        KEY_FOLLOWER_INFO_TIMESTAMP: time.time()
    }
    send(slack_client, message, bot_election_channel_obj)


def ip_2_int(ip_string):
    """
    Input IP address string, and then return int.
    Ex: '192.168.0.1' => 3232235521
    @param ip_string:
    @return: IP integer number.
    """
    return reduce(lambda out, x: (out << 8) + int(x), ip_string.split('.'), 0)


def get_current_hostname():
    """
    return current hostname.
    """
    return socket.gethostname()


def get_current_ip():
    """
    return current IP address.
    """
    return socket.gethostbyname(get_current_hostname())


def get_bot_power_for_election():
    """
    Get the current Bot election power base on IP and PID.
    @return: A integer number <IP to Int><PID>. for example, 323223552119772.
    """
    ip = get_current_ip()
    pid = os.getpid()
    return int('{}{}'.format(ip_2_int(ip), pid))


def handle_rtm(slack_client, rtm_ret, configs, cmd_config, election_type, bot_user_obj, bot_mgt_channel_obj,
               queue_mapping, sending_queue, follower_list):
    """
    Handle Slack RTM message.
    Ref: https://api.slack.com/rtm
    @param slack_client:
    @param rtm_ret:
    @param configs: job configs
    @param cmd_config: cmd_config settings dict object
    @param election_type: current election type, leader will do more than others
    @param bot_user_obj:
    @param bot_mgt_channel_obj:
    @param queue_mapping:
    @param sending_queue:
    @param follower_list:
    @return:
    """
    EVENT_TYPES_HANDLERS = {
        'message': handle_rtm_message
    }

    evt_type = rtm_ret.get('type')
    for evt in EVENT_TYPES_HANDLERS.keys():
        if evt == evt_type:
            return EVENT_TYPES_HANDLERS[evt](slack_client, rtm_ret, configs, cmd_config, election_type, bot_user_obj,
                                             bot_mgt_channel_obj, queue_mapping, sending_queue, follower_list)
    return False


def handle_rtm_message(slack_client, rtm_ret, configs, cmd_config, election_type, bot_user_obj,
                       bot_mgt_channel_obj, queue_mapping, sending_queue, follower_list):
    """
    Handle Slack RTM message which type is "message".
    @param slack_client:
    @param rtm_ret:
    @param configs: job configs
    @param cmd_config: cmd_config settings dict object
    @param election_type: current election type, leader will do more than others
    @param bot_user_obj:
    @param bot_mgt_channel_obj:
    @param queue_mapping:
    @param sending_queue:
    @param follower_list:
    @return:
    """
    bot_id = bot_user_obj.id

    LEADER_CMD_HANDLERS = {
        'help': handle_rtm_message_leader_help,
        'list-agents': handle_rtm_message_leader_list_agents
    }

    COMMAND_TASK_KEY_OBJECT = 'cmd_obj'
    COMMAND_TASK_KEY_PATTERN = 'cmd_pattern'
    COMMAND_TASK_KEY_INPUT_STR = 'input_cmd_str'

    # if message changed, it will have subtype
    if rtm_ret.get('subtype') == 'message_changed':
        new_msg = rtm_ret.get('message')
        if new_msg:
            text = new_msg.get('text')
            # getting user id
            user_id = new_msg.get('user')
        else:
            return False
    else:
        # getting message text
        text = rtm_ret.get('text')
        # getting user id
        user_id = rtm_ret.get('user')

    if text:
        message = text.encode('utf-8')
    else:
        return False

    # Skip if message comes from bot it-self
    if user_id == bot_id:
        # logging.debug('Message from Bot: {msg}, skip.'.format(msg=message))
        return False

    # getting channel and user name
    user_obj = find_user(slack_client, user_id)
    user_name = user_obj.name if user_obj else ''
    logging.debug('=> handle_rtm_message\n'
                  'User/ID: {u} / {uid}\nText: {t}'.format(u=user_name,
                                                           uid=user_id,
                                                           t=message))

    # parsing message to word list
    word_list = re.split('\s*', message.strip(), maxsplit=2)
    if len(word_list) > 0:
        """
        Handle Leader commands
        """
        if election_type == ELECTION_BOT_LEADER:
            for word in word_list:
                for leader_cmd in LEADER_CMD_HANDLERS.keys():
                    if word == leader_cmd:
                        return LEADER_CMD_HANDLERS[leader_cmd](slack_client, rtm_ret, configs, cmd_config,
                                                               election_type, bot_user_obj, bot_mgt_channel_obj,
                                                               follower_list, LEADER_CMD_HANDLERS.keys())

        """
        Handle each agents commands
        format:
            <HOSTNAME_OR_IP> <FUNC> <CONFIGS>
                <HOSTNAME_OR_IP>: string
                <FUNC>: string
                <CONFIGS>: json
        """
        if word_list[0] == get_current_hostname() or word_list[0] == get_current_ip():

            logging.debug('Word list: {}'.format(word_list))
            # getting Input Command Name
            if len(word_list) >= 2:
                input_cmd_name = word_list[1]
            else:
                # Error, show usage
                logging.debug('There is no command: {}'.format(word_list))
                ret_agent_message = 'There is no command.'
                return handle_rtm_message_agent_fail(slack_client, ret_agent_message, message, bot_mgt_channel_obj)

            # getting Input Command's configs
            if len(word_list) >= 3:
                try:
                    input_configs = json.loads(word_list[2])
                except:
                    # Error, show usage
                    logging.debug('Can not parse config to JSON: {}'.format(word_list[2]))
                    ret_agent_message = 'Can not parse config to JSON.'
                    return handle_rtm_message_agent_fail(slack_client, ret_agent_message, message, bot_mgt_channel_obj)
            else:
                input_configs = {}

            #
            # Slack Interactive Commands
            #
            if input_cmd_name in SLACK_INTERACTIVE_CMD:
                # getting command object from SLACK_INTERACTIVE_CMD
                input_cmd_obj = SLACK_INTERACTIVE_CMD.get(input_cmd_name)
                if not input_cmd_obj:
                    # Error, show usage
                    logging.debug('Can not found command in SLACK_INTERACTIVE_CMD: {}'.format(input_cmd_name))
                    ret_agent_message = 'Can not found command in Slack Interactive Commands.'
                    return handle_rtm_message_agent_fail(slack_client, ret_agent_message, message, bot_mgt_channel_obj)
                else:
                    return input_cmd_obj(sending_queue=sending_queue, cmd_configs=input_configs)
            #
            # cmd_config
            #
            elif input_cmd_name in cmd_config['cmd-settings']:
                # getting command object from cmd_config
                input_cmd_obj = cmd_config['cmd-settings'].get(input_cmd_name)
                if not input_cmd_obj:
                    # Error, show usage
                    logging.debug('Can not found command in cmd_config: {}'.format(input_cmd_name))
                    ret_agent_message = 'Can not found command in cmd_config.'
                    return handle_rtm_message_agent_fail(slack_client, ret_agent_message, message, bot_mgt_channel_obj)
                elif input_cmd_obj.get('queue-type') not in queue_mapping.keys():
                    # Error, show usage
                    logging.debug('Not supported queue-type: {}'.format(input_cmd_obj.get('queue-type')))
                    ret_agent_message = 'Not supported queue-type.'
                    return handle_rtm_message_agent_fail(slack_client, ret_agent_message, message, bot_mgt_channel_obj)
                else:
                    if input_configs:
                        input_cmd_obj['configs'] = input_configs
                        ret_message = '*[Agent]* {hn}/{ipaddr}\n*[Get Command]* {cmd}\n*[Configs]*\n{cfg}'.format(
                            hn=get_current_hostname(),
                            ipaddr=get_current_ip(),
                            cmd=input_cmd_name,
                            cfg=input_configs)
                    else:
                        ret_message = '*[Agent]* {hn}/{ipaddr}\n*[Get Command]* {cmd}\n*[Configs]* no configs'.format(
                            hn=get_current_hostname(),
                            ipaddr=get_current_ip(),
                            cmd=input_cmd_name)
                    task_obj = {
                        COMMAND_TASK_KEY_OBJECT: input_cmd_obj,
                        COMMAND_TASK_KEY_PATTERN: input_cmd_name,
                        COMMAND_TASK_KEY_INPUT_STR: message
                    }

                    input_queue_type = input_cmd_obj.get('queue-type')
                    target_queue = queue_mapping.get(input_queue_type)
                    target_queue.put(task_obj)

                    return send(slack_client, ret_message, bot_mgt_channel_obj)


def handle_rtm_message_leader_help(slack_client, rtm_ret, configs, cmd_config, election_type, bot_user_obj,
                                   bot_mgt_channel_obj, follower_list, leader_cmd_list):
    """
    Leader will handle the RTM help message, show usage.
    Will be register in LEADER_CMD_HANDLERS.
    @param slack_client:
    @param rtm_ret:
    @param configs:
    @param cmd_config:
    @param election_type:
    @param bot_user_obj:
    @param bot_mgt_channel_obj:
    @param follower_list:
    @param leader_cmd_list:
    @return:
    """
    cmd_settings = cmd_config.get('cmd-settings')

    sync_commands = {}
    async_commands = {}

    for cmd_key, cmd_obj in cmd_settings.items():
        if cmd_obj.get('queue-type') == 'sync':
            sync_commands[cmd_key] = cmd_obj.get('desc', '')
        if cmd_obj.get('queue-type') == 'async':
            async_commands[cmd_key] = cmd_obj.get('desc', '')

    help_message = 'Here is supported commands.\n\n'

    # Leader commands
    help_message += '*[Leader Commands]*\n'
    for cmd_name in sorted(leader_cmd_list):
        help_message += '    *{cmd}*\n'.format(cmd=cmd_name)

    # Slack Interactive Commands
    if len(SLACK_INTERACTIVE_CMD) > 0:
        help_message += '*[Slack Interactive Commands]*\n'
        for cmd_name in sorted(SLACK_INTERACTIVE_CMD):
            help_message += '    *{cmd}*\n'.format(cmd=cmd_name)

    # Sync commands
    if len(sync_commands) > 0:
        help_message += '*[Sync Commands]*\n'
        for cmd_name in sorted(sync_commands):
            help_message += '    *{cmd}*\t{desc}\n'.format(cmd=cmd_name, desc=sync_commands.get(cmd_name))

    # Async commands
    if len(async_commands) > 0:
        help_message += '*Sync Commands*\n'
        for cmd_name in sorted(async_commands):
            help_message += '    *{cmd}*\t{desc}\n'.format(cmd=cmd_name, desc=async_commands.get(cmd_name))

    help_message += '\n*[Usage]*\n' \
                    '*Input Format* <Agent> <Command> [<Configs>]\n' \
                    '    <Agent>: string, hostname or ip address.\n' \
                    '    <Command>: string, command name.\n' \
                    '    <Configs>: JSON, configs.\n\n' \

    send(slack_client, help_message, bot_mgt_channel_obj)


def handle_rtm_message_leader_list_agents(slack_client, rtm_ret, configs, cmd_config, election_type, bot_user_obj,
                                          bot_mgt_channel_obj, follower_list, leader_cmd_list):
    """
    Leader will handle the RTM help message, show usage.
    Will be register in LEADER_CMD_HANDLERS.
    @param slack_client:
    @param rtm_ret:
    @param configs:
    @param cmd_config:
    @param election_type:
    @param bot_user_obj:
    @param bot_mgt_channel_obj:
    @param follower_list:
    @param leader_cmd_list:
    """
    KEY_FOLLOWER_INFO_HOSTNAME = 'hostname'
    KEY_FOLLOWER_INFO_IP = 'ip'
    KEY_FOLLOWER_INFO_PID = 'pid'
    KEY_FOLLOWER_INFO_TIMESTAMP = 'ts'

    current_time = int(time.time())

    msg = '*[Current Agents]*\n'
    msg += '{hn}/{ip}, PID {pid}, Leader\n'.format(hn=get_current_hostname(),
                                                   ip=get_current_ip(),
                                                   pid=os.getpid())

    for agent_key, agent_object in sorted(follower_list.items()):

        hn = agent_object.get(KEY_FOLLOWER_INFO_HOSTNAME, 'NA')
        ip_addr = agent_object.get(KEY_FOLLOWER_INFO_IP, 'NA')
        pid = agent_object.get(KEY_FOLLOWER_INFO_PID, 'NA')
        ts = agent_object.get(KEY_FOLLOWER_INFO_TIMESTAMP, 0)

        if current_time > ts:
            sec = '{}s ago'.format(int(current_time - ts)) if ts else 'unknow'
        else:
            sec = 'pls update NTP'

        msg += '{hn}/{ip}, PID {pid}, {sec}\n'.format(hn=hn,
                                                      ip=ip_addr,
                                                      pid=pid,
                                                      sec=sec)

    send(slack_client, msg, bot_mgt_channel_obj)


def handle_rtm_message_agent_fail(slack_client, ret_agent_message, origin_input_message, bot_mgt_channel_obj):
    """
    Agnet will handle the RTM message type when failed.
    @param slack_client:
    @param ret_agent_message:
    @param origin_input_message:
    @param bot_mgt_channel_obj:
    @return:
    """
    ret_message = '*[Agent]* {hn}/{ipaddr}\n*[Get Message]* {msg}\n{err_msg}'.format(hn=get_current_hostname(),
                                                                                     ipaddr=get_current_ip(),
                                                                                     msg=origin_input_message,
                                                                                     err_msg=ret_agent_message)
    send(slack_client, ret_message, bot_mgt_channel_obj)


def send(slack_client, message, channel_obj):
    """
    Send slack message.
    @param slack_client:
    @param message:
    @param channel_obj:
    @return:
    """
    ret = slack_client.api_call("chat.postMessage", channel=channel_obj.id, text=message, as_user=True)
    if not ret.get('ok'):
        logging.error('Sending message failed!\n{ret}'.format(ret=ret))
        return False
    return True


def get_bot_user_obj(slack_client, bot_name):
    """
    The method find_user() will return a User object.
        id : U6LNC9BN0
        tz : None
        name : hasal-bot
        real_name : Hasal Bot
    @param slack_client:
    @param bot_name:
    @return: Bot User info.
    """
    return find_user(slack_client, bot_name)


def find_user(slack_client, search_string):
    """
    User object has following attributes:
        - name
        - tz
        - real_name
        - server
        - id
    Ref:
        https://github.com/slackapi/python-slackclient/blob/master/slackclient/_user.py
        https://github.com/slackapi/python-slackclient/blob/master/slackclient/_util.py
            SearchDict
    :param slack_client:
    :param search_string:
    :return:
    """
    return slack_client.server.users.find(search_string)


def find_channel(slack_client, search_string):
    """
    Channel object has following attributes:
        - name
        - id
        - members
        - server
    Ref:
        https://github.com/slackapi/python-slackclient/blob/master/slackclient/_channel.py
        https://github.com/slackapi/python-slackclient/blob/master/slackclient/_util.py
            SearchList
    :param slack_client:
    :param search_string:
    :return:
    """
    return slack_client.server.channels.find(search_string)
