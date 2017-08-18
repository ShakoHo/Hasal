# if you are putting your test script folders under {git project folder}/tests/, it will work fine.
# otherwise, you either add it to system path before you run or hard coded it in here.

INPUT_LIB_PATH = sys.argv[1]
sys.path.append(INPUT_LIB_PATH)

import os
import common
import basecase
import facebook

import string
import shutil
import browser
import time


class Case(basecase.SikuliInputLatencyCase):

    def run(self):
        # Disable Sikuli action and info log
        com = common.General()
        com.infolog_enable(False)
        delay = com.find_key_type_delay()

        ff = browser.Firefox()
        fb = facebook.facebook()

        ff.clickBar()
        ff.enterLink(self.INPUT_TEST_TARGET)
        fb.wait_for_loaded()

        sleep(2)
        _, _, obj = fb.click_post_area_home()
        sample1_fp = os.path.join(self.INPUT_IMG_SAMPLE_DIR_PATH, self.INPUT_IMG_OUTPUT_SAMPLE_1_NAME)
        sample2_fp = os.path.join(self.INPUT_IMG_SAMPLE_DIR_PATH, self.INPUT_IMG_OUTPUT_SAMPLE_1_NAME.replace('sample_1', 'sample_2'))

        sleep(2)
        capture_width = int(self.INPUT_RECORD_WIDTH)
        capture_height = int(self.INPUT_RECORD_HEIGHT)

        # Customized Region
        customized_region_name_start = 'start'
        customized_region_name_end = 'end'

        # part region of search suggestion list
        compare_area = self.tuning_region(obj, x_offset=50, y_offset=45, w_offset=-65, h_offset=-60)
        self.set_override_region_settings(customized_region_name_start, compare_area)
        self.set_override_region_settings(customized_region_name_end, compare_area)

        t1 = time.time()
        capimg1 = capture(0, 0, capture_width, capture_height)

        # Reference from https://en.wikipedia.org/wiki/Lorem_ipsum
        # extract 100 chars from Lorem ipsum text and filter characters which will affect result, e.g., i, j, and l
        char_str = "orempsumdorstametconsecteturadpscngetsedoeusmodtemporncduntutaboretdoremagnaquatenmadmnvenamqusnoexe"
        com.system_print('Type char')
        com.delayed_type(char_str, 0.1, delay)

        sleep(1)
        t2 = time.time()
        capimg2 = capture(0, 0, capture_width, capture_height)
        com.updateJson({'t1': t1, 't2': t2}, self.INPUT_TIMESTAMP_FILE_PATH)
        shutil.move(capimg1, sample1_fp.replace(os.path.splitext(sample1_fp)[1], '.png'))
        shutil.move(capimg2, sample2_fp.replace(os.path.splitext(sample1_fp)[1], '.png'))


case = Case(sys.argv)
case.run()
