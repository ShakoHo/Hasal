from lib.perfBaseTest import PerfBaseTest


class TestSikuli(PerfBaseTest):

    def setUp(self):
        super(TestSikuli, self).setUp()

    def test_firefox_w3school_ail_type_0(self):
        self.round_status = self.sikuli.run_test(self.env.test_name, self.env.output_name, test_target="https://www.w3schools.com/TagS/tryit.asp?filename=tryhtml_textarea",
                                                 script_dp=self.env.test_script_py_dp,
                                                 args_list=[self.env.img_sample_dp, self.env.img_output_sample_1_fn,
                                                            self.exec_config['video-recording-width'],
                                                            self.exec_config['video-recording-height'],
                                                            self.env.DEFAULT_TIMESTAMP])
