import os
import copy
import time
import random
import string
import traceback
from datetime import datetime
from ..common.pyDriveUtil import PyDriveUtil
from ..common.logConfig import get_logger
from lib.helper.desktopHelper import get_browser_version
from thclient import (TreeherderClient, TreeherderJobCollection)

logger = get_logger(__name__)


class PerfherderUploader(object):

    def __init__(self, client_id, secret, os_name, platform, machine_arch, build_arch, server_url=None, repo='mozilla-central'):
        # Perfherder Information
        self.server_url = server_url
        self.client_id = client_id
        self.secret = secret
        self.repo = repo
        # Author
        self.name = 'Hasal Bot'
        self.email = 'hasal-dev@mozilla.com'
        self.author = '{} <{}>'.format(self.name, self.email)
        self.subject = 'Updata Hasal Result'
        # Platform Information
        self.os_name = os_name
        self.platform = platform
        self.machine_arch = machine_arch
        self.build_arch = build_arch

    @staticmethod
    def gen_guid(length=32):
        min_length = 32
        length = max(length, min_length)
        return ''.join(random.choice(string.letters + string.digits) for _ in xrange(length))

    def create_job_dataset(self, revision, browser, timestamp, perf_data, version='', repo_link='', video_links='', extra_info_obj={}):
        job_guid = PerfherderUploader.gen_guid(len(revision))

        if browser.lower() == 'firefox':
            job_symbol = 'F'
            job_name = 'Hasal on Firefox'
        elif browser.lower() == 'chrome':
            job_symbol = 'C'
            job_name = 'Hasal on Chrome'
        else:
            job_symbol = 'O'
            job_name = 'Hasal'

        job_details = [
            {
                'content_type': 'raw_html',
                'title': 'Browser',
                'value': browser
            },
            {
                'content_type': 'raw_html',
                'title': 'Revision',
                'value': revision
            },
            {
                'content_type': 'raw_html',
                'title': 'Platform',
                'value': self.platform
            },
            {
                'content_type': 'raw_html',
                'title': 'OS',
                'value': self.os_name
            }
        ]
        if version:
            job_details.append({
                'content_type': 'raw_html',
                'title': 'Version',
                'value': version
            })
        if repo_link:
            job_details.append({
                'content_type': 'link',
                'url': repo_link,
                'title': 'Repo',
                'value': 'Link'
            })
        if video_links:
            for title, link in video_links.items():
                job_details.append({
                    'content_type': 'link',
                    'url': link,
                    'title': title,
                    'value': 'Video'
                })
        if extra_info_obj:
            for title, text in extra_info_obj.items():
                job_details.append({
                    'content_type': 'raw_html',
                    'title': title,
                    'value': text
                })

        return [
            {
                'project': 'mozilla-central',
                'revision': revision,
                'job': {
                    'job_guid': job_guid,
                    'product_name': 'hasal',
                    'reason': 'scheduler',
                    # TODO:What is `who` for?
                    'who': 'Hasal',
                    'desc': 'Hasal Regression',
                    'name': job_name,
                    # The symbol representing the job displayed in
                    # treeherder.allizom.org
                    'job_symbol': job_symbol,

                    # The symbol representing the job group in
                    # treeherder.allizom.org
                    'group_symbol': 'Hasal',
                    'group_name': 'Hasal Performance Test',

                    # TODO: get the real timing from the test runner
                    'submit_timestamp': timestamp,
                    'start_timestamp': timestamp,
                    'end_timestamp': timestamp,

                    'state': 'completed',
                    'result': 'success',

                    'machine': 'local-machine',
                    # TODO: read platform test result
                    'build_platform': {
                        'platform': self.platform,
                        'os_name': self.os_name,
                        'architecture': self.build_arch
                    },
                    'machine_platform': {
                        'platform': self.platform,
                        'os_name': self.os_name,
                        'architecture': self.machine_arch
                    },

                    'option_collection': {'opt': True},

                    # jobs can belong to different tiers
                    # setting the tier here will determine which tier the job
                    # belongs to.  However, if a job is set as Tier of 1, but
                    # belongs to the Tier 2 profile on the server, it will still
                    # be saved as Tier 2.
                    'tier': 1,

                    # the ``name`` of the log can be the default of "buildbot_text"
                    # however, you can use a custom name.  See below.
                    # TODO: point this to the log when we have them uploaded
                    'log_references': [
                        {
                            'url': 'TBD',
                            'name': 'test log'
                        }
                    ],
                    # The artifact can contain any kind of structured data
                    # associated with a test.
                    'artifacts': [
                        {
                            'type': 'json',
                            'name': 'performance_data',
                            'job_guid': job_guid,
                            'blob': perf_data
                        },
                        {
                            'type': 'json',
                            'name': 'Job Info',
                            'job_guid': job_guid,
                            'blob': {
                                'job_details': job_details
                            }
                        }
                    ],
                    # List of job guids that were coalesced to this job
                    'coalesced': []
                }
            }
        ]

    def create_job_collection(self, dataset):
        # reference the page about tjc ttps://github.com/mozilla/treeherder/blob/master/docs/submitting_data.rst
        tjc = TreeherderJobCollection()

        for data in dataset:
            tj = tjc.get_job()

            tj.add_revision(data['revision'])
            tj.add_project(data['project'])
            tj.add_coalesced_guid(data['job']['coalesced'])
            tj.add_job_guid(data['job']['job_guid'])
            tj.add_job_name(data['job']['name'])
            tj.add_job_symbol(data['job']['job_symbol'])
            tj.add_group_name(data['job']['group_name'])
            tj.add_group_symbol(data['job']['group_symbol'])
            tj.add_description(data['job']['desc'])
            tj.add_product_name(data['job']['product_name'])
            tj.add_state(data['job']['state'])
            tj.add_result(data['job']['result'])
            tj.add_reason(data['job']['reason'])
            tj.add_who(data['job']['who'])
            tj.add_tier(data['job']['tier'])
            tj.add_submit_timestamp(data['job']['submit_timestamp'])
            tj.add_start_timestamp(data['job']['start_timestamp'])
            tj.add_end_timestamp(data['job']['end_timestamp'])
            tj.add_machine(data['job']['machine'])

            tj.add_build_info(
                data['job']['build_platform']['os_name'],
                data['job']['build_platform']['platform'],
                data['job']['build_platform']['architecture']
            )

            tj.add_machine_info(
                data['job']['machine_platform']['os_name'],
                data['job']['machine_platform']['platform'],
                data['job']['machine_platform']['architecture']
            )

            tj.add_option_collection(data['job']['option_collection'])

            # data['artifact'] is a list of artifacts
            for artifact_data in data['job']['artifacts']:
                tj.add_artifact(
                    artifact_data['name'],
                    artifact_data['type'],
                    artifact_data['blob']
                )
            tjc.add(tj)
        return tjc

    def submit(self, revision, browser, timestamp, perf_data, version='', repo_link='', video_links='', extra_info_obj={}):

        j_dataset = self.create_job_dataset(revision=revision,
                                            browser=browser,
                                            timestamp=timestamp,
                                            perf_data=perf_data,
                                            version=version,
                                            repo_link=repo_link,
                                            video_links=video_links,
                                            extra_info_obj=extra_info_obj)
        tjc = self.create_job_collection(j_dataset)

        if self.server_url:
            client = TreeherderClient(server_url=self.server_url,
                                      client_id=self.client_id,
                                      secret=self.secret)
        else:
            client = TreeherderClient(client_id=self.client_id,
                                      secret=self.secret)

        try:
            return_result = client.post_collection(self.repo, tjc)
        except Exception as e:
            print e.message
            print traceback.print_exc()
            return None
        return return_result


class PerfherderUploadDataGenerator(object):

    def __init__(self, input_case_name, input_current_test_result, input_upload_config, input_index_config):
        self.DEFAULT_UPLOAD_DATA_TEMPLATE = {
            "upload_video_fp": None,
            "revision": None,
            "browser": None,
            "timestamp": None,
            "perf_data": None,
            "version": None,
            "repo_link": None,
            "video_link": None,
            "extra_info_obj": None
        }
        self.DEFAULT_PERF_DATA_TEMPLATE = {'performance_data': {'framework': {'name': 'hasal'}, 'suites': []}}
        self.DEFAULT_SUITE_DATA_TEMPLATE = {'name': '', 'value': -1, 'extraOptions': [], 'subtests': []}
        self.case_name = input_case_name
        self.browser_name = self.case_name.split("_")[1]
        self.current_test_result = input_current_test_result
        self.upload_config = input_upload_config
        self.index_config = input_index_config

    def generate_upload_data(self):
        new_perfherder_upload_data = copy.deepcopy(self.DEFAULT_UPLOAD_DATA_TEMPLATE)

        new_perfherder_upload_data['upload_video_fp'] = self.current_test_result.get("upload_video_fp", "")
        new_perfherder_upload_data['revision'] = self.upload_config['perfherder-revision']
        new_perfherder_upload_data['browser'] = self.browser_name
        new_perfherder_upload_data['timestamp'] = time.time()

        new_perf_data = copy.deepcopy(self.DEFAULT_PERF_DATA_TEMPLATE)
        if self.upload_config['perfherder-suitename']:
            suite_name = self.upload_config['perfherder-suitename']
        else:
            suite_name = "_".join(self.case_name.split("_")[2:])

        new_suite_data = copy.deepcopy(self.DEFAULT_SUITE_DATA_TEMPLATE)
        new_suite_data['name'] = '{} Median'.format(suite_name)
        new_suite_data['value'] = self.current_test_result.get(self.index_config['upload-perfherder-data-field'], -1)
        new_suite_data['extraOptions'] = [self.browser_name]
        new_suite_data['subtests'] = [{'name': suite_name, 'value': new_suite_data['value']}]

        new_perf_data['performance_data']['suites'].append(new_suite_data)
        new_perfherder_upload_data['perf_data'] = new_perf_data

        new_perfherder_upload_data['version'] = get_browser_version(self.browser_name)
        if self.browser_name.lower() == 'firefox':
            new_perfherder_upload_data['repo_link'] = 'http://hg.mozilla.org/mozilla-central/rev/{}'.format(
                new_perfherder_upload_data['revision'])
        elif self.browser_name.lower() == 'chrome':
            new_perfherder_upload_data['repo_link'] = 'https://chromium.googlesource.com/chromium/src.git/+/{}'.format(
                new_perfherder_upload_data['version'])
        return new_perfherder_upload_data


class VideoUploader(object):
    DEFAULT_UPLOAD_VIDEO_YAML_SETTING = "./mozhasalvideo.yaml"
    DEFAULT_UPLOAD_VIDEO_MYCRED_TXT = "./mycreds_mozhasalvideo.txt"
    DEFAULT_UPLOAD_FOLDER_URI = "0B9g1GJPq5xo8S0QwandkOGhnNUE"

    @staticmethod
    def upload_video(upload_video_fp):
        # init pydrive object
        pyDriveObj = PyDriveUtil(settings={"settings_file": VideoUploader.DEFAULT_UPLOAD_VIDEO_YAML_SETTING,
                                           "local_cred_file": VideoUploader.DEFAULT_UPLOAD_VIDEO_MYCRED_TXT})
        video_perview_url = ""
        if os.path.exists(upload_video_fp):
            # generate folder of current month
            upload_subfolder_name = datetime.now().strftime('%Y-%m')
            upload_subfolder_obj = pyDriveObj.create_folder_object(VideoUploader.DEFAULT_UPLOAD_FOLDER_URI, upload_subfolder_name)

            upload_folder_uri_id = upload_subfolder_obj.get('id', VideoUploader.DEFAULT_UPLOAD_FOLDER_URI)
            # upload to pydrive
            upload_result = pyDriveObj.upload_file(upload_folder_uri_id, upload_video_fp)
            if upload_result:
                video_perview_url = "/".join(upload_result['alternateLink'].split("/")[:-1]) + "/preview"
            else:
                logger.error("Upload video file [%s] to google drive failed!" % upload_video_fp)

        return video_perview_url
