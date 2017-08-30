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
        # Disable Sikuli action and info log
        self.common.infolog_enable(False)

        ff = browser.Firefox()
        fb = facebook.facebook()

        ff.clickBar()
        ff.enterLink(self.INPUT_TEST_TARGET)
        _, obj = fb.wait_for_loaded()

        sleep(2)
        sample1_fp = os.path.join(self.INPUT_IMG_SAMPLE_DIR_PATH, self.INPUT_IMG_OUTPUT_SAMPLE_1_NAME)
        sample2_fp = os.path.join(self.INPUT_IMG_SAMPLE_DIR_PATH, self.INPUT_IMG_OUTPUT_SAMPLE_1_NAME.replace('sample_1', 'sample_2'))

        sleep(2)
        capture_width = int(self.INPUT_RECORD_WIDTH)
        capture_height = int(self.INPUT_RECORD_HEIGHT)

        # Customized Region
        customized_region_name_start = 'start'
        customized_region_name_end = 'end'

        # get the region for user page and post area
        compare_area = self.tuning_region(obj, x_offset=300, y_offset=280, w_offset=510, h_offset=250)
        self.set_override_region_settings(customized_region_name_start, compare_area)
        self.set_override_region_settings(customized_region_name_end, compare_area)

        # click to make sure space keys would work in scrolling
        click(Pattern("Thinking.png").targetOffset(-284, -4))

        t1 = time.time()
        capimg1 = capture(0, 0, capture_width, capture_height)

        # assume that 100 space keys can lead us to the last car
        setAutoWaitTimeout(0)
        for i in range(100):
            Settings.TypeDelay = 0
            type(Key.SPACE)

        # if the last car wasn't found, raise exception and drop this result
        if not exists("lastCar.png", 0):
            raise Exception("The data might be changed and the last image not matched.")

        sleep(0.3)
        t2 = time.time()
        capimg2 = capture(0, 0, capture_width, capture_height)
        self.common.updateJson({'t1': t1, 't2': t2}, self.INPUT_TIMESTAMP_FILE_PATH)
        shutil.move(capimg1, sample1_fp.replace(os.path.splitext(sample1_fp)[1], '.png'))
        shutil.move(capimg2, sample2_fp.replace(os.path.splitext(sample1_fp)[1], '.png'))


case = Case(sys.argv)
case.run()
