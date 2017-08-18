# if you are putting your test script folders under {git project folder}/tests/, it will work fine.
# otherwise, you either add it to system path before you run or hard coded it in here.

INPUT_LIB_PATH = sys.argv[1]
sys.path.append(INPUT_LIB_PATH)

import os
import common
import basecase
import amazon

import string
import shutil
import browser
import time


class Case(basecase.SikuliInputLatencyCase):

    def run(self):
        # Disable Sikuli action and info log
        com = common.General()
        com.infolog_enable(False)
        com.set_mouse_delay(0)
        delay = com.find_key_type_delay()

        # Prepare
        app = amazon.Amazon()
        sample1_file_path = os.path.join(self.INPUT_IMG_SAMPLE_DIR_PATH, self.INPUT_IMG_OUTPUT_SAMPLE_1_NAME)
        sample2_file_path = os.path.join(self.INPUT_IMG_SAMPLE_DIR_PATH, self.INPUT_IMG_OUTPUT_SAMPLE_1_NAME.replace('sample_1', 'sample_2'))
        sample1_file_path = sample1_file_path.replace(os.path.splitext(sample1_file_path)[1], '.png')
        sample2_file_path = sample2_file_path.replace(os.path.splitext(sample2_file_path)[1], '.png')
        capture_width = int(self.INPUT_RECORD_WIDTH)
        capture_height = int(self.INPUT_RECORD_HEIGHT)

        # Launch browser
        my_browser = browser.Chrome()

        # Access link and wait
        my_browser.clickBar()
        my_browser.enterLink(self.INPUT_TEST_TARGET)
        app.wait_for_search_button_loaded()

        # Wait for stable
        sleep(2)

        # PRE ACTIONS
        app.click_search_field()
        sleep(1)

        # Customized Region
        customized_region_name_start = 'start'
        customized_region_name_end = 'end'
        _, type_area = app.wait_for_component_display(app.AMAZON_SEARCH_BAR, similarity=0.9)
        self.set_override_region_settings(customized_region_name_start, type_area)
        self.set_override_region_settings(customized_region_name_end, type_area)

        t1 = time.time()
        capimg1 = capture(0, 0, capture_width, capture_height)

        # Reference from https://en.wikipedia.org/wiki/Lorem_ipsum
        # extract 100 chars from Lorem ipsum text and filter characters which will affect result, e.g., i, j, and l
        char_str = "orempsumdorstametconsecteturadpscngetsedoeusmodtemporncduntutaboretdoremagnaquatenmadmnvenamqusnoexe"
        com.system_print('Type char')
        com.delayed_type(char_str, 0.1, delay)
        sleep(1)

        # Record T2
        t2 = time.time()

        # POST ACTIONS
        capimg2 = capture(0, 0, capture_width, capture_height)

        # Write timestamp
        com.updateJson({'t1': t1, 't2': t2}, self.INPUT_TIMESTAMP_FILE_PATH)

        # Write the snapshot image
        shutil.move(capimg1, sample1_file_path)
        shutil.move(capimg2, sample2_file_path)


case = Case(sys.argv)
case.run()
