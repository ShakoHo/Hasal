"""

Usage:
  backfill_agent.py [--query] [--latest] [-i=<str>]
  backfill_agent.py (-h | --help)

Options:
  -h --help                 Show this screen.
  --query                   Query latest data.
  --latest                  Automatically check latest nightly build.
  -i=<str>                  Automatically refill data from json file.
"""

import os
import csv
import sys
import json
import random
import platform
import datetime
import subprocess
from dateutil import tz
from docopt import docopt


# common function
def call_subprocess(input_cmd):
    ret_code = subprocess.call(input_cmd, shell=True)
    if ret_code != 0:
        sys.exit(ret_code)


# predefine static data
BROWSER_SET = ['firefox', 'chrome']
MACHINE_SET = ['windows8-64', 'windows10-64']
PLATFORM_DICT = {'Windows-10': 'windows10-64', 'Windows-7': 'windows8-64'}
tmp_file = 'tmp.txt'
csv_file = 'tmp.csv'
backfill_json_template = os.path.join('tools', 'backfill_latest_template.json')
backfill_json_run = os.path.join('tools', 'backfill_latest_run.json')
backfill_python = os.path.join('tools', 'generate_data_for_nightly_build.py')
from_zone = tz.tzutc()
to_zone = tz.tzlocal()

task_schedule = [
    "amazon_ail_hover_related_product_thumbnail Median",
    "amazon_ail_select_search_suggestion Median",
    "amazon_ail_type_in_search_field Median",
    "facebook_ail_click_close_chat_tab Median",
    "facebook_ail_click_open_chat_tab Median",
    "facebook_ail_click_open_chat_tab_emoji Median",
    "facebook_ail_click_photo_viewer_right_arrow Median",
    "facebook_ail_scroll_home_1_txt Median",
    "facebook_ail_type_comment_1_txt Median",
    "facebook_ail_type_composerbox_1_txt Median",
    "facebook_ail_type_message_1_txt Median",
    "gdoc_ail_pagedown_10_text Median",
    "gmail_ail_compose_new_mail_via_keyboard Median",
    "gmail_ail_open_mail Median",
    "gmail_ail_reply_mail Median",
    "gmail_ail_type_in_reply_field Median",
    "gsearch_ail_select_image_cat Median",
    "gsearch_ail_select_search_suggestion Median",
    "gsearch_ail_type_searchbox Median",
    "youtube_ail_select_search_suggestion Median",
    "youtube_ail_type_in_search_field Median"
]


def create_csv(query_days):
    # query data
    query_sec = query_days * 24 * 60 * 60
    print "Start querying data... might takes a while!"
    cmd = 'python tools/query_data_from_perfherder.py --interval={} > {}'.format(query_sec, tmp_file)
    call_subprocess(cmd)
    with open(tmp_file) as fin, open(csv_file, 'w') as fout:
        o = csv.writer(fout)
        o.writerow(['suite_name', '_', 'browser_type', 'machine_platform', 'date', 'time', 'value'])
        for line in fin:
            o.writerow(line.split())
    print "Done query data!"
    os.remove(tmp_file)


def run_backfill():
    # clean space, remove output_config
    call_subprocess('del /F/S/Q output_config')

    # run generate data
    call_subprocess('python {} -i {}'.format(backfill_python, backfill_json_run))


class BFagent(object):
    def __init__(self):
        self.backfill_list = []
        self.history_dates = []
        # reference date is the day we aim to check for
        # Here we set the reference date one day before local time (Taiwan)
        self.ref_date = (datetime.date.today() -
                         datetime.timedelta(days=1)).strftime("%Y-%m-%d")

        # predefine data structure
        self.dot_count = dict()
        for b in BROWSER_SET:
            self.dot_count[b] = {}
            for s in task_schedule:
                self.dot_count[b][s] = 0

        # check current platform
        self.current_platform = ''
        for p in PLATFORM_DICT.keys():
            if p in platform.platform():
                self.current_platform = PLATFORM_DICT[p]

    def reset_date_list_dict(self):
        # Reset the reference date, back fill task list, and counter
        self.backfill_list = []
        self.ref_date = (datetime.date.today() -
                         datetime.timedelta(days=1)).strftime("%Y-%m-%d")

        # Counter must be set to 0 for next round
        for b in BROWSER_SET:
            for s in task_schedule:
                self.dot_count[b][s] = 0

    def analyze_csv(self):
        with open(csv_file) as f:
            r = csv.DictReader(f)
            for row in r:
                _s = '{} {}'.format(row['suite_name'], row['_'])
                _m = row['machine_platform']
                _b = row['browser_type']

                if _s not in task_schedule:
                    continue
                elif _m != self.current_platform or _b not in BROWSER_SET:
                    continue

                # convert UTC to local time
                _t = '{} {}'.format(row['date'], row['time'])
                utc = datetime.datetime.strptime(_t, "%Y-%m-%d %H-%M-%S-000000")
                utc = utc.replace(tzinfo=from_zone)
                central = utc.astimezone(to_zone)
                # _t = central.strftime("%Y-%m-%d %H-%M-%S-000000")
                _d = central.strftime("%Y-%m-%d")

                if self.ref_date != _d:
                    continue
                else:
                    self.dot_count[_b][_s] += 1

    def list_recover_data(self):
        # There must be at least 6 points each day
        ref_count = 6
        for s in task_schedule:
            for b in BROWSER_SET:
                __count = self.dot_count[b][s]
                missing = ref_count - __count
                if missing > 0:
                    self.backfill_list.append([b, s, missing])
                    print 'Missing', b, s, missing

    def create_json(self, refill_date='latest'):
        # create json file for running
        with open(backfill_json_template) as fin, open(backfill_json_run, 'w') as fout:
            for line in fin:
                if '\"ADD_FIREFOX_BUILD_PATH\"' in line:
                    # The input here determines how many time should each case runs.
                    # Here, we only run each case once for every run
                    if refill_date == 'latest':
                        fout.write('\"latest-mozilla-central/\"')
                    else:
                        fout.write('\"{}\"'.format(refill_date))

                elif '\"TEMPLATE\": \"ADD_SUITE_HERE\"' in line:
                    # In latest mode, random select 5 cases to run.
                    # In history mode, run all suite
                    max_suite_num = 5
                    if refill_date == 'latest':
                        selected_suites = random.sample(self.backfill_list, max_suite_num)
                    else:
                        selected_suites = self.backfill_list

                    i = 0
                    for task in selected_suites:
                        i += 1
                        suite = task[1].split()[0]
                        app = task[1].split()[0].split('_')[0]
                        _b = task[0]
                        output_row = '\"{}\": {{\"case_list":[\"tests.regression.{}.test_{}_{}\"],' \
                                     '\"perfherder-suitename\": \"{}\"}}'.format(suite, app, _b, suite, suite)
                        fout.write(output_row)
                        if i != len(selected_suites):
                            # add comma except the last row
                            fout.write(',')
                else:
                    # just copy other lines from template
                    fout.write(line)

    def run(self, need_query):
        """ Refill latest Nightly """
        if need_query or not os.path.isfile(csv_file):
            create_csv(2)  # just query last two dates data
        self.reset_date_list_dict()
        self.analyze_csv()
        self.list_recover_data()
        if len(self.backfill_list) == 0:
            print 'Congratulation! Everything was fine recently.'
        else:
            print 'Oops! Something is missing. I will help you recover it!'
            self.create_json()
            run_backfill()

        # Remove csv file when this round finished
        os.remove(csv_file)

    def run_history(self, backfill_config):
        # load date config file
        with open(backfill_config) as fh:
            self.history_dates = json.load(fh)
        self.history_dates = sorted(self.history_dates, reverse=True)

        # check all input are valid
        # TODO: add file checker

        # Assume back fill dates are in 3 months
        create_csv(90)

        # loop through all the dates picked
        for nightly_build_link in self.history_dates:
            date = nightly_build_link[8:18]
            # set ref_date to config file
            print "\n=======================\n" \
                  "* Checking {} *\n" \
                  "=======================".format(date)
            self.reset_date_list_dict()
            self.ref_date = date
            self.analyze_csv()
            self.list_recover_data()
            if len(self.backfill_list) == 0:
                print 'Congratulation! Everything was fine on {}.'.format(self.ref_date)
            else:
                print 'Oops! Something is missing on {}.'.format(self.ref_date)
                print 'I will help you recover it!'
                self.create_json(nightly_build_link)
                run_backfill()

        # Remove csv file when this round finished
        os.remove(csv_file)


def main():
    arguments = docopt(__doc__)
    agent = BFagent()

    # run in different mode
    if arguments['--latest']:
        print "===============\n* Latest mode *\n==============="
        while True:
            agent.run(True)
    elif arguments['-i']:
        print "================\n* History mode *\n================"
        while True:
            agent.run_history(arguments['-i'])
    else:
        print "===============\n* Single mode *\n==============="
        agent.run(arguments['--query'])


if __name__ == '__main__':
    main()
