from lib.perfBaseTest import PerfBaseTest


class TestSikuli(PerfBaseTest):

    def setUp(self):
        super(TestSikuli, self).setUp()
        self.set_configs(self.config_name.INDEX,
                         self.extract_platform_dep_settings({'win32': {'7': {'compare-threshold': 0.01},
                                                                       '10': {'compare-threshold': 0.01}}}))

    def test_chrome_ymail_ail_compose_new_mail(self):
        self.test_url = self.global_config['yahoo']['mail-url']

        self.round_status = self.sikuli.run_test(self.env.test_name,
                                                 self.env.output_name,
                                                 test_target=self.test_url,
                                                 script_dp=self.env.test_script_py_dp,
                                                 args_list=[self.env.img_sample_dp,
                                                            self.env.img_output_sample_1_fn,
                                                            self.env.DEFAULT_VIDEO_RECORDING_WIDTH,
                                                            self.env.DEFAULT_VIDEO_RECORDING_HEIGHT,
                                                            self.env.DEFAULT_TIMESTAMP])
