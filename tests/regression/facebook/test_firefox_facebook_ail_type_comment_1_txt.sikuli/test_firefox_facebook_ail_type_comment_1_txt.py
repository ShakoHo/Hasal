# if you are putting your test script folders under {git project folder}/tests/, it will work fine.
# otherwise, you either add it to system path before you run or hard coded it in here.

INPUT_LIB_PATH = sys.argv[1]
sys.path.append(INPUT_LIB_PATH)

import os
import basecase
import facebook

import shutil
import browser
import time


class Case(basecase.SikuliInputLatencyCase):

    def run(self):
        sample1_fp = os.path.join(self.INPUT_IMG_SAMPLE_DIR_PATH, self.INPUT_IMG_OUTPUT_SAMPLE_1_NAME)
        sample1_file_path = sample1_fp.replace(os.path.splitext(sample1_fp)[1], '.png')
        capture_width = int(self.INPUT_RECORD_WIDTH)
        capture_height = int(self.INPUT_RECORD_HEIGHT)

        # Disable Sikuli action and info log
        self.common.infolog_enable(False)
        Settings.MoveMouseDelay = 0
        setAutoWaitTimeout(10)

        ff = browser.Firefox()
        fb = facebook.facebook()

        ff.clickBar()
        ff.enterLink(self.INPUT_TEST_TARGET)
        fb.wait_for_loaded()
        sleep(2)

        # Customized Region
        customized_region_name = 'end'
        type_area_component = [
            ['facebook_type_comment_win.png', 0, 0],
            ['facebook_type_comment_win_20170906.png', 0, 0]
        ]
        type_area = self.find_match_region(type_area_component, similarity=0.80)
        self.set_override_region_settings(customized_region_name, type_area)
        click(type_area)
        sleep(0.2)

        # Record T1, and capture the snapshot image
        # Input Latency Action
        screenshot, t1 = fb.il_type('a', capture_width, capture_height)

        # In normal condition, a should appear within 200ms,
        # but if lag happened, that could lead the show up after 200 ms,
        # and that will cause the calculation of AIL much smaller than expected.
        sleep(0.2)

        # Record T2
        t2 = time.time()

        self.common.updateJson({'t1': t1, 't2': t2}, self.INPUT_TIMESTAMP_FILE_PATH)
        shutil.move(screenshot, sample1_file_path)


case = Case(sys.argv)
case.run()
