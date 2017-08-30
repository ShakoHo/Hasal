"""ejenti.

Usage:
  ejenti.py [--cmd-config=<str>] [--job-config=<str>] [--config=<str>]
  ejenti.py (-h | --help)

Options:
  -h --help                       Show this screen.
  --config=<str>                  Specify the config.json file path. [default: configs/ejenti/ejenti_config.json]
  --cmd-config=<str>              Specify the cmd_config.json file path. [default: configs/ejenti/cmd_config.json]
  --job-config=<str>              Specify the job_config.json file path. [default: configs/ejenti/job_config.json]
"""
import os
import re
import sys
import time
import logging
import importlib
from lib.common.commonUtil import CommonUtil
from docopt import docopt
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from multiprocessing import Manager


class MainRunner(object):

    class FilterAllLog(logging.Filter):
        # default we will filter logger from apscheduler.executors.default, apscheduler.scheduler,
        # you can config filter logger in config.json
        def filter(self, record):
            return ""

    def __init__(self, input_cmd_config_fp, input_job_config_fp, input_config_fp):

        # init value
        cmd_config_fp = os.path.abspath(input_cmd_config_fp)
        job_config_fp = os.path.abspath(input_job_config_fp)
        config_fp = os.path.abspath(input_config_fp)

        # load configuration json files
        self.cmd_config = CommonUtil.load_json_file(cmd_config_fp)
        self.job_config = CommonUtil.load_json_file(job_config_fp)
        self.config = CommonUtil.load_json_file(config_fp)

        # init schedulers
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_jobstore('sqlalchemy', url=self.config['job_store_url'])
        self.scheduler.start()

        # init variables
        mananger = Manager()
        self.sync_queue = mananger.Queue()
        self.async_queue = mananger.Queue()
        self.current_job_list = []

        # Slack Sending Queue
        self.slack_sending_queue = mananger.Queue()

        # init logger
        self.set_logging(self.config['log_level'], self.config['log_filter'])

    def set_logging(self, log_level, log_filter_list):
        default_log_format = '%(asctime)s %(levelname)s [%(name)s.%(funcName)s] %(message)s'
        default_datefmt = '%Y-%m-%d %H:%M'
        if log_level.lower() == "debug":
            logging.basicConfig(level=logging.DEBUG, format=default_log_format, datefmt=default_datefmt)
        else:
            logging.basicConfig(level=logging.INFO, format=default_log_format, datefmt=default_datefmt)

        my_filter = self.FilterAllLog()
        for target_logger in log_filter_list:
            logging.getLogger(target_logger).addFilter(my_filter)

    def scheduler_del_job(self, **kwargs):
        input_cmd_str = kwargs.get("input_cmd_str", "")
        cmd_str_list = input_cmd_str.split(" ")
        if len(cmd_str_list) == 2:
            job_id = cmd_str_list[1]
            current_job_list = self.scheduler.get_jobs()
            current_job_id_list = [j.id for j in current_job_list]
            if job_id in current_job_id_list:
                self.scheduler.remove_job(job_id)
            else:
                logging.error("Cannot find the specify job id [%s]" % job_id)
        else:
            logging.error("Incorrect cmd format! [%s]" % input_cmd_str)

    def scheduler_list_job(self, **kwargs):
        self.scheduler.print_jobs()

    def scheduler_shutdown(self, **kwargs):
        self.scheduler.shutdown()
        sys.exit(0)

    def list_all_commands(self, **kwargs):
        print "Current supported commands as below:"
        print "-" * 80
        for cmd_str in self.cmd_config['cmd-settings']:
            print '{:30s} {:50s} '.format(cmd_str, self.cmd_config['cmd-settings'][cmd_str]['desc'])
        print "-" * 80

    def scheduler_job_handler(self, input_cmd_obj, input_cmd_str):
        cmd_match_pattern = input_cmd_obj.keys()[0]
        func_point = getattr(self, input_cmd_obj[cmd_match_pattern]['func-name'])
        func_point(cmd_configs=input_cmd_obj[cmd_match_pattern]['configs'], input_cmd_str=input_cmd_str)

    def cmd_queue_composer(self, input_cmd_str):
        for cmd_pattern in self.cmd_config['cmd-settings']:
            re_compile_obj = re.compile(cmd_pattern)
            re_match_obj = re_compile_obj.search(input_cmd_str)
            if re_match_obj:
                current_command_obj = self.cmd_config['cmd-settings'][cmd_pattern]
                logging.debug("job matched [%s]" % cmd_pattern)
                target_queue_type = current_command_obj.get('queue-type', None)
                if target_queue_type == "async":
                    self.async_queue.put({"cmd_obj": current_command_obj, "cmd_pattern": cmd_pattern, "input_cmd_str": input_cmd_str})
                elif target_queue_type == "sync":
                    self.sync_queue.put({"cmd_obj": current_command_obj, "cmd_pattern": cmd_pattern, "input_cmd_str": input_cmd_str})
                else:
                    self.scheduler_job_handler({cmd_pattern: current_command_obj}, input_cmd_str)
                break

    def load_default_jobs(self, input_scheduler, input_job_config):
        current_jobs = input_scheduler.get_jobs()
        current_jobs_name = [job.name for job in current_jobs]
        for job_name in input_job_config:
            if input_job_config[job_name]['default-loaded']:
                if job_name not in current_jobs_name:
                    func_point = getattr(importlib.import_module(input_job_config[job_name]['module-path']), job_name)
                    self.scheduler.add_job(func_point, input_job_config[job_name]['trigger-type'],
                                           id=job_name,
                                           seconds=input_job_config[job_name]['interval'],
                                           max_instances=input_job_config[job_name]['max-instances'],
                                           kwargs={
                                               'async_queue': self.async_queue,
                                               'sync_queue': self.sync_queue,
                                               'slack_sending_queue': self.slack_sending_queue,
                                               'configs': input_job_config[job_name]['configs'],
                                               'cmd_config': self.cmd_config}
                                           )

    def job_exception_listener(self, event):
        if event.exception:
            logging.error("Job [%s] crashed [%s]" % (event.job_id, event.exception))
            logging.error(event.traceback)

    def add_event_listener(self):
        self.scheduler.add_listener(self.job_exception_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    def run(self):
        # load default job into scheduler if the job is not exist
        self.load_default_jobs(self.scheduler, self.job_config)

        # add event listener into scheduler
        self.add_event_listener()

        # enter the loop to receive the interactive command
        while True:
            user_input = raw_input()
            self.cmd_queue_composer(user_input)
            time.sleep(3)


def main():
    arguments = docopt(__doc__)
    objRunner = MainRunner(arguments['--cmd-config'], arguments['--job-config'], arguments['--config'])
    objRunner.run()


if __name__ == '__main__':
    main()
