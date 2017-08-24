import os
from sikuli import *  # NOQA
from common import WebApp


class Gsearch(WebApp):
    """
        The GSearch library for Sikuli cases.
        The component structure:
            <COMPONENT-NAME> = [
                [<COMPONENT-IMAGE-PLATFORM-FOO>, <OFFSET-X>, <OFFSET-Y>],
                [<COMPONENT-IMAGE-PLATFORM-BAR>, <OFFSET-X>, <OFFSET-Y>]
            ]
    """

    GSEARCH_IMAGE_HEADER = [
        [os.path.join('pics', 'gsearch_image_header.png'), 0, 0]
    ]

    GSEARCH_HOMEPAGE_BUTTONS = [
        [os.path.join('pics', 'gsearch_homepage_buttons.png'), 0, 0],
        [os.path.join('pics', 'gsearch_homepage_buttons_chrome_win10.png'), 0, 0],
        [os.path.join('pics', 'gsearch_homepage_one_button_chrome_win10.png'), 0, 0]
    ]

    GSEARCH_FOCUS_SEARCH_INPUTBOX = [
        [os.path.join('pics', 'gsearch_homepage_buttons.png'), -7, -71],
        [os.path.join('pics', 'gsearch_homepage_buttons_chrome_win10.png'), -7, -71],
        [os.path.join('pics', 'gsearch_homepage_one_button_chrome_win10.png'), -7, -71]
    ]

    GSEARCH_MOZILLA_SUGGESTION = [
        [os.path.join('pics', 'gsearch_search_result_1.png'), 0, 0],
        [os.path.join('pics', 'gsearch_search_result_2.png'), 0, 0]
    ]

    def wait_gsearch_loaded(self, similarity=0.70):
        return self._wait_for_loaded(component=Gsearch.GSEARCH_HOMEPAGE_BUTTONS, similarity=similarity)

    def wait_gimage_loaded(self, similarity=0.70):
        return self._wait_for_loaded(component=Gsearch.GSEARCH_IMAGE_HEADER, similarity=similarity)

    def wait_search_suggestion(self, similarity=0.70):
        return self._wait_for_loaded(component=Gsearch.GSEARCH_MOZILLA_SUGGESTION, similarity=similarity)

    def focus_search_inputbox(self):
        return self._click(action_name='Focus search inputbox',
                           component=Gsearch.GSEARCH_FOCUS_SEARCH_INPUTBOX)

    # click the image located in xth row and yth column (1 based)
    # for example, the very first image is (1,1).
    # this calculation is based on english version of google image search only
    def click_result_image(self, x, y):
        a = -120 + 280 * (x - 1)
        b = 190 + 200 * (y - 1)
        GSEARCH_CLICK_RESULT_IMAGE = [
            [os.path.join('pics', 'gsearch_image_header.png'), a, b]
        ]
        return self._click(action_name='Click result image', component=GSEARCH_CLICK_RESULT_IMAGE)

    def hover_result_image(self, x, y):
        a = -120 + 280 * (x - 1)
        b = 190 + 200 * (y - 1)
        GSEARCH_HOVER_RESULT_IMAGE = [
            [os.path.join('pics', 'gsearch_image_header.png'), a, b]
        ]
        return self._mouseMove(action_name='', component=GSEARCH_HOVER_RESULT_IMAGE)

    def il_type_key_down_search_suggestion(self, width, height):
        """
        Type key down on search suggestions
        """
        return self.il_key_type(key=Key.DOWN,
                                action_name='[log]  Key Down',
                                width=width,
                                height=height)

    def il_click_image(self, width, height, img_x_offset, img_y_offset):
        """
        Click image from x, y index
        """
        a = -120 + 280 * (img_x_offset - 1)
        b = 190 + 200 * (img_y_offset - 1)
        GSEARCH_HOVER_RESULT_IMAGE = [
            [os.path.join('pics', 'gsearch_image_header.png'), a, b]
        ]
        return self._il_click(action_name='[log]  Click on image',
                              component=GSEARCH_HOVER_RESULT_IMAGE,
                              width=width,
                              height=height)
