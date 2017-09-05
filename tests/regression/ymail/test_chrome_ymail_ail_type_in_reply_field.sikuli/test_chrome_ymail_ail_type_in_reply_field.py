# if you are putting your test script folders under {git project folder}/tests/, it will work fine.
# otherwise, you either add it to system path before you run or hard coded it in here.

INPUT_LIB_PATH = sys.argv[1]
sys.path.append(INPUT_LIB_PATH)

import os
import basecase
import ymail

import shutil
import browser
import time


class Case(basecase.SikuliInputLatencyCase):

    def run(self):
        # Disable Sikuli action and info log
        self.common.infolog_enable(False)
        Settings.MoveMouseDelay = 0

        # Prepare
        app = ymail.yMail()
        sample1_file_path = os.path.join(self.INPUT_IMG_SAMPLE_DIR_PATH, self.INPUT_IMG_OUTPUT_SAMPLE_1_NAME)
        sample1_file_path = sample1_file_path.replace(os.path.splitext(sample1_file_path)[1], '.png')
        capture_width = int(self.INPUT_RECORD_WIDTH)
        capture_height = int(self.INPUT_RECORD_HEIGHT)

        # Launch browser
        my_browser = browser.Chrome()

        # Access link and wait
        my_browser.clickBar()
        my_browser.enterLink(self.INPUT_TEST_TARGET)
        app.wait_for_loaded()

        # Wait for stable
        sleep(2)

        # PRE ACTIONS
        loc, _, obj = app.click_compose_btn()
        sleep(1)
        pattern, _ = app.wait_for_mail_composer_toolbar_loaded()
        sleep(1)
        app.click_mail_composer_edit_field()

        # Customized Region
        customized_region_name = 'end'
        compare_area = self.tuning_region(obj, x_offset=200, y_offset=80, w_offset=40, h_offset=40)
        self.set_override_region_settings(customized_region_name, compare_area)

        # Record T1, and capture the snapshot image
        # Input Latency Action
        screenshot, t1 = app.il_type('a', capture_width, capture_height)

        # In normal condition, a should appear within 100ms,
        # but if lag happened, that could lead the show up after 100 ms,
        # and that will cause the calculation of AIL much smaller than expected.
        sleep(0.1)

        # Record T2
        t2 = time.time()

        # POST ACTIONS
        sleep(2)
        app.click_mail_composer_del_btn()

        # Write timestamp
        self.common.updateJson({'t1': t1, 't2': t2}, self.INPUT_TIMESTAMP_FILE_PATH)

        # Write the snapshot image
        shutil.move(screenshot, sample1_file_path)

        app.wait_pattern_for_vanished(pattern=pattern)


case = Case(sys.argv)
case.run()
