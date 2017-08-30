import os

from sikuli import *  # NOQA
from common import WebApp


class Youtube(WebApp):
    """
    The Youtube library for Sikuli cases.
    The component structure:
        <COMPONENT-NAME> = [
            [<COMPONENT-IMAGE-PLATFORM-FOO>, <OFFSET-X>, <OFFSET-Y>],
            [<COMPONENT-IMAGE-PLATFORM-BAR>, <OFFSET-X>, <OFFSET-Y>]
        ]
    """

    YOUTUBE_LOGO = [
        [os.path.join('pics', 'youtube_logo_new_win10.png'), 0, 0],
        [os.path.join('pics', 'youtube_logo.png'), 0, 0],
        [os.path.join('pics', 'youtube_logo_20170830.png'), 0, 0],
    ]

    YOUTUBE_SEARCH_BTN = [
        [os.path.join('pics', 'search_button.png'), 0, 0],
    ]

    YOUTUBE_SEARCH_FIELD = [
        [os.path.join('pics', 'search_button.png'), -80, 0],
    ]

    YOUTUBE_FUNCTION_UNDER_SEARCH_FIELD = [
        [os.path.join('pics', 'function_under_search_field_firefox_win7.png'), 0, 0],
        [os.path.join('pics', 'function_under_search_field_chrome_win7.png'), 0, 0],
        [os.path.join('pics', 'function_under_search_field_firefox_win10.png'), 0, 0],
        [os.path.join('pics', 'function_under_search_field_chrome_win10.png'), 0, 0],
    ]

    YOUTUBE_CLOSE_AD_BTN = [
        [os.path.join('pics', 'close_ad_button_firefox_win7.png'), 0, 0],
        [os.path.join('pics', 'close_ad_button_chrome_win7.png'), 0, 0],
    ]

    YOUTUBE_SEARCH_SUGGESTION_REMOVE = [
        [os.path.join('pics', 'search_suggestions_remove_chrome.png'), 0, 0],
        [os.path.join('pics', 'search_suggestions_remove_firefox.png'), 0, 0],
    ]

    def wait_for_loaded(self, similarity=0.70):
        """
        @param similarity: The similarity of YOUTUBE_LOGO component. Default: 0.70.
        """
        return self._wait_for_loaded(component=Youtube.YOUTUBE_LOGO, similarity=similarity)

    def wait_for_search_suggestion_loaded(self, similarity=0.70):
        """
        @param similarity: The similarity of YOUTUBE_SEARCH_SUGGESTION_REMOVE component. Default: 0.70.
        """
        return self._wait_for_loaded(component=Youtube.YOUTUBE_SEARCH_SUGGESTION_REMOVE, similarity=similarity)

    def click_search_field(self):
        """
        Click search field near the search button.
        """
        return self._click(action_name='Click Search Field',
                           component=Youtube.YOUTUBE_SEARCH_FIELD,
                           wait_component=Youtube.YOUTUBE_SEARCH_BTN)

    def il_type_key_down_search_suggestion(self, width, height):
        """
        Type key down on search suggestions
        """
        return self.il_key_type(key=Key.DOWN,
                                action_name='Type Key Down',
                                width=width,
                                height=height)

    def close_ad(self):
        """
        Close advertisement
        """
        return self._click_without_exception(action_name='Click Close Ad Button',
                                             component=Youtube.YOUTUBE_CLOSE_AD_BTN,
                                             timeout=2)
